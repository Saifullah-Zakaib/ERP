// Finance Module - Dynamic JavaScript with API Integration

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

// ==================== DASHBOARD DATA LOADING ====================
function loadDashboardData() {
    fetch('/finance/api/dashboard/')
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const data = result.data;
                
                // Update KPI cards
                updateKPICard('totalRevenue', data.total_revenue, data.revenue_change);
                updateKPICard('totalExpenses', data.total_expenses, data.expense_change);
                updateKPICard('netProfit', data.net_profit, data.profit_change);
                updateKPICard('pendingInvoices', data.pending_invoices_count, null, data.pending_invoices_amount);
                
                // Update expense breakdown
                updateExpenseBreakdown(data.expense_breakdown, data.total_expenses);
                
                // Update recent expenses
                updateRecentExpenses(data.recent_expenses);
                
                // Update invoices list
                updateInvoicesList(data.recent_invoices);
            }
        })
        .catch(error => console.error('Error loading dashboard data:', error));
}

function updateKPICard(cardId, value, change, extraInfo) {
    const valueElement = document.getElementById(cardId + 'Value');
    const changeElement = document.getElementById(cardId + 'Change');
    const extraElement = document.getElementById(cardId + 'Extra');
    
    if (valueElement) {
        if (cardId === 'pendingInvoices') {
            valueElement.textContent = value;
        } else {
            valueElement.textContent = `PKR ${value}K`;
        }
    }
    
    if (changeElement && change !== null) {
        const isPositive = change >= 0;
        const icon = isPositive ? '↑' : '↓';
        const colorClass = isPositive ? 'text-success' : 'text-danger';
        changeElement.innerHTML = `<span class="${colorClass}">${icon} ${Math.abs(change).toFixed(1)}%</span> vs last month`;
    }
    
    if (extraElement && extraInfo !== undefined) {
        extraElement.textContent = `PKR ${(extraInfo / 1000).toFixed(0)}K outstanding`;
    }
}

function updateExpenseBreakdown(breakdown, totalExpenses) {
    const container = document.getElementById('expenseBreakdownList');
    if (!container) return;
    
    if (breakdown.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No expense data available</p>';
        return;
    }
    
    container.innerHTML = breakdown.map(exp => {
        const categoryName = exp.category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        return `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span>${categoryName}</span>
                <div class="d-flex align-items-center gap-2">
                    <div class="progress" style="width: 100px; height: 8px;">
                        <div class="progress-bar" role="progressbar" style="width: ${exp.percentage}%"></div>
                    </div>
                    <span class="fw-bold">${exp.percentage}%</span>
                </div>
            </div>
        `;
    }).join('');
}

function updateRecentExpenses(expenses) {
    const container = document.getElementById('recentExpensesList');
    if (!container) return;
    
    if (expenses.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No recent expenses</p>';
        return;
    }
    
    container.innerHTML = expenses.map(exp => `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <div>
                <div class="fw-medium">${exp.description}</div>
                <small class="text-muted">${exp.date}</small>
            </div>
            <span class="text-danger fw-bold">PKR ${exp.amount.toLocaleString()}</span>
        </div>
    `).join('');
}

function updateInvoicesList(invoices) {
    const tbody = document.getElementById('invoicesTableBody');
    if (!tbody) return;
    
    if (invoices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No invoices found</td></tr>';
        return;
    }
    
    tbody.innerHTML = invoices.map(inv => {
        const statusBadge = getStatusBadge(inv.status);
        return `
            <tr>
                <td>${inv.invoice_number}</td>
                <td>${inv.customer_name}</td>
                <td>${inv.date}</td>
                <td>PKR ${inv.total_amount.toLocaleString()}</td>
                <td><span class="badge ${statusBadge.class}">${statusBadge.text}</span></td>
            </tr>
        `;
    }).join('');
}

function getStatusBadge(status) {
    const badges = {
        'draft': { class: 'bg-secondary', text: 'Draft' },
        'sent': { class: 'bg-warning', text: 'Sent' },
        'paid': { class: 'bg-success', text: 'Paid' },
        'overdue': { class: 'bg-danger', text: 'Overdue' },
        'cancelled': { class: 'bg-dark', text: 'Cancelled' }
    };
    return badges[status] || { class: 'bg-secondary', text: status };
}

// Load dashboard data on page load
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('totalRevenueValue')) {
        loadDashboardData();
        // Refresh every 60 seconds
        setInterval(loadDashboardData, 60000);
    }
});

