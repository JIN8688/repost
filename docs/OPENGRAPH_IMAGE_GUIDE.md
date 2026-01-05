# 🎨 Repost 오픈그래프 이미지 가이드

## 📋 필요한 이미지 파일

Repost의 완벽한 SEO와 소셜 미디어 공유를 위해 다음 이미지 파일들이 필요합니다:

### 1. 오픈그래프 이미지 (최우선)
**파일명:** `og-image.png`  
**경로:** `/static/images/og-image.png`  
**크기:** 1200 x 630px  
**용도:** Facebook, LinkedIn, 카카오톡 등 소셜 미디어 공유 시 표시

**디자인 가이드:**
```
┌────────────────────────────────────────┐
│                                        │
│         🎨 Repost                      │
│                                        │
│   AI 블로그 댓글 자동 추천             │
│                                        │
│   블로그 네트워킹 시간을 90% 줄이는    │
│   AI 비서                              │
│                                        │
│   [그라데이션 배경: #667eea → #764ba2] │
│                                        │
└────────────────────────────────────────┘
```

**색상:**
- 배경: 그라데이션 (보라 #667eea → 핑크 #764ba2)
- 텍스트: 흰색 #ffffff
- 강조: 핑크 #ec4899

---

### 2. Favicon 세트
**필요한 파일들:**

#### favicon.ico
- **경로:** `/static/favicon.ico`
- **크기:** 32x32px (다중 크기 포함 가능)
- **형식:** ICO

#### favicon-16x16.png
- **경로:** `/static/images/favicon-16x16.png`
- **크기:** 16 x 16px
- **형식:** PNG

#### favicon-32x32.png
- **경로:** `/static/images/favicon-32x32.png`
- **크기:** 32 x 32px
- **형식:** PNG

---

### 3. Apple Touch Icon
**파일명:** `apple-touch-icon.png`  
**경로:** `/static/images/apple-touch-icon.png`  
**크기:** 180 x 180px  
**용도:** iOS 홈 화면에 추가 시 아이콘

---

### 4. PWA 아이콘
#### icon-192x192.png
- **경로:** `/static/images/icon-192x192.png`
- **크기:** 192 x 192px
- **용도:** Android Chrome 홈 화면

#### icon-512x512.png
- **경로:** `/static/images/icon-512x512.png`
- **크기:** 512 x 512px
- **용도:** PWA 스플래시 화면

---

### 5. Microsoft Tile Icon
**파일명:** `ms-icon-144x144.png`  
**경로:** `/static/images/ms-icon-144x144.png`  
**크기:** 144 x 144px  
**용도:** Windows 타일

---

## 🎨 디자인 가이드라인

### 브랜드 컬러
```css
Primary: #667eea (보라)
Secondary: #ec4899 (핑크)
Gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
Text: #ffffff (흰색)
```

### 로고 디자인
- 이모지: 🎨 (팔레트)
- 텍스트: "Repost"
- 폰트: Noto Sans KR, Bold (700)
- 그라데이션 텍스트 적용

### 타이포그래피
- 메인 텍스트: Noto Sans KR Bold
- 서브 텍스트: Noto Sans KR Medium
- 설명 텍스트: Noto Sans KR Regular

---

## 🛠️ 이미지 생성 도구 추천

### 온라인 도구
1. **Canva** (canva.com)
   - 템플릿: "Social Media" → "Facebook Post"
   - 크기: Custom 1200 x 630px

2. **Figma** (figma.com)
   - 프로페셔널한 디자인
   - 정확한 픽셀 제어

3. **Adobe Express** (adobe.com/express)
   - 빠른 제작
   - 다양한 템플릿

### 로컬 도구
- **Photoshop**: 전문가용
- **GIMP**: 무료 대안
- **Sketch**: macOS용

---

## 📝 체크리스트

이미지 준비가 완료되면 다음 위치에 파일을 배치하세요:

```
/static/
├── favicon.ico
├── manifest.json (✅ 완료)
├── robots.txt (✅ 완료)
└── images/
    ├── og-image.png (⚠️ 필요)
    ├── favicon-16x16.png (⚠️ 필요)
    ├── favicon-32x32.png (⚠️ 필요)
    ├── apple-touch-icon.png (⚠️ 필요)
    ├── icon-192x192.png (⚠️ 필요)
    ├── icon-512x512.png (⚠️ 필요)
    └── ms-icon-144x144.png (⚠️ 필요)
```

---

## 🧪 테스트 방법

### Open Graph 테스트
1. **Facebook Sharing Debugger**
   - URL: https://developers.facebook.com/tools/debug/
   - 입력: https://repost.kr
   - "Scrape Again" 클릭

2. **Twitter Card Validator**
   - URL: https://cards-dev.twitter.com/validator
   - 입력: https://repost.kr

3. **LinkedIn Post Inspector**
   - URL: https://www.linkedin.com/post-inspector/
   - 입력: https://repost.kr

4. **카카오톡 캐시 초기화**
   - URL: https://developers.kakao.com/tool/clear/og
   - 입력: https://repost.kr

---

## 💡 현재 상태

### ✅ 완료된 SEO 최적화
- [x] 완벽한 메타 태그 (title, description, keywords)
- [x] Open Graph 메타 태그 (Facebook, LinkedIn)
- [x] Twitter Card 메타 태그
- [x] robots.txt 최적화
- [x] manifest.json (PWA)
- [x] Canonical URL
- [x] Structured Data (JSON-LD)
- [x] 다국어 지원 (ko_KR)
- [x] Theme color
- [x] Mobile-friendly 메타 태그
- [x] Sitemap.xml (이미 존재)

### ⚠️ 이미지 파일 필요
오픈그래프 이미지와 파비콘 세트를 생성하여 위 경로에 배치하면 SEO 최적화가 100% 완료됩니다!

---

## 🚀 배포 후 확인사항

1. 이미지 파일 업로드 확인
2. https://repost.kr/static/images/og-image.png 접근 테스트
3. Facebook/Twitter/LinkedIn에서 공유 테스트
4. Google Search Console에 sitemap 제출
5. 네이버 서치어드바이저에 sitemap 제출

---

**이미지가 준비되는 대로 알려주시면 즉시 적용하겠습니다!** 🎨

