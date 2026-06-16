from django.contrib import admin
from .models import Employee, Attendance, LeaveRequest, Payroll, PerformanceReview

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'email', 'department', 'position', 'is_active']
    list_filter = ['department', 'is_active', 'hire_date']
    search_fields = ['employee_id', 'first_name', 'last_name', 'email']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'status', 'check_in', 'check_out']
    list_filter = ['status', 'date']
    search_fields = ['employee__first_name', 'employee__last_name']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status']
    list_filter = ['leave_type', 'status', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name']


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ['employee', 'pay_period', 'gross_pay', 'net_pay', 'payment_date', 'is_paid']
    list_filter = ['is_paid', 'payment_date']
    search_fields = ['employee__first_name', 'employee__last_name']


@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ['employee', 'reviewer', 'review_period', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
