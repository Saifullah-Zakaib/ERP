from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from production.models import ProductionOrder
from core.models import User, SystemNotification


class Command(BaseCommand):
    help = 'Check production orders close to due date and create notifications'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        
        # Check for orders due in 3 days or less
        warning_date = today + timedelta(days=3)
        
        # Get orders that are pending or in_progress and due soon
        orders_due_soon = ProductionOrder.objects.filter(
            status__in=['pending', 'in_progress'],
            due_date__lte=warning_date,
            due_date__gte=today
        )
        
        # Get production managers and admins
        production_users = User.objects.filter(role__in=['production', 'admin'])
        
        for order in orders_due_soon:
            days_until_due = (order.due_date - today).days
            
            # Check if notification already exists for this order today
            existing_notification = SystemNotification.objects.filter(
                title__contains=f'Order {order.order_id}',
                created_at__date=today
            ).exists()
            
            if not existing_notification:
                # Determine urgency
                if days_until_due == 0:
                    urgency = 'URGENT'
                    notification_type = 'danger'
                    message = f'Order {order.order_id} for {order.customer_name} is due TODAY! Current progress: {order.progress_percentage}%'
                elif days_until_due == 1:
                    urgency = 'HIGH'
                    notification_type = 'warning'
                    message = f'Order {order.order_id} for {order.customer_name} is due TOMORROW! Current progress: {order.progress_percentage}%'
                else:
                    urgency = 'MEDIUM'
                    notification_type = 'warning'
                    message = f'Order {order.order_id} for {order.customer_name} is due in {days_until_due} days. Current progress: {order.progress_percentage}%'
                
                # Create notification for each production user
                for user in production_users:
                    SystemNotification.objects.create(
                        user=user,
                        title=f'{urgency}: Production Order Due Soon',
                        message=message,
                        notification_type=notification_type
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created notifications for order {order.order_id} (due in {days_until_due} days)'
                    )
                )
        
        # Check for overdue orders
        overdue_orders = ProductionOrder.objects.filter(
            status__in=['pending', 'in_progress'],
            due_date__lt=today
        )
        
        for order in overdue_orders:
            days_overdue = (today - order.due_date).days
            
            # Check if notification already exists for this order today
            existing_notification = SystemNotification.objects.filter(
                title__contains=f'Order {order.order_id}',
                created_at__date=today
            ).exists()
            
            if not existing_notification:
                message = f'Order {order.order_id} for {order.customer_name} is {days_overdue} day(s) OVERDUE! Current progress: {order.progress_percentage}%'
                
                # Create notification for each production user
                for user in production_users:
                    SystemNotification.objects.create(
                        user=user,
                        title='OVERDUE: Production Order',
                        message=message,
                        notification_type='danger'
                    )
                
                self.stdout.write(
                    self.style.WARNING(
                        f'Created overdue notifications for order {order.order_id} ({days_overdue} days overdue)'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Checked {orders_due_soon.count()} orders due soon and {overdue_orders.count()} overdue orders'
            )
        )
