from typing import Dict, List
import numpy as np

# ---------------------------------------------------------------------------
# Indian Tax Rules — Updated for Budget 2024
# ---------------------------------------------------------------------------
TAX_RULES = {
    "equity": {
        "ltcg_rate":           0.125,  # Budget 2024: changed from 10% to 12.5%
        "stcg_rate":           0.15,   # Unchanged
        "ltcg_exemption":      125000, # Budget 2024: changed from 1L to 1.25L
        "holding_period_days": 365,
        "note":                "Budget 2024: LTCG 12.5%, STCG 15%, Exemption Rs 1.25L/FY",
    },
    "debt": {
        "ltcg_rate":           None,   # Taxed at slab rate after April 2023
        "stcg_rate":           None,   # Taxed at slab rate
        "holding_period_days": 365,
        "note":                "Debt fund gains taxed at income slab rate from April 2023",
    },
    "gold": {
        "ltcg_rate":           0.125,  # Budget 2024: changed from 20% to 12.5% (no indexation)
        "stcg_rate":           None,   # Taxed at slab rate
        "holding_period_days": 730,    # Budget 2024: changed from 3 years to 2 years
        "indexation":          False,  # Budget 2024: indexation removed
        "note":                "Budget 2024: Gold LTCG 12.5% without indexation, holding 2 years",
    },
    "hybrid": {
        "ltcg_rate":           0.125,  # Budget 2024: updated to 12.5%
        "stcg_rate":           0.15,   # Unchanged
        "holding_period_days": 365,
    },
}

