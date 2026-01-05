<script>
    let selectedStyle = 'friendly';

    // 스타일 선택
    document.querySelectorAll('.style-option').forEach(option => {
        option.addEventListener('click', () => {
            document.querySelectorAll('.style-option').forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');
            selectedStyle = option.dataset.style;
        });
    });

    async function generateTitles() {
        const text = document.getElementById('textInput').value.trim();
        const keywords = document.getElementById('keywordsInput').value.trim();
        const btn = document.getElementById('generateBtn');
        const container = document.getElementById('titlesContainer');

        if (!text && !keywords) {
            alert('본문 또는 키워드를 입력해주세요!');
            return;
        }

        btn.disabled = true;
        btn.textContent = '🤖 AI가 제목을 생성하는 중...';
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <div class="loading-text">최고의 제목을 찾고 있습니다...</div>
            </div>
        `;

        try {
            const response = await fetch('/api/generate-titles', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, keywords, style: selectedStyle })
            });

            const data = await response.json();

            if (data.success) {
                displayTitles(data.titles);
            } else {
                throw new Error(data.error || '제목 생성 실패');
            }
        } catch (error) {
            console.error('생성 오류:', error);
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">❌</div>
                    <div style="font-size: 1.2rem;">제목 생성 중 오류가 발생했습니다</div>
                    <div style="font-size: 0.95rem; opacity: 0.7;">${error.message}</div>
                </div>
            `;
        } finally {
            btn.disabled = false;
            btn.textContent = '✨ AI 제목 생성 (10개)';
        }
    }

    function displayTitles(titles) {
        const container = document.getElementById('titlesContainer');
        
        let html = '';
        titles.forEach((item, index) => {
            const scoreClass = item.evaluation.score >= 80 ? 'score-high' : 
                             item.evaluation.score >= 60 ? 'score-medium' : 'score-low';
            
            html += `
                <div class="title-card" style="animation-delay: ${index * 0.1}s">
                    <div class="title-rank">${index + 1}</div>
                    <div class="title-text">${item.title}</div>
                    <div class="title-meta">
                        <span class="ctr-badge">📈 예상 클릭율 ${item.ctr}%</span>
                        <span class="score-badge ${scoreClass}">⭐ 점수 ${item.evaluation.score}/100</span>
                    </div>
                    <div class="title-strength">💡 ${item.strength}</div>
                    <div class="title-feedback">
                        ${item.evaluation.feedback.map(fb => `<span class="feedback-tag">${fb}</span>`).join('')}
                    </div>
                    <button class="copy-btn" onclick="copyTitle('${item.title.replace(/'/g, "\\'")}')">
                        📋 제목 복사
                    </button>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    async function evaluateTitle() {
        const title = document.getElementById('evaluateInput').value.trim();
        const resultContainer = document.getElementById('evaluateResult');

        if (!title) {
            alert('제목을 입력해주세요!');
            return;
        }

        resultContainer.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <div class="loading-text">제목을 평가하는 중...</div>
            </div>
        `;

        try {
            const response = await fetch('/api/evaluate-title', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title })
            });

            const data = await response.json();

            if (data.success) {
                const eval = data.evaluation;
                const scoreClass = eval.score >= 80 ? 'score-high' : 
                                 eval.score >= 60 ? 'score-medium' : 'score-low';
                
                resultContainer.innerHTML = `
                    <div class="evaluate-result">
                        <div class="evaluate-score">${eval.score}<span style="font-size: 1.5rem;">/100</span></div>
                        <div class="title-feedback">
                            ${eval.feedback.map(fb => `<span class="feedback-tag">${fb}</span>`).join('')}
                        </div>
                    </div>
                `;
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            resultContainer.innerHTML = `
                <div style="color: rgba(255, 255, 255, 0.8); text-align: center; padding: 20px;">
                    ❌ 평가 중 오류가 발생했습니다: ${error.message}
                </div>
            `;
        }
    }

    function copyTitle(title) {
        navigator.clipboard.writeText(title).then(() => {
            alert('✅ 제목이 복사되었습니다!');
        });
    }

    // Enter로 평가
    document.getElementById('evaluateInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') evaluateTitle();
    });
</script>
