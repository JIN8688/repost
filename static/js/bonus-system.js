// ========================================
// 🎁 보너스 시스템 (프로덕션급)
// ========================================

// 보너스 관리 클래스
class BonusSystem {
    constructor() {
        this.init();
    }

    init() {
        // 초기 데이터 로드
        this.loadUsageData();
        this.updateUsageBadge();
        
        // 신규 사용자 체크 (7일 보너스)
        this.checkNewUserBonus();
        
        // URL 파라미터 체크 (referral 추적)
        this.checkReferralParam();
        
        console.log('🎁 보너스 시스템 초기화 완료');
    }
    
    // URL 파라미터로 referral 추적
    checkReferralParam() {
        const urlParams = new URLSearchParams(window.location.search);
        const referrerId = urlParams.get('ref');
        
        if (referrerId) {
            const userId = localStorage.getItem('repost_user_id');
            
            // 자기 자신의 링크는 무시
            if (userId === referrerId) {
                console.log('⚠️ 자신의 추천 링크는 사용할 수 없습니다');
                return;
            }
            
            // 이미 추천 받았는지 확인
            const alreadyReferred = localStorage.getItem('repost_referred_by');
            if (alreadyReferred) {
                console.log('ℹ️ 이미 추천을 통해 가입한 사용자입니다');
                return;
            }
            
            // 서버에 추적 요청
            fetch('/api/referral/track', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    referrerId: referrerId,
                    newUserId: userId
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    localStorage.setItem('repost_referred_by', referrerId);
                    console.log('✅ 추천 링크로 가입 완료:', referrerId);
                }
            })
            .catch(err => console.error('❌ 추천 추적 실패:', err));
        }
    }

    // 사용 데이터 로드
    loadUsageData() {
        const today = new Date().toDateString();
        let data = localStorage.getItem('repost_usage_data');
        
        if (data) {
            data = JSON.parse(data);
            
            // 날짜가 바뀌면 초기화
            if (data.date !== today) {
                this.resetDailyUsage();
            }
        } else {
            // 첫 방문
            this.resetDailyUsage();
        }
    }

    // 일일 사용 횟수 초기화
    resetDailyUsage() {
        const today = new Date().toDateString();
        const firstVisit = localStorage.getItem('repost_first_visit');
        
        // 체험 기간 상태 조회 (상세 정보 포함)
        const trialStatus = this.getTrialStatus();
        const dailyLimit = trialStatus.isNewUser ? 7 : 3; // 7일 이내면 7회, 아니면 3회
        
        const usageData = {
            date: today,
            baseUsage: 0,
            baseLimit: dailyLimit,
            bonuses: this.loadBonuses(),
            isNewUser: trialStatus.isNewUser
        };
        
        localStorage.setItem('repost_usage_data', JSON.stringify(usageData));
        
        console.log(`📊 일일 사용 횟수 초기화: ${dailyLimit}회/일 (상태: ${trialStatus.statusText})`);
    }

    // 신규 사용자 확인 (7일 이내)
    checkIfNewUser() {
        const firstVisit = localStorage.getItem('repost_first_visit');
        
        if (!firstVisit) {
            return true; // 첫 방문
        }
        
        const firstDate = new Date(firstVisit);
        const today = new Date();
        const daysDiff = Math.floor((today - firstDate) / (1000 * 60 * 60 * 24));
        
        return daysDiff < 7;
    }
    
    // 체험 기간 상태 조회 (상세 정보 포함)
    getTrialStatus() {
        const firstVisit = localStorage.getItem('repost_first_visit');
        
        if (!firstVisit) {
            return {
                isNewUser: true,
                daysElapsed: 0,
                daysRemaining: 7,
                statusText: '7일 체험 시작!'
            };
        }
        
        const firstDate = new Date(firstVisit);
        const today = new Date();
        const daysDiff = Math.floor((today - firstDate) / (1000 * 60 * 60 * 24));
        const daysRemaining = Math.max(0, 7 - daysDiff);
        const isNewUser = daysDiff < 7;
        
        let statusText;
        if (isNewUser) {
            if (daysRemaining === 0) {
                statusText = '7일 체험 마지막 날! 🎉';
            } else {
                statusText = `7일 체험 기간 중 (${daysRemaining}일 남음)`;
            }
        } else {
            statusText = '일반 사용자';
        }
        
        return {
            isNewUser,
            daysElapsed: daysDiff,
            daysRemaining,
            statusText
        };
    }

    // 보너스 로드
    loadBonuses() {
        const bonusesStr = localStorage.getItem('repost_bonuses');
        if (!bonusesStr) return [];
        
        const bonuses = JSON.parse(bonusesStr);
        
        // 만료된 보너스 제거
        const now = Date.now();
        const validBonuses = bonuses.filter(b => b.expiresAt > now);
        
        if (validBonuses.length !== bonuses.length) {
            localStorage.setItem('repost_bonuses', JSON.stringify(validBonuses));
        }
        
        return validBonuses;
    }

    // 남은 사용 횟수 계산
    getRemainingUsage() {
        // 🔑 마스터 계정: 무제한 사용
        if (localStorage.getItem('repost_admin') === 'true') {
            return 9999;
        }
        
        const data = JSON.parse(localStorage.getItem('repost_usage_data'));
        if (!data) return 0;
        
        const baseRemaining = data.baseLimit - data.baseUsage;
        const bonusRemaining = data.bonuses.reduce((sum, b) => sum + b.remaining, 0);
        
        return Math.max(0, baseRemaining + bonusRemaining);
    }

    // 사용 횟수 감소
    decreaseUsage() {
        // 🔑 마스터 계정: 사용 횟수 차감 안 함
        if (localStorage.getItem('repost_admin') === 'true') {
            return true;
        }
        
        const data = JSON.parse(localStorage.getItem('repost_usage_data'));
        if (!data) return false;
        
        // 먼저 기본 사용 횟수 차감
        if (data.baseUsage < data.baseLimit) {
            data.baseUsage++;
        } else {
            // 보너스 사용
            const activeBonus = data.bonuses.find(b => b.remaining > 0);
            if (activeBonus) {
                activeBonus.remaining--;
            } else {
                return false; // 사용 불가
            }
        }
        
        localStorage.setItem('repost_usage_data', JSON.stringify(data));
        localStorage.setItem('repost_bonuses', JSON.stringify(data.bonuses));
        this.updateUsageBadge();
        
        return true;
    }

    // 배지 업데이트
    updateUsageBadge() {
        const remaining = this.getRemainingUsage();
        const countEl = document.getElementById('usageCount');
        
        if (countEl) {
            // 숫자 애니메이션
            this.animateCounter(countEl, parseInt(countEl.textContent) || 0, remaining);
        }
        
        // 0회 남았을 때 경고 색상
        const badge = document.getElementById('usageBadge');
        if (badge) {
            if (remaining === 0) {
                badge.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
            } else if (remaining <= 3) {
                badge.style.background = 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)';
            } else {
                badge.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
            }
        }
    }

    // 숫자 카운터 애니메이션
    animateCounter(element, from, to) {
        if (from === to) {
            element.textContent = to;
            return;
        }
        
        const duration = 500;
        const steps = 20;
        const stepValue = (to - from) / steps;
        const stepDuration = duration / steps;
        
        let current = from;
        let step = 0;
        
        const timer = setInterval(() => {
            step++;
            current += stepValue;
            element.textContent = Math.round(current);
            
            if (step >= steps) {
                element.textContent = to;
                clearInterval(timer);
            }
        }, stepDuration);
    }

    // 신규 사용자 보너스 체크 (7일 → 8일 전환 시)
    checkNewUserBonus() {
        const firstVisit = localStorage.getItem('repost_first_visit');
        if (!firstVisit) return;
        
        const firstDate = new Date(firstVisit);
        const today = new Date();
        const daysDiff = Math.floor((today - firstDate) / (1000 * 60 * 60 * 24));
        
        // 정확히 7일째 or 8일째에 알림
        const shownTransition = localStorage.getItem('repost_shown_transition');
        if (daysDiff === 7 && !shownTransition) {
            setTimeout(() => {
                this.showTrialEndModal();
                localStorage.setItem('repost_shown_transition', 'true');
            }, 2000);
        }
    }

    // 7일 체험 종료 모달
    showTrialEndModal() {
        const html = `
            <div class="bonus-modal-overlay" onclick="closeModal(event)">
                <div class="bonus-modal usage-detail-modal" onclick="event.stopPropagation()">
                    <div class="bonus-modal-content">
                        <h2 class="bonus-modal-title">
                            🎉 7일 체험이 종료되었습니다
                        </h2>
                        
                        <p style="font-size: 16px; line-height: 1.6; margin: 20px 0;">
                            Repost가 마음에 드셨나요?<br><br>
                            오늘부터 하루 3회로 제한되지만,<br>
                            걱정 마세요! 보너스로 더 받을 수 있어요 😊
                        </p>
                        
                        <div class="usage-section">
                            <div class="usage-item">
                                <span class="usage-item-label">👥 친구 추천</span>
                                <span class="usage-item-value">+5회</span>
                            </div>
                            <div class="usage-item">
                                <span class="usage-item-label">📢 SNS 공유</span>
                                <span class="usage-item-value">+5회</span>
                            </div>
                        </div>
                        
                        <div class="bonus-actions">
                            <button class="bonus-action-btn" onclick="showReferralModal()">
                                👥 친구 추천 (+5회) | 7일간 최대 25회
                            </button>
                        </div>
                        
                        <button class="bonus-btn bonus-btn-secondary" onclick="closeModal()" style="width: 100%; margin-top: 16px;">
                            3회로 계속 사용
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        const container = document.getElementById('bonusModals');
        container.innerHTML = html;
        
        // 🎨 부드러운 애니메이션을 위해 다음 프레임에 show 클래스 추가
        requestAnimationFrame(() => {
            const overlay = container.querySelector('.bonus-modal-overlay');
            if (overlay) {
                overlay.classList.add('show');
            }
        });
    }

    // 보너스 추가
    addBonus(type, amount, expiryDays = 30) {
        const bonuses = this.loadBonuses();
        
        const newBonus = {
            id: Date.now(),
            type: type, // 'referral' or 'share'
            amount: amount,
            remaining: amount,
            createdAt: Date.now(),
            expiresAt: Date.now() + (expiryDays * 24 * 60 * 60 * 1000)
        };
        
        bonuses.push(newBonus);
        localStorage.setItem('repost_bonuses', JSON.stringify(bonuses));
        
        // 사용 데이터에도 반영
        const data = JSON.parse(localStorage.getItem('repost_usage_data'));
        data.bonuses = bonuses;
        localStorage.setItem('repost_usage_data', JSON.stringify(data));
        
        return newBonus;
    }

    // 보너스 획득 축하
    celebrateBonus(type, amount) {
        // 🎉 더 화려한 Confetti 효과 (3회 연속)
        if (typeof confetti !== 'undefined') {
            // 첫 번째 폭죽
            confetti({
                particleCount: 150,
                spread: 100,
                origin: { y: 0.6 },
                colors: ['#667eea', '#764ba2', '#f59e0b', '#22c55e', '#ec4899']
            });
            
            // 두 번째 폭죽 (0.3초 후)
            setTimeout(() => {
                confetti({
                    particleCount: 120,
                    spread: 80,
                    origin: { x: 0.3, y: 0.5 },
                    colors: ['#667eea', '#764ba2', '#f59e0b', '#22c55e', '#ec4899']
                });
            }, 300);
            
            // 세 번째 폭죽 (0.6초 후)
            setTimeout(() => {
                confetti({
                    particleCount: 120,
                    spread: 80,
                    origin: { x: 0.7, y: 0.5 },
                    colors: ['#667eea', '#764ba2', '#f59e0b', '#22c55e', '#ec4899']
                });
            }, 600);
        }
        
        // 토스트 알림 (5초로 연장)
        this.showToast(
            '🎉 축하합니다! 🎉',
            `${type === 'referral' ? '친구 추천' : 'SNS 공유'} 보너스 +${amount}회 획득!`,
            'success',
            5000  // 5초
        );
        
        // 보너스 모달 (1.5초 후로 조정)
        setTimeout(() => {
            this.showBonusModal(type, amount);
        }, 1500);
        
        // 배지 업데이트
        this.updateUsageBadge();
    }

    // 토스트 알림
    showToast(title, message, type = 'success', duration = 3000) {
        const icons = {
            success: '🎉',
            info: 'ℹ️',
            warning: '⚠️',
            error: '❌'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">${icons[type]}</div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <div class="toast-close" onclick="this.parentElement.remove()">✕</div>
        `;
        
        document.body.appendChild(toast);
        
        // duration 후 자동 제거
        setTimeout(() => {
            toast.style.animation = 'toastPopOut 0.3s ease-out forwards';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    // 보너스 모달 표시
    showBonusModal(type, amount) {
        const data = JSON.parse(localStorage.getItem('repost_usage_data'));
        const remaining = this.getRemainingUsage();
        const typeText = type === 'referral' ? '친구 추천' : 'SNS 공유';
        const typeIcon = type === 'referral' ? '👥' : '📢';
        
        const html = `
            <div class="bonus-modal-overlay" onclick="closeModal(event)">
                <div class="bonus-modal" onclick="event.stopPropagation()">
                    <div class="bonus-modal-content">
                        <h2 class="bonus-modal-title">
                            <span>🎊</span>
                            <span>축하합니다!</span>
                            <span>🎊</span>
                        </h2>
                        
                        <p style="font-size: 18px; margin-bottom: 8px;">
                            ${typeIcon} ${typeText} 보너스 획득!
                        </p>
                        
                        <div class="bonus-amount">+${amount}회</div>
                        
                        <div class="bonus-details">
                            <div class="bonus-detail-row">
                                <span class="bonus-detail-label">남은 횟수</span>
                                <span class="bonus-detail-value">${remaining}회</span>
                            </div>
                            <div class="bonus-detail-row">
                                <span class="bonus-detail-label">유효기간</span>
                                <span class="bonus-detail-value">30일</span>
                            </div>
                        </div>
                        
                        ${type === 'referral' ? this.getReferralProgress() : ''}
                        
                        <div class="bonus-modal-buttons">
                            <button class="bonus-btn bonus-btn-primary" onclick="showReferralModal()">더 많은 친구 추천하기</button>
                            <button class="bonus-btn bonus-btn-secondary" onclick="closeModal()">확인</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const container = document.getElementById('bonusModals');
        container.innerHTML = html;
        
        // 🎨 부드러운 애니메이션을 위해 다음 프레임에 show 클래스 추가
        requestAnimationFrame(() => {
            const overlay = container.querySelector('.bonus-modal-overlay');
            if (overlay) {
                overlay.classList.add('show');
            }
        });
    }

    // 친구 추천 진행률 (7일 롤링 5회)
    getReferralProgress() {
        const referrals = JSON.parse(localStorage.getItem('repost_referrals') || '[]');
        const count = referrals.length;
        const percent = (count / 5) * 100;
        
        const stars = [];
        for (let i = 0; i < 5; i++) {
            const star = i < count ? '⭐' : '☆';
            stars.push(`<span style="--star-index: ${i};">${star}</span>`);
        }
        
        return `
            <div class="bonus-progress">
                <div class="bonus-progress-label">보너스 진행률: ${count}/5회</div>
                <div class="bonus-progress-bar">
                    <div class="bonus-progress-fill" style="width: ${percent}%"></div>
                </div>
                <div class="bonus-stars">${stars.join('')}</div>
                ${count >= 5 ? '<p style="margin-top: 12px; font-size: 14px; color: #7debc8; text-shadow: 0 0 15px rgba(125, 235, 200, 0.5);">🎉 5회 모두 완료! 7일 후 다시 받으세요!</p>' : 
                  count >= 3 ? '<p style="margin-top: 12px; font-size: 14px; color: #a5b4fc; text-shadow: 0 0 15px rgba(165, 180, 252, 0.5);">💡 ${5 - count}번만 더 받으면 완료! (7일간 유효)</p>' : ''}
            </div>
        `;
    }
}

// 전역 보너스 시스템 인스턴스
let bonusSystem;

// 페이지 로드 시 초기화
window.addEventListener('load', () => {
    bonusSystem = new BonusSystem();
    
    // 🔑 Secret Code 시스템 초기화 (DOM 로드 후)
    setupSecretCodeAccess();
});

// ========================================
// 🎁 모달 및 UI 함수들
// ========================================

// 사용 횟수 상세 모달 (신규 디자인)
function showUsageDetail() {
    const container = document.getElementById('bonusModals');
    const existingOverlay = container.querySelector('.bonus-modal-overlay');
    
    // 🎨 부드러운 모달 전환 함수
    const renderModal = () => {
        // 📱 모바일: 배경 스크롤 방지
        document.body.style.overflow = 'hidden';
        
        const data = JSON.parse(localStorage.getItem('repost_usage_data'));
        if (!data) return;
        
        // 체험 기간 상태 조회
        const trialStatus = bonusSystem ? bonusSystem.getTrialStatus() : { isNewUser: false };
        const isTrialEnded = !trialStatus.isNewUser; // 7일 체험 종료 여부
        
        const html = `
            <div class="bonus-modal-overlay" onclick="closeModal(event)">
                <div class="bonus-modal usage-detail-modal" onclick="event.stopPropagation()" style="max-width: 520px;">
                    <div class="bonus-modal-content" style="padding: 40px 32px;">
                        <!-- 제목 -->
                        <div style="text-align: center; margin-bottom: 24px;">
                            <div style="font-size: 1.8rem; font-weight: 800; color: #1a202c; margin-bottom: 16px;">
                                ${isTrialEnded ? '🎉 7일 체험이 종료되었습니다' : '💎 사용 횟수 안내'}
                            </div>
                            <div style="font-size: 1.1rem; color: #4b5563; font-weight: 500;">
                                Repost가 마음에 드셨나요?
                            </div>
                        </div>
                        
                        <!-- 설명 -->
                        <div style="background: #f9fafb; border-radius: 16px; padding: 20px; margin-bottom: 28px; text-align: center; line-height: 1.7;">
                            <p style="font-size: 1rem; color: #374151; margin: 0;">
                                오늘부터 하루 <strong style="color: #667eea;">3회</strong>로 제한되지만,<br>
                                걱정 마세요! 보너스로 더 받을 수 있어요 😊
                            </p>
                        </div>
                        
                        <!-- 보너스 옵션 리스트 -->
                        <div style="margin-bottom: 28px;">
                            <div style="background: white; border-radius: 16px; border: 2px solid #e5e7eb; overflow: hidden;">
                                <!-- 친구 추천 -->
                                <div style="padding: 18px 20px; border-bottom: 1px solid #e5e7eb; display: flex; align-items: center; justify-content: space-between;">
                                    <div style="display: flex; align-items: center; gap: 12px;">
                                        <span style="font-size: 1.5rem;">👥</span>
                                        <span style="font-size: 1rem; font-weight: 600; color: #1a202c;">친구 추천</span>
                                    </div>
                                    <span style="font-size: 1.1rem; font-weight: 700; color: #667eea;">+5회</span>
                                </div>
                                
                                <!-- SNS 공유 -->
                                <div style="padding: 18px 20px; border-bottom: 1px solid #e5e7eb; display: flex; align-items: center; justify-content: space-between;">
                                    <div style="display: flex; align-items: center; gap: 12px;">
                                        <span style="font-size: 1.5rem;">📢</span>
                                        <span style="font-size: 1rem; font-weight: 600; color: #1a202c;">SNS 공유</span>
                                    </div>
                                    <span style="font-size: 1.1rem; font-weight: 700; color: #667eea;">+3회</span>
                                </div>
                                
                                <!-- Basic 플랜 -->
                                <div style="padding: 18px 20px; display: flex; align-items: center; justify-content: space-between;">
                                    <div style="display: flex; align-items: center; gap: 12px;">
                                        <span style="font-size: 1.5rem;">💎</span>
                                        <span style="font-size: 1rem; font-weight: 600; color: #1a202c;">Basic 플랜</span>
                                    </div>
                                    <a href="/pricing" style="font-size: 1rem; font-weight: 700; color: #667eea; text-decoration: none;">하루 100회</a>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 친구 추천 큰 버튼 -->
                        <button class="bonus-action-btn" onclick="showReferralModal()" style="
                            width: 100%;
                            padding: 18px 24px;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            border: none;
                            border-radius: 16px;
                            color: white;
                            font-size: 1.1rem;
                            font-weight: 700;
                            cursor: pointer;
                            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
                            transition: all 0.3s ease;
                            margin-bottom: 12px;
                        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 12px 32px rgba(102, 126, 234, 0.5)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 8px 24px rgba(102, 126, 234, 0.4)'">
                            👥 친구 추천하고 +5회 받기
                        </button>
                        
                        <!-- 요금제 보기 버튼 -->
                        <a href="/pricing" style="
                            display: block;
                            width: 100%;
                            padding: 16px 24px;
                            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
                            border: 2px solid #667eea;
                            border-radius: 16px;
                            color: #667eea;
                            font-size: 1rem;
                            font-weight: 700;
                            cursor: pointer;
                            transition: all 0.3s ease;
                            text-align: center;
                            text-decoration: none;
                            margin-bottom: 12px;
                        " onmouseover="this.style.transform='translateY(-2px)'; this.style.background='linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%)'" onmouseout="this.style.transform='translateY(0)'; this.style.background='linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)'">
                            💎 요금제 보기 (하루 100회)
                        </a>
                        
                        <!-- 3회로 계속 사용 버튼 -->
                        <button onclick="closeModal()" style="
                            width: 100%;
                            padding: 14px;
                            background: transparent;
                            border: none;
                            color: #9ca3af;
                            font-size: 0.95rem;
                            font-weight: 600;
                            cursor: pointer;
                            transition: all 0.3s ease;
                        " onmouseover="this.style.color='#6b7280'" onmouseout="this.style.color='#9ca3af'">
                            3회로 계속 사용
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        
        // 🎨 부드러운 애니메이션을 위해 다음 프레임에 show 클래스 추가
        requestAnimationFrame(() => {
            const overlay = container.querySelector('.bonus-modal-overlay');
            if (overlay) {
                overlay.classList.add('show');
            }
        });
    };
    
    // 🎨 기존 모달이 있으면 페이드아웃 후 새 모달 표시
    if (existingOverlay) {
        existingOverlay.classList.remove('show');
        setTimeout(renderModal, 300); // 300ms 페이드아웃 대기
    } else {
        renderModal();
    }
}

// 친구 추천 모달 (부드러운 전환)
function showReferralModal() {
    const container = document.getElementById('bonusModals');
    const existingOverlay = container.querySelector('.bonus-modal-overlay');
    
    // 🎨 부드러운 모달 전환 함수
    const renderModal = () => {
        // 📱 모바일: 배경 스크롤 방지
        document.body.style.overflow = 'hidden';
        
        const userId = localStorage.getItem('repost_user_id');
        const referralLink = `https://repost.kr?ref=${userId}`;
        const referrals = JSON.parse(localStorage.getItem('repost_referrals') || '[]');
        const count = referrals.length;
        
        const html = `
            <div class="bonus-modal-overlay" onclick="closeModal(event)">
                <div class="bonus-modal referral-modal" onclick="event.stopPropagation()">
                    <div class="bonus-modal-content">
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <button onclick="showUsageDetail()" style="background: none; border: none; cursor: pointer; padding: 8px; margin-right: 10px; display: flex; align-items: center; color: #667eea; font-size: 24px; transition: transform 0.2s;">
                                ←
                            </button>
                            <h2 class="bonus-modal-title" style="margin: 0; flex: 1;">
                                👥 친구 추천하기
                            </h2>
                        </div>
                        
                        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 4px solid #667eea;">
                            <div style="font-size: 15px; font-weight: 700; color: #1a202c; margin-bottom: 12px;">
                                💡 보너스 받는 방법 (3단계)
                            </div>
                            <div style="font-size: 13px; color: #4b5563; line-height: 1.8;">
                                <div style="margin-bottom: 8px;">
                                    <strong style="color: #667eea;">1단계:</strong> 아래 링크를 친구에게 공유
                                </div>
                                <div style="margin-bottom: 8px;">
                                    <strong style="color: #667eea;">2단계:</strong> 친구가 링크를 클릭해서 접속
                                </div>
                                <div>
                                    <strong style="color: #667eea;">3단계:</strong> 하단 "보너스 받기" 버튼 클릭
                                </div>
                            </div>
                        </div>
                        
                        ${bonusSystem.getReferralProgress()}
                        
                        <div style="background: white; border-radius: 12px; padding: 16px; margin: 20px 0; border: 2px solid #667eea; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.15);">
                            <div style="font-size: 14px; margin-bottom: 8px; color: #667eea; font-weight: 700;">📎 내 추천 링크:</div>
                            <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%); border-radius: 8px; padding: 12px; font-family: monospace; font-size: 12px; word-break: break-all; color: #1f2937; border: 1px solid rgba(102, 126, 234, 0.2);">
                                ${referralLink}
                            </div>
                        </div>
                        
                        <div class="share-buttons">
                            <button class="share-btn" id="copyLinkBtn" onclick="event.stopPropagation(); copyReferralLink('${referralLink}', this)">
                                <span class="share-btn-icon">📋</span>
                                <span class="share-btn-text">링크 복사</span>
                            </button>
                            <button class="share-btn" onclick="event.stopPropagation(); shareReferralLink('${referralLink}')">
                                <span class="share-btn-icon">📱</span>
                                <span class="share-btn-text">SNS 공유하기</span>
                            </button>
                        </div>
                        
                        <button class="bonus-btn bonus-btn-primary" onclick="claimReferralBonus(this)" style="width: 100%; margin-top: 24px; font-size: 16px; padding: 18px;">
                            🎁 보너스 받기 (+5회)
                        </button>
                        
                        <div style="background: #fef3c7; border-radius: 8px; padding: 12px; margin-top: 16px; border-left: 3px solid #f59e0b;">
                            <div style="font-size: 12px; color: #92400e; line-height: 1.6;">
                                <strong>⚠️ 주의사항</strong><br>
                                • 자신의 링크는 사용 불가<br>
                                • 7일간 5회까지 보너스 지급 (하루에 다 받아도 OK!)<br>
                                • 5회 소진 후 7일이 지나면 자동 초기화
                            </div>
                        </div>
                        
                        <button class="bonus-btn bonus-btn-secondary" onclick="closeModal()" style="width: 100%; margin-top: 20px;">
                            닫기
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        
        // 🎨 부드러운 애니메이션을 위해 다음 프레임에 show 클래스 추가
        requestAnimationFrame(() => {
            const overlay = container.querySelector('.bonus-modal-overlay');
            if (overlay) {
                overlay.classList.add('show');
            }
        });
    };
    
    // 🎨 기존 모달이 있으면 페이드아웃 후 새 모달 표시
    if (existingOverlay) {
        existingOverlay.classList.remove('show');
        setTimeout(renderModal, 300); // 300ms 페이드아웃 대기
    } else {
        renderModal();
    }
}

// SNS 공유 모달 - 더 이상 사용 안 함 (친구 추천으로 통합)
// function showShareModal() { ... }

// 모달 닫기 (부드러운 애니메이션)
function closeModal(event) {
    if (event && event.target.classList.contains('bonus-modal')) {
        return; // 모달 내부 클릭은 무시
    }
    
    const container = document.getElementById('bonusModals');
    const overlay = container.querySelector('.bonus-modal-overlay');
    
    if (overlay) {
        // 🎨 show 클래스 제거하여 페이드아웃 애니메이션 시작
        overlay.classList.remove('show');
        
        // 🎨 애니메이션 완료 후 DOM에서 제거 (400ms)
        setTimeout(() => {
            container.innerHTML = '';
            // 📱 모바일: 배경 스크롤 복원
            document.body.style.overflow = '';
        }, 400);
    } else {
        // overlay가 없으면 즉시 제거
        container.innerHTML = '';
        // 📱 모바일: 배경 스크롤 복원
        document.body.style.overflow = '';
    }
}

// ========================================
// 🔗 공유 및 추천 함수들
// ========================================

// 추천 링크 복사
function copyReferralLink(link, button) {
    console.log('📋 링크 복사 시도:', link);
    
    // 버튼 즉시 변경 (시각적 피드백)
    const textSpan = button ? button.querySelector('.share-btn-text') : null;
    const originalText = textSpan ? textSpan.textContent : '';
    
    if (textSpan) {
        textSpan.textContent = '복사됨! ✓';
        button.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
    }
    
    // iOS Safari 등을 위한 즉시 실행
    const textArea = document.createElement("textarea");
    textArea.value = link;
    textArea.style.position = "fixed";
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.width = "1px";
    textArea.style.height = "1px";
    textArea.style.padding = "0";
    textArea.style.border = "none";
    textArea.style.outline = "none";
    textArea.style.boxShadow = "none";
    textArea.style.background = "transparent";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    textArea.setSelectionRange(0, 99999); // 모바일 지원
    
    let success = false;
    try {
        success = document.execCommand('copy');
        console.log('✅ execCommand 결과:', success);
    } catch (err) {
        console.error('❌ execCommand 에러:', err);
    }
    
    document.body.removeChild(textArea);
    
    // 버튼 복원
    if (textSpan && button) {
        setTimeout(() => {
            textSpan.textContent = originalText;
            button.style.background = '';
        }, 2000);
    }
    
    if (success) {
        console.log('✅ 복사 성공!');
        if (bonusSystem && bonusSystem.showToast) {
            bonusSystem.showToast(
                '링크 복사 완료! 📋',
                '친구에게 공유해보세요',
                'success'
            );
        }
    } else {
        // Clipboard API 시도
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(link)
                .then(() => {
                    console.log('✅ Clipboard API 성공');
                    if (bonusSystem && bonusSystem.showToast) {
                        bonusSystem.showToast(
                            '링크 복사 완료! 📋',
                            '친구에게 공유해보세요',
                            'success'
                        );
                    }
                })
                .catch(err => {
                    console.error('❌ Clipboard API 실패:', err);
                    // 최후의 수단: 수동 복사 안내
                    if (confirm('클립보드 접근이 제한되었습니다. 링크를 수동으로 복사하시겠습니까?')) {
                        prompt('링크를 복사해주세요 (Ctrl+C 또는 ⌘+C):', link);
                    }
                });
        } else {
            // 최후의 수단: 수동 복사 안내
            if (confirm('클립보드 접근이 제한되었습니다. 링크를 수동으로 복사하시겠습니까?')) {
                prompt('링크를 복사해주세요 (Ctrl+C 또는 ⌘+C):', link);
            }
        }
    }
}

// 추천 링크 공유 (Web Share API)
function shareReferralLink(url) {
    console.log('📤 추천 링크 공유:', url);
    
    if (navigator.share) {
        navigator.share({
            title: 'Repost - AI 블로그 댓글 추천',
            text: 'Repost 덕분에 블로그 댓글 고민 끝! AI가 찰떡같은 댓글 추천해줘요 👍',
            url: url
        })
        .then(() => {
            console.log('✅ 공유 성공');
            // 토스트 제거 - 사용자가 실제로 공유를 완료한 후 보너스 받기 버튼 클릭
        })
        .catch((err) => {
            if (err.name !== 'AbortError') {
                console.error('❌ 공유 실패:', err);
            }
        });
    } else {
        // Web Share API 미지원 시 링크 복사
        copyReferralLink(url, document.querySelector('#copyLinkBtn'));
    }
}

// SNS 공유 (Web Share API) - 더 이상 사용 안 함 (친구 추천으로 통합)
// function shareToSocial(url, text) { ... }

// 친구 추천 보너스 받기
function claimReferralBonus(button) {
    const userId = localStorage.getItem('repost_user_id');
    const originalText = button.textContent;
    
    button.disabled = true;
    button.textContent = '⏳ 처리중...';
    
    fetch('/api/referral/claim', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: userId })
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(data => {
                throw { status: res.status, data: data };
            });
        }
        return res.json();
    })
    .then(data => {
        console.log('📦 서버 응답:', data);
        
        if (data.success) {
            console.log('✅ 보너스 지급 시작');
            
            // 보너스 지급
            const bonus = bonusSystem.addBonus('referral', data.bonus, data.expiryDays);
            console.log('💰 addBonus 완료:', bonus);
            
            // ⭐ 추천 기록에 추가 (별과 게이지 업데이트)
            const referrals = JSON.parse(localStorage.getItem('repost_referrals') || '[]');
            referrals.push({
                timestamp: Date.now(),
                bonusId: bonus.id
            });
            localStorage.setItem('repost_referrals', JSON.stringify(referrals));
            console.log('⭐ 추천 기록 업데이트 완료:', referrals.length);
            
            bonusSystem.celebrateBonus('referral', data.bonus);
            console.log('🎉 celebrateBonus 완료');
            
            bonusSystem.updateUsageBadge();
            console.log('🔄 updateUsageBadge 완료');
            
            button.textContent = '✓ 보너스 받음!';
            button.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
            console.log('✅ 버튼 업데이트 완료');
            
            setTimeout(() => {
                closeModal();
                showUsageDetail();
            }, 2000);  // 2초로 연장 (축하 효과 볼 시간)
        } else {
            console.log('❌ 서버 응답 실패:', data.error);
            // 에러 타입별 친근한 메시지
            if (data.error === 'limit_reached' || data.error === 'reset_pending') {
                const daysLeft = data.days_left || 0;
                const hoursLeft = data.hours_left || 0;
                bonusSystem.showToast(
                    '🎉 5회 보너스를 모두 받으셨어요!',
                    `${daysLeft}일 ${hoursLeft}시간 후에 다시 받을 수 있어요 (7일 후 초기화)`,
                    'success',
                    5000
                );
            } else if (data.error === 'no_referral') {
                bonusSystem.showToast(
                    '🤔 아직 친구가 접속하지 않았어요',
                    '친구에게 링크를 공유하고 접속을 기다려보세요!',
                    'warning',
                    5000
                );
            } else if (data.error === 'self_referral') {
                bonusSystem.showToast(
                    '😅 자신의 링크는 사용할 수 없어요',
                    '다른 친구에게 공유해주세요!',
                    'warning',
                    5000
                );
            } else if (data.error === 'server_error') {
                bonusSystem.showToast(
                    '😔 일시적인 오류가 발생했어요',
                    '잠시 후 다시 시도해주세요!',
                    'error',
                    5000
                );
            } else {
                bonusSystem.showToast(
                    '🤷 보너스를 받을 수 없어요',
                    '친구가 링크를 클릭했는지 확인해보세요!',
                    'warning',
                    5000
                );
            }
            button.disabled = false;
            button.textContent = originalText;
            // ❌ 모달 닫지 않음! 사용자가 토스트를 봐야 함
        }
    })
    .catch(err => {
        console.error('❌ 친구 추천 보너스 요청 실패:', err);
        console.log('🔍 에러 상세:', JSON.stringify(err));
        console.log('🔍 bonusSystem 존재:', !!bonusSystem);
        
        // 서버 에러 응답 처리
        if (err.data) {
            console.log('✅ err.data 존재:', err.data);
            const errorData = err.data;
            
            let title = '';
            let message = '';
            
            if (errorData.error === 'limit_reached' || errorData.error === 'reset_pending') {
                const daysLeft = errorData.days_left || 0;
                const hoursLeft = errorData.hours_left || 0;
                title = '🎉 5회 보너스를 모두 받으셨어요!';
                message = `${daysLeft}일 ${hoursLeft}시간 후에 다시 받을 수 있어요 (7일 후 초기화)`;
            } else if (errorData.error === 'no_referral') {
                title = '🤔 아직 친구가 접속하지 않았어요';
                message = '친구에게 링크를 공유하고 접속을 기다려보세요!';
            } else if (errorData.error === 'self_referral') {
                title = '😅 자신의 링크는 사용할 수 없어요';
                message = '다른 친구에게 공유해주세요!';
            } else if (errorData.error === 'server_not_ready') {
                title = '⚠️ 서버 준비 중이에요';
                message = '잠시 후 다시 시도해주세요!';
            } else {
                title = '😔 일시적인 오류가 발생했어요';
                message = '잠시 후 다시 시도해주세요!';
            }
            
            console.log('🎯 토스트 표시:', title, message);
            
            if (bonusSystem && bonusSystem.showToast) {
                bonusSystem.showToast(title, message, 'warning', 5000);
                console.log('✅ showToast 호출 완료');
            } else {
                console.error('❌ bonusSystem.showToast 없음!');
                alert(title + '\n' + message);  // 긴급 대응: alert로 표시
            }
        } else {
            console.log('❌ err.data 없음 - 네트워크 에러');
            // 네트워크 에러
            if (bonusSystem && bonusSystem.showToast) {
                bonusSystem.showToast(
                    '📡 인터넷 연결을 확인해주세요',
                    '네트워크가 불안정해요. 잠시 후 다시 시도해주세요!',
                    'error',
                    5000
                );
            } else {
                alert('📡 인터넷 연결을 확인해주세요\n네트워크가 불안정해요. 잠시 후 다시 시도해주세요!');
            }
        }
        
        button.disabled = false;
        button.textContent = originalText;
        // ❌ 모달 닫지 않음! 사용자가 토스트를 봐야 함
    });
}

// SNS 공유 보너스 받기 - 더 이상 사용 안 함 (친구 추천으로 통합)
function claimShareBonus(button) {
    const userId = localStorage.getItem('repost_user_id');
    const originalText = button.textContent;
    
    button.disabled = true;
    button.textContent = '⏳ 처리중...';
    
    fetch('/api/share/claim', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: userId })
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(data => {
                throw { status: res.status, data: data };
            });
        }
        return res.json();
    })
    .then(data => {
        console.log('📦 SNS 서버 응답:', data);
        
        if (data.success) {
            console.log('✅ SNS 보너스 지급 시작');
            
            // 보너스 지급
            const bonus = bonusSystem.addBonus('share', data.bonus, data.expiryDays);
            console.log('💰 addBonus 완료:', bonus);
            
            bonusSystem.celebrateBonus('share', data.bonus);
            console.log('🎉 celebrateBonus 완료');
            
            bonusSystem.updateUsageBadge();
            console.log('🔄 updateUsageBadge 완료');
            
            button.textContent = '✓ 보너스 받음!';
            button.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
            console.log('✅ 버튼 업데이트 완료');
            
            setTimeout(() => {
                closeModal();
                showUsageDetail();
            }, 1500);
        } else {
            console.log('❌ SNS 서버 응답 실패:', data.error);
            // 에러 타입별 친근한 메시지
            if (data.error === 'cooldown') {
                bonusSystem.showToast(
                    '😊 이미 보너스를 받으셨어요!',
                    `${data.days_left}일 후에 다시 받을 수 있어요 (주 1회 제한)`,
                    'warning',
                    5000
                );
            } else if (data.error === 'server_error') {
                bonusSystem.showToast(
                    '😔 일시적인 오류가 발생했어요',
                    '잠시 후 다시 시도해주세요!',
                    'error',
                    5000
                );
            } else {
                bonusSystem.showToast(
                    '🤷 보너스를 받을 수 없어요',
                    'SNS에 공유하신 후 다시 시도해주세요!',
                    'warning',
                    5000
                );
            }
            button.disabled = false;
            button.textContent = originalText;
            // ❌ 모달 닫지 않음! 사용자가 토스트를 봐야 함
        }
    })
    .catch(err => {
        console.error('❌ SNS 공유 보너스 요청 실패:', err);
        
        // 서버 에러 응답 처리
        if (err.data) {
            const errorData = err.data;
            if (errorData.error === 'cooldown') {
                bonusSystem.showToast(
                    '😊 이미 보너스를 받으셨어요!',
                    `${errorData.days_left}일 후에 다시 받을 수 있어요 (주 1회 제한)`,
                    'warning',
                    5000
                );
            } else if (errorData.error === 'server_not_ready') {
                bonusSystem.showToast(
                    '⚠️ 서버 준비 중이에요',
                    '잠시 후 다시 시도해주세요!',
                    'warning',
                    5000
                );
            } else if (errorData.error === 'server_error') {
                bonusSystem.showToast(
                    '😔 일시적인 오류가 발생했어요',
                    '잠시 후 다시 시도해주세요!',
                    'error',
                    5000
                );
            } else {
                bonusSystem.showToast(
                    '🤷 보너스를 받을 수 없어요',
                    'SNS에 공유하신 후 다시 시도해주세요!',
                    'warning',
                    5000
                );
            }
        } else {
            // 네트워크 에러
            bonusSystem.showToast(
                '📡 인터넷 연결을 확인해주세요',
                '네트워크가 불안정해요. 잠시 후 다시 시도해주세요!',
                'error',
                5000
            );
        }
        
        button.disabled = false;
        button.textContent = originalText;
        // ❌ 모달 닫지 않음! 사용자가 토스트를 봐야 함
    });
}

// ========================================
// 🔌 기존 시스템 통합
// ========================================

// 분석 전 사용 횟수 체크
const originalAnalyze = window.analyzeBlog || function() {};
window.analyzeBlog = function() {
    if (!bonusSystem) {
        originalAnalyze();
        return;
    }
    
    const remaining = bonusSystem.getRemainingUsage();
    
    if (remaining <= 0) {
        bonusSystem.showToast(
            '사용 횟수 초과',
            '지금 바로 보너스 받고 계속 이용하세요!',
            'warning'
        );
        showUsageDetail();
        return;
    }
    
    // 사용 횟수 차감
    bonusSystem.decreaseUsage();
    
    // 원래 분석 함수 실행
    originalAnalyze();
};

// ========================================
// 🔑 마스터 계정 활성화 시스템
// ========================================

// URL 파라미터로 마스터 계정 활성화 - 제거됨 (시크릿 코드만 사용)
// (function checkAdminAccess() { ... })();

// Secret Code 입력 (로고 5번 클릭)
function setupSecretCodeAccess() {
    let clickCount = 0;
    let clickTimer = null;
    
    console.log('🔍 로고 요소 찾는 중...');
    
    // 로고 요소 찾기 (여러 선택자 시도)
    const logoSelectors = [
        '.logo-text',           // Repost 텍스트
        '.header-logo',         // 로고 링크
        '.header-logo span',    // 로고 내부 span
        'a[href="/"]',          // 홈 링크
        '.logo-icon'            // 이모지 아이콘
    ];
    
    let logo = null;
    for (const selector of logoSelectors) {
        logo = document.querySelector(selector);
        if (logo) {
            console.log(`✅ 로고 발견: ${selector}`, logo);
            break;
        }
    }
    
    if (!logo) {
        console.warn('⚠️ 로고 요소를 찾을 수 없습니다. 1초 후 재시도...');
        // DOM 로드 후 재시도
        setTimeout(setupSecretCodeAccess, 1000);
        return;
    }
    
    console.log('✅ 시크릿 코드 시스템 활성화: 로고를 3초 안에 5번 클릭하세요');
    
    // 클릭 가능하도록 스타일 설정
    logo.style.cursor = 'pointer';
    logo.style.userSelect = 'none';
    
    // 이벤트 리스너 등록
    logo.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        clickCount++;
        console.log(`🖱️ 클릭 ${clickCount}/5`);
        
        // 첫 클릭 시 타이머 시작
        if (clickCount === 1) {
            clickTimer = setTimeout(() => {
                console.log('⏱️ 타임아웃: 클릭 카운트 초기화');
                clickCount = 0;
            }, 3000);
        }
        
        // 5번 클릭 완료
        if (clickCount === 5) {
            clearTimeout(clickTimer);
            clickCount = 0;
            console.log('🔐 시크릿 코드 모달 표시!');
            showSecretCodeModal();
        }
    }, { capture: true }); // capture 모드로 우선 처리
    
    console.log('🎯 이벤트 리스너 등록 완료!');
}

// 🚀 페이지 로드 시 자동 실행
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupSecretCodeAccess);
} else {
    // 이미 로드된 경우 즉시 실행
    setupSecretCodeAccess();
}

// Secret Code 입력 모달
function showSecretCodeModal() {
    const html = `
        <div class="bonus-modal-overlay" onclick="closeSecretModal(event)" style="z-index: 10003;">
            <div class="bonus-modal" onclick="event.stopPropagation()" style="max-width: 400px;">
                <div class="bonus-modal-content">
                    <h2 class="bonus-modal-title" style="margin-bottom: 20px;">
                        🔐 관리자 인증
                    </h2>
                    
                    <div style="margin: 20px 0;">
                        <input 
                            type="password" 
                            id="secretCodeInput" 
                            placeholder="비밀 코드를 입력하세요"
                            style="
                                width: 100%;
                                padding: 16px;
                                border: 2px solid #e5e7eb;
                                border-radius: 12px;
                                font-size: 16px;
                                text-align: center;
                                letter-spacing: 2px;
                                transition: all 0.3s;
                            "
                            onkeypress="if(event.key==='Enter') verifySecretCode()"
                            autofocus
                        />
                    </div>
                    
                    <div style="display: flex; gap: 12px; margin-top: 24px;">
                        <button 
                            class="bonus-btn bonus-btn-secondary" 
                            onclick="closeSecretModal()"
                            style="flex: 1;"
                        >
                            취소
                        </button>
                        <button 
                            class="bonus-btn bonus-btn-primary" 
                            onclick="verifySecretCode()"
                            style="flex: 1;"
                        >
                            확인
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const container = document.getElementById('bonusModals');
    if (!container) {
        console.error('❌ bonusModals 컨테이너를 찾을 수 없습니다!');
        return;
    }
    
    container.innerHTML = html;
    
    // 🎨 부드러운 애니메이션을 위해 다음 프레임에 show 클래스 추가
    requestAnimationFrame(() => {
        const overlay = container.querySelector('.bonus-modal-overlay');
        if (overlay) {
            overlay.classList.add('show');
            console.log('✅ 모달 표시 완료!');
        } else {
            console.error('❌ overlay를 찾을 수 없습니다!');
        }
    });
    
    // 입력창 포커스
    setTimeout(() => {
        const input = document.getElementById('secretCodeInput');
        if (input) {
            input.focus();
            // 입력 시 테두리 색상 변경
            input.addEventListener('focus', function() {
                this.style.borderColor = '#667eea';
                this.style.boxShadow = '0 0 0 3px rgba(102, 126, 234, 0.1)';
            });
            input.addEventListener('blur', function() {
                this.style.borderColor = '#e5e7eb';
                this.style.boxShadow = 'none';
            });
        }
    }, 100);
}

// Secret Code 검증
function verifySecretCode() {
    const input = document.getElementById('secretCodeInput');
    const code = input ? input.value.trim() : '';
    
    // 비밀 코드 (프로덕션에서는 서버 검증 추가 가능)
    const validCodes = ['master2024'];
    
    if (validCodes.includes(code.toLowerCase())) {
        // 성공
        localStorage.setItem('repost_admin', 'true');
        
        // 입력창 성공 애니메이션
        input.style.borderColor = '#10b981';
        input.style.background = '#ecfdf5';
        
        // 모달 닫기
        setTimeout(() => {
            closeSecretModal();
            
            // 성공 알림
            if (bonusSystem && bonusSystem.showToast) {
                bonusSystem.showToast(
                    '🎉 인증 성공!',
                    '마스터 계정이 활성화되었습니다',
                    'success',
                    3000
                );
            }
            
            // 배지 업데이트
            if (bonusSystem) {
                bonusSystem.updateUsageBadge();
            }
            
            // 페이지 새로고침 (선택사항)
            setTimeout(() => {
                location.reload();
            }, 1500);
        }, 500);
        
    } else {
        // 실패
        input.style.borderColor = '#ef4444';
        input.style.background = '#fef2f2';
        input.value = '';
        input.placeholder = '❌ 잘못된 코드입니다';
        
        // 흔들기 애니메이션
        input.style.animation = 'shake 0.5s';
        setTimeout(() => {
            input.style.animation = '';
            input.style.borderColor = '#e5e7eb';
            input.style.background = 'white';
            input.placeholder = '다시 입력해주세요';
        }, 500);
    }
}

// Secret Code 모달 닫기
function closeSecretModal(event) {
    if (event && event.target.classList.contains('bonus-modal')) {
        return;
    }
    
    const modal = document.getElementById('secretCodeModal');
    if (modal) {
        modal.remove();
    }
}

// 흔들기 애니메이션 추가
if (!document.getElementById('shakeAnimation')) {
    const style = document.createElement('style');
    style.id = 'shakeAnimation';
    style.textContent = `
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
            20%, 40%, 60%, 80% { transform: translateX(10px); }
        }
    `;
    document.head.appendChild(style);
}

console.log('🎁 보너스 시스템 로드 완료!');
console.log('🔑 마스터 계정 시스템 활성화됨');

