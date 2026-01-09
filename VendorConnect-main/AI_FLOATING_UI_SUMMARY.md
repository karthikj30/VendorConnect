# AI Floating Assistant - Quick Reference

## 🚀 What Changed

### Before
- AI tools were embedded directly in vendor/customer dashboards
- Only visible on dashboard page
- File upload only for audio transcription
- Inline functions cluttering template files

### After  
- **Floating AI assistant** button in bottom-right corner (🤖 icon)
- **Visible everywhere** - all vendor/customer pages, not just dashboard
- **Live microphone recording** - click mic button to record, click again to stop & auto-transcribe
- **Clean separation** - All AI logic in `ai-assistant.js`, all styles in `ai-assistant.css`

---

## 📁 Files Modified

### Core AI Backend
- `ai_integrations.py` - Fixed API key retrieval (line 32: now uses `QUBRID_API_KEY` env var correctly)

### Frontend Assets
- `static/css/ai-assistant.css` - **NEW** - 437 lines of floating UI styles
- `static/js/ai-assistant.js` - **NEW** - 702 lines with AIAssistant class, MediaRecorder integration

### Templates Updated
- `templates/vendor_dashboard.html`:
  - Removed embedded AI copilot card (~100 lines)
  - Removed inline AI functions (~200 lines)
  - Added includes for ai-assistant.css and ai-assistant.js
  
- `templates/customer_dashboard.html`:
  - Removed embedded AI panel (~90 lines)
  - Removed inline AI functions (~200 lines)  
  - Added includes for ai-assistant.css and ai-assistant.js

### Documentation
- `AI_IMPLEMENTATION_GUIDE.md` - Updated with floating UI architecture, live recording details

---

## 🎯 How to Use

### For Users

1. **Open AI Assistant**
   - Look for 🤖 button in bottom-right corner (above chatbot button)
   - Click to open/close the floating panel

2. **Select a Tool**
   - Click tab at top: Chat | Document | Voice | Image | Command | Search | Analytics/Support
   - Vendors see "Analytics" tab, Customers see "Support" tab

3. **Live Voice Recording** (Voice tab)
   - Click microphone button 🎤
   - Browser asks for mic permission (allow it)
   - Recording starts, timer shows duration (00:05, 00:10, etc.)
   - Click mic button again to stop
   - Audio automatically transcribes via Whisper
   - Transcript appears in output area

4. **Other Tools**
   - **Chat**: Type question → Ask
   - **Document**: Upload receipt/invoice image → Extract
   - **Image**: Enter prompt → Generate
   - **Command**: Type or record voice command → Plan Actions
   - **Search**: Enter query, select type → Search
   - **Analytics** (Vendor): Paste sales data, select period → Analyze
   - **Support** (Customer): Describe issue → Get Help

### For Developers

1. **Set API Key**
   ```bash
   export QUBRID_API_KEY=your_api_key_here  # Linux/Mac
   set QUBRID_API_KEY=your_api_key_here     # Windows CMD
   $env:QUBRID_API_KEY="your_api_key_here"  # Windows PowerShell
   ```

2. **Start App**
   ```bash
   python app.py
   ```

3. **Test AI Assistant**
   - Login as vendor or customer
   - Click 🤖 button in bottom-right
   - Try different tabs
   - Test microphone recording (Voice tab)

---

## 🔧 Technical Details

### JavaScript Architecture
```javascript
class AIAssistant {
    constructor() {
        this.role = 'vendor' | 'customer';  // Auto-detected from URL
        this.isOpen = false;
        this.mediaRecorder = null;
        this.recordingChunks = [];
        this.recordingTimer = null;
    }
    
    // Methods:
    createUI()              // Builds floating panel HTML
    toggle()                // Open/close assistant
    switchTab(tab)          // Switch between tools
    startRecording()        // Start mic capture
    stopRecording()         // Stop & process audio
    processRecording(blob)  // Send to Whisper API
    handleChat()            // Chat tool
    handleDocument()        // Document OCR
    handleVoice()           // Voice transcription
    handleImage()           // Image generation
    handleCommand()         // Voice commands
    handleSearch()          // Semantic search
    handleAnalytics()       // Sales analytics (vendor)
    handleSupport()         // Support assistant (customer)
}
```

