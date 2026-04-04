/* main.js – FIWARE Smart Store client-side JS */

/* ── Localization (i18n) ── */
// Superseded by Flask-Babel server-side templating

/* ── Dark/Light Theme ── */
document.addEventListener('DOMContentLoaded', function () {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.body.classList.add('dark-mode');
    }
    updateThemeIcon();
});

function updateThemeIcon() {
    const icon = document.getElementById('theme-icon');
    if (!icon) return;
    const dark = document.body.classList.contains('dark-mode');
    icon.className = dark ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
}

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const dark = document.body.classList.contains('dark-mode');
    localStorage.setItem('theme', dark ? 'dark' : 'light');
    updateThemeIcon();
    document.dispatchEvent(new Event('themeChanged'));
}

/* ── Socket.IO real-time notifications ── */
const socket = io();

socket.on('price_change', function (data) {
    // Update all price displays for this product
    const priceValue = data.new_price !== undefined ? data.new_price : data.price;
    const formatted = formatPrice(priceValue);
    
    document.querySelectorAll('[data-product-price][data-product-id="' + data.product_id + '"]').forEach(el => {
        el.textContent = formatted;
        // Visual feedback
        el.style.transition = 'background-color 0.5s ease';
        el.style.backgroundColor = 'rgba(255, 193, 7, 0.3)';
        setTimeout(() => el.style.backgroundColor = 'transparent', 2000);
    });
    
    // Show banner
    addNotification('price', '💲 ' + (data.name || data.product_id) + ': ' + formatted);
});

socket.on('low_stock', function (data) {
    addNotification('stock',
        '⚠️ Low stock: ' + data.product_id + ' → ' + data.shelfCount + ' units left',
        data.store_id
    );
});

function formatPrice(value) {
    if (value === null || value === undefined) return '–';
    return parseFloat(value).toFixed(2) + ' €';
}

function addNotification(type, message, storeId) {
    // Shift existing UI notifications down
    for (let i = 2; i > 0; i--) {
        let curr = document.getElementById('global-notif-' + i);
        let currIcon = document.getElementById('global-notif-icon-' + i);
        let currText = document.getElementById('global-notif-text-' + i);
        
        let prev = document.getElementById('global-notif-' + (i - 1));
        let prevIcon = document.getElementById('global-notif-icon-' + (i - 1));
        let prevText = document.getElementById('global-notif-text-' + (i - 1));
        
        if (curr && prev) {
            curr.className = prev.className;
            curr.style.display = prev.style.display;
            if (currIcon && prevIcon) currIcon.className = prevIcon.className;
            if (currText && prevText) currText.textContent = prevText.textContent;
        }
    }
    
    // Set notification 0
    let first = document.getElementById('global-notif-0');
    let firstIcon = document.getElementById('global-notif-icon-0');
    let firstText = document.getElementById('global-notif-text-0');
    
    if (first && firstIcon && firstText) {
        first.className = 'notification-item';
        if (type === 'price') {
            first.classList.add('price');
            firstIcon.className = 'fa-solid fa-tag';
        } else {
            firstIcon.className = 'fa-solid fa-triangle-exclamation';
        }
        first.style.display = 'flex'; // or whatever is appropriate, 'block' or 'flex'
        firstText.textContent = message;
        
        // Hide after some time to keep UI clean
        setTimeout(() => { first.style.display = 'none'; }, 10000);
    }
}

/* ── Dynamic shelf select (Product Detail) ── */
function loadShelvesForStore(storeId, productId, selectId) {
    const sel = document.getElementById(selectId);
    if (!sel) return;
    sel.innerHTML = '<option value="">Loading…</option>';
    fetch('/api/shelves-without-product?store_id=' + encodeURIComponent(storeId)
        + '&product_id=' + encodeURIComponent(productId))
        .then(r => r.json())
        .then(data => {
            sel.innerHTML = '';
            if (data.length === 0) {
                sel.innerHTML = '<option value="">No shelves available</option>';
                return;
            }
            data.forEach(sh => {
                const o = document.createElement('option');
                o.value = sh.id;
                o.textContent = sh.name;
                sel.appendChild(o);
            });
        })
        .catch(() => { sel.innerHTML = '<option value="">Error</option>'; });
}

/* ── Dynamic product select (Store Detail) ── */
function loadProductsForShelf(shelfId, selectId) {
    const sel = document.getElementById(selectId);
    if (!sel) return;
    sel.innerHTML = '<option value="">Loading…</option>';
    fetch('/api/products-not-in-shelf?shelf_id=' + encodeURIComponent(shelfId))
        .then(r => r.json())
        .then(data => {
            sel.innerHTML = '';
            if (data.length === 0) {
                sel.innerHTML = '<option value="">No products available</option>';
                return;
            }
            data.forEach(p => {
                const o = document.createElement('option');
                o.value = p.id;
                o.textContent = p.name;
                sel.appendChild(o);
            });
        })
        .catch(() => { sel.innerHTML = '<option value="">Error</option>'; });
}

/* ── Form Validation Helpers ── */
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('.validated-form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        // Show validation on blur or input after initial blur
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                validateInput(input);
            });
            input.addEventListener('input', () => {
                // If it already has an error or was blurred once, validate on input
                if (!input.validity.valid) {
                    validateInput(input);
                } else {
                    hideError(input);
                }
            });
        });

        // Validate all on submit
        form.addEventListener('submit', function(e) {
            let isValid = true;
            inputs.forEach(input => {
                if (!validateInput(input)) {
                    isValid = false;
                }
            });

            if (!isValid) {
                e.preventDefault();
                // Focus the first invalid input
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) firstInvalid.focus();
            }
        });
    });

    function validateInput(input) {
        if (!input.willValidate) return true;
        
        const errorSpan = input.parentElement.querySelector('.field-error');
        if (!errorSpan) return input.validity.valid;

        if (!input.validity.valid) {
            errorSpan.classList.remove('hidden');
            return false;
        } else {
            errorSpan.classList.add('hidden');
            return true;
        }
    }

    function hideError(input) {
        const errorSpan = input.parentElement.querySelector('.field-error');
        if (errorSpan) {
            errorSpan.classList.add('hidden');
        }
    }
});
