from django.contrib import admin
from .models import InventoryItem, StockMovement, StockAlert, WarehouseReport

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'quantity', 'status', 'reorder_level']
    list_filter = ['category', 'status']
    search_fields = ['sku', 'name']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['item', 'movement_type', 'quantity', 'performed_by', 'timestamp']
    list_filter = ['movement_type', 'timestamp']
    search_fields = ['item__sku', 'item__name', 'reference_number']


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['item', 'alert_level', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'created_at']


@admin.register(WarehouseReport)
class WarehouseReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'generated_by', 'generated_at']
    list_filter = ['report_type', 'generated_at']
