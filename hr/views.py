from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Avg
from datetime import date, datetime
from decimal import Decimal
from .models import Employee, Attendance, LeaveRequest, Payroll, PerformanceReview
from core.models import AuditLog, User, SystemNotification
from core.views import role_required, get_client_ip

@login_required
@role_required('hr', 'admin')
def dashboard(request):
    """HR dashboard"""
    from django.db.models import Q
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    # Calculate monthly payroll summary
    monthly_payrolls = Payroll.objects.filter(
        payment_date__month=current_month,
        payment_date__year=current_year
    )
    
    payroll_summary = monthly_payrolls.aggregate(
        total_gross=Sum('gross_pay'),
        total_federal_tax=Sum('federal_tax'),
        total_state_tax=Sum('state_tax'),
        total_social_security=Sum('social_security'),
        total_medicare=Sum('medicare'),
        total_other=Sum('other_deductions'),
        total_net=Sum('net_pay')
    )
    
    # Calculate total deductions
    total_gross = payroll_summary['total_gross'] or 0
    total_deductions = (
        (payroll_summary['total_federal_tax'] or 0) +
        (payroll_summary['total_state_tax'] or 0) +
        (payroll_summary['total_social_security'] or 0) +
        (payroll_summary['total_medicare'] or 0) +
        (payroll_summary['total_other'] or 0)
    )
    total_net = payroll_summary['total_net'] or 0
    
    # Get current month name and year for display
    from calendar import month_name
    current_month_name = month_name[current_month]
    
    # Count employees on approved leave (not yet ended)
    # Show all approved leaves where the end date hasn't passed yet
    on_leave_count = LeaveRequest.objects.filter(
        status='approved',
        end_date__gte=today
    ).count()
    
    context = {
        'today': today,
        'total_employees': Employee.objects.filter(is_active=True).count(),
        'present_today': Attendance.objects.filter(date=today, status='present').count(),
        'on_leave': on_leave_count,
        'pending_leave_requests': LeaveRequest.objects.filter(status='pending').count(),
        'monthly_payroll': total_net,
        'employees': Employee.objects.filter(is_active=True).order_by('-hire_date')[:20],
        'recent_leave_requests': LeaveRequest.objects.select_related('employee').all()[:10],
        'recent_attendance': Attendance.objects.select_related('employee').filter(date=today)[:10],
        'recent_payrolls': Payroll.objects.select_related('employee').all()[:5],
        # Payroll summary for the card
        'payroll_gross': total_gross,
        'payroll_deductions': total_deductions,
        'payroll_net': total_net,
        'payroll_month': f"{current_month_name} {current_year}",
    }
    
    return render(request, 'hr/dashboard.html', context)


@login_required
def employee_list(request):
    """List all employees"""
    employees = Employee.objects.filter(is_active=True)
    
    # Filter by department
    department = request.GET.get('department')
    if department:
        employees = employees.filter(department=department)
    
    context = {
        'employees': employees,
        'departments': Employee.DEPARTMENT_CHOICES,
    }
    
    return render(request, 'hr/employee_list.html', context)


@login_required
def add_employee(request):
    """Add new employee"""
    if request.method == 'POST':
        employee = Employee.objects.create(
            employee_id=request.POST.get('employee_id'),
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            department=request.POST.get('department'),
            position=request.POST.get('position'),
            monthly_salary=float(request.POST.get('monthly_salary')),
            hire_date=request.POST.get('hire_date'),
        )
        
        AuditLog.objects.create(
            user=request.user,
            action='Add Employee',
            module='HR',
            description=f'Added employee {employee.full_name}',
        )
        
        messages.success(request, 'Employee added successfully!')
        return redirect('hr:employee_detail', employee_id=employee.id)
    
    return render(request, 'hr/add_employee.html', {
        'departments': Employee.DEPARTMENT_CHOICES
    })


@login_required
def employee_detail(request, employee_id):
    """View employee details"""
    employee = get_object_or_404(Employee, id=employee_id)
    attendance_records = Attendance.objects.filter(employee=employee)[:30]
    leave_requests = LeaveRequest.objects.filter(employee=employee)[:10]
    
    context = {
        'employee': employee,
        'attendance_records': attendance_records,
        'leave_requests': leave_requests,
    }
    
    return render(request, 'hr/employee_detail.html', context)


