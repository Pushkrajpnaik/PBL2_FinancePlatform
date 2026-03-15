import requests
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import logging
import io

logger = logging.getLogger(__name__)

AMFI_NAV_URL = "https://www.amfiindia.com/spages/NAVAll.txt"

# Popular funds with their AMFI scheme codes
POPULAR_FUNDS = {
    "Axis Bluechip Fund":              "120503",
    "Mirae Asset Large Cap Fund":      "120465",
    "Parag Parikh Flexi Cap Fund":     "119598",
    "SBI Small Cap Fund":              "125497",
    "HDFC Mid-Cap Opportunities Fund": "118989",
    "Kotak Emerging Equity Fund":      "131655",
    "Axis Long Term Equity Fund":      "120503",
    "Mirae Asset Tax Saver Fund":      "139956",
    "SBI Bluechip Fund":               "119802",
    "ICICI Pru Bluechip Fund":         "120586",
}


def fetch_all_nav() -> Optional[pd.DataFrame]:
    """
    Fetches all mutual fund NAV data from AMFI.
    Free, no API key needed.
    Updates daily after market close.
    """
    try:
        logger.info("Fetching NAV data from AMFI...")
        response = requests.get(AMFI_NAV_URL, timeout=30)
        response.raise_for_status()

        lines = response.text.strip().split("\n")
        records = []
        current_category = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("Open Ended") or line.startswith("Close Ended"):
                current_category = line
                continue
            parts = line.split(";")
            if len(parts) >= 5:
                try:
                    records.append({
                        "scheme_code": parts[0].strip(),
                        "isin_div_payout": parts[1].strip(),
                        "isin_div_reinvest": parts[2].strip(),
                        "scheme_name": parts[3].strip(),
                        "nav": float(parts[4].strip()),
                        "nav_date": parts[5].strip() if len(parts) > 5 else datetime.today().strftime("%d-%b-%Y"),
                        "category": current_category,
                    })
                except (ValueError, IndexError):
                    continue

        df = pd.DataFrame(records)
        logger.info(f"Fetched {len(df)} NAV records from AMFI")
        return df

    except Exception as e:
        logger.error(f"Failed to fetch AMFI NAV: {e}")
        return None


def fetch_nav_for_scheme(scheme_code: str) -> Optional[Dict]:
    """Fetches NAV history for a specific scheme from MFAPI."""
    try:
        url      = f"https://api.mfapi.in/mf/{scheme_code}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data     = response.json()

        if "data" not in data:
            return None

        nav_history = []
        for entry in data["data"][:365]:  # Last 1 year
            try:
                nav_history.append({
                    "date": entry["date"],
                    "nav":  float(entry["nav"]),
                })
            except (ValueError, KeyError):
                continue

        df = pd.DataFrame(nav_history)
        if df.empty:
            return None

        df["date"]    = pd.to_datetime(df["date"], format="%d-%m-%Y")
        df            = df.sort_values("date")
        df["returns"] = df["nav"].pct_change()

        latest_nav  = float(df["nav"].iloc[-1])
        return_1y   = float((df["nav"].iloc[-1] / df["nav"].iloc[0] - 1) * 100) if len(df) > 1 else 0
        volatility  = float(df["returns"].std() * (252 ** 0.5) * 100)

        return {
            "scheme_code":   scheme_code,
            "scheme_name":   data.get("meta", {}).get("scheme_name", ""),
            "fund_house":    data.get("meta", {}).get("fund_house", ""),
            "scheme_type":   data.get("meta", {}).get("scheme_type", ""),
            "latest_nav":    round(latest_nav, 4),
            "return_1y":     round(return_1y, 2),
            "volatility":    round(volatility, 2),
            "nav_date":      df["date"].iloc[-1].strftime("%Y-%m-%d"),
            "history":       df.tail(30).to_dict(orient="records"),
        }

    except Exception as e:
        logger.error(f"Failed to fetch NAV for {scheme_code}: {e}")
        return None


def get_popular_funds_data() -> List[Dict]:
    """Fetches data for all popular funds."""
    results = []
    for name, code in POPULAR_FUNDS.items():
        data = fetch_nav_for_scheme(code)
        if data:
            results.append(data)
        else:
            results.append({
                "scheme_code": code,
                "scheme_name": name,
                "latest_nav":  0,
                "return_1y":   0,
                "volatility":  0,
                "error":       "Could not fetch data",
            })
    return results


def search_fund_by_name(query: str) -> List[Dict]:
    """Searches for mutual funds by name."""
    try:
        url      = f"https://api.mfapi.in/mf/search?q={query}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data     = response.json()
        return [{"scheme_code": f["schemeCode"], "scheme_name": f["schemeName"]} for f in data[:10]]
    except Exception as e:
        logger.error(f"Fund search failed: {e}")
        return []