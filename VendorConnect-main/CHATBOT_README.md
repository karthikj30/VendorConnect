# VendorConnect Chatbot Integration

## Overview

The VendorConnect chatbot is an intelligent assistant designed to help local workers navigate through the VendorConnect platform more easily. It provides multilingual support, voice input capabilities, and contextual responses based on user intent.

## Features

### 🤖 Intelligent Assistant
- **Contextual Responses**: Understands user intent and provides relevant information
- **Multilingual Support**: Available in English, Hindi, Bengali, and Tamil
- **Voice Input**: Speech recognition for hands-free interaction
- **Quick Actions**: Pre-defined buttons for common tasks

### 🎨 Modern UI/UX
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Dark Mode Support**: Automatically adapts to user's theme preference
- **Smooth Animations**: Engaging user experience with smooth transitions
- **Accessibility**: Full keyboard navigation and screen reader support

### 🔧 Technical Features
- **Session Management**: Maintains conversation context across sessions
- **Local Storage**: Saves conversation history locally
- **Real-time Communication**: Instant responses with typing indicators
- **Error Handling**: Graceful error handling with user-friendly messages

## File Structure

```
VendorConnect-main/
├── templates/
│   ├── chatbot.html          # Standalone chatbot page
│   ├── index.html            # Main page with chatbot integration
│   └── vendor_dashboard.html # Dashboard with chatbot integration
├── static/
│   ├── css/
│   │   └── chatbot.css       # Chatbot-specific styles
│   └── js/
│       └── chatbot.js        # Chatbot functionality
└── app.py                    # Backend API endpoints
```

## API Endpoints

### POST `/api/chatbot/message`
Handles chatbot messages and provides intelligent responses.

**Request Body:**
```json
{
    "message": "I need help finding suppliers",
    "language": "en",
    "context": {},
    "session_id": "session_123"
}
```

**Response:**
```json
{
    "message": "I can help you find suppliers! Here are some options:",
    "context": {"intent": "suppliers"},
    "actions": [
        {"action": "view-suppliers", "label": "View All Suppliers"},
        {"action": "filter-suppliers", "label": "Filter by Location"}
    ]
}
```

### POST `/api/chatbot/language`
Handles language changes for the chatbot.

**Request Body:**
```json
{
    "language": "hi",
    "session_id": "session_123"
}
```

## Supported Intents

The chatbot recognizes and responds to the following intents:

1. **Greetings** - Hello, Hi, Namaste, etc.
2. **Suppliers** - Finding suppliers, supplier information
3. **Orders** - Placing orders, order management
4. **Delivery** - Tracking deliveries, delivery status
5. **Pricing** - Price information, price alerts
6. **Help** - Support, FAQ, assistance
7. **Account** - Profile management, settings

## Multilingual Support

### Supported Languages
- **English (EN)** - Default language
- **Hindi (हिं)** - हिंदी support
- **Bengali (বাং)** - বাংলা support  
- **Tamil (தமிழ்)** - தமிழ் support

### Language Features
- **Dynamic Translation**: All UI elements translate based on selected language
- **Voice Recognition**: Speech recognition adapts to selected language
- **Cultural Context**: Responses are culturally appropriate for each language

## Voice Input

### Browser Support
- **Chrome/Edge**: Full support with Web Speech API
- **Firefox**: Limited support
- **Safari**: Basic support
- **Mobile**: Works on Android Chrome and iOS Safari

### Voice Commands
Users can speak commands in their preferred language:
- "Find suppliers near me"
- "Place an order for tomatoes"
- "Track my delivery"
- "Set up price alerts"

## Quick Actions

The chatbot provides quick action buttons for common tasks:

1. **Find Suppliers** - Browse verified suppliers
2. **Place Order** - Start ordering process
3. **Track Delivery** - Check delivery status
4. **Price Alerts** - Set up price notifications

## Integration

### Adding to Existing Pages

To add the chatbot to any page, include these elements before the closing `</body>` tag:

```html
<!-- Chatbot Integration -->
<div id="chatbot-container" class="chatbot-container">
    <!-- Chatbot HTML structure -->
</div>

<!-- Chatbot Toggle Button -->
<button id="chatbot-toggle" class="chatbot-toggle">
    <i class="fas fa-comments"></i>
    <span class="notification-badge" id="notification-badge">1</span>
</button>

<!-- Chatbot Styles -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/chatbot.css') }}">

<!-- Chatbot Script -->
<script src="{{ url_for('static', filename='js/chatbot.js') }}"></script>
```