@login_required
def attendance(request):
    """Manage attendance"""
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        employee = get_object_or_404(Employee, id=employee_id)
        
        Attendance.objects.create(
            employee=employee,
            date=request.POST.get('date'),
            status=request.POST.get('status'),
            check_in=request.POST.get('check_in') or None,
            check_out=request.POST.get('check_out') or None,
            notes=request.POST.get('notes', ''),
        )
        
        messages.success(request, 'Attendance recorded!')
        return redirect('hr:attendance')
    
    today = date.today()
    attendance_records = Attendance.objects.filter(date=today)
    employees = Employee.objects.filter(is_active=True)
    
    context = {
        'attendance_records': attendance_records,
        'employees': employees,
    }
    
    return render(request, 'hr/attendance.html', context)


@login_required
def leave_requests(request):
    """View all leave requests"""
    requests = LeaveRequest.objects.all()
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        requests = requests.filter(status=status)
    
    context = {
        'leave_requests': requests,
        'status_choices': LeaveRequest.STATUS_CHOICES,
    }
    
    return render(request, 'hr/leave_requests.html', context)


@login_required
def create_leave_request(request):
    """Create leave request"""
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        employee = get_object_or_404(Employee, id=employee_id)
        
        LeaveRequest.objects.create(
            employee=employee,
            leave_type=request.POST.get('leave_type'),
            start_date=request.POST.get('start_date'),
            end_date=request.POST.get('end_date'),
            reason=request.POST.get('reason'),
        )
        
        messages.success(request, 'Leave request submitted!')
        return redirect('hr:leave_requests')
    
    employees = Employee.objects.filter(is_active=True)
    return render(request, 'hr/create_leave_request.html', {
        'employees': employees,
        'leave_types': LeaveRequest.LEAVE_TYPES,
    })


@login_required
def approve_leave(request, request_id):
    """Approve/reject leave request"""
    leave_request = get_object_or_404(LeaveRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            leave_request.status = 'approved'
        else:
            leave_request.status = 'rejected'
        
        leave_request.approved_by = request.user
        leave_request.save()
        
        AuditLog.objects.create(
            user=request.user,
            action=f'{action.title()} Leave',
            module='HR',
            description=f'{action.title()}d leave request for {leave_request.employee.full_name}',
        )
        
        messages.success(request, f'Leave request {action}d!')
        return redirect('hr:leave_requests')
    
    return render(request, 'hr/approve_leave.html', {'leave_request': leave_request})


@login_required
@role_required('hr', 'admin')
def payroll(request):
    """View payroll records"""
    payroll_records = Payroll.objects.all()[:50]
    
    context = {
        'payroll_records': payroll_records,
    }
    
    return render(request, 'hr/payroll.html', context)


@login_required
@role_required('hr', 'admin')
def payroll_management(request):
    """Payroll management page"""
    from datetime import date
    
    # Get current month and year
    today = date.today()
    pay_period = today.strftime('%B %Y')
    payment_date = today
    batch_id = f"PAY-{today.year}-{today.month:02d}"
    
    # Get all active employees
    employees = Employee.objects.filter(is_active=True).order_by('employee_id')
    
    # Calculate totals
    total_gross = employees.aggregate(total=Sum('monthly_salary'))['total'] or 0
    total_deductions = total_gross * Decimal('0.3245')  # Default tax rates sum
    total_net = total_gross - total_deductions
    
    context = {
        'employees': employees,
        'pay_period': pay_period,
        'payment_date': payment_date,
        'batch_id': batch_id,
        'total_gross': total_gross,
        'total_deductions': total_deductions,
        'total_net': total_net,
    }
    
    return render(request, 'hr/payroll.html', context)


@login_required
def run_payroll(request):
    """Run payroll for employees"""
    if request.method == 'POST':
        pay_period = request.POST.get('pay_period')
        payment_date = request.POST.get('payment_date')
        
        # Get tax rates
        federal_tax_rate = float(request.POST.get('federal_tax', 15)) / 100
        state_tax_rate = float(request.POST.get('state_tax', 5)) / 100
        social_security_rate = float(request.POST.get('social_security', 6.2)) / 100
        medicare_rate = float(request.POST.get('medicare', 1.45)) / 100
        
        employees = Employee.objects.filter(is_active=True)
        
        for employee in employees:
            gross_pay = employee.monthly_salary
            
            # Calculate deductions
            federal_tax = gross_pay * federal_tax_rate
            state_tax = gross_pay * state_tax_rate
            social_security = gross_pay * social_security_rate
            medicare = gross_pay * medicare_rate
            
            # Create payroll record
            payroll = Payroll.objects.create(
                employee=employee,
                pay_period=pay_period,
                gross_pay=gross_pay,
                federal_tax=federal_tax,
                state_tax=state_tax,
                social_security=social_security,
                medicare=medicare,
                payment_date=payment_date,
            )
            
            payroll.calculate_net_pay()
            payroll.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='Run Payroll',
            module='HR',
            description=f'Processed payroll for {pay_period}',
        )
        
        messages.success(request, 'Payroll processed successfully!')
        return redirect('hr:payroll')
    
    employees = Employee.objects.filter(is_active=True)
    return render(request, 'hr/run_payroll.html', {'employees': employees})



