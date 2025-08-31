"""
Automatic monthly report generation service
Generates reports on the 28th of each month for all active brands
"""
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Brand, Report, ReportTemplate
from app.routers.reports import generate_report_file

def should_generate_monthly_reports() -> bool:
    """Check if today is the 28th of the month"""
    today = datetime.utcnow()
    return today.day == 28

def get_monthly_report_period() -> tuple:
    """Get the date range for the previous month's report"""
    today = datetime.utcnow()
    
    # Calculate the first day of the previous month
    if today.month == 1:
        prev_month = 12
        prev_year = today.year - 1
    else:
        prev_month = today.month - 1
        prev_year = today.year
    
    start_date = datetime(prev_year, prev_month, 1)
    
    # Calculate the last day of the previous month
    if prev_month == 12:
        next_month = 1
        next_year = prev_year + 1
    else:
        next_month = prev_month + 1
        next_year = prev_year
    
    end_date = datetime(next_year, next_month, 1) - timedelta(days=1)
    
    return start_date, end_date

def generate_monthly_reports_for_brand(brand_id: str, db: Session):
    """Generate monthly reports for a specific brand"""
    try:
        # Get the brand
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            print(f"❌ Brand {brand_id} not found")
            return
        
        # Get date range for previous month
        start_date, end_date = get_monthly_report_period()
        
        # Get default templates for monthly reports
        monthly_templates = db.query(ReportTemplate).filter(
            ReportTemplate.is_active == True,
            ReportTemplate.name.in_([
                "Monthly Performance Report",
                "User Engagement Analytics", 
                "Revenue & Conversion Report",
                "Product Category Analysis"
            ])
        ).all()
        
        print(f"📊 Generating monthly reports for {brand.name} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})")
        
        # Generate reports for each template
        for template in monthly_templates:
            # Check if report already exists for this month
            existing_report = db.query(Report).filter(
                Report.brand_id == brand_id,
                Report.report_type == template.report_type,
                Report.generated_at >= start_date,
                Report.generated_at <= end_date + timedelta(days=1)
            ).first()
            
            if existing_report:
                print(f"   ⏭️  Skipping {template.name} - already exists")
                continue
            
            # Create report record
            report_name = f"{template.name} - {start_date.strftime('%B %Y')}"
            report = Report(
                brand_id=brand_id,
                name=report_name,
                report_type=template.report_type,
                parameters={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "template_id": str(template.id),
                    "auto_generated": True
                },
                status="processing"
            )
            
            db.add(report)
            db.commit()
            db.refresh(report)
            
            print(f"   ✅ Created {template.name}")
            
            # Generate the report file
            try:
                generate_report_file(
                    report.id,
                    brand_id,
                    template.report_type,
                    start_date,
                    end_date,
                    db
                )
                print(f"   ✅ Generated {template.name}")
            except Exception as e:
                print(f"   ❌ Failed to generate {template.name}: {e}")
                report.status = "failed"
                report.error_message = str(e)
                db.commit()
        
        print(f"✅ Completed monthly reports for {brand.name}")
        
    except Exception as e:
        print(f"❌ Error generating monthly reports for brand {brand_id}: {e}")

def generate_all_monthly_reports():
    """Generate monthly reports for all active brands"""
    print(f"\n🔄 Starting monthly report generation - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not should_generate_monthly_reports():
        print("⏭️  Not the 28th of the month, skipping monthly report generation")
        return
    
    db = next(get_db())
    
    try:
        # Get all active brands
        brands = db.query(Brand).filter(Brand.status == "active").all()
        
        if not brands:
            print("⚠️  No active brands found")
            return
        
        print(f"📊 Found {len(brands)} active brands")
        
        # Generate reports for each brand
        for brand in brands:
            generate_monthly_reports_for_brand(str(brand.id), db)
        
        print(f"🎉 Completed monthly report generation for {len(brands)} brands")
        
    except Exception as e:
        print(f"❌ Error in monthly report generation: {e}")
    finally:
        db.close()

def start_monthly_report_scheduler():
    """Start the scheduler for monthly report generation"""
    print("🚀 Starting monthly report scheduler...")
    
    # Schedule to run daily at 2 AM UTC
    schedule.every().day.at("02:00").do(generate_all_monthly_reports)
    
    print("✅ Monthly report scheduler started - will run daily at 2 AM UTC")
    print("📅 Reports will be generated on the 28th of each month")
    
    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def run_monthly_report_generation():
    """Run monthly report generation immediately (for testing)"""
    print("🔧 Running monthly report generation immediately...")
    generate_all_monthly_reports()

if __name__ == "__main__":
    # For testing, run immediately
    run_monthly_report_generation() 