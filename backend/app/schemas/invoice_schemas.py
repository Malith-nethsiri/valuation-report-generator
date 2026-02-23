from pydantic import BaseModel, Field
from typing import Optional, List


class InvoiceItem(BaseModel):
    """Individual line item in a professional fee invoice"""
    description: str = Field(..., description="Service description (e.g., 'Valuation of Property 1')")
    total: float = Field(..., ge=0, description="Direct price for this line item")


class InvoiceData(BaseModel):
    """Professional fee invoice data for single or multi-property reports"""
    items: List[InvoiceItem] = Field(default_factory=list)
    subtotal: float = Field(default=0, ge=0)
    traveling_charges: Optional[float] = Field(None, ge=0)
    discount: Optional[float] = Field(None, ge=0)
    total: float = Field(..., ge=0)
    bank_account_ids: List[str] = Field(default_factory=list)
    manual_bank_details: Optional[str] = Field(None)