@login_required
@role_required('hr', 'admin')
def add_employee_api(request):
    """Add new employee via API"""
    if request.method == 'POST':
        try:
            # Generate employee ID
            last_employee = Employee.objects.all().order_by('-id').first()
            if last_employee and last_employee.employee_id:
                last_num = int(last_employee.employee_id.split('-')[1])
                new_num = last_num + 1
            else:
                new_num = 1
            employee_id = f"EMP-{new_num:03d}"
            
            # Get form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            department = request.POST.get('department')
            position = request.POST.get('position')
            monthly_salary = request.POST.get('monthly_salary')
            hire_date = request.POST.get('hire_date', date.today())
            
            # Validate required fields
            if not all([first_name, last_name, email, phone, department, position, monthly_salary]):
                return JsonResponse({
                    'success': False,
                    'message': 'All fields are required'
                })
            
            # Check if email already exists
            if Employee.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Email already exists'
                })
            
            # Create employee
            employee = Employee.objects.create(
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                department=department,
                position=position,
                monthly_salary=Decimal(monthly_salary),
                hire_date=hire_date,
                is_active=True
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Add Employee',
                module='HR',
                description=f'Added employee {employee.full_name} ({employee.employee_id})',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Employee added successfully',
                'employee': {
                    'id': employee.id,
                    'employee_id': employee.employee_id,
                    'name': employee.full_name,
                    'email': employee.email,
                    'phone': employee.phone,
                    'department': employee.get_department_display(),
                    'position': employee.position,
                    'salary': float(employee.monthly_salary)
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('hr', 'admin')
def update_employee_api(request, employee_id):
    """Update employee information via API"""
    if request.method == 'POST':
        try:
            employee = get_object_or_404(Employee, id=employee_id)
            
            # Update fields
            employee.first_name = request.POST.get('first_name', employee.first_name)
            employee.last_name = request.POST.get('last_name', employee.last_name)
            employee.email = request.POST.get('email', employee.email)
            employee.phone = request.POST.get('phone', employee.phone)
            employee.department = request.POST.get('department', employee.department)
            employee.position = request.POST.get('position', employee.position)
            
            if request.POST.get('monthly_salary'):
                employee.monthly_salary = Decimal(request.POST.get('monthly_salary'))
            
            employee.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Update Employee',
                module='HR',
                description=f'Updated employee {employee.full_name}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Employee updated successfully',
                'employee': {
                    'id': employee.id,
                    'employee_id': employee.employee_id,
                    'name': employee.full_name,
                    'email': employee.email,
                    'phone': employee.phone,
                    'department': employee.get_department_display(),
                    'position': employee.position,
                    'salary': float(employee.monthly_salary)
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('hr', 'admin')
def create_leave_request_api(request):
    """Create leave request via API"""
    if request.method == 'POST':
        try:
            employee_name = request.POST.get('employee_name')
            leave_type = request.POST.get('leave_type')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            reason = request.POST.get('reason')
            
            # Validate required fields
            if not all([employee_name, leave_type, start_date, end_date, reason]):
                return JsonResponse({
                    'success': False,
                    'message': 'All fields are required'
                })
            
            # Find employee by name
            name_parts = employee_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            employee = Employee.objects.filter(
                first_name__icontains=first_name,
                last_name__icontains=last_name,
                is_active=True
            ).first()
            
            if not employee:
                return JsonResponse({
                    'success': False,
                    'message': 'Employee not found'
                })
            
            # Parse dates
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid date format'
                })
            
            # Create leave request
            leave_request = LeaveRequest.objects.create(
                employee=employee,
                leave_type=leave_type.lower().replace(' ', '_'),
                start_date=start_date_obj,
                end_date=end_date_obj,
                reason=reason,
                status='pending'
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Create Leave Request',
                module='HR',
                description=f'Created leave request for {employee.full_name}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Leave request submitted successfully',
                'leave_request': {
                    'id': leave_request.id,
                    'employee_name': employee.full_name,
                    'leave_type': leave_request.get_leave_type_display(),
                    'start_date': leave_request.start_date.strftime('%Y-%m-%d'),
                    'end_date': leave_request.end_date.strftime('%Y-%m-%d'),
                    'reason': leave_request.reason,
                    'status': leave_request.get_status_display()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('hr', 'admin')
def approve_leave_api(request, request_id):
    """Approve or reject leave request via API"""
    if request.method == 'POST':
        try:
            leave_request = get_object_or_404(LeaveRequest, id=request_id)
            action = request.POST.get('action')  # 'approve' or 'reject'
            
            if action == 'approve':
                leave_request.status = 'approved'
            elif action == 'reject':
                leave_request.status = 'rejected'
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid action'
                })
            
            leave_request.approved_by = request.user
            leave_request.save()
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action=f'{action.title()} Leave',
                module='HR',
                description=f'{action.title()}d leave request for {leave_request.employee.full_name}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Leave request {action}d successfully',
                'status': leave_request.get_status_display()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('hr', 'admin')
def process_payroll_api(request):
    """Process payroll for selected employees via API"""
    if request.method == 'POST':
        try:
            import json
            
            # Get form data
            pay_period = request.POST.get('pay_period', f"{date.today().strftime('%B %Y')}")
            payment_date = request.POST.get('payment_date', date.today())
            
            # Parse payment date
            if isinstance(payment_date, str):
                try:
                    payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
                except ValueError:
                    payment_date = date.today()
            
            # Get tax rates
            federal_tax_rate = float(request.POST.get('federal_tax', 15)) / 100
            state_tax_rate = float(request.POST.get('state_tax', 5)) / 100
            social_security_rate = float(request.POST.get('social_security', 6.2)) / 100
            medicare_rate = float(request.POST.get('medicare', 1.45)) / 100
            
            # Get selected employee IDs
            selected_employees_json = request.POST.get('selected_employees', '[]')
            selected_employee_ids = json.loads(selected_employees_json)
            
            if not selected_employee_ids:
                # If no specific employees selected, process all active employees
                employees = Employee.objects.filter(is_active=True)
            else:
                employees = Employee.objects.filter(id__in=selected_employee_ids, is_active=True)
            
            payroll_records = []
            total_net_pay = 0
            
            for employee in employees:
                gross_pay = employee.monthly_salary
                
                # Calculate deductions
                federal_tax = gross_pay * Decimal(str(federal_tax_rate))
                state_tax = gross_pay * Decimal(str(state_tax_rate))
                social_security = gross_pay * Decimal(str(social_security_rate))
                medicare = gross_pay * Decimal(str(medicare_rate))
                other_deductions = Decimal('0.00')
                
                # Calculate net pay BEFORE creating the record
                total_deductions = federal_tax + state_tax + social_security + medicare + other_deductions
                net_pay = gross_pay - total_deductions
                
                # Create payroll record with net_pay already calculated
                payroll = Payroll.objects.create(
                    employee=employee,
                    pay_period=pay_period,
                    gross_pay=gross_pay,
                    federal_tax=federal_tax,
                    state_tax=state_tax,
                    social_security=social_security,
                    medicare=medicare,
                    other_deductions=other_deductions,
                    net_pay=net_pay,
                    payment_date=payment_date,
                    is_paid=False
                )
                
                total_net_pay += payroll.net_pay
                
                payroll_records.append({
                    'employee_name': employee.full_name,
                    'gross_pay': float(gross_pay),
                    'federal_tax': float(federal_tax),
                    'state_tax': float(state_tax),
                    'social_security': float(social_security),
                    'medicare': float(medicare),
                    'net_pay': float(payroll.net_pay)
                })
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Process Payroll',
                module='HR',
                description=f'Processed payroll for {len(payroll_records)} employees - {pay_period}',
                ip_address=get_client_ip(request)
            )
            
            # Send notification to finance managers
            finance_managers = User.objects.filter(role__in=['finance', 'admin'])
            
            # Create detailed employee list for notification
            employee_names = ', '.join([record['employee_name'] for record in payroll_records[:5]])
            if len(payroll_records) > 5:
                employee_names += f' and {len(payroll_records) - 5} more'
            
            for manager in finance_managers:
                SystemNotification.objects.create(
                    user=manager,
                    title='Payroll Processed - Payment Required',
                    message=f'Payroll for {pay_period} has been processed for {len(payroll_records)} employees. Total amount: PKR {total_net_pay:,.2f}. Employees: {employee_names}. Please process salary payments.',
                    notification_type='info'
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Payroll processed successfully for {len(payroll_records)} employees',
                'payroll_records': payroll_records,
                'total_net_pay': float(total_net_pay)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
@role_required('hr', 'admin')
def performance_report(request):
    """Generate employee performance report"""
    from django.db.models import Avg, Count
    
    # Get all employees with their performance data
    employees_data = []
    
    for employee in Employee.objects.filter(is_active=True):
        # Get performance reviews
        reviews = PerformanceReview.objects.filter(employee=employee)
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = reviews.count()
        
        # Get attendance data
        total_days = Attendance.objects.filter(employee=employee).count()
        present_days = Attendance.objects.filter(employee=employee, status='present').count()
        attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
        
        # Get leave data
        approved_leaves = LeaveRequest.objects.filter(
            employee=employee,
            status='approved'
        ).count()
        
        employees_data.append({
            'employee': employee,
            'avg_rating': round(avg_rating, 2),
            'review_count': review_count,
            'attendance_rate': round(attendance_rate, 1),
            'total_days': total_days,
            'present_days': present_days,
            'approved_leaves': approved_leaves,
        })
    
    # Sort by average rating (highest first)
    employees_data.sort(key=lambda x: x['avg_rating'], reverse=True)
    
    context = {
        'employees_data': employees_data,
        'total_employees': len(employees_data),
        'report_date': date.today(),
    }
    
    return render(request, 'hr/performance_report.html', context)


@login_required
@role_required('hr', 'admin')
def communicate_finance(request):
    """Send salary disbursement request to finance department"""
    if request.method == 'POST':
        try:
            import json
            from finance.models import Transaction
            
            # Get payroll data
            pay_period = request.POST.get('pay_period')
            payroll_ids_json = request.POST.get('payroll_ids', '[]')
            payroll_ids = json.loads(payroll_ids_json)
            
            if not payroll_ids:
                return JsonResponse({
                    'success': False,
                    'message': 'No payroll records selected'
                })
            
            # Get payroll records
            payroll_records = Payroll.objects.filter(id__in=payroll_ids)
            total_amount = payroll_records.aggregate(total=Sum('net_pay'))['total'] or 0
            
            # Create transaction request for finance
            transaction = Transaction.objects.create(
                transaction_type='expense',
                category='salary',
                amount=total_amount,
                description=f'Salary disbursement for {pay_period} - {payroll_records.count()} employees',
                transaction_date=date.today(),
                status='pending',
                created_by=request.user
            )
            
            # Log the action
            AuditLog.objects.create(
                user=request.user,
                action='Request Salary Disbursement',
                module='HR',
                description=f'Requested salary disbursement of PKR {total_amount} for {pay_period}',
                ip_address=get_client_ip(request)
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Salary disbursement request sent to finance department',
                'transaction_id': transaction.id,
                'total_amount': float(total_amount),
                'employee_count': payroll_records.count()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
