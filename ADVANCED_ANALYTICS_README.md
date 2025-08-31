# Advanced Analytics System

This document describes the advanced analytics functionality that provides deep business insights for your FastAPI backend.

## Overview

The advanced analytics system provides three key types of analysis that deliver significant business value:

1. **User Retention Analysis** - Identify what keeps users coming back
2. **Conversion Funnel Analysis** - Find where users drop off
3. **Product Category Performance** - Which categories drive revenue

## Features

- **Cohort Analysis**: Track user retention by signup date
- **Funnel Optimization**: Identify drop-off points in user journey
- **Category Insights**: Understand which product categories perform best
- **Predictive Insights**: Identify users likely to churn
- **Actionable Recommendations**: Get specific optimization suggestions
- **Comprehensive Reporting**: Combined analysis with key insights

## API Endpoints

### 1. User Retention Analysis
```
GET /analytics/brand/{brand_id}/retention?days=30
```

**Returns:**
- Cohort analysis by signup date
- Retention rates by day/week/month
- User engagement patterns
- Churn prediction indicators

**Example Response:**
```json
{
  "analysis_period": {
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-31T23:59:59",
    "days": 30
  },
  "cohort_analysis": {
    "2024-01-01": {
      "total_users": 150,
      "avg_swipes_per_user": 25.5,
      "avg_likes_per_user": 18.2,
      "engagement_score": 85.3,
      "retention_by_day": {
        "1": 120,
        "7": 85,
        "30": 45
      }
    }
  },
  "overall_retention": {
    "1": {"retention_rate": 80.0},
    "7": {"retention_rate": 56.7},
    "30": {"retention_rate": 30.0}
  },
  "summary": {
    "total_cohorts": 5,
    "total_users_analyzed": 750,
    "avg_retention_day_1": 80.0,
    "avg_retention_day_7": 56.7,
    "avg_retention_day_30": 30.0
  }
}
```

### 2. Conversion Funnel Analysis
```
GET /analytics/brand/{brand_id}/funnel?days=30
```

**Returns:**
- Funnel stages and conversion rates
- Drop-off points
- User journey analysis
- Optimization opportunities

**Example Response:**
```json
{
  "analysis_period": {
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-31T23:59:59",
    "days": 30
  },
  "funnel_stages": [
    "app_opened",
    "product_viewed",
    "swipe_made",
    "like_given",
    "product_clicked",
    "wishlist_added",
    "purchase_intent"
  ],
  "funnel_metrics": {
    "app_opened": 1000,
    "product_viewed": 850,
    "swipe_made": 720,
    "like_given": 540,
    "product_clicked": 380,
    "wishlist_added": 120,
    "purchase_intent": 45
  },
  "conversion_rates": {
    "app_opened": 100.0,
    "product_viewed": 85.0,
    "swipe_made": 84.7,
    "like_given": 75.0,
    "product_clicked": 70.4,
    "wishlist_added": 31.6,
    "purchase_intent": 37.5
  },
  "drop_off_points": [
    {
      "stage": "wishlist_added",
      "next_stage": "purchase_intent",
      "drop_off_rate": 62.5,
      "users_lost": 75
    }
  ],
  "summary": {
    "total_users": 1000,
    "overall_conversion_rate": 4.5,
    "biggest_drop_off": {
      "stage": "wishlist_added",
      "next_stage": "purchase_intent",
      "drop_off_rate": 62.5
    },
    "optimization_opportunities": 1
  }
}
```

### 3. Category Performance Analysis
```
GET /analytics/brand/{brand_id}/categories?days=30
```

**Returns:**
- Category performance metrics
- Revenue contribution by category
- Category trends and growth
- Optimization recommendations

**Example Response:**
```json
{
  "analysis_period": {
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-31T23:59:59",
    "days": 30
  },
  "categories": [
    {
      "category": "Electronics",
      "total_products": 45,
      "total_swipes": 1250,
      "total_likes": 875,
      "total_dislikes": 375,
      "unique_users": 320,
      "avg_price": 299.99,
      "total_value": 13499.55,
      "conversion_rate": 70.0,
      "engagement_rate": 7.1,
      "estimated_revenue": 612.50,
      "performance_score": 85.2,
      "rank": 1,
      "revenue_contribution": 35.2,
      "swipe_growth": 15.5,
      "like_growth": 12.3
    }
  ],
  "top_performers": [
    {
      "category": "Electronics",
      "rank": 1,
      "performance_score": 85.2
    }
  ],
  "underperformers": [
    {
      "category": "Books",
      "conversion_rate": 45.0,
      "total_swipes": 150
    }
  ],
  "summary": {
    "total_categories": 8,
    "total_products": 320,
    "total_swipes": 4500,
    "total_likes": 3150,
    "total_value": 38450.00,
    "avg_conversion_rate": 65.2,
    "top_category": "Electronics",
    "revenue_leaders": ["Electronics", "Clothing", "Home & Garden"]
  }
}
```

### 4. Comprehensive Analytics Report
```
GET /analytics/brand/{brand_id}/comprehensive?days=30
```

**Returns:**
- All three analyses combined
- Key insights and recommendations
- Executive summary

