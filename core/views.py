from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from functools import wraps
from .models import User, AuditLog, SystemNotification
from inventory.models import InventoryItem, StockAlert
from production.models import ProductionOrder
from suppliers.models import PurchaseOrder
from hr.models import Employee, Attendance
from finance.models import Invoice, Expense

def role_required(*roles):
    """Decorator to check if user has required role"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('core:login')
            # Allow access if user's role is in the allowed roles OR user is admin
            if request.user.role not in roles and request.user.role != 'admin':
                messages.error(request, 'You do not have permission to access this page')
                return redirect('core:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def home_view(request):
    """Home page view"""
    from .models import Notice
    
    # Get all notices, pinned first
    notices = Notice.objects.all()[:10]
    
    context = {
        'notices': notices
    }
    
    return render(request, 'core/home.html', context)

def login_view(request):
    """User login"""
    # ✅ AGAR USER PEHLE SE LOGGED IN HAI TO DASHBOARD PAR BHEJO
    # LEKIN AGAR RESET_SUCCESS URL PARAM HAI TO LOGIN PAGE DIKHAO
    if request.user.is_authenticated and not request.GET.get('reset_success'):
        # Role-based redirect
        role_redirects = {
            'admin': 'core:admin_dashboard',
            'inventory': 'inventory:dashboard',
            'production': 'production:dashboard',
            'hr': 'hr:dashboard',
            'finance': 'finance:dashboard',
            'supplier': 'suppliers:dashboard',
        }
        redirect_url = role_redirects.get(request.user.role, 'core:dashboard')
        return redirect(redirect_url)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Log the login
            AuditLog.objects.create(
                user=user,
                action='Login',
                module='Core',
                description=f'User {user.username} logged in',
                ip_address=get_client_ip(request)
            )
            
            # Redirect based on role
            role_redirects = {
                'admin': 'core:admin_dashboard',
                'inventory': 'inventory:dashboard',
                'production': 'production:dashboard',
                'hr': 'hr:dashboard',
                'finance': 'finance:dashboard',
                'supplier': 'suppliers:dashboard',
            }
            
            redirect_url = role_redirects.get(user.role, 'core:dashboard')
            return redirect(redirect_url)
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'core/login.html')

def logout_view(request):
    """User logout"""
    if request.user.is_authenticated:
        AuditLog.objects.create(
            user=request.user,
            action='Logout',
            module='Core',
            description=f'User {request.user.username} logged out',
            ip_address=get_client_ip(request)
        )
    
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('core:home')


@login_required
def dashboard(request):
    """Main dashboard - shows overview for all roles"""
    user = request.user
    
    # Get statistics based on role
    context = {
        'user': user,
        'notifications': SystemNotification.objects.filter(user=user, is_read=False)[:5],
        'unread_notification_count': SystemNotification.objects.filter(user=user, is_read=False).count(),
    }
    
    # Common statistics
    context['pending_production_orders'] = ProductionOrder.objects.filter(status='pending').count()
    # Count items that are low stock or out of stock
    context['inventory_alerts'] = InventoryItem.objects.filter(
        status__in=['low_stock', 'out_of_stock']
    ).count()
    context['open_purchase_orders'] = PurchaseOrder.objects.filter(status__in=['pending', 'approved']).count()
    
    # Calculate cash balance from finance
    total_revenue = Invoice.objects.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    context['cash_balance'] = total_revenue - total_expenses
    
    # Get recent activity
    context['recent_activities'] = AuditLog.objects.select_related('user').all()[:10]
    
    # Production progress data - show orders with highest progress first
    context['production_orders'] = ProductionOrder.objects.exclude(
        status='cancelled'
    ).order_by('-progress_percentage', '-created_at')[:3]
    
    # Inventory levels for chart - get actual data
    inventory_items = InventoryItem.objects.all()[:5]
    context['inventory_chart_data'] = {
        'labels': [item.sku for item in inventory_items],
        'current_stock': [int(item.quantity) for item in inventory_items],
        'reorder_level': [int(item.reorder_level) for item in inventory_items]
    }
    
    # Supplier performance data - calculate on-time delivery percentage
    from suppliers.models import Supplier
    suppliers = Supplier.objects.all()[:3]
    supplier_data = []
    for supplier in suppliers:
        # Get completed purchase orders for this supplier
        completed_orders = PurchaseOrder.objects.filter(
            supplier=supplier,
            status='received',
            actual_delivery__isnull=False
        )
        total_orders = completed_orders.count()
        
        if total_orders > 0:
            # Calculate on-time deliveries (orders received before or on expected date)
            from django.db.models import F
            on_time = completed_orders.filter(
                actual_delivery__lte=F('expected_delivery')
            ).count()
            percentage = int((on_time / total_orders) * 100)
        else:
            percentage = 0
        
        supplier_data.append({
            'name': supplier.name,
            'percentage': percentage
        })
    
    context['supplier_chart_data'] = {
        'labels': [s['name'] for s in supplier_data],
        'percentages': [s['percentage'] for s in supplier_data]
    }
    
    # Role-specific data
    if user.role == 'admin':
        context['total_employees'] = Employee.objects.filter(is_active=True).count()
        context['total_users'] = User.objects.filter(is_active=True).count()
    
    if user.role in ['inventory', 'admin']:
        context['low_stock_items'] = InventoryItem.objects.filter(status='low_stock').count()
        context['out_of_stock_items'] = InventoryItem.objects.filter(status='out_of_stock').count()
    
    if user.role in ['finance', 'admin']:
        context['pending_invoices'] = Invoice.objects.filter(status='sent').count()
        context['monthly_revenue'] = Invoice.objects.filter(
            status='paid',
            invoice_date__month=timezone.now().month
        ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Generate AI demand forecast for dashboard
    from .ai_utils import AIInsightsEngine
    ai_engine = AIInsightsEngine()
    forecast_data = ai_engine.generate_demand_forecast()
    
    # Extract only the forecast portion (last 6 months) for dashboard
    forecast_labels = []
    forecast_values = []
    for i, label in enumerate(forecast_data['labels']):
        if forecast_data['forecast'][i] is not None:
            forecast_labels.append(label)
            forecast_values.append(forecast_data['forecast'][i])
    
    context['forecast_labels'] = forecast_labels
    context['forecast_demand'] = forecast_values
    context['forecast_recommendation'] = forecast_data['recommendation']
    
    # Current time for system health
    context['current_time'] = timezone.now()
    
    return render(request, 'core/dashboard.html', context)

@login_required
@role_required('admin')
def admin_dashboard(request):
    """Admin-specific dashboard with password reset requests"""
    # Get notifications for admin
    notifications = SystemNotification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:10]
    
    unread_notification_count = SystemNotification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    # Get all users
    users = User.objects.all().order_by('-date_joined')
    
    # Get pending password reset requests
    pending_requests_qs = PasswordResetRequest.objects.filter(
        is_approved=False, 
        is_completed=False
    ).select_related('user')
    
    pending_count = pending_requests_qs.count()
    
    context = {
        'total_users': User.objects.filter(is_active=True).count(),
        'total_employees': Employee.objects.filter(is_active=True).count(),
        'system_version': '1.0.0',
        'build_date': '2025.10.28',
        'recent_logs': AuditLog.objects.select_related('user').all()[:20],
        'users': users,
        'database_status': 'Connected',
        'last_backup': timezone.now() - timedelta(hours=2),
        'notifications': notifications,
        'unread_notification_count': unread_notification_count,
        'pending_requests': pending_requests_qs,
        'pending_count': pending_count,
    }
    
    return render(request, 'core/admin.html', context)

@login_required
def profile(request):
    """User profile page"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.phone = request.POST.get('phone', '')
        # Department is not editable by users - it's tied to their role
        user.save()
        
        # Log the action
        AuditLog.objects.create(
            user=user,
            action='Update Profile',
            module='Core',
            description=f'User {user.username} updated their profile',
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('core:profile')
    
    return render(request, 'core/profile.html')




@login_required
def change_password(request):
    """Change password"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
        else:
            # Log the action before changing password
            AuditLog.objects.create(
                user=request.user,
                action='Change Password',
                module='Core',
                description=f'User {request.user.username} changed their password',
                ip_address=get_client_ip(request)
            )
            
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Password changed successfully! Please login with your new password.')
            return redirect('core:login')
    
    return render(request, 'core/change_password.html')


@login_required
def notifications(request):
    """View all notifications"""
    notifications = SystemNotification.objects.filter(user=request.user)
    
    # Mark as read
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            SystemNotification.objects.filter(id=notification_id, user=request.user).update(is_read=True)
    
    return render(request, 'core/notifications.html', {'notifications': notifications})


@login_required
def help_page(request):
    """Help and documentation"""
    return render(request, 'core/help.html')


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
@role_required('admin')
def add_user(request):
    """Add new user (Admin only)"""
    if request.method == 'POST':
        try:
            # Get form data
            username = request.POST.get('username')
            email = request.POST.get('email')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            role = request.POST.get('role')
            department = request.POST.get('department', '')
            password = request.POST.get('password')
            
            # Validate required fields
            if not all([username, email, first_name, last_name, role, password]):
                return JsonResponse({
                    'success': False,
                    'message': 'All fields are required'
                })
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Username already exists'
                })
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Email already exists'
                })
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role,
                department=department
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Add User',
                module='Admin',
                description=f'Created user {username} with role {role}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'User {username} created successfully!')
            
            return JsonResponse({
                'success': True,
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.get_full_name(),
                    'email': user.email,
                    'role': user.get_role_display(),
                    'department': user.department or 'N/A',
                    'is_active': user.is_active
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('admin')
def update_user(request, user_id):
    """Update user (Admin only)"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Update user fields
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.role = request.POST.get('role', user.role)
            user.department = request.POST.get('department', user.department)
            
            # Update password if provided
            new_password = request.POST.get('password')
            if new_password:
                user.set_password(new_password)
            
            user.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Update User',
                module='Admin',
                description=f'Updated user {user.username}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'User {user.username} updated successfully!')
            
            return JsonResponse({
                'success': True,
                'message': 'User updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('admin')
def delete_user(request, user_id):
    """Delete user (Admin only)"""
    if request.method == 'POST':
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Prevent deleting yourself
            if user.id == request.user.id:
                return JsonResponse({
                    'success': False,
                    'message': 'You cannot delete your own account'
                })
            
            username = user.username
            user.delete()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Delete User',
                module='Admin',
                description=f'Deleted user {username}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, f'User {username} deleted successfully!')
            
            return JsonResponse({
                'success': True,
                'message': 'User deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('admin')
def post_notice_api(request):
    """Post a new notice (admin only)"""
    if request.method == 'POST':
        try:
            from .models import Notice
            
            title = request.POST.get('title', '').strip()
            category = request.POST.get('category', 'general')
            content = request.POST.get('content', '').strip()
            is_pinned = request.POST.get('is_pinned') == 'true'
            
            if not title or not content:
                return JsonResponse({
                    'success': False,
                    'message': 'Title and content are required'
                })
            
            notice = Notice.objects.create(
                title=title,
                category=category,
                content=content,
                is_pinned=is_pinned,
                posted_by=request.user
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Post Notice',
                module='Core',
                description=f'Posted notice: {title}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Notice posted successfully',
                'notice': {
                    'id': notice.id,
                    'title': notice.title,
                    'category': notice.get_category_display(),
                    'content': notice.content,
                    'is_pinned': notice.is_pinned,
                    'posted_by': notice.posted_by.get_full_name(),
                    'created_at': notice.created_at.strftime('%Y-%m-%d %H:%M')
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


# ==================== PASSWORD RESET FUNCTIONALITY ====================
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseRedirect
from .models import PasswordResetRequest

def is_admin(user):
    return user.is_staff or user.is_superuser

# ✅ Forgot Password - User Request
@csrf_protect
def forgot_password(request):
    if request.user.is_authenticated:
        role_redirects = {
            'admin': 'core:admin_dashboard',
            'inventory': 'inventory:dashboard',
            'production': 'production:dashboard',
            'hr': 'hr:dashboard',
            'finance': 'finance:dashboard',
            'supplier': 'suppliers:dashboard',
        }
        redirect_url = role_redirects.get(request.user.role, 'core:dashboard')
        return redirect(redirect_url)
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
            
            # Check if already pending request
            pending = PasswordResetRequest.objects.filter(
                user=user, 
                is_approved=False, 
                is_completed=False
            ).exists()
            
            if not pending:
                PasswordResetRequest.objects.create(user=user)
                messages.success(request, 'Password reset request sent to admin!')
                return HttpResponseRedirect('/login/?reset_requested=success')
            else:
                messages.warning(request, 'You already have a pending request!')
                return HttpResponseRedirect('/login/?forgot=true')
        except User.DoesNotExist:
            messages.error(request, 'User not found!')
            return HttpResponseRedirect('/login/?forgot=true')
    
    # GET request ke liye template render karo
    return render(request, 'core/forgot_password.html')


# ✅ Reset Requests Page (for Admin)
@login_required
@user_passes_test(is_admin)
def reset_requests(request):
    pending_requests = PasswordResetRequest.objects.filter(
        is_approved=False, 
        is_completed=False
    ).select_related('user')
    
    context = {
        'pending_requests': pending_requests,
        'count': pending_requests.count(),
    }
    return render(request, 'core/reset_requests.html', context)


# ✅ Approve Reset Request
@login_required
@user_passes_test(is_admin)
def approve_reset(request, request_id):
    reset_request = get_object_or_404(PasswordResetRequest, id=request_id)
    
    if not reset_request.is_approved and not reset_request.is_completed:
        reset_request.is_approved = True
        reset_request.save()
        messages.success(request, f'Request approved! Now reset password for {reset_request.user.username}')
        return redirect('core:reset_password', user_id=reset_request.user.id)
    
    messages.error(request, 'Invalid request!')
    return redirect('core:admin_dashboard')


# ✅ Reject Reset Request
@login_required
@user_passes_test(is_admin)
def reject_reset(request, request_id):
    reset_request = get_object_or_404(PasswordResetRequest, id=request_id)
    
    if not reset_request.is_completed:
        reset_request.delete()
        messages.success(request, f'Request rejected for {reset_request.user.username}')
    
    return redirect('core:admin_dashboard')


# ✅ Reset Password Form (for Admin to set new password)
@login_required
@user_passes_test(is_admin)
def reset_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Check if there's an approved request
    has_approved = PasswordResetRequest.objects.filter(
        user=user,
        is_approved=True,
        is_completed=False
    ).exists()
    
    if not has_approved and not request.user.is_superuser:
        messages.error(request, 'No approved request found!')
        return redirect('core:admin_dashboard')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password and new_password == confirm_password:
            if len(new_password) >= 8:
                # Password set karo
                user.set_password(new_password)
                user.save()
                
                # Request complete karo
                reset_request = PasswordResetRequest.objects.filter(
                    user=user,
                    is_approved=True,
                    is_completed=False
                ).last()
                
                if reset_request:
                    reset_request.is_completed = True
                    reset_request.save()
                
                messages.success(request, f'Password reset successful for {user.username}')
                
                # ✅ USER KO LOGOUT KARAO (agar already logged in ho)
                from django.contrib.auth import logout
                logout(request)
                
                # ✅ LOGIN PAGE PAR REDIRECT WITH PASSWORD
                return HttpResponseRedirect(f'/login/?reset_success=1&username={user.username}&password={new_password}')
                
            else:
                messages.error(request, 'Password must be at least 8 characters!')
        else:
            messages.error(request, 'Passwords do not match!')
    
    return render(request, 'core/reset_password.html', {'reset_user': user})




  



@login_required
def ai_insights_view(request):
    """AI Insights dashboard with dynamic data"""
    from .ai_utils import AIInsightsEngine
    from suppliers.models import Supplier
    import json
    
    # Get data from database
    production_orders = ProductionOrder.objects.all()[:10]
    inventory_items = InventoryItem.objects.all()[:10]
    suppliers = Supplier.objects.all()[:5]
    
    # Initialize AI engine
    ai_engine = AIInsightsEngine()
    
    # Generate demand forecast
    forecast_data = ai_engine.generate_demand_forecast()
    
    # Detect anomalies
    anomalies = ai_engine.detect_anomalies(production_orders, inventory_items, suppliers)
    
    # Generate recommendations
    recommendations = ai_engine.generate_recommendations(production_orders, inventory_items, suppliers)
    
    # Predict inventory stockouts
    inventory_predictions = ai_engine.predict_inventory_stockout(inventory_items)
    
    # Calculate AI health
    ai_health = ai_engine.calculate_ai_health()
    
    # Generate efficiency trends
    efficiency_trends = ai_engine.generate_efficiency_trends()
    
    # Get notifications
    notifications = SystemNotification.objects.filter(user=request.user, is_read=False)[:5]
    unread_notification_count = SystemNotification.objects.filter(user=request.user, is_read=False).count()
    
    context = {
        'user': request.user,
        'notifications': notifications,
        'unread_notification_count': unread_notification_count,
        
        # Forecast data
        'forecast_labels': json.dumps(forecast_data['labels']),
        'historical_demand': json.dumps(forecast_data['historical']),
        'forecast_demand': json.dumps(forecast_data['forecast']),
        'forecast_recommendation': forecast_data['recommendation'],
        
        # AI Health
        'ai_health': ai_health,
        
        # Anomalies
        'anomalies': anomalies,
        
        # Recommendations
        'recommendations': recommendations,
        
        # Predictions
        'inventory_predictions': inventory_predictions,
        
        # Efficiency trends
        'efficiency_labels': json.dumps(efficiency_trends['labels']),
        'efficiency_data': json.dumps(efficiency_trends['data']),
    }
    
    return render(request, 'core/ai_insights.html', context)



@login_required
def ai_insights_api(request):
    """API endpoint for refreshing AI insights"""
    from .ai_utils import AIInsightsEngine
    from suppliers.models import Supplier
    import json
    
    if request.method == 'GET':
        # Get fresh data
        production_orders = ProductionOrder.objects.all()[:10]
        inventory_items = InventoryItem.objects.all()[:10]
        suppliers = Supplier.objects.all()[:5]
        
        ai_engine = AIInsightsEngine()
        
        # Generate new insights
        forecast_data = ai_engine.generate_demand_forecast()
        anomalies = ai_engine.detect_anomalies(production_orders, inventory_items, suppliers)
        recommendations = ai_engine.generate_recommendations(production_orders, inventory_items, suppliers)
        inventory_predictions = ai_engine.predict_inventory_stockout(inventory_items)
        ai_health = ai_engine.calculate_ai_health()
        efficiency_trends = ai_engine.generate_efficiency_trends()
        
        return JsonResponse({
            'success': True,
            'data': {
                'forecast': forecast_data,
                'anomalies': anomalies,
                'recommendations': recommendations,
                'inventory_predictions': inventory_predictions,
                'ai_health': ai_health,
                'efficiency_trends': efficiency_trends
            }
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
