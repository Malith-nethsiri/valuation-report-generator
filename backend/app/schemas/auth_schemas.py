from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional, List

from .validators import _validate_password_common


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    honorific: Optional[str] = Field(None, max_length=10, description="Title/Honorific (e.g., Mr., Mrs., Dr.)")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")

    academic_qualifications: Optional[str] = Field(None, description="Academic qualifications (e.g., B.Sc Estate Management)")
    membership_level: Optional[str] = Field(None, max_length=100, description="Professional membership level (e.g., Fellow Member)")
    membership_number: Optional[str] = Field(None, max_length=100, description="Membership number")
    professional_designation: Optional[str] = Field(None, max_length=200, description="Professional designation (e.g., Chartered Valuer)")
    panel_valuer_banks: Optional[List[str]] = Field(None, description="List of banks where appointed as panel valuer")

    house_number: Optional[str] = Field(None, max_length=50, description="House number (e.g., No:43)")
    area_development: Optional[str] = Field(None, max_length=100, description="Area/Development name (e.g., Highway City)")
    village: Optional[str] = Field(None, max_length=100, description="Village name")
    locality: Optional[str] = Field(None, max_length=100, description="Locality name")
    phone_primary: Optional[str] = Field(None, max_length=50, description="Primary phone number")
    phone_secondary: Optional[str] = Field(None, max_length=50, description="Secondary phone number")

    office_department: Optional[str] = Field(None, max_length=200, description="Office department")
    office_region: Optional[str] = Field(None, max_length=100, description="Office region/province")
    office_street_city: Optional[str] = Field(None, max_length=200, description="Office street and city")
    office_phone: Optional[str] = Field(None, max_length=50, description="Office phone number")

    preferred_letterhead_template: Optional[str] = Field(None, max_length=50, description="Preferred letterhead template ID (e.g., 'classic', 'modern')")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters, must include uppercase, lowercase, digit, and special character)")

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        return _validate_password_common(v)


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class UserResponse(UserBase):
    id: int
    role: str = Field(default="user", description="User role: 'user' or 'admin'")
    email_verified: bool = Field(default=False, description="Whether email has been verified")
    created_at: datetime
    updated_at: Optional[datetime] = None
    bank_accounts: Optional[List["BankAccount"]] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    honorific: Optional[str] = Field(None, max_length=10)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)

    academic_qualifications: Optional[str] = None
    membership_level: Optional[str] = Field(None, max_length=100)
    membership_number: Optional[str] = Field(None, max_length=100)
    professional_designation: Optional[str] = Field(None, max_length=200)
    panel_valuer_banks: Optional[List[str]] = None

    house_number: Optional[str] = Field(None, max_length=50)
    area_development: Optional[str] = Field(None, max_length=100)
    village: Optional[str] = Field(None, max_length=100)
    locality: Optional[str] = Field(None, max_length=100)
    phone_primary: Optional[str] = Field(None, max_length=50)
    phone_secondary: Optional[str] = Field(None, max_length=50)

    office_department: Optional[str] = Field(None, max_length=200)
    office_region: Optional[str] = Field(None, max_length=100)
    office_street_city: Optional[str] = Field(None, max_length=200)
    office_phone: Optional[str] = Field(None, max_length=50)

    preferred_letterhead_template: Optional[str] = Field(None, max_length=50)

    bank_accounts: Optional[List["BankAccount"]] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="The refresh token to use for getting a new access token")


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class BankAccount(BaseModel):
    id: str = Field(..., description="Unique identifier (UUID)")
    bank_name: str = Field(..., min_length=1, max_length=200, description="Bank name")
    account_number: str = Field(..., min_length=1, max_length=50, description="Account number")
    branch_name: str = Field(..., min_length=1, max_length=200, description="Branch name")


class BankAccountCreate(BaseModel):
    bank_name: str = Field(..., min_length=1, max_length=200)
    account_number: str = Field(..., min_length=1, max_length=50)
    branch_name: str = Field(..., min_length=1, max_length=200)


class BankAccountUpdate(BaseModel):
    bank_name: Optional[str] = Field(None, min_length=1, max_length=200)
    account_number: Optional[str] = Field(None, min_length=1, max_length=50)
    branch_name: Optional[str] = Field(None, min_length=1, max_length=200)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to send reset link to")


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address associated with the account")
    token: str = Field(..., min_length=20, description="Password reset token from email")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        return _validate_password_common(v)


class PasswordResetResponse(BaseModel):
    success: bool
    message: str


class SendVerificationRequest(BaseModel):
    pass


class VerifyEmailRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to verify")
    token: str = Field(..., min_length=20, description="Verification token from email")


class EmailVerificationResponse(BaseModel):
    success: bool
    message: str
    email_verified: bool = Field(..., description="Whether the email is now verified")


class RoleUpdate(BaseModel):
    """Schema for admin role update endpoint."""
    role: str = Field(..., description="New role: 'user' or 'admin'")


class GoogleAuthUrlResponse(BaseModel):
    """Response containing Google OAuth authorization URL."""
    authorization_url: str = Field(..., description="Google OAuth authorization URL")
    state: str = Field(..., description="CSRF state token")


class GoogleCallbackRequest(BaseModel):
    """Request body for Google OAuth callback."""
    code: str
    state: str
