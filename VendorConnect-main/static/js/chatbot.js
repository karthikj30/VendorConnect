// VendorConnect Chatbot JavaScript

class VendorConnectChatbot {
    constructor() {
        this.isOpen = false;
        this.isMinimized = false;
        this.currentLanguage = 'en';
        this.isRecording = false;
        this.recognition = null;
        this.messages = [];
        this.conversationContext = {};
        
        this.init();
    }

    init() {
        this.setupElements();
        this.setupEventListeners();
        this.loadConversationHistory();
        this.setupLanguageSupport();
    }

    setupElements() {
        this.chatbotContainer = document.getElementById('chatbot-container');
        this.chatbotToggle = document.getElementById('chatbot-toggle');
        this.chatMessages = document.getElementById('chat-messages');
        this.minimizeBtn = document.getElementById('minimize-btn');
        this.closeBtn = document.getElementById('close-btn');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.quickActions = document.getElementById('quick-actions');
        this.notificationBadge = document.getElementById('notification-badge');
        this.loadingOverlay = document.getElementById('loading-overlay');
    }

    setupEventListeners() {
        // Toggle chatbot
        this.chatbotToggle.addEventListener('click', () => this.toggleChatbot());
        
        // Text input removed - only tag-based interaction
        
        // Voice input removed - tag-based only
        
        // Control buttons
        this.minimizeBtn.addEventListener('click', () => this.minimizeChatbot());
        this.closeBtn.addEventListener('click', () => this.closeChatbot());
        
        // Quick actions
        this.quickActions.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-action-btn')) {
                this.handleQuickAction(e.target.dataset.action);
            }
        });
        
        // Language buttons
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.changeLanguage(e.target.dataset.lang));
        });
        
        // Text input functionality removed - tag-based only
    }

    // Speech recognition removed - tag-based interaction only

    setupLanguageSupport() {
        this.translations = {
            en: {
                placeholder: 'Type your message here...',
                typing: 'Assistant is typing...',
                voiceError: 'Voice input failed. Please try again.',
                processing: 'Processing your request...',
                quickActions: {
                    findSuppliers: 'Find Suppliers',
                    placeOrder: 'Place Order',
                    trackDelivery: 'Track Delivery',
                    priceAlerts: 'Price Alerts'
                }
            },
            hi: {
                placeholder: 'अपना संदेश यहाँ टाइप करें...',
                typing: 'सहायक टाइप कर रहा है...',
                voiceError: 'वॉइस इनपुट विफल। कृपया पुनः प्रयास करें।',
                processing: 'आपका अनुरोध प्रसंस्करण...',
                quickActions: {
                    findSuppliers: 'आपूर्तिकर्ता खोजें',
                    placeOrder: 'ऑर्डर दें',
                    trackDelivery: 'डिलीवरी ट्रैक करें',
                    priceAlerts: 'मूल्य अलर्ट'
                }
            },
            bn: {
                placeholder: 'এখানে আপনার বার্তা টাইপ করুন...',
                typing: 'সহায়ক টাইপ করছে...',
                voiceError: 'ভয়েস ইনপুট ব্যর্থ। অনুগ্রহ করে আবার চেষ্টা করুন।',
                processing: 'আপনার অনুরোধ প্রক্রিয়াকরণ...',
                quickActions: {
                    findSuppliers: 'সরবরাহকারী খুঁজুন',
                    placeOrder: 'অর্ডার দিন',
                    trackDelivery: 'ডেলিভারি ট্র্যাক করুন',
                    priceAlerts: 'মূল্য সতর্কতা'
                }
            },
            ta: {
                placeholder: 'உங்கள் செய்தியை இங்கே தட்டச்சு செய்யவும்...',
                typing: 'உதவியாளர் தட்டச்சு செய்கிறார்...',
                voiceError: 'குரல் உள்ளீடு தோல்வி. மீண்டும் முயற்சிக்கவும்.',
                processing: 'உங்கள் கோரிக்கை செயலாக்கப்படுகிறது...',
                quickActions: {
                    findSuppliers: 'சப்ளையர்களைக் கண்டறியவும்',
                    placeOrder: 'ஆர்டர் செய்யவும்',
                    trackDelivery: 'டெலிவரியைக் கண்காணிக்கவும்',
                    priceAlerts: 'விலை எச்சரிக்கைகள்'
                }
            }
        };
    }

    toggleChatbot() {
        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            this.chatbotContainer.classList.add('open');
            this.chatbotToggle.style.display = 'none';
            this.hideNotificationBadge();
        } else {
            this.chatbotContainer.classList.remove('open');
            this.chatbotToggle.style.display = 'flex';
        }
    }

    minimizeChatbot() {
        this.isMinimized = !this.isMinimized;
        this.chatbotContainer.classList.toggle('minimized', this.isMinimized);
    }

    closeChatbot() {
        this.isOpen = false;
        this.chatbotContainer.classList.remove('open');
        this.chatbotToggle.style.display = 'flex';
    }

    // sendMessage function removed - tag-based interaction only

    // sendToBackend function removed - using sendTagToBackend instead

    addMessage(text, sender, actions = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        
        // Handle different message types
        if (typeof text === 'string') {
            messageText.innerHTML = this.formatMessage(text);
        } else if (text.type === 'list') {
            messageText.innerHTML = this.createListMessage(text.items);
        } else if (text.type === 'card') {
            messageText.innerHTML = this.createCardMessage(text);
        }
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = this.getCurrentTime();
        
        content.appendChild(messageText);
        content.appendChild(messageTime);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Store message
        this.messages.push({
            text: text,
            sender: sender,
            timestamp: new Date(),
            actions: actions
        });
        
        // Save to localStorage
        this.saveConversationHistory();
    }

    formatMessage(text) {
        // Convert URLs to clickable links
        text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        // Convert line breaks to HTML
        text = text.replace(/\n/g, '<br>');
        
        return `<p>${text}</p>`;
    }

    createListMessage(items) {
        let html = '<ul>';
        items.forEach(item => {
            html += `<li>${item}</li>`;
        });
        html += '</ul>';
        return html;
    }

    createCardMessage(card) {
        return `
            <div class="card-message">
                <h4>${card.title}</h4>
                <p>${card.description}</p>
                ${card.actions ? this.createActionButtons(card.actions) : ''}
            </div>
        `;
    }

    createActionButtons(actions) {
        let html = '<div class="action-buttons">';
        actions.forEach(action => {
            html += `<button class="action-btn" data-action="${action.action}">${action.label}</button>`;
        });
        html += '</div>';
        return html;
    }

    handleQuickAction(action) {
        // Handle predefined tag clicks directly
        this.handleTagAction(action);
    }

    async handleTagAction(action) {
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Send tag action to backend
            const response = await this.sendTagToBackend(action);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add bot response
            this.addMessage(response.message, 'bot', response.actions);
            
            // Update conversation context
            this.conversationContext = response.context || {};
            
        } catch (error) {
            console.error('Error handling tag action:', error);
            this.hideTypingIndicator();
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    }

    async sendTagToBackend(action) {
        const response = await fetch('/api/chatbot/tag', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: action,
                language: this.currentLanguage,
                context: this.conversationContext,
                session_id: this.getSessionId()
            })
        });

        if (!response.ok) {
            throw new Error('Failed to send tag action');
        }

        return await response.json();
    }

    // Voice input removed - tag-based interaction only

    changeLanguage(lang) {
        this.currentLanguage = lang;
        
        // Update active language button
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-lang="${lang}"]`).classList.add('active');
        
        // Update speech recognition language
        if (this.recognition) {
            this.recognition.lang = this.getLanguageCode(lang);
        }
        
        // Update UI text
        this.updateUIText();
        
        // Send language change to backend
        this.sendLanguageChange(lang);
    }

    getLanguageCode(lang) {
        const codes = {
            'en': 'en-US',
            'hi': 'hi-IN',
            'bn': 'bn-IN',
            'ta': 'ta-IN'
        };
        return codes[lang] || 'en-US';
    }

    updateUIText() {
        const t = this.translations[this.currentLanguage];
        this.typingIndicator.querySelector('.typing-text').textContent = t.typing;
    }

    showTypingIndicator() {
        this.typingIndicator.classList.add('show');
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.classList.remove('show');
    }

    showQuickActions() {
        this.quickActions.style.display = 'flex';
    }

    hideQuickActions() {
        this.quickActions.style.display = 'none';
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    showNotificationBadge(count = 1) {
        this.notificationBadge.textContent = count;
        this.notificationBadge.style.display = 'flex';
    }

    hideNotificationBadge() {
        this.notificationBadge.style.display = 'none';
    }

    showLoading() {
        this.loadingOverlay.classList.add('show');
    }

    hideLoading() {
        this.loadingOverlay.classList.remove('show');
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    // autoResizeInput function removed - no text input

    getCurrentTime() {
        return new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }

    getSessionId() {
        let sessionId = localStorage.getItem('chatbot_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('chatbot_session_id', sessionId);
        }
        return sessionId;
    }

    saveConversationHistory() {
        const history = {
            messages: this.messages.slice(-50), // Keep last 50 messages
            context: this.conversationContext,
            language: this.currentLanguage,
            timestamp: new Date()
        };
        localStorage.setItem('chatbot_history', JSON.stringify(history));
    }

    loadConversationHistory() {
        const history = localStorage.getItem('chatbot_history');
        if (history) {
            try {
                const data = JSON.parse(history);
                this.messages = data.messages || [];
                this.conversationContext = data.context || {};
                this.currentLanguage = data.language || 'en';
                
                // Restore messages in UI
                this.messages.forEach(msg => {
                    this.addMessageToUI(msg.text, msg.sender);
                });
            } catch (error) {
                console.error('Error loading conversation history:', error);
            }
        }
    }

    addMessageToUI(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.innerHTML = this.formatMessage(text);
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = this.getCurrentTime();
        
        content.appendChild(messageText);
        content.appendChild(messageTime);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        this.chatMessages.appendChild(messageDiv);
    }

    async sendLanguageChange(lang) {
        try {
            await fetch('/api/chatbot/language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    language: lang,
                    session_id: this.getSessionId()
                })
            });
        } catch (error) {
            console.error('Error sending language change:', error);
        }
    }
}

// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new VendorConnectChatbot();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden && window.chatbot) {
        window.chatbot.saveConversationHistory();
    }
});

// Handle beforeunload to save conversation
window.addEventListener('beforeunload', () => {
    if (window.chatbot) {
        window.chatbot.saveConversationHistory();
    }
});
