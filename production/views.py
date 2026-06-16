from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import date
from .models import (
    ProductionOrder, BillOfMaterials, MaterialIssueNote, 
    MaterialIssueItem, ProductionTask, QualityCheck, ProductionReport
)
from inventory.models import InventoryItem, StockMovement
from core.models import AuditLog, SystemNotification
from core.views import role_required, get_client_ip

@login_required
@role_required('production', 'admin')
def dashboard(request):
    """Production dashboard"""
    from datetime import timedelta
    
    # Check for orders close to due date and create notifications
    today = timezone.now().date()
    warning_date = today + timedelta(days=3)
    
    # Get orders due soon
    orders_due_soon = ProductionOrder.objects.filter(
        status__in=['pending', 'in_progress'],
        due_date__lte=warning_date,
        due_date__gte=today
    )
    
    # Create notifications for orders due soon (if not already notified today)
    for order in orders_due_soon:
        days_until_due = (order.due_date - today).days
        
        # Check if notification already exists for this order today
        existing_notification = SystemNotification.objects.filter(
            user=request.user,
            title__contains=f'Order {order.order_id}',
            created_at__date=today
        ).exists()
        
        if not existing_notification:
            if days_until_due == 0:
                urgency = 'URGENT'
                notification_type = 'danger'
                message = f'Order {order.order_id} for {order.customer_name} is due TODAY! Current progress: {order.progress_percentage}%'
            elif days_until_due == 1:
                urgency = 'HIGH'
                notification_type = 'warning'
                message = f'Order {order.order_id} for {order.customer_name} is due TOMORROW! Current progress: {order.progress_percentage}%'
            else:
                urgency = 'MEDIUM'
                notification_type = 'warning'
                message = f'Order {order.order_id} for {order.customer_name} is due in {days_until_due} days. Current progress: {order.progress_percentage}%'
            
            SystemNotification.objects.create(
                user=request.user,
                title=f'{urgency}: Production Order Due Soon',
                message=message,
                notification_type=notification_type
            )
    
    # Check for overdue orders
    overdue_orders = ProductionOrder.objects.filter(
        status__in=['pending', 'in_progress'],
        due_date__lt=today
    )
    
    for order in overdue_orders:
        days_overdue = (today - order.due_date).days
        
        # Check if notification already exists for this order today
        existing_notification = SystemNotification.objects.filter(
            user=request.user,
            title__contains=f'Order {order.order_id}',
            created_at__date=today
        ).exists()
        
        if not existing_notification:
            message = f'Order {order.order_id} for {order.customer_name} is {days_overdue} day(s) OVERDUE! Current progress: {order.progress_percentage}%'
            
            SystemNotification.objects.create(
                user=request.user,
                title='OVERDUE: Production Order',
                message=message,
                notification_type='danger'
            )
    
    context = {
        'total_orders': ProductionOrder.objects.count(),
        'pending_orders': ProductionOrder.objects.filter(status='pending').count(),
        'in_progress_orders': ProductionOrder.objects.filter(status='in_progress').count(),
        'completed_orders': ProductionOrder.objects.filter(status='completed').count(),
        'active_orders': ProductionOrder.objects.filter(
            status__in=['pending', 'in_progress']
        ).order_by('-created_at')[:10],
        'all_orders': ProductionOrder.objects.all().order_by('-created_at')[:20],
        'recent_quality_checks': QualityCheck.objects.select_related('production_order').all()[:5],
        'material_issues': MaterialIssueNote.objects.select_related('production_order').all()[:5],
    }
    
    return render(request, 'production/dashboard.html', context)


@login_required
def order_list(request):
    """List all production orders"""
    orders = ProductionOrder.objects.all()
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    context = {
        'orders': orders,
        'status_choices': ProductionOrder.STATUS_CHOICES,
    }
    
    return render(request, 'production/order_list.html', context)


