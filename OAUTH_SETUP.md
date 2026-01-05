# Repost - Neon PostgreSQL & OAuth 설정 가이드

## 🚀 환경 설정

### 1. Neon PostgreSQL 데이터베이스 설정

1. **Neon 계정 생성** (무료)
   - https://neon.tech 에서 계정 생성
   - 새 프로젝트 생성

2. **데이터베이스 연결 문자열 가져오기**
   - 프로젝트 대시보드에서 "Connection String" 복사
   - 형식: `postgresql://user:password@host/database?sslmode=require`

3. **.env 파일에 추가**
   ```bash
   DATABASE_URL=your_neon_database_connection_string_here
   ```

### 2. OAuth 설정

#### Google OAuth
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 생성 또는 선택
3. "API 및 서비스" → "사용자 인증 정보" 이동
4. "OAuth 2.0 클라이언트 ID" 생성
5. 승인된 리디렉션 URI 추가:
   - `http://localhost:5000/auth/google/callback` (개발)
   - `https://yourdomain.com/auth/google/callback` (프로덕션)
6. 클라이언트 ID와 시크릿 복사

**.env에 추가:**
```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

#### Kakao OAuth
1. [Kakao Developers](https://developers.kakao.com/) 접속
2. "내 애플리케이션" → "애플리케이션 추가하기"
3. "앱 키" → REST API 키 복사
4. "플랫폼" → "Web" 추가 → 사이트 도메인 등록
5. "Redirect URI" 등록:
   - `http://localhost:5000/auth/kakao/callback` (개발)
   - `https://yourdomain.com/auth/kakao/callback` (프로덕션)
6. "동의항목" → 이메일, 닉네임 필수 동의 설정

**.env에 추가:**
```bash
KAKAO_CLIENT_ID=your_kakao_rest_api_key
KAKAO_CLIENT_SECRET=your_kakao_client_secret
```

#### Naver OAuth
1. [Naver Developers](https://developers.naver.com/) 접속
2. "Application" → "애플리케이션 등록"
3. 사용 API: "네아로 (Naver Login)" 선택
4. Callback URL 등록:
   - `http://localhost:5000/auth/naver/callback` (개발)
   - `https://yourdomain.com/auth/naver/callback` (프로덕션)
5. 제공정보: 이메일, 이름 선택
6. Client ID와 Client Secret 복사

**.env에 추가:**
```bash
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
```

### 3. Flask Secret Key 설정

강력한 랜덤 키 생성:
```python
import secrets
print(secrets.token_hex(32))
```

**.env에 추가:**
```bash
SECRET_KEY=your_generated_secret_key
```

### 4. 전체 .env 파일 예시

```bash
# Neon PostgreSQL
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require

# Google OAuth
GOOGLE_CLIENT_ID=123456789-xxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxx

# Kakao OAuth
KAKAO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxx
KAKAO_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxx

# Naver OAuth
NAVER_CLIENT_ID=xxxxxxxxxxxxx
NAVER_CLIENT_SECRET=xxxxxxxxxx

# Flask
SECRET_KEY=your_super_secret_key_here

# OpenAI (기존)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# Redis (기존)
REDIS_URL=redis://your-redis-url
```

## 🎯 로컬 실행

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. 환경 변수 설정 (.env 파일 생성)
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력

# 3. 데이터베이스 테이블 자동 생성 (자동 실행됨)
# app.py가 실행되면 자동으로 테이블이 생성됩니다

# 4. Flask 앱 실행
python app.py
```

## 🚀 Vercel 배포

Vercel 프로젝트 설정에서 환경 변수 추가:
- Settings → Environment Variables
- 위의 모든 환경 변수를 추가

**주의:** Callback URL은 프로덕션 도메인으로 변경해야 합니다!

## ✅ 테이블 구조

### users 테이블
- id: 고유 ID (자동 증가)
- email: 이메일 (중복 불가)
- password_hash: 비밀번호 해시
- name: 이름
- plan: 요금제 (free, basic, pro)
- marketing_consent: 마케팅 동의
- oauth_provider: OAuth 제공자 (google, kakao, naver)
- oauth_id: OAuth ID
- profile_image: 프로필 이미지 URL
- created_at: 가입일
- last_login: 마지막 로그인
- is_active: 활성 상태

### usage_history 테이블
- id: 고유 ID
- user_id: 사용자 ID (외래키)
- action_type: 행동 유형
- created_at: 생성일
- metadata: 메타데이터 (JSON)

## 🔐 보안 주의사항

1. **.env 파일을 절대 Git에 커밋하지 마세요!**
2. 프로덕션 환경에서는 강력한 SECRET_KEY 사용
3. HTTPS 사용 (Let's Encrypt 무료 SSL)
4. OAuth Callback URL은 반드시 HTTPS 사용 (프로덕션)

## 📞 문제 발생 시

- Database 연결 오류: DATABASE_URL 확인
- OAuth 오류: Callback URL 확인
- 패키지 오류: `pip install -r requirements.txt` 재실행

## 🎉 완료!

모든 설정이 완료되면:
- `/signup` - 회원가입 (이메일 또는 소셜)
- `/login-page` - 로그인 (이메일 또는 소셜)
- 소셜 로그인 버튼 클릭 시 자동으로 OAuth 인증 진행!

