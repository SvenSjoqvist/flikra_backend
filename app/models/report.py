from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base
import uuid

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)  # 'performance', 'engagement', 'financial', 'category', 'custom'
    status = Column(String(20), default="processing")  # 'processing', 'ready', 'failed'
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    generated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    parameters = Column(JSON, nullable=True)  # Report generation parameters
    error_message = Column(Text, nullable=True)
    
    # Relationships
    brand = relationship("Brand", back_populates="reports")
    
    def __repr__(self):
        return f"<Report(id={self.id}, name='{self.name}', type='{self.report_type}', status='{self.status}')>"

class ReportTemplate(Base):
    __tablename__ = "report_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(String(50), nullable=False)
    template_config = Column(JSON, nullable=False)  # Configuration for report generation
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ReportTemplate(id={self.id}, name='{self.name}', type='{self.report_type}')>" 