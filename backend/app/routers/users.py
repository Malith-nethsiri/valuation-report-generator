"""
User profile and bank account router.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas, crud
from ..auth import get_current_user
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


@router.put("/api/profile", response_model=schemas.UserResponse)
async def update_profile(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    updated_user = crud.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@router.get("/api/users/me/bank-accounts", response_model=List[schemas.BankAccount])
async def get_my_bank_accounts(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bank accounts for the current user."""
    accounts = crud.get_bank_accounts(db, current_user.id)
    return accounts or []


@router.post("/api/users/me/bank-accounts", response_model=schemas.BankAccount, status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    account: schemas.BankAccountCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a new bank account."""
    new_account = crud.add_bank_account(db, current_user.id, account)
    if not new_account:
        raise HTTPException(status_code=500, detail="Failed to create bank account")
    return new_account


@router.patch("/api/users/me/bank-accounts/{account_id}", response_model=schemas.BankAccount)
async def update_bank_account(
    account_id: str,
    account_update: schemas.BankAccountUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing bank account."""
    updated_account = crud.update_bank_account(db, current_user.id, account_id, account_update)
    if not updated_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    return updated_account


@router.delete("/api/users/me/bank-accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bank_account(
    account_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a bank account."""
    success = crud.delete_bank_account(db, current_user.id, account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    return None


@router.get("/api/letterhead-templates", response_model=schemas.TemplateListResponse)
async def get_letterhead_templates():
    """Get all available letterhead templates."""
    from ..letterhead_templates import get_all_templates
    templates = get_all_templates()
    return {"templates": [t.to_dict() for t in templates]}
