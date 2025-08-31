from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

from app.db import get_db
from app.models import Report, ReportTemplate, Brand, User, Product, Swipe, BrandAnalyticsEvent
from app.schemas import (
    ReportCreate, ReportResponse, ReportUpdate, ReportListResponse,
    ReportTemplateCreate, ReportTemplateResponse, ReportTemplateUpdate,
    ReportGenerationRequest, ReportStatsResponse
)
from app.services.pdf_service import generate_pdf_report

router = APIRouter()

# Create reports directory if it doesn't exist
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

def generate_report_data(brand_id: UUID, report_type: str, start_date: datetime, end_date: datetime, db: Session) -> dict:
    """Generate report data based on type and date range"""
    
    # Base query filters
    base_filters = [
        Product.brand_id == brand_id,
        Swipe.created_at >= start_date,
        Swipe.created_at <= end_date
    ]
    
    if report_type == "performance":
        # Performance report - product performance metrics
        product_stats = db.query(
            Product.id,
            Product.name,
            func.count(Swipe.id).label('total_swipes'),
            func.count(case((Swipe.action == 'like', 1))).label('likes'),
            func.count(case((Swipe.action == 'dislike', 1))).label('dislikes')
        ).join(Swipe).filter(
            and_(*base_filters)
        ).group_by(
            Product.id, Product.name
        ).order_by(
            func.count(Swipe.id).desc()
        ).all()
        
        # Calculate conversion rates
        products_data = []
        for product in product_stats:
            conversion_rate = (product.likes / product.total_swipes * 100) if product.total_swipes > 0 else 0
            products_data.append({
                "product_id": str(product.id),
                "product_name": product.name,
                "total_swipes": product.total_swipes,
                "likes": product.likes,
                "dislikes": product.dislikes,
                "conversion_rate": round(conversion_rate, 2)
            })
        
        return {
            "report_type": "performance",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_products": len(products_data),
            "products": products_data,
            "summary": {
                "total_swipes": sum(p["total_swipes"] for p in products_data),
                "total_likes": sum(p["likes"] for p in products_data),
                "total_dislikes": sum(p["dislikes"] for p in products_data),
                "overall_conversion_rate": round(
                    sum(p["likes"] for p in products_data) / sum(p["total_swipes"] for p in products_data) * 100, 2
                ) if sum(p["total_swipes"] for p in products_data) > 0 else 0
            }
        }
    
    elif report_type == "engagement":
        # Engagement report - user interaction patterns
        daily_activity = db.query(
            func.date(Swipe.created_at).label('date'),
            func.count(Swipe.id).label('swipes'),
            func.count(func.distinct(Swipe.user_id)).label('active_users')
        ).join(Product).filter(
            and_(*base_filters)
        ).group_by(
            func.date(Swipe.created_at)
        ).order_by(
            func.date(Swipe.created_at)
        ).all()
        
        # User engagement metrics
        total_users = db.query(func.count(func.distinct(Swipe.user_id))).join(Product).filter(
            and_(*base_filters)
        ).scalar() or 0
        
        return {
            "report_type": "engagement",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "daily_activity": [
                {
                    "date": str(day.date),
                    "swipes": day.swipes,
                    "active_users": day.active_users
                }
                for day in daily_activity
            ],
            "summary": {
                "total_unique_users": total_users,
                "total_swipes": sum(day.swipes for day in daily_activity),
                "avg_swipes_per_user": round(
                    sum(day.swipes for day in daily_activity) / total_users, 2
                ) if total_users > 0 else 0
            }
        }
    
    elif report_type == "financial":
        # Financial report - revenue and conversion metrics (simplified)
        # In a real app, you'd have actual revenue data
        conversion_data = db.query(
            func.count(Swipe.id).label('total_swipes'),
            func.count(case((Swipe.action == 'like', 1))).label('conversions'),
            func.count(func.distinct(Swipe.user_id)).label('unique_customers')
        ).join(Product).filter(
            and_(*base_filters)
        ).first()
        
        conversion_rate = (conversion_data.conversions / conversion_data.total_swipes * 100) if conversion_data.total_swipes > 0 else 0
        
        return {
            "report_type": "financial",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "metrics": {
                "total_swipes": conversion_data.total_swipes,
                "conversions": conversion_data.conversions,
                "conversion_rate": round(conversion_rate, 2),
                "unique_customers": conversion_data.unique_customers,
                "avg_conversion_value": 25.00,  # Placeholder
                "estimated_revenue": round(conversion_data.conversions * 25.00, 2)  # Placeholder
            }
        }
    
    elif report_type == "category":
        # Category analysis report
        category_stats = db.query(
            Product.category,
            func.count(Swipe.id).label('total_swipes'),
            func.count(case((Swipe.action == 'like', 1))).label('likes'),
            func.count(func.distinct(Product.id)).label('products_count')
        ).join(Swipe).filter(
            and_(*base_filters)
        ).group_by(
            Product.category
        ).order_by(
            func.count(Swipe.id).desc()
        ).all()
        
        return {
            "report_type": "category",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "categories": [
                {
                    "category": cat.category,
                    "total_swipes": cat.total_swipes,
                    "likes": cat.likes,
                    "products_count": cat.products_count,
                    "conversion_rate": round(cat.likes / cat.total_swipes * 100, 2) if cat.total_swipes > 0 else 0
                }
                for cat in category_stats
            ]
        }
    
    else:
        # Custom report - basic analytics
        return {
            "report_type": "custom",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "basic_metrics": {
                "total_swipes": db.query(func.count(Swipe.id)).join(Product).filter(and_(*base_filters)).scalar() or 0,
                "total_likes": db.query(func.count(Swipe.id)).join(Product).filter(
                    and_(*base_filters, Swipe.action == 'like')
                ).scalar() or 0,
                "unique_users": db.query(func.count(func.distinct(Swipe.user_id))).join(Product).filter(
                    and_(*base_filters)
                ).scalar() or 0
            }
        }

