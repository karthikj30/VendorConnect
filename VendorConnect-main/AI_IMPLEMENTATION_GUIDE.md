# AI Implementation Guide - VendorConnect

## Overview
Complete AI integration with **Floating Assistant UI** for Vendor and Customer dashboards using Qubrid platform models. The AI assistant appears as a floating overlay (like the chatbot) accessible from any page, not just embedded in the dashboard.

---

## 🎯 Implementation Summary

### Architecture
- **Floating UI Pattern**: AI assistant appears as a fixed button in bottom-right corner (above chatbot)
- **Accessible Everywhere**: Available on all vendor/customer pages, not just dashboards
- **Live Voice Recording**: Microphone button for direct audio recording (MediaRecorder API)
- **Role-Based Tabs**: Vendors see Analytics tab, Customers see Support tab
- **8 AI Tools**: Chat, Document OCR, Voice Transcription, Image Generation, Voice Commands, Search, Analytics (vendor), Support (customer)

### Vendor Dashboard AI Features ✅
1. **GPT-OSS 120B** - Chatbot for decisions, explanations, demand & trend insights
2. **Qwen Vision (Apache)** - Reads invoices & receipts, extracts items, prices, totals
3. **Whisper (open-source)** - Voice input → text (ordering, queries, commands) + **Live Recording**
4. **Stable Diffusion** - Menu images, food visuals, banners
5. **Whisper + GPT-OSS + Nemotron** - Voice command → backend action (order, assign delivery, alerts)
6. **Semantic Search** - AI-powered search for vendors, menus, suppliers
7. **Sales Analytics** - Sales summary, restock suggestions, trend explanation

### Customer Dashboard AI Features ✅
1. **GPT-OSS 120B** - Chatbot for decisions, explanations, demand & trend insights
2. **Whisper (open-source)** - Voice input → text (ordering, queries, commands) + **Live Recording**
3. **Stable Diffusion** - Menu images, food visuals, banners
4. **Semantic Search** - AI-powered search for vendors, menus
5. **Support Assistant** - Order issues, help, FAQs

---

## 🔧 Setup Instructions

### 1. Environment Variables
Set the following environment variables before starting the app:

