from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

class ReportBase(BaseModel):
    name: str = Field(..., description="Report name")
    report_type: str = Field(..., description="Type of report: performance, engagement, financial, category, custom")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Report generation parameters")

class ReportCreate(ReportBase):
    brand_id: UUID = Field(..., description="Brand ID for the report")

class ReportUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    error_message: Optional[str] = None

class ReportResponse(ReportBase):
    id: UUID
    brand_id: UUID
    status: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    generated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class ReportTemplateBase(BaseModel):
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    report_type: str = Field(..., description="Type of report this template generates")
    template_config: Dict[str, Any] = Field(..., description="Configuration for report generation")

class ReportTemplateCreate(ReportTemplateBase):
    pass

class ReportTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ReportTemplateResponse(ReportTemplateBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

class ReportGenerationRequest(BaseModel):
    brand_id: UUID = Field(..., description="Brand ID for the report")
    template_id: Optional[UUID] = Field(None, description="Template ID to use for generation")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="Custom configuration overrides")
    start_date: Optional[str] = Field(None, description="Start date for report period (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date for report period (YYYY-MM-DD)")

class ReportStatsResponse(BaseModel):
    total_reports: int
    ready_reports: int
    processing_reports: int
    failed_reports: int
    this_month: int 