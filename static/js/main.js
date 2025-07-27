// VendorConnect Main JavaScript File

// Global variables
let currentUser = null;
let cart = [];
let voiceRecognition = null;

// Initialize voice recognition
function initializeVoiceRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        voiceRecognition = new SpeechRecognition();
        voiceRecognition.continuous = false;
        voiceRecognition.interimResults = false;
        voiceRecognition.lang = 'hi-IN'; // Default to Hindi
    }
}

// Language translations
const translations = {
    en: {
        'search-placeholder': 'Search products...',
        'voice-search-placeholder': 'Search products by voice...',
        'add-to-cart': 'Add to Cart',
        'view-details': 'Details',
        'join-order': 'Join Order',
        'create-order': 'Create Group Order',
        'contact-supplier': 'Contact',
        'view-products': 'View Products',
        'loading': 'Loading...',
        'error': 'An error occurred. Please try again.',
        'success': 'Operation completed successfully.',
        'no-products': 'No products found.',
        'no-orders': 'No orders found.',
        'no-alerts': 'No alerts found.'
    },
    hi: {
        'search-placeholder': 'उत्पाद खोजें...',
        'voice-search-placeholder': 'आवाज से उत्पाद खोजें...',
        'add-to-cart': 'कार्ट में जोड़ें',
        'view-details': 'विवरण',
        'join-order': 'ऑर्डर में शामिल हों',
        'create-order': 'समूह ऑर्डर बनाएं',
        'contact-supplier': 'संपर्क करें',
        'view-products': 'उत्पाद देखें',
        'loading': 'लोड हो रहा है...',
        'error': 'एक त्रुटि हुई। कृपया पुनः प्रयास करें।',
        'success': 'कार्य सफलतापूर्वक पूरा हुआ।',
        'no-products': 'कोई उत्पाद नहीं मिला।',
        'no-orders': 'कोई ऑर्डर नहीं मिला।',
        'no-alerts': 'कोई अलर्ट नहीं मिला।'
    },
    bn: {
        'search-placeholder': 'পণ্য অনুসন্ধান করুন...',
        'voice-search-placeholder': 'কণ্ঠস্বর দিয়ে পণ্য অনুসন্ধান করুন...',
        'add-to-cart': 'কার্টে যোগ করুন',
        'view-details': 'বিস্তারিত',
        'join-order': 'অর্ডারে যোগ দিন',
        'create-order': 'গ্রুপ অর্ডার তৈরি করুন',
        'contact-supplier': 'যোগাযোগ করুন',
        'view-products': 'পণ্য দেখুন',
        'loading': 'লোড হচ্ছে...',
        'error': 'একটি ত্রুটি ঘটেছে। অনুগ্রহ করে আবার চেষ্টা করুন।',
        'success': 'অপারেশন সফলভাবে সম্পন্ন হয়েছে।',
        'no-products': 'কোন পণ্য পাওয়া যায়নি।',
        'no-orders': 'কোন অর্ডার পাওয়া যায়নি।',
        'no-alerts': 'কোন অ্যালার্ট পাওয়া যায়নি।'
    },
    ta: {
        'search-placeholder': 'பொருட்களைத் தேடுங்கள்...',
        'voice-search-placeholder': 'குரலால் பொருட்களைத் தேடுங்கள்...',
        'add-to-cart': 'கார்ட்டில் சேர்க்கவும்',
        'view-details': 'விவரங்கள்',
        'join-order': 'ஆர்டரில் சேரவும்',
        'create-order': 'குழு ஆர்டரை உருவாக்கவும்',
        'contact-supplier': 'தொடர்பு கொள்ளவும்',
        'view-products': 'பொருட்களைக் காண்க',
        'loading': 'ஏற்றுகிறது...',
        'error': 'ஒரு பிழை ஏற்பட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.',
        'success': 'செயல்பாடு வெற்றிகரமாக முடிக்கப்பட்டது.',
        'no-products': 'பொருட்கள் எதுவும் கிடைக்கவில்லை.',
        'no-orders': 'ஆர்டர்கள் எதுவும் கிடைக்கவில்லை.',
        'no-alerts': 'எச்சரிக்கைகள் எதுவும் கிடைக்கவில்லை.'
    }
};

