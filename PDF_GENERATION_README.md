# PDF Report Generation

This document describes the PDF generation functionality added to the FastAPI backend.

## Overview

The backend now supports automatic PDF generation for all report types. When a report is generated, both JSON and PDF versions are created and stored. Users can download either format through the API.

## Features

- **Automatic PDF Generation**: Every report is automatically converted to PDF format
- **Multiple Report Types**: Support for performance, engagement, financial, and category reports
- **Professional Layout**: Clean, professional PDF layouts with tables and styling
- **Dual Download Options**: Download reports as either JSON or PDF
- **Background Processing**: PDF generation happens in the background without blocking the API

## Installation

The required packages have been added to `requirements.txt`:

```bash
pip install reportlab fpdf2 jinja2
```

## API Endpoints

### Download PDF Report
```
GET /reports/{report_id}/download-pdf
```

Downloads a report as a PDF file.

**Response**: PDF file with appropriate headers for download

**Example**:
```bash
curl -X GET "http://localhost:8000/reports/123e4567-e89b-12d3-a456-426614174000/download-pdf" \
  -H "Authorization: Bearer your-api-key" \
  --output report.pdf
```

### Download JSON Report (existing)
```
GET /reports/{report_id}/download
```

Downloads a report as a JSON file (existing functionality).

## Report Types and PDF Layouts

### 1. Performance Report
- **Content**: Product performance metrics, conversion rates
- **Layout**: Summary table + detailed product performance table
- **Features**: Color-coded tables, conversion rate calculations

### 2. Engagement Report
- **Content**: User engagement patterns, daily activity
- **Layout**: Summary metrics + daily activity table
- **Features**: User activity tracking, engagement trends

### 3. Financial Report
- **Content**: Revenue metrics, conversion data
- **Layout**: Financial metrics table
- **Features**: Revenue calculations, conversion tracking

### 4. Category Report
- **Content**: Category performance analysis
- **Layout**: Category performance table
- **Features**: Category-wise metrics, performance comparison

### 5. Custom Report
- **Content**: Basic analytics data
- **Layout**: Simple metrics table
- **Features**: Flexible data presentation

## File Storage

- **JSON Files**: Stored as primary format in `reports/` directory
- **PDF Files**: Generated automatically and stored alongside JSON files
- **File Naming**: `report_{report_id}_{type}_{timestamp}.pdf`
- **Database**: PDF path stored in report parameters

## Implementation Details

### PDF Service (`app/services/pdf_service.py`)

The PDF generation is handled by the `PDFReportGenerator` class:

```python
from app.services.pdf_service import generate_pdf_report

# Generate PDF for any report type
pdf_path = generate_pdf_report(report_data, report_id, report_type)
```

### Report Generation Process

1. **Data Generation**: Report data is generated as before
2. **JSON Creation**: JSON file is created and saved
3. **PDF Generation**: PDF is generated using the same data
4. **Database Update**: Both file paths are stored in the database
5. **Status Update**: Report status is set to "ready"

### Integration with Existing Code

The PDF generation is seamlessly integrated into the existing report generation process:

```python
def generate_report_file(report_id, brand_id, report_type, start_date, end_date, db):
    # Generate report data
    report_data = generate_report_data(brand_id, report_type, start_date, end_date, db)
    
    # Create JSON file
    json_path = create_json_file(report_data, report_id, report_type)
    
    # Generate PDF file
    pdf_path = generate_pdf_report(report_data, report_id, report_type)
    
    # Update database with both file paths
    update_report_status(report_id, json_path, pdf_path, db)
```

## Testing

### Test Script
Run the test script to verify PDF generation:

```bash
python test_pdf_generation.py
```

This will:
- Generate sample performance and engagement reports
- Create PDF files in the `reports/` directory
- Verify file creation and sizes

### API Testing
Use the provided API client example:

```bash
python api_client_pdf_example.py
```

Remember to update the API key and brand ID in the script.

## Error Handling

- **Missing Dependencies**: PDF generation fails gracefully if libraries aren't installed
- **File System Errors**: Handles disk space and permission issues
- **Data Validation**: Validates report data before PDF generation
- **Database Consistency**: Ensures both JSON and PDF paths are stored correctly

## Performance Considerations

- **Background Processing**: PDF generation doesn't block API responses
- **File Size**: PDFs are typically 2-5KB for standard reports
- **Memory Usage**: Minimal memory footprint during generation
- **Caching**: Generated PDFs are cached and reused

## Customization

### Adding New Report Types

1. Add a new method to `PDFReportGenerator`:
```python
def generate_new_report_type(self, report_data, report_id):
    # Custom PDF generation logic
    pass
```

2. Update the `generate_pdf_report` function:
```python
elif report_type == "new_type":
    return generator.generate_new_report_type(report_data, report_id)
```

### Styling Customization

Modify the styles in `_setup_custom_styles()`:
```python
self.custom_style = ParagraphStyle(
    'CustomStyle',
    parent=self.styles['Normal'],
    fontSize=12,
    textColor=colors.darkblue
)
```

## Troubleshooting

### Common Issues

1. **PDF Not Generated**
   - Check if reportlab and fpdf2 are installed
   - Verify report data structure
   - Check file permissions in reports directory

2. **PDF Download Fails**
   - Ensure report status is "ready"
   - Check if PDF file exists on disk
   - Verify API authentication

3. **PDF Layout Issues**
   - Check table data structure
   - Verify text encoding
   - Review custom styles

### Debug Mode

Enable debug logging to troubleshoot PDF generation:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- **Charts and Graphs**: Add visual charts to PDFs
- **Branding**: Custom logos and colors per brand
- **Templates**: Customizable PDF templates
- **Batch Processing**: Generate multiple PDFs simultaneously
- **Email Integration**: Send PDFs via email
- **Watermarking**: Add watermarks for security

## Security Considerations

- **File Access**: PDFs are stored in a controlled directory
- **Authentication**: Download endpoints require valid API keys
- **Validation**: Report ownership is verified before download
- **Cleanup**: Old PDF files can be cleaned up periodically

## Support

For issues with PDF generation:
1. Check the test script output
2. Verify all dependencies are installed
3. Review the error logs
4. Test with sample data first 