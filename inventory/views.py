from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Q
from datetime import date, timedelta
from decimal import Decimal
import json
from .models import InventoryItem, StockMovement, StockAlert, WarehouseReport, CustomerOrder
from core.models import AuditLog, SystemNotification
from core.views import role_required, get_client_ip
from production.models import ProductionOrder

@login_required
@role_required('inventory', 'admin')
def dashboard(request):
    """Inventory dashboard"""
    from django.utils import timezone
    
    # Check for low stock and out of stock items and create notifications
    today = timezone.now().date()
    
    # Get low stock items
    low_stock_items = InventoryItem.objects.filter(status='low_stock')
    
    for item in low_stock_items:
        # Check if notification already exists for this item today
        existing_notification = SystemNotification.objects.filter(
            user=request.user,
            title__contains='Low Stock Alert',
            message__contains=item.sku,
            created_at__date=today
        ).exists()
        
        if not existing_notification:
            SystemNotification.objects.create(
                user=request.user,
                title='Low Stock Alert',
                message=f'{item.name} (SKU: {item.sku}) is below reorder level. Current stock: {item.quantity}, Reorder level: {item.reorder_level}',
                notification_type='warning'
            )
    
    # Get out of stock items
    out_of_stock_items = InventoryItem.objects.filter(status='out_of_stock')
    
    for item in out_of_stock_items:
        # Check if notification already exists for this item today
        existing_notification = SystemNotification.objects.filter(
            user=request.user,
            title__contains='Out of Stock Alert',
            message__contains=item.sku,
            created_at__date=today
        ).exists()
        
        if not existing_notification:
            SystemNotification.objects.create(
                user=request.user,
                title='Out of Stock Alert',
                message=f'{item.name} (SKU: {item.sku}) is OUT OF STOCK! Immediate action required.',
                notification_type='danger'
            )
    
    # Get all inventory items
    inventory_items = InventoryItem.objects.all().order_by('name')
    
    # Get all customer orders
    customer_orders = CustomerOrder.objects.filter(status='pending').order_by('-created_at')
    
    # Get only inventory-related notifications for the user
    notifications = SystemNotification.objects.filter(
        user=request.user,
        is_read=False,
        title__in=['Low Stock Alert', 'Out of Stock Alert', 'Production Completed - Inventory Updated', 'Material Request from Inventory']
    ).order_by('-created_at')[:10]
    
    unread_notification_count = notifications.count()
    
    context = {
        'total_items': InventoryItem.objects.count(),
        'low_stock_items': InventoryItem.objects.filter(status='low_stock').count(),
        'out_of_stock_items': InventoryItem.objects.filter(status='out_of_stock').count(),
        'total_value': InventoryItem.objects.aggregate(
            total=Sum('quantity') * Sum('unit_price')
        )['total'] or 0,
        'recent_movements': StockMovement.objects.select_related('item', 'performed_by').all()[:10],
        'active_alerts': StockAlert.objects.filter(is_resolved=False).select_related('item'),
        'inventory_items': inventory_items,
        'customer_orders': customer_orders,
        'categories': InventoryItem.CATEGORY_CHOICES,
        'notifications': notifications,
        'unread_notification_count': unread_notification_count,
    }
    
    return render(request, 'inventory/dashboard.html', context)


@login_required
def item_list(request):
    """List all inventory items"""
    items = InventoryItem.objects.all()
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        items = items.filter(category=category)
    
    # Search
    search = request.GET.get('search')
    if search:
        items = items.filter(
            Q(sku__icontains=search) | 
            Q(name__icontains=search)
        )
    
    context = {
        'items': items,
        'categories': InventoryItem.CATEGORY_CHOICES,
    }
    
    return render(request, 'inventory/item_list.html', context)


@login_required
def item_detail(request, item_id):
    """View item details"""
    item = get_object_or_404(InventoryItem, id=item_id)
    movements = StockMovement.objects.filter(item=item)[:20]
    
    context = {
        'item': item,
        'movements': movements,
    }
    
    return render(request, 'inventory/item_detail.html', context)


