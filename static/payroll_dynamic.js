// Payroll Management - Dynamic JavaScript

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

// Calculate and update payroll preview
function calculatePayroll() {
    const federalTaxRate = parseFloat(document.getElementById('federalTax').value) / 100 || 0;
    const stateTaxRate = parseFloat(document.getElementById('stateTax').value) / 100 || 0;
    const socialSecurityRate = parseFloat(document.getElementById('socialSecurity').value) / 100 || 0;
    const medicareRate = parseFloat(document.getElementById('medicare').value) / 100 || 0;

    let totals = {
        gross: 0,
        federalTax: 0,
        stateTax: 0,
        socialSecurity: 0,
        medicare: 0,
        otherDeductions: 0,
        netPay: 0,
        employeeCount: 0
    };

    const previewTable = document.getElementById('payrollPreview');
    previewTable.innerHTML = '';

    const selectedCheckboxes = document.querySelectorAll('.employee-checkbox:checked');
    totals.employeeCount = selectedCheckboxes.length;

    selectedCheckboxes.forEach(checkbox => {
        const grossPay = parseFloat(checkbox.dataset.salary) || 0;
        const employeeName = checkbox.dataset.name;

        const federalTax = grossPay * federalTaxRate;
        const stateTax = grossPay * stateTaxRate;
        const socialSecurity = grossPay * socialSecurityRate;
        const medicare = grossPay * medicareRate;
        const otherDeductions = 0; // Can be customized
        const netPay = grossPay - (federalTax + stateTax + socialSecurity + medicare + otherDeductions);

        // Add to totals
        totals.gross += grossPay;
        totals.federalTax += federalTax;
        totals.stateTax += stateTax;
        totals.socialSecurity += socialSecurity;
        totals.medicare += medicare;
        totals.otherDeductions += otherDeductions;
        totals.netPay += netPay;

        // Add row to preview table
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${employeeName}</td>
            <td class="text-end">PKR ${grossPay.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            <td class="text-end">PKR ${federalTax.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            <td class="text-end">PKR ${stateTax.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            <td class="text-end">PKR ${socialSecurity.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            <td class="text-end">PKR ${medicare.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            <td class="text-end">PKR ${otherDeductions.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            <td class="text-end fw-bold">PKR ${netPay.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
        `;
        previewTable.appendChild(row);
    });

    // Update totals in footer
    document.getElementById('totalGross').textContent = `PKR ${totals.gross.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('totalFederalTax').textContent = `PKR ${totals.federalTax.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('totalStateTax').textContent = `PKR ${totals.stateTax.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('totalSocialSecurity').textContent = `PKR ${totals.socialSecurity.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('totalMedicare').textContent = `PKR ${totals.medicare.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('totalOtherDeductions').textContent = `PKR ${totals.otherDeductions.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('totalNetPay').textContent = `PKR ${totals.netPay.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    // Update summary cards
    document.getElementById('summaryGrossPay').textContent = `PKR ${totals.gross.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0})}`;
    document.getElementById('summaryDeductions').textContent = `PKR ${(totals.federalTax + totals.stateTax + totals.socialSecurity + totals.medicare + totals.otherDeductions).toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0})}`;
    document.getElementById('summaryNetPay').textContent = `PKR ${totals.netPay.toLocaleString('en-US', {minimumFractionDigits: 0, maximumFractionDigits: 0})}`;

    // Update sidebar summary
    document.getElementById('summaryEmployeeCount').textContent = totals.employeeCount;
    document.getElementById('summaryTotalGross').textContent = `PKR ${totals.gross.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('summaryTotalDeductions').textContent = `PKR ${(totals.federalTax + totals.stateTax + totals.socialSecurity + totals.medicare + totals.otherDeductions).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    document.getElementById('summaryTotalNet').textContent = `PKR ${totals.netPay.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initial calculation
    calculatePayroll();

    // Update on employee selection change
    document.querySelectorAll('.employee-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const row = this.closest('tr');
            if (this.checked) {
                row.classList.add('selected');
            } else {
                row.classList.remove('selected');
            }
            calculatePayroll();
        });
    });

    // Select/Deselect all employees
    document.getElementById('checkAllEmployees').addEventListener('change', function() {
        document.querySelectorAll('.employee-checkbox').forEach(checkbox => {
            checkbox.checked = this.checked;
            const row = checkbox.closest('tr');
            if (this.checked) {
                row.classList.add('selected');
            } else {
                row.classList.remove('selected');
            }
        });
        calculatePayroll();
    });

    document.getElementById('selectAllEmployees').addEventListener('change', function() {
        document.getElementById('checkAllEmployees').checked = this.checked;
        document.getElementById('checkAllEmployees').dispatchEvent(new Event('change'));
    });

    // Update on tax rate change
    document.querySelectorAll('.tax-input').forEach(input => {
        input.addEventListener('input', calculatePayroll);
    });

    // Run Payroll button
    document.getElementById('runPayrollBtn').addEventListener('click', function() {
        const selectedCheckboxes = document.querySelectorAll('.employee-checkbox:checked');
        
        if (selectedCheckboxes.length === 0) {
            alert('Please select at least one employee to process payroll');
            return;
        }

        if (!confirm(`Are you sure you want to process payroll for ${selectedCheckboxes.length} employee(s)?`)) {
            return;
        }

        const selectedEmployeeIds = Array.from(selectedCheckboxes).map(cb => cb.dataset.id);

        const formData = new FormData();
        formData.append('pay_period', document.getElementById('payPeriod').value);
        formData.append('payment_date', document.getElementById('paymentDate').value);
        formData.append('federal_tax', document.getElementById('federalTax').value);
        formData.append('state_tax', document.getElementById('stateTax').value);
        formData.append('social_security', document.getElementById('socialSecurity').value);
        formData.append('medicare', document.getElementById('medicare').value);
        formData.append('selected_employees', JSON.stringify(selectedEmployeeIds));
        formData.append('notes', document.getElementById('payrollNotes').value);
        formData.append('payment_method', document.getElementById('paymentMethod').value);
        formData.append('bank_account', document.getElementById('bankAccount').value);

        // Show loading state
        const btn = this;
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';

        fetch('/hr/api/payroll/process/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = originalText;

            if (data.success) {
                alert(`✅ Payroll processed successfully!\n\n` +
                      `Employees: ${data.payroll_records.length}\n` +
                      `Total Net Pay: PKR ${data.total_net_pay.toLocaleString('en-US', {minimumFractionDigits: 2})}\n\n` +
                      `Payroll records have been saved to the database.`);
                
                // Optionally redirect or reload
                // window.location.href = '/hr/payroll/history/';
            } else {
                alert('❌ Error: ' + data.message);
            }
        })
        .catch(error => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            console.error('Error:', error);
            alert('An error occurred while processing payroll. Please try again.');
        });
    });
});
