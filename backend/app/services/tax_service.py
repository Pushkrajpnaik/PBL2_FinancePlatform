from typing import Dict, List
import numpy as np

# ---------------------------------------------------------------------------
# Indian Tax Rules 2024
# ---------------------------------------------------------------------------
TAX_RULES = {
    "equity": {
        "ltcg_rate":          0.10,   # Long term capital gains > 1 year
        "stcg_rate":          0.15,   # Short term capital gains < 1 year
        "ltcg_exemption":     125000, # LTCG exempt up to 1.25L per year
        "holding_period_days": 365,
    },
    "debt": {
        "ltcg_rate":          None,   # Taxed at slab rate after 2023
        "stcg_rate":          None,   # Taxed at slab rate
        "holding_period_days": 365,
        "note":               "Debt fund gains taxed at income slab rate from 2023",
    },
    "gold": {
        "ltcg_rate":          0.20,   # With indexation benefit
        "stcg_rate":          None,   # Taxed at slab rate
        "holding_period_days": 1095,  # 3 years for LTCG
        "indexation":         True,
    },
    "hybrid": {
        "ltcg_rate":          0.10,
        "stcg_rate":          0.15,
        "holding_period_days": 365,
    },
}

INCOME_TAX_SLABS = {
    "new_regime": [
        {"min": 0,       "max": 300000,   "rate": 0.00},
        {"min": 300000,  "max": 700000,   "rate": 0.05},
        {"min": 700000,  "max": 1000000,  "rate": 0.10},
        {"min": 1000000, "max": 1200000,  "rate": 0.15},
        {"min": 1200000, "max": 1500000,  "rate": 0.20},
        {"min": 1500000, "max": float("inf"), "rate": 0.30},
    ],
    "old_regime": [
        {"min": 0,       "max": 250000,   "rate": 0.00},
        {"min": 250000,  "max": 500000,   "rate": 0.05},
        {"min": 500000,  "max": 1000000,  "rate": 0.20},
        {"min": 1000000, "max": float("inf"), "rate": 0.30},
    ],
}

SECTION_80C_INSTRUMENTS = {
    "elss":         {"limit": 150000, "lock_in_years": 3,  "description": "Equity Linked Savings Scheme"},
    "ppf":          {"limit": 150000, "lock_in_years": 15, "description": "Public Provident Fund"},
    "epf":          {"limit": 150000, "lock_in_years": 0,  "description": "Employee Provident Fund"},
    "nsc":          {"limit": 150000, "lock_in_years": 5,  "description": "National Savings Certificate"},
    "tax_saver_fd": {"limit": 150000, "lock_in_years": 5,  "description": "Tax Saver Fixed Deposit"},
    "nps":          {"limit": 200000, "lock_in_years": 0,  "description": "National Pension System (80CCD)"},
    "lic":          {"limit": 150000, "lock_in_years": 0,  "description": "Life Insurance Premium"},
}


# ---------------------------------------------------------------------------
# Income Tax Calculator
# ---------------------------------------------------------------------------
def calculate_income_tax(
    annual_income: float,
    regime: str = "new_regime",
) -> Dict:
    slabs    = INCOME_TAX_SLABS[regime]
    tax      = 0.0
    breakdown = []

    for slab in slabs:
        if annual_income > slab["min"]:
            taxable_in_slab = min(annual_income, slab["max"]) - slab["min"]
            tax_in_slab     = taxable_in_slab * slab["rate"]
            tax            += tax_in_slab
            if tax_in_slab > 0:
                breakdown.append({
                    "slab":    f"₹{slab['min']:,.0f} - ₹{slab['max']:,.0f}" if slab["max"] != float("inf") else f"Above ₹{slab['min']:,.0f}",
                    "rate":    f"{slab['rate']*100:.0f}%",
                    "taxable": round(taxable_in_slab, 2),
                    "tax":     round(tax_in_slab, 2),
                })

    # 4% health & education cess
    cess            = tax * 0.04
    total_tax       = tax + cess
    effective_rate  = (total_tax / annual_income * 100) if annual_income > 0 else 0

    return {
        "annual_income":  annual_income,
        "regime":         regime,
        "base_tax":       round(tax, 2),
        "cess":           round(cess, 2),
        "total_tax":      round(total_tax, 2),
        "effective_rate": round(effective_rate, 2),
        "breakdown":      breakdown,
    }


