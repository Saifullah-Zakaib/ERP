from django.db import models
from core.models import User

class InventoryItem(models.Model):
    """Inventory items/products"""
    CATEGORY_CHOICES = [
        ('balls', 'Balls'),
        ('footwear', 'Footwear'),
        ('apparel', 'Apparel'),
        ('equipment', 'Equipment'),
        ('raw_materials', 'Raw Materials'),
    ]
    
    STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=50)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=100, default='Warehouse A')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_stock')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_items'
        ordering = ['name']
        
    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Auto-update status based on quantity
        if self.quantity == 0:
            self.status = 'out_of_stock'
        elif self.quantity <= self.reorder_level:
            self.status = 'low_stock'
        else:
            self.status = 'in_stock'
        super().save(*args, **kwargs)


class StockMovement(models.Model):
    """Track incoming and outgoing stock"""
    MOVEMENT_TYPES = [
        ('in', 'Incoming'),
        ('out', 'Outgoing'),
        ('adjustment', 'Adjustment'),
    ]
    
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'stock_movements'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.item.sku} - {self.movement_type} - {self.quantity}"


class StockAlert(models.Model):
    """Reorder alerts for low stock items"""
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='alerts')
    alert_level = models.IntegerField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'stock_alerts'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Alert for {self.item.sku}"


class WarehouseReport(models.Model):
    """Generated warehouse reports"""
    REPORT_TYPES = [
        ('stock_summary', 'Stock Summary'),
        ('movement_report', 'Movement Report'),
        ('valuation', 'Inventory Valuation'),
    ]
    
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file_path = models.FileField(upload_to='reports/inventory/', blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'warehouse_reports'
        ordering = ['-generated_at']
        
    def __str__(self):
        return f"{self.report_type} - {self.generated_at}"


class CustomerOrder(models.Model):
    """Customer orders"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('in_production', 'In Production'),
        ('shipped', 'Shipped'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200)
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customer_orders'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.order_number} - {self.customer_name}"