// Change language
function changeLanguage(lang) {
    const elements = translations[lang];
    for (const [key, value] of Object.entries(elements)) {
        const element = document.getElementById(key);
        if (element) {
            element.textContent = value;
        }
    }
    
    // Update placeholders
    const searchInputs = document.querySelectorAll('[data-translate]');
    searchInputs.forEach(input => {
        const key = input.getAttribute('data-translate');
        if (translations[lang][key]) {
            input.placeholder = translations[lang][key];
        }
    });
}

// Voice search functionality
function startVoiceSearch() {
    if (!voiceRecognition) {
        alert('Voice recognition not supported in this browser.');
        return;
    }
    
    const voiceBtn = document.getElementById('voice-btn');
    const input = document.getElementById('voice-search-input');
    
    voiceBtn.classList.add('recording');
    input.placeholder = 'Listening...';
    
    voiceRecognition.onstart = () => {
        console.log('Voice recognition started');
    };
    
    voiceRecognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        input.value = transcript;
        voiceBtn.classList.remove('recording');
        input.placeholder = translations[currentLanguage || 'en']['voice-search-placeholder'];
        
        // Filter products based on voice input
        filterProductsByVoice(transcript);
    };
    
    voiceRecognition.onerror = (event) => {
        console.error('Voice recognition error:', event.error);
        voiceBtn.classList.remove('recording');
        input.placeholder = translations[currentLanguage || 'en']['voice-search-placeholder'];
    };
    
    voiceRecognition.start();
}

// Filter products by voice input
function filterProductsByVoice(query) {
    const products = window.products || [];
    const filteredProducts = products.filter(product => 
        product.name.toLowerCase().includes(query.toLowerCase()) ||
        product.category.toLowerCase().includes(query.toLowerCase()) ||
        product.supplier_name.toLowerCase().includes(query.toLowerCase())
    );
    
    displayProducts(filteredProducts);
}

// Display products
function displayProducts(products) {
    const container = document.getElementById('products-grid');
    if (!container) return;
    
    if (products.length === 0) {
        container.innerHTML = `<div class="no-data">${translations[currentLanguage || 'en']['no-products']}</div>`;
        return;
    }
    
    container.innerHTML = products.map(product => `
        <div class="product-card">
            <div class="product-name">${product.name}</div>
            <div class="product-price">₹${product.current_price}/${product.unit}</div>
            <div class="product-supplier">${product.supplier_name} (${product.supplier_location})</div>
            <div class="product-actions">
                <button class="btn btn-primary" onclick="addToCart('${product.id}')">${translations[currentLanguage || 'en']['add-to-cart']}</button>
                <button class="btn btn-secondary" onclick="viewDetails('${product.id}')">${translations[currentLanguage || 'en']['view-details']}</button>
            </div>
        </div>
    `).join('');
}

// Add to cart
function addToCart(productId) {
    const product = window.products?.find(p => p.id == productId);
    if (product) {
        cart.push(product);
        updateCartUI();
        showNotification('Product added to cart!', 'success');
    }
}

// Update cart UI
function updateCartUI() {
    const cartCount = document.getElementById('cart-count');
    if (cartCount) {
        cartCount.textContent = cart.length;
        cartCount.style.display = cart.length > 0 ? 'block' : 'none';
    }
}

// View product details
function viewDetails(productId) {
    const product = window.products?.find(p => p.id == productId);
    if (product) {
        showProductModal(product);
    }
}

// Show product modal
function showProductModal(product) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close">&times;</span>
            <h2>${product.name}</h2>
            <div class="product-details">
                <p><strong>Price:</strong> ₹${product.current_price}/${product.unit}</p>
                <p><strong>Supplier:</strong> ${product.supplier_name}</p>
                <p><strong>Location:</strong> ${product.supplier_location}</p>
                <p><strong>Rating:</strong> ${product.supplier_rating}/5.0</p>
                <p><strong>Stock:</strong> ${product.stock_available} ${product.unit} available</p>
            </div>
            <div class="modal-actions">
                <button class="btn btn-primary" onclick="addToCart('${product.id}')">Add to Cart</button>
                <button class="btn btn-secondary" onclick="closeModal()">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close modal functionality
    const closeBtn = modal.querySelector('.close');
    closeBtn.onclick = () => closeModal();
    
    window.onclick = (event) => {
        if (event.target === modal) {
            closeModal();
        }
    };
}