@login_required
def add_item(request):
    """Add new inventory item"""
    if request.method == 'POST':
        item = InventoryItem.objects.create(
            sku=request.POST.get('sku'),
            name=request.POST.get('name'),
            category=request.POST.get('category'),
            description=request.POST.get('description', ''),
            quantity=int(request.POST.get('quantity', 0)),
            reorder_level=int(request.POST.get('reorder_level', 50)),
            unit_price=float(request.POST.get('unit_price', 0)),
            location=request.POST.get('location', 'Warehouse A'),
        )
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='Add Item',
            module='Inventory',
            description=f'Added item {item.sku} - {item.name}',
        )
        
        messages.success(request, 'Item added successfully!')
        return redirect('inventory:item_detail', item_id=item.id)
    
    return render(request, 'inventory/add_item.html', {
        'categories': InventoryItem.CATEGORY_CHOICES
    })


@login_required
def update_item(request, item_id):
    """Update inventory item"""
    item = get_object_or_404(InventoryItem, id=item_id)
    
    if request.method == 'POST':
        item.name = request.POST.get('name')
        item.category = request.POST.get('category')
        item.description = request.POST.get('description', '')
        item.quantity = int(request.POST.get('quantity', 0))
        item.reorder_level = int(request.POST.get('reorder_level', 50))
        item.unit_price = float(request.POST.get('unit_price', 0))
        item.location = request.POST.get('location', 'Warehouse A')
        item.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='Update Item',
            module='Inventory',
            description=f'Updated item {item.sku}',
        )
        
        messages.success(request, 'Item updated successfully!')
        return redirect('inventory:item_detail', item_id=item.id)
    
    return render(request, 'inventory/update_item.html', {
        'item': item,
        'categories': InventoryItem.CATEGORY_CHOICES
    })


@login_required
def record_movement(request):
    """Record stock movement"""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        item = get_object_or_404(InventoryItem, id=item_id)
        
        movement_type = request.POST.get('movement_type')
        quantity = int(request.POST.get('quantity'))
        
        # Create movement record
        movement = StockMovement.objects.create(
            item=item,
            movement_type=movement_type,
            quantity=quantity,
            reference_number=request.POST.get('reference_number', ''),
            notes=request.POST.get('notes', ''),
            performed_by=request.user,
        )
        
        # Update item quantity
        if movement_type == 'in':
            item.quantity += quantity
        elif movement_type == 'out':
            item.quantity -= quantity
        else:  # adjustment
            item.quantity = quantity
        
        item.save()
        
        # Check for low stock and create alert
        if item.quantity <= item.reorder_level:
            StockAlert.objects.get_or_create(
                item=item,
                alert_level=item.quantity,
                is_resolved=False
            )
            
            # Create notification
            SystemNotification.objects.create(
                user=request.user,
                title='Low Stock Alert',
                message=f'{item.name} (SKU: {item.sku}) is below reorder level',
                notification_type='warning'
            )
        
        AuditLog.objects.create(
            user=request.user,
            action='Stock Movement',
            module='Inventory',
            description=f'{movement_type.upper()} - {quantity} units of {item.sku}',
        )
        
        messages.success(request, 'Stock movement recorded successfully!')
        return redirect('inventory:item_detail', item_id=item.id)
    
    items = InventoryItem.objects.all()
    return render(request, 'inventory/record_movement.html', {'items': items})


@login_required
def check_order_status(request):
    """Check order status and determine action (AJAX)"""
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        product = request.POST.get('product')
        quantity = int(request.POST.get('quantity', 0))
        
        # Check inventory
        try:
            item = InventoryItem.objects.filter(name__icontains=product).first()
            
            if item and item.quantity >= quantity:
                # Stock available - ready to ship
                return JsonResponse({
                    'status': 'ready_to_ship',
                    'message': f'Full quantity ({quantity} units) found in {item.location}',
                    'action': 'ship'
                })
            elif item and item.quantity > 0:
                # Partial stock - need production
                return JsonResponse({
                    'status': 'production_needed',
                    'message': 'Raw materials exist. Production can start immediately.',
                    'action': 'production'
                })
            else:
                # Out of stock - need supplier
                return JsonResponse({
                    'status': 'out_of_stock',
                    'message': 'Insufficient raw materials. Procurement required.',
                    'action': 'supplier'
                })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@login_required
