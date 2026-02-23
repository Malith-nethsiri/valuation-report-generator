from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    message: str


class TemplateMetadata(BaseModel):
    """Metadata for a letterhead template"""
    template_id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Display name of the template")
    description: str = Field(..., description="Description of the template's visual style")
    category: str = Field(default="professional", description="Template category")


class TemplateListResponse(BaseModel):
    """Response containing list of available templates"""
    templates: list = Field(..., description="List of available letterhead templates")


class JobCreate(BaseModel):
    """Schema for creating a new background job."""
    report_id: int = Field(..., description="ID of the report to generate document for")
    job_type: str = Field(
        default="docx_generation",
        pattern="^(docx_generation|pdf_generation)$",
        description="Type of job to create"
    )


class JobResponse(BaseModel):
    """Schema for job status responses."""
    id: str = Field(..., description="Unique job identifier (UUID)")
    user_id: int
    report_id: Optional[int] = None
    job_type: str
    status: str = Field(..., description="Job status: pending, processing, completed, failed")
    result_url: Optional[str] = Field(None)
    result_filename: Optional[str] = Field(None)
    error_message: Optional[str] = Field(None)
    progress_percent: Optional[int] = Field(None, ge=0, le=100)
    progress_message: Optional[str] = Field(None)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobStatusResponse(BaseModel):
    """Simplified job status response for polling."""
    id: str
    status: str
    progress_percent: Optional[int] = 0
    progress_message: Optional[str] = None
    error_message: Optional[str] = None
    download_ready: bool = False
    download_url: Optional[str] = None
    filename: Optional[str] = None
