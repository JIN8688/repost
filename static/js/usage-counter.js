// ========================================
// 🎯 사용 횟수 표시 시스템 (Usage Counter)
// ========================================

class UsageCounter {
    constructor() {
        this.init();
    }

    init() {
        console.log('🎯 사용 횟수 표시 시스템 초기화');
        this.updateDisplay();
        
        // 페이지 로드 시 업데이트
        window.addEventListener('load', () => {
            this.updateDisplay();
        });
    }

    // 사용 데이터 가져오기
    getUsageData() {
        const today = new Date().toDateString();
        let data = localStorage.getItem('repost_usage_data');
        
        if (!data) {
            // 첫 방문
            const trialStatus = this.getTrialStatus();
            const dailyLimit = trialStatus.isNewUser ? 7 : 3;
            
            data = {
                date: today,
                baseUsage: 0,
                baseLimit: dailyLimit,
                bonuses: [],
                isNewUser: trialStatus.isNewUser
            };
            
            localStorage.setItem('repost_usage_data', JSON.stringify(data));
            return data;
        }
        
        data = JSON.parse(data);
        
        // 날짜가 바뀌면 초기화
        if (data.date !== today) {
            const trialStatus = this.getTrialStatus();
            const dailyLimit = trialStatus.isNewUser ? 7 : 3;
            
            data = {
                date: today,
                baseUsage: 0,
                baseLimit: dailyLimit,
                bonuses: data.bonuses || [], // 보너스는 유지
                isNewUser: trialStatus.isNewUser
            };
            
            localStorage.setItem('repost_usage_data', JSON.stringify(data));
        }
        
        return data;
    }

    // 체험 기간 상태 확인
    getTrialStatus() {
        const firstVisit = localStorage.getItem('repost_first_visit');
        
        if (!firstVisit) {
            // 첫 방문
            return {
                isNewUser: true,
                daysLeft: 7,
                statusText: '🎉 신규 사용자 (7일 체험)'
            };
        }
        
        const firstDate = new Date(firstVisit);
        const today = new Date();
        const daysPassed = Math.floor((today - firstDate) / (1000 * 60 * 60 * 24));
        const daysLeft = Math.max(0, 7 - daysPassed);
        
        return {
            isNewUser: daysLeft > 0,
            daysLeft: daysLeft,
            statusText: daysLeft > 0 
                ? `🎉 체험 기간 (${daysLeft}일 남음)` 
                : '일반 사용자'
        };
    }

    // 남은 횟수 계산
    getRemainingCount() {
        // 🔑 마스터 계정: 무제한 사용
        if (localStorage.getItem('repost_admin') === 'true') {
            return {
                total: 9999,
                base: 9999,
                bonus: 0,
                limit: 9999,
                isMaster: true
            };
        }
        
        const data = this.getUsageData();
        
        // 기본 사용 가능 횟수
        const baseRemaining = Math.max(0, data.baseLimit - data.baseUsage);
        
        // 보너스 사용 가능 횟수
        let bonusRemaining = 0;
        const today = new Date();
        
        if (data.bonuses && data.bonuses.length > 0) {
            data.bonuses.forEach(bonus => {
                const expiryDate = new Date(bonus.expiryDate);
                if (today <= expiryDate && bonus.remaining > 0) {
                    bonusRemaining += bonus.remaining;
                }
            });
        }
        
        return {
            total: baseRemaining + bonusRemaining,
            base: baseRemaining,
            bonus: bonusRemaining,
            limit: data.baseLimit,
            isMaster: false
        };
    }

