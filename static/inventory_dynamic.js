// Inventory Module - Dynamic JavaScript with API Integration

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

// Global variables for current order being processed
let currentOrderId = null;
let currentOrderNumber = null;

// ==================== ADD INVENTORY ====================
document.addEventListener('DOMContentLoaded', function() {
    const saveInventoryBtn = document.getElementById('saveInventoryBtn');
    
    if (saveInventoryBtn) {
        saveInventoryBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const sku = document.getElementById('newSku').value.trim();
            const name = document.getElementById('newName').value.trim();
            const quantity = document.getElementById('newQuantity').value;
            const reorderLevel = document.getElementById('newReorderLevel').value;
            const category = document.getElementById('newCategory').value;
            
            if (!sku || !name || !category) {
                alert('Please fill all required fields');
                return;
            }
            
            const formData = new FormData();
            formData.append('sku', sku);
            formData.append('name', name);
            formData.append('quantity', quantity);
            formData.append('reorder_level', reorderLevel);
            formData.append('category', category);
            
            fetch('/inventory/api/items/add/', {
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
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addInventoryModal'));
                    if (modal) modal.hide();
                    
                    // Reset form
                    document.getElementById('addInventoryForm').reset();
                    
                    // Reload page
                    window.location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while adding the inventory item');
            });
        });
    }
});

// ==================== ADD ORDER ====================
document.addEventListener('DOMContentLoaded', function() {
    const orderForm = document.getElementById('orderForm');
    const saveOrderBtn = document.getElementById('saveOrderBtn');
    
    if (saveOrderBtn) {
        saveOrderBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const orderId = document.getElementById('orderId').value;
            const custName = document.getElementById('custName').value;
            const prodName = document.getElementById('prodName').value;
            const qty = document.getElementById('qty').value;
            
            if (!orderId || !custName || !prodName || !qty) {
                alert('Please fill all fields');
                return;
            }
            
            const formData = new FormData();
            formData.append('order_number', orderId);
            formData.append('customer_name', custName);
            formData.append('product_name', prodName);
            formData.append('quantity', qty);
            
            fetch('/inventory/api/orders/add/', {
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
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addOrderModal'));
                    if (modal) modal.hide();
                    
                    // Reset form
                    orderForm.reset();
                    
                    // Reload page
                    window.location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while adding the order');
            });
        });
    }
});

// ==================== CHECK ORDER STATUS ====================
function processOrder(orderId, orderNumber, productName, quantity) {
    currentOrderId = orderId;
    currentOrderNumber = orderNumber;
    
    // Open modal
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
    
    // Update display
    document.getElementById('displayOrderID').innerText = orderNumber;
    
    // Show loader and hide result area
    const loader = document.getElementById('loader').querySelector('.spinner-border');
    if (loader) loader.style.display = 'block';
    
    const resultArea = document.getElementById('resultArea');
    resultArea.style.display = 'none';
    
    // Disable all buttons initially
    disableAllButtons();
    
    // Check status via API
    const formData = new FormData();
    formData.append('order_number', orderNumber);
    formData.append('product_name', productName);
    formData.append('quantity', quantity);
    
    fetch('/inventory/api/orders/check-status/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Hide loader and show result
        if (loader) loader.style.display = 'none';
        resultArea.style.display = 'block';
        
        const box = document.getElementById('statusBox');
        const title = document.getElementById('statusTitle');
        const desc = document.getElementById('statusDesc');
        
        console.log('API Response:', data);
        console.log('Action:', data.action);
        
        if (data.action === 'ship') {
            // Stock available - ONLY enable ship button
            box.style.background = "#f0fdf4";
            box.style.borderColor = "#22c55e";
            title.innerText = "✓ READY TO SHIP";
            title.style.color = "#15803d";
            desc.innerText = data.message;
            
            enableButton('shipBtn');
        } else if (data.action === 'production') {
            // Check if already in production
            checkProductionStatus(productName, quantity, data);
        } else {
            // Out of stock - ONLY enable request materials button
            box.style.background = "#fef2f2";
            box.style.borderColor = "#ef4444";
            title.innerText = "✗ STOCK MISSING";
            title.style.color = "#b91c1c";
            desc.innerText = data.message;
            document.getElementById('suppNote').value = `Urgent: Material request for ${quantity} units of ${productName}.`;
            
            enableButton('suppBtn');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (loader) loader.style.display = 'none';
        alert('An error occurred while checking order status');
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    });
}

