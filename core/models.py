from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    """Extended User model with role-based access"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('inventory', 'Inventory Manager'),
        ('production', 'Production Manager'),
        ('hr', 'HR Manager'),
        ('finance', 'Finance Manager'),
        ('supplier', 'Purchase Manager'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=50, blank=True)
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_active_employee = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class AuditLog(models.Model):
    """Track all system activities"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    module = models.CharField(max_length=50)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.user} - {self.action} at {self.timestamp}"


class SystemNotification(models.Model):
    """System-wide notifications"""
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
        ('success', 'Success'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.user}"


class Notice(models.Model):
    """Company-wide notices and announcements"""
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('holiday', 'Holiday'),
        ('policy', 'Policy Update'),
        ('event', 'Event'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notices'
        ordering = ['-is_pinned', '-created_at']
        
    def __str__(self):
        return self.title

# ==================== PASSWORD RESET FUNCTIONALITY ====================
class PasswordResetRequest(models.Model):
    """Password reset requests from users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_requests')
    is_approved = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        status = "Approved" if self.is_approved else "Pending"
        if self.is_completed:
            status = "Completed"
        return f"{self.user.username} - {status}"
    
    def approve(self):
        self.is_approved = True
        self.approved_at = timezone.now()
        self.save()
    
    def complete(self):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
    
    class Meta:
        ordering = ['-requested_at']
        verbose_name = 'Password Reset Request'
        verbose_name_plural = 'Password Reset Requests'



class AIInsight(models.Model):
    """Store AI-generated insights for historical tracking"""
    INSIGHT_TYPES = [
        ('forecast', 'Demand Forecast'),
        ('anomaly', 'Anomaly Detection'),
        ('recommendation', 'Recommendation'),
        ('prediction', 'Prediction'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=50)  # Production, Inventory, etc.
    title = models.CharField(max_length=200)
    description = models.TextField()
    impact = models.CharField(max_length=200, blank=True)
    confidence_score = models.IntegerField(default=80)  # 0-100
    is_actioned = models.BooleanField(default=False)
    actioned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    actioned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_insights'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['insight_type', 'priority']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_insight_type_display()} - {self.title}"
    
    def mark_actioned(self, user):
        """Mark insight as actioned"""
        self.is_actioned = True
        self.actioned_by = user
        self.actioned_at = timezone.now()
        self.save()