// ==================== PAYMENT MANAGEMENT ====================
document.addEventListener('DOMContentLoaded', function() {
    const paymentForm = document.getElementById('paymentForm');
    
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            e.preventDefault();

            if (!paymentForm.checkValidity()) {
                e.stopPropagation();
                paymentForm.classList.add('was-validated');
                return;
            }

            // Prepare form data
            const formData = new FormData();
            formData.append('payment_type', document.getElementById('paymentType').value);
            formData.append('payment_method', document.getElementById('paymentMethod').value);
            formData.append('amount', document.getElementById('paymentAmount').value);
            formData.append('payment_date', document.getElementById('paymentDate').value);
            formData.append('recipient', document.getElementById('recipient').value);
            formData.append('reference_number', document.getElementById('referenceNumber').value);
            formData.append('notes', document.getElementById('paymentNotes').value);

            // Send to backend
            fetch('/finance/api/payments/record/', {
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
                    paymentForm.reset();
                    paymentForm.classList.remove('was-validated');
                    
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('recordPaymentModal'));
                    if (modal) modal.hide();
                    
                    // Reload page to show new payment
                    window.location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while recording the payment');
            });
        });
    }
});

// ==================== INVOICE MANAGEMENT ====================
document.addEventListener('DOMContentLoaded', function() {
    const addItemBtn = document.getElementById('addNewItemRowBtn');
    const modalItemsBody = document.getElementById('modalItemsBody');
    const saveBtn = document.getElementById('saveInvoiceBtn');
    const grandTotalDisplay = document.getElementById('grandTotalDisplay');

    if (addItemBtn) {
        addItemBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><input type="text" class="form-control form-control-sm item-desc" required></td>
                <td><input type="number" class="form-control form-control-sm item-qty" value="1" min="1"></td>
                <td><input type="number" class="form-control form-control-sm item-price" placeholder="0" required></td>
                <td class="row-total small fw-bold pt-2">0.00</td>
                <td class="text-center">
                    <button type="button" class="btn btn-link text-danger p-0 remove-row" style="font-size:1.2rem; text-decoration:none;">×</button>
                </td>
            `;
            modalItemsBody.appendChild(tr);
        });
    }

    // Calculation Logic
    if (modalItemsBody) {
        modalItemsBody.addEventListener('input', function() {
            let grandTotal = 0;
            const rows = modalItemsBody.querySelectorAll('tr');
            rows.forEach(row => {
                const qty = parseFloat(row.querySelector('.item-qty').value) || 0;
                const price = parseFloat(row.querySelector('.item-price').value) || 0;
                const total = qty * price;
                row.querySelector('.row-total').textContent = total.toFixed(2);
                grandTotal += total;
            });
            grandTotalDisplay.textContent = grandTotal.toLocaleString(undefined, {minimumFractionDigits: 2});
        });

        // Delete Row Logic
        modalItemsBody.addEventListener('click', function(e) {
            if (e.target.classList.contains('remove-row')) {
                e.target.closest('tr').remove();
                modalItemsBody.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
    }

    // Save Invoice via API
    if (saveBtn) {
        saveBtn.addEventListener('click', function() {
            const invoiceId = document.getElementById('formInvoiceID').value;
            const customer = document.getElementById('customer').value;
            const invoiceDate = document.getElementById('invoiceDate').value;

            if (!invoiceId || !customer || !invoiceDate) {
                alert("Please fill all required fields");
                return;
            }

            // Collect invoice items
            const items = [];
            const rows = modalItemsBody.querySelectorAll('tr');
            rows.forEach(row => {
                const desc = row.querySelector('.item-desc').value;
                const qty = parseFloat(row.querySelector('.item-qty').value) || 0;
                const price = parseFloat(row.querySelector('.item-price').value) || 0;
                
                if (desc && qty > 0 && price > 0) {
                    items.push({
                        description: desc,
                        quantity: qty,
                        unit_price: price
                    });
                }
            });

            if (items.length === 0) {
                alert("Please add at least one item");
                return;
            }

            // Prepare form data
            const formData = new FormData();
            formData.append('invoice_number', invoiceId);
            formData.append('customer_name', customer);
            formData.append('invoice_date', invoiceDate);
            formData.append('items', JSON.stringify(items));

            // Send to backend
            fetch('/finance/api/invoices/create/', {
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
                    
                    // Close modal
                    const modalInstance = bootstrap.Modal.getInstance(document.getElementById('createInvoiceModal'));
                    if (modalInstance) modalInstance.hide();
                    
                    // Reset form
                    document.getElementById('invoiceForm').reset();
                    modalItemsBody.innerHTML = `
                        <tr>
                            <td><input type="text" class="form-control form-control-sm item-desc" required></td>
                            <td><input type="number" class="form-control form-control-sm item-qty" value="1" min="1"></td>
                            <td><input type="number" class="form-control form-control-sm item-price" placeholder="0" required></td>
                            <td class="row-total small fw-bold pt-2">0.00</td>
                            <td></td>
                        </tr>
                    `;
                    grandTotalDisplay.textContent = "0.00";
                    
                    // Reload page
                    window.location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while creating the invoice');
            });
        });
    }
});

// ==================== REPORT GENERATION ====================
function generateReport(reportType) {
    if (!confirm(`Generate ${reportType} report?`)) {
        return;
    }

    const formData = new FormData();
    formData.append('report_type', reportType);

    fetch('/finance/api/reports/generate/', {
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
            // Optionally download the report
            if (data.report_url) {
                window.open(data.report_url, '_blank');
            }
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while generating the report');
    });
}