    // 화면 업데이트
    updateDisplay() {
        const remaining = this.getRemainingCount();
        const trialStatus = this.getTrialStatus();
        
        const displayText = remaining.isMaster 
            ? `오늘 9999회 남음` 
            : `오늘 ${remaining.total}회 남음`;
        
        // 메인 카운터 업데이트 (홈페이지)
        const counterEl = document.getElementById('remainingCount');
        if (counterEl) {
            counterEl.textContent = displayText;
        }
        
        // 풋터 카운터 업데이트 (모바일)
        const footerCounterEl = document.getElementById('footerRemainingCount');
        if (footerCounterEl) {
            footerCounterEl.textContent = displayText;
        }
        
        if (remaining.isMaster) {
            console.log('🔑 마스터 계정: 무제한 사용 (9999회)');
        } else {
            console.log(`🎯 남은 횟수: ${remaining.total}회 (기본: ${remaining.base}, 보너스: ${remaining.bonus})`);
            
            // 0회가 되면 팝업 자동 표시
            if (remaining.total === 0) {
                setTimeout(() => {
                    console.log('⚠️ 사용 횟수 소진! 팝업 표시');
                    if (typeof showUsageDetail === 'function') {
                        showUsageDetail();
                    }
                }, 500); // 0.5초 후 팝업 (자연스러운 딜레이)
            }
        }
    }

    // 사용 횟수 차감
    decrementUsage() {
        // 🔑 마스터 계정: 사용 횟수 차감 안 함
        if (localStorage.getItem('repost_admin') === 'true') {
            console.log('🔑 마스터 계정: 무제한 사용 (차감 안 함)');
            return {
                success: true,
                remaining: 9999,
                isMaster: true
            };
        }
        
        const data = this.getUsageData();
        const remaining = this.getRemainingCount();
        
        // 사용 불가
        if (remaining.total === 0) {
            return {
                success: false,
                message: '오늘의 무료 사용 횟수를 모두 사용하셨습니다!',
                showUpgradePopup: true
            };
        }
        
        // 보너스부터 사용
        if (remaining.bonus > 0) {
            const today = new Date();
            
            for (let i = 0; i < data.bonuses.length; i++) {
                const bonus = data.bonuses[i];
                const expiryDate = new Date(bonus.expiryDate);
                
                if (today <= expiryDate && bonus.remaining > 0) {
                    bonus.remaining--;
                    console.log(`🎁 보너스 사용: ${bonus.type} (남은: ${bonus.remaining}회)`);
                    break;
                }
            }
        } else {
            // 기본 사용 횟수 차감
            data.baseUsage++;
            console.log(`📊 기본 횟수 사용: ${data.baseUsage}/${data.baseLimit}`);
        }
        
        localStorage.setItem('repost_usage_data', JSON.stringify(data));
        this.updateDisplay();
        
        return {
            success: true,
            remaining: this.getRemainingCount().total
        };
    }

    // 보너스 추가 (행동 보상)
    addBonus(type, count, days = 7) {
        const data = this.getUsageData();
        
        const expiryDate = new Date();
        expiryDate.setDate(expiryDate.getDate() + days);
        
        const bonus = {
            type: type,
            amount: count,
            remaining: count,
            expiryDate: expiryDate.toISOString(),
            earnedAt: new Date().toISOString()
        };
        
        if (!data.bonuses) {
            data.bonuses = [];
        }
        
        data.bonuses.push(bonus);
        localStorage.setItem('repost_usage_data', JSON.stringify(data));
        
        this.updateDisplay();
        
        console.log(`🎁 보너스 추가: ${type} +${count}회 (${days}일간 유효)`);
        
        return {
            success: true,
            bonus: bonus
        };
    }
}

// 전역 인스턴스 생성
const usageCounter = new UsageCounter();

// 전역 함수 (기존 호환성)
function updateUsageCounter() {
    usageCounter.updateDisplay();
}

// 사용 상세 보기 (기존 함수 연동)
function showUsageDetail() {
    // bonus-system.js의 함수 호출
    if (typeof bonusSystem !== 'undefined' && bonusSystem.showUsageDetail) {
        bonusSystem.showUsageDetail();
    } else {
        alert('사용 횟수 정보를 불러올 수 없습니다.');
    }
}

console.log('✅ usage-counter.js 로드 완료');

