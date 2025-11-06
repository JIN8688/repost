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
        
        // 신규 사용자 여부 확인
        const isNewUser = this.checkIfNewUser();
        const dailyLimit = isNewUser ? 7 : 3; // 7일 이내면 7회, 아니면 3회
        
        const usageData = {
            date: today,
            baseUsage: 0,
            baseLimit: dailyLimit,
            bonuses: this.loadBonuses(),
            isNewUser: isNewUser
        };
        
        localStorage.setItem('repost_usage_data', JSON.stringify(usageData));
        
        console.log(`📊 일일 사용 횟수 초기화: ${dailyLimit}회 (신규: ${isNewUser})`);
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
        const data = JSON.parse(localStorage.getItem('repost_usage_data'));
        if (!data) return 0;
        
        const baseRemaining = data.baseLimit - data.baseUsage;
        const bonusRemaining = data.bonuses.reduce((sum, b) => sum + b.remaining, 0);
        
        return Math.max(0, baseRemaining + bonusRemaining);
    }

    // 사용 횟수 감소
    decreaseUsage() {
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
                                <span class="usage-item-value">+3회</span>
                            </div>
                            <div class="usage-item">
                                <span class="usage-item-label">💎 Basic 플랜</span>
                                <span class="usage-item-value">무제한</span>
                            </div>
                        </div>
                        
                        <div class="bonus-actions">
                            <button class="bonus-action-btn" onclick="showReferralModal()">
                                친구 추천하기
                            </button>
                            <button class="bonus-action-btn" onclick="showShareModal()">
                                SNS 공유하기
                            </button>
                            <button class="bonus-action-btn upgrade-btn" onclick="alert('업그레이드 기능은 곧 출시됩니다!')">
                                💎 Basic 50% 할인
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
        // Confetti 효과
        if (typeof confetti !== 'undefined') {
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#667eea', '#764ba2', '#f59e0b', '#22c55e']
            });
        }
        
        // 토스트 알림
        this.showToast(
            '축하합니다!',
            `${type === 'referral' ? '친구 추천' : 'SNS 공유'} 보너스 +${amount}회 획득!`,
            'success'
        );
        
        // 보너스 모달
        setTimeout(() => {
            this.showBonusModal(type, amount);
        }, 1000);
        
        // 배지 업데이트
        this.updateUsageBadge();
    }

    // 토스트 알림
    showToast(title, message, type = 'success') {
        const icons = {
            success: '🎉',
            info: 'ℹ️',
            warning: '⚠️'
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
        
        // 3초 후 자동 제거
        setTimeout(() => {
            toast.style.animation = 'toastPopOut 0.3s ease-out forwards';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
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
                            ${type === 'referral' ? 
                                '<button class="bonus-btn bonus-btn-primary" onclick="showReferralModal()">더 많은 친구 추천하기</button>' :
                                '<button class="bonus-btn bonus-btn-primary" onclick="showShareModal()">다시 공유하기</button>'
                            }
                            <button class="bonus-btn bonus-btn-secondary" onclick="closeModal()">확인</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        const container = document.getElementById('bonusModals');
        container.innerHTML = html;
    }

    // 친구 추천 진행률
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
                <div class="bonus-progress-label">추천 현황: ${count}/5명 완료</div>
                <div class="bonus-progress-bar">
                    <div class="bonus-progress-fill" style="width: ${percent}%"></div>
                </div>
                <div class="bonus-stars">${stars.join('')}</div>
                ${count >= 5 ? '<p style="margin-top: 12px; font-size: 14px; color: #7debc8; text-shadow: 0 0 15px rgba(125, 235, 200, 0.5);">🎁 Basic 1개월 무료 획득!</p>' : 
                  count >= 3 ? '<p style="margin-top: 12px; font-size: 14px; color: #a5b4fc; text-shadow: 0 0 15px rgba(165, 180, 252, 0.5);">💡 2명만 더 추천하면 Basic 무료!</p>' : ''}
            </div>
        `;
    }
}

// 전역 보너스 시스템 인스턴스
let bonusSystem;

// 페이지 로드 시 초기화
window.addEventListener('load', () => {
    bonusSystem = new BonusSystem();
});

// ========================================
// 🎁 모달 및 UI 함수들
// ========================================

// 사용 횟수 상세 모달
function showUsageDetail() {
    const data = JSON.parse(localStorage.getItem('repost_usage_data'));
    if (!data) return;
    
    const baseRemaining = data.baseLimit - data.baseUsage;
    const bonusTotal = data.bonuses.reduce((sum, b) => sum + b.remaining, 0);
    const total = baseRemaining + bonusTotal;
    
    const bonusesHtml = data.bonuses.map(b => {
        const typeText = b.type === 'referral' ? '친구 추천' : 'SNS 공유';
        const daysLeft = Math.ceil((b.expiresAt - Date.now()) / (1000 * 60 * 60 * 24));
        
        return `
            <div class="usage-item">
                <span class="usage-item-label">${typeText} (${daysLeft}일 남음)</span>
                <span class="usage-item-value">+${b.remaining}회</span>
            </div>
        `;
    }).join('');
    
    const html = `
        <div class="bonus-modal-overlay" onclick="closeModal(event)">
            <div class="bonus-modal usage-detail-modal" onclick="event.stopPropagation()">
                <div class="bonus-modal-content">
                    <h2 class="modal-title">
                        📊 사용 횟수 상세
                    </h2>
                    
                    <div class="usage-section">
                        <div class="usage-section-title">🔹 기본 제공</div>
                        <div class="usage-item">
                            <span class="usage-item-label">${data.isNewUser ? '신규 사용자 (7일)' : '일일 제공'}</span>
                            <span class="usage-item-value">${data.baseLimit}회/일</span>
                        </div>
                        <div class="usage-item">
                            <span class="usage-item-label">사용</span>
                            <span class="usage-item-value">${data.baseUsage}회</span>
                        </div>
                        <div class="usage-item">
                            <span class="usage-item-label">남음</span>
                            <span class="usage-item-value">${baseRemaining}회</span>
                        </div>
                    </div>
                    
                    ${data.bonuses.length > 0 ? `
                        <div class="usage-section">
                            <div class="usage-section-title">🎁 보너스</div>
                            ${bonusesHtml}
                            <div class="usage-item" style="border-top: 2px solid #667eea; margin-top: 8px; padding-top: 12px;">
                                <span class="usage-item-label" style="font-weight: 700;">총 보너스</span>
                                <span class="usage-item-value">${bonusTotal}회</span>
                            </div>
                        </div>
                    ` : ''}
                    
            <div class="total-remaining-box">
                <div style="font-size: 14px; color: #6b7280; margin-bottom: 8px;">총 남은 횟수</div>
                <div class="remaining-count ${total === 0 ? 'zero-count' : ''}" style="font-size: ${total === 0 ? '48px' : '36px'}; font-weight: 900; color: ${total === 0 ? '#f59e0b' : '#667eea'};">${total}회</div>
                <div style="font-size: 12px; color: #9ca3af; margin-top: 8px;">📅 내일 자정 초기화</div>
            </div>
            
            <div style="margin-top: 24px;">
                <div style="font-size: 16px; font-weight: 700; color: #1a202c; margin-bottom: 8px; text-align: center;">
                    ${total === 0 ? '🚨 지금 바로 보너스 받으세요!' : '💡 더 많은 보너스 받기'}
                </div>
                ${total === 0 ? '<div style="font-size: 13px; color: #6b7280; margin-bottom: 16px; text-align: center;">친구 추천 5회 · SNS 공유 3회 즉시 지급!</div>' : ''}
                
                <div class="bonus-actions">
                    <button class="bonus-action-btn ${total === 0 ? 'pulse' : ''}" onclick="showReferralModal()">
                        👥 친구 추천 (+5회)
                    </button>
                    <button class="bonus-action-btn ${total === 0 ? 'pulse' : ''}" onclick="showShareModal()">
                        📢 SNS 공유 (+3회)
                    </button>
                </div>
            </div>
                    
            <button class="bonus-btn-close" onclick="closeModal()" style="width: 100%; margin-top: 20px;">
                닫기
            </button>
                </div>
            </div>
        </div>
    `;
    
    const container = document.getElementById('bonusModals');
    container.innerHTML = html;
}

// 친구 추천 모달
function showReferralModal() {
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
                        <button class="share-btn" id="copyLinkBtn" onclick="copyReferralLink('${referralLink}', this)">
                            <span class="share-btn-icon">📋</span>
                            <span class="share-btn-text">링크 복사</span>
                        </button>
                        <button class="share-btn" onclick="shareReferralLink('${referralLink}')">
                            <span class="share-btn-icon">📤</span>
                            <span>공유하기</span>
                        </button>
                    </div>
                    
                    <button class="bonus-btn bonus-btn-primary" onclick="claimReferralBonus(this)" style="width: 100%; margin-top: 24px; font-size: 16px; padding: 18px;">
                        🎁 보너스 받기 (+5회)
                    </button>
                    
                    <div style="background: #fef3c7; border-radius: 8px; padding: 12px; margin-top: 16px; border-left: 3px solid #f59e0b;">
                        <div style="font-size: 12px; color: #92400e; line-height: 1.6;">
                            <strong>⚠️ 주의사항</strong><br>
                            • 자신의 링크는 사용 불가<br>
                            • 주 1회만 보너스 지급<br>
                            • 친구가 실제로 접속해야 인정
                        </div>
                    </div>
                    
                    <button class="bonus-btn bonus-btn-secondary" onclick="closeModal()" style="width: 100%; margin-top: 20px;">
                        닫기
                    </button>
                </div>
            </div>
        </div>
    `;
    
    const container = document.getElementById('bonusModals');
    container.innerHTML = html;
}

// SNS 공유 모달
function showShareModal() {
    const shareUrl = 'https://repost.kr';
    const shareText = 'Repost 덕분에 블로그 댓글 고민 끝! AI가 찰떡같은 댓글 추천해줘요 👍';
    
    const html = `
        <div class="bonus-modal-overlay" onclick="closeModal(event)">
            <div class="bonus-modal share-modal" onclick="event.stopPropagation()">
                <div class="bonus-modal-content">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <button onclick="showUsageDetail()" style="background: none; border: none; cursor: pointer; padding: 8px; margin-right: 10px; display: flex; align-items: center; color: #667eea; font-size: 24px; transition: transform 0.2s;">
                            ←
                        </button>
                        <h2 class="bonus-modal-title" style="margin: 0; flex: 1;">
                            📢 SNS 공유하기
                        </h2>
                    </div>
                    
                    <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 12px; padding: 20px; margin: 20px 0; border-left: 4px solid #667eea;">
                        <div style="font-size: 15px; font-weight: 700; color: #1a202c; margin-bottom: 12px;">
                            💡 보너스 받는 방법 (2단계)
                        </div>
                        <div style="font-size: 13px; color: #4b5563; line-height: 1.8;">
                            <div style="margin-bottom: 8px;">
                                <strong style="color: #667eea;">1단계:</strong> 아래 "공유하기" 버튼으로 SNS에 공유
                            </div>
                            <div>
                                <strong style="color: #667eea;">2단계:</strong> 하단 "보너스 받기" 버튼 클릭
                            </div>
                        </div>
                    </div>
                    
                    <button class="share-btn" onclick="shareToSocial('${shareUrl}', '${shareText}')" style="width: 100%; margin: 20px 0; padding: 20px;">
                        <span class="share-btn-icon" style="font-size: 28px;">📤</span>
                        <span style="font-size: 16px; font-weight: 700;">공유하기</span>
                    </button>
                    
                    <button class="bonus-btn bonus-btn-primary" onclick="claimShareBonus(this)" style="width: 100%; margin-top: 16px; font-size: 16px; padding: 18px;">
                        🎁 보너스 받기 (+3회)
                    </button>
                    
                    <div style="background: #fef3c7; border-radius: 8px; padding: 12px; margin-top: 16px; border-left: 3px solid #f59e0b;">
                        <div style="font-size: 12px; color: #92400e; line-height: 1.6;">
                            <strong>⚠️ 주의사항</strong><br>
                            • 주 1회만 보너스 지급<br>
                            • 공유 후 "보너스 받기" 클릭 필수
                        </div>
                    </div>
                    
                    <button class="bonus-btn bonus-btn-secondary" onclick="closeModal()" style="width: 100%; margin-top: 20px;">
                        닫기
                    </button>
                </div>
            </div>
        </div>
    `;
    
    const container = document.getElementById('bonusModals');
    container.innerHTML = html;
}

// 모달 닫기
function closeModal(event) {
    if (event && event.target.classList.contains('bonus-modal')) {
        return; // 모달 내부 클릭은 무시
    }
    
    const container = document.getElementById('bonusModals');
    container.innerHTML = '';
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
            if (bonusSystem && bonusSystem.showToast) {
                bonusSystem.showToast(
                    '공유 완료! 📤',
                    '친구에게 전달되었습니다',
                    'success'
                );
            }
        })
        .catch((err) => {
            if (err.name !== 'AbortError') {
                console.error('❌ 공유 실패:', err);
            }
        });
    } else {
        // Web Share API 미지원 시 링크 복사
        copyReferralLink(url, document.querySelector('#copyLinkBtn'));
        bonusSystem.showToast(
            '링크 복사 완료',
            '카톡이나 문자로 공유해주세요!',
            'info'
        );
    }
}

