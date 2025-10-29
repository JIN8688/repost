# Vercel 배포 완벽 가이드

## 📋 문서 정보
- **작성일**: 2025년 10월 29일
- **목적**: Repost 서비스를 Vercel에 프로덕션 배포
- **난이도**: ⭐⭐ 중급
- **소요 시간**: 30분

---

## ✅ 사전 준비 체크리스트

### 필수 사항
- [x] GitHub 계정
- [x] Vercel 계정 (https://vercel.com/signup)
- [x] OpenAI API 키
- [x] 도메인 (repost.kr)

### 확인 사항
- [x] `vercel.json` 생성 완료
- [x] `app.py` Flask 앱 준비 완료
- [x] `requirements.txt` 최신화
- [x] `.gitignore`에 `.env` 포함

---

## 🚀 배포 단계

### Step 1: Vercel 계정 생성 및 GitHub 연동

#### 1-1. Vercel 가입
```
1. https://vercel.com/signup 접속
2. "Continue with GitHub" 클릭
3. GitHub 계정으로 로그인
4. Vercel 권한 승인
```

#### 1-2. Import 프로젝트
```
1. Vercel 대시보드에서 "Add New..." → "Project" 클릭
2. "Import Git Repository" 선택
3. GitHub에서 "JIN8688/repost" 저장소 선택
4. "Import" 클릭
```

---

### Step 2: 프로젝트 설정

#### 2-1. 기본 설정
```
Project Name: repost (또는 원하는 이름)
Framework Preset: Other (Flask는 자동 감지됨)
Root Directory: ./
Build Command: (비워두기)
Output Directory: (비워두기)
Install Command: pip install -r requirements.txt
```

#### 2-2. 환경 변수 설정 (중요! ⚠️)
```
Environment Variables 섹션에서 추가:

이름: OPENAI_API_KEY
값: sk-proj-xxxxxxxxxxxxx (실제 OpenAI API 키)
환경: Production, Preview, Development (모두 체크)

[Add] 버튼 클릭
```

**⚠️ 주의사항:**
- API 키를 절대 코드에 하드코딩하지 마세요
- `.env` 파일은 GitHub에 업로드되지 않습니다 (`.gitignore`에 포함)
- Vercel 대시보드에서만 환경변수 설정

---

### Step 3: 배포 실행

#### 3-1. 첫 배포
```
1. "Deploy" 버튼 클릭
2. 빌드 로그 확인 (2-3분 소요)
3. 성공 메시지 확인: "Your project has been deployed"
```

#### 3-2. 배포 URL 확인
```
자동 생성된 URL: https://repost-xxxxx.vercel.app
→ 이 URL로 즉시 접속 가능!
```

#### 3-3. 테스트
```
1. https://repost-xxxxx.vercel.app 접속
2. 네이버 블로그 URL 입력
3. "분석하기" 버튼 클릭
4. 댓글 생성 확인
```

---

### Step 4: 커스텀 도메인 연결 (repost.kr)

#### 4-1. Vercel에서 도메인 추가
```
1. Vercel 프로젝트 페이지 → "Settings" 탭
2. "Domains" 메뉴 클릭
3. "repost.kr" 입력
4. "Add" 클릭
```

#### 4-2. DNS 설정 (Cafe24)
```
Vercel이 제공하는 정보:

Type: A
Name: @
Value: 76.76.21.21

Type: CNAME
Name: www
Value: cname.vercel-dns.com

→ Cafe24 DNS 관리 페이지에서 위 정보 입력
```

#### 4-3. DNS 전파 대기
```
대기 시간: 10분 ~ 48시간 (보통 10분)
확인: https://repost.kr 접속
```

#### 4-4. SSL 자동 발급 확인
```
Vercel이 자동으로 Let's Encrypt 인증서 발급
→ https://repost.kr로 자동 리다이렉트
→ 🔒 자물쇠 아이콘 확인
```

---

### Step 5: 배포 확인 및 검증

#### 5-1. 기능 테스트
```
✅ 메인 페이지 로딩
✅ 블로그 URL 입력 및 분석
✅ 댓글 생성 확인
✅ 댓글 복사 기능
✅ 블로그 이동 버튼
✅ 이용약관 페이지
✅ 개인정보처리방침 페이지
✅ 풋터 링크 작동
```

#### 5-2. 성능 테스트
```
1. https://pagespeed.web.dev 접속
2. https://repost.kr 입력
3. Performance 점수 확인 (목표: 90+)
```

#### 5-3. 모바일 테스트
```
1. 모바일 브라우저에서 접속
2. 반응형 디자인 확인
3. 터치 이벤트 작동 확인
```

---

## 🔧 설정 파일 설명

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {
    "PYTHONUNBUFFERED": "1"
  }
}
```

**설명:**
- `builds`: Python 앱을 빌드하는 방법 지정
- `routes`: URL 라우팅 규칙
  - `/static/*` → 정적 파일 (CSS, JS, 이미지)
  - `/*` → Flask 앱으로 전달
- `env`: 환경변수 설정

---

## 🔒 보안 설정

### 환경변수 관리
```
✅ Vercel 대시보드에서만 설정
✅ GitHub에 절대 업로드 금지
✅ 팀원 공유 시 Vercel 접근 권한 부여
```

### CORS 설정 (이미 완료)
```python
# app.py에 이미 설정됨
from flask_cors import CORS
CORS(app)
```

---

## 📊 모니터링 설정

### Vercel Analytics (무료)
```
1. Vercel 프로젝트 → "Analytics" 탭
2. "Enable Analytics" 클릭
3. 실시간 트래픽 모니터링 가능
```

### 제공 정보:
- ✅ 실시간 방문자 수
- ✅ 페이지뷰
- ✅ 평균 응답 시간
- ✅ 에러율
- ✅ 지역별 트래픽

---

## 🚨 문제 해결 (Troubleshooting)

### 문제 1: 500 Internal Server Error
```
원인: 환경변수 누락
해결:
1. Vercel 대시보드 → Settings → Environment Variables
2. OPENAI_API_KEY 확인
3. Redeploy 버튼 클릭
```

### 문제 2: Static 파일 로딩 안됨
```
원인: 경로 문제
해결:
1. vercel.json에서 routes 확인
2. 템플릿에서 url_for 사용 확인
3. /static/ 경로 체크
```

### 문제 3: Cold Start 느림
```
해결: Vercel은 자동으로 최적화
→ 첫 요청 후 캐싱
→ 이후 요청은 빠름 (<100ms)
```

### 문제 4: 도메인 연결 안됨
```
원인: DNS 전파 시간
해결:
1. 10-30분 대기
2. nslookup repost.kr 명령어로 확인
3. Vercel에서 DNS 상태 확인
```

---

## 🔄 배포 자동화

### Git Push → 자동 배포
```
1. 코드 수정
2. git add .
3. git commit -m "메시지"
4. git push
→ Vercel이 자동으로 감지하여 배포 시작!
```

### Preview 배포
```
브랜치를 생성하면:
→ 자동으로 Preview URL 생성
→ 프로덕션에 영향 없이 테스트 가능
→ 병합 전 검증 가능
```

---

## 📈 성능 최적화

### 이미 적용된 최적화
- ✅ Serverless Functions (자동 스케일링)
- ✅ Edge Network (글로벌 CDN)
- ✅ 자동 캐싱
- ✅ 이미지 최적화

### 추가 최적화 옵션 (선택)
```python
# app.py에 캐시 헤더 추가 (선택사항)
@app.after_request
def add_header(response):
    response.cache_control.max_age = 300  # 5분 캐싱
    return response
```

---

## 💰 비용 관리

### 무료 플랜 한도
```
✅ 대역폭: 100GB/월
✅ 함수 호출: 무제한
✅ 빌드 시간: 6000분/월
✅ 프로젝트: 무제한

→ 월 10,000명까지 충분!
```

### Pro 플랜 ($20/월)
```
필요한 경우:
- 월 방문자 10,000명 초과
- 더 긴 함수 실행시간 필요
- 더 많은 로그 보관
```

---

## ✅ 최종 체크리스트

### 배포 완료 확인
- [ ] https://repost.kr 접속 가능
- [ ] SSL 인증서 (🔒) 확인
- [ ] 메인 페이지 정상 로딩
- [ ] 블로그 분석 기능 작동
- [ ] 댓글 생성 확인
- [ ] 모바일 반응형 확인
- [ ] 이용약관 페이지 접속
- [ ] 개인정보처리방침 접속
- [ ] Open Graph 이미지 표시
- [ ] 네이버 블로그 URL 검증 작동

### 모니터링 설정
- [ ] Vercel Analytics 활성화
- [ ] 에러 알림 설정
- [ ] 성능 지표 확인

### 보안 확인
- [ ] 환경변수 Vercel에만 설정
- [ ] GitHub에 API 키 없음
- [ ] HTTPS 강제 리다이렉트

---

## 🎉 배포 완료!

### 다음 단계
1. **사용자 피드백 수집**: 실제 사용자 반응 확인
2. **성능 모니터링**: Vercel Analytics 정기 확인
3. **기능 추가**: 유료 플랫폼 지원 준비
4. **마케팅 시작**: SNS, 블로그 커뮤니티 홍보

---

## 📞 지원

### Vercel 공식 문서
- [Vercel Documentation](https://vercel.com/docs)
- [Python on Vercel](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [Custom Domains](https://vercel.com/docs/concepts/projects/domains)

### 커뮤니티
- [Vercel Discord](https://vercel.com/discord)
- [GitHub Discussions](https://github.com/vercel/vercel/discussions)

---

## 📝 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|-----------|
| 2025-10-29 | 1.0 | 초안 작성 |

---

**배포 성공을 기원합니다! 🚀**

