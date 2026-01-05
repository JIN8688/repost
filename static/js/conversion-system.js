// ========================================
// 💰 스마트 전환 팝업 시스템 (Conversion System)
// ========================================

// 전환 팝업 표시
function showUpgradePopup(scenario = 'limit_reached') {
    const popups = {
        // 상황 1: 하루 제한 도달
        limit_reached: {
            emoji: '😊',
            title: '오늘 많이 쓰셨네요!',
            subtitle: '오늘 무료 횟수를 모두 사용하셨어요',
            benefits: [
                { icon: '✨', text: '하루 50회 (16배!)' },
                { icon: '🎯', text: '제한 걱정 없이 쭉~' },
                { icon: '💎', text: '첫 달 50% 할인' }
            ],
            cta: '지금 바로 시작 →',
            secondary: '내일 다시',
            bonus: '💡 지금 가입하면 즉시 50회 충전!'
        },
        
        // 상황 2: Premium 기능 시도
        premium_feature: {
            emoji: '🔥',
            title: 'AI 글쓰기는 Pro 기능입니다',
            subtitle: '1,000자 블로그 글을 10초 만에!',
            benefits: [
                { icon: '⚡', text: 'Basic: 하루 10회' },
                { icon: '🚀', text: 'Pro: 무제한' },
                { icon: '💯', text: '완벽한 SEO 최적화' }
            ],
            cta: '요금제 보기 →',
            secondary: '나중에',
            bonus: null
        },
        
        // 상황 3: 3일 연속 사용 (최고 전환율!)
        power_user: {
            emoji: '🎉',
            title: '3일 연속 사용 중이시네요!',
            subtitle: '당신은 파워 유저입니다!',
            benefits: [
                { icon: '📊', text: '지금까지 45분 시간 절약' },
                { icon: '💬', text: '댓글 23개 생성' },
                { icon: '🎯', text: '블로그 12개 분석' }
            ],
            cta: '특별 할인 받기 →',
            secondary: null,
            bonus: '⏰ 오늘만! 3일 연속 사용자 30% 할인',
            discount: true,
            timer: true
        }
    };
    
    const popup = popups[scenario] || popups.limit_reached;
    
    // 팝업 HTML 생성
    const overlay = document.createElement('div');
    overlay.className = 'conversion-overlay';
    overlay.innerHTML = `
        <div class="conversion-popup">
            <div class="conversion-emoji">${popup.emoji}</div>
            <h2 class="conversion-title">${popup.title}</h2>
            <p class="conversion-subtitle">${popup.subtitle}</p>
            
            <div class="conversion-benefits">
                ${popup.benefits.map(b => `
                    <div class="benefit-item">
                        <span class="benefit-icon">${b.icon}</span>
                        <span class="benefit-text">${b.text}</span>
                    </div>
                `).join('')}
            </div>
            
            ${popup.bonus ? `
                <div class="conversion-bonus">
                    ${popup.bonus}
                </div>
            ` : ''}
            
            ${popup.timer ? `
                <div class="conversion-timer" id="conversionTimer">
                    남은 시간: <span id="timerDisplay">23:59:59</span>
                </div>
            ` : ''}
            
            <div class="conversion-buttons">
                <button class="conversion-btn-primary" onclick="goToPricing()">
                    ${popup.cta}
                </button>
                ${popup.secondary ? `
                    <button class="conversion-btn-secondary" onclick="closeConversionPopup()">
                        ${popup.secondary}
                    </button>
                ` : ''}
            </div>
        </div>
        
        <style>
            .conversion-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                padding: 20px;
                animation: fadeIn 0.3s ease-out;
            }
            
            .conversion-popup {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.95) 100%);
                backdrop-filter: blur(30px);
                border-radius: 32px;
                padding: 50px 40px;
                max-width: 500px;
                width: 100%;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
                animation: slideUp 0.5s ease-out;
            }
            
            .conversion-emoji {
                font-size: 80px;
                margin-bottom: 20px;
            }
            
            .conversion-title {
                font-size: 2rem;
                font-weight: 800;
                margin: 0 0 12px 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .conversion-subtitle {
                font-size: 1.1rem;
                color: #64748b;
                margin: 0 0 30px 0;
            }
            
            .conversion-benefits {
                background: #f8f9fa;
                border-radius: 20px;
                padding: 24px;
                margin: 24px 0;
            }
            
            .benefit-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 0;
                font-size: 1.1rem;
            }
            
            .benefit-icon {
                font-size: 1.5rem;
            }
            
            .benefit-text {
                color: #1a1a2e;
                font-weight: 600;
            }
            
            .conversion-bonus {
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
                border: 2px solid rgba(102, 126, 234, 0.3);
                border-radius: 16px;
                padding: 16px;
                margin: 20px 0;
                color: #667eea;
                font-weight: 700;
                font-size: 1.05rem;
            }
            
            .conversion-timer {
                background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%);
                border: 2px solid rgba(239, 68, 68, 0.3);
                border-radius: 12px;
                padding: 12px;
                margin: 16px 0;
                color: #ef4444;
                font-weight: 700;
            }
            
            .conversion-buttons {
                display: flex;
                flex-direction: column;
                gap: 12px;
                margin-top: 24px;
            }
            
            .conversion-btn-primary {
                padding: 18px 48px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 1.2rem;
                font-weight: 700;
                cursor: pointer;
                box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
                transition: all 0.3s ease;
            }
            
            .conversion-btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 12px 32px rgba(102, 126, 234, 0.5);
            }
            
            .conversion-btn-secondary {
                padding: 12px;
                background: transparent;
                color: #94a3b8;
                border: none;
                font-size: 1rem;
                cursor: pointer;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(30px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            @media (max-width: 768px) {
                .conversion-popup {
                    padding: 40px 28px;
                }
                
                .conversion-title {
                    font-size: 1.5rem;
                }
            }
        </style>
    `;
    
    document.body.appendChild(overlay);
    
    // 타이머 시작 (power_user 시나리오)
    if (popup.timer) {
        startConversionTimer();
    }
    
    // ESC 키로 닫기
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            closeConversionPopup();
            document.removeEventListener('keydown', escHandler);
        }
    };
    document.addEventListener('keydown', escHandler);
    
    console.log(`💰 전환 팝업 표시: ${scenario}`);
}