def alerts(request):
    """View all stock alerts"""
    alerts = StockAlert.objects.filter(is_resolved=False)
    
    if request.method == 'POST':
        alert_id = request.POST.get('alert_id')
        alert = get_object_or_404(StockAlert, id=alert_id)
        alert.is_resolved = True
        alert.save()
        
        messages.success(request, 'Alert resolved!')
        return redirect('inventory:alerts')
    
    return render(request, 'inventory/alerts.html', {'alerts': alerts})


@login_required
def reports(request):
    """Generate inventory reports"""
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        
        report = WarehouseReport.objects.create(
            report_type=report_type,
            generated_by=request.user,
        )
        
        messages.success(request, 'Report generated successfully!')
        return redirect('inventory:reports')
    
    reports = WarehouseReport.objects.all()[:20]
    return render(request, 'inventory/reports.html', {'reports': reports})



# ==================== API ENDPOINTS ====================

@login_required
@role_required('inventory', 'admin')
def add_item_api(request):
    """Add new inventory item via API"""
    if request.method == 'POST':
        try:
            sku = request.POST.get('sku', '').strip()
            name = request.POST.get('name', '').strip()
            quantity = int(request.POST.get('quantity', 0))
            reorder_level = int(request.POST.get('reorder_level', 50))
            category = request.POST.get('category', '')
            
            # Validate required fields
            if not all([sku, name, category]):
                return JsonResponse({
                    'success': False,
                    'message': 'All required fields must be filled'
                })
            
            # Check if SKU already exists
            if InventoryItem.objects.filter(sku=sku).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'SKU {sku} already exists'
                })
            
            # Create inventory item with default values
            item = InventoryItem.objects.create(
                sku=sku,
                name=name,
                quantity=quantity,
                reorder_level=reorder_level,
                unit_price=Decimal('0.00'),  # Default value
                location='Warehouse A',  # Default value
                category=category,
                description=''  # Default empty
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Add Inventory',
                module='Inventory',
                description=f'Added new item {item.sku} - {item.name}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Inventory item added successfully',
                'item': {
                    'id': item.id,
                    'sku': item.sku,
                    'name': item.name,
                    'quantity': item.quantity,
                    'reorder_level': item.reorder_level,
                    'category': item.category,
                    'status': item.get_status_display()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('inventory', 'admin')
def update_item_api(request, item_id):
    """Update inventory item via API"""
    if request.method == 'POST':
        try:
            item = get_object_or_404(InventoryItem, id=item_id)
            
            # Update fields
            item.name = request.POST.get('name', item.name)
            item.quantity = int(request.POST.get('quantity', item.quantity))
            item.reorder_level = int(request.POST.get('reorder_level', item.reorder_level))
            item.unit_price = Decimal(request.POST.get('unit_price', item.unit_price))
            item.location = request.POST.get('location', item.location)
            item.category = request.POST.get('category', item.category)
            item.description = request.POST.get('description', item.description)
            
            # Save will auto-update status based on quantity vs reorder_level
            item.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Update Item',
                module='Inventory',
                description=f'Updated {item.sku}: Qty={item.quantity}, Threshold={item.reorder_level}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Item updated successfully',
                'item': {
                    'id': item.id,
                    'sku': item.sku,
                    'name': item.name,
                    'quantity': item.quantity,
                    'reorder_level': item.reorder_level,
                    'unit_price': float(item.unit_price),
                    'status': item.get_status_display(),
                    'status_class': item.status
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('inventory', 'admin')
def add_order_api(request):
    """Add new customer order via API"""
    if request.method == 'POST':
        try:
            order_number = request.POST.get('order_number')
            customer_name = request.POST.get('customer_name')
            product_name = request.POST.get('product_name')
            quantity = int(request.POST.get('quantity'))
            
            # Validate required fields
            if not all([order_number, customer_name, product_name, quantity]):
                return JsonResponse({
                    'success': False,
                    'message': 'All fields are required'
                })
            
            # Check if order number already exists
            if CustomerOrder.objects.filter(order_number=order_number).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Order number already exists'
                })
            
            # Create order
            order = CustomerOrder.objects.create(
                order_number=order_number,
                customer_name=customer_name,
                product_name=product_name,
                quantity=quantity,
                status='pending',
                created_by=request.user
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Add Order',
                module='Inventory',
                description=f'Created order {order.order_number} for {customer_name}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Order created successfully',
                'order': {
                    'id': order.id,
                    'order_number': order.order_number,
                    'customer_name': order.customer_name,
                    'product_name': order.product_name,
                    'quantity': order.quantity,
                    'status': order.get_status_display()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('inventory', 'admin')
def check_order_status_api(request):
    """Check order status and determine action via API"""
    if request.method == 'POST':
        try:
            order_number = request.POST.get('order_number')
            product_name = request.POST.get('product_name')
            quantity = int(request.POST.get('quantity'))
            
            # Find matching inventory item
            item = InventoryItem.objects.filter(
                Q(name__icontains=product_name) | Q(sku__icontains=product_name)
            ).first()
            
            if not item:
                return JsonResponse({
                    'success': True,
                    'status': 'out_of_stock',
                    'message': 'Product not found in inventory. Procurement required.',
                    'action': 'supplier',
                    'available_quantity': 0
                })
            
            # Check stock availability
            if item.quantity >= quantity:
                # Full stock available
                return JsonResponse({
                    'success': True,
                    'status': 'ready_to_ship',
                    'message': f'Full quantity ({quantity} units) found in {item.location}.',
                    'action': 'ship',
                    'available_quantity': item.quantity,
                    'location': item.location,
                    'item_id': item.id
                })
            elif item.quantity > 0:
                # Partial stock - need production
                return JsonResponse({
                    'success': True,
                    'status': 'production_needed',
                    'message': f'Only {item.quantity} units available. Production needed for remaining {quantity - item.quantity} units.',
                    'action': 'production',
                    'available_quantity': item.quantity,
                    'needed_quantity': quantity - item.quantity,
                    'item_id': item.id
                })
            else:
                # Out of stock - need supplier
                return JsonResponse({
                    'success': True,
                    'status': 'out_of_stock',
                    'message': 'Insufficient raw materials. Procurement required.',
                    'action': 'supplier',
                    'available_quantity': 0,
                    'needed_quantity': quantity,
                    'item_id': item.id
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('inventory', 'admin')
def approve_order_api(request, order_id):
    """Approve and ship order via API"""
    if request.method == 'POST':
        try:
            order = get_object_or_404(CustomerOrder, id=order_id)
            
            # Find inventory item
            item = InventoryItem.objects.filter(
                Q(name__icontains=order.product_name) | Q(sku__icontains=order.product_name)
            ).first()
            
            if not item or item.quantity < order.quantity:
                return JsonResponse({
                    'success': False,
                    'message': 'Insufficient stock to approve order'
                })
            
            # Deduct stock
            item.quantity -= order.quantity
            item.save()
            
            # Update order status
            order.status = 'shipped'
            order.save()
            
            # Record stock movement
            StockMovement.objects.create(
                item=item,
                movement_type='out',
                quantity=order.quantity,
                reference_number=order.order_number,
                notes=f'Shipped to {order.customer_name}',
                performed_by=request.user
            )
            
            # Notify finance managers to create invoice for shipped order
            from core.models import User, SystemNotification
            finance_managers = User.objects.filter(role__in=['finance', 'admin'])
            for manager in finance_managers:
                SystemNotification.objects.create(
                    user=manager,
                    title='Order Shipped - Invoice Required',
                    message=f'Order {order.order_number} shipped to {order.customer_name}: {order.quantity} units of {order.product_name}. Please generate customer invoice.',
                    notification_type='info'
                )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Approve Order',
                module='Inventory',
                description=f'Approved and shipped order {order.order_number}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Order approved and ready to ship',
                'order_status': order.get_status_display()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('inventory', 'admin')
def send_to_production_api(request, order_id):
    """Send order to production via API"""
    if request.method == 'POST':
        try:
            order = get_object_or_404(CustomerOrder, id=order_id)
            instructions = request.POST.get('instructions', '')
            
            # Generate production order number
            last_po = ProductionOrder.objects.all().order_by('-id').first()
            if last_po and last_po.order_id:
                last_num = int(last_po.order_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            po_number = f"PO-{date.today().year}-{new_num:03d}"
            
            # Create production order with due date (7 days from today)
            due_date = date.today() + timedelta(days=7)
            
            production_order = ProductionOrder.objects.create(
                order_id=po_number,
                customer_name=order.customer_name,
                product_name=order.product_name,
                quantity=order.quantity,
                due_date=due_date,
                status='pending',
                notes=instructions or f'Production for customer order {order.order_number}',
                created_by=request.user
            )
            
            # Update customer order status
            order.status = 'in_production'
            order.notes = f'Production Order: {po_number}'
            order.save()
            
            # Create notifications for ALL production managers
            from core.models import User
            production_managers = User.objects.filter(role__in=['production', 'admin'])
            for manager in production_managers:
                SystemNotification.objects.create(
                    user=manager,
                    title='New Production Order',
                    message=f'Order {po_number} created: {order.quantity} units of {order.product_name} for {order.customer_name}',
                    notification_type='info'
                )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Send to Production',
                module='Inventory',
                description=f'Created production order {po_number} for {order.order_number}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Production order created successfully',
                'production_order_number': po_number
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('inventory', 'admin')
def request_materials_api(request, order_id):
    """Request raw materials from supplier via API"""
    if request.method == 'POST':
        try:
            order = get_object_or_404(CustomerOrder, id=order_id)
            notes = request.POST.get('notes', '')
            
            # Generate material request number
            from suppliers.models import MaterialRequest
            last_request = MaterialRequest.objects.all().order_by('-id').first()
            if last_request and last_request.request_number:
                last_num = int(last_request.request_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            request_number = f"MR-{date.today().year}-{new_num:04d}"
            
            # Create material request
            material_request = MaterialRequest.objects.create(
                request_number=request_number,
                requested_by=request.user,
                material_name=order.product_name,
                quantity_needed=order.quantity,
                urgency='high',
                reason=notes or f'Material needed for customer order {order.order_number}',
                status='pending'
            )
            
            # Create notifications for ALL supplier users
            from core.models import User
            supplier_users = User.objects.filter(role__in=['supplier', 'admin'])
            for supplier in supplier_users:
                SystemNotification.objects.create(
                    user=supplier,
                    title='Material Request from Inventory',
                    message=f'Material request {request_number}: {order.quantity} units of {order.product_name} needed for order {order.order_number}',
                    notification_type='info'
                )
            
            # Update order notes
            order.notes = f'Material request {request_number} created. {notes}'
            order.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Request Materials',
                module='Inventory',
                description=f'Created material request {request_number} for order {order.order_number}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Material request sent to supplier successfully',
                'material_request_number': request_number
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})



@login_required
def check_production_status_api(request):
    """Check if product is already in production and if raw materials are available"""
    if request.method == 'POST':
        try:
            product_name = request.POST.get('product_name')
            quantity = int(request.POST.get('quantity'))
            
            # Check if product is already in production
            from production.models import ProductionOrder
            
            existing_production = ProductionOrder.objects.filter(
                product_name__icontains=product_name,
                status__in=['pending', 'in_progress']
            ).first()
            
            if existing_production:
                # Product is already being produced
                return JsonResponse({
                    'success': True,
                    'in_production': True,
                    'production_order_number': existing_production.order_id,
                    'message': f'{existing_production.quantity} units already in production.',
                    'progress': existing_production.progress_percentage,
                    'expected_completion': existing_production.due_date.strftime('%Y-%m-%d') if existing_production.due_date else None
                })
            
            # Check if raw materials are available
            # Look for raw material items in inventory
            raw_materials = InventoryItem.objects.filter(
                category='raw_materials',
                quantity__gt=0
            )
            
            # Simple check: if we have any raw materials, production is possible
            raw_materials_available = raw_materials.exists()
            
            return JsonResponse({
                'success': True,
                'in_production': False,
                'raw_materials_available': raw_materials_available,
                'message': 'Raw materials available for production.' if raw_materials_available else 'Raw materials not available.',
                'raw_material_count': raw_materials.count()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
