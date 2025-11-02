from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import requests
from bs4 import BeautifulSoup
import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from urllib.parse import urlparse, parse_qs
import redis
from collections import Counter
import pytz

# 🇰🇷 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

def get_kst_now():
    """한국 시간(KST) 현재 시각 반환"""
    return datetime.now(KST)

# Vercel Serverless 환경에서도 로그가 보이도록 설정
def log(message, level="INFO"):
    """Vercel에서도 보이는 로그 출력"""
    timestamp = get_kst_now().strftime('%H:%M:%S')
    formatted_message = f"[{timestamp}] {level}: {message}"
    print(formatted_message, flush=True)
    sys.stdout.flush()
    sys.stderr.flush()

# 📊 Analytics 로깅 시스템 (Vercel KV + GA4)
def log_analytics(action, data=None, success=True, error_message=None):
    """
    사용자 행동 로깅 - Vercel KV (Redis)에 저장
    
    Args:
        action: 액션 유형 ('blog_analyzed', 'comment_copied', 'blog_visited')
        data: 추가 데이터 (dict)
        success: 성공 여부
        error_message: 실패 시 에러 메시지
    """
    try:
        # 서버 로그 출력
        log(f"📊 Analytics: {action} | success={success}", "ANALYTICS")
        
        # Vercel KV에 저장 (Redis 프로토콜)
        if redis_client:
            try:
                now_kst = get_kst_now()
                today = now_kst.strftime('%Y-%m-%d')
                hour = now_kst.strftime('%H')
                status = 'success' if success else 'failed'
                
                # 1. 전체 카운트 증가
                redis_client.incr(f"analytics:total:{action}")
                
                # 2. 오늘 카운트 증가
                key_daily = f"analytics:daily:{today}:{action}"
                redis_client.incr(key_daily)
                redis_client.expire(key_daily, 2592000)  # 30일
                
                # 3. 성공/실패 카운트
                redis_client.incr(f"analytics:{status}:{action}")
                
                # 4. 시간대별 카운트 (오늘만)
                key_hourly = f"analytics:hourly:{today}:{hour}"
                redis_client.incr(key_hourly)
                redis_client.expire(key_hourly, 86400)  # 24시간
                
                # 5. 브라우저/디바이스/OS 통계 (page_view 이벤트에서만)
                if action == 'page_view' and data:
                    if 'browser' in data:
                        redis_client.incr(f"analytics:browser:{data['browser']}")
                    if 'deviceType' in data:
                        redis_client.incr(f"analytics:device:{data['deviceType']}")
                    if 'os' in data:
                        redis_client.incr(f"analytics:os:{data['os']}")
                
                # 6. 피드백 통계 (rating별 카운트)
                if action == 'quick_feedback' and data and 'rating' in data:
                    rating = data['rating']
                    redis_client.incr(f"analytics:feedback:rating_{rating}")
                
                log(f"✅ KV 저장 완료: {action}", "ANALYTICS")
                
            except Exception as kv_error:
                log(f"⚠️ KV 저장 실패: {kv_error}", "WARNING")
        
        if error_message:
            log(f"⚠️ Error: {error_message}", "ERROR")
        
    except Exception as e:
        log(f"⚠️ Analytics logging failed: {e}", "WARNING")

# 로컬 개발 환경에서만 .env 파일 로드
if os.path.exists('.env'):
    load_dotenv()
    log("📁 .env 파일 로드됨 (로컬 개발 모드)")
else:
    log("☁️ 배포 환경 - 시스템 환경변수 사용")

app = Flask(__name__)
CORS(app)

# 🔐 세션 보안 설정
app.secret_key = os.environ.get('SECRET_KEY', 'repost-admin-secret-key-change-this-in-production')
# HTTPS 환경에서만 Secure Cookie 사용 (로컬 테스트 시 http 허용)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# 🔐 관리자 계정 설정 (환경변수에서 가져오기)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'repost2025!')

# 🔐 로그인 필수 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# 📊 Redis (Vercel KV) 클라이언트 초기화
redis_client = None
try:
    redis_url = os.environ.get('KV_REDIS_URL') or os.environ.get('REDIS_URL')
    
    if redis_url:
        # Redis 프로토콜 연결
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,  # 문자열로 자동 디코딩
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # 연결 테스트
        redis_client.ping()
        log("✅ Vercel KV (Redis) 연결 성공!")
    else:
        log("⚠️ KV 환경변수 없음 - GA4만 사용")
        redis_client = None
except Exception as e:
    log(f"⚠️ KV 연결 실패: {e} - GA4만 사용")
    redis_client = None

# OpenAI 클라이언트 초기화
api_key = os.environ.get('OPENAI_API_KEY')
log(f"🔑 환경변수 확인: OPENAI_API_KEY={'있음 ('+api_key[:10]+'...)' if api_key else '❌ 없음'}")

# 클라이언트 초기화 (에러 핸들링 추가)
client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
        log("✅ OpenAI 클라이언트 초기화 성공!")
    except Exception as e:
        log(f"❌ OpenAI 클라이언트 초기화 실패: {e}")
        client = None
else:
    log("⚠️ API 키가 없어서 기본 템플릿 사용")

