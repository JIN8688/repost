<script>
    async function recommendKeywords() {
        const topic = document.getElementById('topicInput').value.trim();
        const btn = document.getElementById('recommendBtn');
        const container = document.getElementById('resultsContainer');
        if (!topic) { alert('주제를 입력해주세요!'); return; }
        btn.disabled = true; btn.textContent = '🔍 분석 중...';
        container.innerHTML = '<div class="glass-card"><div class="loading"><div class="spinner"></div><div class="loading-text">최적의 키워드를 찾고 있습니다...</div></div></div>';
        try {
            // 🔑 마스터 계정 확인
            const isAdmin = localStorage.getItem('repost_admin') === 'true';
            
            const response = await fetch('/api/recommend-keywords', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic, isAdmin })
            });
            const data = await response.json();
            if (data.success) { displayResults(data.keywords); }
            else { throw new Error(data.error || '추천 실패'); }
        } catch (error) {
            console.error('추천 오류:', error);
            container.innerHTML = '<div class="glass-card"><div class="empty-state"><div class="empty-icon">❌</div><div style="font-size: 1.2rem;">키워드 추천 중 오류가 발생했습니다</div></div></div>';
        } finally { btn.disabled = false; btn.textContent = '✨ 키워드 추천받기'; }
    }
    function displayResults(keywords) {
        const container = document.getElementById('resultsContainer');
        container.innerHTML = `
            <div class="glass-card">
                <div class="keyword-section">
                    <div class="section-header">🎯 주요 키워드 (검색량 높음)</div>
                    <div class="keyword-list">
                        ${keywords.primary.map(kw => createKeywordCard(kw)).join('')}
                    </div>
                </div>
            </div>
            <div class="glass-card">
                <div class="keyword-section">
                    <div class="section-header">🔗 연관 키워드</div>
                    <div class="keyword-list">
                        ${keywords.secondary.map(kw => createKeywordCard(kw)).join('')}
                    </div>
                </div>
            </div>
            <div class="glass-card">
                <div class="keyword-section">
                    <div class="section-header">💎 롱테일 키워드 (추천!)</div>
                    <div class="keyword-list">
                        ${keywords.long_tail.map(kw => createKeywordCard(kw)).join('')}
                    </div>
                </div>
            </div>
            <div class="glass-card">
                <h2 class="card-title"><span>🎨</span> 추천 키워드 조합</h2>
                <div class="combination-list">
                    ${keywords.recommended_combination.map(combo => `
                        <div class="combination-item">
                            <div class="combination-title">${combo.title}</div>
                            <div class="combination-keywords">
                                ${combo.keywords.map(kw => `<span class="combination-keyword-tag">${kw}</span>`).join('')}
                            </div>
                            <div class="combination-strategy">💡 ${combo.strategy}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    function createKeywordCard(kw) {
        const volumeClass = kw.volume === 'high' ? 'volume-high' : kw.volume === 'medium' ? 'volume-medium' : 'volume-low';
        const difficultyClass = kw.difficulty === 'hard' ? 'difficulty-hard' : kw.difficulty === 'medium' ? 'difficulty-medium' : 'difficulty-easy';
        const volumeText = kw.volume === 'high' ? '높음' : kw.volume === 'medium' ? '중간' : '낮음';
        const difficultyText = kw.difficulty === 'hard' ? '어려움' : kw.difficulty === 'medium' ? '보통' : '쉬움';
        return `
            <div class="keyword-item" onclick="copyKeyword('${kw.keyword}')">
                <div class="keyword-text">${kw.keyword}</div>
                <div class="keyword-meta">
                    <div class="meta-item">
                        <span>📊</span>
                        <span class="volume-badge ${volumeClass}">검색량 ${volumeText}</span>
                    </div>
                    <div class="meta-item">
                        <span>🎯</span>
                        <span class="difficulty-badge ${difficultyClass}">난이도 ${difficultyText}</span>
                    </div>
                </div>
                <div class="meta-item" style="margin-bottom: 8px;">
                    <span>🔢</span>
                    <span>월 ${kw.volume_estimate.toLocaleString()}회 검색 (추정)</span>
                </div>
                <div class="keyword-recommendation">💡 ${kw.recommendation}</div>
            </div>
        `;
    }
    function copyKeyword(keyword) {
        navigator.clipboard.writeText(keyword).then(() => {
            alert(`✅ "${keyword}" 키워드가 복사되었습니다!`);
        });
    }
    document.getElementById('topicInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') recommendKeywords();
    });
</script>
