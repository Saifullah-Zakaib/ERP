"""
Management command to populate AI insights for demonstration
"""
from django.core.management.base import BaseCommand
from core.models import AIInsight
from django.utils import timezone


class Command(BaseCommand):
    help = 'Populate sample AI insights for demonstration'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Populating AI Insights...'))
        
        # Clear existing insights
        AIInsight.objects.all().delete()
        
        insights = [
            {
                'insight_type': 'forecast',
                'priority': 'high',
                'category': 'Production',
                'title': 'Demand Surge Expected',
                'description': 'AI predicts 23% increase in demand for next quarter',
                'impact': 'Requires 15% capacity increase',
                'confidence_score': 87
            },
            {
                'insight_type': 'anomaly',
                'priority': 'high',
                'category': 'Production',
                'title': 'Production Delay Detected',
                'description': 'PO-2025-002 is 15% behind schedule',
                'impact': 'May affect delivery timeline',
                'confidence_score': 92
            },
            {
                'insight_type': 'recommendation',
                'priority': 'medium',
                'category': 'Inventory',
                'title': 'Optimize Reorder Points',
                'description': 'Adjust reorder levels for 5 SKUs to reduce stockouts',
                'impact': 'Reduces stockouts by 30%',
                'confidence_score': 85
            },
            {
                'insight_type': 'prediction',
                'priority': 'medium',
                'category': 'Inventory',
                'title': 'Stockout Warning',
                'description': 'SKU BALL-002 predicted to run out in 45 days',
                'impact': 'Order 250 units to maintain stock',
                'confidence_score': 89
            },
            {
                'insight_type': 'anomaly',
                'priority': 'high',
                'category': 'Suppliers',
                'title': 'Supplier Risk Alert',
                'description': 'Supplier delivery reliability dropped 12%',
                'impact': 'Consider backup suppliers',
                'confidence_score': 81
            },
            {
                'insight_type': 'recommendation',
                'priority': 'low',
                'category': 'Finance',
                'title': 'Cash Flow Optimization',
                'description': 'Extend payment terms with key suppliers',
                'impact': 'Improves cash flow by $25K',
                'confidence_score': 78
            },
        ]
        
        created_count = 0
        for insight_data in insights:
            AIInsight.objects.create(**insight_data)
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} AI insights!'))