@login_required
def create_order(request):
    """Create new production order"""
    if request.method == 'POST':
        order = ProductionOrder.objects.create(
            order_id=request.POST.get('order_id'),
            customer_name=request.POST.get('customer_name'),
            product_name=request.POST.get('product_name'),
            quantity=int(request.POST.get('quantity')),
            due_date=request.POST.get('due_date'),
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='Create Production Order',
            module='Production',
            description=f'Created order {order.order_id} for {order.customer_name}',
        )
        
        # Create notification for other production managers and admins (not the creator)
        from core.models import User
        production_users = User.objects.filter(
            role__in=['production', 'admin']
        ).exclude(id=request.user.id)  # Exclude the creator
        
        for user in production_users:
            SystemNotification.objects.create(
                user=user,
                title='Production Order Created',
                message=f'Order {order.order_id} has been created by {request.user.get_full_name() or request.user.username}',
                notification_type='success'
            )
        
        messages.success(request, 'Production order created successfully!')
        return redirect('production:order_detail', order_id=order.id)
    
    return render(request, 'production/create_order.html')


@login_required
def order_detail(request, order_id):
    """View production order details"""
    order = get_object_or_404(ProductionOrder, id=order_id)
    bom_items = BillOfMaterials.objects.filter(production_order=order)
    tasks = ProductionTask.objects.filter(production_order=order)
    quality_checks = QualityCheck.objects.filter(production_order=order)
    
    context = {
        'order': order,
        'bom_items': bom_items,
        'tasks': tasks,
        'quality_checks': quality_checks,
    }
    
    return render(request, 'production/order_detail.html', context)


@login_required
def update_order_status(request, order_id):
    """Update production order status (AJAX)"""
    if request.method == 'POST':
        order = get_object_or_404(ProductionOrder, id=order_id)
        
        old_status = order.status
        order.progress_percentage = int(request.POST.get('progress', 0))
        order.current_phase = request.POST.get('phase', 'cutting')
        order.assigned_machine = request.POST.get('machine', '')
        
        # Update status based on progress
        if order.progress_percentage == 100:
            order.status = 'completed'
            order.completed_at = timezone.now()
            
            # Automatically add completed product to inventory
            from inventory.models import InventoryItem, StockMovement
            
            # Generate SKU for the product
            product_name_short = ''.join([word[0].upper() for word in order.product_name.split()[:3]])
            sku_base = f"{product_name_short}-{order.order_id.split('-')[-1]}"
            
            # Check if item already exists in inventory
            inventory_item, created = InventoryItem.objects.get_or_create(
                name=order.product_name,
                defaults={
                    'sku': sku_base,
                    'category': 'equipment',  # Default category, can be adjusted
                    'description': f'Produced from order {order.order_id} for {order.customer_name}',
                    'quantity': order.quantity,
                    'reorder_level': 50,
                    'unit_price': 0,  # Price can be set later
                    'location': 'Warehouse A',
                }
            )
            
            if not created:
                # Item exists, update quantity
                inventory_item.quantity += order.quantity
                inventory_item.save()
            
            # Create stock movement record
            StockMovement.objects.create(
                item=inventory_item,
                movement_type='in',
                quantity=order.quantity,
                reference_number=order.order_id,
                notes=f'Completed production order {order.order_id}',
                performed_by=request.user
            )
            
            # Create notification for inventory managers
            from core.models import User, SystemNotification
            inventory_managers = User.objects.filter(role__in=['inventory', 'admin'])
            for manager in inventory_managers:
                SystemNotification.objects.create(
                    user=manager,
                    title='Production Completed - Inventory Updated',
                    message=f'{order.quantity} units of {order.product_name} added to inventory from order {order.order_id}',
                    notification_type='success'
                )
            
        elif order.progress_percentage > 0:
            order.status = 'in_progress'
        
        order.save()
        
        # Log the action
        AuditLog.objects.create(
            user=request.user,
            action='Update Production Status',
            module='Production',
            description=f'Updated order {order.order_id} to {order.progress_percentage}%' + 
                       (f' - Added {order.quantity} units to inventory' if order.status == 'completed' and old_status != 'completed' else ''),
        )
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Order status updated successfully' + 
                          (' and product added to inventory!' if order.status == 'completed' and old_status != 'completed' else '')
            })
        
        messages.success(request, 'Order status updated successfully!' + 
                        (' Product has been added to inventory.' if order.status == 'completed' and old_status != 'completed' else ''))
        return redirect('production:order_detail', order_id=order.id)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@login_required
