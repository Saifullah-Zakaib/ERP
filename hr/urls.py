from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.add_employee, name='add_employee'),
    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('attendance/', views.attendance, name='attendance'),
    path('leave-requests/', views.leave_requests, name='leave_requests'),
    path('leave-requests/create/', views.create_leave_request, name='create_leave_request'),
    path('leave-requests/<int:request_id>/approve/', views.approve_leave, name='approve_leave'),
    path('payroll/', views.payroll_management, name='payroll'),
    path('payroll/run/', views.run_payroll, name='run_payroll'),
    
    # Reports
    path('reports/performance/', views.performance_report, name='performance_report'),
    
    # API endpoints
    path('api/employees/add/', views.add_employee_api, name='add_employee_api'),
    path('api/employees/<int:employee_id>/update/', views.update_employee_api, name='update_employee_api'),
    path('api/leave-requests/create/', views.create_leave_request_api, name='create_leave_request_api'),
    path('api/leave-requests/<int:request_id>/approve/', views.approve_leave_api, name='approve_leave_api'),
    path('api/payroll/process/', views.process_payroll_api, name='process_payroll_api'),
    path('api/finance/communicate/', views.communicate_finance, name='communicate_finance'),
]