def generate_report_file(report_id: UUID, brand_id: UUID, report_type: str, start_date: datetime, end_date: datetime, db: Session):
    """Background task to generate report files"""
    try:
        # Generate report data
        report_data = generate_report_data(brand_id, report_type, start_date, end_date, db)
        
        # Create JSON file
        json_filename = f"report_{report_id}_{report_type}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        json_path = REPORTS_DIR / json_filename
        
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Generate PDF file
        pdf_path = generate_pdf_report(report_data, str(report_id), report_type)
        
        # Update report status
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.status = "ready"
            report.file_path = str(json_path)  # Keep JSON as primary
            report.file_size = json_path.stat().st_size
            report.completed_at = datetime.utcnow()
            # Add PDF path to parameters
            if not report.parameters:
                report.parameters = {}
            report.parameters['pdf_path'] = str(pdf_path)
            db.commit()
            
    except Exception as e:
        # Update report with error
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.status = "failed"
            report.error_message = str(e)
            db.commit()

@router.get("/brand/{brand_id}", response_model=ReportListResponse)
def get_reports(
    brand_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    report_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all reports for a brand with pagination and filtering"""
    
    # Validate brand exists
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Build query
    query = db.query(Report).filter(Report.brand_id == brand_id)
    
    if status:
        query = query.filter(Report.status == status)
    
    if report_type:
        query = query.filter(Report.report_type == report_type)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    reports = query.order_by(desc(Report.generated_at)).offset((page - 1) * per_page).limit(per_page).all()
    
    return ReportListResponse(
        reports=reports,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page
    )

@router.get("/brand/{brand_id}/stats", response_model=ReportStatsResponse)
def get_report_stats(brand_id: UUID, db: Session = Depends(get_db)):
    """Get report statistics for a brand"""
    
    # Validate brand exists
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Get current month
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    
    # Calculate stats
    total_reports = db.query(func.count(Report.id)).filter(Report.brand_id == brand_id).scalar() or 0
    ready_reports = db.query(func.count(Report.id)).filter(
        and_(Report.brand_id == brand_id, Report.status == "ready")
    ).scalar() or 0
    processing_reports = db.query(func.count(Report.id)).filter(
        and_(Report.brand_id == brand_id, Report.status == "processing")
    ).scalar() or 0
    failed_reports = db.query(func.count(Report.id)).filter(
        and_(Report.brand_id == brand_id, Report.status == "failed")
    ).scalar() or 0
    this_month = db.query(func.count(Report.id)).filter(
        and_(Report.brand_id == brand_id, Report.generated_at >= month_start)
    ).scalar() or 0
    
    return ReportStatsResponse(
        total_reports=total_reports,
        ready_reports=ready_reports,
        processing_reports=processing_reports,
        failed_reports=failed_reports,
        this_month=this_month
    )

@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    report: ReportCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new report"""
    
    # Validate brand exists
    brand = db.query(Brand).filter(Brand.id == report.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Create report record
    db_report = Report(
        brand_id=report.brand_id,
        name=report.name,
        report_type=report.report_type,
        parameters=report.parameters,
        status="processing"
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    # Determine date range from parameters or use default
    end_date = datetime.utcnow()
    if report.parameters and "end_date" in report.parameters:
        end_date = datetime.fromisoformat(report.parameters["end_date"])
    
    start_date = end_date - timedelta(days=30)  # Default to 30 days
    if report.parameters and "start_date" in report.parameters:
        start_date = datetime.fromisoformat(report.parameters["start_date"])
    
    # Start background task to generate report
    background_tasks.add_task(
        generate_report_file,
        db_report.id,
        report.brand_id,
        report.report_type,
        start_date,
        end_date,
        db
    )
    
    return db_report

@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Generate a report using a template or custom configuration"""
    
    # Validate brand exists
    brand = db.query(Brand).filter(Brand.id == request.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Get template if provided
    template = None
    if request.template_id:
        template = db.query(ReportTemplate).filter(
            and_(ReportTemplate.id == request.template_id, ReportTemplate.is_active == True)
        ).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
    
    # Determine report configuration
    if template:
        config = template.template_config.copy()
        if request.custom_config:
            config.update(request.custom_config)
        report_type = template.report_type
        name = f"{template.name} - {datetime.utcnow().strftime('%Y-%m-%d')}"
    else:
        config = request.custom_config or {}
        report_type = config.get("report_type", "custom")
        name = config.get("name", f"Custom Report - {datetime.utcnow().strftime('%Y-%m-%d')}")
    
    # Create report record
    db_report = Report(
        brand_id=request.brand_id,
        name=name,
        report_type=report_type,
        parameters=config,
        status="processing"
    )
    
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    
    # Determine date range
    end_date = datetime.utcnow()
    if request.end_date:
        end_date = datetime.fromisoformat(request.end_date)
    
    start_date = end_date - timedelta(days=30)
    if request.start_date:
        start_date = datetime.fromisoformat(request.start_date)
    
    # Start background task
    background_tasks.add_task(
        generate_report_file,
        db_report.id,
        request.brand_id,
        report_type,
        start_date,
        end_date,
        db
    )
    
    return db_report

# Template endpoints - MUST come BEFORE generic routes to avoid conflicts
@router.get("/templates", response_model=List[ReportTemplateResponse])
@router.get("/templates/", response_model=List[ReportTemplateResponse])
def get_report_templates(db: Session = Depends(get_db)):
    """Get all available report templates"""
    
    templates = db.query(ReportTemplate).filter(ReportTemplate.is_active == True).all()
    return templates

@router.post("/templates/", response_model=ReportTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_report_template(template: ReportTemplateCreate, db: Session = Depends(get_db)):
    """Create a new report template"""
    
    db_template = ReportTemplate(**template.dict())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    return db_template

@router.get("/templates/{template_id}", response_model=ReportTemplateResponse)
def get_report_template(template_id: UUID, db: Session = Depends(get_db)):
    """Get a specific report template"""
    
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template

@router.put("/templates/{template_id}", response_model=ReportTemplateResponse)
def update_report_template(
    template_id: UUID,
    template_update: ReportTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a report template"""
    
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    for field, value in template_update.dict(exclude_unset=True).items():
        setattr(template, field, value)
    
    template.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(template)
    
    return template

# Generic report routes - MUST come AFTER specific routes
@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: UUID, db: Session = Depends(get_db)):
    """Get a specific report by ID"""
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report

@router.get("/{report_id}/download")
def download_report(report_id: UUID, db: Session = Depends(get_db)):
    """Download a report file"""
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != "ready":
        raise HTTPException(status_code=400, detail="Report is not ready for download")
    
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    # Return the actual file for download
    filename = f"report_{report_id}_{report.report_type}_{datetime.now().strftime('%Y%m%d')}.json"
    
    return FileResponse(
        path=report.file_path,
        filename=filename,
        media_type='application/json',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

@router.get("/{report_id}/download-pdf")
def download_pdf_report(report_id: UUID, db: Session = Depends(get_db)):
    """Download a report as PDF"""
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != "ready":
        raise HTTPException(status_code=400, detail="Report is not ready for download")
    
    # Check if PDF path exists in parameters
    pdf_path = report.parameters.get('pdf_path') if report.parameters else None
    
    # If PDF doesn't exist, try to generate it from the JSON file
    if not pdf_path or not os.path.exists(pdf_path):
        if report.file_path and os.path.exists(report.file_path):
            try:
                # Load JSON data and generate PDF
                with open(report.file_path, 'r') as f:
                    report_data = json.load(f)
                
                # Generate PDF
                pdf_path = generate_pdf_report(report_data, str(report_id), report.report_type)
                
                # Update report parameters with PDF path
                if not report.parameters:
                    report.parameters = {}
                report.parameters['pdf_path'] = str(pdf_path)
                db.commit()
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
        else:
            raise HTTPException(status_code=404, detail="Report file not found")
    
    filename = f"report_{report_id}_{report.report_type}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return FileResponse(
        path=pdf_path,
        filename=filename,
        media_type='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

@router.post("/{report_id}/regenerate-pdf")
def regenerate_pdf_report(report_id: UUID, db: Session = Depends(get_db)):
    """Regenerate PDF for an existing report"""
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if report.status != "ready":
        raise HTTPException(status_code=400, detail="Report is not ready")
    
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    
    try:
        # Load JSON data
        with open(report.file_path, 'r') as f:
            report_data = json.load(f)
        
        # Generate new PDF
        pdf_path = generate_pdf_report(report_data, str(report_id), report.report_type)
        
        # Update report parameters
        if not report.parameters:
            report.parameters = {}
        report.parameters['pdf_path'] = str(pdf_path)
        db.commit()
        
        return {"message": "PDF regenerated successfully", "pdf_path": str(pdf_path)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate PDF: {str(e)}")

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(report_id: UUID, db: Session = Depends(get_db)):
    """Delete a report"""
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Delete files if they exist
    if report.file_path and os.path.exists(report.file_path):
        os.remove(report.file_path)
    
    # Delete PDF file if it exists
    pdf_path = report.parameters.get('pdf_path') if report.parameters else None
    if pdf_path and os.path.exists(pdf_path):
        os.remove(pdf_path)
    
    db.delete(report)
    db.commit() 