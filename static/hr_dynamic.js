// HR Module - Dynamic JavaScript with API Integration

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// ==================== EMPLOYEE MANAGEMENT ====================
document.addEventListener('DOMContentLoaded', function() {
    const employeeForm = document.getElementById('employeeForm');
    const tableBody = document.querySelector('#employeeTable tbody');
    
    if (employeeForm) {
        employeeForm.addEventListener('submit', function(e) {
            e.preventDefault();

            if (!employeeForm.checkValidity()) {
                e.stopPropagation();
                employeeForm.classList.add('was-validated');
                return;
            }

            // Prepare form data
            const formData = new FormData();
            const firstName = document.getElementById('firstName').value;
            const lastName = document.getElementById('lastName').value;
            
            formData.append('first_name', firstName);
            formData.append('last_name', lastName);
            formData.append('email', document.getElementById('email').value);
            formData.append('phone', document.getElementById('phone').value);
            formData.append('department', document.getElementById('department').value);
            formData.append('position', document.getElementById('position').value);
            formData.append('monthly_salary', document.getElementById('salary').value);
            formData.append('hire_date', new Date().toISOString().split('T')[0]);

            // Send to backend
            fetch('/hr/api/employees/add/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    employeeForm.reset();
                    employeeForm.classList.remove('was-validated');
                    
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addEmployeeModal'));
                    if (modal) modal.hide();
                    
                    // Reload page to show new employee
                    window.location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while adding the employee');
            });
        });
    }
});