// Check if product is already in production
function checkProductionStatus(productName, quantity, stockData) {
    console.log('Checking production status for:', productName, quantity);
    
    fetch('/inventory/api/check-production-status/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `product_name=${encodeURIComponent(productName)}&quantity=${quantity}`
    })
    .then(response => response.json())
    .then(data => {
        console.log('Production status response:', data);
        
        const box = document.getElementById('statusBox');
        const title = document.getElementById('statusTitle');
        const desc = document.getElementById('statusDesc');
        
        if (data.in_production) {
            // Already in production - show info only, NO buttons enabled
            box.style.background = "#eff6ff";
            box.style.borderColor = "#3b82f6";
            title.innerText = "⏳ IN PRODUCTION";
            title.style.color = "#1e40af";
            desc.innerText = `${data.message} Production Order: ${data.production_order_number}. Expected completion: ${data.expected_completion || 'Soon'}`;
            console.log('Product in production - all buttons disabled');
            // All buttons remain disabled
        } else if (data.raw_materials_available) {
            // Raw materials available - ONLY enable production button
            box.style.background = "#fffbeb";
            box.style.borderColor = "#f59e0b";
            title.innerText = "⚙ PRODUCTION NEEDED";
            title.style.color = "#b45309";
            desc.innerText = stockData.message + ' Raw materials are available.';
            document.getElementById('prodNote').value = `Order ${currentOrderNumber}: Produce ${quantity} units of ${productName}.`;
            
            enableButton('prodBtn');
        } else {
            // No raw materials - ONLY enable request materials button
            box.style.background = "#fef2f2";
            box.style.borderColor = "#ef4444";
            title.innerText = "✗ RAW MATERIALS NEEDED";
            title.style.color = "#b91c1c";
            desc.innerText = 'Raw materials not available. Procurement required before production.';
            document.getElementById('suppNote').value = `Urgent: Raw material request for producing ${quantity} units of ${productName}.`;
            
            enableButton('suppBtn');
        }
    })
    .catch(error => {
        console.error('Error checking production status:', error);
        // Fallback to production view
        const box = document.getElementById('statusBox');
        const title = document.getElementById('statusTitle');
        const desc = document.getElementById('statusDesc');
        box.style.background = "#fffbeb";
        box.style.borderColor = "#f59e0b";
        title.innerText = "⚙ PRODUCTION NEEDED";
        title.style.color = "#b45309";
        desc.innerText = stockData.message;
        document.getElementById('prodNote').value = `Order ${currentOrderNumber}: Produce ${quantity} units of ${productName}.`;
        
        enableButton('prodBtn');
    });
}

// ==================== APPROVE & SHIP ====================
function approveAndShip() {
    if (!currentOrderId) {
        alert('Order ID not found');
        return;
    }
    
    // Disable button to prevent double-click
    const btn = document.getElementById('shipBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
    
    fetch(`/inventory/api/orders/${currentOrderId}/approve/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            const box = document.getElementById('statusBox');
            box.style.background = "#f0fdf4";
            box.style.borderColor = "#22c55e";
            document.getElementById('statusTitle').innerText = "✓ ORDER APPROVED & SHIPPED";
            document.getElementById('statusTitle').style.color = "#15803d";
            document.getElementById('statusDesc').innerText = data.message;
            
            // Hide all buttons
            disableAllButtons();
            btn.style.display = 'none';
            
            // Show success alert
            alert('✓ Success: Order has been approved and shipped!');
            
            // Close modal and reload after 1 second
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
                window.location.reload();
            }, 1000);
        } else {
            alert('Error: ' + data.message);
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-check-circle me-2"></i>APPROVE & SHIP ORDER';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-check-circle me-2"></i>APPROVE & SHIP ORDER';
    });
}

// ==================== SEND TO PRODUCTION ====================
function sendToProduction() {
    if (!currentOrderId) {
        alert('Order ID not found');
        return;
    }
    
    const instructions = document.getElementById('prodNote').value;
    
    // Disable button
    const btn = document.getElementById('prodBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
    
    const formData = new FormData();
    formData.append('instructions', instructions);
    
    fetch(`/inventory/api/orders/${currentOrderId}/send-to-production/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            const box = document.getElementById('statusBox');
            box.style.background = "#f0fdf4";
            box.style.borderColor = "#22c55e";
            document.getElementById('statusTitle').innerText = "✓ SENT TO PRODUCTION";
            document.getElementById('statusTitle').style.color = "#15803d";
            document.getElementById('statusDesc').innerText = `Production Order ${data.production_order_number} has been created successfully!`;
            
            // Hide all buttons
            disableAllButtons();
            btn.style.display = 'none';
            
            // Show success alert
            alert(`✓ Success: Order sent to production!\nProduction Order: ${data.production_order_number}`);
            
            // Close modal and reload after 1 second
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
                window.location.reload();
            }, 1000);
        } else {
            alert('Error: ' + data.message);
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-gear me-2"></i>SEND TO PRODUCTION';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-gear me-2"></i>SEND TO PRODUCTION';
    });
}

