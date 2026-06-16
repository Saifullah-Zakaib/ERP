from django.contrib import admin
from .models import Supplier, PurchaseOrder, PurchaseOrderItem, SupplierPerformance, MaterialRequest

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['supplier_id', 'name', 'category', 'contact_person', 'status', 'rating']
    list_filter = ['category', 'status']
    search_fields = ['supplier_id', 'name', 'contact_person']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'supplier', 'order_date', 'expected_delivery', 'total_amount', 'status']
    list_filter = ['status', 'order_date']
    search_fields = ['po_number', 'supplier__name']


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'item_name', 'quantity', 'unit_price', 'total']


@admin.register(SupplierPerformance)
class SupplierPerformanceAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'evaluation_period', 'overall_rating', 'created_at']
    list_filter = ['created_at']


@admin.register(MaterialRequest)
class MaterialRequestAdmin(admin.ModelAdmin):
    list_display = ['request_number', 'material_name', 'quantity_needed', 'urgency', 'status']
    list_filter = ['status', 'urgency', 'created_at']
    search_fields = ['request_number', 'material_name']
