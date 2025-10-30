# Cafe24 DNS 설정 가이드 (Vercel 연결)

## 🎯 목표
repost.kr 도메인을 Vercel에 연결하기

---

## 📋 설정해야 할 DNS 레코드

### 1. A 레코드 (필수)
```
호스트명: @
타입: A
값: 76.76.21.21
TTL: 3600 (기본값)
```

### 2. CNAME 레코드 (필수)
```
호스트명: www
타입: CNAME
값: cname.vercel-dns.com.
TTL: 3600 (기본값)
```

**⚠️ 주의사항:**
- `www`만 입력 (www.repost.kr 입력하면 실패!)
- CNAME 값 끝에 `.` (점) 붙이는 것 권장
- 기존 www 레코드가 있으면 먼저 삭제

---

## 🔧 Cafe24 설정 단계

### Step 1: Cafe24 로그인
```
1. https://www.cafe24.com 접속
2. 로그인
3. "나의 서비스 관리" → "도메인" 클릭
```

### Step 2: DNS 관리 페이지 접속
```
1. repost.kr 도메인 선택
2. "부가서비스" → "DNS 레코드 관리" 클릭
```

### Step 3: 기존 레코드 확인
```
⚠️ 중요: 기존 www 레코드가 있는지 확인!

있다면:
→ 기존 www 레코드 삭제 후 진행
→ 충돌 방지
```

### Step 4: A 레코드 추가
```
1. "레코드 추가" 버튼 클릭
2. 타입: A
3. 호스트명: @
4. 값: 76.76.21.21
5. "저장" 클릭
```

### Step 5: CNAME 레코드 추가
```
1. "레코드 추가" 버튼 클릭
2. 타입: CNAME
3. 호스트명: www
4. 값: cname.vercel-dns.com. (점 포함)
5. "저장" 클릭
```

### Step 6: 설정 확인
```
설정 후 목록에 이렇게 표시되어야 함:

@ → A → 76.76.21.21
www → CNAME → cname.vercel-dns.com.
```

---

## ✅ 검증 방법

### 1. 터미널에서 DNS 확인
```bash
# A 레코드 확인
nslookup repost.kr

# CNAME 레코드 확인
nslookup www.repost.kr
```

### 2. 온라인 도구로 확인
```
https://dnschecker.org
→ repost.kr 입력
→ 전세계 DNS 전파 상태 확인
```

### 3. 브라우저에서 확인 (10분 후)
```
https://repost.kr → 정상 접속되면 성공!
https://www.repost.kr → 정상 접속되면 성공!
```

---

## 🚨 자주 발생하는 에러

### 에러 1: "별칭(CNAME) 추가에 실패하였습니다"
**원인:**
- ❌ www.repost.kr 전체 입력 (잘못됨)
- ❌ 기존 www 레코드와 충돌
- ❌ 잘못된 값 입력

**해결:**
```
1. 기존 www 레코드 삭제
2. 호스트명에 "www"만 입력 (도메인 제외)
3. 값에 "cname.vercel-dns.com." 입력
```

### 에러 2: DNS가 전파되지 않음
**원인:**
- DNS 전파 시간 필요 (10분~48시간)

**해결:**
```
1. 10-30분 대기
2. 브라우저 캐시 삭제
3. 시크릿 모드로 접속
```

### 에러 3: SSL 인증서 에러
**원인:**
- DNS 전파 완료되지 않음
- Vercel SSL 생성 중

**해결:**
```
1. Vercel 대시보드에서 "Refresh" 클릭
2. SSL 생성 완료까지 대기 (최대 10분)
3. https://repost.kr 접속 확인
```

---

## 📞 추가 도움

### Vercel에서 정확한 DNS 값 확인
```
1. Vercel 대시보드 → repost 프로젝트
2. Settings → Domains
3. repost.kr 클릭
4. "View DNS Records" 확인
```

### Cafe24 고객센터
```
전화: 1544-8614
채팅: Cafe24 웹사이트 우측 하단
→ DNS 설정 문의 가능
```

---

## 🎉 성공 확인

모든 설정 완료 후:

```
✅ https://repost.kr → 정상 접속
✅ https://www.repost.kr → 정상 접속
✅ 🔒 자물쇠 아이콘 (SSL 인증서)
✅ Vercel 대시보드에서 "Valid Configuration"
```

**축하합니다! 도메인 연결 완료! 🎊**

---

작성일: 2025년 10월 30일