// ==================== LEAVE REQUEST MANAGEMENT ====================
document.addEventListener('DOMContentLoaded', function() {
    const leaveForm = document.getElementById('leaveForm');
    
    if (leaveForm) {
        leaveForm.addEventListener('submit', function(e) {
            e.preventDefault();

            if (!leaveForm.checkValidity()) {
                e.stopPropagation();
                leaveForm.classList.add('was-validated');
                return;
            }

            // Prepare form data
            const formData = new FormData();
            formData.append('employee_name', document.getElementById('leaveEmpName').value);
            formData.append('leave_type', document.getElementById('leaveType').value);
            formData.append('start_date', document.getElementById('leaveStart').value);
            formData.append('end_date', document.getElementById('leaveEnd').value);
            formData.append('reason', document.getElementById('leaveReason').value);

            // Send to backend
            fetch('/hr/api/leave-requests/create/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    leaveForm.reset();
                    leaveForm.classList.remove('was-validated');
                    
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('leaveRequestModal'));
                    if (modal) modal.hide();
                    
                    // Reload page to show new leave request
                    window.location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while submitting the leave request');
            });
        });
    }

    // Approve/Reject leave requests
    document.querySelectorAll('.btn-approve, .btn-reject').forEach(button => {
        button.addEventListener('click', function() {
            const row = this.closest('tr');
            const leaveId = row.dataset.leaveId;
            const action = this.classList.contains('btn-approve') ? 'approve' : 'reject';

            if (!leaveId) {
                alert('Leave request ID not found');
                return;
            }

            const formData = new FormData();
            formData.append('action', action);

            fetch(`/hr/api/leave-requests/${leaveId}/approve/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    window.location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred');
            });
        });
    });
});

// ==================== PAYROLL PROCESSING ====================
document.addEventListener('DOMContentLoaded', function() {
    const empTable = document.getElementById('payrollEmployees');
    const previewTable = document.getElementById('payrollPreview');
    const processPayrollBtn = document.getElementById('processPayrollBtn');

    // Calculate payroll preview
    function calculatePayroll() {
        if (!previewTable) return;
        
        const fedRate = parseFloat(document.getElementById('federalTax')?.value || 15) / 100;
        const stateRate = parseFloat(document.getElementById('stateTax')?.value || 5) / 100;
        const ssRate = parseFloat(document.getElementById('socialSecurity')?.value || 6.2) / 100;
        const medRate = parseFloat(document.getElementById('medicare')?.value || 1.45) / 100;

        let totals = { gross: 0, fed: 0, state: 0, ss: 0, med: 0, other: 0, net: 0 };
        previewTable.innerHTML = '';

        const selectedCheckboxes = document.querySelectorAll('.emp-checkbox:checked');
        const employeeCount = selectedCheckboxes.length;

        selectedCheckboxes.forEach(cb => {
            const salary = parseFloat(cb.dataset.salary || 0);
            const name = cb.dataset.name || '';
            
            const fedTax = salary * fedRate;
            const stateTax = salary * stateRate;
            const socialSecurity = salary * ssRate;
            const medicare = salary * medRate;
            const otherDeductions = 0; // Can be extended later
            const netPay = salary - (fedTax + stateTax + socialSecurity + medicare + otherDeductions);

            previewTable.innerHTML += `
                <tr class="small">
                    <td class="text-start">${name}</td>
                    <td>PKR ${salary.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    <td>PKR ${fedTax.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    <td>PKR ${stateTax.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    <td>PKR ${socialSecurity.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    <td>PKR ${medicare.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    <td>PKR ${otherDeductions.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    <td class="fw-bold">PKR ${netPay.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                </tr>
            `;

            totals.gross += salary;
            totals.fed += fedTax;
            totals.state += stateTax;
            totals.ss += socialSecurity;
            totals.med += medicare;
            totals.other += otherDeductions;
            totals.net += netPay;
        });

        // Update footer totals in preview table
        if (document.getElementById('totalGross')) {
            document.getElementById('totalGross').innerText = `PKR ${totals.gross.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            document.getElementById('totalFederalTax').innerText = `PKR ${totals.fed.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            document.getElementById('totalStateTax').innerText = `PKR ${totals.state.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            document.getElementById('totalSocialSecurity').innerText = `PKR ${totals.ss.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            document.getElementById('totalMedicare').innerText = `PKR ${totals.med.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            document.getElementById('totalOtherDeductions').innerText = `PKR ${totals.other.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            document.getElementById('totalNetPay').innerText = `PKR ${totals.net.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        }

        // Update summary card
        const totalDeductions = totals.fed + totals.state + totals.ss + totals.med + totals.other;
        if (document.getElementById('summaryEmployees')) {
            document.getElementById('summaryEmployees').innerText = employeeCount;
            document.getElementById('summaryGross').innerText = `PKR ${totals.gross.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            document.getElementById('summaryDeductions').innerText = `PKR ${totalDeductions.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            document.getElementById('summaryNet').innerText = `PKR ${totals.net.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        }
    }

    // Event listeners for payroll calculation
    if (empTable) {
        empTable.addEventListener('change', (e) => {
            if (e.target.classList.contains('emp-checkbox')) calculatePayroll();
        });
    }

    // Add event listeners to tax input fields
    const taxInputs = ['federalTax', 'stateTax', 'socialSecurity', 'medicare'];
    taxInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('input', calculatePayroll);
        }
    });

    const checkAll = document.getElementById('checkAll');
    if (checkAll) {
        checkAll.addEventListener('change', function() {
            document.querySelectorAll('.emp-checkbox').forEach(cb => cb.checked = this.checked);
            calculatePayroll();
        });
    }

    // Process payroll via API
    if (processPayrollBtn) {
        processPayrollBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const selectedCheckboxes = document.querySelectorAll('.emp-checkbox:checked');
            const selectedEmployeeIds = Array.from(selectedCheckboxes).map(cb => cb.dataset.id);

            if (selectedEmployeeIds.length === 0) {
                alert('Please select at least one employee');
                return;
            }

            // Show confirmation
            if (!confirm(`Process payroll for ${selectedEmployeeIds.length} employees?`)) {
                return;
            }

            // Disable button and show loading
            processPayrollBtn.disabled = true;
            processPayrollBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Processing...';

            const formData = new FormData();
            formData.append('pay_period', document.getElementById('payPeriod')?.value || new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' }));
            formData.append('payment_date', document.getElementById('paymentDate')?.value || new Date().toISOString().split('T')[0]);
            formData.append('federal_tax', document.getElementById('federalTax')?.value || 15);
            formData.append('state_tax', document.getElementById('stateTax')?.value || 5);
            formData.append('social_security', document.getElementById('socialSecurity')?.value || 6.2);
            formData.append('medicare', document.getElementById('medicare')?.value || 1.45);
            formData.append('selected_employees', JSON.stringify(selectedEmployeeIds));

            fetch('/hr/api/payroll/process/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message + '\nTotal Net Pay: PKR ' + data.total_net_pay.toLocaleString());
                    
                    // Close modal
                    const payrollModal = bootstrap.Modal.getInstance(document.getElementById('runPayrollModal'));
                    if (payrollModal) payrollModal.hide();
                    
                    // Reload page
                    window.location.reload();
                } else {
                    alert('Error: ' + data.message);
                    // Re-enable button
                    processPayrollBtn.disabled = false;
                    processPayrollBtn.innerHTML = '<i class="bi bi-play-circle me-1"></i>Process Payroll';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while processing payroll');
                // Re-enable button
                processPayrollBtn.disabled = false;
                processPayrollBtn.innerHTML = '<i class="bi bi-play-circle me-1"></i>Process Payroll';
            });
        });
    }

    // Initialize payroll calculation when modal opens
    const payrollModal = document.getElementById('runPayrollModal');
    if (payrollModal) {
        payrollModal.addEventListener('shown.bs.modal', function() {
            calculatePayroll();
        });
    }
});


// ==================== EDIT EMPLOYEE ====================
function editEmployee(id, firstName, lastName, email, phone, department, position, salary) {
    // Populate the edit form with employee data
    document.getElementById('editEmployeeId').value = id;
    document.getElementById('editFirstName').value = firstName;
    document.getElementById('editLastName').value = lastName;
    document.getElementById('editEmail').value = email;
    document.getElementById('editPhone').value = phone;
    document.getElementById('editDepartment').value = department;
    document.getElementById('editPosition').value = position;
    document.getElementById('editSalary').value = salary;
    
    // Show the modal
    const editModal = new bootstrap.Modal(document.getElementById('editEmployeeModal'));
    editModal.show();
}

// Handle edit employee form submission
document.addEventListener('DOMContentLoaded', function() {
    const editEmployeeForm = document.getElementById('editEmployeeForm');
    
    if (editEmployeeForm) {
        editEmployeeForm.addEventListener('submit', function(e) {
            e.preventDefault();

            if (!editEmployeeForm.checkValidity()) {
                e.stopPropagation();
                editEmployeeForm.classList.add('was-validated');
                return;
            }

            const employeeId = document.getElementById('editEmployeeId').value;
            
            // Prepare form data
            const formData = new FormData();
            formData.append('first_name', document.getElementById('editFirstName').value);
            formData.append('last_name', document.getElementById('editLastName').value);
            formData.append('email', document.getElementById('editEmail').value);
            formData.append('phone', document.getElementById('editPhone').value);
            formData.append('department', document.getElementById('editDepartment').value);
            formData.append('position', document.getElementById('editPosition').value);
            formData.append('monthly_salary', document.getElementById('editSalary').value);

            // Send to backend
            fetch(`/hr/api/employees/${employeeId}/update/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    editEmployeeForm.reset();
                    editEmployeeForm.classList.remove('was-validated');
                    
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editEmployeeModal'));
                    if (modal) modal.hide();
                    
                    // Reload page to show updated employee
                    window.location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while updating the employee');
            });
        });
    }
});
