from django.contrib import admin
from .models import (
    ProductionOrder, BillOfMaterials, MaterialIssueNote, 
    MaterialIssueItem, ProductionTask, QualityCheck, ProductionReport
)

@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer_name', 'product_name', 'quantity', 'status', 'progress_percentage', 'due_date']
    list_filter = ['status', 'current_phase', 'created_at']
    search_fields = ['order_id', 'customer_name', 'product_name']


@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(admin.ModelAdmin):
    list_display = ['production_order', 'material', 'quantity_required', 'quantity_issued']
    list_filter = ['production_order']


@admin.register(MaterialIssueNote)
class MaterialIssueNoteAdmin(admin.ModelAdmin):
    list_display = ['issue_number', 'production_order', 'issued_by', 'issue_date']
    list_filter = ['issue_date']
    search_fields = ['issue_number']


@admin.register(ProductionTask)
class ProductionTaskAdmin(admin.ModelAdmin):
    list_display = ['production_order', 'task_name', 'assigned_to', 'status']
    list_filter = ['status']


@admin.register(QualityCheck)
class QualityCheckAdmin(admin.ModelAdmin):
    list_display = ['production_order', 'inspector', 'result', 'defects_found', 'check_date']
    list_filter = ['result', 'check_date']


@admin.register(ProductionReport)
class ProductionReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'report_period', 'generated_by', 'generated_at']
    list_filter = ['report_type', 'generated_at']
