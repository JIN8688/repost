/**
 * ===========================================
 * Repost - 공통 JavaScript (Common JS)
 * ===========================================
 * 
 * 모든 페이지에서 사용되는 공통 함수와 이벤트 핸들러
 * - 헤더 동작, 스크롤 효과, 유틸리티 함수
 * 
 * @version 1.0.0
 * @author Repost Team
 */

/* ===========================================
   1. 초기화
   =========================================== */
(function() {
    'use strict';
    
    console.log('🚀 Repost Common JS Loaded');
    
    // DOM이 로드되면 초기화
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        initHeader();
        initSmoothScroll();
        initLazyLoad();
        initAccessibility();
    }
    
    /* ===========================================
       2. 헤더 관련 기능
       =========================================== */
    function initHeader() {
        const header = document.querySelector('.site-header');
        const hamburger = document.querySelector('.header-hamburger');
        const mobileMenu = document.querySelector('.header-mobile-menu');
        
        if (!header) return;
        
        // 스크롤 시 헤더 스타일 변경
        let lastScroll = 0;
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            
            if (currentScroll > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
            
            lastScroll = currentScroll;
        });
        
        // 햄버거 메뉴 토글
        if (hamburger && mobileMenu) {
            hamburger.addEventListener('click', () => {
                hamburger.classList.toggle('active');
                mobileMenu.classList.toggle('active');
                document.body.style.overflow = mobileMenu.classList.contains('active') ? 'hidden' : '';
            });
            
            // 메뉴 아이템 클릭 시 메뉴 닫기
            const menuLinks = mobileMenu.querySelectorAll('a');
            menuLinks.forEach(link => {
                link.addEventListener('click', () => {
                    hamburger.classList.remove('active');
                    mobileMenu.classList.remove('active');
                    document.body.style.overflow = '';
                });
            });
        }
        
        // 현재 페이지 활성화 표시
        highlightCurrentPage();
    }
    
    function highlightCurrentPage() {
        const currentPath = window.location.pathname;
        const menuLinks = document.querySelectorAll('.header-menu-link, .header-mobile-menu-link');
        
        menuLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }
    
    /* ===========================================
       3. 스무스 스크롤
       =========================================== */
    function initSmoothScroll() {
        const links = document.querySelectorAll('a[href^="#"]');
        
        links.forEach(link => {
            link.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href === '#') return;
                
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    const headerHeight = document.querySelector('.site-header')?.offsetHeight || 0;
                    const targetPosition = target.offsetTop - headerHeight - 20;
                    
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }
    
    /* ===========================================
       4. Lazy Load (이미지 지연 로딩)
       =========================================== */
    function initLazyLoad() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            const lazyImages = document.querySelectorAll('img.lazy');
            lazyImages.forEach(img => imageObserver.observe(img));
        }
    }
    
    /* ===========================================
       5. 접근성 개선
       =========================================== */
    function initAccessibility() {
        // ESC 키로 모달/메뉴 닫기
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const hamburger = document.querySelector('.header-hamburger.active');
                const mobileMenu = document.querySelector('.header-mobile-menu.active');
                
                if (hamburger && mobileMenu) {
                    hamburger.classList.remove('active');
                    mobileMenu.classList.remove('active');
                    document.body.style.overflow = '';
                }
            }
        });
        
        // 포커스 트랩 (모달용)
        const focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
        
        window.trapFocus = function(element) {
            const focusable = element.querySelectorAll(focusableElements);
            const firstFocusable = focusable[0];
            const lastFocusable = focusable[focusable.length - 1];
            
            element.addEventListener('keydown', function(e) {
                if (e.key !== 'Tab') return;
                
                if (e.shiftKey) {
                    if (document.activeElement === firstFocusable) {
                        e.preventDefault();
                        lastFocusable.focus();
                    }
                } else {
                    if (document.activeElement === lastFocusable) {
                        e.preventDefault();
                        firstFocusable.focus();
                    }
                }
            });
        };
    }
    
    /* ===========================================
       6. 유틸리티 함수
       =========================================== */
    
    // 토스트 메시지 표시
    window.showToast = function(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 30px;
            right: 30px;
            padding: 16px 24px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            z-index: 10000;
            animation: slideInRight 0.3s ease-out;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    };
    
    // 클립보드에 복사
    window.copyToClipboard = function(text) {
        return navigator.clipboard.writeText(text)
            .then(() => {
                showToast('✅ 복사되었습니다!', 'success');
                return true;
            })
            .catch(err => {
                console.error('복사 실패:', err);
                showToast('❌ 복사에 실패했습니다', 'error');
                return false;
            });
    };
    
    // 디바운스 함수
    window.debounce = function(func, wait) {
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
    
    // 쓰로틀 함수
    window.throttle = function(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    };
    
    // 로컬 스토리지 헬퍼
    window.storage = {
        set: (key, value) => {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                console.error('Storage set error:', e);
                return false;
            }
        },
        get: (key) => {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : null;
            } catch (e) {
                console.error('Storage get error:', e);
                return null;
            }
        },
        remove: (key) => {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (e) {
                console.error('Storage remove error:', e);
                return false;
            }
        }
    };
    
    // 날짜 포맷터
    window.formatDate = function(date, format = 'YYYY-MM-DD') {
        const d = new Date(date);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes);
    };
    
    /* ===========================================
       7. 애니메이션 추가
       =========================================== */
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
})();

