<script>
    async function analyzeText() {
        const text = document.getElementById('textInput').value.trim();
        const title = document.getElementById('titleInput').value.trim();
        const btn = document.getElementById('analyzeBtn');
        const resultsContainer = document.getElementById('resultsContainer');

        if (!text) {
            alert('본문을 입력해주세요!');
            return;
        }

        btn.disabled = true;
        btn.textContent = '🔄 분석 중...';
        resultsContainer.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <div class="loading-text">AI가 텍스트를 분석하고 있습니다...</div>
            </div>
        `;

        try {
            const response = await fetch('/api/analyze-text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text, title })
            });

            const data = await response.json();

            if (data.success) {
                displayResults(data.analysis);
            } else {
                throw new Error(data.error || '분석 실패');
            }
        } catch (error) {
            console.error('분석 오류:', error);
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">❌</div>
                    <div style="font-size: 1.2rem;">분석 중 오류가 발생했습니다</div>
                    <div style="font-size: 0.95rem; opacity: 0.7;">${error.message}</div>
                </div>
            `;
        } finally {
            btn.disabled = false;
            btn.textContent = '🔍 분석 시작';
        }
    }

    function displayResults(analysis) {
        const resultsContainer = document.getElementById('resultsContainer');
        
        let html = '<div class="results-section">';

        // 1️⃣ 가독성 점수
        html += `
            <div class="score-display">
                <div class="score-number">${analysis.readability.score}<span style="font-size: 2rem;">/100</span></div>
                <div class="score-label">가독성 점수</div>
            </div>
        `;

        // 2️⃣ 글자수 분석
        const charCount = analysis.character_count;
        html += `
            <div class="result-card">
                <h3>📝 글자수 분석</h3>
                <div class="result-item">
                    <span class="result-label">전체 글자수</span>
                    <span class="result-value">${charCount.total.toLocaleString()}자</span>
                </div>
                <div class="result-item">
                    <span class="result-label">공백 제외</span>
                    <span class="result-value">${charCount.without_space.toLocaleString()}자</span>
                </div>
                ${charCount.title > 0 ? `
                <div class="result-item">
                    <span class="result-label">제목</span>
                    <span class="result-value">${charCount.title}자</span>
                </div>
                ` : ''}
                <div class="result-item">
                    <span class="result-label">읽는 시간</span>
                    <span class="result-value">⏱️ ${charCount.reading_time}</span>
                </div>
                <div class="result-item">
                    <span class="result-label">권장 범위</span>
                    <span class="result-value">
                        ${charCount.recommended_range}
                        <span class="status-badge status-${charCount.status}">
                            ${charCount.status === 'good' ? '✅' : charCount.status === 'warning' ? '⚠️' : 'ℹ️'}
                        </span>
                    </span>
                </div>
                ${charCount.message ? `
                <div class="message-box ${charCount.status}">
                    <span>${charCount.status === 'good' ? '✅' : charCount.status === 'warning' ? '⚠️' : 'ℹ️'}</span>
                    <span>${charCount.message}</span>
                </div>
                ` : ''}
            </div>
        `;

        // 3️⃣ 키워드 밀도
        const keywords = analysis.keyword_density.keywords;
        if (keywords && keywords.length > 0) {
            html += `
                <div class="result-card">
                    <h3>🔍 키워드 밀도 분석</h3>
                    <div class="keyword-list">
            `;
            
            keywords.forEach(kw => {
                html += `
                    <div class="keyword-item">
                        <div class="keyword-info">
                            <span class="keyword-word">${kw.word}</span>
                            <div class="keyword-stats">
                                <span class="keyword-stat">${kw.count}회</span>
                                <span class="keyword-stat">${kw.density}%</span>
                                <span class="status-badge status-${kw.status}">
                                    ${kw.status === 'good' ? '✅' : kw.status === 'warning' ? '⚠️' : 'ℹ️'}
                                </span>
                            </div>
                        </div>
                    </div>
                    ${kw.suggestion ? `
                    <div class="suggestion-box">
                        💡 ${kw.suggestion}
                    </div>
                    ` : ''}
                `;
            });

            html += `
                    </div>
                </div>
            `;
        }

        // 4️⃣ 중복 표현
        const duplicates = analysis.duplicate_expressions;
        if (duplicates && duplicates.length > 0) {
            html += `
                <div class="result-card">
                    <h3>🔄 중복 표현 감지</h3>
                    <div class="keyword-list">
            `;
            
            duplicates.forEach(dup => {
                html += `
                    <div class="keyword-item">
                        <div class="keyword-info">
                            <span class="keyword-word">${dup.expression}</span>
                            <div class="keyword-stats">
                                <span class="keyword-stat">${dup.count}회 반복</span>
                                <span class="status-badge status-${dup.status}">
                                    ${dup.status === 'warning' ? '⚠️' : 'ℹ️'}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div class="suggestion-box">
                        💡 ${dup.suggestion}
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        }

        // 5️⃣ 가독성 상세
        const readability = analysis.readability;
        html += `
            <div class="result-card">
                <h3>📖 가독성 상세 분석</h3>
                <div class="result-item">
                    <span class="result-label">평균 문장 길이</span>
                    <span class="result-value">
                        ${readability.sentence_length.avg}자
                        <span class="status-badge status-${readability.sentence_length.status}">
                            ${readability.sentence_length.status === 'good' ? '✅' : readability.sentence_length.status === 'warning' ? '⚠️' : 'ℹ️'}
                        </span>
                    </span>
                </div>
                ${readability.sentence_length.message ? `
                <div class="message-box ${readability.sentence_length.status}">
                    <span>${readability.sentence_length.status === 'good' ? '✅' : readability.sentence_length.status === 'warning' ? '⚠️' : 'ℹ️'}</span>
                    <span>${readability.sentence_length.message}</span>
                </div>
                ` : ''}

                <div class="result-item" style="margin-top: 10px;">
                    <span class="result-label">평균 단락 길이</span>
                    <span class="result-value">
                        ${readability.paragraph_length.avg}줄
                        <span class="status-badge status-${readability.paragraph_length.status}">
                            ${readability.paragraph_length.status === 'good' ? '✅' : '⚠️'}
                        </span>
                    </span>
                </div>
                ${readability.paragraph_length.message ? `
                <div class="message-box ${readability.paragraph_length.status}">
                    <span>${readability.paragraph_length.status === 'good' ? '✅' : '⚠️'}</span>
                    <span>${readability.paragraph_length.message}</span>
                </div>
                ` : ''}

                <div class="result-item" style="margin-top: 10px;">
                    <span class="result-label">줄바꿈</span>
                    <span class="result-value">
                        ${readability.line_breaks.count}회
                        <span class="status-badge status-${readability.line_breaks.status}">
                            ${readability.line_breaks.status === 'good' ? '✅' : '⚠️'}
                        </span>
                    </span>
                </div>
                ${readability.line_breaks.message ? `
                <div class="message-box ${readability.line_breaks.status}">
                    <span>${readability.line_breaks.status === 'good' ? '✅' : '⚠️'}</span>
                    <span>${readability.line_breaks.message}</span>
                </div>
                ` : ''}
            </div>
        `;

        html += '</div>';
        
        resultsContainer.innerHTML = html;
    }

    // Enter 키로 분석 (Ctrl+Enter 또는 Cmd+Enter)
    document.getElementById('textInput').addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            analyzeText();
        }
    });
</script>
