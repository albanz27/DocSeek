(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        
        initScrollEffects();
        initScrollToTop();
        initNavbarBehavior();
        initAlertAutoDismiss();
        initTooltips();
        initDropdownEnhancements();
        initFormValidation();
        
    });


    // Aggiungi effetti visivi allo scroll
    function initScrollEffects() {
        const navbar = document.querySelector('.navbar');
        if (!navbar) return;

        let lastScroll = 0;
        const scrollThreshold = 50;

        window.addEventListener('scroll', function() {
            const currentScroll = window.pageYOffset;

            // Aggiungi classe "scrolled" quando si scrolla
            if (currentScroll > scrollThreshold) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }

            lastScroll = currentScroll;
        }, { passive: true });
    }


     // Mostra/nascondi il bottone "torna su" basato sullo scroll
    function initScrollToTop() {
        const scrollBtn = document.getElementById('scrollTopBtn');
        if (!scrollBtn) return;

        // Mostra il bottone dopo 300px di scroll
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                scrollBtn.classList.add('show');
            } else {
                scrollBtn.classList.remove('show');
            }
        }, { passive: true });

        scrollBtn.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }


    // Gestisce il comportamento della navbar 
    function initNavbarBehavior() {
        const navbarCollapse = document.getElementById('navbarNav');
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        
        if (!navbarCollapse) return;

        // Chiudi il menu mobile dopo il click su un link
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth < 992) { // Solo su mobile
                    const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                    if (bsCollapse) {
                        bsCollapse.hide();
                    }
                }
            });
        });

        // Evidenzia il link attivo
        highlightActiveNavLink();
    }

    
    // Evidenzia il link della navbar della pagina corrente 
    function highlightActiveNavLink() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

        navLinks.forEach(link => {
            const linkPath = new URL(link.href).pathname;
            
            if (linkPath === currentPath) {
                link.classList.add('active');
                link.setAttribute('aria-current', 'page');
            } else {
                link.classList.remove('active');
                link.removeAttribute('aria-current');
            }
        });
    }


    // Chiudi automaticamente gli alert dopo 5 secondi
    function initAlertAutoDismiss() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        
        alerts.forEach(alert => {
            setTimeout(() => {
                const bsAlert = bootstrap.Alert.getInstance(alert) || new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000); // 5 secondi
        });
    }


     // Inizializza i tooltip di Bootstrap per tutti gli elementi con data-bs-toggle="tooltip"
    function initTooltips() {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }


    // Migliora l'UX dei dropdown
    function initDropdownEnhancements() {
        const dropdownToggles = document.querySelectorAll('.dropdown-toggle');

        dropdownToggles.forEach(toggle => {
            // Aggiungi animazione al click
            toggle.addEventListener('click', function() {
                this.classList.add('clicked');
                setTimeout(() => {
                    this.classList.remove('clicked');
                }, 300);
            });
        });

        // Chiudi dropdown al click fuori
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.dropdown')) {
                const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
                openDropdowns.forEach(dropdown => {
                    const bsDropdown = bootstrap.Dropdown.getInstance(dropdown.previousElementSibling);
                    if (bsDropdown) bsDropdown.hide();
                });
            }
        });
    }


    // Validazione HTML5 migliorata per i form
    function initFormValidation() {
        const forms = document.querySelectorAll('.needs-validation');

        forms.forEach(form => {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                    
                    // Scroll al primo campo non valido
                    const firstInvalid = form.querySelector(':invalid');
                    if (firstInvalid) {
                        firstInvalid.focus();
                        firstInvalid.scrollIntoView({ 
                            behavior: 'smooth', 
                            block: 'center' 
                        });
                    }
                }
                
                form.classList.add('was-validated');
            }, false);
        });
    }


    //Mostra un loading spinner globale
     
    window.showLoading = function() {
        let overlay = document.querySelector('.spinner-overlay');
        
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'spinner-overlay';
            overlay.innerHTML = '<div class="spinner"></div>';
            document.body.appendChild(overlay);
        }
        
        overlay.classList.add('active');
    };

    // Nascondi il loading spinner     
    window.hideLoading = function() {
        const overlay = document.querySelector('.spinner-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    };


    window.showToast = function(message, type = 'info', duration = 3000) {
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
            `;
            document.body.appendChild(toastContainer);
        }

        // Crea il toast
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show shadow-lg`;
        toast.style.cssText = 'min-width: 250px; margin-bottom: 10px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        toastContainer.appendChild(toast);

        // Auto-rimuovi dopo duration
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 150);
        }, duration);
    };

 
    window.copyToClipboard = function(text) {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('Copied to clipboard!', 'success', 2000);
            });
        } else {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                showToast('Copied to clipboard!', 'success', 2000);
            } catch (err) {
                showToast('Failed to copy', 'error', 2000);
            }
            textArea.remove();
        }
    };


    window.confirmAction = function(message, callback) {
        if (confirm(message)) {
            if (typeof callback === 'function') {
                callback();
            }
            return true;
        }
        return false;
    };


    window.debounce = function(func, wait = 300) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };


    window.addEventListener('load', function() {
        if ('performance' in window) {
            const perfData = window.performance.timing;
            const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
        }
    });


    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
            openDropdowns.forEach(dropdown => {
                const toggle = dropdown.previousElementSibling;
                if (toggle) {
                    const bsDropdown = bootstrap.Dropdown.getInstance(toggle);
                    if (bsDropdown) bsDropdown.hide();
                }
            });
        }
    });

})();