from django.core.management.base import BaseCommand
from inventory.models import InventoryItem, CustomerOrder
from core.models import User


class Command(BaseCommand):
    help = 'Create sample inventory data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample inventory data...')
        
        # Create inventory items
        items = [
            {
                'sku': 'BALL-001',
                'name': 'Soccer Ball - Professional',
                'category': 'balls',
                'description': 'Professional grade soccer ball',
                'quantity': 450,
                'reorder_level': 100,
                'unit_price': 1500.00,
                'location': 'Warehouse A'
            },
            {
                'sku': 'BALL-002',
                'name': 'Basketball - Indoor',
                'category': 'balls',
                'description': 'Indoor basketball',
                'quantity': 85,
                'reorder_level': 100,
                'unit_price': 1800.00,
                'location': 'Warehouse A'
            },
            {
                'sku': 'SHOE-001',
                'name': 'Running Shoes - Pro',
                'category': 'footwear',
                'description': 'Professional running shoes',
                'quantity': 200,
                'reorder_level': 50,
                'unit_price': 5000.00,
                'location': 'Warehouse B'
            },
            {
                'sku': 'GLOVE-001',
                'name': 'Goalkeeper Gloves',
                'category': 'equipment',
                'description': 'Professional goalkeeper gloves',
                'quantity': 30,
                'reorder_level': 40,
                'unit_price': 2500.00,
                'location': 'Warehouse A'
            },
            {
                'sku': 'JERSEY-001',
                'name': 'Team Jersey - Home',
                'category': 'apparel',
                'description': 'Home team jersey',
                'quantity': 150,
                'reorder_level': 80,
                'unit_price': 1200.00,
                'location': 'Warehouse C'
            },
        ]
        
        for item_data in items:
            item, created = InventoryItem.objects.get_or_create(
                sku=item_data['sku'],
                defaults=item_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {item.sku} - {item.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Already exists: {item.sku}'))
        
        # Create sample orders
        try:
            user = User.objects.filter(role='inventory').first() or User.objects.first()
            
            orders = [
                {
                    'order_number': '#ORD-READY-01',
                    'customer_name': 'Ali Khan',
                    'product_name': 'Football',
                    'quantity': 10,
                    'status': 'pending',
                    'created_by': user
                },
                {
                    'order_number': '#ORD-PROD-05',
                    'customer_name': 'Zain Ahmed',
                    'product_name': 'Gloves',
                    'quantity': 50,
                    'status': 'pending',
                    'created_by': user
                },
            ]
            
            for order_data in orders:
                order, created = CustomerOrder.objects.get_or_create(
                    order_number=order_data['order_number'],
                    defaults=order_data
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created order: {order.order_number}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Order already exists: {order.order_number}'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating orders: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('Sample data creation complete!'))
