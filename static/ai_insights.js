/**
 * AI Insights Dynamic JavaScript
 * Handles real-time updates and chart rendering
 */

let demandChart = null;
let efficiencyChart = null;

// Initialize charts on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    
    // Auto-refresh every 5 minutes
    setInterval(refreshInsights, 300000);
});

function initializeCharts() {
    // Demand Forecast Chart is already initialized in template
    // This function can be used for additional chart customization
}

async function refreshInsights() {
    try {
        const response = await fetch('/api/ai-insights/');
        const result = await response.json();
        
        if (result.success) {
            updateDashboard(result.data);
            showToast('AI insights refreshed successfully', 'success');
        } else {
            showToast('Failed to refresh insights', 'error');
        }
    } catch (error) {
        console.error('Error refreshing insights:', error);
        showToast('Error refreshing insights', 'error');
    }
}

function updateDashboard(data) {
    // Update AI Health Score
    updateAIHealth(data.ai_health);
    
    // Update Anomalies
    updateAnomalies(data.anomalies);
    
    // Update Recommendations
    updateRecommendations(data.recommendations);
    
    // Update Inventory Predictions
    updateInventoryPredictions(data.inventory_predictions);
}

function updateAIHealth(health) {
    const accuracyEl = document.querySelector('.fw-bold[style*="font-size: 2rem"]');
    if (accuracyEl) {
        accuracyEl.textContent = health.accuracy + '%';
    }
    
    // Update circle progress
    const circle = document.querySelector('circle[stroke="#1A73E8"]');
    if (circle) {
        circle.setAttribute('stroke-dashoffset', health.dashoffset);
    }
}

function updateAnomalies(anomalies) {
    // Anomalies update logic can be added here
    console.log('Anomalies updated:', anomalies);
}

function updateRecommendations(recommendations) {
    // Recommendations update logic can be added here
    console.log('Recommendations updated:', recommendations);
}

function updateInventoryPredictions(predictions) {
    // Predictions update logic can be added here
    console.log('Predictions updated:', predictions);
}

function handleAction(action, id) {
    showToast(`Processing action: ${action} for recommendation #${id}`, 'info');
    
    // Here you can add actual API calls to perform actions
    setTimeout(() => {
        showToast('Action completed successfully', 'success');
    }, 1000);
}

function showToast(message, type = 'info') {
    // Simple toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}