def manage_bom(request, order_id):
    """Manage Bill of Materials"""
    order = get_object_or_404(ProductionOrder, id=order_id)
    
    if request.method == 'POST':
        material_id = request.POST.get('material_id')
        quantity = float(request.POST.get('quantity'))
        
        material = get_object_or_404(InventoryItem, id=material_id)
        
        BillOfMaterials.objects.create(
            production_order=order,
            material=material,
            quantity_required=quantity,
            unit=request.POST.get('unit', 'units'),
            notes=request.POST.get('notes', ''),
        )
        
        messages.success(request, 'Material added to BOM!')
        return redirect('production:order_detail', order_id=order.id)
    
    materials = InventoryItem.objects.all()
    bom_items = BillOfMaterials.objects.filter(production_order=order)
    
    context = {
        'order': order,
        'materials': materials,
        'bom_items': bom_items,
    }
    
    return render(request, 'production/manage_bom.html', context)


@login_required
def issue_materials(request, order_id):
    """Issue materials for production"""
    order = get_object_or_404(ProductionOrder, id=order_id)
    
    if request.method == 'POST':
        # Create material issue note
        issue_note = MaterialIssueNote.objects.create(
            issue_number=f'MIN-{order.order_id}-{timezone.now().strftime("%Y%m%d")}',
            production_order=order,
            issued_by=request.user,
            notes=request.POST.get('notes', ''),
        )
        
        # Issue materials from BOM
        bom_items = BillOfMaterials.objects.filter(production_order=order)
        
        for bom_item in bom_items:
            # Create issue item
            MaterialIssueItem.objects.create(
                issue_note=issue_note,
                material=bom_item.material,
                quantity_issued=bom_item.quantity_required,
            )
            
            # Update BOM
            bom_item.quantity_issued = bom_item.quantity_required
            bom_item.save()
            
            # Update inventory
            item = bom_item.material
            item.quantity -= bom_item.quantity_required
            item.save()
            
            # Record stock movement
            StockMovement.objects.create(
                item=item,
                movement_type='out',
                quantity=bom_item.quantity_required,
                reference_number=issue_note.issue_number,
                notes=f'Issued for production order {order.order_id}',
                performed_by=request.user,
            )
        
        AuditLog.objects.create(
            user=request.user,
            action='Issue Materials',
            module='Production',
            description=f'Issued materials for order {order.order_id}',
        )
        
        messages.success(request, 'Materials issued successfully!')
        return redirect('production:order_detail', order_id=order.id)
    
    bom_items = BillOfMaterials.objects.filter(production_order=order)
    
    context = {
        'order': order,
        'bom_items': bom_items,
    }
    
    return render(request, 'production/issue_materials.html', context)


@login_required
def quality_check(request, order_id):
    """Perform quality check"""
    order = get_object_or_404(ProductionOrder, id=order_id)
    
    if request.method == 'POST':
        QualityCheck.objects.create(
            production_order=order,
            inspector=request.user,
            result=request.POST.get('result'),
            defects_found=int(request.POST.get('defects_found', 0)),
            comments=request.POST.get('comments', ''),
        )
        
        AuditLog.objects.create(
            user=request.user,
            action='Quality Check',
            module='Production',
            description=f'Quality check performed for order {order.order_id}',
        )
        
        messages.success(request, 'Quality check recorded!')
        return redirect('production:order_detail', order_id=order.id)
    
    return render(request, 'production/quality_check.html', {'order': order})


@login_required
def reports(request):
    """Generate production reports"""
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        report_period = request.POST.get('report_period')
        
        report = ProductionReport.objects.create(
            report_type=report_type,
            report_period=report_period,
            generated_by=request.user,
        )
        
        messages.success(request, 'Report generated successfully!')
        return redirect('production:reports')
    
    reports = ProductionReport.objects.all()[:20]
    return render(request, 'production/reports.html', {'reports': reports})


