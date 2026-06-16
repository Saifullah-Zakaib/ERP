from django.contrib import admin
from .models import Invoice, InvoiceItem, Expense, Payment, FinancialReport, Budget

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer_name', 'invoice_date', 'total_amount', 'status']
    list_filter = ['status', 'invoice_date']
    search_fields = ['invoice_number', 'customer_name']


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'description', 'quantity', 'unit_price', 'total']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['expense_number', 'category', 'description', 'amount', 'expense_date']
    list_filter = ['category', 'expense_date']
    search_fields = ['expense_number', 'description']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'payment_type', 'recipient', 'amount', 'payment_date']
    list_filter = ['payment_type', 'payment_method', 'payment_date']
    search_fields = ['payment_number', 'recipient']


@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'report_period', 'generated_by', 'generated_at']
    list_filter = ['report_type', 'generated_at']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['department', 'fiscal_year', 'allocated_amount', 'spent_amount', 'remaining_amount']
    list_filter = ['department', 'fiscal_year']
