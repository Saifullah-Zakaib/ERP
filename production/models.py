from django.db import models
from core.models import User
from inventory.models import InventoryItem

class ProductionOrder(models.Model):
    """Production orders"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PHASE_CHOICES = [
        ('cutting', 'Material Cutting'),
        ('stitching', 'Stitching/Assembly'),
        ('qc', 'Quality Control'),
        ('packing', 'Final Packing'),
    ]
    
    order_id = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=200)
    product_name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default='cutting')
    progress_percentage = models.IntegerField(default=0)
    assigned_machine = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'production_orders'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.order_id} - {self.product_name}"


class BillOfMaterials(models.Model):
    """Bill of Materials for production orders"""
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name='bom_items')
    material = models.ForeignKey(InventoryItem, on_delete=models.PROTECT)
    quantity_required = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_issued = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=20, default='units')
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'bill_of_materials'
        
    def __str__(self):
        return f"{self.production_order.order_id} - {self.material.name}"


class MaterialIssueNote(models.Model):
    """Material issue notes for production"""
    issue_number = models.CharField(max_length=50, unique=True)
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name='material_issues')
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    issue_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'material_issue_notes'
        ordering = ['-issue_date']
        
    def __str__(self):
        return f"{self.issue_number} - {self.production_order.order_id}"


class MaterialIssueItem(models.Model):
    """Items in material issue note"""
    issue_note = models.ForeignKey(MaterialIssueNote, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(InventoryItem, on_delete=models.PROTECT)
    quantity_issued = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'material_issue_items'
        
    def __str__(self):
        return f"{self.issue_note.issue_number} - {self.material.name}"


class ProductionTask(models.Model):
    """Individual tasks in production process"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]
    
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name='tasks')
    task_name = models.CharField(max_length=200)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'production_tasks'
        ordering = ['production_order', 'created_at']
        
    def __str__(self):
        return f"{self.production_order.order_id} - {self.task_name}"


class QualityCheck(models.Model):
    """Quality control checks"""
    RESULT_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('conditional', 'Conditional Pass'),
    ]
    
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name='quality_checks')
    check_date = models.DateTimeField(auto_now_add=True)
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    defects_found = models.IntegerField(default=0)
    comments = models.TextField()
    
    class Meta:
        db_table = 'quality_checks'
        ordering = ['-check_date']
        
    def __str__(self):
        return f"{self.production_order.order_id} - {self.result}"


class ProductionReport(models.Model):
    """Production efficiency and waste reports"""
    REPORT_TYPES = [
        ('efficiency', 'Efficiency Report'),
        ('waste', 'Waste Report'),
        ('output', 'Output Report'),
    ]
    
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    report_period = models.CharField(max_length=50)
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.SET_NULL, null=True, blank=True)
    estimated_materials = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actual_materials = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    waste_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    efficiency_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    file_path = models.FileField(upload_to='reports/production/', blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'production_reports'
        ordering = ['-generated_at']
        
    def __str__(self):
        return f"{self.report_type} - {self.report_period}"
    
    def calculate_waste(self):
        """Calculate waste percentage"""
        if self.estimated_materials > 0:
            waste = self.actual_materials - self.estimated_materials
            self.waste_percentage = (waste / self.estimated_materials) * 100
        return self.waste_percentage