INCOME_TAX_SLABS = {
    "new_regime": [
        {"min": 0,        "max": 300000,       "rate": 0.00},
        {"min": 300000,   "max": 700000,       "rate": 0.05},
        {"min": 700000,   "max": 1000000,      "rate": 0.10},
        {"min": 1000000,  "max": 1200000,      "rate": 0.15},
        {"min": 1200000,  "max": 1500000,      "rate": 0.20},
        {"min": 1500000,  "max": float("inf"), "rate": 0.30},
    ],
    "old_regime": [
        {"min": 0,        "max": 250000,       "rate": 0.00},
        {"min": 250000,   "max": 500000,       "rate": 0.05},
        {"min": 500000,   "max": 1000000,      "rate": 0.20},
        {"min": 1000000,  "max": float("inf"), "rate": 0.30},
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

# Budget 2024 key changes summary
BUDGET_2024_CHANGES = {
    "equity_ltcg":       "Increased from 10% to 12.5%",
    "equity_stcg":       "Unchanged at 15%",
    "ltcg_exemption":    "Increased from Rs 1L to Rs 1.25L per FY",
    "gold_ltcg":         "Changed from 20% (with indexation) to 12.5% (without indexation)",
    "gold_holding":      "Reduced from 3 years to 2 years for LTCG",
    "debt_funds":        "No change — taxed at slab rate since April 2023",
    "effective_date":    "23 July 2024",
}


# ---------------------------------------------------------------------------
# Income Tax Calculator
# ---------------------------------------------------------------------------
def calculate_income_tax(
    annual_income: float,
    regime:        str = "new_regime",
) -> Dict:
    slabs     = INCOME_TAX_SLABS[regime]
    tax       = 0.0
    breakdown = []

    for slab in slabs:
        if annual_income > slab["min"]:
            taxable_in_slab = min(annual_income, slab["max"]) - slab["min"]
            tax_in_slab     = taxable_in_slab * slab["rate"]
            tax            += tax_in_slab
            if tax_in_slab > 0:
                breakdown.append({
                    "slab":    f"Rs {slab['min']:,.0f} - Rs {slab['max']:,.0f}" if slab["max"] != float("inf") else f"Above Rs {slab['min']:,.0f}",
                    "rate":    f"{slab['rate']*100:.0f}%",
                    "taxable": round(taxable_in_slab, 2),
                    "tax":     round(tax_in_slab, 2),
                })

    cess           = tax * 0.04
    total_tax      = tax + cess
    effective_rate = (total_tax / annual_income * 100) if annual_income > 0 else 0

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
# Capital Gains Tax Calculator — Budget 2024 Updated
# ---------------------------------------------------------------------------
def calculate_capital_gains_tax(
    asset_type:               str,
    purchase_price:           float,
    sale_price:               float,
    holding_days:             int,
    annual_income:            float = 1000000,
    tax_regime:               str   = "new_regime",
    inflation_index_purchase: float = 100,
    inflation_index_sale:     float = 100,
) -> Dict:
    """
    Calculates capital gains tax per Indian tax law.
    Updated for Budget 2024 (effective 23 July 2024):
    - Equity LTCG: 12.5% (was 10%)
    - Equity STCG: 15% (unchanged)
    - LTCG Exemption: Rs 1.25L/FY (was Rs 1L)
    - Gold LTCG: 12.5% without indexation, holding period 2 years (was 3 years)
    - Debt: Slab rate (unchanged since April 2023)

    Important: Rs 1.25L exemption is per FINANCIAL YEAR, not per transaction.
    """
    gain = sale_price - purchase_price

    if gain <= 0:
        return {
            "asset_type":     asset_type,
            "purchase_price": purchase_price,
            "sale_price":     sale_price,
            "gain":           round(gain, 2),
            "gain_type":      "Loss — No Tax",
            "is_long_term":   False,
            "holding_days":   holding_days,
            "tax_rate":       0.0,
            "base_tax":       0.0,
            "cess":           0.0,
            "total_tax":      0.0,
            "net_proceeds":   round(sale_price, 2),
            "budget_2024":    BUDGET_2024_CHANGES,
        }

    rules          = TAX_RULES.get(asset_type, TAX_RULES["equity"])
    holding_period = rules["holding_period_days"]
    is_long_term   = holding_days >= holding_period

    if asset_type == "equity":
        if is_long_term:
            # Budget 2024: LTCG exempt up to Rs 1.25L per FY
            # Note: This exemption is shared across ALL equity gains in the FY
            taxable_gain = max(0, gain - rules["ltcg_exemption"])
            tax_rate     = rules["ltcg_rate"]   # 12.5%
            tax          = taxable_gain * tax_rate
            gain_type    = "LTCG (Long Term Capital Gain)"
        else:
            taxable_gain = gain
            tax_rate     = rules["stcg_rate"]   # 15%
            tax          = taxable_gain * tax_rate
            gain_type    = "STCG (Short Term Capital Gain)"

    elif asset_type == "debt":
        # Taxed at income slab rate (no separate LTCG/STCG distinction post April 2023)
        income_tax   = calculate_income_tax(annual_income + gain, tax_regime)
        base_tax_val = calculate_income_tax(annual_income, tax_regime)
        tax          = income_tax["total_tax"] - base_tax_val["total_tax"]
        tax_rate     = (tax / gain) if gain > 0 else 0
        taxable_gain = gain
        gain_type    = "Debt Fund Gain (Slab Rate — post April 2023)"

    elif asset_type == "gold":
        if is_long_term:
            # Budget 2024: 12.5% WITHOUT indexation (holding 2+ years)
            taxable_gain = gain  # No indexation benefit post Budget 2024
            tax_rate     = rules["ltcg_rate"]   # 12.5%
            tax          = taxable_gain * tax_rate
            gain_type    = "LTCG Gold (12.5% — Budget 2024, no indexation)"
        else:
            # STCG gold: slab rate
            income_tax   = calculate_income_tax(annual_income + gain, tax_regime)
            base_tax_val = calculate_income_tax(annual_income, tax_regime)
            tax          = income_tax["total_tax"] - base_tax_val["total_tax"]
            tax_rate     = (tax / gain) if gain > 0 else 0
            taxable_gain = gain
            gain_type    = "STCG Gold (Slab Rate)"

    elif asset_type == "hybrid":
        if is_long_term:
            taxable_gain = gain
            tax_rate     = rules["ltcg_rate"]   # 12.5%
            tax          = taxable_gain * tax_rate
            gain_type    = "LTCG Hybrid Fund"
        else:
            taxable_gain = gain
            tax_rate     = rules["stcg_rate"]   # 15%
            tax          = taxable_gain * tax_rate
            gain_type    = "STCG Hybrid Fund"

    else:
        # Default: treat as equity
        if is_long_term:
            taxable_gain = max(0, gain - 125000)
            tax_rate     = 0.125
            tax          = taxable_gain * tax_rate
            gain_type    = "LTCG"
        else:
            taxable_gain = gain
            tax_rate     = 0.15
            tax          = taxable_gain * tax_rate
            gain_type    = "STCG"

    # 4% health & education cess on all taxes
    cess      = tax * 0.04
    total_tax = tax + cess

    return {
        "asset_type":     asset_type,
        "purchase_price": purchase_price,
        "sale_price":     sale_price,
        "gain":           round(gain, 2),
        "taxable_gain":   round(float(taxable_gain), 2),
        "gain_type":      gain_type,
        "is_long_term":   is_long_term,
        "holding_days":   holding_days,
        "ltcg_exemption": rules.get("ltcg_exemption", 0) if is_long_term else 0,
        "tax_rate":       round(float(tax_rate) * 100, 2),
        "base_tax":       round(float(tax), 2),
        "cess":           round(float(cess), 2),
        "total_tax":      round(float(total_tax), 2),
        "net_proceeds":   round(sale_price - total_tax, 2),
        "budget_2024_note": "LTCG 12.5%, STCG 15%, Exemption Rs 1.25L/FY (effective 23 Jul 2024)",
    }


# ---------------------------------------------------------------------------
# Multi-Transaction Tax Calculator (FY level exemption)
# ---------------------------------------------------------------------------
def calculate_multi_transaction_tax(
    transactions:  List[Dict],
    annual_income: float = 1000000,
    tax_regime:    str   = "new_regime",
) -> Dict:
    """
    Calculates tax across multiple transactions sharing the Rs 1.25L exemption.
    This is the CORRECT way to calculate tax — exemption is per FY not per transaction.

    Example:
        Gain 1 = Rs 70,000
        Gain 2 = Rs 80,000
        Total  = Rs 1,50,000
        Taxable = 1,50,000 - 1,25,000 = Rs 25,000
        Tax    = 12.5% x 25,000 = Rs 3,125
    """
    LTCG_EXEMPTION = 125000  # Rs 1.25L per FY — shared across all LTCG transactions
    LTCG_RATE      = 0.125
    STCG_RATE      = 0.15
    CESS_RATE      = 0.04

    total_ltcg  = 0.0
    total_stcg  = 0.0
    results     = []

    for txn in transactions:
        gain         = txn["sale_price"] - txn["purchase_price"]
        is_long_term = txn["holding_days"] >= 365

        if gain > 0:
            if is_long_term:
                total_ltcg += gain
            else:
                total_stcg += gain

        results.append({
            "name":          txn.get("name", "Transaction"),
            "gain":          round(gain, 2),
            "is_long_term":  is_long_term,
            "gain_type":     "LTCG" if is_long_term else "STCG",
        })

    # Apply shared exemption to total LTCG
    taxable_ltcg = max(0, total_ltcg - LTCG_EXEMPTION)
    ltcg_tax     = taxable_ltcg * LTCG_RATE
    stcg_tax     = total_stcg * STCG_RATE
    total_tax_before_cess = ltcg_tax + stcg_tax
    cess         = total_tax_before_cess * CESS_RATE
    total_tax    = total_tax_before_cess + cess

    return {
        "transactions":       results,
        "total_ltcg":         round(total_ltcg, 2),
        "total_stcg":         round(total_stcg, 2),
        "ltcg_exemption_used": min(total_ltcg, LTCG_EXEMPTION),
        "taxable_ltcg":       round(taxable_ltcg, 2),
        "ltcg_tax":           round(ltcg_tax, 2),
        "stcg_tax":           round(stcg_tax, 2),
        "cess":               round(cess, 2),
        "total_tax":          round(total_tax, 2),
        "note":               "Rs 1.25L LTCG exemption is per FY and shared across all equity transactions",
        "budget_2024":        "LTCG 12.5%, STCG 15%, Exemption Rs 1.25L/FY",
    }


# ---------------------------------------------------------------------------
# Section 80C Optimizer
# ---------------------------------------------------------------------------
def optimize_80c_deductions(
    annual_income:       float,
    current_investments: Dict[str, float],
    tax_regime:          str = "old_regime",
) -> Dict:
    total_80c_limit  = 150000
    total_invested   = sum(current_investments.values())
    remaining_limit  = max(0, total_80c_limit - total_invested)

    tax_before       = calculate_income_tax(annual_income, tax_regime)
    taxable_after    = max(0, annual_income - min(total_invested, total_80c_limit))
    tax_after        = calculate_income_tax(taxable_after, tax_regime)
    tax_saved        = tax_before["total_tax"] - tax_after["total_tax"]

    recommendations  = []
    if remaining_limit > 0:
        recommendations.append({
            "instrument": "ELSS",
            "amount":     min(remaining_limit, 150000),
            "benefit":    "Tax saving + equity returns — best of both worlds",
            "lock_in":    "3 years (shortest among 80C options)",
        })
        recommendations.append({
            "instrument": "PPF",
            "amount":     min(remaining_limit, 150000),
            "benefit":    "Tax-free interest + maturity, government backed",
            "lock_in":    "15 years",
        })
        recommendations.append({
            "instrument": "NPS (80CCD(1B))",
            "amount":     min(50000, remaining_limit),
            "benefit":    "Additional Rs 50,000 deduction OVER the Rs 1.5L 80C limit",
            "lock_in":    "Till retirement age 60",
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
# Tax Loss Harvesting — Budget 2024 Updated
# ---------------------------------------------------------------------------
def calculate_tax_loss_harvesting(
    holdings:      List[Dict],
    annual_income: float = 1000000,
) -> Dict:
    """
    Identifies loss-making holdings to offset gains.
    Updated for Budget 2024: uses 12.5% LTCG rate.
    """
    LTCG_RATE      = 0.125   # Budget 2024 updated rate
    LTCG_EXEMPTION = 125000  # Budget 2024 updated exemption
    CESS_RATE      = 0.04

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

    # Tax calculations with Budget 2024 rates
    taxable_without = max(0, total_gains - LTCG_EXEMPTION)
    tax_without     = taxable_without * LTCG_RATE * (1 + CESS_RATE)

    taxable_with    = max(0, net_gain - LTCG_EXEMPTION)
    tax_with        = taxable_with * LTCG_RATE * (1 + CESS_RATE)

    tax_saved       = tax_without - tax_with

    return {
        "total_gains":              round(total_gains, 2),
        "total_harvestable_losses": round(total_losses, 2),
        "net_taxable_gain":         round(net_gain, 2),
        "tax_without_harvesting":   round(tax_without, 2),
        "tax_with_harvesting":      round(tax_with, 2),
        "tax_saved":                round(tax_saved, 2),
        "loss_holdings":            losses,
        "gain_holdings":            gains,
        "ltcg_rate_used":           "12.5% (Budget 2024)",
        "recommendation":           f"Harvest losses to save Rs {tax_saved:,.0f} in taxes this year.",
    }


# ---------------------------------------------------------------------------
# After-Tax Return Comparison — Budget 2024 Updated
# ---------------------------------------------------------------------------
def compare_after_tax_returns(
    portfolios:    List[Dict],
    annual_income: float = 1000000,
    tax_regime:    str   = "new_regime",
) -> Dict:
    results = []
    for p in portfolios:
        pre_tax_return = p["pre_tax_return"]
        asset_type     = p.get("asset_type", "equity")
        holding_days   = p.get("holding_days", 400)
        investment     = p.get("investment", 100000)

        gain    = investment * pre_tax_return
        cg_tax  = calculate_capital_gains_tax(
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
            "name":               p["name"],
            "pre_tax_return":     round(pre_tax_return * 100, 2),
            "after_tax_return":   round(after_tax_return * 100, 2),
            "tax_paid":           round(cg_tax["total_tax"], 2),
            "effective_tax_rate": round(cg_tax["total_tax"] / gain * 100, 2) if gain > 0 else 0,
            "gain_type":          cg_tax.get("gain_type", ""),
        })

    results.sort(key=lambda x: x["after_tax_return"], reverse=True)

    return {
        "comparison":    results,
        "recommended":   results[0]["name"] if results else None,
        "note":          "Recommendation based on highest after-tax return (Budget 2024 rates)",
        "budget_2024":   "LTCG 12.5%, STCG 15%, Exemption Rs 1.25L/FY",
    }