// ==================== REQUEST MATERIALS ====================
function requestMaterials() {
    if (!currentOrderId) {
        alert('Order ID not found');
        return;
    }
    
    const notes = document.getElementById('suppNote').value;
    
    // Disable button
    const btn = document.getElementById('suppBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
    
    const formData = new FormData();
    formData.append('notes', notes);
    
    fetch(`/inventory/api/orders/${currentOrderId}/request-materials/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            const box = document.getElementById('statusBox');
            box.style.background = "#f0fdf4";
            box.style.borderColor = "#22c55e";
            document.getElementById('statusTitle').innerText = "✓ MATERIAL REQUEST SENT";
            document.getElementById('statusTitle').style.color = "#15803d";
            document.getElementById('statusDesc').innerText = `Material Request ${data.material_request_number || ''} has been sent to procurement team! Inventory will auto-update when materials are received.`;
            
            // Hide all buttons
            disableAllButtons();
            btn.style.display = 'none';
            
            // Show success alert
            alert(`✓ Success: Material request sent!\nRequest Number: ${data.material_request_number || 'Created'}\n\nInventory will automatically update when supplier delivers the materials.`);
            
            // Close modal and reload after 1 second
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
                window.location.reload();
            }, 1000);
        } else {
            alert('Error: ' + data.message);
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-truck me-2"></i>REQUEST RAW MATERIALS';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-truck me-2"></i>REQUEST RAW MATERIALS';
    });
}

// ==================== EDIT ITEM ====================
let currentItemId = null;

function editItem(itemId, sku, name, quantity, reorderLevel, unitPrice, location, category, description) {
    currentItemId = itemId;
    
    // Fill form
    document.getElementById('editSku').value = sku;
    document.getElementById('editName').value = name;
    document.getElementById('editQuantity').value = quantity;
    document.getElementById('editReorderLevel').value = reorderLevel;
    document.getElementById('editUnitPrice').value = unitPrice;
    document.getElementById('editLocation').value = location;
    document.getElementById('editCategory').value = category;
    document.getElementById('editDescription').value = description;
    
    // Open modal
    const modal = new bootstrap.Modal(document.getElementById('editItemModal'));
    modal.show();
}

document.addEventListener('DOMContentLoaded', function() {
    const saveEditBtn = document.getElementById('saveEditBtn');
    
    if (saveEditBtn) {
        saveEditBtn.addEventListener('click', function() {
            if (!currentItemId) {
                alert('Item ID not found');
                return;
            }
            
            const formData = new FormData();
            formData.append('name', document.getElementById('editName').value);
            formData.append('quantity', document.getElementById('editQuantity').value);
            formData.append('reorder_level', document.getElementById('editReorderLevel').value);
            formData.append('unit_price', document.getElementById('editUnitPrice').value);
            formData.append('location', document.getElementById('editLocation').value);
            formData.append('category', document.getElementById('editCategory').value);
            formData.append('description', document.getElementById('editDescription').value);
            
            fetch(`/inventory/api/items/${currentItemId}/update/`, {
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
                    const modal = bootstrap.Modal.getInstance(document.getElementById('editItemModal'));
                    if (modal) modal.hide();
                    
                    // Reload page
                    window.location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while updating the item');
            });
        });
    }
});


// ==================== HELPER FUNCTIONS ====================
function disableAllButtons() {
    // Disable all action buttons and make them visually disabled
    const buttons = ['shipBtn', 'prodBtn', 'suppBtn'];
    buttons.forEach(btnId => {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
        }
    });
}

function enableButton(btnId) {
    // Enable only the specified button
    const btn = document.getElementById(btnId);
    if (btn) {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.cursor = 'pointer';
        console.log(`Button ${btnId} enabled`);
    }
}
