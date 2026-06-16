from django.db import models
from core.models import User

class Supplier(models.Model):
    """Supplier/Vendor information"""
    CATEGORY_CHOICES = [
        ('raw_materials', 'Raw Materials'),
        ('textiles', 'Textiles'),
        ('packaging', 'Packaging'),
        ('components', 'Components'),
        ('equipment', 'Equipment'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('blacklisted', 'Blacklisted'),
    ]
    
    supplier_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(max_length=100, default='Net 30')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)  # 0-5 rating
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'suppliers'
        ordering = ['name']
        
    def __str__(self):
        return f"{self.supplier_id} - {self.name}"


class PurchaseOrder(models.Model):
    """Purchase orders to suppliers"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('sent', 'Sent to Supplier'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_orders')
    supplier_name = models.CharField(max_length=200, blank=True)  # Store supplier name for history
    order_date = models.DateField()
    expected_delivery = models.DateField()
    actual_delivery = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_pos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-order_date']
        
    def __str__(self):
        supplier_display = self.supplier.name if self.supplier else self.supplier_name or "Deleted Supplier"
        return f"{self.po_number} - {supplier_display}"
    
    def get_supplier_name(self):
        """Get supplier name, handling deleted suppliers"""
        return self.supplier.name if self.supplier else self.supplier_name or "Deleted Supplier"
    
    def save(self, *args, **kwargs):
        # Store supplier name for historical reference
        if self.supplier and not self.supplier_name:
            self.supplier_name = self.supplier.name
        super().save(*args, **kwargs)


class PurchaseOrderItem(models.Model):
    """Purchase order line items"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    received_quantity = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'purchase_order_items'
        
    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class SupplierPerformance(models.Model):
    """Track supplier performance metrics"""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='performance_records')
    evaluation_period = models.CharField(max_length=50)
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage
    quality_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5
    price_competitiveness = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    communication_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2)
    comments = models.TextField(blank=True)
    evaluated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'supplier_performance'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.supplier.name} - {self.evaluation_period}"
    
    def calculate_overall_rating(self):
        """Calculate overall rating from individual metrics"""
        self.overall_rating = (
            self.quality_rating + 
            self.price_competitiveness + 
            self.communication_rating
        ) / 3
        return self.overall_rating


class MaterialRequest(models.Model):
    """Material requests from inventory to purchase"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('rejected', 'Rejected'),
    ]
    
    request_number = models.CharField(max_length=50, unique=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    material_name = models.CharField(max_length=200)
    quantity_needed = models.IntegerField()
    urgency = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ])
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'material_requests'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.request_number} - {self.material_name}"
