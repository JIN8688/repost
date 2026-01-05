# 🏗️ Repost - 프로젝트 아키텍처 문서

> 프로덕션급 코드 구조 및 유지보수 가이드

## 📁 프로젝트 구조

```
Repost/
├── app.py                      # Flask 메인 애플리케이션
├── requirements.txt            # Python 의존성
├── vercel.json                # Vercel 배포 설정
│
├── templates/                  # Jinja2 템플릿
│   ├── base.html              # ✨ 기본 템플릿 (모든 페이지가 상속)
│   ├── index.html             # 메인 페이지
│   ├── login.html             # 로그인 페이지
│   ├── signup.html            # 회원가입 페이지
│   ├── pricing.html           # 가격 페이지
│   ├── tools.html             # 도구 허브 페이지
│   ├── text-analyzer.html     # 텍스트 분석기
│   ├── title-generator.html   # 제목 생성기
│   ├── seo-checker.html       # SEO 체커
│   ├── ai-writer.html         # AI 글쓰기
│   ├── competitor-analyzer.html  # 경쟁 분석
│   └── keyword-recommender.html  # 키워드 추천
│
├── static/                     # 정적 파일
│   ├── css/
│   │   ├── common.css         # ✨ 공통 스타일 (전역 변수, 유틸리티)
│   │   ├── header.css         # ✨ 헤더 전용 스타일
│   │   ├── footer.css         # ✨ 풋터 전용 스타일
│   │   ├── main.css           # ✨ 메인 페이지 전용 스타일
│   │   └── bonus-system.css   # 보너스 시스템 스타일
│   │
│   ├── js/
│   │   ├── common.js          # ✨ 공통 JavaScript (헤더, 유틸리티)
│   │   └── bonus-system.js    # 보너스 시스템 로직
│   │
│   └── images/                # 이미지 파일
│       ├── favicon.svg
│       └── logo-og.png
│
└── docs/                       # 문서
    ├── ARCHITECTURE.md        # ✨ 이 파일
    ├── CODING_STANDARDS.md    # 코딩 컨벤션
    └── API_DOCUMENTATION.md   # API 문서
```

## 🎨 CSS 아키텍처

### 계층 구조
```
common.css (기본 레이어)
    ↓
header.css, footer.css (컴포넌트 레이어)
    ↓
main.css, tools.css (페이지 레이어)
    ↓
페이지별 inline CSS (커스터마이징 레이어)
```

### CSS 파일 역할

#### 1. `common.css` - 공통 스타일 시스템
- **CSS 변수 (Design Tokens)**: 색상, 간격, 폰트, 그림자 등
- **리셋 스타일**: 브라우저 기본 스타일 초기화
- **타이포그래피**: h1-h6, p, a 등 기본 텍스트 스타일
- **유틸리티 클래스**: 
  - 레이아웃: `.flex`, `.grid`, `.container`
  - 간격: `.m-*`, `.p-*`, `.gap-*`
  - 텍스트: `.text-center`, `.font-bold`
  - 버튼: `.btn`, `.btn-primary`, `.btn-outline`
  - 카드: `.card`, `.card-glass`
- **글래스모피즘**: `.glass`, `.glass-white`
- **애니메이션**: `@keyframes` 정의
- **반응형 breakpoints**: 1024px, 768px

**언제 수정하나?**
- 전역 디자인 토큰 변경 (브랜드 컬러, 폰트 등)
- 새로운 유틸리티 클래스 추가
- 애니메이션 효과 추가

#### 2. `header.css` - 헤더 컴포넌트
- **고정 헤더**: `.site-header`
- **네비게이션**: `.header-nav`, `.header-menu`
- **로고**: `.header-logo`
- **햄버거 메뉴**: `.header-hamburger` (모바일)
- **모바일 메뉴**: `.header-mobile-menu`

**언제 수정하나?**
- 헤더 디자인 변경
- 네비게이션 메뉴 스타일 수정
- 모바일 메뉴 애니메이션 변경

#### 3. `footer.css` - 풋터 컴포넌트
- **4컬럼 레이아웃**: `.footer-grid`
- **소셜 링크**: `.footer-social`
- **하단 정보**: `.footer-bottom`

**언제 수정하나?**
- 풋터 레이아웃 변경
- 소셜 링크 스타일 수정

#### 4. `main.css` - 메인 페이지
- **배경**: `.main-page`
- **도구 그리드**: `.tools-grid`, `.tool-card`
- **입력 섹션**: `.input-section`
- **댓글 섹션**: `.comments-section`

**언제 수정하나?**
- 메인 페이지 레이아웃 변경
- 도구 카드 디자인 수정

## 🚀 JavaScript 아키텍처

### 파일 역할

#### 1. `common.js` - 공통 기능
```javascript
// 헤더 동작
initHeader() 
    - 스크롤 시 헤더 스타일 변경
    - 햄버거 메뉴 토글
    - 현재 페이지 하이라이트

// 유틸리티 함수
showToast(message, type)     // 토스트 알림
copyToClipboard(text)         // 클립보드 복사
debounce(func, wait)          // 디바운스
throttle(func, limit)         // 쓰로틀
storage.set/get/remove(key)   // 로컬스토리지
formatDate(date, format)      // 날짜 포맷

// 기타
initSmoothScroll()            // 스무스 스크롤
initLazyLoad()                // 이미지 지연 로딩
initAccessibility()           // 접근성 개선
```

#### 2. `bonus-system.js` - 보너스 시스템
- 사용 횟수 추적
- 보너스 지급/회수
- 모달 관리

## 📐 템플릿 상속 구조