def scrape_blog_content(url):
    """네이버 블로그 내용 스크래핑"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.naver.com/'
        }
        # 네이버 블로그 URL 파싱 (모바일/데스크톱 모두 지원)
        blog_id = None
        log_no = None
        
        if 'blog.naver.com' in url or 'm.blog.naver.com' in url:
            # URL 파싱
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # 1. 쿼리 파라미터에서 추출 (모바일 URL)
            if 'blogId' in query_params and 'logNo' in query_params:
                blog_id = query_params['blogId'][0]
                log_no = query_params['logNo'][0]
                print(f"📱 모바일 URL 감지: blogId={blog_id}, logNo={log_no}")
            
            # 2. 경로에서 추출 (데스크톱 URL)
            elif '/' in parsed_url.path:
                path_parts = parsed_url.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    blog_id = path_parts[0]
                    log_no = path_parts[-1]
                    print(f"🖥️ 데스크톱 URL 감지: blogId={blog_id}, logNo={log_no}")
            
            # blogId와 logNo가 있으면 정규 URL로 접근
            if blog_id and log_no:
                content_url = f'https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}'
                print(f"🔗 변환된 URL: {content_url}")
                response = requests.get(content_url, headers=headers, timeout=10, allow_redirects=True)
            else:
                response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        else:
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 제목 추출
        title = ''
        title_selectors = [
            'meta[property="og:title"]',
            'title',
            '.se-title-text',
            '.pcol1'
        ]
        for selector in title_selectors:
            title_tag = soup.select_one(selector)
            if title_tag:
                title = title_tag.get('content', '') or title_tag.get_text(strip=True)
                if title:
                    break
        
        # 본문 내용 추출
        content = ''
        content_selectors = [
            'meta[property="og:description"]',
            '.se-main-container',
            '#postViewArea',
            '.post-view',
            'article'
        ]
        for selector in content_selectors:
            content_tag = soup.select_one(selector)
            if content_tag:
                content = content_tag.get('content', '') or content_tag.get_text(strip=True)
                if content:
                    break
        
        # 내용이 너무 길면 일부만 사용 (1000자)
        if len(content) > 1000:
            content = content[:1000] + '...'
        
        return {
            'title': title or '제목 없음',
            'content': content or '내용을 가져올 수 없습니다.',
            'url': url
        }
    
    except Exception as e:
        return {
            'title': '오류',
            'content': f'블로그 내용을 가져오는 중 오류가 발생했습니다: {str(e)}',
            'url': url
        }

def generate_comments_with_ai(title, content):
    """OpenAI를 사용하여 블로그 내용 기반 댓글 생성 (프로덕션 레벨)"""
    log("=" * 60)
    log("🤖 AI 댓글 생성 함수 시작", "AI")
    log("=" * 60)
    
    try:
        if not client:
            log("❌ OpenAI 클라이언트가 초기화되지 않음 → 템플릿 사용", "WARNING")
            return None
        
        log("✅ OpenAI 클라이언트 확인 완료", "AI")
        
        # 블로그 내용 요약 및 정제
        content_preview = content[:500] if len(content) > 500 else content
        content_preview = content_preview.strip()
        
        if not content_preview:
            log("❌ 블로그 내용이 비어있음 → 템플릿 사용", "WARNING")
            return None
        
        log(f"📝 블로그 제목: {title[:50]}...", "AI")
        log(f"📝 내용 길이: {len(content)}자 (미리보기: {len(content_preview)}자)", "AI")
        
        prompt = f"""다음은 네이버 블로그 글입니다. 이 글을 실제로 읽은 사람처럼 자연스러운 댓글을 **정확히 8개** 한국어로 작성해주세요.

블로그 제목: {title}
블로그 내용: {content_preview}

요구사항:
1. **반드시 정확히 8개의 댓글을 생성해야 합니다** (중요!)
2. 실제 블로그 내용을 구체적으로 언급하는 댓글
3. 자연스럽고 친근한 톤
4. 이모지 적절히 사용
5. 길이: 짧은 댓글 5개(10-25자), 긴 댓글 3개(30-50자)
6. 스팸처럼 보이지 않는 진심 어린 댓글
7. 각 댓글은 서로 다른 스타일로

반드시 JSON 형식으로만 응답하세요:
{{"comments": ["댓글1", "댓글2", "댓글3", "댓글4", "댓글5", "댓글6", "댓글7", "댓글8"]}}