### MediaRecorder Flow
1. User clicks mic button → `startRecording()`
2. Request mic permission → `navigator.mediaDevices.getUserMedia({ audio: true })`
3. Create MediaRecorder → `new MediaRecorder(stream)`
4. Start recording → `mediaRecorder.start()`
5. Update timer every second → `setInterval()`
6. User clicks again → `stopRecording()`
7. MediaRecorder fires `ondataavailable` → Collect chunks
8. MediaRecorder fires `onstop` → `processRecording()`
9. Create Blob from chunks → `new Blob(chunks, { type: 'audio/webm' })`
10. Send to `/api/ai/audio` → FormData with blob
11. Display transcript in output area

### CSS Positioning
```css
.ai-assistant-container {
    position: fixed;
    bottom: 90px;        /* Above chatbot at 20px */
    right: 20px;
    width: 420px;
    max-height: 85vh;
    z-index: 999;        /* Below chatbot at 1000 */
}

.ai-assistant-toggle {
    position: fixed;
    bottom: 90px;
    right: 20px;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

---

## 🐛 Troubleshooting

### Microphone Not Working
- **Check permissions**: Browser should prompt for mic access. Allow it.
- **HTTPS required**: MediaRecorder needs secure context (localhost or HTTPS)
- **Browser support**: Chrome, Edge, Firefox support MediaRecorder. Safari may need fallback.

### "QUBRID_API_KEY is not configured"
- Environment variable not set. Run: `export QUBRID_API_KEY=your_key`
- Key name must be exactly `QUBRID_API_KEY` (not the key value itself)

### AI Button Not Showing
- Check browser console for JavaScript errors
- Verify ai-assistant.js is loaded: View Page Source → Look for `<script src="/static/js/ai-assistant.js">`
- Check ai-assistant.css is loaded: Look for `<link rel="stylesheet" href="/static/css/ai-assistant.css">`

### Recording Stops Immediately
- Browser may have blocked mic access. Check browser permissions.
- Check console for MediaRecorder errors
- Verify HTTPS or localhost (MediaRecorder security requirement)

---

## 📊 API Endpoints (Reference)

All endpoints require vendor_id or customer_id in session:

| Endpoint | Method | Purpose | Input | Output |
|----------|--------|---------|-------|--------|
| `/api/ai/chat` | POST | Chat completion | `{prompt, model, temperature}` | `{success, content}` |
| `/api/ai/document` | POST | OCR from image/PDF | FormData: `file, model, prompt` | `{success, content}` |
| `/api/ai/audio` | POST | Speech-to-text | FormData: `audio, model` | `{success, text}` |
| `/api/ai/image` | POST | Image generation | `{prompt, model, size}` | `{success, image_b64}` |
| `/api/ai/command` | POST | Voice → actions | FormData: `audio` OR JSON: `{command}` | `{success, transcript, plan}` |
| `/api/ai/search` | POST | Semantic search | `{query, type, model}` | `{success, results, analysis}` |
| `/api/ai/analytics` | POST | Sales insights | `{sales_data, period, model}` | `{success, insights}` |
| `/api/ai/support` | POST | Customer help | `{message, model}` | `{success, response}` |

---

## ✅ Testing Checklist

- [ ] AI button visible in bottom-right corner
- [ ] Click button opens floating panel
- [ ] All 8 tabs visible and clickable
- [ ] Vendor sees "Analytics" tab
- [ ] Customer sees "Support" tab
- [ ] Chat tool works (type prompt → Ask → response)
- [ ] Document tool works (upload image → Extract → text)
- [ ] Voice tool works:
  - [ ] Click mic → browser asks permission
  - [ ] Recording starts, timer shows (00:01, 00:02...)
  - [ ] Click mic again → recording stops
  - [ ] Transcript appears automatically
- [ ] Image tool works (enter prompt → Generate → image displays)
- [ ] Command tool works (type/record → Plan → actions shown)
- [ ] Search tool works (query + type → Search → results)
- [ ] Analytics works (vendor: paste data → Analyze → insights)
- [ ] Support works (customer: type issue → Get Help → response)
- [ ] Assistant accessible from all pages (not just dashboard)
- [ ] Mobile responsive (panel adjusts for small screens)

---

## 🎉 Summary

You now have a **floating AI assistant** that:
- ✅ Appears everywhere (not just dashboard)
- ✅ 8 AI-powered tools in one interface
- ✅ Live microphone recording for voice transcription
- ✅ Role-based features (vendor Analytics vs customer Support)
- ✅ Clean, modular code (separate CSS/JS files)
- ✅ Auto-initializes on page load
- ✅ Works alongside existing chatbot

**Next Steps**: Set `QUBRID_API_KEY` environment variable and test all 8 tools!