```
base.html (베이스 템플릿)
    ├── 공통 CSS 로드
    ├── 공통 JS 로드
    ├── 헤더 컴포넌트
    ├── {% block content %} ← 페이지별 컨텐츠
    └── 풋터 컴포넌트

모든 페이지는 base.html을 상속:
{% extends "base.html" %}
{% block content %}
    <!-- 페이지별 컨텐츠 -->
{% endblock %}
```

### 블록 구조

```jinja2
{% block title %}페이지 제목{% endblock %}
{% block extra_css %}
    <!-- 페이지별 추가 CSS -->
{% endblock %}

{% block content %}
    <!-- 메인 컨텐츠 -->
{% endblock %}

{% block extra_js %}
    <!-- 페이지별 추가 JS -->
{% endblock %}
```

## 🎯 CSS 변수 사용법

```css
/* common.css에 정의된 변수 사용 */
.my-element {
    color: var(--color-primary);
    padding: var(--spacing-lg);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-lg);
    transition: all var(--transition-base);
}

/* 그라데이션 사용 */
.my-button {
    background: var(--gradient-primary);
}
```

## 📱 반응형 Breakpoints

```css
/* 데스크톱 우선 (Desktop First) */

/* 태블릿 (1024px 이하) */
@media (max-width: 1024px) {
    /* 태블릿 스타일 */
}

/* 모바일 (768px 이하) */
@media (max-width: 768px) {
    /* 모바일 스타일 */
}

/* 작은 모바일 (480px 이하) */
@media (max-width: 480px) {
    /* 작은 모바일 스타일 */
}
```

## 🔧 유틸리티 클래스 사용 예제

```html
<!-- 레이아웃 -->
<div class="container">
    <div class="flex items-center justify-between gap-lg">
        <div class="card shadow-lg rounded-xl p-lg">
            <!-- 컨텐츠 -->
        </div>
    </div>
</div>

<!-- 버튼 -->
<button class="btn btn-primary btn-lg">클릭</button>

<!-- 그리드 -->
<div class="grid grid-cols-3 gap-md">
    <div class="card">카드 1</div>
    <div class="card">카드 2</div>
    <div class="card">카드 3</div>
</div>

<!-- 애니메이션 -->
<div class="animate-fadeInUp">
    <!-- 페이드인 애니메이션 -->
</div>
```

## 🛠️ 개발 워크플로우

### 새로운 페이지 추가 시

1. **템플릿 생성** (`templates/new-page.html`)
```html
{% extends "base.html" %}
{% block title %}페이지 제목{% endblock %}

{% block extra_css %}
<style>
    /* 페이지 전용 스타일 */
</style>
{% endblock %}

{% block content %}
    <!-- 컨텐츠 -->
{% endblock %}
```

2. **라우트 추가** (`app.py`)
```python
@app.route('/new-page')
def new_page():
    return render_template('new-page.html')
```

3. **네비게이션에 추가** (`base.html`)
```html
<a href="/new-page" class="header-menu-link">새 페이지</a>
```

### 새로운 컴포넌트 추가 시

1. **CSS 클래스 정의** (`common.css` 또는 별도 파일)
```css
.my-component {
    /* 스타일 정의 */
}
```

2. **JavaScript 기능** (`common.js` 또는 별도 파일)
```javascript
function initMyComponent() {
    // 컴포넌트 초기화
}
```

3. **템플릿에서 사용**
```html
<div class="my-component">
    <!-- 컴포넌트 컨텐츠 -->
</div>
```

## ✅ 코딩 컨벤션

### CSS
- **BEM 네이밍**: `.block__element--modifier`
- **kebab-case**: `.my-class-name`
- **유틸리티 우선**: 가능하면 유틸리티 클래스 사용
- **컴포넌트 단위**: 재사용 가능한 컴포넌트로 분리

### JavaScript
- **camelCase**: `myFunction()`
- **const/let**: var 사용 금지
- **화살표 함수**: 가독성이 좋은 경우 사용
- **주석**: JSDoc 스타일 권장

### HTML
- **시맨틱 태그**: `<header>`, `<nav>`, `<main>`, `<footer>` 등
- **접근성**: `aria-label`, `alt` 속성 필수
- **들여쓰기**: 4칸 (스페이스)

## 🚀 성능 최적화

### CSS
- ✅ Critical CSS는 인라인으로
- ✅ 불필요한 셀렉터 제거
- ✅ 애니메이션은 `transform`과 `opacity`만 사용

### JavaScript
- ✅ 이벤트 리스너는 debounce/throttle 사용
- ✅ DOM 조작 최소화
- ✅ Lazy loading 적용

### 이미지
- ✅ WebP 포맷 사용
- ✅ 적절한 사이즈로 리사이즈
- ✅ Lazy loading 적용

## 🔐 보안

- ✅ CSRF 토큰 사용
- ✅ XSS 방지 (템플릿 자동 이스케이프)
- ✅ 환경 변수로 시크릿 관리
- ✅ HTTPS 강제

## 📊 모니터링

- GA4 통합
- 에러 로깅
- 성능 메트릭

## 🆘 문제 해결

### 스타일이 적용되지 않을 때
1. 브라우저 캐시 클리어 (Ctrl+Shift+R)
2. CSS 파일 경로 확인
3. 브라우저 개발자 도구에서 로드 여부 확인

### JavaScript 에러 발생 시
1. 콘솔에서 에러 메시지 확인
2. 파일 로드 순서 확인 (common.js가 먼저)
3. 함수/변수 스코프 확인

## 📚 참고 자료

- [Flask 공식 문서](https://flask.palletsprojects.com/)
- [Jinja2 템플릿 문서](https://jinja.palletsprojects.com/)
- [CSS 변수 가이드](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [JavaScript 모범 사례](https://github.com/ryanmcdermott/clean-code-javascript)

---

**마지막 업데이트**: 2026-01-05  
**버전**: 1.0.0  
**작성자**: Repost Team