# ---------------------------------------------------------------------------
# Capital Gains Tax Calculator
# ---------------------------------------------------------------------------
def calculate_capital_gains_tax(
    asset_type:        str,
    purchase_price:    float,
    sale_price:        float,
    holding_days:      int,
    annual_income:     float = 1000000,
    tax_regime:        str   = "new_regime",
    inflation_index_purchase: float = 100,
    inflation_index_sale:     float = 100,
) -> Dict:
    gain = sale_price - purchase_price

    if gain <= 0:
        return {
            "asset_type":    asset_type,
            "purchase_price": purchase_price,
            "sale_price":    sale_price,
            "gain":          round(gain, 2),
            "tax":           0.0,
            "gain_type":     "Loss — No Tax",
            "tax_rate":      0.0,
            "net_proceeds":  round(sale_price, 2),
        }

    rules              = TAX_RULES.get(asset_type, TAX_RULES["equity"])
    holding_period     = rules["holding_period_days"]
    is_long_term       = holding_days >= holding_period

    if asset_type == "equity":
        if is_long_term:
            # LTCG exemption of 1.25L
            taxable_gain = max(0, gain - rules["ltcg_exemption"])
            tax_rate     = rules["ltcg_rate"]
            tax          = taxable_gain * tax_rate
            gain_type    = "LTCG (Long Term Capital Gain)"
        else:
            tax_rate  = rules["stcg_rate"]
            tax       = gain * tax_rate
            gain_type = "STCG (Short Term Capital Gain)"

    elif asset_type == "debt":
        # Taxed at slab rate
        income_tax = calculate_income_tax(annual_income + gain, tax_regime)
        base_tax   = calculate_income_tax(annual_income, tax_regime)
        tax        = income_tax["total_tax"] - base_tax["total_tax"]
        tax_rate   = (tax / gain) if gain > 0 else 0
        gain_type  = "Debt Fund Gain (Slab Rate)"

    elif asset_type == "gold":
        if is_long_term:
            # With indexation
            indexed_cost = purchase_price * (inflation_index_sale / inflation_index_purchase)
            taxable_gain = max(0, sale_price - indexed_cost)
            tax_rate     = rules["ltcg_rate"]
            tax          = taxable_gain * tax_rate
            gain_type    = "LTCG with Indexation"
        else:
            income_tax = calculate_income_tax(annual_income + gain, tax_regime)
            base_tax   = calculate_income_tax(annual_income, tax_regime)
            tax        = income_tax["total_tax"] - base_tax["total_tax"]
            tax_rate   = (tax / gain) if gain > 0 else 0
            gain_type  = "STCG (Slab Rate)"
    else:
        tax_rate  = rules.get("ltcg_rate", 0.10) if is_long_term else rules.get("stcg_rate", 0.15)
        tax       = gain * tax_rate
        gain_type = "LTCG" if is_long_term else "STCG"

    # Add 4% cess
    cess      = tax * 0.04
    total_tax = tax + cess

    return {
        "asset_type":    asset_type,
        "purchase_price": purchase_price,
        "sale_price":    sale_price,
        "gain":          round(gain, 2),
        "gain_type":     gain_type,
        "is_long_term":  is_long_term,
        "holding_days":  holding_days,
        "tax_rate":      round(float(tax_rate) * 100, 2),
        "base_tax":      round(float(tax), 2),
        "cess":          round(float(cess), 2),
        "total_tax":     round(float(total_tax), 2),
        "net_proceeds":  round(sale_price - total_tax, 2),
    }


