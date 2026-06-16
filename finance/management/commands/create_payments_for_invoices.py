from django.core.management.base import BaseCommand
from django.utils import timezone
from finance.models import Invoice, Payment
from core.models import User

class Command(BaseCommand):
    help = 'Create payment records for existing paid invoices'

    def handle(self, *args, **kwargs):
        # Get admin user
        admin = User.objects.filter(role='admin').first()
        if not admin:
            self.stdout.write(self.style.ERROR('No admin user found'))
            return
        
        # Get all paid invoices
        paid_invoices = Invoice.objects.filter(status='paid')
        self.stdout.write(f'Found {paid_invoices.count()} paid invoices')
        
        created_count = 0
        for invoice in paid_invoices:
            # Check if payment already exists for this invoice
            existing_payment = Payment.objects.filter(reference_number=invoice.invoice_number).first()
            if existing_payment:
                self.stdout.write(f'Payment already exists for invoice {invoice.invoice_number}')
                continue
            
            # Generate payment number
            last_payment = Payment.objects.all().order_by('-id').first()
            if last_payment and last_payment.payment_number:
                last_num = int(last_payment.payment_number.split('-')[1])
                new_num = last_num + 1
            else:
                new_num = 1
            payment_number = f'PAY-{new_num:05d}'
            
            # Create payment
            payment = Payment.objects.create(
                payment_number=payment_number,
                payment_type='other',
                payment_method='bank_transfer',
                amount=invoice.total_amount,
                payment_date=invoice.invoice_date,
                recipient=invoice.customer_name,
                reference_number=invoice.invoice_number,
                notes=f'Payment received for invoice {invoice.invoice_number}',
                processed_by=admin
            )
            
            self.stdout.write(self.style.SUCCESS(f'Created payment {payment_number} for invoice {invoice.invoice_number}'))
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\nTotal payments created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total payments in database: {Payment.objects.count()}'))
