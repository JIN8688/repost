<script>
    let keywords = [];
    let selectedTone = 'friendly';
    let selectedStructure = 'intro-body-conclusion';

    // 옵션 버튼 이벤트
    document.querySelectorAll('#toneOptions .option-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#toneOptions .option-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedTone = btn.dataset.value;
        });
    });

    document.querySelectorAll('#structureOptions .option-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#structureOptions .option-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedStructure = btn.dataset.value;
        });
    });

    function handleKeywordEnter(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const input = e.target;
            const keyword = input.value.trim();
            if (keyword && !keywords.includes(keyword)) {
                keywords.push(keyword);
                addKeywordTag(keyword);
                input.value = '';
            }
        }
    }

    function addKeywordTag(keyword) {
        const container = document.getElementById('tagsContainer');
        const input = document.getElementById('keywordInput');
        
        const tag = document.createElement('div');
        tag.className = 'tag';
        tag.innerHTML = `
            <span>${keyword}</span>
            <span class="tag-remove" onclick="removeKeyword('${keyword}')">×</span>
        `;
        
        container.insertBefore(tag, input);
    }

    function removeKeyword(keyword) {
        keywords = keywords.filter(k => k !== keyword);
        updateTagsDisplay();
    }

    function updateTagsDisplay() {
        const container = document.getElementById('tagsContainer');
        const input = document.getElementById('keywordInput');
        container.innerHTML = '';
        keywords.forEach(kw => addKeywordTag(kw));
        container.appendChild(input);
    }

    function updateWordCount(value) {
        document.getElementById('wordCountValue').textContent = value + '자';
    }

    async function generateContent() {
        const topic = document.getElementById('topicInput').value.trim();
        const wordCount = parseInt(document.getElementById('wordCountSlider').value);
        const btn = document.getElementById('generateBtn');
        const container = document.getElementById('resultContainer');

        if (!topic) {
            alert('주제를 입력해주세요!');
            return;
        }

        btn.disabled = true;
        btn.textContent = '🤖 AI가 글을 작성하는 중...';
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <div class="loading-text">AI가 창의적인 글을 작성하고 있습니다...<br>약 10-15초 소요됩니다</div>
            </div>
        `;

        try {
            // 🔑 마스터 계정 확인
            const isAdmin = localStorage.getItem('repost_admin') === 'true';
            
            const response = await fetch('/api/generate-content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic,
                    keywords,
                    tone: selectedTone,
                    structure: selectedStructure,
                    word_count: wordCount,
                    isAdmin
                })
            });

            const data = await response.json();

            if (data.success) {
                displayContent(data.content, data.metadata);
            } else {
                throw new Error(data.error || 'AI 글 생성 실패');
            }
        } catch (error) {
            console.error('생성 오류:', error);
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">❌</div>
                    <div style="font-size: 1.2rem;">글 생성 중 오류가 발생했습니다</div>
                    <div style="font-size: 0.95rem; opacity: 0.7;">${error.message}</div>
                </div>
            `;
        } finally {
            btn.disabled = false;
            btn.textContent = '✨ AI로 글 작성하기';
        }
    }

    function displayContent(content, metadata) {
        const container = document.getElementById('resultContainer');
        
        container.innerHTML = `
            <div class="metadata-box">
                <div class="metadata-item">
                    <div class="metadata-label">글자수</div>
                    <div class="metadata-value">${metadata.char_count.toLocaleString()}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">단어수</div>
                    <div class="metadata-value">${metadata.word_count}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">읽는 시간</div>
                    <div class="metadata-value">${metadata.estimated_reading_time}</div>
                </div>
            </div>

            <div class="result-content scrollbar-custom">${content}</div>

            <div class="result-actions">
                <button class="action-btn" onclick="copyContent()">
                    📋 복사하기
                </button>
                <button class="action-btn" onclick="downloadContent()">
                    💾 저장하기
                </button>
                <button class="action-btn" onclick="regenerateContent()">
                    🔄 다시 생성
                </button>
            </div>
        `;
    }

    function copyContent() {
        const content = document.querySelector('.result-content').textContent;
        navigator.clipboard.writeText(content).then(() => {
            alert('✅ 글이 클립보드에 복사되었습니다!');
        });
    }

    function downloadContent() {
        const content = document.querySelector('.result-content').textContent;
        const topic = document.getElementById('topicInput').value || '블로그글';
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${topic}_AI글쓰기.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    function regenerateContent() {
        if (confirm('새로운 내용으로 다시 생성할까요?')) {
            generateContent();
        }
    }
</script>