# ==================== API ENDPOINTS ====================

@login_required
@role_required('production', 'admin')
def create_order_api(request):
    """Create production order via API"""
    if request.method == 'POST':
        try:
            order_id = request.POST.get('order_id', '').strip()
            customer_name = request.POST.get('customer_name', '').strip()
            product_name = request.POST.get('product_name', '').strip()
            quantity = int(request.POST.get('quantity', 0))
            due_date = request.POST.get('due_date')
            
            # Validate required fields
            if not all([order_id, customer_name, product_name, quantity, due_date]):
                return JsonResponse({
                    'success': False,
                    'message': 'All fields are required'
                })
            
            # Check if order ID already exists
            if ProductionOrder.objects.filter(order_id=order_id).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'Order ID {order_id} already exists'
                })
            
            # Create production order
            order = ProductionOrder.objects.create(
                order_id=order_id,
                customer_name=customer_name,
                product_name=product_name,
                quantity=quantity,
                due_date=due_date,
                status='pending',
                current_phase='cutting',
                progress_percentage=0,
                created_by=request.user
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Create Production Order',
                module='Production',
                description=f'Created order {order.order_id} for {customer_name}',
                ip_address=get_client_ip(request)
            )
            
            # Create notification for other production managers and admins (not the creator)
            from core.models import User
            production_users = User.objects.filter(
                role__in=['production', 'admin']
            ).exclude(id=request.user.id)  # Exclude the creator
            
            for user in production_users:
                SystemNotification.objects.create(
                    user=user,
                    title='Production Order Created',
                    message=f'Order {order.order_id} has been created by {request.user.get_full_name() or request.user.username}',
                    notification_type='success'
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Production order created successfully',
                'order': {
                    'id': order.id,
                    'order_id': order.order_id,
                    'customer_name': order.customer_name,
                    'product_name': order.product_name,
                    'quantity': order.quantity,
                    'due_date': str(order.due_date),
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
@role_required('production', 'admin')
def list_orders_api(request):
    """List all production orders via API"""
    try:
        # Get active orders (pending and in_progress)
        active_orders = ProductionOrder.objects.filter(
            status__in=['pending', 'in_progress']
        ).order_by('-created_at')
        
        # Get all orders
        all_orders = ProductionOrder.objects.all().order_by('-created_at')
        
        active_orders_data = []
        for order in active_orders:
            active_orders_data.append({
                'id': order.id,
                'order_id': order.order_id,
                'customer_name': order.customer_name,
                'product_name': order.product_name,
                'quantity': order.quantity,
                'due_date': order.due_date.strftime('%Y-%m-%d') if hasattr(order.due_date, 'strftime') else str(order.due_date),
                'status': order.status,
                'status_display': order.get_status_display(),
                'current_phase': order.current_phase,
                'current_phase_display': order.get_current_phase_display(),
                'progress_percentage': order.progress_percentage,
                'assigned_machine': order.assigned_machine or ''
            })
        
        all_orders_data = []
        for order in all_orders:
            all_orders_data.append({
                'id': order.id,
                'order_id': order.order_id,
                'customer_name': order.customer_name,
                'product_name': order.product_name,
                'quantity': order.quantity,
                'due_date': order.due_date.strftime('%Y-%m-%d') if hasattr(order.due_date, 'strftime') else str(order.due_date),
                'status': order.status,
                'status_display': order.get_status_display(),
                'current_phase': order.current_phase,
                'current_phase_display': order.get_current_phase_display(),
                'progress_percentage': order.progress_percentage,
                'assigned_machine': order.assigned_machine or ''
            })
        
        return JsonResponse({
            'success': True,
            'active_orders': active_orders_data,
            'all_orders': all_orders_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@role_required('production', 'admin')
def update_order_api(request, order_id):
    """Update production order status via API"""
    if request.method == 'POST':
        try:
            order = get_object_or_404(ProductionOrder, id=order_id)
            
            # Get update data
            progress = int(request.POST.get('progress', order.progress_percentage))
            phase = request.POST.get('phase', order.current_phase)
            machine = request.POST.get('machine', order.assigned_machine)
            
            old_status = order.status
            
            # Update order
            order.progress_percentage = progress
            order.current_phase = phase
            order.assigned_machine = machine
            
            # Update status based on progress
            if progress == 100:
                order.status = 'completed'
                order.completed_at = timezone.now()
                
                # Automatically add completed product to inventory
                from inventory.models import InventoryItem, StockMovement
                
                # Generate SKU for the product
                product_name_short = ''.join([word[0].upper() for word in order.product_name.split()[:3]])
                sku_base = f"{product_name_short}-{order.order_id.split('-')[-1]}"
                
                # Check if item already exists in inventory
                inventory_item, created = InventoryItem.objects.get_or_create(
                    name=order.product_name,
                    defaults={
                        'sku': sku_base,
                        'category': 'equipment',
                        'description': f'Produced from order {order.order_id} for {order.customer_name}',
                        'quantity': order.quantity,
                        'reorder_level': 50,
                        'unit_price': 0,
                        'location': 'Warehouse A',
                    }
                )
                
                if not created:
                    # Item exists, update quantity
                    inventory_item.quantity += order.quantity
                    inventory_item.save()
                
                # Create stock movement record
                StockMovement.objects.create(
                    item=inventory_item,
                    movement_type='in',
                    quantity=order.quantity,
                    reference_number=order.order_id,
                    notes=f'Completed production order {order.order_id}',
                    performed_by=request.user
                )
                
                # Create notification for inventory managers
                from core.models import User, SystemNotification
                inventory_managers = User.objects.filter(role__in=['inventory', 'admin'])
                for manager in inventory_managers:
                    SystemNotification.objects.create(
                        user=manager,
                        title='Production Completed - Inventory Updated',
                        message=f'{order.quantity} units of {order.product_name} added to inventory from order {order.order_id}',
                        notification_type='success'
                    )
                
                # Notify finance managers to create invoice for completed order
                finance_managers = User.objects.filter(role__in=['finance', 'admin'])
                for manager in finance_managers:
                    SystemNotification.objects.create(
                        user=manager,
                        title='Production Completed - Invoice Required',
                        message=f'Order {order.order_id} completed: {order.quantity} units of {order.product_name} for {order.customer_name}. Please generate customer invoice.',
                        notification_type='info'
                    )
                
            elif progress > 0:
                order.status = 'in_progress'
            
            order.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Update Production Status',
                module='Production',
                description=f'Updated order {order.order_id} to {progress}% - Phase: {phase}' +
                           (f' - Added {order.quantity} units to inventory' if order.status == 'completed' and old_status != 'completed' else ''),
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Production order updated successfully' +
                          (' and product added to inventory!' if order.status == 'completed' and old_status != 'completed' else ''),
                'order': {
                    'id': order.id,
                    'order_id': order.order_id,
                    'progress_percentage': order.progress_percentage,
                    'current_phase': order.get_current_phase_display(),
                    'assigned_machine': order.assigned_machine,
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
@role_required('production', 'admin')
def get_notifications_api(request):
    """Get notifications for current user via API"""
    try:
        # Get unread notifications
        notifications = SystemNotification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:10]
        
        notifications_data = []
        for notif in notifications:
            # Calculate time ago
            from django.utils.timesince import timesince
            time_ago = timesince(notif.created_at) + ' ago'
            
            # Map notification type to icon
            icon_map = {
                'info': 'bi-info-circle-fill',
                'warning': 'bi-exclamation-triangle-fill',
                'danger': 'bi-exclamation-triangle-fill',
                'success': 'bi-check-circle-fill'
            }
            
            notifications_data.append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'type': notif.notification_type,
                'icon': icon_map.get(notif.notification_type, 'bi-info-circle-fill'),
                'time_ago': time_ago,
                'is_read': notif.is_read
            })
        
        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'count': len(notifications_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

