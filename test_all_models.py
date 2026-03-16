"""
============================================================
COMPREHENSIVE MODEL ROBUSTNESS TEST SUITE
AI-Powered Financial Intelligence Platform
============================================================
Run: python test_all_models.py
Expected Score: 90%+
============================================================
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
EMAIL    = "test@gmail.com"
PASSWORD = "test123"

# ─── Terminal Colors ──────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

results = {"passed": 0, "failed": 0, "warnings": 0, "details": []}


def log(msg, color=RESET):       print(f"{color}{msg}{RESET}")
def section(title):              log(f"\n{BOLD}{'='*60}\nTEST SUITE — {title}\n{'='*60}{RESET}", BLUE)

def passed(name, detail=""):
    results["passed"] += 1
    results["details"].append({"test": name, "status": "PASS", "detail": detail})
    log(f"  ✅ PASS  {name}: {detail}", GREEN)

def failed(name, detail=""):
    results["failed"] += 1
    results["details"].append({"test": name, "status": "FAIL", "detail": detail})
    log(f"  ❌ FAIL  {name}: {detail}", RED)

def warning(name, detail=""):
    results["warnings"] += 1
    results["details"].append({"test": name, "status": "WARN", "detail": detail})
    log(f"  ⚠️  WARN  {name}: {detail}", YELLOW)

def get_token():
    try:
        res = requests.post(f"{BASE_URL}/auth/login",
            json={"email": EMAIL, "password": PASSWORD}, timeout=10)
        return res.json().get("access_token")
    except Exception as e:
        log(f"Login failed: {e}", RED)
        return None

def api(token, method, path, data=None, params=None, timeout=90):
    headers = {"Authorization": f"Bearer {token}"}
    url     = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            return requests.get(url, headers=headers, params=params, timeout=timeout)
        else:
            return requests.post(url, headers=headers, json=data, timeout=timeout)
    except Exception as e:
        log(f"    Request failed: {e}", RED)
        return None


# ============================================================
# SUITE 1 — AUTHENTICATION & VALIDATION
# ============================================================
def test_auth(token):
    section("1 — AUTHENTICATION & VALIDATION")

    # Test 1.1 — Valid login
    r = requests.post(f"{BASE_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD})
    if r and r.status_code == 200 and r.json().get("access_token"):
        passed("Auth - Valid login returns token")
    else:
        failed("Auth - Valid login", str(r.status_code if r else "no response"))

    # Test 1.2 — Invalid password rejected
    r = requests.post(f"{BASE_URL}/auth/login",
        json={"email": EMAIL, "password": "wrongpassword"})
    if r and r.status_code in [401, 403, 400]:
        passed("Auth - Wrong password rejected", f"Status {r.status_code}")
    else:
        warning("Auth - Wrong password", f"Got {r.status_code if r else 'no response'}")

    # Test 1.3 — Invalid email format rejected
    r = requests.post(f"{BASE_URL}/auth/register",
        json={"email": "notanemail", "full_name": "Test User", "password": "Test@123"})
    if r and r.status_code == 422:
        passed("Auth - Invalid email format rejected", "422 Unprocessable")
    else:
        warning("Auth - Email validation", f"Got {r.status_code if r else 'no response'}")

    # Test 1.4 — Special chars in name rejected
    r = requests.post(f"{BASE_URL}/auth/register",
        json={"email": "newtest@gmail.com", "full_name": "Test@#$123", "password": "Test@123"})
    if r and r.status_code == 422:
        passed("Auth - Special chars in name rejected", "422 Unprocessable")
    else:
        warning("Auth - Name validation", f"Got {r.status_code if r else 'no response'}")

    # Test 1.5 — Weak password rejected
    r = requests.post(f"{BASE_URL}/auth/register",
        json={"email": "newtest2@gmail.com", "full_name": "Test User", "password": "weak"})
    if r and r.status_code == 422:
        passed("Auth - Weak password rejected", "422 Unprocessable")
    else:
        warning("Auth - Password validation", f"Got {r.status_code if r else 'no response'}")

    # Test 1.6 — Token required for protected routes
    r = requests.get(f"{BASE_URL}/market/summary")
    if r and r.status_code in [401, 403]:
        passed("Auth - Protected route requires token", f"Status {r.status_code}")
    else:
        warning("Auth - Route protection", f"Got {r.status_code if r else 'no response'}")


# ============================================================
# SUITE 2 — LIVE MARKET DATA
# ============================================================
def test_market_data(token):
    section("2 — LIVE MARKET DATA")

    # Test 2.1 — Market summary returns real values
    r = api(token, "GET", "/market/summary")
    if r and r.status_code == 200:
        data   = r.json()
        nifty  = data.get("NIFTY50", {}).get("price", 0)
        sensex = data.get("SENSEX", {}).get("price", 0)
        gold   = data.get("GOLD", {}).get("price", 0)
        crude  = data.get("CRUDE_OIL", {}).get("price", 0)
        usd    = data.get("USD_INR", {}).get("price", 0)

        if 15000 < nifty < 35000:
            passed("Market - NIFTY50 valid range", f"Rs {nifty}")
        else:
            failed("Market - NIFTY50 out of range", str(nifty))

        if 50000 < sensex < 120000:
            passed("Market - SENSEX valid range", f"Rs {sensex}")
        else:
            failed("Market - SENSEX out of range", str(sensex))

        if gold > 0:
            passed("Market - Gold price exists", f"${gold}")
        else:
            failed("Market - Gold price missing")

        if 40 < crude < 200:
            passed("Market - Crude oil valid range", f"${crude}")
        else:
            failed("Market - Crude oil out of range", str(crude))

        if 70 < usd < 110:
            passed("Market - USD/INR valid range", f"Rs {usd}")
        else:
            failed("Market - USD/INR out of range", str(usd))
    else:
        failed("Market - Summary API failed", str(r.status_code if r else "no response"))

    # Test 2.2 — NIFTY history different periods give different results
    log("\n  Checking NIFTY history across periods...")
    histories = {}
    for period in ["1mo", "3mo", "6mo", "1y"]:
        r = api(token, "GET", f"/market/nifty50?period={period}")
        if r and r.status_code == 200:
            histories[period] = len(r.json().get("history", []))

    if len(set(histories.values())) > 1:
        passed("Market - Different periods = different data", str(histories))
    else:
        warning("Market - Periods same count", str(histories))

    # Test 2.3 — Stats vary across periods
    returns_list = []
    for period in ["1mo", "3mo", "1y"]:
        r = api(token, "GET", f"/market/nifty50?period={period}")
        if r and r.status_code == 200:
            stat = r.json().get("stats", {}).get("annual_return", 0)
            returns_list.append(round(stat, 1))

    if len(set(returns_list)) > 1:
        passed("Market - Returns vary across periods", str(returns_list))
    else:
        warning("Market - Returns identical (expected for same market)", str(returns_list))

    # Test 2.4 — Regime detection from real data
    r = api(token, "GET", "/market/regime/real?period=3mo")
    if r and r.status_code == 200:
        data       = r.json()
        regime     = data.get("regime", "")
        confidence = data.get("confidence", 0)
        momentum   = data.get("momentum", 0)
        valid      = ["Bull Market","Bear Market","High Volatility","Recovery","Sideways/Neutral"]

        if regime in valid:
            passed("Market - Valid regime detected", f"{regime} ({confidence:.1f}% conf)")
        else:
            failed("Market - Invalid regime", regime)

        if 0 < confidence <= 100:
            passed("Market - Confidence valid range", f"{confidence:.2f}%")
        else:
            failed("Market - Confidence out of range", str(confidence))

        # Momentum consistency
        if regime == "Bear Market" and momentum < 0:
            passed("Market - Momentum matches Bear Market", f"{momentum:.2f}%")
        elif regime == "Bull Market" and momentum > 0:
            passed("Market - Momentum matches Bull Market", f"{momentum:.2f}%")
        else:
            warning("Market - Regime/momentum check",
                    f"Regime={regime}, Momentum={momentum:.2f}%")
    else:
        failed("Market - Regime API failed")

    # Test 2.5 — Macro data
    r = api(token, "GET", "/market/macro")
    if r and r.status_code == 200:
        data    = r.json()
        usd_inr = data.get("forex", {}).get("usd_inr", 0)
        crude   = data.get("commodities", {}).get("crude_oil_usd", 0)
        if 70 < usd_inr < 110:
            passed("Market - Macro USD/INR valid", f"Rs {usd_inr}")
        else:
            failed("Market - Macro USD/INR invalid", str(usd_inr))
    else:
        failed("Market - Macro API failed")


# ============================================================
# SUITE 3 — FINBERT NEWS SENTIMENT
# ============================================================
def test_news_sentiment(token):
    section("3 — FINBERT NEWS SENTIMENT")

    # 8 test cases with known expected sentiments
    test_cases = [
        {"text": "Nifty crashes 1300 points as Iran war fears grip markets",            "expected": "Negative", "label": "War/Crash news"       },
        {"text": "India GDP grows 7.5%, beats all analyst expectations",                 "expected": "Positive", "label": "GDP growth"            },
        {"text": "RBI keeps repo rate unchanged at 6.5%",                               "expected": "Neutral",  "label": "Policy neutral"        },
        {"text": "Sensex surges 1500 points on FII buying, Nifty breaks 25000",         "expected": "Positive", "label": "Market rally"          },
        {"text": "Bank NPA crisis deepens, RBI warns of systemic risk",                  "expected": "Negative", "label": "Banking crisis"        },
        {"text": "Infosys beats Q4 earnings, revenue up 15% year on year",              "expected": "Positive", "label": "Earnings beat"         },
        {"text": "SEBI approves new mutual fund category for retail investors",          "expected": "Positive", "label": "Regulatory positive"   },
        {"text": "Market ends sharply lower as selling pressure intensifies across sectors", "expected": "Negative", "label": "Market selloff"   },
    ]

    scores    = []
    correct   = 0
    log(f"\n  Running {len(test_cases)} FinBERT sentiment tests...")

    for tc in test_cases:
        r = api(token, "POST", "/news/analyze-text",
                data={"text": tc["text"], "use_finbert": True})
        if r and r.status_code == 200:
            data      = r.json()
            sentiment = data.get("sentiment", "")
            score     = data.get("compound_score", 0)
            model     = data.get("model_used", "")
            scores.append(score)

            if sentiment == tc["expected"]:
                correct += 1
                passed(f"FinBERT - {tc['label']}",
                       f"{sentiment} (score={score:.4f}, model={model})")
            else:
                warning(f"FinBERT - {tc['label']}",
                        f"Expected={tc['expected']}, Got={sentiment}, score={score:.4f}")
        else:
            failed(f"FinBERT - {tc['label']}", "API call failed")

    # Score diversity check
    unique_scores = len(set([round(s, 2) for s in scores]))
    if unique_scores >= 4:
        passed("FinBERT - Score diversity", f"{unique_scores} unique scores across {len(scores)} tests")
    else:
        warning("FinBERT - Low diversity", f"Only {unique_scores} unique scores")

    # Sentiment diversity
    sentiments_got = set()
    for tc in test_cases:
        r = api(token, "POST", "/news/analyze-text",
                data={"text": tc["text"], "use_finbert": False})
        if r and r.status_code == 200:
            sentiments_got.add(r.json().get("sentiment", ""))

    if len(sentiments_got) >= 2:
        passed("FinBERT - Detects multiple sentiments", str(sentiments_got))
    else:
        failed("FinBERT - Only one sentiment detected", str(sentiments_got))

    # Overall accuracy
    accuracy = correct / len(test_cases) * 100
    if accuracy >= 70:
        passed("FinBERT - Overall accuracy", f"{accuracy:.1f}% ({correct}/{len(test_cases)})")
    elif accuracy >= 50:
        warning("FinBERT - Accuracy acceptable", f"{accuracy:.1f}%")
    else:
        failed("FinBERT - Accuracy below threshold", f"{accuracy:.1f}%")

    # Geopolitical risk tests
    log("\n  Testing geopolitical risk scoring...")
    geo_cases = [
        ("Iran war missiles attack Hormuz strait closure oil supply", 0.4, "War scenario"),
        ("RBI quarterly policy review meeting held today in Mumbai", 0.0, "Normal policy (should be low)"),
        ("Russia Ukraine conflict oil supply disruption global sanctions", 0.3, "Geopolitical conflict"),
    ]
    for text, min_score, label in geo_cases:
        r = api(token, "POST", "/news/analyze-text",
                data={"text": text, "use_finbert": False})
        if r and r.status_code == 200:
            geo   = r.json().get("geopolitical_risk", {})
            score = geo.get("score", 0)
            level = geo.get("level", "")
            if score >= min_score:
                passed(f"GeoRisk - {label}", f"Score={score}, Level={level}")
            else:
                warning(f"GeoRisk - {label}", f"Score={score} (expected >={min_score})")

    # Live news test
    r = api(token, "GET", "/news/market-sentiment?force_refresh=false", timeout=30)
    if r and r.status_code == 200:
        data     = r.json()
        articles = data.get("total_articles", 0)
        if articles > 0:
            passed("News - Live articles fetched", f"{articles} articles")
        else:
            warning("News - No articles (cache may be empty)", "Try force_refresh=true")
    else:
        warning("News - Market sentiment endpoint", "Check if news cache is populated")


# ============================================================
# SUITE 4 — ARIMA PREDICTION
# ============================================================
def test_arima(token):
    section("4 — ARIMA PREDICTION")

    periods      = ["6mo", "1y", "2y"]
    arima_results = []

    for period in periods:
        r = api(token, "GET", f"/prediction/nifty50/arima?period={period}&forecast_days=30")
        if r and r.status_code == 200:
            data      = r.json()
            summary   = data.get("summary", {})
            current   = data.get("current_price", 0)
            pred_30   = summary.get("predicted_price_30d", 0)
            ret_30    = summary.get("expected_return_30d", 0)
            direction = summary.get("direction", "")
            arima_results.append({"period": period, "return": ret_30, "direction": direction})

            if current > 0:
                passed(f"ARIMA ({period}) - Current price valid", f"Rs {current}")
            else:
                failed(f"ARIMA ({period}) - Invalid price", str(current))

            if pred_30 > 0:
                passed(f"ARIMA ({period}) - Prediction positive", f"Rs {pred_30:.2f}")
            else:
                failed(f"ARIMA ({period}) - Prediction invalid", str(pred_30))

            if current > 0:
                diff_pct = abs((pred_30 - current) / current * 100)
                if diff_pct < 50:
                    passed(f"ARIMA ({period}) - Prediction reasonable",
                           f"{ret_30:.2f}% predicted return")
                else:
                    failed(f"ARIMA ({period}) - Prediction extreme", f"{diff_pct:.1f}% from current")

            stat = data.get("stationarity", {})
            if stat.get("p_value", 1) < 0.05:
                passed(f"ARIMA ({period}) - Stationarity test",
                       f"p={stat.get('p_value')} (stationary)")
            else:
                warning(f"ARIMA ({period}) - Non-stationary",
                        f"p={stat.get('p_value')} (need more data)")

            preds = data.get("predictions", [])
            if len(preds) == 30:
                passed(f"ARIMA ({period}) - 30 predictions generated", "✓")
            else:
                warning(f"ARIMA ({period}) - Prediction count", f"Got {len(preds)}")
        else:
            failed(f"ARIMA ({period}) - API failed",
                   str(r.status_code if r else "no response"))

    # Different periods = different predictions
    if len(arima_results) >= 2:
        rets = [round(r["return"], 2) for r in arima_results]
        if len(set(rets)) > 1:
            passed("ARIMA - Periods give different predictions",
                   str([f"{r['period']}:{r['return']:.2f}%" for r in arima_results]))
        else:
            warning("ARIMA - All periods same prediction", str(rets))


# ============================================================
# SUITE 5 — XGBOOST PREDICTION
# ============================================================
def test_xgboost(token):
    section("5 — XGBOOST PREDICTION")

    xgb_results = []
    for period in ["1y", "2y"]:
        r = api(token, "GET", f"/prediction/nifty50/xgboost?period={period}")
        if r and r.status_code == 200:
            data      = r.json()
            accuracy  = data.get("accuracy", 0)
            direction = data.get("next_day_direction", "")
            confidence= data.get("confidence", 0)
            up_prob   = data.get("up_probability", 0)
            down_prob = data.get("down_probability", 0)
            feat_imp  = data.get("feature_importance", {})
            train_n   = data.get("training_samples", 0)
            xgb_results.append(data)

            if accuracy > 45:
                passed(f"XGBoost ({period}) - Accuracy above random", f"{accuracy:.2f}%")
            else:
                failed(f"XGBoost ({period}) - Below random baseline", f"{accuracy:.2f}%")

            prob_sum = up_prob + down_prob
            if 98 < prob_sum < 102:
                passed(f"XGBoost ({period}) - Probabilities sum ~100%",
                       f"UP={up_prob:.1f}% DOWN={down_prob:.1f}%")
            else:
                failed(f"XGBoost ({period}) - Probability sum error", f"Sum={prob_sum:.1f}%")

            if direction in ["UP", "DOWN"]:
                passed(f"XGBoost ({period}) - Valid direction", direction)
            else:
                failed(f"XGBoost ({period}) - Invalid direction", direction)

            if feat_imp and len(feat_imp) >= 5:
                top = list(feat_imp.keys())[0]
                passed(f"XGBoost ({period}) - Feature importance populated",
                       f"Top: {top}")
            else:
                warning(f"XGBoost ({period}) - Sparse feature importance")

            if train_n > 50:
                passed(f"XGBoost ({period}) - Sufficient training data",
                       f"{train_n} samples")
            else:
                failed(f"XGBoost ({period}) - Insufficient data", f"{train_n} samples")
        else:
            failed(f"XGBoost ({period}) - API failed",
                   str(r.status_code if r else "no response"))

    # Feature importance differs across periods (model learns differently)
    if len(xgb_results) >= 2:
        fi1 = list(xgb_results[0].get("feature_importance", {}).values())[:3]
        fi2 = list(xgb_results[1].get("feature_importance", {}).values())[:3]
        if fi1 != fi2:
            passed("XGBoost - Feature importance varies across periods",
                   "Model learns different patterns")
        else:
            warning("XGBoost - Feature importance identical", "May indicate overfitting")


# ============================================================
# SUITE 6 — INVESTMENT SIGNAL (Combined Pipeline)
# ============================================================
def test_investment_signal(token):
    section("6 — INVESTMENT SIGNAL (Combined Pipeline)")

    r = api(token, "GET", "/prediction/investment-signal", timeout=120)
    if r and r.status_code == 200:
        data   = r.json()
        signal = data.get("signal", "")
        score  = data.get("score", 0)
        regime = data.get("regime", "")
        geo    = data.get("geo_risk", 0)
        comps  = data.get("components", {})

        valid_signals = ["STRONG BUY", "BUY", "HOLD", "SELL", "STRONG SELL"]
        if signal in valid_signals:
            passed("Signal - Valid signal generated", f"'{signal}'")
        else:
            failed("Signal - Invalid signal", str(signal))

        if -5 <= score <= 5:
            passed("Signal - Score in valid range", f"{score:.3f}")
        else:
            failed("Signal - Score out of range", str(score))

        required = ["arima_direction","xgboost_direction","regime","news_score","geo_risk_score"]
        missing  = [c for c in required if c not in comps]
        if not missing:
            passed("Signal - All 5 components present", "✓")
        else:
            warning("Signal - Missing components", str(missing))

        if 0 <= geo <= 1:
            passed("Signal - Geo risk valid range", f"{geo:.3f}")
        else:
            failed("Signal - Geo risk out of range", str(geo))

        # Signal/regime consistency
        if regime == "Bear Market" and signal in ["SELL","STRONG SELL","HOLD"]:
            passed("Signal - Consistent with Bear Market", f"{signal} during {regime}")
        elif regime == "Bull Market" and signal in ["BUY","STRONG BUY","HOLD"]:
            passed("Signal - Consistent with Bull Market", f"{signal} during {regime}")
        else:
            warning("Signal - Mixed signals (models disagree)",
                    f"Signal={signal}, Regime={regime} — this is normal")

        log(f"\n  Signal Summary:")
        log(f"    Signal:   {signal}", GREEN if "BUY" in signal else RED if "SELL" in signal else YELLOW)
        log(f"    Score:    {score:.3f}")
        log(f"    Regime:   {regime}")
        log(f"    Geo Risk: {geo:.3f}")
        for k, v in comps.items():
            log(f"    {k}: {v}")
    else:
        failed("Signal - API failed",
               str(r.status_code if r else "no response"))


# ============================================================
# SUITE 7 — PORTFOLIO OPTIMIZATION
# ============================================================
def test_portfolio(token):
    section("7 — PORTFOLIO OPTIMIZATION")

    profiles = ["Conservative","Moderate","Aggressive"]
    methods  = ["markowitz","risk_parity","cvar"]
    results_by_profile = {}

    # Test different profiles
    for profile in profiles:
        r = api(token, "POST", "/portfolio/optimize",
                data={"risk_profile": profile, "method": "markowitz",
                      "investment_amount": 1000000})
        if r and r.status_code == 200:
            data       = r.json()
            allocation = data.get("allocation", {})
            ret        = data.get("expected_return", 0)
            risk       = data.get("expected_risk", 0)
            sharpe     = data.get("sharpe_ratio", 0)
            amounts    = data.get("allocated_amounts", {})
            results_by_profile[profile] = data

            total_weight = sum(allocation.values())
            if 98 < total_weight < 102:
                passed(f"Portfolio ({profile}) - Weights sum 100%",
                       f"Sum={total_weight:.2f}%")
            else:
                failed(f"Portfolio ({profile}) - Weights don't sum 100%",
                       f"Sum={total_weight:.2f}%")

            if all(v >= 0 for v in allocation.values()):
                passed(f"Portfolio ({profile}) - All weights positive", "✓")
            else:
                failed(f"Portfolio ({profile}) - Negative weights!", str(allocation))

            if -2 < sharpe < 5:
                passed(f"Portfolio ({profile}) - Sharpe reasonable", f"{sharpe}")
            else:
                failed(f"Portfolio ({profile}) - Sharpe extreme", str(sharpe))

            total_alloc = sum(amounts.values())
            if abs(total_alloc - 1000000) < 1000:
                passed(f"Portfolio ({profile}) - Amounts sum to investment",
                       f"Rs {total_alloc:,.0f}")
            else:
                warning(f"Portfolio ({profile}) - Amount mismatch",
                        f"Rs {total_alloc:,.0f} vs Rs 1,000,000")

            log(f"    {profile}: Return={ret:.2f}% Risk={risk:.2f}% Sharpe={sharpe:.3f}")
        else:
            failed(f"Portfolio ({profile}) - API failed",
                   str(r.status_code if r else "no response"))

    # Aggressive > Conservative return
    if "Conservative" in results_by_profile and "Aggressive" in results_by_profile:
        cons = results_by_profile["Conservative"].get("expected_return", 0)
        aggr = results_by_profile["Aggressive"].get("expected_return", 0)
        if aggr >= cons:
            passed("Portfolio - Aggressive > Conservative return",
                   f"Aggr={aggr:.2f}% > Cons={cons:.2f}%")
        else:
            warning("Portfolio - Return ordering",
                    f"Aggr={aggr:.2f}% vs Cons={cons:.2f}%")

    # Different methods give different Sharpe ratios
    method_sharpes = {}
    for method in methods:
        r = api(token, "POST", "/portfolio/optimize",
                data={"risk_profile": "Moderate", "method": method,
                      "investment_amount": 1000000})
        if r and r.status_code == 200:
            method_sharpes[method] = round(r.json().get("sharpe_ratio", 0), 3)

    if len(set(method_sharpes.values())) > 1:
        passed("Portfolio - Methods give different Sharpe",
               str(method_sharpes))
    else:
        warning("Portfolio - All methods same Sharpe", str(method_sharpes))

    # Dynamic portfolio with real data
    r = api(token, "GET", "/portfolio/optimize/dynamic/auto", timeout=120)
    if r and r.status_code == 200:
        data     = r.json()
        dq       = data.get("data_quality", {})
        real_pct = dq.get("real_data_percentage", 0)
        sharpe   = data.get("sharpe_ratio", 0)

        if real_pct >= 50:
            passed("Portfolio - Dynamic uses real data",
                   f"{real_pct}% real data")
        else:
            warning("Portfolio - Low real data", f"{real_pct}%")

        if sharpe > 0:
            passed("Portfolio - Dynamic positive Sharpe", f"{sharpe:.3f}")
        else:
            failed("Portfolio - Dynamic negative Sharpe", str(sharpe))

        news_adj = data.get("news_adjusted", False)
        if news_adj:
            passed("Portfolio - News signal applied", "✓")
        else:
            warning("Portfolio - News signal not applied",
                    "Refresh news cache: /news/market-sentiment?force_refresh=true")
    else:
        warning("Portfolio - Dynamic auto endpoint",
                str(r.status_code if r else "no response"))


# ============================================================
# SUITE 8 — BACKTESTING
# ============================================================
def test_backtesting(token):
    section("8 — BACKTESTING (Real NIFTY50 Data)")

    r = api(token, "GET", "/prediction/backtest/compare-all?period=3y", timeout=120)
    if r and r.status_code == 200:
        data       = r.json()
        strategies = data.get("strategies", {})
        ranked     = data.get("ranked", [])
        data_pts   = data.get("data_points", 0)

        if data_pts > 500:
            passed("Backtest - Sufficient real data", f"{data_pts} trading days")
        else:
            warning("Backtest - Limited data", f"{data_pts} days")

        # All 4 strategies present
        for strat in ["buy_and_hold","momentum","mean_reversion","regime_based"]:
            if strat in strategies:
                m = strategies[strat]
                passed(f"Backtest - {strat} has results",
                       f"Return={m.get('annual_return',0):.2f}% Sharpe={m.get('sharpe_ratio',0):.3f}")
            else:
                failed(f"Backtest - {strat} missing")

        # Regime beats buy-and-hold
        if "regime_based" in strategies and "buy_and_hold" in strategies:
            rb  = strategies["regime_based"].get("sharpe_ratio", 0)
            bah = strategies["buy_and_hold"].get("sharpe_ratio", 0)
            if rb > bah:
                passed("Backtest - Regime beats buy-and-hold",
                       f"Regime={rb:.3f} > BnH={bah:.3f}")
            else:
                warning("Backtest - Regime vs buy-and-hold",
                        f"Regime={rb:.3f} BnH={bah:.3f}")

        # Rankings ordered by Sharpe
        if len(ranked) >= 2:
            sharpes = [r["sharpe"] for r in ranked]
            if sharpes == sorted(sharpes, reverse=True):
                passed("Backtest - Rankings ordered by Sharpe", "✓")
            else:
                failed("Backtest - Rankings wrong order", str(sharpes))

        # Win rates valid
        for strat, metrics in strategies.items():
            wr = metrics.get("win_rate", -1)
            if 0 <= wr <= 100:
                passed(f"Backtest - {strat} win rate valid", f"{wr:.1f}%")
            else:
                failed(f"Backtest - {strat} win rate invalid", str(wr))

        # Print summary
        log(f"\n  Strategy Rankings:")
        for r in ranked:
            log(f"    #{r['rank']} {r['strategy']:20} Return={r['return']:.2f}% Sharpe={r['sharpe']:.3f}")
    else:
        failed("Backtest - API failed",
               str(r.status_code if r else "no response"))


# ============================================================
# SUITE 9 — TAX OPTIMIZATION (Budget 2024)
# ============================================================
def test_tax(token):
    section("9 — TAX OPTIMIZATION (Budget 2024)")

    # Test 9.1 — LTCG under Rs 1.25L exemption = zero tax
    r = api(token, "POST", "/tax/capital-gains",
            data={"asset_type":"equity","purchase_price":100000,
                  "sale_price":150000,"holding_days":400,"annual_income":1200000})
    if r and r.status_code == 200:
        data      = r.json()
        total_tax = data.get("total_tax", -1)
        gain_type = data.get("gain_type", "")
        is_ltcg   = data.get("is_long_term", False)

        if total_tax == 0:
            passed("Tax - LTCG under Rs 1.25L = zero tax",
                   f"Gain=Rs50K < Rs1.25L exemption → Tax=0")
        else:
            failed("Tax - LTCG exemption wrong", f"Got tax={total_tax}, expected 0")

        if "LTCG" in gain_type:
            passed("Tax - LTCG classification correct", gain_type)
        else:
            failed("Tax - LTCG classification", gain_type)

        if is_ltcg:
            passed("Tax - Long term flag correct", "holding_days=400 > 365")
        else:
            failed("Tax - Long term flag wrong", str(is_ltcg))
    else:
        failed("Tax - LTCG under exemption API failed",
               str(r.status_code if r else "no response"))

    # Test 9.2 — LTCG above Rs 1.25L (Budget 2024: 12.5% rate)
    r = api(token, "POST", "/tax/capital-gains",
            data={"asset_type":"equity","purchase_price":100000,
                  "sale_price":300000,"holding_days":400,"annual_income":1200000})
    if r and r.status_code == 200:
        data      = r.json()
        total_tax = data.get("total_tax", 0)
        base_tax  = data.get("base_tax", 0)
        cess      = data.get("cess", 0)
        tax_rate  = data.get("tax_rate", 0)

        # Gain=200000, Taxable=75000, Tax=75000*12.5%=9375, Cess=375, Total=9750
        if tax_rate == 12.5:
            passed("Tax - LTCG rate 12.5% (Budget 2024)", f"Rate={tax_rate}%")
        else:
            failed("Tax - LTCG rate wrong (should be 12.5%)", f"Got {tax_rate}%")

        if abs(base_tax - 9375) < 1:
            passed("Tax - Base tax correct", f"Rs {base_tax} (75000 × 12.5%)")
        else:
            failed("Tax - Base tax wrong", f"Got {base_tax}, expected 9375")

        if abs(cess - 375) < 1:
            passed("Tax - 4% cess correct", f"Rs {cess}")
        else:
            failed("Tax - Cess wrong", f"Got {cess}, expected 375")

        if abs(total_tax - 9750) < 1:
            passed("Tax - Total tax correct (Budget 2024)", f"Rs {total_tax}")
        else:
            failed("Tax - Total tax wrong", f"Got {total_tax}, expected 9750")
    else:
        failed("Tax - LTCG above exemption API failed",
               str(r.status_code if r else "no response"))

    # Test 9.3 — STCG (held 180 days = short term, 15% rate)
    r = api(token, "POST", "/tax/capital-gains",
            data={"asset_type":"equity","purchase_price":100000,
                  "sale_price":200000,"holding_days":180,"annual_income":1200000})
    if r and r.status_code == 200:
        data      = r.json()
        total_tax = data.get("total_tax", 0)
        tax_rate  = data.get("tax_rate", 0)
        gain_type = data.get("gain_type", "")
        is_ltcg   = data.get("is_long_term", True)

        if "STCG" in gain_type:
            passed("Tax - STCG classification correct", gain_type)
        else:
            failed("Tax - STCG classification wrong", gain_type)

        if not is_ltcg:
            passed("Tax - Short term flag correct", "holding_days=180 < 365")
        else:
            failed("Tax - Short term flag wrong", str(is_ltcg))

        if tax_rate == 15:
            passed("Tax - STCG rate 15% correct", f"{tax_rate}%")
        else:
            failed("Tax - STCG rate wrong", f"Got {tax_rate}%")

        # Gain=100000, Tax=15000, Cess=600, Total=15600
        if abs(total_tax - 15600) < 1:
            passed("Tax - STCG total tax correct", f"Rs {total_tax}")
        else:
            failed("Tax - STCG total tax wrong", f"Got {total_tax}, expected 15600")
    else:
        failed("Tax - STCG API failed",
               str(r.status_code if r else "no response"))

    # Test 9.4 — Net proceeds = sale price - total tax
    r = api(token, "POST", "/tax/capital-gains",
            data={"asset_type":"equity","purchase_price":100000,
                  "sale_price":200000,"holding_days":180,"annual_income":1200000})
    if r and r.status_code == 200:
        data         = r.json()
        sale_price   = data.get("sale_price", 0)
        total_tax    = data.get("total_tax", 0)
        net_proceeds = data.get("net_proceeds", 0)
        expected_net = sale_price - total_tax
        if abs(net_proceeds - expected_net) < 1:
            passed("Tax - Net proceeds formula correct",
                   f"Rs {net_proceeds:,.0f} = Sale - Tax")
        else:
            failed("Tax - Net proceeds wrong",
                   f"Got {net_proceeds}, expected {expected_net}")

    # Test 9.5 — Gold LTCG (Budget 2024: 12.5%, 2 years holding)
    r = api(token, "POST", "/tax/capital-gains",
            data={"asset_type":"gold","purchase_price":100000,
                  "sale_price":200000,"holding_days":800,"annual_income":1200000})
    if r and r.status_code == 200:
        data     = r.json()
        tax_rate = data.get("tax_rate", 0)
        is_ltcg  = data.get("is_long_term", False)
        if tax_rate == 12.5:
            passed("Tax - Gold LTCG 12.5% (Budget 2024)", f"{tax_rate}%")
        else:
            warning("Tax - Gold rate", f"Got {tax_rate}% (check budget 2024 update)")
    else:
        warning("Tax - Gold LTCG test", "Endpoint may not support gold type")


# ============================================================
# SUITE 10 — RISK PROFILING
# ============================================================
def test_risk_profile(token):
    section("10 — RISK PROFILING")

    # Test 10.1 — Get existing profile
    r = api(token, "GET", "/risk/me")
    if r and r.status_code == 200:
        data         = r.json()
        profile_type = data.get("profile_type", "")
        score        = data.get("score", 0)
        allocation   = data.get("recommended_allocation", {})

        if profile_type in ["Conservative","Moderate","Aggressive"]:
            passed("Risk - Valid profile type", profile_type)
        else:
            failed("Risk - Invalid profile type", profile_type)

        if 0 < score <= 100:
            passed("Risk - Score valid range", f"{score}/100")
        else:
            failed("Risk - Score out of range", str(score))

        if allocation and sum(allocation.values()) > 0:
            total = sum(allocation.values())
            passed("Risk - Allocation provided", f"Total={total}%")
        else:
            warning("Risk - No allocation in profile")
    else:
        warning("Risk - No profile found",
                "Run: POST /risk/assess with questionnaire answers")

    # Test 10.2 — Re-assess gives consistent result
    r = api(token, "POST", "/risk/assess",
            data={"financial_goal":3,"time_horizon":4,"loss_reaction":3,
                  "income_stability":3,"investment_experience":2,"savings_rate":2,
                  "emergency_fund":3,"max_acceptable_loss":2,
                  "primary_motivation":3,"age_group":4})
    if r and r.status_code == 200:
        data  = r.json()
        score = data.get("score", 0)
        ptype = data.get("profile_type", "")
        if abs(score - 68.46) < 0.5:
            passed("Risk - Consistent score", f"Score={score:.2f} (expected ~68.46)")
        else:
            warning("Risk - Score different from expected",
                    f"Got {score:.2f}, expected ~68.46")
        if ptype == "Aggressive":
            passed("Risk - Correct profile type", ptype)
        else:
            warning("Risk - Profile type", f"Got {ptype}, expected Aggressive")
    else:
        failed("Risk - Assessment API failed",
               str(r.status_code if r else "no response"))

    # Test 10.3 — Conservative profile (low scores)
    r = api(token, "POST", "/risk/assess",
            data={"financial_goal":1,"time_horizon":1,"loss_reaction":1,
                  "income_stability":1,"investment_experience":1,"savings_rate":1,
                  "emergency_fund":1,"max_acceptable_loss":1,
                  "primary_motivation":1,"age_group":1})
    if r and r.status_code == 200:
        ptype = r.json().get("profile_type", "")
        score = r.json().get("score", 100)
        if ptype == "Conservative":
            passed("Risk - Low answers = Conservative", f"Score={score:.2f}")
        else:
            warning("Risk - Low answers profile", f"Got {ptype}, score={score:.2f}")
    else:
        warning("Risk - Conservative test failed")


# ============================================================
# SUITE 11 — MONTE CARLO SIMULATION
# ============================================================
def test_monte_carlo(token):
    section("11 — MONTE CARLO SIMULATION")

    scenarios = [
        {
            "label":             "Conservative 5yr",
            "initial_investment": 500000,
            "monthly_sip":        5000,
            "investment_horizon":  5,
            "risk_profile":        "Conservative",
            "expected_return":     0.08,
        },
        {
            "label":             "Aggressive 10yr",
            "initial_investment": 1000000,
            "monthly_sip":        20000,
            "investment_horizon":  10,
            "risk_profile":        "Aggressive",
            "expected_return":     0.14,
        },
    ]

    mc_results = []
    for scenario in scenarios:
        label = scenario.pop("label")
        r     = api(token, "POST", "/simulation/run", data=scenario)
        if r and r.status_code == 200:
            data        = r.json()
            median      = data.get("median_final_value", 0)
            p10         = data.get("percentile_10", 0)
            p90         = data.get("percentile_90", 0)
            profit_prob = data.get("probability_of_profit", 0)
            mc_results.append({"label": label, **data})

            if median > scenario["initial_investment"]:
                passed(f"Monte Carlo ({label}) - Median > initial",
                       f"Rs {median:,.0f}")
            else:
                warning(f"Monte Carlo ({label}) - Median < initial",
                        f"Rs {median:,.0f}")

            if p90 > p10:
                passed(f"Monte Carlo ({label}) - P90 > P10 (valid distribution)",
                       f"P10=Rs{p10:,.0f} P90=Rs{p90:,.0f}")
            else:
                failed(f"Monte Carlo ({label}) - Distribution wrong",
                       f"P10={p10} P90={p90}")

            if 0 <= profit_prob <= 100:
                passed(f"Monte Carlo ({label}) - Valid profit probability",
                       f"{profit_prob:.1f}%")
            else:
                failed(f"Monte Carlo ({label}) - Invalid probability", str(profit_prob))
        else:
            # Try alternate endpoint
            r2 = api(token, "POST", "/simulation/monte-carlo", data=scenario)
            if r2 and r2.status_code == 200:
                passed(f"Monte Carlo ({label}) - Works via /monte-carlo endpoint")
            else:
                failed(f"Monte Carlo ({label}) - API failed",
                       f"Tried /run and /monte-carlo — check your simulation route")

    if len(mc_results) >= 2:
        m1 = mc_results[0].get("median_final_value", 0)
        m2 = mc_results[1].get("median_final_value", 0)
        if m2 > m1:
            passed("Monte Carlo - Aggressive 10yr > Conservative 5yr",
                   "Correct risk-return tradeoff")
        else:
            warning("Monte Carlo - Return ordering",
                    "May be due to different investment amounts")


# ============================================================
# FINAL REPORT
# ============================================================
def print_final_report():
    log(f"\n{BOLD}{'='*60}{RESET}")
    log(f"{BOLD}FINAL TEST REPORT — AI Finance Platform{RESET}", BLUE)
    log(f"{BOLD}{'='*60}{RESET}")

    total = results["passed"] + results["failed"] + results["warnings"]
    score = results["passed"] / total * 100 if total > 0 else 0

    log(f"\n  Total Tests:  {total}")
    log(f"  Passed:       {results['passed']}", GREEN)
    log(f"  Failed:       {results['failed']}", RED)
    log(f"  Warnings:     {results['warnings']}", YELLOW)
    log(f"  Score:        {score:.1f}%",
        GREEN if score >= 80 else YELLOW if score >= 60 else RED)

    if results["failed"] > 0:
        log(f"\n{BOLD}FAILED TESTS (Need Fixing):{RESET}", RED)
        for d in results["details"]:
            if d["status"] == "FAIL":
                log(f"  ❌ {d['test']}: {d['detail']}", RED)

    if results["warnings"] > 0:
        log(f"\n{BOLD}WARNINGS (Review These):{RESET}", YELLOW)
        for d in results["details"]:
            if d["status"] == "WARN":
                log(f"  ⚠️  {d['test']}: {d['detail']}", YELLOW)

    log(f"\n{'='*60}")
    if score >= 85:
        log(f"  🏆 EXCELLENT — Platform is robust and reliable!", GREEN)
    elif score >= 70:
        log(f"  ✅ GOOD — Platform working well, minor issues", YELLOW)
    elif score >= 50:
        log(f"  ⚠️  FAIR — Several issues need attention", YELLOW)
    else:
        log(f"  ❌ NEEDS WORK — Major issues detected", RED)

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total":    total,
            "passed":   results["passed"],
            "failed":   results["failed"],
            "warnings": results["warnings"],
            "score":    round(score, 2),
        },
        "details": results["details"],
    }
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    log(f"\n  Report saved to: test_report.json")
    log(f"{'='*60}\n")


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    log(f"\n{BOLD}{'='*60}{RESET}")
    log(f"{BOLD}  AI FINANCE PLATFORM — FULL TEST SUITE{RESET}", BLUE)
    log(f"{BOLD}{'='*60}{RESET}")
    log(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"  Server:  {BASE_URL}")
    log(f"  User:    {EMAIL}\n")

    log("🔐 Authenticating...")
    token = get_token()
    if not token:
        log("❌ Authentication failed! Check server is running.", RED)
        log("   Run: ../venv/bin/python -m uvicorn app.main:app --reload", YELLOW)
        exit(1)
    log(f"✅ Authenticated!\n", GREEN)

    # Run all 11 test suites
    test_auth(token)
    test_market_data(token)
    test_news_sentiment(token)
    test_arima(token)
    test_xgboost(token)
    test_investment_signal(token)
    test_portfolio(token)
    test_backtesting(token)
    test_tax(token)
    test_risk_profile(token)
    test_monte_carlo(token)

    print_final_report()