### Customization

The chatbot can be customized by modifying:

1. **CSS Variables** in `chatbot.css`:
   ```css
   :root {
       --primary-color: #667eea;
       --secondary-color: #764ba2;
       --success-color: #28a745;
       --error-color: #dc3545;
   }
   ```

2. **Response Templates** in `app.py`:
   ```python
   def get_custom_response(language, vendor):
       # Add custom response logic
       pass
   ```

3. **Quick Actions** in the HTML:
   ```html
   <button class="quick-action-btn" data-action="custom-action">
       <i class="fas fa-custom-icon"></i>
       Custom Action
   </button>
   ```

## Usage Examples

### Basic Usage
```javascript
// Initialize chatbot
const chatbot = new VendorConnectChatbot();

// Send a message programmatically
chatbot.sendMessage("I need help with orders");

// Change language
chatbot.changeLanguage('hi');

// Toggle chatbot visibility
chatbot.toggleChatbot();
```

### Custom Integration
```javascript
// Listen for chatbot events
document.addEventListener('chatbot:message', (event) => {
    console.log('New message:', event.detail);
});

// Custom quick action handler
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('quick-action-btn')) {
        const action = e.target.dataset.action;
        // Handle custom action
    }
});
```

## Testing

### Manual Testing
1. Visit `/chatbot` for standalone testing
2. Test on main page (`/`) and dashboard (`/vendor/dashboard`)
3. Try different languages and voice input
4. Test responsive design on mobile devices

### Automated Testing
```javascript
// Test chatbot initialization
test('Chatbot initializes correctly', () => {
    const chatbot = new VendorConnectChatbot();
    expect(chatbot.isOpen).toBe(false);
});

// Test message sending
test('Sends message to backend', async () => {
    const chatbot = new VendorConnectChatbot();
    const response = await chatbot.sendToBackend('Hello');
    expect(response.message).toBeDefined();
});
```

## Performance Considerations

### Optimization Tips
1. **Lazy Loading**: Chatbot scripts load only when needed
2. **Local Storage**: Conversation history stored locally to reduce server load
3. **Debounced Input**: Voice input is debounced to prevent excessive API calls
4. **Cached Responses**: Common responses are cached for faster delivery

### Browser Compatibility
- **Modern Browsers**: Full feature support
- **Older Browsers**: Graceful degradation with basic functionality
- **Mobile**: Optimized for touch interactions

## Security

### Data Protection
- **No Sensitive Data**: Chatbot doesn't store sensitive user information
- **Session Management**: Secure session handling
- **Input Validation**: All user inputs are validated and sanitized

### Privacy
- **Local Storage**: Conversation history stored locally
- **No Tracking**: No user behavior tracking
- **GDPR Compliant**: Follows privacy best practices

## Troubleshooting

### Common Issues

1. **Voice Input Not Working**
   - Check browser permissions for microphone access
   - Ensure HTTPS connection for speech recognition
   - Verify browser support for Web Speech API

2. **Language Not Changing**
   - Clear browser cache and reload
   - Check if language files are loaded correctly
   - Verify API endpoint is responding

3. **Chatbot Not Appearing**
   - Check if CSS and JS files are loaded
   - Verify no JavaScript errors in console
   - Ensure proper HTML structure

### Debug Mode
Enable debug mode by adding this to the console:
```javascript
window.chatbot.debug = true;
```

## Future Enhancements

### Planned Features
1. **AI Integration**: Connect to external AI services for more intelligent responses
2. **Offline Support**: Work without internet connection
3. **Push Notifications**: Real-time notifications for important updates
4. **Analytics**: Usage analytics and insights
5. **Custom Themes**: User-customizable chatbot appearance

### API Improvements
1. **WebSocket Support**: Real-time bidirectional communication
2. **File Upload**: Support for image and document sharing
3. **Rich Media**: Support for cards, carousels, and interactive elements
4. **Integration APIs**: Connect with external services

## Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`
4. Visit `http://localhost:5000/chatbot` to test

### Code Style
- Follow PEP 8 for Python code
- Use ESLint for JavaScript
- Maintain consistent CSS naming conventions
- Write comprehensive comments and documentation

## License

This chatbot integration is part of the VendorConnect project and follows the same licensing terms.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the code comments and documentation
3. Create an issue in the project repository
4. Contact the development team

---

**Note**: This chatbot is designed specifically for the VendorConnect platform and may require modifications for use in other applications.
