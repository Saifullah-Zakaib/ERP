from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.create_invoice, name='create_invoice'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/record/', views.record_payment, name='record_payment'),
    path('reports/', views.reports, name='reports'),
    path('reports/financial-summary/', views.financial_summary_report, name='financial_summary_report'),
    
    # API endpoints
    path('api/dashboard/', views.dashboard_api, name='dashboard_api'),
    path('api/customers/', views.get_customers_api, name='get_customers_api'),
    path('api/invoices/create/', views.create_invoice_api, name='create_invoice_api'),
    path('api/invoices/<int:invoice_id>/update-status/', views.update_invoice_status_api, name='update_invoice_status_api'),
    path('api/payments/record/', views.record_payment_api, name='record_payment_api'),
    path('api/reports/generate/', views.generate_report_api, name='generate_report_api'),
    path('api/export/pdf/', views.export_financial_summary_pdf, name='export_financial_summary_pdf'),
    path('api/export/excel/', views.export_financial_excel, name='export_financial_excel'),
    path('invoices/<int:invoice_id>/pdf/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
    path('reports/<str:report_type>/pdf/', views.generate_financial_report_pdf, name='generate_financial_report_pdf'),
]