### 5. Key Insights
```
GET /analytics/brand/{brand_id}/insights?days=30
```

**Returns:**
- Top insights from all analyses
- Actionable recommendations
- Priority areas for improvement

## Implementation Details

### Advanced Analytics Service (`app/services/advanced_analytics.py`)

The core analytics functionality is implemented in the `AdvancedAnalytics` class:

```python
from app.services.advanced_analytics import AdvancedAnalytics

# Initialize analytics
analytics = AdvancedAnalytics(db)

# Run analyses
retention = analytics.analyze_user_retention(brand_id, days=30)
funnel = analytics.analyze_conversion_funnel(brand_id, days=30)
categories = analytics.analyze_category_performance(brand_id, days=30)
comprehensive = analytics.generate_combined_analytics_report(brand_id, days=30)
```

### Key Methods

#### `analyze_user_retention(brand_id, days)`
- **Purpose**: Analyze user retention patterns
- **Returns**: Cohort analysis, retention rates, engagement metrics
- **Key Metrics**: Day 1, 7, 30 retention rates

#### `analyze_conversion_funnel(brand_id, days)`
- **Purpose**: Identify drop-off points in user journey
- **Returns**: Funnel stages, conversion rates, optimization opportunities
- **Key Metrics**: Overall conversion rate, biggest drop-off points

#### `analyze_category_performance(brand_id, days)`
- **Purpose**: Understand category performance and revenue contribution
- **Returns**: Category metrics, growth rates, performance rankings
- **Key Metrics**: Conversion rates, revenue contribution, growth trends

## Business Value

### 1. User Retention Analysis
- **Identify Churn Patterns**: Understand when and why users leave
- **Optimize Onboarding**: Improve Day 1 retention rates
- **Engagement Strategies**: Develop better user engagement tactics
- **Predictive Insights**: Identify users likely to churn

### 2. Conversion Funnel Analysis
- **Optimize User Journey**: Find and fix drop-off points
- **Increase Conversions**: Improve overall conversion rates
- **Resource Allocation**: Focus efforts on high-impact areas
- **A/B Testing**: Identify areas for testing

### 3. Category Performance Analysis
- **Inventory Optimization**: Focus on high-performing categories
- **Revenue Growth**: Identify revenue opportunities
- **Product Strategy**: Optimize product mix
- **Marketing Focus**: Target marketing efforts effectively

## Usage Examples

### Basic Usage
```python
import requests

# Get retention analysis
response = requests.get("http://localhost:8000/analytics/brand/123/retention?days=30")
retention_data = response.json()

# Get conversion funnel
response = requests.get("http://localhost:8000/analytics/brand/123/funnel?days=30")
funnel_data = response.json()

# Get category performance
response = requests.get("http://localhost:8000/analytics/brand/123/categories?days=30")
category_data = response.json()
```

### Advanced Usage
```python
# Get comprehensive report with insights
response = requests.get("http://localhost:8000/analytics/brand/123/comprehensive?days=30")
comprehensive_data = response.json()

# Extract key insights
insights = comprehensive_data['key_insights']
recommendations = comprehensive_data['recommendations']

# Get executive summary
response = requests.get("http://localhost:8000/analytics/brand/123/insights?days=30")
summary = response.json()
```

## Testing

### Test Script
Run the test script to verify functionality:

```bash
python test_advanced_analytics.py
```

Remember to update the `BRAND_ID` variable with your actual brand ID.

### Manual Testing
Test individual endpoints:

```bash
# Test retention analysis
curl "http://localhost:8000/analytics/brand/your-brand-id/retention?days=30"

# Test conversion funnel
curl "http://localhost:8000/analytics/brand/your-brand-id/funnel?days=30"

# Test category performance
curl "http://localhost:8000/analytics/brand/your-brand-id/categories?days=30"
```

## Performance Considerations

- **Caching**: Analytics results are cached for 5 minutes
- **Query Optimization**: Uses optimized SQL queries with proper indexing
- **Data Limits**: Analysis limited to 365 days maximum
- **Memory Management**: Efficient data processing and memory usage

## Customization

### Adding New Metrics
To add new analytics metrics:

1. Add new methods to `AdvancedAnalytics` class
2. Create corresponding API endpoints
3. Update the comprehensive report generation

### Custom Insights
To customize insights generation:

1. Modify `_extract_*_insights()` methods
2. Update `_generate_recommendations()` method
3. Add new insight types as needed

## Troubleshooting

### Common Issues

1. **No Data Returned**
   - Check if brand exists
   - Verify date range has data
   - Check database connectivity

2. **Slow Performance**
   - Reduce analysis period (days parameter)
   - Check database indexes
   - Monitor cache usage

3. **Incorrect Results**
   - Verify data quality
   - Check calculation logic
   - Review SQL queries

### Debug Mode
Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- **Real-time Analytics**: Live dashboard updates
- **Predictive Modeling**: ML-based predictions
- **Custom Dashboards**: User-configurable views
- **Export Functionality**: PDF/Excel reports
- **Alert System**: Automated insights and notifications
- **Integration**: Connect with external analytics tools

## Support

For issues with advanced analytics:
1. Check the test script output
2. Verify API endpoints are accessible
3. Review database connectivity
4. Check data quality and completeness 