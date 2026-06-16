// Production Module - Dynamic JavaScript with API Integration

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

let csrftoken = null;
let currentOrderId = null;

// ==================== CREATE PRODUCTION ORDER ====================
document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token when page loads
    csrftoken = getCookie('csrftoken');
    console.log('🔐 CSRF Token:', csrftoken ? 'Found ✅' : 'NOT FOUND ❌');
    
    if (!csrftoken) {
        console.error('❌ CSRF token not found! Forms will not work.');
        return;
    }
    
    console.log('✅ Production dynamic JS loaded');
    
    const newOrderForm = document.getElementById('newOrderForm');
    
    if (newOrderForm) {
        console.log('✅ Form element found');
        
        newOrderForm.addEventListener('submit', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('📝 Form submitted - prevented default');
            
            // Get form elements using querySelector to be absolutely sure
            const form = document.getElementById('newOrderForm');
            const orderIdInput = form.querySelector('#orderId');
            const customerNameInput = form.querySelector('#customerName');
            const productNameInput = form.querySelector('#productName');
            const qtyInput = form.querySelector('#qty');
            const dueDateInput = form.querySelector('#dueDate');
            
            console.log('Input elements:', {
                orderIdInput: orderIdInput,
                customerNameInput: customerNameInput,
                productNameInput: productNameInput,
                qtyInput: qtyInput,
                dueDateInput: dueDateInput
            });
            
            // Get values
            const orderId = orderIdInput ? orderIdInput.value : '';
            const customerName = customerNameInput ? customerNameInput.value : '';
            const productName = productNameInput ? productNameInput.value : '';
            const qty = qtyInput ? qtyInput.value : '';
            const dueDate = dueDateInput ? dueDateInput.value : '';
            
            console.log('📋 Raw values:', { orderId, customerName, productName, qty, dueDate });
            
            // Trim strings
            const orderIdTrimmed = orderId.trim();
            const customerNameTrimmed = customerName.trim();
            const productNameTrimmed = productName.trim();
            
            console.log('📋 Trimmed values:', { 
                orderId: orderIdTrimmed, 
                customerName: customerNameTrimmed, 
                productName: productNameTrimmed, 
                qty, 
                dueDate 
            });
            
            // Validate
            if (!orderIdTrimmed) {
                alert('Please enter Order ID');
                console.error('❌ Missing: Order ID');
                orderIdInput.focus();
                return;
            }
            if (!customerNameTrimmed) {
                alert('Please enter Customer Name');
                console.error('❌ Missing: Customer Name');
                customerNameInput.focus();
                return;
            }
            if (!productNameTrimmed) {
                alert('Please enter Product Name');
                console.error('❌ Missing: Product Name');
                productNameInput.focus();
                return;
            }
            if (!qty || parseInt(qty) <= 0) {
                alert('Please enter valid Quantity');
                console.error('❌ Missing or invalid: Quantity');
                qtyInput.focus();
                return;
            }
            if (!dueDate) {
                alert('Please select Due Date');
                console.error('❌ Missing: Due Date');
                dueDateInput.focus();
                return;
            }
            
            // Create FormData
            const formData = new FormData();
            formData.append('order_id', orderIdTrimmed);
            formData.append('customer_name', customerNameTrimmed);
            formData.append('product_name', productNameTrimmed);
            formData.append('quantity', qty);
            formData.append('due_date', dueDate);
            
            console.log('🚀 Sending request to /production/api/orders/create/');
            console.log('📦 FormData contents:', {
                order_id: formData.get('order_id'),
                customer_name: formData.get('customer_name'),
                product_name: formData.get('product_name'),
                quantity: formData.get('quantity'),
                due_date: formData.get('due_date')
            });
            
            fetch('/production/api/orders/create/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken
                },
                body: formData
            })
            .then(response => {
                console.log('📡 Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('📦 Response data:', data);
                if (data.success) {
                    alert('✅ ' + data.message);
                    
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('createOrderModal'));
                    if (modal) modal.hide();
                    
                    // Reset form
                    newOrderForm.reset();
                    
                    // Reload page to show new order
                    console.log('🔄 Reloading page...');
                    window.location.reload();
                } else {
                    alert('❌ Error: ' + data.message);
                    console.error('❌ Server error:', data.message);
                }
            })
            .catch(error => {
                console.error('❌ Fetch Error:', error);
                alert('❌ Failed to create order: ' + error.message + '\n\nCheck browser console for details.');
            });
        });
    } else {
        console.error('❌ Form element not found!');
    }
});

// ==================== UPDATE PRODUCTION STATUS ====================
function openUpdateModal(orderId, orderNumber, progress, phase, machine) {
    currentOrderId = orderId;
    console.log('📝 Opening update modal for:', orderNumber);
    
    // Set values
    document.getElementById('displayUpdateId').innerText = orderNumber;
    document.getElementById('targetOrderId').value = orderId;
    document.getElementById('updateProgressRange').value = progress;
    document.getElementById('rangeText').innerText = progress + '%';
    document.getElementById('updatePhaseSelect').value = phase;
    document.getElementById('updateMachineInput').value = machine;
    
    // Open modal
    const modal = new bootstrap.Modal(document.getElementById('prodUpdateModal'));
    modal.show();
}

// Update progress range display
document.addEventListener('DOMContentLoaded', function() {
    const progressRange = document.getElementById('updateProgressRange');
    const rangeText = document.getElementById('rangeText');
    
    if (progressRange) {
        progressRange.addEventListener('input', function() {
            rangeText.innerText = this.value + '%';
        });
    }
});

// Save production status
function saveProductionStatus() {
    if (!currentOrderId) {
        alert('❌ Order ID not found');
        console.error('❌ currentOrderId is null');
        return;
    }
    
    const progress = document.getElementById('updateProgressRange').value;
    const phase = document.getElementById('updatePhaseSelect').value;
    const machine = document.getElementById('updateMachineInput').value;
    
    console.log('💾 Updating order:', currentOrderId, { progress, phase, machine });
    
    const formData = new FormData();
    formData.append('progress', progress);
    formData.append('phase', phase);
    formData.append('machine', machine);
    
    fetch(`/production/api/orders/${currentOrderId}/update/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        },
        body: formData
    })
    .then(response => {
        console.log('📡 Update response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('📦 Update response data:', data);
        if (data.success) {
            alert('✅ ' + data.message);
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('prodUpdateModal'));
            if (modal) modal.hide();
            
            // Reload page
            console.log('🔄 Reloading page...');
            window.location.reload();
        } else {
            alert('❌ Error: ' + data.message);
            console.error('❌ Server error:', data.message);
        }
    })
    .catch(error => {
        console.error('❌ Update Error:', error);
        alert('❌ Failed to update order: ' + error.message + '\n\nCheck browser console for details.');
    });
}
