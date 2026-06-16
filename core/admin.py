from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AuditLog, SystemNotification, AIInsight

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'department', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff', 'department']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'department', 'employee_id', 'is_active_employee')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'department', 'employee_id')
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'module', 'timestamp', 'ip_address']
    list_filter = ['module', 'timestamp']
    search_fields = ['user__username', 'action', 'description']
    readonly_fields = ['user', 'action', 'module', 'description', 'ip_address', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']



@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['title', 'insight_type', 'priority', 'category', 'confidence_score', 'is_actioned', 'created_at']
    list_filter = ['insight_type', 'priority', 'category', 'is_actioned', 'created_at']
    search_fields = ['title', 'description', 'category']
    readonly_fields = ['created_at', 'actioned_at']
    
    fieldsets = (
        ('Insight Information', {
            'fields': ('insight_type', 'priority', 'category', 'title', 'description', 'impact')
        }),
        ('AI Metrics', {
            'fields': ('confidence_score',)
        }),
        ('Action Status', {
            'fields': ('is_actioned', 'actioned_by', 'actioned_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
