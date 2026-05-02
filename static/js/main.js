// 上海局铁路客票系统 - 公共脚本

// 自动关闭提示消息
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// 站点自动补全（简易实现）
function setupStationAutocomplete(inputElement, callback) {
    if (!inputElement) return;
    
    let timeout = null;
    
    inputElement.addEventListener('input', function() {
        const query = this.value.trim();
        if (query.length < 2) return;
        
        clearTimeout(timeout);
        timeout = setTimeout(function() {
            fetch('/api/stations?q=' + encodeURIComponent(query))
                .then(function(response) {
                    return response.json();
                })
                .then(function(data) {
                    callback(data);
                })
                .catch(function(error) {
                    console.error('获取站点失败:', error);
                });
        }, 300);
    });
}

// 表单验证增强
function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(function(input) {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        }
    });
    
    return isValid;
}

// 确认对话框
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

// 格式化金额
function formatCurrency(amount) {
    return '¥' + parseFloat(amount).toFixed(2);
}

// 复制到剪贴板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        alert('已复制到剪贴板');
    }).catch(function(err) {
        console.error('复制失败:', err);
    });
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = function() {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 导出公共函数
window.railwayApp = {
    setupAutocomplete: setupStationAutocomplete,
    validateForm: validateForm,
    confirmAction: confirmAction,
    formatDate: formatDate,
    formatCurrency: formatCurrency,
    copyToClipboard: copyToClipboard,
    debounce: debounce
};
