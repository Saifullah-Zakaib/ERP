// js/main.js

// Toggle Sidebar
document.getElementById('toggleSidebar').addEventListener('click', function() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
    
    const icon = this.querySelector('i');
    if (sidebar.classList.contains('collapsed')) {
        icon.classList.remove('bi-chevron-left');
        icon.classList.add('bi-chevron-right');
    } else {
        icon.classList.remove('bi-chevron-right');
        icon.classList.add('bi-chevron-left');
    }
});

// Mobile Menu Toggle
const mobileMenuBtn = document.getElementById('mobileMenuToggle');
if (mobileMenuBtn) {
    mobileMenuBtn.addEventListener('click', function() {
        document.getElementById('sidebar').classList.add('mobile-open');
        document.getElementById('mobileOverlay').classList.add('active');
    });
}

const mobileOverlay = document.getElementById('mobileOverlay');
if (mobileOverlay) {
    mobileOverlay.addEventListener('click', function() {
        document.getElementById('sidebar').classList.remove('mobile-open');
        this.classList.remove('active');
    });
}

// Update current time
function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    updateTime();
    setInterval(updateTime, 1000);
    
    // Initialize charts if chart elements exist
    initializeCharts();
});

// Initialize Charts
function initializeCharts() {
    const chartColors = {
        primary: '#1A73E8',
        secondary: '#00897B',
        success: '#0F9D58',
        warning: '#F9AB00',
        danger: '#D93025',
        info: '#1A73E8'
    };

    // Inventory Chart
    const inventoryCtx = document.getElementById('inventoryChart');
    if (inventoryCtx) {
        new Chart(inventoryCtx, {
            type: 'bar',
            data: {
                labels: ['BALL-001', 'BALL-002', 'SHOE-001', 'JERSEY-001', 'BAT-001'],
                datasets: [
                    {
                        label: 'Current Stock',
                        data: [450, 85, 320, 180, 65],
                        backgroundColor: chartColors.primary,
                        borderRadius: 6
                    },
                    {
                        label: 'Reorder Level',
                        data: [100, 100, 50, 50, 80],
                        backgroundColor: chartColors.warning,
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#E8EAED'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // Supplier Chart
    const supplierCtx = document.getElementById('supplierChart');
    if (supplierCtx) {
        new Chart(supplierCtx, {
            type: 'bar',
            data: {
                labels: ['Global Sports', 'Premium Fabrics', 'TechPack'],
                datasets: [{
                    label: 'On-Time Delivery %',
                    data: [95, 88, 92],
                    backgroundColor: chartColors.success,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: '#E8EAED'
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    // Forecast Chart
    const forecastCtx = document.getElementById('forecastChart');
    if (forecastCtx) {
        new Chart(forecastCtx, {
            type: 'line',
            data: {
                labels: ['Oct 2025', 'Nov 2025', 'Dec 2025', 'Jan 2026', 'Feb 2026'],
                datasets: [{
                    label: 'Predicted Demand',
                    data: [850, 920, 1045, 980, 1020],
                    borderColor: chartColors.primary,
                    backgroundColor: 'rgba(26, 115, 232, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: chartColors.primary
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: '#E8EAED'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // AI Demand Chart
    const aiDemandCtx = document.getElementById('aiDemandChart');
    if (aiDemandCtx) {
        new Chart(aiDemandCtx, {
            type: 'line',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
                datasets: [{
                    label: 'Predicted Demand',
                    data: [850, 920, 985, 1045, 1120, 1180],
                    borderColor: chartColors.primary,
                    backgroundColor: 'rgba(26, 115, 232, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: chartColors.primary
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: '#E8EAED'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
}

// Keyboard shortcut for search (Ctrl+K)
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('searchModal'));
        searchModal.show();
    }
});

// Form submission handlers
document.addEventListener('DOMContentLoaded', function() {
    // Create Production Order Form
    const createOrderForm = document.querySelector('#createOrderModal form');
    if (createOrderForm) {
        createOrderForm.addEventListener('submit', function(e) {
            e.preventDefault();
            alert('Production order created successfully!');
            const modal = bootstrap.Modal.getInstance(document.getElementById('createOrderModal'));
            modal.hide();
        });
    }

});

// Progress range display update(Production Dash)

 const newOrderForm = document.getElementById('newOrderForm');
        const floorContainer = document.getElementById('productionFloorContainer');
        const tableBody = document.getElementById('tableBody');
        const noOrdersMsg = document.getElementById('noOrdersMsg');

        // Handle Progress Slider Label
        document.getElementById('updateProgressRange').addEventListener('input', (e) => {
            document.getElementById('rangeText').innerText = e.target.value + "%";
        });

        // FORM SUBMIT: Add to Card and Table
        newOrderForm.onsubmit = function(e) {
            e.preventDefault();
            const id = document.getElementById('orderId').value;
            const customer = document.getElementById('customerName').value;
            const product = document.getElementById('productName').value;
            const qty = document.getElementById('qty').value;
            const date = document.getElementById('dueDate').value;

            // 1. Create Floor Card (Added Col-md-4 for better grid)
            const cardHtml = `
                <div class="col-md-4" id="card-container-${id}">
                    <div class="p-3 border rounded bg-light shadow-sm" id="floor-card-${id}">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="fw-bold mb-0">Order #${id}</h6>
                            <span class="badge bg-info text-dark" id="card-phase-${id}">PHASE: CUTTING</span>
                        </div>
                        <p class="small text-muted mb-2">${qty} x ${product}</p>
                        <div class="progress mb-3" style="height: 12px;">
                            <div id="card-bar-${id}" class="progress-bar progress-bar-striped progress-bar-animated bg-success" style="width: 0%;">0%</div>
                        </div>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">Machine: <span id="card-machine-${id}">Pending</span></small>
                            <button class="btn btn-sm btn-outline-primary" onclick="openUpdateModal('${id}')">
                                <i class="bi bi-pencil-square me-1"></i> Update
                            </button>
                        </div>
                    </div>
                </div>`;

            // 2. Create Table Row (Updated Button to "Update")
            const rowHtml = `
                <tr id="row-${id}">
                    <td><span class="fw-medium">${id}</span></td>
                    <td>${customer}</td>
                    <td>${product}</td>
                    <td>${date}</td>
                    <td>${qty}</td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <div class="progress" style="width: 80px; height: 8px;">
                                <div class="progress-bar" id="table-bar-${id}" style="width: 0%"></div>
                            </div>
                            <span class="small fw-medium" id="table-percent-${id}">0%</span>
                        </div>
                    </td>
                    <td><span class="badge bg-secondary" id="table-status-${id}">Pending</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary-custom" onclick="scrollToAndUpdate('${id}')">
                            <i class="bi bi-arrow-up-circle me-1"></i>Update
                        </button>
                    </td>
                </tr>`;

            if(noOrdersMsg) noOrdersMsg.remove();
            floorContainer.insertAdjacentHTML('afterbegin', cardHtml);
            tableBody.insertAdjacentHTML('afterbegin', rowHtml);

            bootstrap.Modal.getInstance(document.getElementById('createOrderModal')).hide();
            newOrderForm.reset();
        };

        // NEW FUNCTION: Scroll to card and open modal
        function scrollToAndUpdate(id) {
            const card = document.getElementById(`floor-card-${id}`);
            if (card) {
                // Scroll behavior
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Add highlight animation
                card.classList.add('highlight-card');
                setTimeout(() => card.classList.remove('highlight-card'), 3000);

                // Open Modal after a small delay
                setTimeout(() => openUpdateModal(id), 500);
            }
        }

        // OPEN UPDATE MODAL
        function openUpdateModal(id) {
            document.getElementById('targetOrderId').value = id;
            document.getElementById('displayUpdateId').innerText = id;
            
            // Sync current values back to modal
            const currentProgress = document.getElementById(`table-percent-${id}`).innerText.replace('%', '');
            document.getElementById('updateProgressRange').value = currentProgress;
            document.getElementById('rangeText').innerText = currentProgress + "%";

            new bootstrap.Modal(document.getElementById('prodUpdateModal')).show();
        }

        // SAVE STATUS UPDATES
        function saveProductionStatus() {
            const id = document.getElementById('targetOrderId').value;
            const progress = document.getElementById('updateProgressRange').value;
            const phase = document.getElementById('updatePhaseSelect').value;
            const machine = document.getElementById('updateMachineInput').value || 'N/A';

            // Update Card
            document.getElementById(`card-bar-${id}`).style.width = progress + "%";
            document.getElementById(`card-bar-${id}`).innerText = progress + "%";
            document.getElementById(`card-phase-${id}`).innerText = "PHASE: " + phase.toUpperCase();
            document.getElementById(`card-machine-${id}`).innerText = machine;

            // Update Table
            document.getElementById(`table-bar-${id}`).style.width = progress + "%";
            document.getElementById(`table-percent-${id}`).innerText = progress + "%";
            
            const statusBadge = document.getElementById(`table-status-${id}`);
            statusBadge.innerText = (progress == 100) ? "Completed" : "In Progress";
            statusBadge.className = (progress == 100) ? "badge bg-success" : "badge bg-info";

            bootstrap.Modal.getInstance(document.getElementById('prodUpdateModal')).hide();
        }


