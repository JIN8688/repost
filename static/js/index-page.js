        // 현재 블로그 URL 저장
        let currentBlogUrl = '';

        // Enter 키로 분석 실행
        document.getElementById('blogUrl').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                analyzeBlog();
            }
        });

        // 블로그로 이동하는 함수
        function goToBlog() {
            if (!currentBlogUrl) return;
            
            // 📊 GA4: 블로그 이동 이벤트
            if (typeof gtag !== 'undefined') {
                gtag('event', 'blog_visit', {
                    'event_category': 'engagement',
                    'event_label': 'go_to_blog',
                    'value': 1
                });
                console.log('📊 GA4 이벤트 전송: blog_visit (블로그 이동)');
            }
            
            // 📊 백엔드: 블로그 이동 이벤트
            trackEvent('blog_visit', { url: currentBlogUrl.slice(0, 100) });
            
            // 카카오톡/인앱 브라우저 감지
            const isInAppBrowser = /KAKAOTALK|Messenger|Instagram|Line|NAVER/.test(navigator.userAgent);
            const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
            
            if (isInAppBrowser && isMobile) {
                // 인앱 브라우저일 경우 - 사용자에게 선택 옵션 제공
                showBrowserOptions(currentBlogUrl);
            } else {
                // 일반 브라우저 - 그냥 새 탭으로 열기
                window.open(currentBlogUrl, '_blank');
            }
        }
        
        function showBrowserOptions(url) {
            // 커스텀 알림 생성
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                padding: 20px;
            `;
            
            const modal = document.createElement('div');
            modal.style.cssText = `
                background: white;
                border-radius: 20px;
                padding: 30px;
                max-width: 400px;
                width: 100%;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            `;
            
            modal.innerHTML = `
                <div style="font-size: 2em; margin-bottom: 15px;">🔓</div>
                <h3 style="color: #333; margin-bottom: 15px; font-size: 1.2em;">
                    로그인 상태 유지하기
                </h3>
                <p style="color: #666; margin-bottom: 25px; line-height: 1.6;">
                    카카오톡에서는 네이버 로그인이 풀릴 수 있습니다.<br>
                    편하게 댓글을 달려면 아래 방법을 선택하세요!
                </p>
                <div style="display: flex; flex-direction: column; gap: 12px;">
                    <button onclick="openInNaver('${url}')" style="
                        background: linear-gradient(135deg, #00C73C 0%, #00B533 100%);
                        color: white;
                        border: none;
                        padding: 15px 20px;
                        border-radius: 12px;
                        font-size: 1em;
                        font-weight: 600;
                        cursor: pointer;
                        transition: transform 0.2s;
                    " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                        📱 네이버 앱으로 열기 (추천)
                    </button>
                    <button onclick="openInExternalBrowser('${url}')" style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        padding: 15px 20px;
                        border-radius: 12px;
                        font-size: 1em;
                        font-weight: 600;
                        cursor: pointer;
                        transition: transform 0.2s;
                    " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                        🌐 Safari/Chrome으로 열기
                    </button>
                    <button onclick="openInCurrentTab('${url}')" style="
                        background: #f0f0f0;
                        color: #666;
                        border: none;
                        padding: 12px 20px;
                        border-radius: 12px;
                        font-size: 0.95em;
                        cursor: pointer;
                    ">
                        그냥 여기서 열기
                    </button>
                    <button onclick="closeBrowserModal()" style="
                        background: transparent;
                        color: #999;
                        border: none;
                        padding: 10px;
                        font-size: 0.9em;
                        cursor: pointer;
                    ">
                        닫기
                    </button>
                </div>
            `;
            
            overlay.appendChild(modal);
            document.body.appendChild(overlay);
            overlay.id = 'browserModal';
            
            // 오버레이 클릭 시 닫기
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    closeBrowserModal();
                }
            });
        }
        
        function openInNaver(url) {
            // 네이버 앱 딥링크로 시도
            const naverAppUrl = 'naversearchapp://inappbrowser?url=' + encodeURIComponent(url);
            window.location.href = naverAppUrl;
            
            // 1초 후 앱이 안 열리면 일반 링크로
            setTimeout(() => {
                closeBrowserModal();
            }, 1000);
        }
        
        function openInExternalBrowser(url) {
            // 외부 브라우저로 열기 안내
            const message = 'URL이 복사되었습니다!\n\nSafari나 Chrome을 열어서 붙여넣기 해주세요:\n' + url;
            
            // URL 클립보드에 복사
            navigator.clipboard.writeText(url).then(() => {
                alert(message);
                closeBrowserModal();
            }).catch(() => {
                // 복사 실패 시 프롬프트로 표시
                prompt('이 URL을 복사해서 Safari/Chrome에 붙여넣으세요:', url);
                closeBrowserModal();
            });
        }
        
        function openInCurrentTab(url) {
            window.open(url, '_blank');
            closeBrowserModal();
        }
        
        function closeBrowserModal() {
            const modal = document.getElementById('browserModal');
            if (modal) {
                modal.remove();
            }
        }

        // 페이지 초기화 (새로고침 시)
        function initializePage() {
            // 모든 결과 영역 숨기기
            document.getElementById('loading').style.display = 'none';
            document.getElementById('loading').classList.remove('show');
            document.getElementById('blogInfo').classList.remove('show');
            document.getElementById('commentsSection').classList.remove('show');
            document.getElementById('goToBlogBtn').classList.remove('show');
            document.getElementById('errorMsg').classList.remove('show');
            
            // 3가지 강점 카드 표시
            const features = document.querySelector('.features');
            if (features) {
                features.style.display = 'grid';
            }
            
            // 현재 블로그 URL 초기화
            currentBlogUrl = '';
        }

        // 입력란 초기화 함수
        function resetInput() {
            // 입력란 초기화
            document.getElementById('blogUrl').value = '';
            
            // 페이지 초기화 실행
            initializePage();
            
            // 입력란에 포커스
            document.getElementById('blogUrl').focus();
            
            // 리프레쉬 애니메이션 효과
            const resetBtn = document.getElementById('resetBtn');
            resetBtn.style.animation = 'none';
            setTimeout(() => {
                resetBtn.style.animation = '';
            }, 10);
        }

        async function analyzeBlog() {
            const url = document.getElementById('blogUrl').value.trim();
            const analyzeBtn = document.getElementById('analyzeBtn');
            const loading = document.getElementById('loading');
            const errorMsg = document.getElementById('errorMsg');
            const blogInfo = document.getElementById('blogInfo');
            const commentsSection = document.getElementById('commentsSection');
            const goToBlogBtn = document.getElementById('goToBlogBtn');
            const features = document.querySelector('.features');

            // 초기화
            errorMsg.classList.remove('show');
            blogInfo.classList.remove('show');
            commentsSection.classList.remove('show');
            goToBlogBtn.classList.remove('show');

            if (!url) {
                showError('URL을 입력해주세요.');
                return;
            }

            // 네이버 블로그 URL 형식 검증 (무료 버전)
            const naverBlogPattern = /^https?:\/\/(m\.)?blog\.naver\.com\/.+/i;
            
            if (!naverBlogPattern.test(url)) {
                showError('올바른 네이버 블로그 URL을 입력해주세요.\n예시: https://blog.naver.com/아이디/글번호');
                return;
            }

            // 🔒 유료 버전에서 확장 가능한 플랫폼 (백엔드 구현 필요)
            // - 티스토리: /^https?:\/\/[^\/]+\.tistory\.com\/.+/i
            // - 워드프레스: /^https?:\/\/[^\/]+\.wordpress\.com\/.+/i
            // - 브런치: /^https?:\/\/brunch\.co\.kr\/@[^\/]+\/.+/i
            // - Velog: /^https?:\/\/velog\.io\/@[^\/]+\/.+/i
            // - Medium: /^https?:\/\/medium\.com\/@[^\/]+\/.+/i

            // 3단 카드 숨기기
            if (features) {
                features.style.display = 'none';
            }

            // 로딩 시작
            loading.classList.add('show');
            analyzeBtn.disabled = true;
            analyzeBtn.textContent = '분석 중...';
            
            // 로딩 애니메이션 시작
            startLoadingAnimation();

            try {
                // 🔑 마스터 계정 확인
                const isAdmin = localStorage.getItem('repost_admin') === 'true';
                
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        url: url,
                        isAdmin: isAdmin  // 마스터 계정 여부 전달
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || '오류가 발생했습니다.');
                }

                // 현재 블로그 URL 저장
                currentBlogUrl = url;

                // 블로그 정보 표시
                document.getElementById('blogTitle').textContent = data.blog.title;
                document.getElementById('blogContent').textContent = data.blog.content.substring(0, 200) + '...';
                blogInfo.classList.add('show');

                // 블로그 이동 버튼 표시
                goToBlogBtn.classList.add('show');

                // 댓글 목록 표시
                displayComments(data.comments);
                commentsSection.classList.add('show');

                // 📊 GA4: 분석 성공 이벤트
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'blog_analyzed', {
                        'event_category': 'engagement',
                        'event_label': 'success',
                        'value': 1
                    });
                    console.log('📊 GA4 이벤트 전송: blog_analyzed (성공)');
                } else {
                    console.error('❌ GA4가 로드되지 않았습니다!');
                }

            } catch (error) {
                showError(error.message);
                
                // 📊 GA4: 분석 실패 이벤트
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'blog_analyze_failed', {
                        'event_category': 'error',
                        'event_label': error.message,
                        'value': 0
                    });
                    console.log('📊 GA4 이벤트 전송: blog_analyze_failed (실패)', error.message);
                }
            } finally {
                // 로딩 애니메이션 중지
                stopLoadingAnimation();
                loading.classList.remove('show');
                analyzeBtn.disabled = false;
                analyzeBtn.textContent = '분석하기';
            }
        }

        function displayComments(comments) {
            const commentsList = document.getElementById('commentsList');
            commentsList.innerHTML = '';

            comments.forEach((comment, index) => {
                const commentItem = document.createElement('div');
                commentItem.className = 'comment-item';
                commentItem.innerHTML = `
                    <div class="comment-text">${comment}</div>
                    <button class="copy-btn" onclick="copyComment('${escapeHtml(comment)}', this)">
                        복사
                    </button>
                `;
                commentsList.appendChild(commentItem);
            });
        }

        function copyComment(text, button) {
            // 클립보드에 복사
            navigator.clipboard.writeText(text).then(() => {
                // 버튼 상태 변경
                const originalText = button.textContent;
                button.textContent = '복사됨! ✓';
                button.classList.add('copied');

                // 🎉 보너스 시스템 토스트 사용
                if (bonusSystem) {
                    bonusSystem.showToast(
                        '복사 완료!',
                        '댓글이 클립보드에 복사되었습니다',
                        'success'
                    );
                }

                // 2초 후 버튼 원래대로
                setTimeout(() => {
                    button.textContent = originalText;
                    button.classList.remove('copied');
                }, 2000);

                // 📊 GA4: 댓글 복사 이벤트
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'comment_copied', {
                        'event_category': 'engagement',
                        'event_label': 'copy_success',
                        'value': 1
                    });
                    console.log('📊 GA4 이벤트 전송: comment_copied (복사 성공)');
                }
                
                // 📊 백엔드: 댓글 복사 이벤트
                trackEvent('comment_copied', { comment: text.slice(0, 50) });

                // 💬 댓글 복사 후 3초 뒤 피드백 위젯 표시
                setTimeout(() => {
                    showFeedbackWidget();
                }, 3000);

                // 2초 후 원래 상태로
                setTimeout(() => {
                    button.textContent = originalText;
                    button.classList.remove('copied');
                }, 2000);
            }).catch(err => {
                alert('복사에 실패했습니다: ' + err);
                
                // 📊 GA4: 댓글 복사 실패 이벤트
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'comment_copy_failed', {
                        'event_category': 'error',
                        'event_label': err.message,
                        'value': 0
                    });
                }
            });
        }

        // 로딩 애니메이션 제어
        let loadingInterval;
        let progressInterval;
        
        function startLoadingAnimation() {
            const tips = [
                '💡 댓글을 복사한 후 바로 블로그로 이동할 수 있어요!',
                '✨ AI가 블로그 내용을 꼼꼼히 읽고 있어요!',
                '🎯 자연스러운 댓글로 블로거와 소통해보세요!',
                '📝 여러 댓글 중 마음에 드는 것을 골라보세요!',
                '🚀 모바일에서도 편하게 사용할 수 있어요!',
                '💬 진심 어린 댓글이 가장 좋은 댓글이에요!',
                '⭐ 블로그 내용을 반영한 맞춤 댓글을 만들고 있어요!'
            ];
            
            const steps = [
                '블로그 내용을 읽고 있어요... 📖',
                'AI가 내용을 분석하고 있어요... 🤔',
                '자연스러운 댓글을 만들고 있어요... ✍️',
                '마지막 손질 중이에요... ✨'
            ];
            
            // 랜덤 팁 표시
            const randomTip = tips[Math.floor(Math.random() * tips.length)];
            document.getElementById('loadingTip').textContent = randomTip;
            
            // 단계별 메시지 변경
            let stepIndex = 0;
            document.getElementById('loadingStep').textContent = steps[stepIndex];
            
            loadingInterval = setInterval(() => {
                stepIndex = (stepIndex + 1) % steps.length;
                document.getElementById('loadingStep').textContent = steps[stepIndex];
            }, 2000);
            
            // 프로그레스 바 애니메이션
            const progressBar = document.getElementById('progressBar');
            let progress = 0;
            
            progressInterval = setInterval(() => {
                if (progress < 90) {
                    progress += Math.random() * 15;
                    if (progress > 90) progress = 90;
                    progressBar.style.width = progress + '%';
                }
            }, 500);
        }
        
        function stopLoadingAnimation() {
            if (loadingInterval) {
                clearInterval(loadingInterval);
                loadingInterval = null;
            }
            if (progressInterval) {
                clearInterval(progressInterval);
                progressInterval = null;
            }
            
            // 프로그레스 바 완료
            const progressBar = document.getElementById('progressBar');
            progressBar.style.width = '100%';
            
            setTimeout(() => {
                progressBar.style.width = '0%';
            }, 500);
        }
        
        function showError(message) {
            const errorMsg = document.getElementById('errorMsg');
            errorMsg.textContent = message;
            errorMsg.classList.add('show');
        }

        function escapeHtml(text) {
            return text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }

        // 📊 이벤트 트래킹 함수
        // 🆔 고유 사용자 ID 생성 및 관리
        function getUserId() {
            let userId = localStorage.getItem('repost_user_id');
            
            if (!userId) {
                // 첫 방문: 고유 ID 생성
                userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                localStorage.setItem('repost_user_id', userId);
                
                // 첫 방문 시간 기록
                const firstVisit = new Date().toISOString();
                localStorage.setItem('repost_first_visit', firstVisit);
                
                console.log('🎉 첫 방문! 사용자 ID 생성:', userId);
            } else {
                console.log('✅ 사용자 ID 로드됨 (재방문):', userId);
            }
            
            return userId;
        }

        // 📊 세션 시작 시간 기록
        const sessionStartTime = Date.now();

        async function trackEvent(eventType, data = {}) {
            try {
                const userId = getUserId();
                const firstVisit = localStorage.getItem('repost_first_visit');
                
                // ⚠️ page_view는 세션 시간 제외 (로드 직후라 부정확)
                // 실제 행동(댓글 복사, 블로그 이동)만 세션 시간 포함
                const payload = { 
                    event: eventType, 
                    userId: userId,
                    firstVisit: firstVisit,
                    ...data 
                };
                
                // page_view가 아닌 경우만 세션 시간 포함
                if (eventType !== 'page_view') {
                    const duration = Math.floor((Date.now() - sessionStartTime) / 1000);
                    payload.sessionDuration = duration;
                    console.log(`⏱️ 세션 시간: ${duration}초 (${eventType})`);
                }
                
                await fetch('/api/track', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                console.log(`📊 이벤트 전송: ${eventType} (userId: ${userId.substr(0, 15)}...)`);
            } catch (error) {
                console.error('📊 이벤트 전송 실패:', error);
            }
        }

        // 📱 브라우저 & 디바이스 감지
        function getDeviceInfo() {
            const ua = navigator.userAgent;
            
            // 디바이스 타입 감지
            let deviceType = 'Desktop';
            if (/mobile/i.test(ua)) deviceType = 'Mobile';
            else if (/tablet|ipad/i.test(ua)) deviceType = 'Tablet';
            
            // 브라우저 감지
            let browser = 'Other';
            if (/edg/i.test(ua)) browser = 'Edge';
            else if (/chrome/i.test(ua) && !/edg/i.test(ua)) browser = 'Chrome';
            else if (/safari/i.test(ua) && !/chrome/i.test(ua)) browser = 'Safari';
            else if (/firefox/i.test(ua)) browser = 'Firefox';
            else if (/msie|trident/i.test(ua)) browser = 'IE';
            
            // OS 감지
            let os = 'Other';
            if (/windows/i.test(ua)) os = 'Windows';
            else if (/macintosh|mac os x/i.test(ua)) os = 'macOS';
            else if (/linux/i.test(ua)) os = 'Linux';
            else if (/android/i.test(ua)) os = 'Android';
            else if (/iphone|ipad|ipod/i.test(ua)) os = 'iOS';
            
            return { deviceType, browser, os };
        }

        // 📊 페이지 로드 시 초기화 및 방문자 추적
        window.addEventListener('load', () => {
            // 페이지 초기화 (새로고침 시 결과 숨기기)
            initializePage();
            
            // 방문자 추적 (브라우저/디바이스 정보 포함)
            const deviceInfo = getDeviceInfo();
            trackEvent('page_view', deviceInfo);
        });