주의: 댓글이 8개가 안 되면 안 됩니다! 반드시 8개를 채워주세요!"""

        # OpenAI API 호출 (JSON 모드 강제, 토큰 증가)
        log("🚀 OpenAI API 호출 시작...", "AI")
        log(f"   모델: gpt-3.5-turbo-1106, max_tokens: 1000", "AI")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": "당신은 블로그 댓글을 작성하는 친근한 한국인입니다. 반드시 JSON 형식으로만 응답하고, 정확히 8개의 댓글을 생성해야 합니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
            max_tokens=1000
        )
        
        log("✅ OpenAI API 응답 수신 완료", "AI")
        
        # 응답 검증
        if not response.choices or not response.choices[0].message.content:
            log("❌ AI 응답이 비어있음 → 템플릿 사용", "ERROR")
            return None
        
        # JSON 파싱 (안전하게)
        import json
        response_text = response.choices[0].message.content.strip()
        log(f"📥 AI 응답 받음 (길이: {len(response_text)}자)", "AI")
        log(f"   내용 미리보기: {response_text[:150]}...", "AI")
        
        try:
            result = json.loads(response_text)
            log("✅ JSON 파싱 성공", "AI")
        except json.JSONDecodeError as je:
            log(f"❌ JSON 파싱 실패: {je} → 템플릿 사용", "ERROR")
            log(f"   응답 내용: {response_text[:200]}", "ERROR")
            return None
        
        # 댓글 배열 검증
        comments = result.get('comments', [])
        log(f"📊 댓글 배열 추출: {len(comments)}개 받음", "AI")
        
        if not isinstance(comments, list) or len(comments) == 0:
            log(f"❌ 댓글 형식 오류: 타입={type(comments)}, 길이={len(comments) if isinstance(comments, list) else 0} → 템플릿 사용", "ERROR")
            return None
        
        # 유효한 댓글만 필터링
        valid_comments = [c for c in comments if isinstance(c, str) and len(c.strip()) > 0]
        log(f"✅ 유효한 댓글 필터링: {len(valid_comments)}개", "AI")
        
        if len(valid_comments) < 3:
            log(f"⚠️ 유효한 댓글이 너무 적음: {len(valid_comments)}개 → 템플릿 사용", "WARNING")
            return None
        
        # 댓글 내용 미리보기
        for i, comment in enumerate(valid_comments[:3], 1):
            log(f"   💬 댓글 {i}: {comment[:30]}...", "AI")
        
        log("=" * 60, "AI")
        log(f"🎉 AI 댓글 생성 최종 성공! 총 {len(valid_comments)}개 반환", "SUCCESS")
        log("=" * 60, "AI")
        
        return valid_comments[:8]
    
    except Exception as e:
        log("=" * 60, "ERROR")
        log(f"❌ AI 댓글 생성 중 예외 발생", "ERROR")
        log(f"   예외 타입: {type(e).__name__}", "ERROR")
        log(f"   예외 메시지: {str(e)}", "ERROR")
        log("   → 템플릿 댓글로 대체합니다", "ERROR")
        log("=" * 60, "ERROR")
        import traceback
        traceback.print_exc()
        return None

def generate_template_comments(title, content, count=8):
    """기본 템플릿을 사용하여 댓글 생성 (내부 함수)"""
    comments = []
    text = (title + ' ' + content).lower()
    
    # 제목에서 핵심 키워드 추출 (명사형 단어들)
    title_words = [word for word in title.split() if len(word) > 1]
    
    # 상세 키워드 기반 맞춤형 댓글 (대폭 확장!)
    keyword_patterns = {
        # 맛집 관련
        ('맛집', '음식점', '카페', '레스토랑', '식당'): [
            f'{title_words[0] if title_words else "여기"} 정말 가보고 싶네요! 상세한 후기 감사합니다 😊',
            f'와 {title_words[0] if title_words else "이곳"} 분위기 좋아보이네요! 다음에 꼭 방문해볼게요!',
            '메뉴 구성이 정말 괜찮아 보이네요! 리뷰 보고 가고 싶어졌어요 👍',
            '사진만 봐도 맛있어 보이네요! 상세한 리뷰 너무 감사합니다!',
            '인테리어도 예쁘고 메뉴도 다양하네요! 저장해뒀다가 꼭 가볼게요 ⭐',
            '가격대도 합리적인 것 같고 분위기도 좋아보여요! 데이트 코스로 좋을 것 같아요 💕',
            '주차 정보까지 알려주셔서 정말 도움됐어요! 주말에 방문 계획 잡아야겠어요!',
            '웨이팅이 있을 것 같은데 그만큼 맛있다는 거겠죠? 기대되네요!',
            '사진 퀄리티가 장난 아니네요! 실제로 가면 더 예쁠 것 같아요 📸',
            '메뉴판 사진까지 올려주셔서 미리 뭐 먹을지 고를 수 있겠어요! 감사합니다!',
            '근처에 볼 거리도 많은 것 같은데 코스로 묶어서 가면 좋겠네요!',
            '리뷰 보니까 재방문 의사 100%시네요 ㅎㅎ 저도 한번 가봐야겠어요!',
        ],
        ('맛있', '맛나', '맛집', '먹', '음식', '메뉴'): [
            '포스팅 보니까 정말 맛있어 보이네요! 꼭 가봐야겠어요!',
            '이렇게 자세한 리뷰 남겨주셔서 감사해요! 메뉴 선택에 도움이 많이 됐어요!',
            '사진 보니까 침이 고이네요 ㅎㅎ 좋은 정보 감사합니다!',
            '비주얼이 정말 예술이네요! 맛도 비주얼만큼 좋을 것 같아요 😋',
            '양도 푸짐하고 가성비 좋아보여요! 이 가격이면 완전 혜자네요!',
            '시그니처 메뉴 추천해주셔서 감사해요! 처음 가는데 뭐 먹을지 고민했거든요!',
            '재료가 신선해 보이고 정성이 가득 느껴지네요! 맛집 인정입니다 👍',
            '먹방 유튜버처럼 상세하게 설명해주시네요 ㅎㅎ 너무 잘 봤습니다!',
            '디저트까지 완벽하네요! 식후 커피 한잔하기 딱 좋을 것 같아요 ☕',
            '계절 한정 메뉴라니! 놓치지 말고 빨리 가봐야겠어요!',
        ],
        
        # 여행 관련
        ('여행', '관광', '여행지', '투어', '트립'): [
            f'{title_words[0] if title_words else "여기"} 여행 계획 중인데 정말 유용한 정보네요!',
            '여행 코스 참고하겠습니다! 자세한 후기 너무 좋아요 ✈️',
            '사진 보니까 정말 가고 싶네요! 일정 짤 때 참고할게요!',
            '이런 숨은 명소가 있었다니! 포스팅 감사합니다!',
            '교통편이랑 숙소 정보까지 꼼꼼하게 정리해주셔서 너무 좋아요!',
            '여행 경비 정보도 있어서 예산 짜는데 도움이 많이 됐어요!',
            '날씨 정보까지! 완전 세심한 후기네요! 감사합니다 🌤️',
            '사진 찍기 좋은 포토존 정보까지 있어서 딱이에요!',
            '현지인 맛집 추천까지 해주시다니! 진짜 알찬 후기네요!',
            '가족 여행으로도 좋을 것 같아요! 아이들이 좋아할 만한 코스네요!',
            '비수기 때 가면 여유롭게 즐길 수 있겠네요! 팁 감사합니다!',
            '렌터카 정보 정말 유용했어요! 자유 여행 준비하는데 큰 도움됐습니다!',
        ],
        ('힐링', '휴양', '휴가', '쉼', '풍경', '바다', '산', '자연'): [
            '힐링 제대로 되겠어요! 저도 꼭 가보고 싶네요 🌿',
            '풍경이 정말 아름답네요! 좋은 곳 공유해주셔서 감사해요!',
            '일상에 지쳐있었는데 이런 곳에서 쉬고 싶네요! 힐링 스팟 저장했어요!',
            '자연 경관이 정말 압권이네요! 사진만 봐도 힐링됩니다 🏞️',
            '도심 속 휴양지라니! 이번 주말에 당장 가봐야겠어요!',
            '일몰 사진 진짜 예술이네요! 저도 그 시간에 맞춰서 가보고 싶어요 🌅',
            '조용하고 여유로운 분위기가 너무 좋아보여요! 혼자 가기도 좋을 것 같아요!',
            '반려동물과 함께 갈 수 있다니! 강아지랑 같이 가봐야겠어요 🐶',
        ],
        
        # 제품 리뷰/후기
        ('후기', '리뷰', '사용기', '체험', '언박싱', '개봉기'): [
            '솔직한 후기 너무 감사합니다! 구매 결정하는데 큰 도움이 됐어요!',
            '이런 상세한 리뷰 찾고 있었는데 딱이네요! 감사합니다 👏',
            '장단점을 잘 정리해주셔서 이해하기 쉬웠어요! 좋은 정보 감사합니다!',
            '실사용 후기라서 더 신뢰가 가네요! 포스팅 감사드려요!',
            '제품 비교까지 해주셔서 선택하는데 큰 도움됐어요!',
            '가격대비 성능 분석이 정말 꼼꼼하시네요! 참고 많이 됐습니다!',
            '사진이 고퀄이라 제품이 더 잘 보이네요! 구매 욕구 폭발입니다 💳',
            '단점까지 솔직하게 말씀해주셔서 더 신뢰가 가요! 객관적인 리뷰 감사합니다!',
            '사용 기간까지 명시해주셔서 신뢰도 높은 후기네요!',
            '타사 제품과 비교 분석까지! 정말 전문적인 리뷰네요!',
            '할인 정보까지 알려주셔서 감사해요! 바로 구매했습니다!',
            'AS 정보까지 있어서 좋네요! 꼼꼼한 후기 감사드려요!',
        ],
        ('추천', '강추', '인정', '좋', '최고', '굿'): [
            '추천해주신 내용 꼼꼼히 읽어봤어요! 정말 도움이 많이 됐습니다!',
            '이렇게 자세히 알려주시니 고민이 해결됐어요! 감사합니다!',
            '강추하시는 이유를 알겠네요! 저도 구매 리스트에 추가했어요!',
            '믿고 보는 리뷰어시네요! 다른 후기도 찾아봐야겠어요!',
            '가성비 최고라는 말에 완전 공감합니다! 저도 써보고 인정했어요!',
        ],
        
        # 정보성 글
        ('정보', '팁', 'tip', '방법', '노하우', '가이드', '알려'): [
            '유익한 정보 공유해주셔서 감사합니다! 바로 적용해볼게요!',
            '이런 꿀팁이! 포스팅 보고 많이 배웠어요 👍',
            '정말 필요한 정보였는데 감사합니다! 저장해뒀어요!',
            '자세한 설명 덕분에 이해가 쏙쏙 되네요! 감사해요!',
            '단계별로 설명해주셔서 따라하기 쉬울 것 같아요!',
            '이런 정보 찾느라 고생했는데 한번에 정리되어 있어서 너무 좋아요!',
            '초보자도 이해하기 쉽게 설명해주셔서 감사합니다!',
            '실용적인 팁이 가득하네요! 북마크 해뒀어요 📌',
            '전문가다운 설명이네요! 믿고 따라할 수 있을 것 같아요!',
            '그림이나 표까지 넣어주셔서 이해가 더 잘 돼요!',
        ],
        
        # 레시피/요리
        ('레시피', '요리', '만들', '조리', '음식', '베이킹'): [
            '레시피 너무 자세해서 좋아요! 저도 만들어봐야겠어요 🍳',
            '이렇게 간단하게 만들 수 있다니! 주말에 도전해볼게요!',
            '사진이랑 설명이 너무 잘 되어있어서 따라하기 쉬울 것 같아요!',
            '요리 초보인데도 따라할 수 있을 것 같아요! 쉽게 설명해주셔서 감사해요!',
            '재료 준비부터 완성까지 단계별로 알려주셔서 좋아요!',
            '비주얼이 정말 대박이네요! 맛도 좋을 것 같아요 😋',
            '대체 재료까지 알려주셔서 정말 꿀팁이에요!',
            '칼로리 정보까지! 다이어트 중인데 도움됩니다!',
            '냉장고에 있는 재료로 만들 수 있겠어요! 오늘 저녁 메뉴 결정!',
            '아이들도 좋아할 것 같은 메뉴네요! 주말에 함께 만들어봐야겠어요!',
        ],
        
        # 일상/공감
        ('일상', '하루', '오늘', '요즘', '브이로그', 'vlog'): [
            '공감가는 내용이 많네요! 잘 읽고 갑니다 😊',
            '저도 비슷한 경험이 있어서 더 공감이 가네요!',
            '일상 브이로그 느낌이라 편하게 잘 봤어요!',
            '소소한 일상이지만 힐링됐어요! 감사합니다!',
            '진솔한 이야기 잘 읽었습니다! 응원할게요!',
            '저도 이런 하루를 보내고 싶네요! 부러워요!',
            '공감 백배예요! 저만 그런 게 아니었네요 ㅎㅎ',
        ],
        
        # 뷰티/패션
        ('화장', '메이크업', '뷰티', '코스메틱', '스킨케어', '화장품'): [
            '제품 정보 너무 상세하게 알려주셔서 감사해요! 구매 리스트에 추가했어요!',
            '사용 후기가 궁금했는데 딱 원하던 정보네요! 감사합니다 💄',
            '피부 타입별로 설명해주셔서 좋네요! 제 피부에도 맞을 것 같아요!',
            '발색이 정말 예쁘네요! 색상 정보 감사합니다!',
            '가성비 좋은 제품 추천 감사해요! 바로 구매각이에요!',
            '성분 분석까지! 전문가시네요! 믿고 구매할 수 있겠어요!',
            '비포 애프터 사진 완전 대박이네요! 효과 확실한 것 같아요!',
            '민감성 피부인데 이 제품 써도 될까요? 후기가 너무 좋아서 관심 가네요!',
        ],
        ('패션', '옷', '코디', '스타일', '룩북', 'ootd'): [
            '스타일링 센스가 너무 좋으세요! 참고할게요 👗',
            '코디가 정말 세련됐어요! 어디서 구매하셨어요?',
            'OOTD 너무 예뻐요! 저도 따라입고 싶네요!',
            '체형별 코디 팁까지! 정말 유용한 정보네요!',
            '가을 룩북 완전 감각적이에요! 옷장 정리 참고할게요!',
            '키 작은 사람도 소화할 수 있는 코디네요! 감사합니다!',
        ],
        
        # 육아/교육
        ('육아', '아이', '아기', '엄마', '교육', '유아', '어린이'): [
            '육아 정보 너무 유익해요! 저도 적용해봐야겠어요!',
            '같은 고민 하고 있었는데 도움이 많이 됐어요! 감사합니다!',
            '워킹맘으로서 많은 공감이 갔어요! 함께 파이팅해요!',
            '아이 교육 방법 정말 좋네요! 우리 아이한테도 적용해볼게요!',
            '연령별 발달 정보까지 꼼꼼하시네요! 초보 엄마에게 큰 도움됐어요!',
            '육아 템 추천 감사해요! 이런 게 필요했는데 딱이네요!',
            '훈육 방법이 현실적이고 좋아보여요! 참고 많이 됩니다!',
        ],
        
        # 운동/건강
        ('운동', '헬스', '다이어트', '건강', '피트니스', '요가', '필라테스'): [
            '운동 루틴 참고하겠습니다! 동기부여 받고 가요 💪',
            '자세한 운동 방법 알려주셔서 감사해요! 따라해볼게요!',
            '다이어트 식단까지 공유해주시다니! 정말 감사합니다!',
            '운동 전후 사진 대박이에요! 저도 열심히 해야겠어요!',
            '홈트레이닝으로 이 정도 효과가 나온다니! 바로 시작합니다!',
            '초보자도 따라하기 쉽게 설명해주셔서 좋아요!',
            '부상 방지 팁까지! 안전하게 운동할 수 있겠어요!',
            '꾸준함이 정말 대단하세요! 저도 자극 받고 갑니다!',
        ],
        
        # IT/게임/테크
        ('게임', 'IT', '테크', '스마트폰', '컴퓨터', 'PC', '노트북'): [
            '기술 정보가 정말 상세하네요! IT 문외한인데 이해하기 쉬웠어요!',
            '스펙 비교 분석 감사합니다! 구매 결정하는데 도움됐어요!',
            '게임 리뷰 완전 디테일하네요! 구매 고민 중이었는데 결정했어요!',
            '최적화 팁 대박이에요! 바로 적용해봤습니다!',
            '가성비 제품 추천 감사해요! 가격대별로 알려주셔서 좋네요!',
        ],
        
        # 부동산/인테리어
        ('부동산', '인테리어', '집', '아파트', '전세', '매매', '주택', '리모델링'): [
            '부동산 정보 정말 유용해요! 집 알아보는 중인데 도움됐습니다!',
            '인테리어 센스가 정말 좋으시네요! 저희 집도 이렇게 꾸미고 싶어요!',
            '셀프 인테리어 팁 감사해요! 비용 절감할 수 있겠어요!',
            '공간 활용이 정말 효율적이네요! 작은 평수에 딱 필요한 정보예요!',
            '가구 배치 참고할게요! 3D 느낌이 나서 상상이 잘 돼요!',
        ],
        
        # 반려동물
        ('강아지', '고양이', '반려동물', '펫', '애견'): [
            '반려동물 정보 너무 유익해요! 초보 집사에게 딱이네요!',
            '강아지가 너무 귀여워요! 견종 정보도 자세히 알려주셔서 감사해요!',
            '고양이 돌보는 팁 정말 좋네요! 우리 냥이한테도 적용해볼게요!',
            '펫 용품 추천 감사합니다! 어떤 걸 사야 할지 고민이었거든요!',
        ],
    }
    
    # 키워드 매칭으로 댓글 생성
    matched = False
    for keywords, templates in keyword_patterns.items():
        if any(keyword in text for keyword in keywords):
            comments.extend(templates)
            matched = True
    
    # 블로그 제목의 핵심 단어를 활용한 개인화된 댓글 추가
    if title_words and matched:
        personalized = [
            f'"{title}" 글 너무 잘 읽었어요! 유익한 정보 감사합니다!',
            f'포스팅 제목보고 들어왔는데 기대 이상이네요! 알찬 정보 감사해요!',
        ]
        comments.extend(personalized)
    
    # 범용 고품질 댓글 (키워드 매칭 안된 경우)
    if not comments:
        comments = [
            '포스팅 정말 알차게 잘 쓰셨네요! 많은 도움이 됐어요!',
            '이렇게 자세한 글은 처음 봐요! 감사합니다 👍',
            '꼼꼼하게 작성해주셔서 읽기 편했어요! 좋은 정보 감사해요!',
            '궁금했던 내용이었는데 덕분에 궁금증이 해소됐어요!',
            '유익한 정보 공유해주셔서 감사합니다! 도움이 많이 됐어요!',
            '글 읽으면서 많이 배웠어요! 앞으로도 좋은 글 부탁드려요 😊',
            '상세한 설명 덕분에 이해가 쏙쏙 되네요! 감사합니다!',
            '정성스러운 포스팅 감사드립니다! 저장해뒀어요!',
        ]
    
    # 중복 제거 및 최대 8개까지만
    comments = list(dict.fromkeys(comments))[:8]
    
    # 최소 5개는 보장
    if len(comments) < 5:
        additional = [
            '블로그 자주 방문할게요! 좋은 글 감사합니다!',
            '유익한 정보 공유해주셔서 감사해요! 다음 글도 기대할게요!',
            '정말 유용한 내용이네요! 주변에도 공유하겠습니다!',
            '이런 양질의 콘텐츠 감사합니다! 구독하고 갑니다!',
        ]
        for comment in additional:
            if comment not in comments and len(comments) < 8:
                comments.append(comment)
    
    return comments

def generate_comments(blog_data):
    """블로그 내용을 기반으로 댓글 추천 생성 (AI 우선, 부족하면 템플릿 보충)"""
    title = blog_data['title']
    content = blog_data['content']
    
    log("━" * 60)
    log(f"📋 댓글 생성 프로세스 시작", "COMMENT")
    log(f"   블로그 제목: {title[:50]}...", "COMMENT")
    log("━" * 60)
    
    # AI 댓글 생성 시도
    ai_comments = generate_comments_with_ai(title, content)
    
    # AI 댓글이 8개 이상이면 그대로 반환
    if ai_comments and len(ai_comments) >= 8:
        log("━" * 60, "SUCCESS")
        log(f"🎉 100% AI 댓글 생성 완료! ({len(ai_comments)}개)", "SUCCESS")
        log("   템플릿 사용: 0개", "SUCCESS")
        log("━" * 60, "SUCCESS")
        return ai_comments[:8]
    
    # AI 댓글이 1개 이상 8개 미만이면 템플릿으로 보충
    if ai_comments and len(ai_comments) > 0:
        needed_count = 8 - len(ai_comments)
        log("━" * 60, "HYBRID")
        log(f"🔀 하이브리드 모드: AI {len(ai_comments)}개 + 템플릿 {needed_count}개", "HYBRID")
        log("━" * 60, "HYBRID")
        
        # 템플릿 댓글 생성
        template_comments = generate_template_comments(title, content, count=needed_count)
        
        # AI 댓글과 템플릿 댓글 합치기
        final_comments = ai_comments + template_comments[:needed_count]
        
        # 중복 제거 (혹시 모를 경우 대비)
        final_comments = list(dict.fromkeys(final_comments))
        
        # 여전히 8개가 안 되면 더 추가
        if len(final_comments) < 8:
            additional = [
                '블로그 자주 방문할게요! 좋은 글 감사합니다!',
                '유익한 정보 공유해주셔서 감사해요! 다음 글도 기대할게요!',
                '정말 유용한 내용이네요! 주변에도 공유하겠습니다!',
                '이런 양질의 콘텐츠 감사합니다! 구독하고 갑니다!',
                '포스팅 잘 봤습니다! 도움이 많이 됐어요 👍',
            ]
            for comment in additional:
                if comment not in final_comments and len(final_comments) < 8:
                    final_comments.append(comment)
        
        log(f"✅ 하이브리드 댓글 생성 완료: 총 {len(final_comments)}개", "HYBRID")
        log(f"   구성: AI {len(ai_comments)}개 + 템플릿 {len(final_comments)-len(ai_comments)}개", "HYBRID")
        log("━" * 60, "HYBRID")
        return final_comments[:8]
    
    # AI 댓글이 없으면 템플릿만 사용
    log("━" * 60, "TEMPLATE")
    log("⚠️ AI 생성 실패 → 100% 템플릿 댓글 사용", "TEMPLATE")
    log("━" * 60, "TEMPLATE")
    template_comments = generate_template_comments(title, content, count=8)
    return template_comments[:8]

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """파비콘 제공"""
    return app.send_static_file('images/logo-og.png')

@app.route('/robots.txt')
def robots():
    """robots.txt 제공 (네이버 검색 최적화)"""
    robots_txt = """User-agent: *
