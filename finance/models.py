from django.db import models
from core.models import User
from suppliers.models import Supplier

class Invoice(models.Model):
    """Customer invoices"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200)
    invoice_date = models.DateField()
    due_date = models.DateField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-invoice_date']
        
    def __str__(self):
        return f"{self.invoice_number} - {self.customer_name}"


class InvoiceItem(models.Model):
    """Invoice line items"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=200)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        db_table = 'invoice_items'
        
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description}"
    
    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Expense(models.Model):
    """Company expenses"""
    CATEGORY_CHOICES = [
        ('raw_materials', 'Raw Materials'),
        ('labor', 'Labor Costs'),
        ('overhead', 'Overhead'),
        ('utilities', 'Utilities'),
        ('office_supplies', 'Office Supplies'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]
    
    expense_number = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    receipt_file = models.FileField(upload_to='receipts/', blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'expenses'
        ordering = ['-expense_date']
        
    def __str__(self):
        return f"{self.expense_number} - {self.description}"


class Payment(models.Model):
    """Payment records"""
    PAYMENT_TYPES = [
        ('supplier', 'Supplier Payment'),
        ('salary', 'Salary Payment'),
        ('expense', 'Expense Payment'),
        ('other', 'Other'),
    ]
    
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('online', 'Online Payment'),
    ]
    
    payment_number = models.CharField(max_length=50, unique=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    recipient = models.CharField(max_length=200)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date']
        
    def __str__(self):
        return f"{self.payment_number} - {self.recipient}"


class FinancialReport(models.Model):
    """Generated financial reports"""
    REPORT_TYPES = [
        ('income_statement', 'Income Statement'),
        ('balance_sheet', 'Balance Sheet'),
        ('cash_flow', 'Cash Flow Statement'),
        ('profit_loss', 'Profit & Loss'),
    ]
    
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    report_period = models.CharField(max_length=50)  # e.g., "Q3 2025"
    file_path = models.FileField(upload_to='reports/finance/', blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'financial_reports'
        ordering = ['-generated_at']
        
    def __str__(self):
        return f"{self.report_type} - {self.report_period}"


class Budget(models.Model):
    """Budget planning"""
    department = models.CharField(max_length=50)
    fiscal_year = models.CharField(max_length=10)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'budgets'
        unique_together = ['department', 'fiscal_year']
        
    def __str__(self):
        return f"{self.department} - {self.fiscal_year}"
    
    def save(self, *args, **kwargs):
        self.remaining_amount = self.allocated_amount - self.spent_amount
        super().save(*args, **kwargs)