// SNS 공유 (Web Share API)
function shareToSocial(url, text) {
    console.log('📱 SNS 공유:', url);
    
    if (navigator.share) {
        navigator.share({
            title: 'Repost - AI 블로그 댓글 추천',
            text: text,
            url: url
        })
        .then(() => {
            console.log('✅ 공유 성공');
            if (bonusSystem && bonusSystem.showToast) {
                bonusSystem.showToast(
                    '공유 완료! 📱',
                    '감사합니다!',
                    'success'
                );
            }
        })
        .catch((err) => {
            if (err.name !== 'AbortError') {
                console.error('❌ 공유 실패:', err);
            }
        });
    } else {
        // PC에서는 링크 복사
        const textArea = document.createElement("textarea");
        textArea.value = url;
        textArea.style.position = "fixed";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        bonusSystem.showToast(
            '링크 복사 완료',
            'SNS에 붙여넣어 주세요!',
            'info'
        );
    }
}

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
            }, 1500);
        } else {
            console.log('❌ 서버 응답 실패:', data.error);
            // 에러 타입별 친근한 메시지
            if (data.error === 'cooldown') {
                bonusSystem.showToast(
                    '😊 이미 보너스를 받으셨어요!',
                    `${data.days_left}일 후에 다시 받을 수 있어요 (주 1회 제한)`,
                    'warning'
                );
            } else if (data.error === 'no_referral') {
                bonusSystem.showToast(
                    '🤔 아직 친구가 접속하지 않았어요',
                    '친구에게 링크를 공유하고 접속을 기다려보세요!',
                    'warning'
                );
            } else if (data.error === 'self_referral') {
                bonusSystem.showToast(
                    '😅 자신의 링크는 사용할 수 없어요',
                    '다른 친구에게 공유해주세요!',
                    'warning'
                );
            } else if (data.error === 'server_error') {
                bonusSystem.showToast(
                    '😔 일시적인 오류가 발생했어요',
                    '잠시 후 다시 시도해주세요!',
                    'error'
                );
            } else {
                bonusSystem.showToast(
                    '🤷 보너스를 받을 수 없어요',
                    '친구가 링크를 클릭했는지 확인해보세요!',
                    'warning'
                );
            }
            button.disabled = false;
            button.textContent = originalText;
        }
    })
    .catch(err => {
        console.error('❌ 친구 추천 보너스 요청 실패:', err);
        
        // 서버 에러 응답 처리
        if (err.data) {
            const errorData = err.data;
            if (errorData.error === 'cooldown') {
                bonusSystem.showToast(
                    '😊 이미 보너스를 받으셨어요!',
                    `${errorData.days_left}일 후에 다시 받을 수 있어요 (주 1회 제한)`,
                    'warning'
                );
            } else if (errorData.error === 'no_referral') {
                bonusSystem.showToast(
                    '🤔 아직 친구가 접속하지 않았어요',
                    '친구에게 링크를 공유하고 접속을 기다려보세요!',
                    'warning'
                );
            } else if (errorData.error === 'self_referral') {
                bonusSystem.showToast(
                    '😅 자신의 링크는 사용할 수 없어요',
                    '다른 친구에게 공유해주세요!',
                    'warning'
                );
            } else if (errorData.error === 'server_not_ready') {
                bonusSystem.showToast(
                    '⚠️ 서버 준비 중이에요',
                    '잠시 후 다시 시도해주세요!',
                    'warning'
                );
            } else {
                bonusSystem.showToast(
                    '😔 일시적인 오류가 발생했어요',
                    '잠시 후 다시 시도해주세요!',
                    'error'
                );
            }
        } else {
            // 네트워크 에러
            bonusSystem.showToast(
                '📡 인터넷 연결을 확인해주세요',
                '네트워크가 불안정해요. 잠시 후 다시 시도해주세요!',
                'error'
            );
        }
        
        button.disabled = false;
        button.textContent = originalText;
    });
}

