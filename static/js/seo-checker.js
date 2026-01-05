<script>
    async function checkSEO() {
        const title = document.getElementById('titleInput').value.trim();
        const text = document.getElementById('textInput').value.trim();
        const keywords = document.getElementById('keywordsInput').value.trim();
        const imageCount = parseInt(document.getElementById('imageCountInput').value) || 0;
        const btn = document.getElementById('checkBtn');
        const container = document.getElementById('resultsContainer');

        if (!title || !text) {
            alert('제목과 본문을 입력해주세요!');
            return;
        }

        btn.disabled = true;
        btn.textContent = '🔍 분석 중...';
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <div class="loading-text">SEO를 분석하고 있습니다...</div>
            </div>
        `;

        try {
            // 🔑 마스터 계정 확인
            const isAdmin = localStorage.getItem('repost_admin') === 'true';
            
            const response = await fetch('/api/check-seo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, text, keywords, image_count: imageCount, isAdmin })
            });

            const data = await response.json();

            if (data.success) {
                displaySEOResults(data.seo);
            } else {
                throw new Error(data.error || 'SEO 분석 실패');
            }
        } catch (error) {
            console.error('분석 오류:', error);
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">❌</div>
                    <div style="font-size: 1.2rem;">분석 중 오류가 발생했습니다</div>
                    <div style="font-size: 0.95rem; opacity: 0.7;">${error.message}</div>
                </div>
            `;
        } finally {
            btn.disabled = false;
            btn.textContent = '🚀 SEO 점수 확인';
        }
    }

    function displaySEOResults(seo) {
        const container = document.getElementById('resultsContainer');
        const score = seo.overall_score;
        const circumference = 2 * Math.PI * 90;
        const offset = circumference - (score / 100) * circumference;

        let html = `
            <div style="text-align: center; margin-bottom: 30px;">
                <div class="score-circle">
                    <svg class="score-svg" width="200" height="200">
                        <defs>
                            <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                                <stop offset="0%" style="stop-color:#10b981;stop-opacity:1" />
                                <stop offset="100%" style="stop-color:#3b82f6;stop-opacity:1" />
                            </linearGradient>
                        </defs>
                        <circle class="score-bg" cx="100" cy="100" r="90"></circle>
                        <circle class="score-progress" cx="100" cy="100" r="90"
                                stroke-dasharray="${circumference}"
                                stroke-dashoffset="${offset}"></circle>
                    </svg>
                    <div class="score-text">
                        <div class="score-number">${score}</div>
                        <div class="score-label">/ 100</div>
                    </div>
                </div>
                <div class="grade-badge grade-${seo.grade}">${seo.grade} 등급</div>
                <div style="color: white; font-size: 1.1rem;">${seo.grade_message}</div>
            </div>

            <div class="category-grid">
                <div class="category-card">
                    <div class="category-icon">📝</div>
                    <div class="category-name">제목 최적화</div>
                    <div class="category-score">${seo.title_optimization.score}</div>
                </div>
                <div class="category-card">
                    <div class="category-icon">📄</div>
                    <div class="category-name">본문 최적화</div>
                    <div class="category-score">${seo.content_optimization.score}</div>
                </div>
                <div class="category-card">
                    <div class="category-icon">🖼️</div>
                    <div class="category-name">이미지 최적화</div>
                    <div class="category-score">${seo.image_optimization.score}</div>
                </div>
                <div class="category-card">
                    <div class="category-icon">📖</div>
                    <div class="category-name">가독성</div>
                    <div class="category-score">${seo.readability.score}</div>
                </div>
            </div>

            ${seo.quick_wins.length > 0 ? `
            <div class="quick-wins">
                <h3>⚡ 즉시 개선 가능 (${seo.quick_wins.length}개)</h3>
                ${seo.quick_wins.map(win => `
                    <div class="win-item">
                        <div class="win-action">${win.action}</div>
                        <div class="win-meta">
                            <span class="win-impact ${win.impact === '높음' ? 'high' : 'medium'}">
                                💥 영향도: ${win.impact}
                            </span>
                            <span class="win-time">⏱️ 소요: ${win.time}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
            ` : ''}

            <div class="details-section">
                ${generateDetailCard('📝 제목 분석', seo.title_optimization)}
                ${generateDetailCard('📄 본문 분석', seo.content_optimization)}
                ${generateDetailCard('🖼️ 이미지 분석', seo.image_optimization)}
            </div>
        `;

        container.innerHTML = html;
    }

    function generateDetailCard(title, data) {
        return `
            <div class="detail-card">
                <h3>${title} - ${data.score}점</h3>
                
                ${data.issues && data.issues.length > 0 ? `
                <div style="margin-bottom: 15px;">
                    <div style="color: rgba(255, 255, 255, 0.8); font-weight: 500; margin-bottom: 8px;">
                        ⚠️ 문제점
                    </div>
                    <ul class="issue-list">
                        ${data.issues.map(issue => `<li><span>•</span><span>${issue}</span></li>`).join('')}
                    </ul>
                </div>
                ` : ''}

                ${data.suggestions && data.suggestions.length > 0 ? `
                <div>
                    <div style="color: rgba(255, 255, 255, 0.8); font-weight: 500; margin-bottom: 8px;">
                        💡 개선 제안
                    </div>
                    <ul class="suggestion-list">
                        ${data.suggestions.map(suggestion => `<li><span>•</span><span>${suggestion}</span></li>`).join('')}
                    </ul>
                </div>
                ` : ''}
            </div>
        `;
    }
</script>
