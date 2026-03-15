from pydantic import BaseModel
from typing import Optional, Dict, List

class CapitalGainsTaxRequest(BaseModel):
    asset_type:     str
    purchase_price: float
    sale_price:     float
    holding_days:   int
    annual_income:  float = 1000000
    tax_regime:     str   = "new_regime"

class Section80CRequest(BaseModel):
    annual_income:       float
    current_investments: Dict[str, float]
    tax_regime:          str = "old_regime"

class HoldingItem(BaseModel):
    name:           str
    asset_type:     str
    purchase_value: float
    current_value:  float
    holding_days:   int

class TaxLossHarvestingRequest(BaseModel):
    holdings:      List[HoldingItem]
    annual_income: float = 1000000

class AfterTaxPortfolio(BaseModel):
    name:           str
    pre_tax_return: float
    asset_type:     str   = "equity"
    holding_days:   int   = 400
    investment:     float = 100000

class AfterTaxComparisonRequest(BaseModel):
    portfolios:    List[AfterTaxPortfolio]
    annual_income: float = 1000000
    tax_regime:    str   = "new_regime"