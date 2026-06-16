from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from suppliers.models import Supplier, PurchaseOrder, PurchaseOrderItem, SupplierPerformance
from core.models import User


class Command(BaseCommand):
    help = 'Create sample supplier and purchase order data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample supplier data...')
        
        # Get or create a user for created_by field
        try:
            user = User.objects.filter(role__in=['supplier', 'admin']).first()
            if not user:
                user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting user: {e}'))
            return
        
        # Sample suppliers data
        suppliers_data = [
            {
                'supplier_id': 'SUP-0001',
                'name': 'Global Textiles Ltd',
                'category': 'textiles',
                'contact_person': 'John Smith',
                'email': 'john@globaltextiles.com',
                'phone': '+92-300-1234567',
                'address': '123 Industrial Area',
                'city': 'Karachi',
                'country': 'Pakistan',
                'payment_terms': 'Net 30',
                'rating': Decimal('4.5')
            },
            {
                'supplier_id': 'SUP-0002',
                'name': 'Premium Raw Materials Co',
                'category': 'raw_materials',