// Close modal
function closeModal() {
    const modal = document.querySelector('.modal');
    if (modal) {
        modal.remove();
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Join group order
async function joinGroupOrder(orderId) {
    try {
        const response = await fetch('/api/join-group-order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                group_order_id: orderId,
                quantity: 5 // Default quantity, should be user input
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            loadGroupOrders(); // Refresh the list
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('An error occurred while joining the order.', 'error');
    }
}

// Create group order
function showCreateGroupOrder() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close">&times;</span>
            <h2>Create Group Order</h2>
            <form id="create-group-order-form">
                <div class="form-group">
                    <label for="product-select">Select Product</label>
                    <select id="product-select" required>
                        <option value="">Choose a product...</option>
                        ${window.products?.map(p => `<option value="${p.id}">${p.name} - ₹${p.current_price}/${p.unit}</option>`).join('') || ''}
                    </select>
                </div>
                <div class="form-group">
                    <label for="target-quantity">Target Quantity (kg)</label>
                    <input type="number" id="target-quantity" required min="10" step="1">
                </div>
                <div class="form-group">
                    <label for="your-quantity">Your Quantity (kg)</label>
                    <input type="number" id="your-quantity" required min="1" step="1">
                </div>
                <div class="modal-actions">
                    <button type="submit" class="btn btn-primary">Create Order</button>
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Form submission
    document.getElementById('create-group-order-form').onsubmit = async (e) => {
        e.preventDefault();
        
        const productId = document.getElementById('product-select').value;
        const targetQuantity = document.getElementById('target-quantity').value;
        const yourQuantity = document.getElementById('your-quantity').value;
        const product = window.products?.find(p => p.id == productId);
        
        if (!product) {
            showNotification('Please select a valid product.', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/create-group-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_id: productId,
                    target_quantity: parseFloat(targetQuantity),
                    price_per_unit: product.current_price,
                    quantity: parseFloat(yourQuantity)
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showNotification(data.message, 'success');
                closeModal();
                loadGroupOrders(); // Refresh the list
            } else {
                showNotification(data.message, 'error');
            }
        } catch (error) {
            showNotification('An error occurred while creating the group order.', 'error');
        }
    };
    
    // Close modal functionality
    const closeBtn = modal.querySelector('.close');
    closeBtn.onclick = () => closeModal();
    
    window.onclick = (event) => {
        if (event.target === modal) {
            closeModal();
        }
    };
}

// Contact supplier
function contactSupplier(phone) {
    if (confirm(`Call ${phone}?`)) {
        window.location.href = `tel:${phone}`;
    }
}

// Initialize app
function initializeApp() {
    initializeVoiceRecognition();
    updateCartUI();
    
    // Set default language
    const savedLanguage = localStorage.getItem('preferred-language') || 'en';
    changeLanguage(savedLanguage);
    
    // Load initial data
    if (window.location.pathname.includes('/vendor/dashboard')) {
        loadDashboardData();
    }
}

// Enhanced mapping of business types to relevant ingredients (robust to variations)
const businessTypeIngredients = {
    'ice_cream': ['Milk', 'Sugar', 'Ice Cream Mix', 'Vanilla Essence', 'Chocolate Syrup', 'Dry Fruits'],
    'ice cream': ['Milk', 'Sugar', 'Ice Cream Mix', 'Vanilla Essence', 'Chocolate Syrup', 'Dry Fruits'],
    'ice cream stall': ['Milk', 'Sugar', 'Ice Cream Mix', 'Vanilla Essence', 'Chocolate Syrup', 'Dry Fruits'],
    'chaat': ['Potatoes', 'Onions', 'Tomatoes', 'Coriander', 'Chutney', 'Papdi', 'Curd', 'Spices'],
    'dosa': ['Rice', 'Urad Dal', 'Oil', 'Potatoes', 'Onions', 'Chutney', 'Spices'],
    'samosa': ['Potatoes', 'Peas', 'Flour', 'Oil', 'Spices'],
    'vada_pav': ['Potatoes', 'Buns', 'Oil', 'Spices', 'Chutney'],
    'vada pav': ['Potatoes', 'Buns', 'Oil', 'Spices', 'Chutney'],
    'tea': ['Tea Leaves', 'Milk', 'Sugar', 'Spices'],
    'juice': ['Fruits', 'Sugar', 'Ice', 'Salt'],
    'other': []
};

// Load dashboard data
async function loadDashboardData() {
    try {
        const [productsRes, alertsRes] = await Promise.all([
            fetch('/api/products'),
            fetch('/api/price-alerts')
        ]);
        
        window.products = await productsRes.json();
        window.alerts = await alertsRes.json();
        
        // Update stats
        document.getElementById('total-orders').textContent = '12';
        document.getElementById('monthly-savings').textContent = '₹2,450';
        document.getElementById('active-group-orders').textContent = '3';
        document.getElementById('verified-suppliers').textContent = '5';
        
        // Display relevant products for business type
        displayRelevantProductsForBusinessType();
        
        // Display price alerts
        displayPriceAlerts();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showNotification('Error loading dashboard data.', 'error');
    }
}

// Display products relevant to the vendor's business type
function displayRelevantProductsForBusinessType() {
    const container = document.getElementById('recent-products');
    if (!container) return;
    let businessType = (window.vendorBusinessType || '').toLowerCase().replace(/_/g, ' ').trim();
    console.log('Business Type:', businessType);
    console.log('Available business types:', Object.keys(businessTypeIngredients));
    let ingredientList = businessTypeIngredients[businessType];
    // Fallback: if businessType contains 'ice cream', use ice cream ingredients
    if (!ingredientList) {
        if (businessType.includes('ice cream')) {
            ingredientList = businessTypeIngredients['ice cream'];
            console.log('Using ice cream ingredients via fallback');
        } else if (businessType.includes('vada pav')) {
            ingredientList = businessTypeIngredients['vada pav'];
        } else {
            ingredientList = [];
        }
    }
    console.log('Ingredient List:', ingredientList);
    if (!window.products) return;
    console.log('All Products:', window.products.map(p => p.name));
    // Filter products by ingredient names
    const relevantProducts = window.products.filter(product =>
        ingredientList.some(ingredient => product.name.toLowerCase().includes(ingredient.toLowerCase()))
    );
    console.log('Relevant Products:', relevantProducts.map(p => p.name));
    if (relevantProducts.length === 0) {
        container.innerHTML = `<div class="no-data">No relevant ingredients found for your business type.</div>`;
        return;
    }
    container.innerHTML = relevantProducts.map(product => `
        <div class="product-card">
            <div class="product-name">${product.name}</div>
            <div class="product-price">₹${product.current_price}/${product.unit}</div>
            <div class="product-supplier">${product.supplier_name}</div>
            <div class="product-actions">
                <button class="btn btn-primary" onclick="addToCart('${product.id}')">Add to Cart</button>
                <button class="btn btn-secondary" onclick="viewDetails('${product.id}')">Details</button>
            </div>
        </div>
    `).join('');
}

// Display price alerts
function displayPriceAlerts() {
    const container = document.getElementById('price-alerts');
    if (!container) return;
    
    const alerts = window.alerts || [];
    
    if (alerts.length === 0) {
        container.innerHTML = `<div class="no-data">${translations[currentLanguage || 'en']['no-alerts']}</div>`;
        return;
    }
    
    container.innerHTML = alerts.map(alert => `
        <div class="alert alert-info">
            <strong>${alert.product}:</strong> ${alert.message}
            <br><small>${alert.timestamp}</small>
        </div>
    `).join('');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

// Export functions for global access
window.VendorConnect = {
    changeLanguage,
    startVoiceSearch,
    addToCart,
    viewDetails,
    joinGroupOrder,
    showCreateGroupOrder,
    contactSupplier,
    showNotification
}; 