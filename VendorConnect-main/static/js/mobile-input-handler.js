/**
 * Mobile Input and Touch Handler
 * Fixes keyboard and touch responsiveness issues on mobile devices
 */

class MobileInputHandler {
    constructor() {
        this.init();
    }

    init() {
        this.setupTouchEventListeners();
        this.setupKeyboardOptimization();
        this.setupInputFocus();
        this.setupFormSubmission();
        this.setupButtonTouchFeedback();
        this.preventDoubleZoom();
    }

    /**
     * Setup touch event listeners as primary input method
     */
    setupTouchEventListeners() {
        // Convert click-only buttons to touch-friendly
        document.addEventListener('touchstart', (e) => {
            if (this.isClickableElement(e.target)) {
                e.target.style.backgroundColor = this.getHoverColor(e.target);
                e.target.style.opacity = '0.8';
            }
        }, { passive: true });

        document.addEventListener('touchend', (e) => {
            if (this.isClickableElement(e.target)) {
                e.target.style.backgroundColor = '';
                e.target.style.opacity = '1';
            }
        }, { passive: true });

        // Add touch feedback to all buttons
        document.querySelectorAll('button, [role="button"], a.btn, .btn-link').forEach(btn => {
            btn.addEventListener('touchstart', (e) => {
                btn.classList.add('touch-active');
            }, { passive: true });

            btn.addEventListener('touchend', (e) => {
                btn.classList.remove('touch-active');
            }, { passive: true });
        });
    }

    /**
     * Optimize keyboard behavior on mobile
     */
    setupKeyboardOptimization() {
        const inputs = document.querySelectorAll('input, textarea, select');

        inputs.forEach(input => {
            // Prevent zoom on input focus (font-size 16px minimum)
            if (input.tagName === 'INPUT' || input.tagName === 'TEXTAREA') {
                const computedStyle = window.getComputedStyle(input);
                const fontSize = parseInt(computedStyle.fontSize);
                if (fontSize < 16) {
                    input.style.fontSize = '16px';
                }
            }

            // Handle Enter key for forms
            if (input.tagName === 'INPUT' && input.type !== 'checkbox' && input.type !== 'radio') {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        const form = input.closest('form');
                        if (form) {
                            this.submitForm(form);
                        }
                    }
                });
            }

