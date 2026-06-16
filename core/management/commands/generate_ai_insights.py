"""
Management command to test AI insights generation
"""
from django.core.management.base import BaseCommand
from core.ai_utils import AIInsightsEngine
from production.models import ProductionOrder
from inventory.models import InventoryItem
from suppliers.models import Supplier


class Command(BaseCommand):
    help = 'Generate and display AI insights for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Generating AI Insights...'))
        
        # Get data
        production_orders = ProductionOrder.objects.all()[:10]
        inventory_items = InventoryItem.objects.all()[:10]
        suppliers = Supplier.objects.all()[:5]
        
        # Initialize AI engine
        ai_engine = AIInsightsEngine()
        
        # Generate insights
        self.stdout.write('\n=== Demand Forecast ===')
        forecast = ai_engine.generate_demand_forecast()
        self.stdout.write(f"Recommendation: {forecast['recommendation']}")
        
        self.stdout.write('\n=== Anomalies Detected ===')
        anomalies = ai_engine.detect_anomalies(production_orders, inventory_items, suppliers)
        for anomaly in anomalies:
            self.stdout.write(f"[{anomaly['severity'].upper()}] {anomaly['title']}: {anomaly['description']}")
        
        self.stdout.write('\n=== AI Recommendations ===')
        recommendations = ai_engine.generate_recommendations(production_orders, inventory_items, suppliers)
        for rec in recommendations:
            self.stdout.write(f"[{rec['priority']}] {rec['category']}: {rec['recommendation']}")
        
        self.stdout.write('\n=== AI Health ===')
        health = ai_engine.calculate_ai_health()
        self.stdout.write(f"Accuracy: {health['accuracy']}%")
        self.stdout.write(f"Data Quality: {health['data_quality']}%")
        self.stdout.write(f"Model Confidence: {health['model_confidence']}%")
        
        self.stdout.write(self.style.SUCCESS('\nAI Insights generated successfully!'))