# ---------------------------------------------------------------------------
# Section 80C Optimizer
# ---------------------------------------------------------------------------
def optimize_80c_deductions(
    annual_income:    float,
    current_investments: Dict[str, float],
    tax_regime:       str = "old_regime",
) -> Dict:
    total_80c_limit   = 150000
    total_invested    = sum(current_investments.values())
    remaining_limit   = max(0, total_80c_limit - total_invested)

    # Tax before optimization
    tax_before = calculate_income_tax(annual_income, tax_regime)

    # Tax after full 80C utilization
    taxable_after = max(0, annual_income - min(total_invested, total_80c_limit))
    tax_after     = calculate_income_tax(taxable_after, tax_regime)

    tax_saved = tax_before["total_tax"] - tax_after["total_tax"]

    recommendations = []
    if remaining_limit > 0:
        recommendations.append({
            "instrument":  "ELSS",
            "amount":      min(remaining_limit, 150000),
            "benefit":     "Tax saving + equity returns (best of both)",
            "lock_in":     "3 years",
        })
        recommendations.append({
            "instrument":  "PPF",
            "amount":      min(remaining_limit, 150000),
            "benefit":     "Tax-free interest + maturity",
            "lock_in":     "15 years",
        })
        recommendations.append({
            "instrument":  "NPS (80CCD)",
            "amount":      min(50000, remaining_limit),
            "benefit":     "Additional ₹50,000 deduction over 80C limit",
            "lock_in":     "Till retirement",
        })

    return {
        "annual_income":       annual_income,
        "total_80c_invested":  total_invested,
        "80c_limit":           total_80c_limit,
        "remaining_80c_limit": remaining_limit,
        "tax_before_80c":      tax_before["total_tax"],
        "tax_after_80c":       tax_after["total_tax"],
        "tax_saved":           round(tax_saved, 2),
        "recommendations":     recommendations,
        "instruments":         SECTION_80C_INSTRUMENTS,
    }


# ---------------------------------------------------------------------------
# Tax Loss Harvesting
# ---------------------------------------------------------------------------
def calculate_tax_loss_harvesting(
    holdings: List[Dict],
    annual_income: float = 1000000,
) -> Dict:
    """
    Identifies loss-making holdings that can be sold to offset gains.
    """
    gains  = []
    losses = []

    for h in holdings:
        pnl = h["current_value"] - h["purchase_value"]
        if pnl > 0:
            gains.append({**h, "pnl": pnl})
        else:
            losses.append({**h, "pnl": pnl})

    total_gains  = sum(g["pnl"] for g in gains)
    total_losses = abs(sum(l["pnl"] for l in losses))
    net_gain     = max(0, total_gains - total_losses)

    # Tax on gross gains
    tax_without_harvesting = total_gains * 0.10
    # Tax after harvesting
    tax_with_harvesting    = net_gain * 0.10
    tax_saved              = tax_without_harvesting - tax_with_harvesting

    return {
        "total_gains":              round(total_gains, 2),
        "total_harvestable_losses": round(total_losses, 2),
        "net_taxable_gain":         round(net_gain, 2),
        "tax_without_harvesting":   round(tax_without_harvesting, 2),
        "tax_with_harvesting":      round(tax_with_harvesting, 2),
        "tax_saved":                round(tax_saved, 2),
        "loss_holdings":            losses,
        "gain_holdings":            gains,
        "recommendation":           f"Harvest losses to save ₹{tax_saved:,.0f} in taxes this year.",
    }


# ---------------------------------------------------------------------------
# After-Tax Return Comparison
# ---------------------------------------------------------------------------
def compare_after_tax_returns(
    portfolios: List[Dict],
    annual_income: float = 1000000,
    tax_regime: str = "new_regime",
) -> Dict:
    results = []
    for p in portfolios:
        pre_tax_return  = p["pre_tax_return"]
        asset_type      = p.get("asset_type", "equity")
        holding_days    = p.get("holding_days", 400)
        investment      = p.get("investment", 100000)

        gain            = investment * pre_tax_return
        cg_tax          = calculate_capital_gains_tax(
            asset_type=asset_type,
            purchase_price=investment,
            sale_price=investment + gain,
            holding_days=holding_days,
            annual_income=annual_income,
            tax_regime=tax_regime,
        )

        after_tax_gain   = gain - cg_tax["total_tax"]
        after_tax_return = after_tax_gain / investment

        results.append({
            "name":             p["name"],
            "pre_tax_return":   round(pre_tax_return * 100, 2),
            "after_tax_return": round(after_tax_return * 100, 2),
            "tax_paid":         round(cg_tax["total_tax"], 2),
            "effective_tax_rate": round(cg_tax["total_tax"] / gain * 100, 2) if gain > 0 else 0,
        })

    # Sort by after-tax return
    results.sort(key=lambda x: x["after_tax_return"], reverse=True)
    return {
        "comparison":  results,
        "recommended": results[0]["name"] if results else None,
        "note":        "Recommendation based on highest after-tax return",
    }