            // Handle Tab key navigation
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    // Allow natural tab behavior
                    return true;
                }
            });

            // Improve mobile text selection
            input.addEventListener('focus', () => {
                // Scroll input into view
                setTimeout(() => {
                    input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 100);
            });
        });
    }

    /**
     * Handle input focus and virtual keyboard
     */
    setupInputFocus() {
        const inputs = document.querySelectorAll('input:not([type="hidden"]), textarea, select');

        inputs.forEach(input => {
            // Prevent automatic zoom on focus
            input.addEventListener('focus', (e) => {
                // Set minimum font size to prevent zoom
                const fontSize = parseInt(window.getComputedStyle(input).fontSize);
                if (fontSize < 16) {
                    input.style.fontSize = '16px';
                }
            });

            // Handle blur
            input.addEventListener('blur', (e) => {
                // Restore viewport if needed
                if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
                    setTimeout(() => {
                        window.scrollTo(0, 0);
                    }, 300);
                }
            });

            // Select all text on focus for easier editing
            input.addEventListener('focus', (e) => {
                if (input.type === 'text' || input.type === 'email' || input.type === 'password') {
                    setTimeout(() => {
                        input.select();
                    }, 0);
                }
            });
        });
    }

    /**
     * Setup form submission handlers
     */
    setupFormSubmission() {
        const forms = document.querySelectorAll('form');

        forms.forEach(form => {
            // Prevent double submission on mobile
            let isSubmitting = false;

            form.addEventListener('submit', (e) => {
                if (isSubmitting) {
                    e.preventDefault();
                    return;
                }

                isSubmitting = true;

                // Disable all submit buttons
                const submitButtons = form.querySelectorAll('button[type="submit"]');
                submitButtons.forEach(btn => {
                    btn.disabled = true;
                    btn.style.opacity = '0.6';
                });

                // Re-enable after 3 seconds (failsafe)
                setTimeout(() => {
                    isSubmitting = false;
                    submitButtons.forEach(btn => {
                        btn.disabled = false;
                        btn.style.opacity = '1';
                    });
                }, 3000);
            });

            // Handle form validation errors
            form.addEventListener('invalid', (e) => {
                e.preventDefault();
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, true);
        });
    }

    /**
     * Add touch feedback to buttons
     */
    setupButtonTouchFeedback() {
        const style = document.createElement('style');
        style.textContent = `
            .touch-active {
                opacity: 0.7 !important;
                transform: scale(0.98) !important;
                transition: all 0.1s ease !important;
            }

            button, [role="button"], a.btn, .btn-link, .action-btn {
                -webkit-user-select: none;
                user-select: none;
                -webkit-touch-callout: none;
                touch-action: manipulation;
            }

            input:focus, textarea:focus, select:focus {
                outline: 2px solid #667eea;
                outline-offset: 2px;
            }

            /* Mobile safe area support */
            @supports (padding: max(0px)) {
                body {
                    padding-left: max(0px, env(safe-area-inset-left));
                    padding-right: max(0px, env(safe-area-inset-right));
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Prevent double-tap zoom on buttons
     */
    preventDoubleZoom() {
        let lastTouchEnd = 0;

        document.addEventListener('touchend', (e) => {
            const now = Date.now();
            if (now - lastTouchEnd <= 300 && this.isClickableElement(e.target)) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);

        // Add touch-action CSS to prevent double-tap zoom
        document.querySelectorAll('button, a, [role="button"]').forEach(el => {
            el.style.touchAction = 'manipulation';
        });
    }

    /**
     * Check if element is clickable
     */
    isClickableElement(element) {
        if (!element) return false;
        
        const clickableSelectors = [
            'button', 'a', '[role="button"]', '[onclick]', 
            'input[type="button"]', 'input[type="submit"]', 
            'input[type="radio"]', 'input[type="checkbox"]',
            '.btn', '.action-btn', '.quick-action-btn'
        ];

        return clickableSelectors.some(selector => element.matches(selector));
    }

    /**
     * Get hover color for element
     */
    getHoverColor(element) {
        const computedStyle = window.getComputedStyle(element);
        const bgColor = computedStyle.backgroundColor;
        
        // Darken the background color on touch
        if (bgColor && bgColor !== 'rgba(0, 0, 0, 0)') {
            return bgColor;
        }
        return '#f0f0f0';
    }

    /**
     * Submit form with proper handling
     */
    submitForm(form) {
        if (form.checkValidity() === false) {
            form.reportValidity();
            return false;
        }
        form.submit();
    }

    /**
     * Handle mobile keyboard visibility
     */
    handleKeyboardVisibility() {
        const initialHeight = window.innerHeight;

        window.addEventListener('resize', () => {
            const currentHeight = window.innerHeight;
            if (currentHeight < initialHeight * 0.75) {
                // Keyboard is likely open
                document.body.classList.add('keyboard-open');
            } else {
                // Keyboard is likely closed
                document.body.classList.remove('keyboard-open');
            }
        });
    }

    /**
     * Fix for iOS Safari address bar height changes
     */
    fixIOSSafari() {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);

        window.addEventListener('resize', () => {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.mobileInputHandler = new MobileInputHandler();
    });
} else {
    window.mobileInputHandler = new MobileInputHandler();
}

// Handle dynamic content
const observer = new MutationObserver(() => {
    if (window.mobileInputHandler) {
        window.mobileInputHandler.setupTouchEventListeners();
        window.mobileInputHandler.setupInputFocus();
        window.mobileInputHandler.setupFormSubmission();
        window.mobileInputHandler.preventDoubleZoom();
    }
});

observer.observe(document.body, { childList: true, subtree: true });
