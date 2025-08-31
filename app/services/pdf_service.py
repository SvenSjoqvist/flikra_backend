"""
PDF Generation Service
Handles creation of PDF reports using reportlab and fpdf2
"""
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from fpdf import FPDF
import json

# Create reports directory if it doesn't exist
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

class PDFReportGenerator:
    """Generate PDF reports using reportlab"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.darkblue
        )
        
        # Header style
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Normal text style
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
    
    def generate_performance_report(self, report_data: Dict[str, Any], report_id: str) -> str:
        """Generate a performance report PDF"""
        filename = f"report_{report_id}_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = REPORTS_DIR / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []
        
        # Title
        story.append(Paragraph("Performance Report", self.title_style))
        story.append(Spacer(1, 20))
        
        # Report period
        period = report_data.get('period', {})
        period_text = f"Period: {period.get('start_date', 'N/A')} to {period.get('end_date', 'N/A')}"
        story.append(Paragraph(period_text, self.normal_style))
        story.append(Spacer(1, 20))
        
        # Summary section
        story.append(Paragraph("Summary", self.subtitle_style))
        summary = report_data.get('summary', {})
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Products', str(summary.get('total_products', 0))],
            ['Total Swipes', str(summary.get('total_swipes', 0))],
            ['Total Likes', str(summary.get('total_likes', 0))],
            ['Total Dislikes', str(summary.get('total_dislikes', 0))],
            ['Overall Conversion Rate', f"{summary.get('overall_conversion_rate', 0)}%"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Product performance table
        story.append(Paragraph("Product Performance", self.subtitle_style))
        
        products = report_data.get('products', [])
        if products:
            # Table headers
            product_data = [['Product', 'Swipes', 'Likes', 'Dislikes', 'Conversion Rate']]
            
            # Add product data
            for product in products[:20]:  # Limit to top 20 products
                product_data.append([
                    product.get('product_name', 'N/A')[:30],  # Truncate long names
                    str(product.get('total_swipes', 0)),
                    str(product.get('likes', 0)),
                    str(product.get('dislikes', 0)),
                    f"{product.get('conversion_rate', 0)}%"
                ])
            
            product_table = Table(product_data, colWidths=[2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
            product_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            story.append(product_table)
        else:
            story.append(Paragraph("No product data available", self.normal_style))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        
        doc.build(story)
        return str(filepath)
    
    def generate_engagement_report(self, report_data: Dict[str, Any], report_id: str) -> str:
        """Generate an engagement report PDF"""
        filename = f"report_{report_id}_engagement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = REPORTS_DIR / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []
        
        # Title
        story.append(Paragraph("User Engagement Report", self.title_style))
        story.append(Spacer(1, 20))
        
        # Report period
        period = report_data.get('period', {})
        period_text = f"Period: {period.get('start_date', 'N/A')} to {period.get('end_date', 'N/A')}"
        story.append(Paragraph(period_text, self.normal_style))
        story.append(Spacer(1, 20))
        
        # Summary section
        story.append(Paragraph("Engagement Summary", self.subtitle_style))
        summary = report_data.get('summary', {})
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Unique Users', str(summary.get('total_unique_users', 0))],
            ['Total Swipes', str(summary.get('total_swipes', 0))],
            ['Average Swipes per User', str(summary.get('avg_swipes_per_user', 0))]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Daily activity table
        story.append(Paragraph("Daily Activity", self.subtitle_style))
        
        daily_activity = report_data.get('daily_activity', [])
        if daily_activity:
            # Table headers
            activity_data = [['Date', 'Swipes', 'Active Users']]
            
            # Add daily data
            for day in daily_activity[:30]:  # Limit to 30 days
                activity_data.append([
                    day.get('date', 'N/A'),
                    str(day.get('swipes', 0)),
                    str(day.get('active_users', 0))
                ])
            
            activity_table = Table(activity_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch])
            activity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            story.append(activity_table)
        else:
            story.append(Paragraph("No daily activity data available", self.normal_style))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        
        doc.build(story)
        return str(filepath)
    
    def generate_financial_report(self, report_data: Dict[str, Any], report_id: str) -> str:
        """Generate a financial report PDF"""
        filename = f"report_{report_id}_financial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = REPORTS_DIR / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []
        
        # Title
        story.append(Paragraph("Financial Report", self.title_style))
        story.append(Spacer(1, 20))
        
        # Report period
        period = report_data.get('period', {})
        period_text = f"Period: {period.get('start_date', 'N/A')} to {period.get('end_date', 'N/A')}"
        story.append(Paragraph(period_text, self.normal_style))
        story.append(Spacer(1, 20))
        
        # Financial metrics
        story.append(Paragraph("Financial Metrics", self.subtitle_style))
        metrics = report_data.get('metrics', {})
        
        metrics_data = [
            ['Metric', 'Value'],
            ['Total Swipes', str(metrics.get('total_swipes', 0))],
            ['Conversions', str(metrics.get('conversions', 0))],
            ['Conversion Rate', f"{metrics.get('conversion_rate', 0)}%"],
            ['Unique Customers', str(metrics.get('unique_customers', 0))],
            ['Average Conversion Value', f"${metrics.get('avg_conversion_value', 0):.2f}"],
            ['Estimated Revenue', f"${metrics.get('estimated_revenue', 0):.2f}"]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metrics_table)
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        
        doc.build(story)
        return str(filepath)
    
    def generate_category_report(self, report_data: Dict[str, Any], report_id: str) -> str:
        """Generate a category analysis report PDF"""
        filename = f"report_{report_id}_category_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = REPORTS_DIR / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []
        
        # Title
        story.append(Paragraph("Category Analysis Report", self.title_style))
        story.append(Spacer(1, 20))
        
        # Report period
        period = report_data.get('period', {})
        period_text = f"Period: {period.get('start_date', 'N/A')} to {period.get('end_date', 'N/A')}"
        story.append(Paragraph(period_text, self.normal_style))
        story.append(Spacer(1, 20))
        
        # Category performance
        story.append(Paragraph("Category Performance", self.subtitle_style))
        
        categories = report_data.get('categories', [])
        if categories:
            # Table headers
            category_data = [['Category', 'Products', 'Swipes', 'Likes', 'Conversion Rate']]
            
            # Add category data
            for category in categories:
                category_data.append([
                    category.get('category', 'N/A'),
                    str(category.get('products_count', 0)),
                    str(category.get('total_swipes', 0)),
                    str(category.get('likes', 0)),
                    f"{category.get('conversion_rate', 0)}%"
                ])
            
            category_table = Table(category_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1.2*inch])
            category_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            story.append(category_table)
        else:
            story.append(Paragraph("No category data available", self.normal_style))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        
        doc.build(story)
        return str(filepath)
    
    def generate_custom_report(self, report_data: Dict[str, Any], report_id: str) -> str:
        """Generate a custom report PDF"""
        filename = f"report_{report_id}_custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = REPORTS_DIR / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        story = []
        
        # Title
        story.append(Paragraph("Custom Analytics Report", self.title_style))
        story.append(Spacer(1, 20))
        
        # Report period
        period = report_data.get('period', {})
        period_text = f"Period: {period.get('start_date', 'N/A')} to {period.get('end_date', 'N/A')}"
        story.append(Paragraph(period_text, self.normal_style))
        story.append(Spacer(1, 20))
        
        # Basic metrics
        story.append(Paragraph("Basic Metrics", self.subtitle_style))
        basic_metrics = report_data.get('basic_metrics', {})
        
        metrics_data = [
            ['Metric', 'Value'],
            ['Total Swipes', str(basic_metrics.get('total_swipes', 0))],
            ['Total Likes', str(basic_metrics.get('total_likes', 0))],
            ['Unique Users', str(basic_metrics.get('unique_users', 0))]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 1.5*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metrics_table)
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        
        doc.build(story)
        return str(filepath)

def generate_pdf_report(report_data: Dict[str, Any], report_id: str, report_type: str) -> str:
    """Generate PDF report based on report type"""
    generator = PDFReportGenerator()
    
    if report_type == "performance":
        return generator.generate_performance_report(report_data, report_id)
    elif report_type == "engagement":
        return generator.generate_engagement_report(report_data, report_id)
    elif report_type == "financial":
        return generator.generate_financial_report(report_data, report_id)
    elif report_type == "category":
        return generator.generate_category_report(report_data, report_id)
    else:
        return generator.generate_custom_report(report_data, report_id) 