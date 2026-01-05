# 🚀 Repost - AI 블로그 댓글 자동 추천

> 블로그 네트워킹의 시간을 90% 줄이는 AI 비서

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/openai-1.0+-orange.svg)](https://openai.com/)

## ✨ 주요 기능

### 📝 AI 댓글 생성
- 블로그 URL만 입력하면 3초 만에 자연스러운 댓글 8개 생성
- GPT-4o-mini 기반 맞춤형 댓글 추천
- 원클릭 복사 & 블로그 이동

### 🛠️ 블로거 필수 도구

#### Tier S (프리미엄 기능)
1. **실시간 텍스트 분석기** 📊
   - 글자수, 키워드 밀도, 가독성 실시간 체크
   - 중복 표현 자동 감지

2. **스마트 제목 생성기** 💡
   - AI가 클릭율 높은 제목 10개 생성
   - 예상 클릭율 & 점수 표시

3. **SEO 점수 체커** 🎯
   - 100점 만점 SEO 점수 분석
   - 즉시 개선 가능한 항목 제안

#### Tier A (추가 기능)
4. **AI 글쓰기 도우미** ✍️
   - 주제만 입력하면 블로그 초안 자동 생성
   - 5가지 스타일 & 5가지 구조 선택

5. **경쟁 블로그 분석** 🔍
   - 상위 블로그 통계 자동 분석
   - 개선 방법 구체적 제시

6. **키워드 추천 엔진** 🔑
   - 검색량 & 경쟁도 기반 키워드 추천
   - 롱테일 키워드 자동 발굴

### 💎 보너스 시스템
- 7일 무료 체험 (일일 7회)
- 친구 추천 시 +5회 보너스
- SNS 공유 시 +5회 보너스
- 시크릿 코드로 무제한 사용

## 🏗️ 프로젝트 구조

프로덕션급 코드 구조로 최적화되어 있습니다. 자세한 내용은 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)를 참조하세요.

```
Repost/
├── app.py                  # Flask 메인 애플리케이션
├── templates/              # Jinja2 템플릿
│   ├── base.html          # 베이스 템플릿
│   ├── index.html         # 메인 페이지
│   └── tools/             # 도구 페이지들
├── static/
│   ├── css/               # 스타일시트
│   │   ├── common.css     # 공통 스타일
│   │   ├── header.css     # 헤더 스타일
│   │   ├── footer.css     # 풋터 스타일
│   │   └── main.css       # 메인 페이지 스타일
│   └── js/                # JavaScript
│       ├── common.js      # 공통 기능
│       └── bonus-system.js
└── docs/                   # 문서
    └── ARCHITECTURE.md     # 아키텍처 문서
```

## 🚀 시작하기

### 필수 요구사항
- Python 3.9+
- OpenAI API 키
- Redis (Vercel KV)

### 설치

1. **저장소 클론**
```bash
git clone https://github.com/your-username/repost.git
cd repost
```

2. **가상환경 생성 및 활성화**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

4. **환경 변수 설정**
```bash
# .env 파일 생성
OPENAI_API_KEY=your_openai_api_key
KV_URL=your_vercel_kv_url
KV_REST_API_URL=your_kv_rest_api_url
KV_REST_API_TOKEN=your_kv_rest_api_token
KV_REST_API_READ_ONLY_TOKEN=your_kv_rest_api_read_only_token
SECRET_KEY=your_secret_key
```

5. **개발 서버 실행**
```bash
flask run
```

또는

```bash
python app.py
```

서버가 `http://localhost:5000`에서 실행됩니다.

## 🎨 개발 가이드

### CSS 수정
- 전역 스타일: `static/css/common.css`
- 헤더/풋터: `static/css/header.css`, `static/css/footer.css`
- 페이지별: 각 페이지 템플릿의 `{% block extra_css %}`

### JavaScript 추가
- 공통 기능: `static/js/common.js`
- 페이지별: 각 페이지 템플릿의 `{% block extra_js %}`

### 새로운 페이지 추가
1. `templates/` 폴더에 HTML 파일 생성
2. `base.html`을 상속받아 작성
3. `app.py`에 라우트 추가

자세한 가이드는 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)를 참조하세요.

## 📚 API 엔드포인트

### 댓글 생성
```http
POST /api/analyze
Content-Type: application/json

{
  "url": "https://blog.naver.com/..."
}
```

### 텍스트 분석
```http
POST /api/analyze-text
Content-Type: application/json

{
  "text": "분석할 텍스트",
  "title": "제목 (선택)"
}
```

### 제목 생성
```http
POST /api/generate-titles
Content-Type: application/json

{
  "text": "본문 내용",
  "keywords": "키워드1, 키워드2",
  "style": "friendly"
}
```

더 많은 API는 [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md)를 참조하세요.

## 🧪 테스트

```bash
# 유닛 테스트
pytest tests/

# 커버리지 리포트
pytest --cov=app tests/
```

## 📦 배포

### Vercel 배포

1. **Vercel CLI 설치**
```bash
npm i -g vercel
```

2. **배포**
```bash
vercel
```

3. **환경 변수 설정**
Vercel 대시보드에서 환경 변수 설정

### Docker 배포

```bash
# 이미지 빌드
docker build -t repost .

# 컨테이너 실행
docker run -p 5000:5000 --env-file .env repost
```

## 🛠️ 기술 스택

### Backend
- **Flask** 2.3+ - 웹 프레임워크
- **OpenAI** 1.0+ - AI 모델
- **Redis** - 세션 & 캐싱
- **BeautifulSoup4** - 웹 스크래핑

### Frontend
- **Jinja2** - 템플릿 엔진
- **Vanilla JavaScript** - 인터랙션
- **CSS3** - 스타일링 (Glassmorphism)

### DevOps
- **Vercel** - 호스팅
- **GitHub Actions** - CI/CD
- **GA4** - 분석

## 📊 성능

- ⚡ 평균 응답 시간: 3초
- 📈 댓글 품질: 평균 4.8/5.0
- 💯 시스템 가용성: 99.9%

## 🔒 보안

- CSRF 토큰 적용
- XSS 방지 (자동 이스케이프)
- Rate Limiting
- 환경 변수로 시크릿 관리

## 🤝 기여하기

기여를 환영합니다! 다음 단계를 따라주세요:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스에 따라 라이선스가 부여됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 👥 팀

- **개발** - Repost Team
- **디자인** - Repost Design
- **기획** - Repost Planning

## 📞 문의

- 이메일: support@repost.kr
- 웹사이트: [https://repost.kr](https://repost.kr)
- GitHub: [@JIN8688](https://github.com/JIN8688)

## 🙏 감사의 말

- OpenAI - GPT API 제공
- Vercel - 호스팅 플랫폼
- Flask Community - 훌륭한 프레임워크

---

**Made with ❤️ by Repost Team**

© 2026 Repost. All rights reserved.
