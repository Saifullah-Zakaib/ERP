from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from production.models import ProductionOrder
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Create dummy production orders for testing'

    def handle(self, *args, **kwargs):
        # Get or create a production user
        try:
            user = User.objects.filter(role='production').first()
            if not user:
                user = User.objects.filter(role='admin').first()
            
            if not user:
                self.stdout.write(self.style.ERROR('No production or admin user found. Please create users first.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error finding user: {str(e)}'))
            return

        # Clear existing production orders (optional)
        ProductionOrder.objects.all().delete()
        self.stdout.write(self.style.WARNING('Cleared existing production orders'))

        # Create sample production orders
        orders_data = [
            {
                'order_id': 'PO-2026-001',
                'customer_name': 'Sports Arena Ltd',
                'product_name': 'Soccer Ball - Professional',
                'quantity': 500,
                'due_date': date.today() + timedelta(days=7),
                'status': 'in_progress',
                'current_phase': 'stitching',
                'progress_percentage': 45,
                'assigned_machine': 'Machine-A1'
            },
            {
                'order_id': 'PO-2026-002',
                'customer_name': 'Elite Sports Club',
                'product_name': 'Basketball - Premium',
                'quantity': 300,
                'due_date': date.today() + timedelta(days=10),
                'status': 'in_progress',
                'current_phase': 'qc',
                'progress_percentage': 75,
                'assigned_machine': 'Machine-B2'
            },
            {
                'order_id': 'PO-2026-003',
                'customer_name': 'City Sports Center',
                'product_name': 'Running Shoes - Pro',
                'quantity': 200,
                'due_date': date.today() + timedelta(days=5),
                'status': 'pending',
                'current_phase': 'cutting',
                'progress_percentage': 0,
                'assigned_machine': ''
            },
            {
                'order_id': 'PO-2026-004',
                'customer_name': 'National Team',
                'product_name': 'Team Jersey - Custom',
                'quantity': 150,
                'due_date': date.today() + timedelta(days=14),
                'status': 'in_progress',
                'current_phase': 'cutting',
                'progress_percentage': 25,
                'assigned_machine': 'Machine-C3'
            },
            {
                'order_id': 'PO-2026-005',
                'customer_name': 'Youth Academy',
                'product_name': 'Goalkeeper Gloves',
                'quantity': 100,
                'due_date': date.today() + timedelta(days=3),
                'status': 'completed',
                'current_phase': 'packing',
                'progress_percentage': 100,
                'assigned_machine': 'Machine-D1'
            }
        ]

        for order_data in orders_data:
            order = ProductionOrder.objects.create(
                order_id=order_data['order_id'],
                customer_name=order_data['customer_name'],
                product_name=order_data['product_name'],
                quantity=order_data['quantity'],
                due_date=order_data['due_date'],
                status=order_data['status'],
                current_phase=order_data['current_phase'],
                progress_percentage=order_data['progress_percentage'],
                assigned_machine=order_data['assigned_machine'],
                created_by=user
            )
            
            self.stdout.write(self.style.SUCCESS(f'Created production order: {order.order_id}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Successfully created 5 sample production orders!'))
        self.stdout.write(self.style.SUCCESS('You can now test the production module.'))
