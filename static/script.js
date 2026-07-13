// Common JavaScript functions for the Cancer Detection System

// Utility function to show loading state
function showLoading(element) {
    element.disabled = true;
    element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
}

// Utility function to hide loading state
function hideLoading(element, originalText) {
    element.disabled = false;
    element.innerHTML = originalText;
}

// Format percentage display
function formatPercentage(value) {
    return Math.round(value) + '%';
}

// Validate email format
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Validate phone number
function isValidPhone(phone) {
    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
    return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
}

// Calculate BMI
function calculateBMI(weight, height) {
    return (weight / ((height / 100) ** 2)).toFixed(1);
}

// Get BMI category
function getBMICategory(bmi) {
    if (bmi < 18.5) return 'Underweight';
    if (bmi < 25) return 'Normal weight';
    if (bmi < 30) return 'Overweight';
    return 'Obese';
}

// Format date for display
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Get risk level text
function getRiskLevel(score) {
    if (score > 50) return 'High Risk';
    if (score > 30) return 'Moderate Risk';
    return 'Low Risk';
}

// Get risk color
function getRiskColor(score) {
    if (score > 50) return '#e74c3c';
    if (score > 30) return '#f39c12';
    return '#4fc3a1';
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Local storage helper functions
const storage = {
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error saving to localStorage:', error);
            return false;
        }
    },
    
    get: (key) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return null;
        }
    },
    
    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    }
};

// API call helper
async function apiCall(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const config = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(endpoint, config);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'API request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API call error:', error);
        throw error;
    }
}

// Check if user is authenticated
function isAuthenticated() {
    return !!storage.get('user_token');
}

// Redirect if not authenticated
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/auth';
        return false;
    }
    return true;
}

// Initialize tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
    
    function showTooltip(e) {
        const tooltipText = e.target.getAttribute('data-tooltip');
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = tooltipText;
        
        document.body.appendChild(tooltip);
        
        const rect = e.target.getBoundingClientRect();
        tooltip.style.left = rect.left + 'px';
        tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
    }
    
    function hideTooltip() {
        const tooltip = document.querySelector('.tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }
}

// Add CSS for tooltips
const tooltipStyles = `
.tooltip {
    position: fixed;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 12px;
    z-index: 1000;
    pointer-events: none;
}
`;

// Inject tooltip styles
if (!document.querySelector('#tooltip-styles')) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'tooltip-styles';
    styleSheet.textContent = tooltipStyles;
    document.head.appendChild(styleSheet);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
    
    // Add loading states to all buttons with loading class
    const loadingButtons = document.querySelectorAll('.btn-loading');
    loadingButtons.forEach(button => {
        button.addEventListener('click', function() {
            const originalText = this.innerHTML;
            showLoading(this);
            
            // Restore after 3 seconds (for demo)
            setTimeout(() => {
                hideLoading(this, originalText);
            }, 3000);
        });
    });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showLoading,
        hideLoading,
        formatPercentage,
        isValidEmail,
        isValidPhone,
        calculateBMI,
        getBMICategory,
        formatDate,
        getRiskLevel,
        getRiskColor,
        debounce,
        storage,
        apiCall,
        isAuthenticated,
        requireAuth
    };
}