```bash
# Required - Get your API key from platform.qubrid.com
QUBRID_API_KEY=your_api_key_here

# Optional (defaults are set)
QUBRID_API_BASE=https://platform.qubrid.com/v1
QUBRID_CHAT_MODEL=gpt-oss-120b
QUBRID_VISION_MODEL=qwen-vision
QUBRID_AUDIO_MODEL=whisper-large
QUBRID_IMAGE_MODEL=stable-diffusion
QUBRID_ORCH_MODEL=nemotron-orchestrator-8b
QUBRID_TIMEOUT_SECONDS=45
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

---

## 📋 API Endpoints

All AI endpoints are accessible at `/api/ai/*` and require vendor or customer authentication.

### Chat Completion
**POST** `/api/ai/chat`
```json
{
  "prompt": "What are trending menu items?",
  "model": "gpt-oss-120b",
  "temperature": 0.3
}
```

### Document Reader (Vision)
**POST** `/api/ai/document`
- **Content-Type**: `multipart/form-data`
- **Fields**: 
  - `file`: Image or PDF file
  - `model`: Vision model name (optional)
  - `prompt`: Extraction instructions (optional)

### Speech-to-Text
**POST** `/api/ai/audio`
- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `audio`: Audio file
  - `model`: Audio model name (optional)
  - `language`: Language code (default: en)

### Image Generation
**POST** `/api/ai/image`
```json
{
  "prompt": "Street food banner with colorful designs",
  "model": "stable-diffusion"
}
```

### Voice Command Router
**POST** `/api/ai/command`
- Accepts either audio file (multipart) or text command (JSON)
- Returns orchestrated action plan

### Semantic Search
**POST** `/api/ai/search`
```json
{
  "query": "best biryani near me",
  "type": "vendors",
  "model": "gpt-oss-120b"
}
```

### Sales Analytics (Vendor Only)
**POST** `/api/ai/analytics`
```json
{
  "sales_data": "Item: Samosa, Qty: 150, Revenue: 3000...",
  "period": "monthly",
  "model": "gpt-oss-120b"
}
```

### Support Assistant (Customer Only)
**POST** `/api/ai/support`
```json
{
  "message": "My order is delayed, where is it?",
  "conversation": [],
  "model": "gpt-oss-120b"
}
```

---

## 🎨 UI Components

### Vendor Dashboard
Navigate to: `/vendor/dashboard`

AI Copilot card includes:
- **Chat & Decisions** - General AI chatbot
- **Document Reader** - Upload receipts/invoices
- **Speech to Text** - Transcribe voice notes
- **Image Generator** - Create menu visuals
- **Voice Commands** - Plan actions from voice
- **Semantic Search** - Find vendors/suppliers
- **Sales Analytics** - Get business insights

### Customer Dashboard
Navigate to: `/customer/dashboard`

AI Copilot panel includes:
- **Chat & Decisions** - General AI assistance
- **Receipt Reader** - Scan food bills
- **Voice to Text** - Voice ordering
- **Image Generator** - Create custom visuals
- **Voice Commands** - Action planning
- **Smart Search** - Find restaurants/dishes
- **Support Assistant** - 24/7 help for issues

---

## 🔐 Security

- All endpoints require authentication (vendor_id or customer_id in session)
- File uploads are capped at 15MB
- Request timeout is 45 seconds (configurable)
- API key is never exposed to frontend

---

## 📊 Model Usage by Role

| Feature | Model | Vendor | Customer |
|---------|-------|--------|----------|
| Chatbot | GPT-OSS 120B | ✅ | ✅ |
| Document OCR | Qwen Vision | ✅ | ✅ |
| Speech-to-Text | Whisper Large | ✅ | ✅ |
| Image Generation | Stable Diffusion | ✅ | ✅ |
| Voice Commands | Whisper + GPT + Nemotron | ✅ | ✅ |
| Semantic Search | GPT-OSS 120B | ✅ | ✅ |
| Sales Analytics | GPT-OSS 120B | ✅ | ❌ |
| Support Assistant | GPT-OSS 120B | ❌ | ✅ |

---

## 🚀 Testing

1. Login as vendor: `/vendor/login`
2. Login as customer: `/customer/login`
3. Navigate to respective dashboards
4. Use AI Copilot tools in the top card/panel
5. Check console for errors

---

## 📝 Notes

- Supplier and Delivery Agent dashboards are **not** modified (as requested)
- All AI responses are displayed inline in the UI
- Models can be changed per request via the `model` parameter
- Provider API errors are logged and returned safely to users
- File upload handling includes type and size validation

---

## 🛠️ Customization

### Change Model Endpoints
If Qubrid uses different paths, set these environment variables:
```bash
QUBRID_CHAT_PATH=/chat/completions
QUBRID_VISION_PATH=/vision/completions
QUBRID_AUDIO_PATH=/audio/transcriptions
QUBRID_IMAGE_PATH=/images/generations
QUBRID_ORCH_PATH=/chat/completions
```

### Add More Models
Edit `ai_integrations.py` and add new default model constants:
```python
DEFAULT_NEW_MODEL = os.environ.get('QUBRID_NEW_MODEL', 'model-name')
```

---

## 🎨 Floating UI Features

### Design
- **Fixed Position**: Bottom-right corner at `bottom: 90px` (above chatbot at `bottom: 20px`)
- **Toggle Button**: 60px circular button with AI icon (🤖)
- **Panel Size**: 420px width, max 85vh height with scrollable content
- **Responsive**: Stacks vertically on mobile, adjusts for small screens

### User Experience
1. **Click toggle button** → AI assistant panel slides in
2. **Select tab** (Chat, Document, Voice, Image, Command, Search, Analytics/Support)
3. **Use tools**:
   - **Chat**: Type question → Click "Ask"
   - **Document**: Upload image/PDF → Click "Extract"
   - **Voice**: Click microphone 🎤 → Record → Click again to stop → Auto-transcribe
   - **Image**: Enter prompt → Click "Generate" → View result
   - **Command**: Type or record → Click "Plan"
   - **Search**: Enter query + type → Click "Search"
   - **Analytics** (Vendor): Paste sales data + period → Click "Analyze"
   - **Support** (Customer): Type issue → Click "Get Help"

### Live Voice Recording
- **Click microphone button** → Browser requests mic permission → Recording starts
- **Timer displays** recording duration (MM:SS)
- **Click again to stop** → Audio automatically sent to Whisper → Transcript appears
- **Audio format**: WebM (browser default), compatible with Qubrid Whisper API
- **No file upload needed** for voice transcription

### Files
- **CSS**: `static/css/ai-assistant.css` (437 lines) - Floating styles, animations, tabs
- **JavaScript**: `static/js/ai-assistant.js` (702 lines) - AIAssistant class, MediaRecorder, all tools
- **Auto-initialization**: Script auto-detects role (vendor/customer) and initializes on page load

---

## ✅ Implementation Checklist

- [x] Chat completion (GPT-OSS 120B)
- [x] Document reader (Qwen Vision)
- [x] Speech-to-text (Whisper)
- [x] Image generation (Stable Diffusion)
- [x] Voice command router (Whisper + Nemotron)
- [x] Semantic search (GPT-OSS 120B)
- [x] Sales analytics (Vendor only)
- [x] Support assistant (Customer only)
- [x] Floating UI with toggle button
- [x] Live microphone recording (MediaRecorder API)
- [x] Role-based tab visibility
- [x] Vendor template integration
- [x] Customer template integration
- [x] Authentication & security
- [x] Error handling
- [x] File upload validation
- [x] Environment configuration

---

**Status**: ✅ Complete and ready for deployment
