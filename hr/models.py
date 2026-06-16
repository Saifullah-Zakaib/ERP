from django.db import models
from core.models import User
from decimal import Decimal

class Employee(models.Model):
    """Employee information"""
    DEPARTMENT_CHOICES = [
        ('production', 'Production'),
        ('inventory', 'Inventory'),
        ('supplier', 'Supplier'),
        ('hr', 'HR'),
        ('finance', 'Finance'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    employee_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    position = models.CharField(max_length=100)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2)
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employees'
        ordering = ['first_name', 'last_name']
        
    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Attendance(models.Model):
    """Employee attendance tracking"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'On Leave'),
        ('half_day', 'Half Day'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'attendance'
        unique_together = ['employee', 'date']
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.employee.full_name} - {self.date} - {self.status}"


class LeaveRequest(models.Model):
    """Employee leave requests"""
    LEAVE_TYPES = [
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('annual', 'Annual Leave'),
        ('emergency', 'Emergency Leave'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'leave_requests'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} - {self.status}"


class Payroll(models.Model):
    """Payroll processing records"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payroll_records')
    pay_period = models.CharField(max_length=50)  # e.g., "October 2025"
    gross_pay = models.DecimalField(max_digits=10, decimal_places=2)
    federal_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    state_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    social_security = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    medicare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payroll'
        ordering = ['-payment_date']
        
    def __str__(self):
        return f"{self.employee.full_name} - {self.pay_period}"
    
    def calculate_net_pay(self):
        """Calculate net pay after deductions"""
        total_deductions = (
            self.federal_tax + 
            self.state_tax + 
            self.social_security + 
            self.medicare + 
            self.other_deductions
        )
        self.net_pay = self.gross_pay - total_deductions
        return self.net_pay


class PerformanceReview(models.Model):
    """Employee performance reviews"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    review_period = models.CharField(max_length=50)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 rating
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'performance_reviews'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.employee.full_name} - {self.review_period} - {self.rating}/5"
