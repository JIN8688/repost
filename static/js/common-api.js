/**
 * Repost - 공통 API 처리 함수
 * 인증 및 사용 제한 처리
 */

// API 호출 공통 함수
async function callAPI(url, data, showToast = true) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        // 로그인 필요
        if (result.login_required) {
            if (showToast && typeof showToast === 'function') {
                showToast('로그인 필요', '이 기능을 사용하려면 로그인이 필요합니다.', 'error');
            } else {
                alert('이 기능을 사용하려면 로그인이 필요합니다.');
            }
            
            // 2초 후 로그인 페이지로 이동
            setTimeout(() => {
                window.location.href = '/login-page';
            }, 2000);
            
            return null;
        }

        // 사용 제한 도달
        if (result.limit_reached) {
            if (showToast && typeof showToast === 'function') {
                showToast(
                    '사용 제한 도달', 
                    `${result.error} - 더 많은 기능을 이용하시려면 요금제를 업그레이드하세요.`, 
                    'error'
                );
            } else {
                alert(`${result.error}\n\n더 많은 기능을 이용하시려면 요금제를 업그레이드하세요.`);
            }
            
            // 3초 후 요금제 페이지로 이동
            setTimeout(() => {
                window.location.href = '/pricing';
            }, 3000);
            
            return null;
        }

        // 일반 에러
        if (!result.success && result.error) {
            if (showToast && typeof showToast === 'function') {
                showToast('오류', result.error, 'error');
            } else {
                alert(result.error);
            }
            return null;
        }

        return result;

    } catch (error) {
        console.error('API 호출 오류:', error);
        
        if (showToast && typeof showToast === 'function') {
            showToast('오류', '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.', 'error');
        } else {
            alert('서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
        }
        
        return null;
    }
}

// 사용자 정보 가져오기
async function getUserInfo() {
    try {
        const response = await fetch('/api/user-info');
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        console.error('사용자 정보 가져오기 오류:', error);
        return null;
    }
}

// 로그아웃 처리
function logout() {
    if (confirm('로그아웃하시겠습니까?')) {
        window.location.href = '/logout';
    }
}

