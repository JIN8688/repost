# 🚀 리포스트 배포 가이드 (Render.com)

완전 무료로 Render.com에 배포하는 방법입니다!

## 📋 사전 준비

1. **GitHub 계정** (https://github.com)
2. **Render.com 계정** (https://render.com) - GitHub로 로그인 가능

## 🔧 1단계: GitHub에 코드 올리기

### 1-1. GitHub 저장소 만들기

1. https://github.com 접속 및 로그인
2. 오른쪽 상단 `+` 버튼 클릭 → `New repository` 선택
3. 저장소 정보 입력:
   - Repository name: `repost` (원하는 이름)
   - Description: `블로그 댓글 자동 추천 프로그램`
   - Public 선택 (무료 배포를 위해)
4. `Create repository` 클릭

### 1-2. 로컬 코드를 GitHub에 푸시

터미널에서 다음 명령어를 순서대로 실행하세요:

```bash
# 프로젝트 폴더로 이동
cd "/Users/taejinkim/Desktop/IDEAS /Repost"

# Git 초기화 (이미 되어있으면 건너뛰기)
git init

# 모든 파일 추가
git add .

# 커밋
git commit -m "Initial commit: 리포스트 앱"

# GitHub 저장소 연결 (YOUR-USERNAME을 본인 GitHub 아이디로 변경)
git remote add origin https://github.com/YOUR-USERNAME/repost.git

# 푸시
git branch -M main
git push -u origin main
```

## 🌐 2단계: Render.com에서 배포하기

### 2-1. Render.com 가입

1. https://render.com 접속
2. `Get Started for Free` 클릭
3. `GitHub` 버튼으로 로그인 (GitHub 계정으로 간편 가입)

### 2-2. 새 Web Service 만들기

1. Render 대시보드에서 `New +` 버튼 클릭
2. `Web Service` 선택
3. GitHub 저장소 연결:
   - `Connect GitHub` 클릭
   - 방금 만든 `repost` 저장소 선택
   - `Connect` 클릭

### 2-3. 배포 설정

다음 정보를 입력하세요:

- **Name**: `repost` (또는 원하는 이름)
- **Region**: `Singapore` (한국과 가까움)
- **Branch**: `main`
- **Root Directory**: 비워두기
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Instance Type**: `Free` 선택

### 2-4. 환경 변수 설정 (선택사항)

특별한 환경 변수는 필요 없지만, 필요시 여기서 추가 가능합니다.

### 2-5. 배포 시작

1. 모든 설정 확인 후 `Create Web Service` 클릭
2. 배포 시작! (약 5-10분 소요)
3. 빌드 로그를 보면서 진행 상황 확인

## ✅ 3단계: 배포 완료 및 확인

### 배포 성공!

- 빌드가 완료되면 상단에 URL이 표시됩니다
- 예: `https://repost-xxxx.onrender.com`
- 이 URL을 클릭하면 앱이 실행됩니다!

### 주의사항

⚠️ **Free Tier 특징**:
- 15분 동안 사용하지 않으면 자동으로 슬립 모드
- 다시 접속하면 약 30초~1분 정도 로딩 시간 필요
- 월 750시간 무료 사용 가능 (충분!)

## 🔄 코드 업데이트 시

코드를 수정하고 다시 배포하려면:

```bash
cd "/Users/taejinkim/Desktop/IDEAS /Repost"
git add .
git commit -m "업데이트 내용 설명"
git push
```

GitHub에 푸시하면 Render가 **자동으로 재배포**합니다!

## 🎉 완료!

이제 전 세계 어디서나 접속 가능한 리포스트 앱이 완성되었습니다!

URL을 친구들에게 공유하세요! 😊

---

## 📞 문제 해결

### 빌드 실패 시

1. Render 대시보드에서 Logs 확인
2. 에러 메시지 확인 후 수정
3. GitHub에 다시 푸시하면 자동 재배포

### 느린 응답 속도

- Free tier는 15분 후 슬립 모드 진입
- 첫 접속 시 30초~1분 대기
- 이후에는 빠르게 동작

### 도메인 변경

- Render 설정에서 Custom Domain 추가 가능
- 본인 도메인 연결 가능 (선택사항)

