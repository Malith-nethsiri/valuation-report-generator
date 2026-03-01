"""
User and bank account CRUD operations.
"""
import uuid
from sqlalchemy.orm import Session

from .. import models, schemas
from ..utils.password_utils import get_password_hash


def create_user(db: Session, user: schemas.UserCreate):
    """Create a new user with hashed password"""
    hashed_password = get_password_hash(user.password)
    user_data = user.model_dump(exclude={"password"})
    db_user = models.User(password_hash=hashed_password, **user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: int):
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    """Update user information"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def add_bank_account(db: Session, user_id: int, account: schemas.BankAccountCreate):
    """Add a new bank account to user profile"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    if db_user.bank_accounts is None:
        db_user.bank_accounts = []

    new_account = {
        "id": str(uuid.uuid4()),
        "bank_name": account.bank_name,
        "account_number": account.account_number,
        "branch_name": account.branch_name
    }

    accounts = db_user.bank_accounts.copy() if db_user.bank_accounts else []
    accounts.append(new_account)
    db_user.bank_accounts = accounts

    db.commit()
    db.refresh(db_user)
    return new_account


def update_bank_account(db: Session, user_id: int, account_id: str,
                        account_update: schemas.BankAccountUpdate):
    """Update an existing bank account"""
    db_user = get_user(db, user_id)
    if not db_user or not db_user.bank_accounts:
        return None

    accounts = db_user.bank_accounts.copy()
    account_found = False

    for account in accounts:
        if account["id"] == account_id:
            update_data = account_update.model_dump(exclude_unset=True)
            account.update(update_data)
            account_found = True
            break

    if not account_found:
        return None

    db_user.bank_accounts = accounts
    db.commit()
    db.refresh(db_user)

    return next(acc for acc in accounts if acc["id"] == account_id)


def delete_bank_account(db: Session, user_id: int, account_id: str):
    """Delete a bank account"""
    db_user = get_user(db, user_id)
    if not db_user or not db_user.bank_accounts:
        return False

    accounts = [acc for acc in db_user.bank_accounts if acc["id"] != account_id]

    if len(accounts) == len(db_user.bank_accounts):
        return False  # Account not found

    db_user.bank_accounts = accounts
    db.commit()
    return True


def get_bank_accounts(db: Session, user_id: int):
    """Get all bank accounts for a user"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    return db_user.bank_accounts or []
