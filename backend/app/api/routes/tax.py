from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.tax import (
    CapitalGainsTaxRequest,
    Section80CRequest,
    TaxLossHarvestingRequest,
    AfterTaxComparisonRequest,
)
from app.services.tax_service import (
    calculate_income_tax,
    calculate_capital_gains_tax,
    optimize_80c_deductions,
    calculate_tax_loss_harvesting,
    compare_after_tax_returns,
    TAX_RULES,
    SECTION_80C_INSTRUMENTS,
)

router = APIRouter()


@router.get("/rules")
def get_tax_rules(
    current_user: User = Depends(get_current_active_user),
):
    """Returns all Indian tax rules for investments."""
    return {
        "capital_gains": TAX_RULES,
        "section_80c_instruments": SECTION_80C_INSTRUMENTS,
        "key_rules": [
            "Equity LTCG (>1 year): 10% above ₹1.25L exemption",
            "Equity STCG (<1 year): 15%",
            "Debt funds: Taxed at income slab rate (post 2023)",
            "Gold LTCG (>3 years): 20% with indexation",
            "Section 80C: Up to ₹1.5L deduction",
            "NPS 80CCD: Additional ₹50,000 deduction",
            "4% Health & Education cess on all taxes",
        ],
    }


@router.post("/capital-gains")
def calculate_cg_tax(
    request: CapitalGainsTaxRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Calculate capital gains tax on investment."""
    return calculate_capital_gains_tax(
        asset_type=request.asset_type,
        purchase_price=request.purchase_price,
        sale_price=request.sale_price,
        holding_days=request.holding_days,
        annual_income=request.annual_income,
        tax_regime=request.tax_regime,
    )


@router.post("/income-tax")
def calculate_tax(
    annual_income: float,
    regime: str = "new_regime",
    current_user: User = Depends(get_current_active_user),
):
    """Calculate income tax for given income."""
    return calculate_income_tax(annual_income, regime)


@router.post("/optimize-80c")
def optimize_80c(
    request: Section80CRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Optimize Section 80C deductions."""
    return optimize_80c_deductions(
        annual_income=request.annual_income,
        current_investments=request.current_investments,
        tax_regime=request.tax_regime,
    )


@router.post("/tax-loss-harvesting")
def tax_loss_harvest(
    request: TaxLossHarvestingRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Identify tax loss harvesting opportunities."""
    holdings = [h.model_dump() for h in request.holdings]
    return calculate_tax_loss_harvesting(holdings, request.annual_income)


@router.post("/after-tax-comparison")
def after_tax_comparison(
    request: AfterTaxComparisonRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Compare portfolios by after-tax returns."""
    portfolios = [p.model_dump() for p in request.portfolios]
    return compare_after_tax_returns(
        portfolios=portfolios,
        annual_income=request.annual_income,
        tax_regime=request.tax_regime,
    )