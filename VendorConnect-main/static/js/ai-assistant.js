// AI Assistant JavaScript
class AIAssistant {
    constructor() {
        this.container = null;
        this.activeTab = 'chat';
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.conversationHistory = [];
        this.init();
    }

    init() {
        this.createUI();
        this.attachEventListeners();
    }

    createUI() {
        // Check if already exists
        if (document.getElementById('ai-assistant-container')) return;

        const html = `
            <!-- AI Assistant Toggle Button -->
            <button id="ai-assistant-toggle" class="ai-assistant-toggle" title="AI Assistant">
                <i class="fas fa-robot"></i>
                <span class="ai-badge-float">AI</span>
            </button>

            <!-- AI Assistant Container -->
            <div id="ai-assistant-container" class="ai-assistant-container">
                <div class="ai-assistant-header">
                    <div class="ai-assistant-title">
                        <i class="fas fa-robot"></i>
                        AI Assistant
                    </div>
                    <button class="ai-close-btn" id="ai-close-btn">
                        <i class="fas fa-times"></i>
                    </button>
                </div>

                <div class="ai-tabs">
                    <button class="ai-tab active" data-tab="chat">
                        <i class="fas fa-comment"></i> Chat
                    </button>
                    <button class="ai-tab" data-tab="document">
                        <i class="fas fa-file-invoice"></i> Doc
                    </button>
                    <button class="ai-tab" data-tab="voice">
                        <i class="fas fa-microphone"></i> Voice
                    </button>
                    <button class="ai-tab" data-tab="image">
                        <i class="fas fa-image"></i> Image
                    </button>
                    <button class="ai-tab" data-tab="command">
                        <i class="fas fa-terminal"></i> Command
                    </button>
                    <button class="ai-tab" data-tab="search">
                        <i class="fas fa-search"></i> Search
                    </button>
                    <button class="ai-tab" data-tab="analytics" id="analytics-tab" style="display: none;">
                        <i class="fas fa-chart-bar"></i> Analytics
                    </button>
                    <button class="ai-tab" data-tab="support" id="support-tab" style="display: none;">
                        <i class="fas fa-headset"></i> Support
                    </button>
                </div>

                <div class="ai-content">
                    ${this.createChatPanel()}
                    ${this.createDocumentPanel()}
                    ${this.createVoicePanel()}
                    ${this.createImagePanel()}
                    ${this.createCommandPanel()}
                    ${this.createSearchPanel()}
                    ${this.createAnalyticsPanel()}
                    ${this.createSupportPanel()}
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', html);
        this.container = document.getElementById('ai-assistant-container');

        // Show/hide role-specific tabs
        this.updateRoleTabs();
    }

    updateRoleTabs() {
        const isVendor = window.location.pathname.includes('/vendor/');
        const isCustomer = window.location.pathname.includes('/customer/');

        if (isVendor) {
            document.getElementById('analytics-tab').style.display = 'block';
        } else if (isCustomer) {
            document.getElementById('support-tab').style.display = 'block';
        }
    }

    createChatPanel() {
        return `
            <div class="ai-tool-panel active" data-panel="chat">
                <div class="ai-field">
                    <label class="ai-label">Ask anything</label>
                    <textarea id="ai-chat-input" class="ai-textarea-box" placeholder="Ask about pricing, menu ideas, inventory, promotions, or any questions..."></textarea>
                </div>
                <div class="ai-action-btns">
                    <button id="ai-chat-btn" class="ai-btn-primary">
                        <i class="fas fa-paper-plane"></i> Ask
                    </button>
                </div>
                <div id="ai-chat-output" class="ai-output-area empty">AI response will appear here...</div>
            </div>
        `;
    }

    createDocumentPanel() {
        return `
            <div class="ai-tool-panel" data-panel="document">
                <div class="ai-field">
                    <label class="ai-label">Upload Receipt/Invoice</label>
                    <input type="file" id="ai-doc-file" class="ai-input-box" accept="image/*,.pdf" />
                    <p class="ai-helper-text">Upload image or PDF to extract text, totals, and items</p>
                </div>
                <div class="ai-action-btns">
                    <button id="ai-doc-btn" class="ai-btn-primary">
                        <i class="fas fa-file-upload"></i> Extract
                    </button>
                </div>
                <div id="ai-doc-output" class="ai-output-area empty">Extracted data will appear here...</div>
            </div>
        `;
    }

    createVoicePanel() {
        return `
            <div class="ai-tool-panel" data-panel="voice">
                <div class="ai-field">
                    <label class="ai-label">Voice to Text</label>
                    <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                        <button id="ai-record-btn" class="ai-record-btn">
                            <i class="fas fa-microphone"></i>
                            <span id="ai-record-label">Start Recording</span>
                        </button>
                        <span id="ai-record-timer" style="display: none; color: #ef4444; font-weight: 600; align-self: center;">0:00</span>
                    </div>
                    <p class="ai-helper-text">Click to record voice, click again to stop and transcribe</p>
                    <p id="ai-voice-status" class="ai-helper-text" style="color: #6366f1; display: none;"></p>
                </div>
                <div class="ai-field" style="margin-top: 16px;">
                    <label class="ai-label">Or Type Your Question</label>
                    <div style="display: flex; gap: 8px;">
                        <input type="text" id="ai-voice-text-input" class="ai-input-box" placeholder="Type your question here..." style="flex: 1;" />
                        <button id="ai-voice-text-send" class="ai-btn-primary" style="padding: 0 16px;">
                            <i class="fas fa-paper-plane"></i> Ask
                        </button>
                    </div>
                    <p class="ai-helper-text">If voice doesn't work, you can type your question</p>
                </div>
                <div class="ai-action-btns" style="margin-top: 12px;">
                    <input type="file" id="ai-audio-file" class="ai-input-box" accept="audio/*" style="display: none;" />
                    <button id="ai-audio-upload-btn" class="ai-btn-secondary" onclick="document.getElementById('ai-audio-file').click()">
                        <i class="fas fa-file-audio"></i> Or Upload Audio
                    </button>
                </div>
                <div id="ai-voice-output" class="ai-output-area empty">Transcript will appear here...</div>
            </div>
        `;
    }

    createImagePanel() {
        return `
            <div class="ai-tool-panel" data-panel="image">
                <div class="ai-field">
                    <label class="ai-label">Describe the image</label>
                    <textarea id="ai-image-prompt" class="ai-textarea-box" placeholder="Street food banner, menu poster, promotional graphic..."></textarea>
                </div>
                <div class="ai-action-btns">
                    <button id="ai-image-btn" class="ai-btn-primary">
                        <i class="fas fa-magic"></i> Generate
                    </button>
                </div>
                <div id="ai-image-preview" class="ai-image-preview-area empty">Generated image will appear here...</div>
            </div>
        `;
    }

    createCommandPanel() {
        return `
            <div class="ai-tool-panel" data-panel="command">
                <div class="ai-field">
                    <label class="ai-label">Voice Command or Text</label>
                    <textarea id="ai-command-text" class="ai-textarea-box" placeholder="Type or record: 'Update today's special to Rs 120', 'Track my last order', etc."></textarea>
                </div>
                <div class="ai-action-btns">
                    <button id="ai-command-btn" class="ai-btn-primary">
                        <i class="fas fa-cogs"></i> Plan Actions
                    </button>
                </div>
                <div id="ai-command-output" class="ai-output-area empty">Action plan will appear here...</div>
            </div>
        `;
    }

    createSearchPanel() {
        return `
            <div class="ai-tool-panel" data-panel="search">
                <div class="ai-field">
                    <label class="ai-label">Search Query</label>
                    <input type="text" id="ai-search-query" class="ai-input-box" placeholder="Find best biryani, cheap tea stalls, suppliers..." />
                </div>
                <div class="ai-field">
                    <label class="ai-label">Search Type</label>
                    <select id="ai-search-type" class="ai-select-box">
                        <option value="all">All</option>
                        <option value="vendors">Vendors</option>
                        <option value="menu">Menu Items</option>
                        <option value="suppliers">Suppliers</option>
                    </select>
                </div>
                <div class="ai-action-btns">
                    <button id="ai-search-btn" class="ai-btn-primary">
                        <i class="fas fa-search"></i> Search
                    </button>
                </div>
                <div id="ai-search-output" class="ai-output-area empty">Search insights will appear here...</div>
            </div>
        `;
    }

    createAnalyticsPanel() {
        return `
            <div class="ai-tool-panel" data-panel="analytics">
                <div class="ai-field">
                    <label class="ai-label">Sales Data</label>
                    <textarea id="ai-analytics-data" class="ai-textarea-box" placeholder="Paste your sales data (JSON, CSV, or plain text)..."></textarea>
                </div>
                <div class="ai-field">
                    <label class="ai-label">Period</label>
                    <select id="ai-analytics-period" class="ai-select-box">
                        <option value="daily">Daily</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly" selected>Monthly</option>
                        <option value="yearly">Yearly</option>
                    </select>
                </div>
                <div class="ai-action-btns">
                    <button id="ai-analytics-btn" class="ai-btn-primary">
                        <i class="fas fa-chart-line"></i> Analyze
                    </button>
                </div>
                <div id="ai-analytics-output" class="ai-output-area empty">Analytics insights will appear here...</div>
            </div>
        `;
    }

    createSupportPanel() {
        return `
            <div class="ai-tool-panel" data-panel="support">
                <div class="ai-field">
                    <label class="ai-label">Your Question or Issue</label>
                    <textarea id="ai-support-input" class="ai-textarea-box" placeholder="My order is late, payment failed, how to track delivery..."></textarea>
                </div>
                <div class="ai-action-btns">
                    <button id="ai-support-btn" class="ai-btn-primary">
                        <i class="fas fa-paper-plane"></i> Get Help
                    </button>
                </div>
                <div id="ai-support-output" class="ai-output-area empty">Support response will appear here...</div>
            </div>
        `;
    }

    attachEventListeners() {
        // Toggle button
        document.getElementById('ai-assistant-toggle').addEventListener('click', () => this.toggle());
        document.getElementById('ai-close-btn').addEventListener('click', () => this.close());

        // Tab switching
        document.querySelectorAll('.ai-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // Chat
        document.getElementById('ai-chat-btn').addEventListener('click', () => this.handleChat());

        // Document
        document.getElementById('ai-doc-btn').addEventListener('click', () => this.handleDocument());

        // Voice recording
        document.getElementById('ai-record-btn').addEventListener('click', () => this.toggleRecording());
        document.getElementById('ai-audio-file').addEventListener('change', () => this.handleAudioUpload());
        document.getElementById('ai-voice-text-send').addEventListener('click', () => this.handleVoiceTextInput());
        
        // Allow Enter key in voice text input
        document.getElementById('ai-voice-text-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleVoiceTextInput();
            }
        });

        // Image
        document.getElementById('ai-image-btn').addEventListener('click', () => this.handleImage());

        // Command
        document.getElementById('ai-command-btn').addEventListener('click', () => this.handleCommand());

        // Search
        document.getElementById('ai-search-btn').addEventListener('click', () => this.handleSearch());

        // Analytics (vendor only)
        const analyticsBtn = document.getElementById('ai-analytics-btn');
        if (analyticsBtn) {
            analyticsBtn.addEventListener('click', () => this.handleAnalytics());
        }

        // Support (customer only)
        const supportBtn = document.getElementById('ai-support-btn');
        if (supportBtn) {
            supportBtn.addEventListener('click', () => this.handleSupport());
        }
    }

    toggle() {
        this.container.classList.toggle('open');
    }

    close() {
        this.container.classList.remove('open');
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.ai-tab').forEach(tab => tab.classList.remove('active'));
        document.querySelector(`.ai-tab[data-tab="${tabName}"]`).classList.add('active');

        // Update panels
        document.querySelectorAll('.ai-tool-panel').forEach(panel => panel.classList.remove('active'));
        document.querySelector(`.ai-tool-panel[data-panel="${tabName}"]`).classList.add('active');

        this.activeTab = tabName;
    }

    setLoading(btnId, isLoading) {
        const btn = document.getElementById(btnId);
        if (!btn) return;
        if (!btn.dataset.originalText) {
            btn.dataset.originalText = btn.innerHTML;
        }
        btn.disabled = isLoading;
        btn.innerHTML = isLoading ? '<i class="fas fa-spinner fa-spin"></i> Working...' : btn.dataset.originalText;
    }

    // Trim and clean AI text; prefer the last meaningful part
    sanitizeAI(text) {
        if (!text) return '';
        let t = String(text);
        // Strip code blocks and most markdown noise
        t = t.replace(/```[\s\S]*?```/g, ' ')
             .replace(/[\*_`>#~]/g, ' ');
        // Remove common meta/instructional prefixes
        t = t.replace(/^\s*(the\s+system\s+says:?)\s*/i, '')
             .replace(/^\s*(according\s+to\s+system[:,]?)\s*/i, '')
             .replace(/^\s*(as\s+an\s+ai[^.!?:;]*[:.,-]?)\s*/i, '')
             .replace(/^\s*(i'?m\s+an\s+ai[^.!?:;]*[:.,-]?)\s*/i, '');
        // Collapse whitespace
        t = t.replace(/\s+/g, ' ').trim();

        let candidate = '';
        // 1) If there are quotes, take the last quoted phrase
        const quoteRegex = /["'“”‘’]([^"'“”‘’]+)["'“”‘’]/g;
        let qm;
        while ((qm = quoteRegex.exec(t)) !== null) {
            candidate = qm[1].trim();
        }

        // 2) Else, take the text after the last colon
        if (!candidate) {
            const idx = t.lastIndexOf(':');
            if (idx !== -1 && idx + 1 < t.length) {
                candidate = t.slice(idx + 1).trim();
            }
        }

        // 3) Else, take the last sentence
        if (!candidate) {
            const parts = t.split(/(?<=[.!?])\s+/).filter(s => s && /[A-Za-z0-9]/.test(s));
            candidate = parts.length ? parts[parts.length - 1] : t;
        }

        // Remove lingering policy mentions and extra whitespace
        candidate = candidate.replace(/\b(system|policy|instruction|guideline|internal)\b.*$/i, '').trim();
        candidate = candidate.replace(/\s+/g, ' ');

        // Enforce max length
        const MAX = 140;
        if (candidate.length > MAX) candidate = candidate.slice(0, MAX - 1).trimEnd() + '…';
        return candidate;
    }

    async handleChat() {
        const input = document.getElementById('ai-chat-input');
        const output = document.getElementById('ai-chat-output');
        const prompt = input.value.trim();

        if (!prompt) {
            output.textContent = 'Please enter a question.';
            output.classList.remove('empty');
            return;
        }

        this.setLoading('ai-chat-btn', true);
        try {
            // Use the enhanced chatbot API that includes database queries
            const resp = await fetch('/api/chatbot/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: prompt,
                    language: 'en',
                    context: this.conversationHistory || {},
                    session_id: this.getSessionId()
                })
            });
            const data = await resp.json();
            
            if (data.message) {
                // Handle different message types
                if (typeof data.message === 'string') {
                    output.textContent = data.message;
                } else if (data.message.type === 'list' && data.message.items) {
                    output.innerHTML = '<ul>' + data.message.items.map(item => `<li>${item}</li>`).join('') + '</ul>';
                } else {
                    output.textContent = JSON.stringify(data.message);
                }
                
                // Store conversation context
                if (data.context) {
                    this.conversationHistory = data.context;
                }
            } else {
                output.textContent = 'No response received';
            }
            output.classList.remove('empty');
        } catch (err) {
            output.textContent = 'Error: ' + err.message;
            output.classList.remove('empty');
        } finally {
            this.setLoading('ai-chat-btn', false);
        }
    }

    async handleDocument() {
        const fileInput = document.getElementById('ai-doc-file');
        const output = document.getElementById('ai-doc-output');
        const file = fileInput.files[0];

        if (!file) {
            output.textContent = 'Please upload a file.';
            output.classList.remove('empty');
            return;
        }

        this.setLoading('ai-doc-btn', true);
        const fd = new FormData();
        fd.append('file', file);
        fd.append('model', 'qwen-vision');
        fd.append('prompt', 'Extract all key information from this document: merchant, date, items, quantities, prices, subtotal, tax, total.');

        try {
            const resp = await fetch('/api/ai/document', { method: 'POST', body: fd });
            const data = await resp.json();
            output.textContent = data.success ? (data.content || 'No text extracted') : (data.message || 'Request failed');
            output.classList.remove('empty');
        } catch (err) {
            output.textContent = 'Error: ' + err.message;
            output.classList.remove('empty');
        } finally {
            this.setLoading('ai-doc-btn', false);
        }
    }

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        const output = document.getElementById('ai-voice-output');
        const voiceStatus = document.getElementById('ai-voice-status');
        
        try {
            // Check browser and connection info
            const isSecure = window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
            const hasNavigator = 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices;
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            
            console.log('🎤 Voice Recording Debug Info:');
            console.log('- Protocol:', window.location.protocol);
            console.log('- Hostname:', window.location.hostname);
            console.log('- Is Secure:', isSecure);
            console.log('- Has MediaDevices:', hasNavigator);
            console.log('- Speech Recognition Available:', !!SpeechRecognition);
            console.log('- Online:', navigator.onLine);
            
            // Show detailed error message
            if (!isSecure) {
                voiceStatus.innerHTML = `<strong>⚠️ Connection Not Secure</strong><br>
                    Voice recognition requires HTTPS or localhost.<br>
                    <strong>Current URL:</strong> ${window.location.protocol}//${window.location.host}<br>
                    <br><strong>Solution:</strong> Use the text input below instead!`;
                voiceStatus.style.display = 'block';
                voiceStatus.style.color = '#ef4444';
                // Scroll to text input
                document.getElementById('ai-voice-text-input').focus();
                return;
            }
            
            if (!hasNavigator) {
                voiceStatus.innerHTML = `<strong>❌ Microphone Not Supported</strong><br>
                    Your browser doesn't support microphone access.<br>
                    <br><strong>Solution:</strong> Use the text input below!`;
                voiceStatus.style.display = 'block';
                voiceStatus.style.color = '#ef4444';
                document.getElementById('ai-voice-text-input').focus();
                return;
            }
            
            if (!SpeechRecognition) {
                voiceStatus.innerHTML = `<strong>❌ Speech Recognition Not Supported</strong><br>
                    Please use <strong>Chrome</strong>, <strong>Edge</strong>, or <strong>Safari</strong>.<br>
                    <br><strong>Solution:</strong> Use the text input below!`;
                voiceStatus.style.display = 'block';
                voiceStatus.style.color = '#ef4444';
                document.getElementById('ai-voice-text-input').focus();
                return;
            }
            
            if (!navigator.onLine) {
                voiceStatus.innerHTML = `<strong>❌ No Internet Connection</strong><br>
                    Speech recognition requires internet connection.<br>
                    <br><strong>Solution:</strong> Use the text input below!`;
                voiceStatus.style.display = 'block';
                voiceStatus.style.color = '#ef4444';
                document.getElementById('ai-voice-text-input').focus();
                return;
            }
            
            // Request microphone permission
            try {
                await navigator.mediaDevices.getUserMedia({ audio: true });
                console.log('✅ Microphone permission granted');
            } catch (micError) {
                console.error('❌ Microphone permission denied:', micError);
                voiceStatus.innerHTML = `<strong>🎤 Microphone Access Denied</strong><br>
                    Please allow microphone access in your browser settings.<br>
                    <br><strong>Solution:</strong> Use the text input below!`;
                voiceStatus.style.display = 'block';
                voiceStatus.style.color = '#ef4444';
                document.getElementById('ai-voice-text-input').focus();
                return;
            }
            
            // Use Web Speech API for real-time transcription
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';
            this.recognition.maxAlternatives = 1;
            
            // Store transcript as instance variable
            this.finalTranscript = '';
            this.interimTranscript = '';
            
            this.recognition.onstart = () => {
                console.log('Speech recognition started');
                voiceStatus.textContent = 'Listening... Speak now';
                voiceStatus.style.display = 'block';
                voiceStatus.style.color = '#10b981';
            };
            
            this.recognition.onresult = (event) => {
                this.interimTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        this.finalTranscript += transcript + ' ';
                    } else {
                        this.interimTranscript += transcript;
                    }
                }
                
                // Display live transcription
                output.innerHTML = `<div style="padding: 10px; background: #f0f9ff; border-left: 3px solid #3b82f6; border-radius: 4px;">
                    <strong style="color: #1e40af;">Transcribing...</strong><br>
                    <span style="color: #334155;">${this.finalTranscript}</span>
                    <span style="color: #94a3b8; font-style: italic;">${this.interimTranscript}</span>
                </div>`;
                output.classList.remove('empty');
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                let errorMessage = 'Error: ';
                switch(event.error) {
                    case 'network':
                        errorMessage += 'Network error. Please check your internet connection.';
                        break;
                    case 'not-allowed':
                        errorMessage += 'Microphone access denied. Please allow microphone access.';
                        break;
                    case 'no-speech':
                        errorMessage += 'No speech detected. Please speak clearly.';
                        break;
                    case 'audio-capture':
                        errorMessage += 'No microphone found. Please connect a microphone.';
                        break;
                    default:
                        errorMessage += event.error + '. Please try again.';
                }
                voiceStatus.textContent = errorMessage;
                voiceStatus.style.color = '#ef4444';
                this.stopRecording();
            };
            
            this.recognition.onend = async () => {
                if (this.isRecording) {
                    // If stopped intentionally, process the final transcript
                    if (this.finalTranscript && this.finalTranscript.trim()) {
                        voiceStatus.textContent = 'Getting AI answer...';
                        voiceStatus.style.color = '#6366f1';
                        
                        try {
                            // Get AI response using chatbot API
                            const resp = await fetch('/api/chatbot/message', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    message: this.finalTranscript.trim(),
                                    language: 'en',
                                    context: {},
                                    session_id: this.getSessionId()
                                })
                            });
                            const data = await resp.json();
                            
                            if (data.message) {
                                const answer = typeof data.message === 'string' ? data.message : JSON.stringify(data.message);
                                output.innerHTML = `<div style="margin-bottom: 15px; padding: 10px; background: #f0f9ff; border-left: 3px solid #3b82f6; border-radius: 4px;">
                                    <strong style="color: #1e40af;">You asked:</strong><br>
                                    <span style="color: #334155;">${this.finalTranscript.trim()}</span>
                                </div>
                                <div style="padding: 10px; background: #f0fdf4; border-left: 3px solid #10b981; border-radius: 4px;">
                                    <strong style="color: #065f46;">AI Answer:</strong><br>
                                    <span style="color: #334155; white-space: pre-wrap;">${answer}</span>
                                </div>`;
                            } else {
                                output.textContent = 'No response received';
                            }
                            voiceStatus.style.display = 'none';
                        } catch (err) {
                            output.innerHTML += `<div style="padding: 10px; background: #fef2f2; border-left: 3px solid #ef4444; border-radius: 4px; color: #991b1b; margin-top: 10px;">
                                Error getting answer: ${err.message}
                            </div>`;
                            voiceStatus.style.display = 'none';
                        }
                    }
                }
            };
            
            this.recognition.start();
            this.isRecording = true;

            // Update UI
            const recordBtn = document.getElementById('ai-record-btn');
            const recordLabel = document.getElementById('ai-record-label');
            const recordTimer = document.getElementById('ai-record-timer');

            recordBtn.classList.add('recording');
            recordLabel.textContent = 'Stop Recording';
            recordTimer.style.display = 'inline';
            voiceStatus.textContent = 'Listening... Speak now';
            voiceStatus.style.display = 'block';
            voiceStatus.style.color = '#10b981';

            // Start timer
            this.recordingStartTime = Date.now();
            this.recordingTimer = setInterval(() => {
                const elapsed = Math.floor((Date.now() - this.recordingStartTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                recordTimer.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            }, 1000);

        } catch (err) {
            console.error('Speech recognition error:', err);
            const voiceStatus = document.getElementById('ai-voice-status');
            voiceStatus.textContent = 'Error starting voice recognition. Please try again.';
            voiceStatus.style.display = 'block';
            voiceStatus.style.color = '#ef4444';
        }
    }

    stopRecording() {
        if (this.recognition) {
            this.recognition.stop();
            this.recognition = null;
        }
        this.isRecording = false;
        
        // Reset transcripts
        this.finalTranscript = '';
        this.interimTranscript = '';

        // Update UI
        const recordBtn = document.getElementById('ai-record-btn');
        const recordLabel = document.getElementById('ai-record-label');
        const recordTimer = document.getElementById('ai-record-timer');

        recordBtn.classList.remove('recording');
        recordLabel.textContent = 'Start Recording';
        recordTimer.style.display = 'none';

        // Clear timer
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
    }

    async handleVoiceTextInput() {
        const textInput = document.getElementById('ai-voice-text-input');
        const output = document.getElementById('ai-voice-output');
        const voiceStatus = document.getElementById('ai-voice-status');
        const question = textInput.value.trim();

        if (!question) {
            voiceStatus.textContent = 'Please type a question first.';
            voiceStatus.style.display = 'block';
            voiceStatus.style.color = '#ef4444';
            setTimeout(() => {
                voiceStatus.style.display = 'none';
            }, 3000);
            return;
        }

        // Show processing status
        voiceStatus.textContent = 'Getting AI answer...';
        voiceStatus.style.display = 'block';
        voiceStatus.style.color = '#6366f1';

        // Show question in output
        output.innerHTML = `<div style="padding: 10px; background: #f0f9ff; border-left: 3px solid #3b82f6; border-radius: 4px;">
            <strong style="color: #1e40af;">You asked:</strong><br>
            <span style="color: #334155;">${question}</span>
        </div>
        <div style="color: #64748b; font-style: italic; margin-top: 10px;">Thinking...</div>`;
        output.classList.remove('empty');

        try {
            // Get AI response using chatbot API
            const resp = await fetch('/api/chatbot/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: question,
                    language: 'en',
                    context: {},
                    session_id: this.getSessionId()
                })
            });
            const data = await resp.json();
            
            if (data.message) {
                const answer = typeof data.message === 'string' ? data.message : JSON.stringify(data.message);
                output.innerHTML = `<div style="margin-bottom: 15px; padding: 10px; background: #f0f9ff; border-left: 3px solid #3b82f6; border-radius: 4px;">
                    <strong style="color: #1e40af;">You asked:</strong><br>
                    <span style="color: #334155;">${question}</span>
                </div>
                <div style="padding: 10px; background: #f0fdf4; border-left: 3px solid #10b981; border-radius: 4px;">
                    <strong style="color: #065f46;">AI Answer:</strong><br>
                    <span style="color: #334155; white-space: pre-wrap;">${answer}</span>
                </div>`;
            } else {
                output.textContent = 'No response received';
            }
            voiceStatus.style.display = 'none';
            textInput.value = ''; // Clear input
        } catch (err) {
            output.innerHTML += `<div style="padding: 10px; background: #fef2f2; border-left: 3px solid #ef4444; border-radius: 4px; color: #991b1b; margin-top: 10px;">
                Error getting answer: ${err.message}
            </div>`;
            voiceStatus.style.display = 'none';
        }
    }

    async handleAudioUpload() {
        const fileInput = document.getElementById('ai-audio-file');
        const output = document.getElementById('ai-voice-output');
        const voiceStatus = document.getElementById('ai-voice-status');
        const file = fileInput.files[0];

        if (!file) return;

        voiceStatus.textContent = 'Transcribing audio...';
        voiceStatus.style.display = 'block';
        voiceStatus.style.color = '#6366f1';

        const fd = new FormData();
        fd.append('audio', file);
        fd.append('model', 'whisper-large');

        try {
            // Step 1: Transcribe audio
            const resp = await fetch('/api/ai/audio', { method: 'POST', body: fd });
            const data = await resp.json();
            
            if (!data.success || !data.text) {
                output.textContent = data.message || 'Transcription failed';
                output.classList.remove('empty');
                voiceStatus.style.display = 'none';
                return;
            }

            const transcript = data.text;
            
            // Show transcript first
            output.innerHTML = `<div style="margin-bottom: 15px; padding: 10px; background: #f0f9ff; border-left: 3px solid #3b82f6; border-radius: 4px;">
                <strong style="color: #1e40af;">You asked:</strong><br>
                <span style="color: #334155;">${transcript}</span>
            </div>
            <div style="color: #64748b; font-style: italic;">Getting answer...</div>`;
            output.classList.remove('empty');

            // Step 2: Get GPT answer
            voiceStatus.textContent = 'Getting AI answer...';
            
            const chatResp = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    prompt: transcript, 
                    model: 'openai/gpt-oss-120b', 
                    temperature: 0.7 
                })
            });
            const chatData = await chatResp.json();
            
            // Show both transcript and answer
            if (chatData.success && chatData.content) {
                output.innerHTML = `<div style="margin-bottom: 15px; padding: 10px; background: #f0f9ff; border-left: 3px solid #3b82f6; border-radius: 4px;">
                    <strong style="color: #1e40af;">You asked:</strong><br>
                    <span style="color: #334155;">${transcript}</span>
                </div>
                <div style="padding: 10px; background: #f0fdf4; border-left: 3px solid #10b981; border-radius: 4px;">
                    <strong style="color: #065f46;">AI Answer:</strong><br>
                    <span style="color: #334155; white-space: pre-wrap;">${chatData.content}</span>
                </div>`;
            } else {
                output.innerHTML = `<div style="margin-bottom: 15px; padding: 10px; background: #f0f9ff; border-left: 3px solid #3b82f6; border-radius: 4px;">
                    <strong style="color: #1e40af;">You asked:</strong><br>
                    <span style="color: #334155;">${transcript}</span>
                </div>
                <div style="padding: 10px; background: #fef2f2; border-left: 3px solid #ef4444; border-radius: 4px; color: #991b1b;">
                    Failed to get answer: ${chatData.message || 'Unknown error'}
                </div>`;
            }
            
            voiceStatus.style.display = 'none';
        } catch (err) {
            output.textContent = 'Error: ' + err.message;
            output.classList.remove('empty');
            voiceStatus.style.display = 'none';
        }
    }

    async handleImage() {
        const promptInput = document.getElementById('ai-image-prompt');
        const preview = document.getElementById('ai-image-preview');
        const prompt = promptInput.value.trim();

        if (!prompt) {
            preview.textContent = 'Please describe the image you want.';
            preview.classList.remove('empty');
            return;
        }

        this.setLoading('ai-image-btn', true);
        try {
            const resp = await fetch('/api/ai/image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt, model: 'stable-diffusion' })
            });
            const data = await resp.json();
            if (data.success && data.image_b64) {
                preview.innerHTML = `<img src="data:image/png;base64,${data.image_b64}" alt="Generated image" />`;
                preview.classList.remove('empty');
            } else {
                preview.textContent = data.message || 'Image generation failed';
                preview.classList.remove('empty');
            }
        } catch (err) {
            preview.textContent = 'Error: ' + err.message;
            preview.classList.remove('empty');
        } finally {
            this.setLoading('ai-image-btn', false);
        }
    }

    async handleCommand() {
        const textInput = document.getElementById('ai-command-text');
        const output = document.getElementById('ai-command-output');
        const command = textInput.value.trim();

        if (!command) {
            output.textContent = 'Please enter a command.';
            output.classList.remove('empty');
            return;
        }

        this.setLoading('ai-command-btn', true);
        try {
            const resp = await fetch('/api/ai/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command })
            });
            const data = await resp.json();
            if (data.success) {
                const parts = [];
                if (data.transcript) parts.push('Transcript: ' + data.transcript);
                if (data.plan) parts.push('Plan:\n' + data.plan);
                output.textContent = parts.join('\n\n');
            } else {
                output.textContent = data.message || 'Request failed';
            }
            output.classList.remove('empty');
        } catch (err) {
            output.textContent = 'Error: ' + err.message;
            output.classList.remove('empty');
        } finally {
            this.setLoading('ai-command-btn', false);
        }
    }

    async handleSearch() {
        const queryInput = document.getElementById('ai-search-query');
        const typeSelect = document.getElementById('ai-search-type');
        const output = document.getElementById('ai-search-output');
        const query = queryInput.value.trim();
        const searchType = typeSelect.value;

        if (!query) {
            output.textContent = 'Please enter a search query.';
            output.classList.remove('empty');
            return;
        }

        this.setLoading('ai-search-btn', true);
        try {
            const resp = await fetch('/api/ai/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, type: searchType, model: 'openai/gpt-oss-120b' })
            });
            const data = await resp.json();
            output.textContent = data.success ? (data.analysis || 'No insights') : (data.message || 'Search failed');
            output.classList.remove('empty');
        } catch (err) {
            output.textContent = 'Error: ' + err.message;
            output.classList.remove('empty');
        } finally {
            this.setLoading('ai-search-btn', false);
        }
    }

    async handleAnalytics() {
        const dataInput = document.getElementById('ai-analytics-data');
        const periodSelect = document.getElementById('ai-analytics-period');
        const output = document.getElementById('ai-analytics-output');
        const salesData = dataInput.value.trim();
        const period = periodSelect.value;

        if (!salesData) {
            output.textContent = 'Please provide sales data.';
            output.classList.remove('empty');
            return;
        }

        this.setLoading('ai-analytics-btn', true);
        try {
            const resp = await fetch('/api/ai/analytics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sales_data: salesData, period, model: 'openai/gpt-oss-120b' })
            });
            const data = await resp.json();
            output.textContent = data.success ? (data.insights || 'No insights') : (data.message || 'Analysis failed');
            output.classList.remove('empty');
        } catch (err) {
            output.textContent = 'Error: ' + err.message;
            output.classList.remove('empty');
        } finally {
            this.setLoading('ai-analytics-btn', false);
        }
    }

    async handleSupport() {
        const input = document.getElementById('ai-support-input');
        const output = document.getElementById('ai-support-output');
        const message = input.value.trim();

        if (!message) {
            output.textContent = 'Please describe your issue.';
            output.classList.remove('empty');
            return;
        }

        this.setLoading('ai-support-btn', true);
        try {
            const resp = await fetch('/api/ai/support', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, model: 'openai/gpt-oss-120b' })
            });
            const data = await resp.json();
            output.textContent = data.success ? (data.response || 'No response') : (data.message || 'Support request failed');
            output.classList.remove('empty');
        } catch (err) {
            output.textContent = 'Error: ' + err.message;
            output.classList.remove('empty');
        } finally {
            this.setLoading('ai-support-btn', false);
        }
    }

    getSessionId() {
        let sessionId = localStorage.getItem('ai_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('ai_session_id', sessionId);
        }
        return sessionId;
    }
}

// Initialize AI Assistant when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.aiAssistant = new AIAssistant();
    });
} else {
    window.aiAssistant = new AIAssistant();
}
