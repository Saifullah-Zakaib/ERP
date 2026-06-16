from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import models
from datetime import datetime
from .models import Supplier, PurchaseOrder, PurchaseOrderItem, SupplierPerformance, MaterialRequest
from core.models import AuditLog,User, SystemNotification
from core.views import role_required, get_client_ip

@login_required
@role_required('supplier', 'admin')
def dashboard(request):
    """Suppliers dashboard"""
    from django.db.models import Sum, Count, Q
    from datetime import datetime, timedelta
    
    # Calculate monthly spend (current month)
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_spend = PurchaseOrder.objects.filter(
        order_date__month=current_month,
        order_date__year=current_year
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    monthly_spend_k = monthly_spend / 1000  # Convert to thousands
    
    # Calculate on-time delivery rate
    delivered_orders = PurchaseOrder.objects.filter(
        status='received',
        actual_delivery__isnull=False
    )
    total_delivered = delivered_orders.count()
    if total_delivered > 0:
        on_time = delivered_orders.filter(
            actual_delivery__lte=models.F('expected_delivery')
        ).count()
        on_time_delivery_rate = int((on_time / total_delivered) * 100)
    else:
        on_time_delivery_rate = 0
    
    context = {
        'total_suppliers': Supplier.objects.filter(status='active').count(),
        'pending_orders': PurchaseOrder.objects.filter(status='pending').count(),
        'approved_orders': PurchaseOrder.objects.filter(status='approved').count(),
        'delivered_orders': PurchaseOrder.objects.filter(status='received').count(),
        'monthly_spend': monthly_spend_k,
        'on_time_delivery_rate': on_time_delivery_rate,
        'suppliers': Supplier.objects.filter(status='active').order_by('-created_at')[:20],
        'purchase_orders': PurchaseOrder.objects.select_related('supplier').all().order_by('-created_at')[:20],
        'recent_material_requests': MaterialRequest.objects.select_related('requested_by').all()[:10],
        'supplier_performance': SupplierPerformance.objects.select_related('supplier').all()[:10],
    }
    
    return render(request, 'suppliers/dashboard.html', context)


@login_required
@role_required('supplier', 'admin')
def add_supplier_api(request):
    """Add new supplier via API"""
    if request.method == 'POST':
        try:
            # Generate supplier ID
            last_supplier = Supplier.objects.all().order_by('-id').first()
            if last_supplier and last_supplier.supplier_id:
                last_num = int(last_supplier.supplier_id.split('-')[1])
                new_num = last_num + 1
            else:
                new_num = 1
            supplier_id = f"SUP-{new_num:04d}"
            
            # Get form data
            name = request.POST.get('name')
            category = request.POST.get('category')
            contact_person = request.POST.get('contact_person')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            
            # Validate required fields
            if not all([name, category, contact_person, email, phone]):
                return JsonResponse({
                    'success': False,
                    'message': 'All fields are required'
                })
            
            # Check if email already exists
            if Supplier.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Email already exists'
                })
            
            # Create supplier
            supplier = Supplier.objects.create(
                supplier_id=supplier_id,
                name=name,
                category=category,
                contact_person=contact_person,
                email=email,
                phone=phone,
                address=request.POST.get('address', ''),
                city=request.POST.get('city', ''),
                country=request.POST.get('country', ''),
                tax_id=request.POST.get('tax_id', ''),
                payment_terms=request.POST.get('payment_terms', 'Net 30'),
                status='active'
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Add Supplier',
                module='Suppliers',
                description=f'Added supplier {supplier.name} ({supplier.supplier_id})',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Supplier added successfully',
                'supplier': {
                    'id': supplier.id,
                    'supplier_id': supplier.supplier_id,
                    'name': supplier.name,
                    'contact_person': supplier.contact_person,
                    'email': supplier.email,
                    'phone': supplier.phone,
                    'category': supplier.get_category_display(),
                    'status': supplier.get_status_display()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('supplier', 'admin')
def update_supplier_rating_api(request, supplier_id):
    """Update supplier rating via API"""
    if request.method == 'POST':
        try:
            supplier = Supplier.objects.get(id=supplier_id)
            rating = request.POST.get('rating')
            
            if rating is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Rating is required'
                })
            
            # Convert to decimal and validate
            rating = float(rating)
            if rating < 0 or rating > 5:
                return JsonResponse({
                    'success': False,
                    'message': 'Rating must be between 0 and 5'
                })
            
            supplier.rating = rating
            supplier.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Supplier rating updated successfully',
                'rating': float(supplier.rating)
            })
            
        except Supplier.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Supplier not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('supplier', 'admin')
