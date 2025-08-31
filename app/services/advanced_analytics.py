"""
Advanced Analytics Service
Provides deep insights into user behavior, conversion patterns, and product performance
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, case, distinct, extract, text
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import json

from app.models import User, Product, Swipe, WishlistItem

class AdvancedAnalytics:
    """Advanced analytics for business intelligence"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_user_retention(self, brand_id: UUID, days: int = 30) -> Dict[str, Any]:
        """
        Analyze user retention patterns to identify what keeps users coming back
        
        Returns:
        - Cohort analysis by signup date
        - Retention rates by day/week/month
        - User engagement patterns
        - Churn prediction indicators
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all users who signed up in the period
        cohort_users = self.db.query(
            func.date(func.date_trunc('day', User.created_at)).label('cohort_date'),
            User.id,
            User.created_at
        ).filter(
            and_(
                User.created_at >= start_date,
                User.created_at <= end_date
            )
        ).all()
        
        # Get user activity data
        user_activity = self.db.query(
            User.id,
            func.date(func.date_trunc('day', Swipe.created_at)).label('activity_date'),
            func.count(Swipe.id).label('swipe_count'),
            func.count(case((Swipe.action == 'like', 1))).label('likes'),
            func.count(case((Swipe.action == 'dislike', 1))).label('dislikes')
        ).join(Swipe).filter(
            and_(
                Swipe.created_at >= start_date,
                Swipe.created_at <= end_date
            )
        ).group_by(
            User.id,
            func.date(func.date_trunc('day', Swipe.created_at))
        ).all()
        
        # Calculate retention metrics
        retention_data = {}
        cohort_sizes = {}
        
        for cohort_user in cohort_users:
            cohort_date = cohort_user.cohort_date
            user_id = cohort_user.id
            
            if cohort_date not in retention_data:
                retention_data[cohort_date] = {
                    'total_users': 0,
                    'retention_by_day': {},
                    'avg_swipes_per_user': 0,
                    'avg_likes_per_user': 0,
                    'engagement_score': 0
                }
                cohort_sizes[cohort_date] = 0
            
            cohort_sizes[cohort_date] += 1
            retention_data[cohort_date]['total_users'] += 1
            
            # Find user's activity
            user_activities = [ua for ua in user_activity if ua.id == user_id]
            
            if user_activities:
                total_swipes = sum(ua.swipe_count for ua in user_activities)
                total_likes = sum(ua.likes for ua in user_activities)
                total_days_active = len(set(ua.activity_date for ua in user_activities))
                
                retention_data[cohort_date]['avg_swipes_per_user'] += total_swipes
                retention_data[cohort_date]['avg_likes_per_user'] += total_likes
                
                # Calculate engagement score (swipes + likes + days active)
                engagement_score = total_swipes + total_likes + (total_days_active * 10)
                retention_data[cohort_date]['engagement_score'] += engagement_score
                
                # Track retention by day
                for ua in user_activities:
                    days_since_cohort = (ua.activity_date - cohort_date).days
                    if days_since_cohort not in retention_data[cohort_date]['retention_by_day']:
                        retention_data[cohort_date]['retention_by_day'][days_since_cohort] = 0
                    retention_data[cohort_date]['retention_by_day'][days_since_cohort] += 1
        
        # Calculate averages
        for cohort_date in retention_data:
            total_users = retention_data[cohort_date]['total_users']
            if total_users > 0:
                retention_data[cohort_date]['avg_swipes_per_user'] = round(
                    retention_data[cohort_date]['avg_swipes_per_user'] / total_users, 2
                )
                retention_data[cohort_date]['avg_likes_per_user'] = round(
                    retention_data[cohort_date]['avg_likes_per_user'] / total_users, 2
                )
                retention_data[cohort_date]['engagement_score'] = round(
                    retention_data[cohort_date]['engagement_score'] / total_users, 2
                )
        
        # Calculate overall retention rates
        overall_retention = {}
        for cohort_date in retention_data:
            for day, users_active in retention_data[cohort_date]['retention_by_day'].items():
                if day not in overall_retention:
                    overall_retention[day] = {'active_users': 0, 'total_users': 0}
                overall_retention[day]['active_users'] += users_active
                overall_retention[day]['total_users'] += retention_data[cohort_date]['total_users']
        
        # Calculate retention percentages
        for day in overall_retention:
            if overall_retention[day]['total_users'] > 0:
                overall_retention[day]['retention_rate'] = round(
                    (overall_retention[day]['active_users'] / overall_retention[day]['total_users']) * 100, 2
                )
        
        return {
            'analysis_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'cohort_analysis': retention_data,
            'overall_retention': overall_retention,
            'summary': {
                'total_cohorts': len(retention_data),
                'total_users_analyzed': sum(cohort_sizes.values()),
                'avg_retention_day_1': overall_retention.get(1, {}).get('retention_rate', 0),
                'avg_retention_day_7': overall_retention.get(7, {}).get('retention_rate', 0),
                'avg_retention_day_30': overall_retention.get(30, {}).get('retention_rate', 0)
            }
        }
    
    def analyze_conversion_funnel(self, brand_id: UUID, days: int = 30) -> Dict[str, Any]:
        """
        Analyze conversion funnel to identify where users drop off
        
        Returns:
        - Funnel stages and conversion rates
        - Drop-off points
        - User journey analysis
        - Optimization opportunities
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Define funnel stages
        funnel_stages = [
            'app_opened',
            'product_viewed', 
            'swipe_made',
            'like_given',
            'product_clicked',
            'wishlist_added',
            'purchase_intent'
        ]
        
        # Get user activity data for funnel analysis
        user_journey = self.db.query(
            User.id,
            func.count(distinct(func.date(Swipe.created_at))).label('days_active'),
            func.count(Swipe.id).label('total_swipes'),
            func.count(case((Swipe.action == 'like', 1))).label('total_likes'),
            func.count(case((Swipe.action == 'dislike', 1))).label('total_dislikes'),
            func.count(distinct(Swipe.product_id)).label('products_viewed')
        ).join(Swipe).filter(
            and_(
                Swipe.created_at >= start_date,
                Swipe.created_at <= end_date
            )
        ).group_by(User.id).all()
        
        # Get wishlist data
        wishlist_data = self.db.query(
            User.id,
            func.count(WishlistItem.id).label('wishlist_items')
        ).join(WishlistItem).filter(
            and_(
                WishlistItem.saved_at >= start_date,
                WishlistItem.saved_at <= end_date
            )
        ).group_by(User.id).all()
        
        wishlist_dict = {w.id: w.wishlist_items for w in wishlist_data}
        
        # Calculate funnel metrics
        funnel_metrics = {
            'app_opened': 0,
            'product_viewed': 0,
            'swipe_made': 0,
            'like_given': 0,
            'product_clicked': 0,
            'wishlist_added': 0,
            'purchase_intent': 0
        }
        
        total_users = len(user_journey)
        
        for user in user_journey:
            # App opened (users with any activity)
            funnel_metrics['app_opened'] += 1
            
            # Product viewed (users who viewed products)
            if user.products_viewed > 0:
                funnel_metrics['product_viewed'] += 1
            
            # Swipe made (users who made swipes)
            if user.total_swipes > 0:
                funnel_metrics['swipe_made'] += 1
            
            # Like given (users who gave likes)
            if user.total_likes > 0:
                funnel_metrics['like_given'] += 1
            
            # Product clicked (estimated from engagement)
            if user.total_swipes > 5:  # Users with high engagement likely clicked
                funnel_metrics['product_clicked'] += 1
            
            # Wishlist added (users with wishlist items)
            wishlist_count = wishlist_dict.get(user.id, 0)
            if wishlist_count > 0:
                funnel_metrics['wishlist_added'] += 1
            
            # Purchase intent (users with high engagement and wishlist items)
            if user.total_likes > 10 and wishlist_count > 0:
                funnel_metrics['purchase_intent'] += 1
        
        # Calculate conversion rates
        conversion_rates = {}
        previous_stage = None
        
        for stage in funnel_stages:
            current_count = funnel_metrics[stage]
            if previous_stage is None:
                conversion_rates[stage] = 100.0  # First stage is 100%
            else:
                previous_count = funnel_metrics[previous_stage]
                if previous_count > 0:
                    conversion_rates[stage] = round((current_count / previous_count) * 100, 2)
                else:
                    conversion_rates[stage] = 0.0
            previous_stage = stage
        
        # Identify drop-off points
        drop_off_points = []
        for i, stage in enumerate(funnel_stages[:-1]):
            next_stage = funnel_stages[i + 1]
            current_rate = conversion_rates[stage]
            next_rate = conversion_rates[next_stage]
            drop_off = current_rate - next_rate
            
            if drop_off > 20:  # Significant drop-off threshold
                drop_off_points.append({
                    'stage': stage,
                    'next_stage': next_stage,
                    'drop_off_rate': round(drop_off, 2),
                    'users_lost': funnel_metrics[stage] - funnel_metrics[next_stage]
                })
        
        return {
            'analysis_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'funnel_stages': funnel_stages,
            'funnel_metrics': funnel_metrics,
            'conversion_rates': conversion_rates,
            'drop_off_points': drop_off_points,
            'summary': {
                'total_users': total_users,
                'overall_conversion_rate': conversion_rates.get('purchase_intent', 0),
                'biggest_drop_off': max(drop_off_points, key=lambda x: x['drop_off_rate']) if drop_off_points else None,
                'optimization_opportunities': len(drop_off_points)
            }
        }
    
    def analyze_category_performance(self, brand_id: UUID, days: int = 30) -> Dict[str, Any]:
        """
        Analyze product category performance to identify which categories drive revenue
        
        Returns:
        - Category performance metrics
        - Revenue contribution by category
        - Category trends and growth
        - Optimization recommendations
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get category performance data
        category_stats = self.db.query(
            Product.category,
            func.count(distinct(Product.id)).label('total_products'),
            func.count(Swipe.id).label('total_swipes'),
            func.count(case((Swipe.action == 'like', 1))).label('total_likes'),
            func.count(case((Swipe.action == 'dislike', 1))).label('total_dislikes'),
            func.count(distinct(Swipe.user_id)).label('unique_users'),
            func.avg(Product.price).label('avg_price'),
            func.sum(Product.price).label('total_value')
        ).join(Swipe).filter(
            and_(
                Swipe.created_at >= start_date,
                Swipe.created_at <= end_date,
                Product.category.isnot(None),
                Product.category != ''
            )
        ).group_by(Product.category).order_by(
            func.count(Swipe.id).desc()
        ).all()
        
        # Calculate category metrics
        categories_data = []
        total_swipes = 0
        total_likes = 0
        total_value = 0
        
        for cat in category_stats:
            conversion_rate = (cat.total_likes / cat.total_swipes * 100) if cat.total_swipes > 0 else 0
            engagement_rate = (cat.unique_users / cat.total_products) if cat.total_products > 0 else 0
            
            # Estimate revenue (assuming likes lead to purchases)
            avg_price = float(cat.avg_price or 0)
            estimated_revenue = cat.total_likes * avg_price * 0.1  # 10% conversion assumption
            
            category_data = {
                'category': cat.category,
                'total_products': cat.total_products,
                'total_swipes': cat.total_swipes,
                'total_likes': cat.total_likes,
                'total_dislikes': cat.total_dislikes,
                'unique_users': cat.unique_users,
                'avg_price': float(cat.avg_price or 0),
                'total_value': float(cat.total_value or 0),
                'conversion_rate': round(conversion_rate, 2),
                'engagement_rate': round(engagement_rate, 2),
                'estimated_revenue': round(estimated_revenue, 2),
                'performance_score': round((conversion_rate * 0.4) + (engagement_rate * 0.3) + (cat.total_swipes * 0.3), 2)
            }
            
            categories_data.append(category_data)
            total_swipes += cat.total_swipes
            total_likes += cat.total_likes
            total_value += float(cat.total_value or 0)
        
        # Calculate category rankings
        categories_data.sort(key=lambda x: x['performance_score'], reverse=True)
        
        for i, cat in enumerate(categories_data):
            cat['rank'] = i + 1
            cat['revenue_contribution'] = round((cat['estimated_revenue'] / sum(c['estimated_revenue'] for c in categories_data)) * 100, 2) if categories_data else 0
        
        # Get category trends (compare with previous period)
        previous_start = start_date - timedelta(days=days)
        previous_end = start_date
        
        previous_category_stats = self.db.query(
            Product.category,
            func.count(Swipe.id).label('total_swipes'),
            func.count(case((Swipe.action == 'like', 1))).label('total_likes')
        ).join(Swipe).filter(
            and_(
                Swipe.created_at >= previous_start,
                Swipe.created_at <= previous_end,
                Product.category.isnot(None),
                Product.category != ''
            )
        ).group_by(Product.category).all()
        
        previous_stats = {cat.category: {'swipes': cat.total_swipes, 'likes': cat.total_likes} for cat in previous_category_stats}
        
        # Calculate growth rates
        for cat in categories_data:
            previous = previous_stats.get(cat['category'], {'swipes': 0, 'likes': 0})
            
            if previous['swipes'] > 0:
                cat['swipe_growth'] = round(((cat['total_swipes'] - previous['swipes']) / previous['swipes']) * 100, 2)
            else:
                cat['swipe_growth'] = 0
            
            if previous['likes'] > 0:
                cat['like_growth'] = round(((cat['total_likes'] - previous['likes']) / previous['likes']) * 100, 2)
            else:
                cat['like_growth'] = 0
        
        # Identify top performers and opportunities
        top_performers = [cat for cat in categories_data if cat['rank'] <= 3]
        underperformers = [cat for cat in categories_data if cat['conversion_rate'] < 50 and cat['total_swipes'] > 10]
        
        return {
            'analysis_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'categories': categories_data,
            'top_performers': top_performers,
            'underperformers': underperformers,
            'summary': {
                'total_categories': len(categories_data),
                'total_products': sum(cat['total_products'] for cat in categories_data),
                'total_swipes': total_swipes,
                'total_likes': total_likes,
                'total_value': round(total_value, 2),
                'avg_conversion_rate': round(sum(cat['conversion_rate'] for cat in categories_data) / len(categories_data), 2) if categories_data else 0,
                'top_category': categories_data[0]['category'] if categories_data else None,
                'revenue_leaders': [cat['category'] for cat in categories_data[:3]]
            }
        }
    
    def generate_combined_analytics_report(self, brand_id: UUID, days: int = 30) -> Dict[str, Any]:
        """
        Generate a comprehensive analytics report combining all three analyses
        """
        retention = self.analyze_user_retention(brand_id, days)
        funnel = self.analyze_conversion_funnel(brand_id, days)
        categories = self.analyze_category_performance(brand_id, days)
        
        return {
            'report_metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'brand_id': str(brand_id),
                'analysis_period_days': days
            },
            'user_retention_analysis': retention,
            'conversion_funnel_analysis': funnel,
            'category_performance_analysis': categories,
            'key_insights': {
                'retention_insights': self._extract_retention_insights(retention),
                'funnel_insights': self._extract_funnel_insights(funnel),
                'category_insights': self._extract_category_insights(categories)
            },
            'recommendations': self._generate_recommendations(retention, funnel, categories)
        }
    
    def _extract_retention_insights(self, retention_data: Dict) -> List[str]:
        """Extract key insights from retention analysis"""
        insights = []
        
        day_1_retention = retention_data['summary']['avg_retention_day_1']
        day_7_retention = retention_data['summary']['avg_retention_day_7']
        day_30_retention = retention_data['summary']['avg_retention_day_30']
        
        if day_1_retention < 50:
            insights.append("Low Day 1 retention - focus on onboarding experience")
        if day_7_retention < 20:
            insights.append("Low Day 7 retention - need better engagement strategies")
        if day_30_retention < 10:
            insights.append("Low Day 30 retention - consider re-engagement campaigns")
        
        return insights
    
    def _extract_funnel_insights(self, funnel_data: Dict) -> List[str]:
        """Extract key insights from funnel analysis"""
        insights = []
        
        biggest_drop_off = funnel_data['summary']['biggest_drop_off']
        if biggest_drop_off:
            insights.append(f"Biggest drop-off: {biggest_drop_off['stage']} to {biggest_drop_off['next_stage']} ({biggest_drop_off['drop_off_rate']}%)")
        
        overall_conversion = funnel_data['summary']['overall_conversion_rate']
        if overall_conversion < 5:
            insights.append("Low overall conversion rate - optimize user journey")
        
        return insights
    
    def _extract_category_insights(self, category_data: Dict) -> List[str]:
        """Extract key insights from category analysis"""
        insights = []
        
        top_category = category_data['summary']['top_category']
        if top_category:
            insights.append(f"Top performing category: {top_category}")
        
        underperformers = category_data['underperformers']
        if underperformers:
            insights.append(f"{len(underperformers)} categories need optimization")
        
        return insights
    
    def _generate_recommendations(self, retention: Dict, funnel: Dict, categories: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Retention recommendations
        if retention['summary']['avg_retention_day_1'] < 50:
            recommendations.append("Improve onboarding flow to increase Day 1 retention")
        
        # Funnel recommendations
        biggest_drop_off = funnel['summary']['biggest_drop_off']
        if biggest_drop_off:
            recommendations.append(f"Focus on optimizing {biggest_drop_off['stage']} to {biggest_drop_off['next_stage']} transition")
        
        # Category recommendations
        underperformers = categories['underperformers']
        if underperformers:
            recommendations.append("Optimize underperforming categories or consider removing them")
        
        return recommendations 