Allow: /

User-agent: Yeti
Allow: /

Sitemap: https://repost.kr/sitemap.xml
Sitemap: https://www.repost.kr/sitemap.xml
"""
    return robots_txt, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/sitemap.xml')
def sitemap():
    """sitemap.xml 제공"""
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
    
    <!-- 메인 페이지 -->
    <url>
        <loc>https://repost.kr/</loc>
        <lastmod>2025-10-30</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    
    <!-- 이용약관 -->
    <url>
        <loc>https://repost.kr/terms</loc>
        <lastmod>2025-10-10</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
    
    <!-- 개인정보처리방침 -->
    <url>
        <loc>https://repost.kr/privacy</loc>
        <lastmod>2025-10-10</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.5</priority>
    </url>
    
</urlset>"""
    return sitemap_xml, 200, {'Content-Type': 'application/xml; charset=utf-8'}

@app.route('/terms')
def terms():
    """이용약관 페이지"""
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    """개인정보처리방침 페이지"""
    return render_template('privacy.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_blog():
    """블로그 분석 및 댓글 추천 API"""
    try:
        data = request.json
        blog_url = data.get('url', '').strip()
        
        if not blog_url:
            return jsonify({'error': 'URL을 입력해주세요.'}), 400
        
        log("═" * 60)
        log("🚀 새로운 블로그 분석 요청 시작", "API")
        log(f"   URL: {blog_url}", "API")
        log("═" * 60)
        
        # 블로그 내용 스크래핑
        log("📡 블로그 스크래핑 시작...", "SCRAPE")
        blog_data = scrape_blog_content(blog_url)
        log(f"✅ 스크래핑 완료: {blog_data['title'][:50]}...", "SCRAPE")
        
        # 댓글 생성
        comments = generate_comments(blog_data)
        
        log("═" * 60, "API")
        log(f"🎉 전체 분석 완료! 댓글 {len(comments)}개 생성", "API")
        log("═" * 60, "API")
        
        # 📊 Analytics 로깅 (성공)
        log_analytics(
            action='blog_analyzed',
            data={
                'blog_url': blog_url,
                'title': blog_data.get('title', '')[:100],  # 제목 일부만
                'comments_count': len(comments)
            },
            success=True
        )
        
        return jsonify({
            'success': True,
            'blog': blog_data,
            'comments': comments
        })
    
    except Exception as e:
        # 📊 Analytics 로깅 (실패)
        log_analytics(
            action='blog_analyzed',
            data={'blog_url': blog_url if 'blog_url' in locals() else 'unknown'},
            success=False,
            error_message=str(e)
        )
        return jsonify({'error': f'오류가 발생했습니다: {str(e)}'}), 500

# 📊 Analytics 통계 계산 함수 (Vercel KV)
def get_analytics_stats(days=30):
    """
    Vercel KV에서 통계 데이터 조회 (Redis 프로토콜)
    
    Args:
        days: 최근 며칠간의 데이터 (기본 30일)
    
    Returns:
        dict: 통계 데이터
    """
    
    stats = {
        'total_analyses': 0,
        'success_analyses': 0,
        'failed_analyses': 0,
        'today_analyses': 0,
        'yesterday_analyses': 0,
        'week_analyses': 0,
        'month_analyses': 0,
        'hourly_stats': {},
        'daily_stats': {},
        'recent_logs': [],
        'top_blog_domains': {'네이버 블로그': 0},
        'conversion_funnel': {
            'visits': 0,
            'analyses': 0,
            'copies': 0,
            'visits_to_blog': 0
        },
        'success_rate': 0,
        'avg_comments_count': 8.0,
        # 새로운 통계
        'total_page_views': 0,
        'total_comment_copies': 0,
        'total_blog_visits': 0,
        'today_page_views': 0,
        'today_comment_copies': 0,
        'today_blog_visits': 0,
        'week_page_views': 0,
        'week_comment_copies': 0,
        'week_blog_visits': 0,
        'daily_page_views': {},
        'daily_comment_copies': {},
        'daily_blog_visits': {}
    }
    
    # Vercel KV가 없으면 빈 stats 반환
    if not redis_client:
        log("⚠️ KV 비활성화 - 빈 통계 반환", "WARNING")
        return stats
    
    try:
        today = get_kst_now()
        today_str = today.strftime('%Y-%m-%d')
        yesterday_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 1. 전체 통계
        try:
            val = redis_client.get("analytics:total:blog_analyzed")
            stats['total_analyses'] = int(val) if val else 0
        except: pass
        
        # 2. 성공/실패 통계
        try:
            val = redis_client.get("analytics:success:blog_analyzed")
            stats['success_analyses'] = int(val) if val else 0
        except: pass
        
        try:
            val = redis_client.get("analytics:failed:blog_analyzed")
            stats['failed_analyses'] = int(val) if val else 0
        except: pass
        
        # 3. 오늘 통계
        try:
            val = redis_client.get(f"analytics:daily:{today_str}:blog_analyzed")
            stats['today_analyses'] = int(val) if val else 0
        except: pass
        
        # 4. 어제 통계
        try:
            val = redis_client.get(f"analytics:daily:{yesterday_str}:blog_analyzed")
            stats['yesterday_analyses'] = int(val) if val else 0
        except: pass
        
        # 5. 시간대별 통계 (오늘)
        for hour in range(24):
            hour_str = f"{hour:02d}"
            try:
                val = redis_client.get(f"analytics:hourly:{today_str}:{hour_str}")
                count = int(val) if val else 0
                if count > 0:
                    stats['hourly_stats'][hour_str] = count
            except: pass
        
        # 6. 일별 통계 (최근 30일)
        for i in range(days):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            try:
                val = redis_client.get(f"analytics:daily:{date}:blog_analyzed")
                count = int(val) if val else 0
                stats['daily_stats'][date] = count
                
                # 주간/월간 합산
                if i < 7:
                    stats['week_analyses'] += count
                stats['month_analyses'] += count
            except: pass
        
        # 7. 페이지 뷰 통계
        try:
            val = redis_client.get("analytics:total:page_view")
            stats['total_page_views'] = int(val) if val else 0
        except: pass
        
        try:
            val = redis_client.get(f"analytics:daily:{today_str}:page_view")
            stats['today_page_views'] = int(val) if val else 0
        except: pass
        
        # 8. 댓글 복사 통계
        try:
            val = redis_client.get("analytics:total:comment_copied")
            stats['total_comment_copies'] = int(val) if val else 0
        except: pass
        
        try:
            val = redis_client.get(f"analytics:daily:{today_str}:comment_copied")
            stats['today_comment_copies'] = int(val) if val else 0
        except: pass
        
        # 9. 블로그 이동 통계
        try:
            val = redis_client.get("analytics:total:blog_visit")
            stats['total_blog_visits'] = int(val) if val else 0
        except: pass
        
        try:
            val = redis_client.get(f"analytics:daily:{today_str}:blog_visit")
            stats['today_blog_visits'] = int(val) if val else 0
        except: pass
        
        # 10. 주간 통계 (page_view, comment_copied, blog_visit)
        for i in range(7):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            try:
                val = redis_client.get(f"analytics:daily:{date}:page_view")
                stats['week_page_views'] += int(val) if val else 0
                
                val = redis_client.get(f"analytics:daily:{date}:comment_copied")
                stats['week_comment_copies'] += int(val) if val else 0
                
                val = redis_client.get(f"analytics:daily:{date}:blog_visit")
                stats['week_blog_visits'] += int(val) if val else 0
            except: pass
        
        # 11. 일별 통계 (30일)
        for i in range(days):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            try:
                val = redis_client.get(f"analytics:daily:{date}:page_view")
                stats['daily_page_views'][date] = int(val) if val else 0
                
                val = redis_client.get(f"analytics:daily:{date}:comment_copied")
                stats['daily_comment_copies'][date] = int(val) if val else 0
                
                val = redis_client.get(f"analytics:daily:{date}:blog_visit")
                stats['daily_blog_visits'][date] = int(val) if val else 0
            except: pass
        
        # 12. 전환율 계산
        stats['conversion_funnel']['visits'] = stats['total_page_views']
        stats['conversion_funnel']['analyses'] = stats['success_analyses']
        stats['conversion_funnel']['copies'] = stats['total_comment_copies']
        stats['conversion_funnel']['visits_to_blog'] = stats['total_blog_visits']
        
        # 13. 성공률 계산
        if stats['total_analyses'] > 0:
            stats['success_rate'] = round((stats['success_analyses'] / stats['total_analyses']) * 100, 1)
        
        # 14. 플랫폼 (네이버만 사용 중)
        stats['top_blog_domains']['네이버 블로그'] = stats['total_analyses']
        
        # 15. 브라우저 분포
        stats['browser_stats'] = {}
        for browser in ['Chrome', 'Safari', 'Edge', 'Firefox', 'Other']:
            try:
                val = redis_client.get(f"analytics:browser:{browser}")
                count = int(val) if val else 0
                if count > 0:
                    stats['browser_stats'][browser] = count
            except: pass
        
        # 16. 디바이스 분포
        stats['device_stats'] = {}
        for device in ['Desktop', 'Mobile', 'Tablet']:
            try:
                val = redis_client.get(f"analytics:device:{device}")
                count = int(val) if val else 0
                if count > 0:
                    stats['device_stats'][device] = count
            except: pass
        
        # 17. OS 분포
        stats['os_stats'] = {}
        for os in ['Windows', 'macOS', 'iOS', 'Android', 'Linux', 'Other']:
            try:
                val = redis_client.get(f"analytics:os:{os}")
                count = int(val) if val else 0
                if count > 0:
                    stats['os_stats'][os] = count
            except: pass
        
        # 18. 피드백 통계 (rating별)
        stats['feedback_stats'] = {}
        stats['total_feedbacks'] = 0
        for rating in [5, 4, 3, 2]:
            try:
                val = redis_client.get(f"analytics:feedback:rating_{rating}")
                count = int(val) if val else 0
                if count > 0:
                    stats['feedback_stats'][rating] = count
                    stats['total_feedbacks'] += count
            except: pass
        
        # 평균 만족도 계산
        if stats['total_feedbacks'] > 0:
            weighted_sum = sum(rating * count for rating, count in stats['feedback_stats'].items())
            stats['avg_rating'] = round(weighted_sum / stats['total_feedbacks'], 2)
        else:
            stats['avg_rating'] = 0
        
        log(f"✅ KV 통계 조회 완료: 총 {stats['total_analyses']}건", "ANALYTICS")
        
    except Exception as e:
        log(f"⚠️ KV 통계 조회 실패: {e}", "ERROR")
    
    return stats

@app.route('/api/track', methods=['POST'])
def track_event():
    """사용자 이벤트 트래킹 API"""
    try:
        data = request.json
        event_type = data.get('event')  # 'page_view', 'comment_copied', 'blog_visit'
        
        if not event_type:
            return jsonify({'error': 'event type required'}), 400
        
        # 이벤트별 로깅
        if event_type == 'page_view':
            # 브라우저/디바이스 정보 포함
            device_data = {
                'browser': data.get('browser', 'Other'),
                'deviceType': data.get('deviceType', 'Desktop'),
                'os': data.get('os', 'Other')
            }
            log_analytics('page_view', data=device_data, success=True)
        elif event_type == 'comment_copied':
            log_analytics('comment_copied', data={'comment': data.get('comment', '')[:50]}, success=True)
        elif event_type == 'blog_visit':
            log_analytics('blog_visit', data={'url': data.get('url', '')[:100]}, success=True)
        elif event_type == 'quick_feedback':
            log_analytics('quick_feedback', data={'rating': data.get('rating', 0)}, success=True)
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        log(f"⚠️ Track event failed: {e}", "ERROR")
        return jsonify({'error': str(e)}), 500

# ============================
# 🔐 관리자 로그인/로그아웃
# ============================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """관리자 로그인 페이지"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session.permanent = True
            log(f"✅ 관리자 로그인 성공: {username}", "ADMIN")
            return redirect(url_for('admin_dashboard'))
        else:
            log(f"⚠️ 로그인 실패 시도: {username}", "WARNING")
            return render_template('login.html', error='아이디 또는 비밀번호가 잘못되었습니다.')
    
    # 이미 로그인된 경우 대시보드로
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    """관리자 로그아웃"""
    session.pop('admin_logged_in', None)
    log("👋 관리자 로그아웃", "ADMIN")
    return redirect(url_for('admin_login'))

# ============================
# 📊 관리자 대시보드
# ============================

@app.route('/admin')
@login_required
def admin_dashboard():
    """📊 Analytics 대시보드 (로그인 필수)"""
    try:
        # 통계 계산
        stats = get_analytics_stats(days=30)  # 최근 30일
        
        return render_template('analytics.html', stats=stats)
    
    except Exception as e:
        log(f"⚠️ 대시보드 로드 실패: {e}", "ERROR")
        return f"오류: {str(e)}", 500

if __name__ == '__main__':
    # 로컬 개발용
    app.run(debug=True, port=5001)

