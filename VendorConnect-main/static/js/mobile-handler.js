/**
 * Mobile Responsive Handler
 * Handles mobile-specific interactions and optimizations
 */

class MobileHandler {
    constructor() {
        this.isMobile = window.innerWidth <= 768;
        this.sidebarOpen = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.handleOrientationChange();
        this.setupTouchOptimizations();
        this.createMobileToggle();
    }

    setupEventListeners() {
        window.addEventListener('resize', () => this.handleResize());
        window.addEventListener('orientationchange', () => this.handleOrientationChange());
        document.addEventListener('click', (e) => this.handleDocumentClick(e));
    }

    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth <= 768;
        
        if (wasMobile !== this.isMobile) {
            this.closeSidebar();
            if (!this.isMobile) {
                this.showSidebar();
            }
        }
    }

    handleOrientationChange() {
        // Adjust viewport on orientation change
        setTimeout(() => {
            window.scrollTo(0, 0);
            this.adjustLayout();
        }, 100);
    }

    adjustLayout() {
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');
        
        if (sidebar && mainContent) {
            if (this.isMobile) {
                sidebar.classList.remove('mobile-active');
                this.sidebarOpen = false;
            }
        }
    }

    createMobileToggle() {
        if (this.isMobile) {
            let toggle = document.querySelector('.sidebar-toggle');
            if (!toggle) {
                toggle = document.createElement('button');
                toggle.className = 'sidebar-toggle';
                toggle.innerHTML = '<i class="fas fa-bars"></i>';
                toggle.setAttribute('aria-label', 'Toggle menu');
                document.body.insertBefore(toggle, document.body.firstChild);
                toggle.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleSidebar();
                });
            }
        }
    }

    toggleSidebar() {
        if (this.sidebarOpen) {
            this.closeSidebar();
        } else {
            this.openSidebar();
        }
    }

    openSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.add('mobile-active');
            this.sidebarOpen = true;
            document.body.style.overflow = 'hidden';
        }
    }

    closeSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.remove('mobile-active');
            this.sidebarOpen = false;
            document.body.style.overflow = '';
        }
    }

    showSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.add('mobile-active');
            this.sidebarOpen = true;
        }
    }

    handleDocumentClick(e) {
        const sidebar = document.querySelector('.sidebar');
        const toggle = document.querySelector('.sidebar-toggle');
        
        if (this.isMobile && this.sidebarOpen) {
            if (sidebar && !sidebar.contains(e.target) && 
                toggle && !toggle.contains(e.target)) {
                this.closeSidebar();
            }
        }
    }

    setupTouchOptimizations() {
        // Prevent double-tap zoom on buttons
        document.addEventListener('touchstart', function(e) {
            if (e.target.matches('button, a, input, select, textarea')) {
                e.target.style.touchAction = 'manipulation';
            }
        }, false);

        // Add feedback for touch interactions
        document.addEventListener('touchstart', function(e) {
            if (e.target.matches('.btn, button, [role="button"]')) {
                e.target.style.opacity = '0.8';
            }
        }, false);

        document.addEventListener('touchend', function(e) {
            if (e.target.matches('.btn, button, [role="button"]')) {
                e.target.style.opacity = '1';
            }
        }, false);
    }

    // Detect if device is in landscape mode
    isLandscape() {
        return window.innerHeight < window.innerWidth;
    }

    // Get safe area insets for notches
    getSafeAreaInsets() {
        return {
            top: parseInt(getComputedStyle(document.documentElement).getPropertyValue('env(safe-area-inset-top)')) || 0,
            right: parseInt(getComputedStyle(document.documentElement).getPropertyValue('env(safe-area-inset-right)')) || 0,
            bottom: parseInt(getComputedStyle(document.documentElement).getPropertyValue('env(safe-area-inset-bottom)')) || 0,
            left: parseInt(getComputedStyle(document.documentElement).getPropertyValue('env(safe-area-inset-left)')) || 0
        };
    }

    // Fix for viewport height on mobile (address bar)
    setupViewportHeightFix() {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
        window.addEventListener('resize', () => {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        });
    }
}

// Initialize mobile handler when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.mobileHandler = new MobileHandler();
        window.mobileHandler.setupViewportHeightFix();
    });
} else {
    window.mobileHandler = new MobileHandler();
    window.mobileHandler.setupViewportHeightFix();
}

// Prevent default pinch zoom on mobile
document.addEventListener('touchmove', function(e) {
    if (e.touches.length > 1) {
        e.preventDefault();
    }
}, { passive: false });