// 타이머 시작
function startConversionTimer() {
    const timerEl = document.getElementById('timerDisplay');
    if (!timerEl) return;
    
    // 오늘 자정까지 남은 시간
    const now = new Date();
    const midnight = new Date(now);
    midnight.setHours(24, 0, 0, 0);
    
    const interval = setInterval(() => {
        const now = new Date();
        const diff = midnight - now;
        
        if (diff <= 0) {
            clearInterval(interval);
            timerEl.textContent = '00:00:00';
            return;
        }
        
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        
        timerEl.textContent = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }, 1000);
}

// 팝업 닫기
function closeConversionPopup() {
    const overlay = document.querySelector('.conversion-overlay');
    if (overlay) {
        overlay.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => overlay.remove(), 300);
    }
}

// 요금제 페이지로 이동
function goToPricing() {
    window.location.href = '/pricing';
}

// 3일 연속 사용 감지
function checkPowerUserStatus() {
    const visits = JSON.parse(localStorage.getItem('repost_visit_dates') || '[]');
    const today = new Date().toDateString();
    
    // 오늘 방문 추가 (중복 제거)
    if (!visits.includes(today)) {
        visits.push(today);
        
        // 최근 10일만 유지
        if (visits.length > 10) {
            visits.shift();
        }
        
        localStorage.setItem('repost_visit_dates', JSON.stringify(visits));
    }
    
    // 최근 3일 연속 체크
    const recent = visits.slice(-3);
    if (recent.length >= 3) {
        const dates = recent.map(d => new Date(d));
        let consecutive = true;
        
        for (let i = 1; i < dates.length; i++) {
            const diff = (dates[i] - dates[i-1]) / (1000 * 60 * 60 * 24);
            if (diff > 1.5) { // 1.5일 이내 (여유)
                consecutive = false;
                break;
            }
        }
        
        if (consecutive) {
            const powerUserShown = localStorage.getItem('power_user_popup_shown');
            if (!powerUserShown) {
                // 3일 연속 사용자 특별 팝업 (1회만)
                setTimeout(() => {
                    showUpgradePopup('power_user');
                    localStorage.setItem('power_user_popup_shown', 'true');
                }, 5000); // 5초 후 표시
            }
        }
    }
}

// 페이지 로드 시 체크
window.addEventListener('load', () => {
    checkPowerUserStatus();
});

console.log('✅ conversion-system.js 로드 완료');