def create_purchase_order_api(request):
    """Create new purchase order via API"""
    if request.method == 'POST':
        try:
            # Generate PO number
            last_po = PurchaseOrder.objects.all().order_by('-id').first()
            if last_po and last_po.po_number:
                last_num = int(last_po.po_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            po_number = f"PUR-{timezone.now().year}-{new_num:04d}"
            
            # Get form data
            supplier_id = request.POST.get('supplier_id')
            order_date = request.POST.get('order_date')
            expected_delivery = request.POST.get('expected_delivery')
            
            # Validate required fields
            if not all([supplier_id, order_date, expected_delivery]):
                return JsonResponse({
                    'success': False,
                    'message': 'Supplier, order date, and expected delivery are required'
                })
            
            # Get supplier
            try:
                supplier = Supplier.objects.get(id=supplier_id)
            except Supplier.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Supplier not found'
                })
            
            # Parse dates
            try:
                order_date_obj = datetime.strptime(order_date, '%Y-%m-%d').date()
                expected_delivery_obj = datetime.strptime(expected_delivery, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid date format'
                })
            
            # Get items data
            import json
            items_json = request.POST.get('items', '[]')
            items = json.loads(items_json)
            
            if not items:
                return JsonResponse({
                    'success': False,
                    'message': 'At least one item is required'
                })
            
            # Calculate totals
            subtotal = 0
            for item in items:
                qty = float(item.get('quantity', 0))
                price = float(item.get('unit_price', 0))
                subtotal += qty * price
            
            tax_amount = subtotal * 0.0  # No tax for now
            shipping_cost = 0
            total_amount = subtotal + tax_amount + shipping_cost
            
            # Create purchase order
            po = PurchaseOrder.objects.create(
                po_number=po_number,
                supplier=supplier,
                order_date=order_date_obj,
                expected_delivery=expected_delivery_obj,
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_cost=shipping_cost,
                total_amount=total_amount,
                status='pending',
                notes=request.POST.get('notes', ''),
                created_by=request.user
            )
            
            # Create PO items
            for item in items:
                item_name = item.get('item_name', '')
                quantity = int(item.get('quantity', 0))
                unit_price = float(item.get('unit_price', 0))
                
                if item_name and quantity > 0:
                    PurchaseOrderItem.objects.create(
                        purchase_order=po,
                        item_name=item_name,
                        description=item.get('description', ''),
                        quantity=quantity,
                        unit_price=unit_price,
                        total=quantity * unit_price
                    )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Create Purchase Order',
                module='Suppliers',
                description=f'Created PO {po.po_number} for {supplier.name}',
                ip_address=get_client_ip(request)
            )
            
            # Send notification to finance managers to generate invoice
            from core.models import SystemNotification
            finance_managers = User.objects.filter(role__in=['finance', 'admin'])
            for manager in finance_managers:
                SystemNotification.objects.create(
                    user=manager,
                    title='New Purchase Order - Invoice Required',
                    message=f'Purchase Order {po.po_number} created for {supplier.name}. Total amount: ${po.total_amount}. Please generate invoice.',
                    notification_type='info'
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Purchase order created successfully',
                'po': {
                    'id': po.id,
                    'po_number': po.po_number,
                    'supplier_name': supplier.name,
                    'order_date': po.order_date.strftime('%Y-%m-%d'),
                    'expected_delivery': po.expected_delivery.strftime('%Y-%m-%d'),
                    'total_amount': float(po.total_amount),
                    'status': po.get_status_display()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('supplier', 'admin')
def update_purchase_order_status(request, po_id):
    """Update purchase order status via API"""
    if request.method == 'POST':
        try:
            # Get the purchase order
            po = get_object_or_404(PurchaseOrder, id=po_id)
            
            # Get new status from request
            new_status = request.POST.get('status')
            
            # Validate status
            valid_statuses = ['draft', 'pending', 'approved', 'sent', 'received', 'cancelled']
            if new_status not in valid_statuses:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid status'
                })
            
            # Update status
            old_status = po.status
            po.status = new_status
            
            # If status is received, set actual delivery date
            if new_status == 'received' and not po.actual_delivery:
                po.actual_delivery = timezone.now().date()
            
            po.save()
            
            # Create notifications based on status change
            from core.models import User, SystemNotification
            
            if new_status == 'sent':
                # Notify inventory managers when order is in transit
                inventory_managers = User.objects.filter(role__in=['inventory', 'admin'])
                supplier_name = po.get_supplier_name()
                for manager in inventory_managers:
                    SystemNotification.objects.create(
                        user=manager,
                        title='Purchase Order In Transit',
                        message=f'PO {po.po_number} from {supplier_name} is now in transit. Expected delivery: {po.expected_delivery.strftime("%b %d, %Y")}',
                        notification_type='info'
                    )
            
            elif new_status == 'received':
                # AUTOMATICALLY UPDATE INVENTORY when materials are received
                from inventory.models import InventoryItem, StockMovement
                
                # Get all items from this purchase order
                po_items = po.items.all()
                supplier_name = po.get_supplier_name()
                
                for po_item in po_items:
                    # Try to find matching inventory item
                    inventory_item = InventoryItem.objects.filter(
                        models.Q(name__iexact=po_item.item_name) | 
                        models.Q(sku__icontains=po_item.item_name)
                    ).first()
                    
                    if inventory_item:
                        # Update existing inventory item
                        old_quantity = inventory_item.quantity
                        inventory_item.quantity += po_item.quantity
                        inventory_item.save()
                        
                        # Record stock movement
                        StockMovement.objects.create(
                            item=inventory_item,
                            movement_type='in',
                            quantity=po_item.quantity,
                            reference_number=po.po_number,
                            notes=f'Received from supplier: {supplier_name}',
                            performed_by=request.user
                        )
                        
                        # Log inventory update
                        AuditLog.objects.create(
                            user=request.user,
                            action='Auto-Update Inventory',
                            module='Inventory',
                            description=f'Auto-updated {inventory_item.sku} from {old_quantity} to {inventory_item.quantity} units (PO: {po.po_number})',
                            ip_address=get_client_ip(request)
                        )
                    else:
                        # Create new inventory item if not exists
                        # Generate SKU
                        last_item = InventoryItem.objects.all().order_by('-id').first()
                        if last_item and last_item.sku:
                            last_num = int(last_item.sku.split('-')[1])
                            new_num = last_num + 1
                        else:
                            new_num = 1
                        new_sku = f"SKU-{new_num:04d}"
                        
                        new_item = InventoryItem.objects.create(
                            sku=new_sku,
                            name=po_item.item_name,
                            category='raw_materials',
                            quantity=po_item.quantity,
                            reorder_level=50,
                            unit_price=po_item.unit_price,
                            location='Warehouse A',
                            description=f'Auto-created from PO {po.po_number}'
                        )
                        
                        # Record stock movement
                        StockMovement.objects.create(
                            item=new_item,
                            movement_type='in',
                            quantity=po_item.quantity,
                            reference_number=po.po_number,
                            notes=f'Initial stock from supplier: {supplier_name}',
                            performed_by=request.user
                        )
                        
                        # Log new item creation
                        AuditLog.objects.create(
                            user=request.user,
                            action='Auto-Create Inventory',
                            module='Inventory',
                            description=f'Auto-created {new_item.sku} - {new_item.name} with {new_item.quantity} units (PO: {po.po_number})',
                            ip_address=get_client_ip(request)
                        )
                
                # Notify inventory managers about the inventory update
                inventory_managers = User.objects.filter(role__in=['inventory', 'admin'])
                for manager in inventory_managers:
                    SystemNotification.objects.create(
                        user=manager,
                        title='Inventory Auto-Updated',
                        message=f'PO {po.po_number} received from {supplier_name}. Inventory has been automatically updated with new materials.',
                        notification_type='success'
                    )
                
                # Notify supplier managers about delivery
                supplier_managers = User.objects.filter(role__in=['supplier', 'admin'])
                for manager in supplier_managers:
                    SystemNotification.objects.create(
                        user=manager,
                        title='Purchase Order Delivered',
                        message=f'PO {po.po_number} from {supplier_name} has been delivered successfully.',
                        notification_type='success'
                    )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Update PO Status',
                module='Suppliers',
                description=f'Updated PO {po.po_number} status from {old_status} to {new_status}',
                ip_address=get_client_ip(request)
            )
            
            # Create user-friendly message
            status_messages = {
                'sent': f'Order {po.po_number} moved to In Transit',
                'received': f'Order {po.po_number} marked as Delivered',
                'pending': f'Order {po.po_number} status updated to Pending',
                'approved': f'Order {po.po_number} has been approved',
                'cancelled': f'Order {po.po_number} has been cancelled and removed'
            }
            
            # If cancelled, delete the purchase order from database
            if new_status == 'cancelled':
                po_number = po.po_number
                supplier_name = po.get_supplier_name()
                
                # Log before deletion
                AuditLog.objects.create(
                    user=request.user,
                    action='Cancel & Delete PO',
                    module='Suppliers',
                    description=f'Cancelled and deleted PO {po_number} from {supplier_name}',
                    ip_address=get_client_ip(request)
                )
                
                # Delete the purchase order (cascade will delete items too)
                po.delete()
                
                return JsonResponse({
                    'success': True,
                    'message': status_messages.get(new_status),
                    'deleted': True,
                    'po_id': po_id
                })
            
            return JsonResponse({
                'success': True,
                'message': status_messages.get(new_status, 'Purchase order status updated successfully'),
                'po': {
                    'id': po.id,
                    'po_number': po.po_number,
                    'status': po.status,
                    'status_display': po.get_status_display()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('supplier', 'admin')
def supplier_performance_report(request):
    """Generate supplier performance report"""
    from django.db.models import Count, Avg, Q, F, Sum
    from datetime import timedelta
    
    # Get date range from request or default to last 3 months
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=90)
    
    # Get all active suppliers with their performance metrics
    suppliers_data = []
    
    for supplier in Supplier.objects.filter(status='active'):
        # Get ALL POs for this supplier (not filtered by date for now to show all data)
        pos = PurchaseOrder.objects.filter(supplier=supplier)
        
        total_orders = pos.count()
        
        # Calculate metrics even if no orders (will show 0s)
        completed_orders = pos.filter(status='received').count()
        pending_orders = pos.filter(status__in=['pending', 'approved', 'sent', 'draft']).count()
        
        # Calculate on-time delivery
        delivered = pos.filter(status='received', actual_delivery__isnull=False)
        if delivered.count() > 0:
            on_time = delivered.filter(actual_delivery__lte=F('expected_delivery')).count()
            on_time_rate = (on_time / delivered.count() * 100)
        else:
            on_time_rate = 0
        
        # Calculate total spend using Sum aggregation
        total_spend = pos.aggregate(total=Sum('total_amount'))['total']
        if total_spend is None:
            total_spend = 0
        else:
            total_spend = float(total_spend)
        
        # Get average rating from performance records
        avg_rating = SupplierPerformance.objects.filter(
            supplier=supplier
        ).aggregate(avg=Avg('overall_rating'))['avg']
        
        if avg_rating is None:
            avg_rating = 0
        else:
            avg_rating = round(float(avg_rating), 2)
        
        # Include all suppliers in the report, even those with no orders
        suppliers_data.append({
            'supplier': supplier,
            'total_orders': total_orders,
            'on_time_rate': round(on_time_rate, 1),
            'total_spend': total_spend,
            'avg_rating': avg_rating,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
        })
    
    # Sort by on-time rate (highest first), then by total spend
    suppliers_data.sort(key=lambda x: (x['on_time_rate'], x['total_spend']), reverse=True)
    
    # Calculate summary statistics
    total_suppliers_evaluated = len([s for s in suppliers_data if s['total_orders'] > 0])
    
    if total_suppliers_evaluated > 0:
        avg_on_time_rate = sum(s['on_time_rate'] for s in suppliers_data if s['total_orders'] > 0) / total_suppliers_evaluated
        total_spend_all = sum(s['total_spend'] for s in suppliers_data)
    else:
        avg_on_time_rate = 0
        total_spend_all = 0
    
    context = {
        'suppliers_data': suppliers_data,
        'start_date': start_date,
        'end_date': end_date,
        'total_suppliers': Supplier.objects.filter(status='active').count(),
        'total_suppliers_evaluated': total_suppliers_evaluated,
        'avg_on_time_rate': round(avg_on_time_rate, 1),
        'total_spend_all': total_spend_all,
    }
    
    return render(request, 'suppliers/performance_report.html', context)


@login_required
@role_required('supplier', 'admin')
def purchase_report(request):
    """Generate purchase report"""
    from django.db.models import Sum, Count, Avg
    from datetime import timedelta
    
    # Get date range from request or default to current month
    end_date = timezone.now().date()
    start_date = end_date.replace(day=1)  # First day of current month
    
    # Get all POs in date range
    pos = PurchaseOrder.objects.filter(
        order_date__gte=start_date,
        order_date__lte=end_date
    ).select_related('supplier', 'created_by')
    
    # Calculate summary metrics
    total_orders = pos.count()
    total_value = pos.aggregate(total=Sum('total_amount'))['total'] or 0
    avg_order_value = pos.aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    # Status breakdown (excluding approved and sent)
    status_breakdown = {
        'pending': pos.filter(status='pending').count(),
        'received': pos.filter(status='received').count(),
        'cancelled': pos.filter(status='cancelled').count(),
    }
    
    # Top suppliers by spend
    top_suppliers = pos.values('supplier__name').annotate(
        total_spend=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('-total_spend')[:5]
    
    # Monthly trend (last 6 months)
    monthly_data = []
    for i in range(6):
        month_date = end_date - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if month_date.month == 12:
            month_end = month_date.replace(day=31)
        else:
            month_end = (month_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_pos = PurchaseOrder.objects.filter(
            order_date__gte=month_start,
            order_date__lte=month_end
        )
        
        monthly_data.append({
            'month': month_date.strftime('%B %Y'),
            'orders': month_pos.count(),
            'value': month_pos.aggregate(total=Sum('total_amount'))['total'] or 0
        })
    
    monthly_data.reverse()
    
    context = {
        'purchase_orders': pos[:50],  # Latest 50 orders
        'start_date': start_date,
        'end_date': end_date,
        'total_orders': total_orders,
        'total_value': total_value,
        'avg_order_value': avg_order_value,
        'status_breakdown': status_breakdown,
        'top_suppliers': top_suppliers,
        'monthly_data': monthly_data,
    }
    
    return render(request, 'suppliers/purchase_report.html', context)


@login_required
@role_required('supplier', 'admin')
def order_tracking(request):
    """Track order status and supplier deliveries"""
    from django.db.models import Q
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    supplier_filter = request.GET.get('supplier', '')
    
    # Base queryset
    orders = PurchaseOrder.objects.select_related('supplier', 'created_by').all()
    
    # Apply filters
    if status_filter:
        orders = orders.filter(status=status_filter)
    if supplier_filter:
        orders = orders.filter(supplier_id=supplier_filter)
    
    # Separate orders by status
    pending_orders = orders.filter(status='pending').order_by('-order_date')
    in_transit_orders = orders.filter(status__in=['approved', 'sent']).order_by('expected_delivery')
    delivered_orders = orders.filter(status='received').order_by('-actual_delivery')[:20]
    overdue_orders = orders.filter(
        status__in=['pending', 'approved', 'sent'],
        expected_delivery__lt=timezone.now().date()
    ).order_by('expected_delivery')
    
    # Calculate delivery metrics
    total_delivered = PurchaseOrder.objects.filter(status='received', actual_delivery__isnull=False).count()
    if total_delivered > 0:
        on_time_delivered = PurchaseOrder.objects.filter(
            status='received',
            actual_delivery__lte=models.F('expected_delivery')
        ).count()
        on_time_rate = (on_time_delivered / total_delivered) * 100
    else:
        on_time_rate = 0
    
    context = {
        'pending_orders': pending_orders,
        'in_transit_orders': in_transit_orders,
        'delivered_orders': delivered_orders,
        'overdue_orders': overdue_orders,
        'on_time_rate': round(on_time_rate, 1),
        'total_pending': pending_orders.count(),
        'total_in_transit': in_transit_orders.count(),
        'total_overdue': overdue_orders.count(),
        'suppliers': Supplier.objects.filter(status='active'),
        'status_choices': PurchaseOrder.STATUS_CHOICES,
        'current_status': status_filter,
        'current_supplier': supplier_filter,
    }
    
    return render(request, 'suppliers/order_tracking.html', context)


@login_required
def supplier_list(request):
    """List all suppliers"""
    suppliers = Supplier.objects.all()
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        suppliers = suppliers.filter(category=category)
    
    context = {
        'suppliers': suppliers,
        'categories': Supplier.CATEGORY_CHOICES,
    }
    
    return render(request, 'suppliers/supplier_list.html', context)


@login_required
def add_supplier(request):
    """Add new supplier"""
    if request.method == 'POST':
        supplier = Supplier.objects.create(
            supplier_id=request.POST.get('supplier_id'),
            name=request.POST.get('name'),
            category=request.POST.get('category'),
            contact_person=request.POST.get('contact_person'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address', ''),
            city=request.POST.get('city', ''),
            country=request.POST.get('country', ''),
            payment_terms=request.POST.get('payment_terms', 'Net 30'),
        )
        
        AuditLog.objects.create(
            user=request.user,
            action='Add Supplier',
            module='Suppliers',
            description=f'Added supplier {supplier.name}',
        )
        
        messages.success(request, 'Supplier added successfully!')
        return redirect('suppliers:supplier_detail', supplier_id=supplier.id)
    
    return render(request, 'suppliers/add_supplier.html', {
        'categories': Supplier.CATEGORY_CHOICES
    })


@login_required
def supplier_detail(request, supplier_id):
    """View supplier details"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    purchase_orders = PurchaseOrder.objects.filter(supplier=supplier)
    
    context = {
        'supplier': supplier,
        'purchase_orders': purchase_orders,
    }
    
    return render(request, 'suppliers/supplier_detail.html', context)


@login_required
def purchase_order_list(request):
    """List all purchase orders"""
    pos = PurchaseOrder.objects.all()
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        pos = pos.filter(status=status)
    
    context = {
        'purchase_orders': pos,
        'status_choices': PurchaseOrder.STATUS_CHOICES,
    }
    
    return render(request, 'suppliers/purchase_order_list.html', context)


@login_required
def create_purchase_order(request):
    """Create new purchase order"""
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier_id')
        supplier = get_object_or_404(Supplier, id=supplier_id)
        
        po = PurchaseOrder.objects.create(
            po_number=request.POST.get('po_number'),
            supplier=supplier,
            order_date=request.POST.get('order_date'),
            expected_delivery=request.POST.get('expected_delivery'),
            total_amount=float(request.POST.get('total_amount', 0)),
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        
        # Add PO items
        item_count = int(request.POST.get('item_count', 0))
        subtotal = 0
        
        for i in range(item_count):
            item_name = request.POST.get(f'item_name_{i}')
            quantity = int(request.POST.get(f'item_quantity_{i}', 0))
            unit_price = float(request.POST.get(f'item_price_{i}', 0))
            
            if item_name and quantity and unit_price:
                PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    item_name=item_name,
                    quantity=quantity,
                    unit_price=unit_price,
                )
                subtotal += quantity * unit_price
        
        po.subtotal = subtotal
        po.total_amount = subtotal
        po.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='Create Purchase Order',
            module='Suppliers',
            description=f'Created PO {po.po_number}',
        )
        
        messages.success(request, 'Purchase order created successfully!')
        return redirect('suppliers:po_detail', po_id=po.id)
    
    suppliers = Supplier.objects.filter(status='active')
    return render(request, 'suppliers/create_purchase_order.html', {'suppliers': suppliers})


@login_required
def po_detail(request, po_id):
    """View purchase order details"""
    po = get_object_or_404(PurchaseOrder, id=po_id)
    items = PurchaseOrderItem.objects.filter(purchase_order=po)
    
    context = {
        'po': po,
        'items': items,
    }
    
    return render(request, 'suppliers/po_detail.html', context)


@login_required
def material_requests(request):
    """View material requests"""
    requests = MaterialRequest.objects.all()
    
    context = {
        'material_requests': requests,
    }
    
    return render(request, 'suppliers/material_requests.html', context)


@login_required
@role_required('supplier', 'admin')
def notifications_api(request):
    """Get notifications for supplier users"""
    from core.models import SystemNotification
    
    notifications = SystemNotification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:10]
    
    notifications_data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.notification_type,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'time_ago': get_time_ago(n.created_at)
    } for n in notifications]
    
    return JsonResponse({
        'success': True,
        'notifications': notifications_data,
        'count': len(notifications_data)
    })


def get_time_ago(dt):
    """Calculate time ago from datetime"""
    from django.utils import timezone
    now = timezone.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


@login_required
@role_required('supplier', 'admin')
def get_purchase_orders_status(request):
    """Get current status of all purchase orders for real-time updates"""
    try:
        # Get recent purchase orders (last 20)
        orders = PurchaseOrder.objects.select_related('supplier').order_by('-created_at')[:20]
        
        orders_data = [{
            'id': po.id,
            'po_number': po.po_number,
            'status': po.status,
            'status_display': po.get_status_display(),
            'updated_at': po.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        } for po in orders]
        
        return JsonResponse({
            'success': True,
            'orders': orders_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
    else:
        return "Just now"


@login_required
@role_required('supplier', 'admin')
def delete_supplier_api(request, supplier_id):
    """Delete supplier via API"""
    if request.method == 'POST':
        try:
            supplier = get_object_or_404(Supplier, id=supplier_id)
            supplier_name = supplier.name
            supplier_code = supplier.supplier_id
            
            # Check if supplier has any purchase orders that are NOT received
            pending_pos = PurchaseOrder.objects.filter(
                supplier=supplier
            ).exclude(status='received')
            
            pending_count = pending_pos.count()
            
            if pending_count > 0:
                # Get status breakdown
                status_list = []
                for po in pending_pos[:5]:  # Show first 5
                    status_list.append(f"{po.po_number} ({po.get_status_display()})")
                
                status_text = ", ".join(status_list)
                if pending_count > 5:
                    status_text += f" and {pending_count - 5} more"
                
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot delete supplier "{supplier_name}".\n\n{pending_count} purchase order(s) are not yet received:\n{status_text}\n\nPlease wait until all orders are marked as "Received" before deleting this supplier.'
                })
            
            # All orders are received or no orders exist, safe to delete
            # The supplier field in PurchaseOrder will be set to NULL (historical data preserved)
            supplier.delete()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Delete Supplier',
                module='Suppliers',
                description=f'Deleted supplier {supplier_code} - {supplier_name}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Supplier "{supplier_name}" deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