// SNS 공유 보너스 받기
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
                    'warning'
                );
            } else if (data.error === 'server_error') {
                bonusSystem.showToast(
                    '😔 일시적인 오류가 발생했어요',
                    '잠시 후 다시 시도해주세요!',
                    'error'
                );
            } else {
                bonusSystem.showToast(
                    '🤷 보너스를 받을 수 없어요',
                    'SNS에 공유하신 후 다시 시도해주세요!',
                    'warning'
                );
            }
            button.disabled = false;
            button.textContent = originalText;
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
                    'warning'
                );
            } else if (errorData.error === 'server_not_ready') {
                bonusSystem.showToast(
                    '⚠️ 서버 준비 중이에요',
                    '잠시 후 다시 시도해주세요!',
                    'warning'
                );
            } else if (errorData.error === 'server_error') {
                bonusSystem.showToast(
                    '😔 일시적인 오류가 발생했어요',
                    '잠시 후 다시 시도해주세요!',
                    'error'
                );
            } else {
                bonusSystem.showToast(
                    '🤷 보너스를 받을 수 없어요',
                    'SNS에 공유하신 후 다시 시도해주세요!',
                    'warning'
                );
            }
        } else {
            // 네트워크 에러
            bonusSystem.showToast(
                '📡 인터넷 연결을 확인해주세요',
                '네트워크가 불안정해요. 잠시 후 다시 시도해주세요!',
                'error'
            );
        }
        
        button.disabled = false;
        button.textContent = originalText;
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

console.log('🎁 보너스 시스템 로드 완료!');

