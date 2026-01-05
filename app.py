from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
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
import hashlib
import hmac

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
    
    ✨ NEW: DAU/WAU/MAU/신규/재방문/세션 시간 추적
    
    Args:
        action: 액션 유형 ('page_view', 'blog_analyzed', 'comment_copied', 'blog_visit')
        data: 추가 데이터 (dict) - userId, firstVisit, sessionDuration 포함
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
                
                # ✨ 5. DAU/WAU/MAU 추적 (page_view 이벤트에서만)
                if action == 'page_view' and data and 'userId' in data:
                    user_id = data['userId']
                    first_visit = data.get('firstVisit', '')
                    
                    log(f"👤 page_view 수신: userId={user_id[:20]}..., firstVisit={first_visit[:30] if first_visit else 'None'}...", "ANALYTICS")
                    
                    # DAU: 오늘 활성 사용자 (SET - 자동 중복 제거!)
                    redis_client.sadd(f'analytics:dau:{today}', user_id)
                    redis_client.expire(f'analytics:dau:{today}', 2592000)  # 30일
                    log(f"✅ DAU 저장: {user_id[:20]}... → analytics:dau:{today}", "ANALYTICS")
                    
                    # WAU: 최근 7일 활성 사용자 (각 날짜별 SET)
                    for i in range(7):
                        date = (now_kst - timedelta(days=i)).strftime('%Y-%m-%d')
                        if date == today:  # 오늘만 추가
                            redis_client.sadd(f'analytics:wau:{date}', user_id)
                            redis_client.expire(f'analytics:wau:{date}', 2592000)
                    
                    # MAU: 최근 30일 활성 사용자 (각 날짜별 SET)
                    for i in range(30):
                        date = (now_kst - timedelta(days=i)).strftime('%Y-%m-%d')
                        if date == today:  # 오늘만 추가
                            redis_client.sadd(f'analytics:mau:{date}', user_id)
                            redis_client.expire(f'analytics:mau:{date}', 2592000)
                    
                    # 신규 vs 재방문 사용자 구분
                    user_key = f'analytics:user:{user_id}:info'
                    user_exists = redis_client.exists(user_key)
                    
                    log(f"🔍 Redis 확인: user_key={user_key[:60]}... exists={user_exists}", "ANALYTICS")
                    
                    if not user_exists:
                        # 신규 사용자
                        redis_client.hset(user_key, 'first_visit', first_visit or now_kst.isoformat())
                        redis_client.hset(user_key, 'first_date', today)
                        redis_client.expire(user_key, 7776000)  # 90일
                        
                        # 오늘 신규 사용자 카운트
                        redis_client.sadd(f'analytics:new_users:{today}', user_id)
                        redis_client.expire(f'analytics:new_users:{today}', 2592000)
                        
                        log(f"✨ 신규 사용자 저장 완료: {user_id[:15]}... → {user_key[:60]}...", "ANALYTICS")
                    else:
                        # 재방문 사용자
                        stored_data = redis_client.hgetall(user_key)
                        log(f"🔄 재방문 사용자: {user_id[:15]}... (첫방문: {stored_data.get('first_date', 'N/A')})", "ANALYTICS")
                
                # ✨ 세션 시간 기록 (모든 이벤트, page_view 제외)
                # page_view는 로드 직후라 부정확하므로 실제 행동(댓글 복사, 블로그 이동)만 기록
                session_duration = data.get('sessionDuration', 0) if data else 0
                if session_duration > 0 and action != 'page_view':
                    redis_client.lpush(f'analytics:sessions:{today}', session_duration)
                    redis_client.ltrim(f'analytics:sessions:{today}', 0, 9999)  # 최대 10000개
                    redis_client.expire(f'analytics:sessions:{today}', 2592000)
                    log(f"✅ 세션 시간 저장: {session_duration}초 ({action})", "ANALYTICS")
                
                # 6. 브라우저/디바이스/OS 통계 (page_view 이벤트에서만)
                if action == 'page_view' and data:
                    if 'browser' in data:
                        redis_client.incr(f"analytics:browser:{data['browser']}")
                    if 'deviceType' in data:
                        redis_client.incr(f"analytics:device:{data['deviceType']}")
                    if 'os' in data:
                        redis_client.incr(f"analytics:os:{data['os']}")
                
                # 7. 피드백 통계 (rating별 카운트)
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
app.secret_key = os.getenv('SECRET_KEY', 'repost-secret-key-2025-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
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

# ============================
# 💾 캐싱 시스템 (프로덕션급)
# ============================

import hashlib

def normalize_blog_url(url):
    """
    블로그 URL 정규화 (모바일/데스크톱 URL 통일)
    
    Args:
        url: 블로그 URL
    
    Returns:
        str: 정규화된 URL
    """
    try:
        from urllib.parse import urlparse, parse_qs
        
        parsed = urlparse(url)
        
        # 네이버 블로그 URL 처리
        if 'blog.naver.com' in url or 'm.blog.naver.com' in url:
            # 쿼리 파라미터에서 blogId, logNo 추출
            query_params = parse_qs(parsed.query)
            
            if 'blogId' in query_params and 'logNo' in query_params:
                blog_id = query_params['blogId'][0]
                log_no = query_params['logNo'][0]
            else:
                # 경로에서 추출
                path_parts = parsed.path.strip('/').split('/')
                if len(path_parts) >= 2:
                    blog_id = path_parts[0]
                    log_no = path_parts[-1]
                else:
                    return url  # 변환 실패 시 원본 반환
            
            # 정규화된 URL 생성 (항상 동일한 형식)
            return f"blog.naver.com/{blog_id}/{log_no}"
        
        # 다른 블로그 플랫폼은 도메인 + 경로
        return f"{parsed.netloc}{parsed.path}"
    
    except:
        return url  # 에러 시 원본 반환

def generate_cache_key(url):
    """
    캐시 키 생성 (URL 해시)
    
    Args:
        url: 정규화된 URL
    
    Returns:
        str: 캐시 키
    """
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return f"cache:blog:{url_hash}"

def get_cached_comments(url):
    """
    캐시에서 댓글 조회
    
    Args:
        url: 블로그 URL
    
    Returns:
        dict or None: 캐시된 데이터 (blog + comments) 또는 None
    """
    if not redis_client:
        return None
    
    try:
        normalized_url = normalize_blog_url(url)
        cache_key = generate_cache_key(normalized_url)
        
        # Redis에서 조회
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            import json
            log(f"✅ 캐시 HIT: {normalized_url[:50]}...", "CACHE")
            
            # 캐시 히트 통계 증가
            redis_client.incr('analytics:cache:hits')
            redis_client.incr(f'analytics:cache:hits:{get_kst_now().strftime("%Y-%m-%d")}')
            
            return json.loads(cached_data)
        else:
            log(f"❌ 캐시 MISS: {normalized_url[:50]}...", "CACHE")
            
            # 캐시 미스 통계 증가
            redis_client.incr('analytics:cache:misses')
            redis_client.incr(f'analytics:cache:misses:{get_kst_now().strftime("%Y-%m-%d")}')
            
            return None
    
    except Exception as e:
        log(f"⚠️ 캐시 조회 실패: {e}", "WARNING")
        return None

def set_cached_comments(url, blog_data, comments, ttl=86400):
    """
    댓글을 캐시에 저장
    
    Args:
        url: 블로그 URL
        blog_data: 블로그 데이터
        comments: 댓글 리스트
        ttl: TTL (초, 기본 24시간)
    
    Returns:
        bool: 저장 성공 여부
    """
    if not redis_client:
        return False
    
    try:
        normalized_url = normalize_blog_url(url)
        cache_key = generate_cache_key(normalized_url)
        
        import json
        cache_data = {
            'blog': blog_data,
            'comments': comments,
            'cached_at': get_kst_now().isoformat()
        }
        
        # Redis에 저장 (24시간 TTL)
        redis_client.setex(
            cache_key,
            ttl,
            json.dumps(cache_data, ensure_ascii=False)
        )
        
        log(f"💾 캐시 저장 완료: {normalized_url[:50]}... (TTL: {ttl}초)", "CACHE")
        
        # 캐시 저장 통계 증가
        redis_client.incr('analytics:cache:stores')
        
        return True
    
    except Exception as e:
        log(f"⚠️ 캐시 저장 실패: {e}", "WARNING")
        return False

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

def generate_comments_with_ai(title, content, is_admin=False):
    """OpenAI를 사용하여 블로그 내용 기반 댓글 생성 (프로덕션 레벨)"""
    log("=" * 60)
    log("🤖 AI 댓글 생성 함수 시작", "AI")
    log("=" * 60)
    
    try:
        if not client:
            log("❌ OpenAI 클라이언트가 초기화되지 않음 → 템플릿 사용", "WARNING")
            return None
        
        log("✅ OpenAI 클라이언트 확인 완료", "AI")
        
        # 🔑 블로그 내용 요약 및 정제 (마스터 계정은 1000자)
        max_length = 1000 if is_admin else 500
        content_preview = content[:max_length] if len(content) > max_length else content
        content_preview = content_preview.strip()
        
        if not content_preview:
            log("❌ 블로그 내용이 비어있음 → 템플릿 사용", "WARNING")
            return None
        
        log(f"📝 블로그 제목: {title[:50]}...", "AI")
        log(f"📝 내용 길이: {len(content)}자 (미리보기: {len(content_preview)}자)", "AI")
        log(f"🔑 마스터 계정: {is_admin} (분석 길이: {max_length}자)", "AI")
        
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

def generate_comments(blog_data, is_admin=False):
    """블로그 내용을 기반으로 댓글 추천 생성 (AI 우선, 부족하면 템플릿 보충)"""
    title = blog_data['title']
    content = blog_data['content']
    
    log("━" * 60)
    log(f"📋 댓글 생성 프로세스 시작", "COMMENT")
    log(f"   블로그 제목: {title[:50]}...", "COMMENT")
    log(f"   🔑 마스터 계정: {is_admin}", "COMMENT")
    log("━" * 60)
    
    # AI 댓글 생성 시도 (마스터 계정 여부 전달)
    ai_comments = generate_comments_with_ai(title, content, is_admin)
    
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

@app.route('/test')
def test_usage():
    """사용 횟수 테스트 페이지"""
    with open('test_usage.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/favicon.ico')
def favicon():
    """파비콘 제공"""
    return app.send_static_file('images/favicon.svg')

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
    """블로그 분석 및 댓글 추천 API (💾 캐싱 적용)"""
    try:
        data = request.json
        blog_url = data.get('url', '').strip()
        force_refresh = data.get('force_refresh', False)  # 강제 재생성 옵션
        is_admin = data.get('isAdmin', False)  # 🔑 마스터 계정 여부
        
        if not blog_url:
            return jsonify({'error': 'URL을 입력해주세요.'}), 400
        
        log("═" * 60)
        log("🚀 새로운 블로그 분석 요청 시작", "API")
        log(f"   URL: {blog_url}", "API")
        log(f"   강제 재생성: {force_refresh}", "API")
        log(f"   🔑 마스터 계정: {is_admin}", "API")
        log("═" * 60)
        
        # 💾 1단계: 캐시 조회 (강제 재생성이 아닌 경우)
        if not force_refresh:
            cached_result = get_cached_comments(blog_url)
            if cached_result:
                log("⚡ 캐시된 데이터 반환 (즉시 응답!)", "CACHE")
                
                # 📊 Analytics 로깅 (캐시 히트)
                log_analytics(
                    action='blog_analyzed',
                    data={
                        'blog_url': blog_url,
                        'title': cached_result['blog'].get('title', '')[:100],
                        'comments_count': len(cached_result['comments']),
                        'from_cache': True
                    },
                    success=True
                )
                
                return jsonify({
                    'success': True,
                    'blog': cached_result['blog'],
                    'comments': cached_result['comments'],
                    'from_cache': True,
                    'cached_at': cached_result.get('cached_at')
                })
        
        # 💾 2단계: 캐시 미스 → 새로 생성
        log("🔨 새로운 댓글 생성 시작...", "API")
        
        # 블로그 내용 스크래핑
        log("📡 블로그 스크래핑 시작...", "SCRAPE")
        blog_data = scrape_blog_content(blog_url)
        log(f"✅ 스크래핑 완료: {blog_data['title'][:50]}...", "SCRAPE")
        
        # 댓글 생성 (마스터 계정 여부 전달)
        comments = generate_comments(blog_data, is_admin)
        
        # 💾 3단계: 캐시에 저장 (24시간)
        cache_saved = set_cached_comments(blog_url, blog_data, comments, ttl=86400)
        
        log("═" * 60, "API")
        log(f"🎉 전체 분석 완료! 댓글 {len(comments)}개 생성", "API")
        log(f"💾 캐시 저장: {'성공' if cache_saved else '실패'}", "API")
        log("═" * 60, "API")
        
        # 📊 Analytics 로깅 (성공)
        log_analytics(
            action='blog_analyzed',
            data={
                'blog_url': blog_url,
                'title': blog_data.get('title', '')[:100],
                'comments_count': len(comments),
                'from_cache': False
            },
            success=True
        )
        
        return jsonify({
            'success': True,
            'blog': blog_data,
            'comments': comments,
            'from_cache': False
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
    ⚡ 최적화된 통계 조회 (Redis Pipeline 사용 - 10배 이상 빠름!)
    
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
        'daily_blog_visits': {},
        # ✨ NEW: DAU/WAU/MAU/신규/재방문/세션
        'dau': 0,
        'wau': 0,
        'mau': 0,
        'today_new_users': 0,
        'new_user_rate': 0,
        'retention_rate': 0,
        'avg_session_time': 0,
        'completion_rate': 0
    }
    
    if not redis_client:
        log("⚠️ KV 비활성화 - 빈 통계 반환", "WARNING")
        return stats
    
    try:
        today = get_kst_now()
        today_str = today.strftime('%Y-%m-%d')
        yesterday_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # ⚡ Redis Pipeline: 모든 키를 한 번에 가져오기
        pipe = redis_client.pipeline()
        keys_map = {}
        
        # 기본 통계 키
        keys_to_get = [
            ('total_analyses', 'analytics:total:blog_analyzed'),
            ('success_analyses', 'analytics:success:blog_analyzed'),
            ('failed_analyses', 'analytics:failed:blog_analyzed'),
            ('today_analyses', f'analytics:daily:{today_str}:blog_analyzed'),
            ('yesterday_analyses', f'analytics:daily:{yesterday_str}:blog_analyzed'),
            ('total_page_views', 'analytics:total:page_view'),
            ('today_page_views', f'analytics:daily:{today_str}:page_view'),
            ('total_comment_copies', 'analytics:total:comment_copied'),
            ('today_comment_copies', f'analytics:daily:{today_str}:comment_copied'),
            ('total_blog_visits', 'analytics:total:blog_visit'),
            ('today_blog_visits', f'analytics:daily:{today_str}:blog_visit'),
        ]
        
        # 시간대별 (24시간)
        for hour in range(24):
            hour_str = f"{hour:02d}"
            keys_to_get.append((f'hourly_{hour_str}', f'analytics:hourly:{today_str}:{hour_str}'))
        
        # 일별 통계 (30일)
        for i in range(days):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            keys_to_get.append((f'daily_analyzed_{date}', f'analytics:daily:{date}:blog_analyzed'))
            keys_to_get.append((f'daily_pageview_{date}', f'analytics:daily:{date}:page_view'))
            keys_to_get.append((f'daily_copies_{date}', f'analytics:daily:{date}:comment_copied'))
            keys_to_get.append((f'daily_visits_{date}', f'analytics:daily:{date}:blog_visit'))
        
        # 브라우저 분포
        for browser in ['Chrome', 'Safari', 'Edge', 'Firefox', 'Other']:
            keys_to_get.append((f'browser_{browser}', f'analytics:browser:{browser}'))
        
        # 디바이스 분포
        for device in ['Desktop', 'Mobile', 'Tablet']:
            keys_to_get.append((f'device_{device}', f'analytics:device:{device}'))
        
        # OS 분포
        for os in ['Windows', 'macOS', 'iOS', 'Android', 'Linux', 'Other']:
            keys_to_get.append((f'os_{os}', f'analytics:os:{os}'))
        
        # 피드백 분포
        for rating in [5, 4, 3, 2]:
            keys_to_get.append((f'feedback_{rating}', f'analytics:feedback:rating_{rating}'))
        
        # 💾 캐시 통계
        keys_to_get.append(('cache_hits', 'analytics:cache:hits'))
        keys_to_get.append(('cache_misses', 'analytics:cache:misses'))
        keys_to_get.append(('cache_stores', 'analytics:cache:stores'))
        keys_to_get.append(('today_cache_hits', f'analytics:cache:hits:{today_str}'))
        keys_to_get.append(('today_cache_misses', f'analytics:cache:misses:{today_str}'))
        
        # 👥 추천 통계
        keys_to_get.append(('total_referrals', 'analytics:total_referrals'))
        keys_to_get.append(('total_bonus_claims', 'analytics:total_bonus_claims'))
        
        # Pipeline에 모든 get 추가
        for key_name, redis_key in keys_to_get:
            pipe.get(redis_key)
            keys_map[key_name] = len(keys_map)
        
        # ⚡ 한 번에 실행!
        results = pipe.execute()
        
        # 결과 파싱
        def get_val(key_name):
            idx = keys_map.get(key_name)
            if idx is not None and results[idx]:
                try:
                    return int(results[idx])
                except:
                    return 0
            return 0
        
        # 기본 통계
        stats['total_analyses'] = get_val('total_analyses')
        stats['success_analyses'] = get_val('success_analyses')
        stats['failed_analyses'] = get_val('failed_analyses')
        stats['today_analyses'] = get_val('today_analyses')
        stats['yesterday_analyses'] = get_val('yesterday_analyses')
        stats['total_page_views'] = get_val('total_page_views')
        stats['today_page_views'] = get_val('today_page_views')
        stats['total_comment_copies'] = get_val('total_comment_copies')
        stats['today_comment_copies'] = get_val('today_comment_copies')
        stats['total_blog_visits'] = get_val('total_blog_visits')
        stats['today_blog_visits'] = get_val('today_blog_visits')
        
        # 시간대별 통계
        for hour in range(24):
            hour_str = f"{hour:02d}"
            count = get_val(f'hourly_{hour_str}')
            if count > 0:
                stats['hourly_stats'][hour_str] = count
        
        # 일별 통계
        for i in range(days):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            
            analyzed = get_val(f'daily_analyzed_{date}')
            stats['daily_stats'][date] = analyzed
            
            if i < 7:
                stats['week_analyses'] += analyzed
                stats['week_page_views'] += get_val(f'daily_pageview_{date}')
                stats['week_comment_copies'] += get_val(f'daily_copies_{date}')
                stats['week_blog_visits'] += get_val(f'daily_visits_{date}')
            
            stats['month_analyses'] += analyzed
            stats['daily_page_views'][date] = get_val(f'daily_pageview_{date}')
            stats['daily_comment_copies'][date] = get_val(f'daily_copies_{date}')
            stats['daily_blog_visits'][date] = get_val(f'daily_visits_{date}')
        
        # 브라우저 분포
        stats['browser_stats'] = {}
        for browser in ['Chrome', 'Safari', 'Edge', 'Firefox', 'Other']:
            count = get_val(f'browser_{browser}')
            if count > 0:
                stats['browser_stats'][browser] = count
        
        # 디바이스 분포
        stats['device_stats'] = {}
        for device in ['Desktop', 'Mobile', 'Tablet']:
            count = get_val(f'device_{device}')
            if count > 0:
                stats['device_stats'][device] = count
        
        # OS 분포
        stats['os_stats'] = {}
        for os in ['Windows', 'macOS', 'iOS', 'Android', 'Linux', 'Other']:
            count = get_val(f'os_{os}')
            if count > 0:
                stats['os_stats'][os] = count
        
        # 피드백 통계
        stats['feedback_stats'] = {}
        stats['total_feedbacks'] = 0
        for rating in [5, 4, 3, 2]:
            count = get_val(f'feedback_{rating}')
            if count > 0:
                stats['feedback_stats'][rating] = count
                stats['total_feedbacks'] += count
        
        # 평균 만족도 계산
        if stats['total_feedbacks'] > 0:
            weighted_sum = sum(rating * count for rating, count in stats['feedback_stats'].items())
            stats['avg_rating'] = round(weighted_sum / stats['total_feedbacks'], 2)
        else:
            stats['avg_rating'] = 0
        
        # 💾 캐시 통계
        stats['cache_hits'] = get_val('cache_hits')
        stats['cache_misses'] = get_val('cache_misses')
        stats['cache_stores'] = get_val('cache_stores')
        stats['today_cache_hits'] = get_val('today_cache_hits')
        stats['today_cache_misses'] = get_val('today_cache_misses')
        
        # 캐시 히트율 계산
        total_cache_requests = stats['cache_hits'] + stats['cache_misses']
        if total_cache_requests > 0:
            stats['cache_hit_rate'] = round((stats['cache_hits'] / total_cache_requests) * 100, 1)
        else:
            stats['cache_hit_rate'] = 0
        
        # 오늘 캐시 히트율
        today_cache_requests = stats['today_cache_hits'] + stats['today_cache_misses']
        if today_cache_requests > 0:
            stats['today_cache_hit_rate'] = round((stats['today_cache_hits'] / today_cache_requests) * 100, 1)
        else:
            stats['today_cache_hit_rate'] = 0
        
        # 👥 추천 통계
        stats['total_referrals'] = get_val('total_referrals')  # 총 추천 건수
        stats['total_bonus_claims'] = get_val('total_bonus_claims')  # 총 보너스 지급 횟수
        
        # 추천한 유저 수 (SET 크기 조회)
        try:
            stats['total_referrers'] = redis_client.scard('analytics:referrers') or 0
        except:
            stats['total_referrers'] = 0
        
        # 전환율 계산
        stats['conversion_funnel']['visits'] = stats['total_page_views']
        stats['conversion_funnel']['analyses'] = stats['success_analyses']
        stats['conversion_funnel']['copies'] = stats['total_comment_copies']
        stats['conversion_funnel']['visits_to_blog'] = stats['total_blog_visits']
        
        # 성공률 계산
        if stats['total_analyses'] > 0:
            stats['success_rate'] = round((stats['success_analyses'] / stats['total_analyses']) * 100, 1)
        
        # ✨ NEW: DAU/WAU/MAU 조회 (⚡ 초고속 최적화!)
        try:
            # ⚡ Pipeline으로 모든 작업 한 번에!
            pipe_dau = redis_client.pipeline()
            
            # 1. DAU (오늘 고유 사용자)
            pipe_dau.scard(f'analytics:dau:{today_str}')
            
            # 2. WAU (최근 7일 고유 사용자) - SUNIONSTORE 사용!
            wau_keys = [f'analytics:wau:{(today - timedelta(days=i)).strftime("%Y-%m-%d")}' for i in range(7)]
            if wau_keys:
                pipe_dau.sunionstore('analytics:wau:temp', *wau_keys)  # 임시 SET 생성
                pipe_dau.scard('analytics:wau:temp')  # 크기만 조회 (초고속!)
                pipe_dau.expire('analytics:wau:temp', 3600)  # 1시간 후 자동 삭제
            
            # 3. MAU (최근 30일 고유 사용자) - SUNIONSTORE 사용!
            mau_keys = [f'analytics:mau:{(today - timedelta(days=i)).strftime("%Y-%m-%d")}' for i in range(30)]
            if mau_keys:
                pipe_dau.sunionstore('analytics:mau:temp', *mau_keys)  # 임시 SET 생성
                pipe_dau.scard('analytics:mau:temp')  # 크기만 조회 (초고속!)
                pipe_dau.expire('analytics:mau:temp', 3600)  # 1시간 후 자동 삭제
            
            # 4. 오늘 신규 사용자
            pipe_dau.scard(f'analytics:new_users:{today_str}')
            
            # 5. 세션 시간 리스트
            pipe_dau.lrange(f'analytics:sessions:{today_str}', 0, -1)
            
            # ⚡ 한 번에 실행!
            dau_results = pipe_dau.execute()
            
            # 결과 파싱
            idx = 0
            stats['dau'] = dau_results[idx] or 0
            idx += 1
            
            if wau_keys:
                idx += 1  # sunionstore 결과 스킵
                stats['wau'] = dau_results[idx] or 0
                idx += 2  # scard, expire 스킵
            
            if mau_keys:
                idx += 1  # sunionstore 결과 스킵
                stats['mau'] = dau_results[idx] or 0
                idx += 2  # scard, expire 스킵
            
            stats['today_new_users'] = dau_results[idx] or 0
            idx += 1
            
            # 세션 시간 계산
            session_times = dau_results[idx] or []
            if session_times:
                total_time = sum(int(t) for t in session_times)
                stats['avg_session_time'] = round(total_time / len(session_times), 0)
                log(f"📊 세션 시간 통계: {len(session_times)}개 기록, 총 {total_time}초, 평균 {stats['avg_session_time']}초", "ANALYTICS")
            else:
                log(f"⚠️ 세션 시간 데이터 없음 (오늘: {today_str})", "WARNING")
            
            # 계산형 지표
            if stats['dau'] > 0:
                stats['new_user_rate'] = round((stats['today_new_users'] / stats['dau']) * 100, 1)
                returning_users = stats['dau'] - stats['today_new_users']
                stats['retention_rate'] = round((returning_users / stats['dau']) * 100, 1)
                log(f"👥 DAU: {stats['dau']}명, 신규: {stats['today_new_users']}명, 재방문: {returning_users}명 ({stats['retention_rate']}%)", "ANALYTICS")
            
            if stats['total_page_views'] > 0:
                stats['completion_rate'] = round((stats['total_blog_visits'] / stats['total_page_views']) * 100, 1)
            
            # 👥 추천 참여율 계산 (추천한 유저 / 전체 유저)
            if stats['mau'] > 0:
                stats['referral_participation_rate'] = round((stats['total_referrers'] / stats['mau']) * 100, 1)
            else:
                stats['referral_participation_rate'] = 0
            
            log(f"⚡ DAU: {stats['dau']}, WAU: {stats['wau']}, MAU: {stats['mau']} (초고속 조회!)", "ANALYTICS")
            log(f"✨ 신규: {stats['today_new_users']}, 재방문율: {stats['retention_rate']}%", "ANALYTICS")
            
        except Exception as dau_error:
            log(f"⚠️ DAU/WAU/MAU 조회 실패: {dau_error}", "WARNING")
        
        # 플랫폼 (네이버만 사용 중)
        stats['top_blog_domains']['네이버 블로그'] = stats['total_analyses']
        
        log(f"⚡ KV 통계 조회 완료 (Pipeline): 총 {stats['total_analyses']}건, DAU {stats['dau']}명", "ANALYTICS")
        
    except Exception as e:
        log(f"⚠️ KV 통계 조회 실패: {e}", "ERROR")
    
    return stats

@app.route('/api/track', methods=['POST'])
def track_event():
    """사용자 이벤트 트래킹 API - DAU/WAU/MAU 추적 포함"""
    try:
        data = request.json
        event_type = data.get('event')  # 'page_view', 'comment_copied', 'blog_visit'
        
        log(f"📨 /api/track 수신: event={event_type}, userId={data.get('userId', 'None')[:20] if data.get('userId') else 'None'}...", "API")
        
        if not event_type:
            return jsonify({'error': 'event type required'}), 400
        
        # 이벤트별 로깅
        if event_type == 'page_view':
            # 브라우저/디바이스 + userId/firstVisit/sessionDuration 정보 포함
            device_data = {
                'browser': data.get('browser', 'Other'),
                'deviceType': data.get('deviceType', 'Desktop'),
                'os': data.get('os', 'Other'),
                'userId': data.get('userId'),
                'firstVisit': data.get('firstVisit'),
                'sessionDuration': data.get('sessionDuration', 0)
            }
            log(f"📊 page_view 데이터: userId={device_data.get('userId', 'None')[:30] if device_data.get('userId') else 'None'}..., firstVisit={device_data.get('firstVisit', 'None')[:30] if device_data.get('firstVisit') else 'None'}...", "API")
            log_analytics('page_view', data=device_data, success=True)
        elif event_type == 'comment_copied':
            comment_data = {
                'comment': data.get('comment', '')[:50],
                'sessionDuration': data.get('sessionDuration', 0)
            }
            log_analytics('comment_copied', data=comment_data, success=True)
        elif event_type == 'blog_visit':
            visit_data = {
                'url': data.get('url', '')[:100],
                'sessionDuration': data.get('sessionDuration', 0)
            }
            log_analytics('blog_visit', data=visit_data, success=True)
        elif event_type == 'quick_feedback':
            feedback_data = {
                'rating': data.get('rating', 0),
                'sessionDuration': data.get('sessionDuration', 0)
            }
            log_analytics('quick_feedback', data=feedback_data, success=True)
        
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
# 🎁 보너스 시스템 API
# ============================

@app.route('/api/referral/track', methods=['POST'])
def track_referral():
    """친구 추천 추적"""
    try:
        data = request.get_json()
        referrer_id = data.get('referrerId')  # 추천한 사람
        new_user_id = data.get('newUserId')   # 신규 유저
        
        if not referrer_id or not new_user_id:
            return jsonify({'success': False, 'error': 'Missing parameters'}), 400
        
        # 🚫 자기 자신의 링크는 무시
        if referrer_id == new_user_id:
            log(f"⚠️ 자기 자신의 추천 링크 무시: {referrer_id}", "REFERRAL")
            return jsonify({'success': True})  # 에러 없이 무시
        
        # Redis 연결 확인
        if not redis_client:
            log(f"⚠️ Redis 연결 없음 - 추천 기록 불가", "WARNING")
            return jsonify({'success': True})  # 실패해도 사용자에게는 성공 반환
        
        # Redis에 기록
        key = f'referral:{referrer_id}:{new_user_id}'
        redis_client.set(key, json.dumps({
            'referrer_id': referrer_id,
            'new_user_id': new_user_id,
            'timestamp': datetime.now(KST).isoformat(),
            'bonus_given': False
        }), ex=30*24*60*60)  # 30일 보관
        
        # 📊 Analytics: 추천 통계 기록
        redis_client.incr('analytics:total_referrals')  # 총 추천 건수
        redis_client.sadd('analytics:referrers', referrer_id)  # 추천한 유저 집합
        
        log(f"📋 친구 추천 기록: {referrer_id} → {new_user_id}", "REFERRAL")
        
        return jsonify({'success': True})
    
    except Exception as e:
        log(f"⚠️ 친구 추천 추적 실패: {e}", "ERROR")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/referral/claim', methods=['POST'])
def claim_referral_bonus():
    """친구 추천 보너스 지급 (7일 롤링 5회 제한)"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        log(f"📥 보너스 요청 받음: userId={user_id}", "BONUS")
        
        if not user_id:
            log(f"⚠️ userId 없음", "ERROR")
            return jsonify({'success': False, 'error': 'missing_user'}), 400
        
        # Redis 연결 확인
        if not redis_client:
            log(f"⚠️ Redis 연결 없음 - 보너스 지급 불가", "ERROR")
            return jsonify({'success': False, 'error': 'server_not_ready'}), 500
        
        now = datetime.now(KST)
        
        # 1. 리셋 시점 확인 (5회 소진 후 7일)
        reset_key = f'referral:reset:{user_id}'
        reset_time_str = redis_client.get(reset_key)
        
        if reset_time_str:
            reset_time = datetime.fromisoformat(reset_time_str)
            if now < reset_time:
                # 아직 리셋 시점이 안 됨 (7일 미경과)
                days_left = (reset_time - now).days
                hours_left = ((reset_time - now).seconds // 3600)
                
                log(f"⏰ 리셋 대기 중: {user_id} (남은 시간: {days_left}일 {hours_left}시간)", "BONUS")
                return jsonify({
                    'success': False,
                    'error': 'reset_pending',
                    'reset_time': reset_time.isoformat(),
                    'days_left': days_left,
                    'hours_left': hours_left
                }), 400
            else:
                # 리셋 시점 도달 → 초기화
                log(f"🔄 7일 경과 → 클레임 횟수 초기화: {user_id}", "BONUS")
                redis_client.delete(reset_key)
                redis_client.delete(f'referral:claims:{user_id}')
        
        # 2. 현재 클레임 횟수 확인
        claims_key = f'referral:claims:{user_id}'
        current_claims = int(redis_client.get(claims_key) or 0)
        
        log(f"📊 현재 클레임 횟수: {current_claims}/5", "BONUS")
        
        # 3. 한도 체크 (5회)
        if current_claims >= 5:
            log(f"⚠️ 한도 초과: {user_id} (5/5)", "BONUS")
            # 리셋 시점을 다시 확인해서 반환
            reset_time_str = redis_client.get(reset_key)
            if reset_time_str:
                reset_time = datetime.fromisoformat(reset_time_str)
                days_left = (reset_time - now).days
                hours_left = ((reset_time - now).seconds // 3600)
                return jsonify({
                    'success': False,
                    'error': 'limit_reached',
                    'current_claims': current_claims,
                    'max_claims': 5,
                    'reset_time': reset_time.isoformat(),
                    'days_left': days_left,
                    'hours_left': hours_left
                }), 400
        
        # 4. 실제 추천 기록 확인 (너그러운 정책)
        has_referral = False
        
        try:
            referred_by_key = f'referred_by:{user_id}'
            referred_by = redis_client.get(referred_by_key)
            
            if referred_by:
                has_referral = True
                log(f"✅ 추천 기록 확인: {user_id}", "BONUS")
            else:
                # 너그러운 정책으로 일단 지급
                log(f"⚠️ 추천 기록 없음, 하지만 지급: {user_id}", "BONUS")
                has_referral = True
        except Exception as e:
            log(f"⚠️ 추천 기록 확인 중 오류 (무시): {e}", "WARNING")
            has_referral = True  # 에러 시에도 너그럽게 지급
        
        if not has_referral:
            log(f"❌ 추천 기록 없음: {user_id}", "BONUS")
            return jsonify({
                'success': False,
                'error': 'no_referral'
            }), 400
        
        # 5. 클레임 횟수 증가
        new_claims = current_claims + 1
        redis_client.set(claims_key, str(new_claims), ex=30*24*60*60)  # 30일 보관
        
        # 📊 Analytics: 보너스 지급 통계 기록
        redis_client.incr('analytics:total_bonus_claims')  # 총 보너스 지급 횟수
        
        # 6. 5회 소진 시 리셋 시점 기록 (현재 시각 + 7일)
        if new_claims >= 5:
            reset_time = now + timedelta(days=7)
            redis_client.set(reset_key, reset_time.isoformat(), ex=8*24*60*60)  # 8일 보관 (여유)
            log(f"🔒 5회 소진 완료 → 7일 후 초기화: {reset_time.strftime('%Y-%m-%d %H:%M')}", "BONUS")
        
        log(f"🎁 친구 추천 보너스 지급 성공: {user_id} (+5회) [{new_claims}/5]", "BONUS")
        
        return jsonify({
            'success': True,
            'bonus': 5,
            'current_claims': new_claims,
            'max_claims': 5,
            'remaining_claims': 5 - new_claims,
            'reset_in_7_days': new_claims >= 5
        }), 200
    
    except Exception as e:
        log(f"❌ 친구 추천 보너스 지급 실패: {e}", "ERROR")
        import traceback
        log(f"📋 상세 에러: {traceback.format_exc()}", "ERROR")
        return jsonify({
            'success': False, 
            'error': 'server_error',
            'message': str(e)
        }), 500

@app.route('/api/share/claim', methods=['POST'])
def claim_share_bonus():
    """SNS 공유 보너스 지급"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        log(f"📥 SNS 공유 보너스 요청: userId={user_id}", "BONUS")
        
        if not user_id:
            log(f"⚠️ userId 없음", "ERROR")
            return jsonify({'success': False, 'error': 'missing_user'}), 400
        
        # Redis 연결 확인
        if not redis_client:
            log(f"⚠️ Redis 연결 없음 - 보너스 지급 불가", "ERROR")
            return jsonify({'success': False, 'error': 'server_not_ready'}), 500
        
        # 쿨다운 체크 (7일)
        last_claim_key = f'share_claim:{user_id}'
        last_claim = redis_client.get(last_claim_key)
        
        if last_claim:
            last_claim_time = datetime.fromisoformat(last_claim)  # decode 제거 (이미 문자열)
            days_diff = (datetime.now(KST) - last_claim_time).days
            
            if days_diff < 7:
                log(f"⏰ 쿨다운: {user_id} (남은 일수: {7 - days_diff}일)", "BONUS")
                return jsonify({
                    'success': False,
                    'error': 'cooldown',
                    'days_left': 7 - days_diff
                }), 400
        
        # 보너스 지급 기록
        redis_client.set(last_claim_key, datetime.now(KST).isoformat(), ex=30*24*60*60)
        
        log(f"🎁 SNS 공유 보너스 지급 성공: {user_id} (+5회)", "BONUS")
        
        return jsonify({
            'success': True,
            'bonus': 5,
            'expiryDays': 30
        }), 200
    
    except Exception as e:
        log(f"❌ SNS 공유 보너스 지급 실패: {e}", "ERROR")
        import traceback
        log(f"📋 상세 에러: {traceback.format_exc()}", "ERROR")
        return jsonify({
            'success': False,
            'error': 'server_error',
            'message': str(e)
        }), 500

# ============================
# 🎨 블로거 도구 페이지
# ============================

@app.route('/tools')
def blogger_tools():
    """🎨 블로거 도구 메인 페이지"""
    return render_template('tools.html')

@app.route('/tools/text-analyzer')
def text_analyzer():
    """📊 텍스트 분석기 페이지"""
    return render_template('text-analyzer.html')

@app.route('/tools/title-generator')
def title_generator():
    """💡 제목 생성기 페이지"""
    return render_template('title-generator.html')

@app.route('/tools/seo-checker')
def seo_checker():
    """🎯 SEO 점수 체커 페이지"""
    return render_template('seo-checker.html')

@app.route('/tools/ai-writer')
def ai_writer():
    """✍️ AI 글쓰기 도우미 페이지"""
    return render_template('ai-writer.html')

@app.route('/tools/competitor-analyzer')
def competitor_analyzer():
    """🔍 경쟁 블로그 분석 페이지"""
    return render_template('competitor-analyzer.html')

@app.route('/tools/keyword-recommender')
def keyword_recommender():
    """🔑 키워드 추천 엔진 페이지"""
    return render_template('keyword-recommender.html')

# ============================
# 📊 블로거 도구 - 텍스트 분석
# ============================

@app.route('/api/analyze-text', methods=['POST'])
def analyze_text():
    """📊 실시간 텍스트 분석 API"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        title = data.get('title', '')
        
        if not text:
            return jsonify({'error': 'text is required'}), 400
        
        # 분석 결과 생성
        analysis = {
            'character_count': analyze_character_count(text, title),
            'keyword_density': analyze_keyword_density(text),
            'duplicate_expressions': analyze_duplicate_expressions(text),
            'readability': analyze_readability(text)
        }
        
        log(f"📊 텍스트 분석 완료: {len(text)}자", "ANALYSIS")
        
        return jsonify({
            'success': True,
            'analysis': analysis
        }), 200
    
    except Exception as e:
        log(f"❌ 텍스트 분석 실패: {e}", "ERROR")
        import traceback
        log(f"📋 상세 에러: {traceback.format_exc()}", "ERROR")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def analyze_character_count(text, title):
    """글자수 분석"""
    import re
    
    # 공백 포함/제외 글자수
    total_chars = len(text)
    chars_no_space = len(text.replace(' ', '').replace('\n', '').replace('\t', ''))
    title_chars = len(title)
    
    # 읽는 시간 계산 (한국어 기준: 분당 500자)
    reading_time_minutes = total_chars / 500
    reading_time_seconds = int((reading_time_minutes % 1) * 60)
    reading_time_minutes = int(reading_time_minutes)
    
    # 권장 범위 체크
    status = 'good'
    message = '적정한 길이입니다'
    if total_chars < 800:
        status = 'warning'
        message = f'{800 - total_chars}자 더 작성하는 것을 권장합니다'
    elif total_chars > 2000:
        status = 'info'
        message = '긴 글은 여러 문단으로 나누는 것을 권장합니다'
    
    return {
        'total': total_chars,
        'without_space': chars_no_space,
        'title': title_chars,
        'reading_time': f"{reading_time_minutes}분 {reading_time_seconds}초",
        'recommended_range': '800-2,000자',
        'status': status,
        'message': message
    }

def analyze_keyword_density(text):
    """키워드 밀도 분석"""
    import re
    from collections import Counter
    
    # 한글 단어 추출 (2글자 이상)
    words = re.findall(r'[가-힣]{2,}', text)
    
    if not words:
        return {'keywords': [], 'total_words': 0}
    
    # 불용어 제거
    stopwords = {'그리고', '하지만', '그러나', '그래서', '때문에', '그것', '이것', '저것', 
                 '있는', '없는', '되는', '하는', '같은', '있다', '없다', '이다', '아니다',
                 '수', '등', '및', '또는', '또한', '따라', '대한', '위해', '통해', '까지'}
    
    filtered_words = [word for word in words if word not in stopwords]
    
    # 빈도수 계산
    word_counts = Counter(filtered_words)
    total_words = len(filtered_words)
    
    # 상위 키워드 추출 (빈도 3회 이상)
    keywords = []
    for word, count in word_counts.most_common(20):
        if count >= 3:
            density = (count / total_words) * 100
            
            # 키워드 밀도 평가
            status = 'good'
            suggestion = ''
            if density > 1.5:
                status = 'warning'
                recommended_count = int(total_words * 0.01)
                suggestion = f'너무 많이 사용되었습니다. {recommended_count}-{recommended_count + 2}회로 줄이는 것을 권장합니다'
            elif density < 0.3:
                status = 'info'
                suggestion = '조금 더 사용해도 좋습니다'
            else:
                status = 'good'
                suggestion = '적정한 사용 빈도입니다'
            
            keywords.append({
                'word': word,
                'count': count,
                'density': round(density, 2),
                'status': status,
                'suggestion': suggestion
            })
    
    return {
        'keywords': keywords[:10],  # 상위 10개만
        'total_words': total_words
    }

def analyze_duplicate_expressions(text):
    """중복 표현 분석"""
    import re
    from collections import Counter
    
    duplicates = []
    
    # 1. 반복 단어 체크 (2글자 이상, 5회 이상 반복)
    words = re.findall(r'[가-힣]{2,}', text)
    word_counts = Counter(words)
    
    common_words = ['정말', '진짜', '너무', '아주', '매우', '완전', '엄청', '되게', 
                   '것', '같아요', '같은', '같다', '거예요', '거에요']
    
    for word in common_words:
        count = word_counts.get(word, 0)
        if count >= 5:
            alternatives = get_alternatives(word)
            duplicates.append({
                'type': 'word',
                'expression': word,
                'count': count,
                'suggestion': f'대체어: {", ".join(alternatives)}',
                'status': 'warning' if count >= 8 else 'info'
            })
    
    # 2. 문장 패턴 체크
    sentence_patterns = [
        (r'~\s*것\s*같아요?', '~것 같아요'),
        (r'~\s*거\s*같아요?', '~거 같아요'),
        (r'~\s*네요', '~네요'),
        (r'정말\s+', '정말 ')
    ]
    
    for pattern, display in sentence_patterns:
        matches = re.findall(pattern, text)
        count = len(matches)
        if count >= 4:
            duplicates.append({
                'type': 'pattern',
                'expression': display,
                'count': count,
                'suggestion': '다양한 표현으로 변경을 권장합니다',
                'status': 'warning' if count >= 6 else 'info'
            })
    
    return duplicates

def get_alternatives(word):
    """대체어 추천"""
    alternatives_map = {
        '정말': ['진짜', '굉장히', '아주', '매우', '무척', '상당히'],
        '진짜': ['정말', '굉장히', '아주', '매우', '무척'],
        '너무': ['아주', '매우', '굉장히', '정말', '상당히'],
        '아주': ['매우', '굉장히', '정말', '무척', '상당히'],
        '매우': ['아주', '굉장히', '정말', '무척', '상당히'],
        '완전': ['정말', '아주', '굉장히', '매우'],
        '엄청': ['굉장히', '정말', '아주', '매우'],
        '것': ['점', '부분', '면'],
        '같아요': ['생각해요', '느껴져요', '보여요', '인 것 같습니다'],
        '같은': ['비슷한', '유사한', '~와 같은'],
        '같다': ['비슷하다', '유사하다', '~와 같다']
    }
    return alternatives_map.get(word, ['다양한 표현 사용 권장'])

def analyze_readability(text):
    """가독성 분석"""
    import re
    
    # 문장 분리
    sentences = re.split(r'[.!?]\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return {
            'score': 0,
            'sentence_length': {'avg': 0, 'status': 'good'},
            'paragraph_length': {'avg': 0, 'status': 'good'},
            'line_breaks': {'count': 0, 'status': 'good'}
        }
    
    # 1. 문장 길이 분석
    sentence_lengths = [len(s) for s in sentences]
    avg_sentence_length = sum(sentence_lengths) / len(sentences)
    
    sentence_status = 'good'
    sentence_message = '적절한 문장 길이입니다'
    if avg_sentence_length > 60:
        sentence_status = 'warning'
        sentence_message = '문장이 길어서 읽기 어려울 수 있습니다. 짧게 나누는 것을 권장합니다'
    elif avg_sentence_length < 20:
        sentence_status = 'info'
        sentence_message = '문장이 짧습니다. 조금 더 자세한 설명을 추가해보세요'
    
    # 2. 단락 분석
    paragraphs = text.split('\n\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    paragraph_lengths = [len(p.split('\n')) for p in paragraphs]
    avg_paragraph_length = sum(paragraph_lengths) / len(paragraph_lengths) if paragraph_lengths else 0
    
    paragraph_status = 'good'
    paragraph_message = '적절한 단락 구성입니다'
    if avg_paragraph_length > 8:
        paragraph_status = 'warning'
        paragraph_message = '단락이 길어서 지루할 수 있습니다. 4-6줄로 나누는 것을 권장합니다'
    
    # 3. 줄바꿈 분석
    line_breaks = text.count('\n')
    line_break_status = 'good'
    line_break_message = '적절한 줄바꿈입니다'
    
    total_chars = len(text)
    if total_chars > 500 and line_breaks < 3:
        line_break_status = 'warning'
        line_break_message = '줄바꿈이 부족합니다. 가독성을 위해 더 추가하세요'
    
    # 4. 종합 점수 계산
    score = 100
    if sentence_status == 'warning':
        score -= 15
    elif sentence_status == 'info':
        score -= 5
    
    if paragraph_status == 'warning':
        score -= 15
    
    if line_break_status == 'warning':
        score -= 10
    
    return {
        'score': max(0, score),
        'sentence_length': {
            'avg': round(avg_sentence_length, 1),
            'status': sentence_status,
            'message': sentence_message
        },
        'paragraph_length': {
            'avg': round(avg_paragraph_length, 1),
            'status': paragraph_status,
            'message': paragraph_message
        },
        'line_breaks': {
            'count': line_breaks,
            'status': line_break_status,
            'message': line_break_message
        }
    }

# ============================
# 💡 블로거 도구 - 제목 생성
# ============================

@app.route('/api/generate-titles', methods=['POST'])
def generate_titles():
    """💡 AI 제목 생성 API"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        keywords = data.get('keywords', '')
        style = data.get('style', 'friendly')  # friendly, professional, sensational
        
        if not text and not keywords:
            return jsonify({'error': 'text or keywords required'}), 400
        
        # OpenAI로 제목 생성
        titles = generate_titles_with_ai(text, keywords, style)
        
        log(f"💡 제목 생성 완료: {len(titles)}개", "TITLE")
        
        return jsonify({
            'success': True,
            'titles': titles
        }), 200
    
    except Exception as e:
        log(f"❌ 제목 생성 실패: {e}", "ERROR")
        import traceback
        log(f"📋 상세 에러: {traceback.format_exc()}", "ERROR")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_titles_with_ai(text, keywords, style):
    """AI로 제목 생성"""
    try:
        # 스타일별 프롬프트
        style_prompts = {
            'friendly': '친근하고 편안한 말투로, 독자가 친구에게 추천받는 느낌의',
            'professional': '전문적이고 신뢰감 있는 톤으로',
            'sensational': '클릭을 유도하는 자극적이면서도 과하지 않은',
            'informative': '정보 전달에 집중한 명확하고 구체적인',
            'emotional': '감성적이고 공감을 이끌어내는'
        }
        
        style_desc = style_prompts.get(style, style_prompts['friendly'])
        
        # 텍스트에서 핵심 키워드 추출
        import re
        from collections import Counter
        
        content_keywords = []
        if text:
            words = re.findall(r'[가-힣]{2,}', text[:500])  # 앞 500자만
            word_counts = Counter(words)
            content_keywords = [word for word, count in word_counts.most_common(5) if count >= 2]
        
        if keywords:
            content_keywords.extend(keywords.split(','))
        
        content_keywords = list(set(content_keywords))[:7]  # 중복 제거, 최대 7개
        
        # AI 프롬프트
        prompt = f"""당신은 블로그 제목 전문가입니다. 아래 정보를 바탕으로 클릭율이 높은 블로그 제목 10개를 생성해주세요.

글 내용 미리보기:
{text[:300] if text else '없음'}

핵심 키워드: {', '.join(content_keywords)}

제목 스타일: {style_desc}

제목 작성 규칙:
1. 제목 길이: 20-50자
2. 숫자 활용 (TOP 5, BEST 10 등)
3. 혜택 명시 (가성비, 무료, 꿀팁 등)
4. 궁금증 유발
5. 구체적이고 명확하게
6. 이모지는 사용하지 말 것

각 제목에 대해:
- 제목
- 예상 클릭율 (7-15% 범위)
- 강점 (간단히 한줄)

JSON 형식으로 응답:
[
  {{
    "title": "제목",
    "ctr": 12.5,
    "strength": "강점 설명"
  }},
  ...
]
"""
        
        # OpenAI API 호출
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 블로그 제목 전문가입니다. 클릭율이 높은 제목을 생성합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1500
        )
        
        # 응답 파싱
        result_text = response.choices[0].message.content.strip()
        
        # JSON 추출 (마크다운 코드 블록 제거)
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()
        
        titles_data = json.loads(result_text)
        
        # 제목 평가 추가
        for title_obj in titles_data:
            title_obj['evaluation'] = evaluate_title(title_obj['title'])
        
        return titles_data
    
    except Exception as e:
        log(f"❌ AI 제목 생성 실패: {e}", "ERROR")
        # 폴백: 간단한 제목 생성
        return generate_fallback_titles(keywords or text[:50])

def evaluate_title(title):
    """제목 평가"""
    score = 50  # 기본 점수
    feedback = []
    
    title_length = len(title)
    
    # 1. 길이 체크
    if 20 <= title_length <= 50:
        score += 20
        feedback.append('✅ 적절한 길이')
    elif title_length < 20:
        score -= 10
        feedback.append('⚠️ 너무 짧음 (20자 이상 권장)')
    else:
        score -= 15
        feedback.append('⚠️ 너무 김 (50자 이하 권장)')
    
    # 2. 숫자 포함 체크
    import re
    if re.search(r'\d+|TOP|BEST|순위', title):
        score += 15
        feedback.append('✅ 숫자/리스트 포함 (클릭율 +23%)')
    else:
        feedback.append('💡 숫자 추가 권장 (TOP 5, BEST 10)')
    
    # 3. 혜택/가치 명시
    benefit_keywords = ['가성비', '무료', '꿀팁', '추천', '완벽', '최고', '인기', '핫플', '데이트', '예약']
    if any(keyword in title for keyword in benefit_keywords):
        score += 10
        feedback.append('✅ 혜택 명시')
    else:
        feedback.append('💡 혜택 키워드 추가 고려')
    
    # 4. 궁금증 유발
    question_patterns = ['?', '방법', '비법', '노하우', '총정리', '완벽', '알아보기']
    if any(pattern in title for pattern in question_patterns):
        score += 10
        feedback.append('✅ 궁금증 유발')
    
    # 5. 구체성
    if '|' in title or ':' in title:
        score += 5
        feedback.append('✅ 구체적 정보 제공')
    
    score = min(100, max(0, score))
    
    return {
        'score': score,
        'feedback': feedback
    }

def generate_fallback_titles(base_text):
    """폴백 제목 생성 (AI 실패시)"""
    import re
    words = re.findall(r'[가-힣]+', base_text)
    main_keyword = words[0] if words else '블로그'
    
    templates = [
        f"{main_keyword} 완벽 가이드 | 초보자도 쉽게!",
        f"{main_keyword} TOP 5 추천 (2025년 최신)",
        f"{main_keyword} 총정리 | 이것만 보면 끝",
        f"알아두면 좋은 {main_keyword} 꿀팁 BEST 7",
        f"{main_keyword} 완전 정복 | 실전 노하우",
        f"{main_keyword}의 모든 것 | 상세 리뷰",
        f"{main_keyword} 추천 | 검증된 후기",
        f"{main_keyword} 어떻게 선택할까? (비교 분석)",
        f"{main_keyword} 이렇게 하세요 | 단계별 가이드",
        f"{main_keyword} 시작하기 전 꼭 알아야 할 것들"
    ]
    
    return [
        {
            'title': title,
            'ctr': 8.0 + (i * 0.3),
            'strength': '템플릿 기반 제목',
            'evaluation': evaluate_title(title)
        }
        for i, title in enumerate(templates)
    ]

@app.route('/api/evaluate-title', methods=['POST'])
def evaluate_title_api():
    """💡 제목 평가 API"""
    try:
        data = request.get_json()
        title = data.get('title', '')
        
        if not title:
            return jsonify({'error': 'title is required'}), 400
        
        evaluation = evaluate_title(title)
        
        return jsonify({
            'success': True,
            'evaluation': evaluation
        }), 200
    
    except Exception as e:
        log(f"❌ 제목 평가 실패: {e}", "ERROR")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================
# 🎯 블로거 도구 - SEO 분석
# ============================

@app.route('/api/check-seo', methods=['POST'])
def check_seo():
    """🎯 SEO 종합 분석 API"""
    try:
        data = request.get_json()
        title = data.get('title', '')
        text = data.get('text', '')
        keywords = data.get('keywords', '')
        image_count = data.get('image_count', 0)
        
        if not text:
            return jsonify({'error': 'text is required'}), 400
        
        # SEO 종합 분석
        seo_result = {
            'title_optimization': analyze_title_seo(title, keywords),
            'content_optimization': analyze_content_seo(text, keywords),
            'image_optimization': analyze_image_seo(image_count),
            'readability': analyze_readability(text),
            'overall_score': 0,
            'quick_wins': []
        }
        
        # 종합 점수 계산
        scores = [
            seo_result['title_optimization']['score'] * 0.25,  # 25%
            seo_result['content_optimization']['score'] * 0.35,  # 35%
            seo_result['image_optimization']['score'] * 0.15,  # 15%
            seo_result['readability']['score'] * 0.25  # 25%
        ]
        seo_result['overall_score'] = int(sum(scores))
        
        # 즉시 개선 가능 항목 추출
        seo_result['quick_wins'] = extract_quick_wins(seo_result)
        
        # 등급 계산
        score = seo_result['overall_score']
        if score >= 90:
            seo_result['grade'] = 'S'
            seo_result['grade_message'] = '완벽한 SEO 최적화!'
        elif score >= 80:
            seo_result['grade'] = 'A'
            seo_result['grade_message'] = '우수한 SEO 최적화'
        elif score >= 70:
            seo_result['grade'] = 'B'
            seo_result['grade_message'] = '양호한 SEO 최적화'
        elif score >= 60:
            seo_result['grade'] = 'C'
            seo_result['grade_message'] = '보통 수준의 SEO'
        else:
            seo_result['grade'] = 'D'
            seo_result['grade_message'] = '개선이 많이 필요함'
        
        log(f"🎯 SEO 분석 완료: {len(text)}자, 점수 {seo_result['overall_score']}", "SEO")
        
        return jsonify({
            'success': True,
            'seo': seo_result
        }), 200
    
    except Exception as e:
        log(f"❌ SEO 분석 실패: {e}", "ERROR")
        import traceback
        log(f"📋 상세 에러: {traceback.format_exc()}", "ERROR")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def analyze_title_seo(title, keywords):
    """제목 SEO 분석"""
    import re
    
    if not title:
        return {
            'score': 0,
            'issues': ['제목이 없습니다'],
            'suggestions': ['제목을 입력해주세요'],
            'details': {}
        }
    
    score = 50
    issues = []
    suggestions = []
    details = {}
    
    title_length = len(title)
    details['length'] = title_length
    
    # 1. 길이 체크 (20-50자 권장)
    if 20 <= title_length <= 50:
        score += 20
        details['length_status'] = 'good'
    elif title_length < 20:
        issues.append('제목이 너무 짧습니다')
        suggestions.append('제목을 20자 이상으로 늘리세요')
        details['length_status'] = 'short'
    else:
        issues.append('제목이 너무 깁니다')
        suggestions.append('제목을 50자 이하로 줄이세요')
        score -= 10
        details['length_status'] = 'long'
    
    # 2. 키워드 포함 체크
    keywords_list = [k.strip() for k in keywords.split(',') if k.strip()] if keywords else []
    keyword_in_title = any(kw in title for kw in keywords_list) if keywords_list else False
    
    if keyword_in_title:
        score += 15
        details['keyword_included'] = True
    else:
        if keywords_list:
            issues.append('주요 키워드가 제목에 없습니다')
            suggestions.append(f'"{keywords_list[0]}" 키워드를 제목에 추가하세요')
        details['keyword_included'] = False
    
    # 3. 숫자 포함 체크 (클릭율 향상)
    has_number = bool(re.search(r'\d+|TOP|BEST|순위', title))
    details['has_number'] = has_number
    
    if has_number:
        score += 10
    else:
        suggestions.append('숫자를 넣으면 클릭율이 23% 증가합니다 (예: TOP 5, BEST 10)')
    
    # 4. 특수문자/이모지 체크
    has_special = bool(re.search(r'[|:!?]', title))
    details['has_special'] = has_special
    
    if has_special:
        score += 5
    else:
        suggestions.append('구분자(|, :)를 사용하면 가독성이 좋아집니다')
    
    return {
        'score': min(100, score),
        'issues': issues,
        'suggestions': suggestions,
        'details': details
    }

def analyze_content_seo(text, keywords):
    """본문 SEO 분석"""
    import re
    from collections import Counter
    
    score = 50
    issues = []
    suggestions = []
    details = {}
    
    # 1. 글자수 체크 (800-2000자 권장)
    text_length = len(text)
    details['length'] = text_length
    
    if 800 <= text_length <= 2000:
        score += 20
        details['length_status'] = 'good'
    elif text_length < 800:
        issues.append(f'본문이 너무 짧습니다 ({text_length}자)')
        suggestions.append(f'{800 - text_length}자를 더 작성하세요')
        details['length_status'] = 'short'
    else:
        score += 10  # 긴 건 나쁘지 않음
        details['length_status'] = 'long'
    
    # 2. 키워드 밀도 체크
    keywords_list = [k.strip() for k in keywords.split(',') if k.strip()] if keywords else []
    
    if keywords_list:
        main_keyword = keywords_list[0]
        keyword_count = text.count(main_keyword)
        words = re.findall(r'[가-힣]{2,}', text)
        total_words = len(words)
        
        if total_words > 0:
            keyword_density = (keyword_count / total_words) * 100
            details['keyword_density'] = round(keyword_density, 2)
            details['keyword_count'] = keyword_count
            
            if 0.5 <= keyword_density <= 1.5:
                score += 15
                details['density_status'] = 'good'
            elif keyword_density < 0.5:
                issues.append(f'"{main_keyword}" 키워드가 부족합니다')
                suggestions.append(f'"{main_keyword}"를 {int(total_words * 0.01) - keyword_count}회 더 사용하세요')
                details['density_status'] = 'low'
            else:
                issues.append(f'"{main_keyword}" 키워드가 과다합니다')
                suggestions.append(f'"{main_keyword}"를 {keyword_count - int(total_words * 0.015)}회 줄이세요')
                score -= 10
                details['density_status'] = 'high'
    
    # 3. 단락 구조 (줄바꿈)
    paragraphs = text.split('\n\n')
    paragraph_count = len([p for p in paragraphs if p.strip()])
    details['paragraph_count'] = paragraph_count
    
    if paragraph_count >= 3:
        score += 10
        details['paragraph_status'] = 'good'
    else:
        issues.append('단락이 부족합니다')
        suggestions.append('글을 3개 이상의 단락으로 나누세요')
        details['paragraph_status'] = 'poor'
    
    # 4. 내부 링크 (실제로는 HTML 파싱 필요, 여기서는 URL 패턴 체크)
    has_links = bool(re.search(r'http[s]?://|www\.', text))
    details['has_links'] = has_links
    
    if has_links:
        score += 5
    else:
        suggestions.append('관련 포스트 링크를 추가하면 SEO에 도움됩니다')
    
    return {
        'score': min(100, score),
        'issues': issues,
        'suggestions': suggestions,
        'details': details
    }

def analyze_image_seo(image_count):
    """이미지 SEO 분석"""
    score = 50
    issues = []
    suggestions = []
    details = {'count': image_count}
    
    # 1. 이미지 개수 체크 (5-15개 권장)
    if 5 <= image_count <= 15:
        score += 30
        details['count_status'] = 'good'
    elif image_count < 5:
        issues.append(f'이미지가 부족합니다 ({image_count}개)')
        suggestions.append(f'{5 - image_count}개의 이미지를 더 추가하세요')
        details['count_status'] = 'low'
    else:
        score += 10  # 많은 건 나쁘지 않음
        details['count_status'] = 'high'
    
    # 2. 이미지 최적화 가이드
    if image_count > 0:
        suggestions.append('이미지 파일명을 키워드로 변경하세요 (예: keyword-image-01.jpg)')
        suggestions.append('이미지 ALT 태그를 추가하세요')
        suggestions.append('이미지 용량을 최적화하세요 (권장: 200KB 이하)')
    
    return {
        'score': min(100, score),
        'issues': issues,
        'suggestions': suggestions,
        'details': details
    }

def extract_quick_wins(seo_result):
    """즉시 개선 가능한 항목 추출"""
    quick_wins = []
    
    # 제목 개선
    if seo_result['title_optimization']['score'] < 80:
        for suggestion in seo_result['title_optimization']['suggestions'][:2]:
            quick_wins.append({
                'category': 'title',
                'action': suggestion,
                'impact': '높음',
                'time': '5초'
            })
    
    # 본문 개선
    if seo_result['content_optimization']['score'] < 80:
        for suggestion in seo_result['content_optimization']['suggestions'][:2]:
            quick_wins.append({
                'category': 'content',
                'action': suggestion,
                'impact': '중간',
                'time': '5-10분'
            })
    
    # 이미지 개선
    if seo_result['image_optimization']['score'] < 70:
        if seo_result['image_optimization']['suggestions']:
            quick_wins.append({
                'category': 'image',
                'action': seo_result['image_optimization']['suggestions'][0],
                'impact': '중간',
                'time': '2분'
            })
    
    return quick_wins[:5]  # 최대 5개

# ============================
# ✍️ 블로거 도구 - AI 글쓰기 도우미
# ============================

@app.route('/api/generate-content', methods=['POST'])
def generate_content():
    """✍️ AI 글쓰기 도우미 API"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        keywords = data.get('keywords', [])
        tone = data.get('tone', 'friendly')  # friendly, professional, casual, formal
        structure = data.get('structure', 'intro-body-conclusion')
        word_count = data.get('word_count', 1000)
        
        if not topic:
            return jsonify({'error': 'topic is required'}), 400
        
        # AI로 글 생성
        content = generate_blog_content(topic, keywords, tone, structure, word_count)
        
        log(f"✍️ AI 글쓰기 완료: {topic[:30]}... ({len(content)}자)", "AI_WRITER")
        
        return jsonify({
            'success': True,
            'content': content,
            'metadata': {
                'char_count': len(content),
                'word_count': len(content.split()),
                'estimated_reading_time': f"{len(content) // 500}분"
            }
        }), 200
    
    except Exception as e:
        log(f"❌ AI 글쓰기 실패: {e}", "ERROR")
        import traceback
        log(f"📋 상세 에러: {traceback.format_exc()}", "ERROR")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_blog_content(topic, keywords, tone, structure, word_count):
    """AI로 블로그 콘텐츠 생성"""
    try:
        # 톤 설정
        tone_descriptions = {
            'friendly': '친근하고 편안한 말투로, 친구에게 이야기하듯 자연스럽게',
            'professional': '전문적이고 신뢰감 있는 톤으로, 정확한 정보 전달에 집중',
            'casual': '가볍고 재미있는 분위기로, 읽기 편한 일상적인 표현',
            'formal': '격식 있고 정중한 말투로, 공식적이고 체계적으로',
            'emotional': '감성적이고 공감을 이끌어내는 스토리텔링 방식으로'
        }
        
        tone_desc = tone_descriptions.get(tone, tone_descriptions['friendly'])
        
        # 구조 설정
        structure_templates = {
            'intro-body-conclusion': '''
서론: 주제 소개 및 독자의 관심 유도 (2-3문단)
본론: 핵심 내용을 3-5개 소제목으로 나누어 자세히 설명
결론: 요약 및 마무리, 독자 행동 유도
''',
            'listicle': '''
도입: 간단한 소개
본론: 번호가 매겨진 리스트 형식 (각 항목마다 상세 설명)
마무리: 간단한 요약
''',
            'how-to': '''
문제 제기: 왜 이것이 필요한가?
단계별 가이드: 1단계, 2단계... (각 단계마다 상세 설명)
팁과 주의사항
결론: 정리 및 독려
''',
            'story': '''
도입: 상황 설정 및 배경
전개: 경험 또는 사례 상세 서술
교훈/인사이트: 배운 점, 느낀 점
마무리: 독자에게 전하는 메시지
''',
            'comparison': '''
서론: 비교 대상 소개
각 항목의 장단점 분석
비교표 또는 요약
결론: 추천 및 선택 가이드
'''
        }
        
        structure_template = structure_templates.get(structure, structure_templates['intro-body-conclusion'])
        
        # 키워드 문자열 생성
        keywords_str = ', '.join(keywords) if keywords else '없음'
        
        # 글자수 가이드
        word_guide = ''
        if word_count <= 500:
            word_guide = '짧고 간결하게 (500자 이내)'
        elif word_count <= 1000:
            word_guide = '적당한 길이로 (800-1200자)'
        elif word_count <= 1500:
            word_guide = '상세하게 (1200-1500자)'
        else:
            word_guide = '매우 상세하게 (1500자 이상)'
        
        # AI 프롬프트
        prompt = f"""당신은 전문 블로그 작가입니다. 아래 요구사항에 맞춰 고품질 블로그 글을 작성해주세요.

📌 주제: {topic}

🔑 핵심 키워드: {keywords_str}

🎨 작성 스타일: {tone_desc}

📋 글 구조:
{structure_template}

📏 분량: {word_guide} (목표: 약 {word_count}자)

✍️ 작성 가이드라인:
1. 독자의 관심을 사로잡는 매력적인 도입부
2. 키워드를 자연스럽게 포함 (과도하지 않게)
3. 구체적인 예시와 실용적인 정보 제공
4. 적절한 문단 나누기 (가독성 중시)
5. 검색 엔진 최적화(SEO)를 고려한 구조
6. 독자에게 가치를 제공하는 실질적인 내용

⚠️ 주의사항:
- 제목은 포함하지 마세요 (본문만)
- 자연스러운 한국어 표현 사용
- 과장되거나 광고성 표현 지양
- 실제 블로그 글처럼 진정성 있게

지금 바로 작성을 시작하세요:"""
        
        # OpenAI API 호출
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 10년 경력의 전문 블로그 작가입니다. 독자를 사로잡는 매력적이고 실용적인 콘텐츠를 작성합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )
        
        content = response.choices[0].message.content.strip()
        
        return content
    
    except Exception as e:
        log(f"❌ AI 콘텐츠 생성 실패: {e}", "ERROR")
        # 폴백: 간단한 템플릿
        return f"""안녕하세요! 오늘은 {topic}에 대해 이야기해보려고 합니다.

{topic}는 많은 분들이 관심을 가지고 계시는 주제인데요, 저도 이에 대해 자세히 알아보았습니다.

[본문 내용]

{', '.join(keywords[:3]) if keywords else topic}에 대해 더 자세히 알고 싶으시다면, 댓글로 질문해주세요!

오늘 소개해드린 {topic}, 어떠셨나요? 
도움이 되셨기를 바랍니다!"""

@app.route('/api/improve-content', methods=['POST'])
def improve_content():
    """✍️ 기존 글 개선 API"""
    try:
        data = request.get_json()
        original_content = data.get('content', '')
        improvement_type = data.get('type', 'overall')  # overall, grammar, style, seo
        
        if not original_content:
            return jsonify({'error': 'content is required'}), 400
        
        # AI로 글 개선
        improved_content = improve_with_ai(original_content, improvement_type)
        suggestions = generate_improvement_suggestions(original_content, improved_content)
        
        log(f"✨ 글 개선 완료: {improvement_type}", "AI_IMPROVE")
        
        return jsonify({
            'success': True,
            'improved_content': improved_content,
            'suggestions': suggestions
        }), 200
    
    except Exception as e:
        log(f"❌ 글 개선 실패: {e}", "ERROR")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def improve_with_ai(content, improvement_type):
    """AI로 글 개선"""
    try:
        improvement_prompts = {
            'overall': '전체적인 흐름, 가독성, 표현력을 개선',
            'grammar': '맞춤법, 띄어쓰기, 문법을 교정',
            'style': '더 매력적이고 자연스러운 문체로 변경',
            'seo': 'SEO에 최적화된 구조와 키워드 배치로 개선',
            'concise': '불필요한 내용을 제거하고 간결하게',
            'detailed': '더 자세하고 풍부한 내용으로 확장'
        }
        
        improvement_desc = improvement_prompts.get(improvement_type, improvement_prompts['overall'])
        
        prompt = f"""아래 블로그 글을 {improvement_desc}해주세요.

원본 글:
{content}

개선 지침:
1. 원본의 핵심 내용과 의도는 유지
2. {improvement_desc}
3. 자연스러운 한국어 표현
4. 가독성 향상
5. 더 매력적이고 전문적으로

개선된 글을 작성해주세요:"""
        
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 전문 편집자이자 블로그 컨설턴트입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=3000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        log(f"❌ AI 개선 실패: {e}", "ERROR")
        return content  # 실패시 원본 반환

def generate_improvement_suggestions(original, improved):
    """개선 전후 비교 및 제안"""
    suggestions = []
    
    # 글자수 비교
    orig_len = len(original)
    imp_len = len(improved)
    if abs(orig_len - imp_len) > 100:
        if imp_len > orig_len:
            suggestions.append({
                'type': 'length',
                'message': f'더 자세한 설명을 추가했습니다 (+{imp_len - orig_len}자)'
            })
        else:
            suggestions.append({
                'type': 'length',
                'message': f'불필요한 내용을 제거했습니다 (-{orig_len - imp_len}자)'
            })
    
    # 문단 수 비교
    orig_paragraphs = len([p for p in original.split('\n\n') if p.strip()])
    imp_paragraphs = len([p for p in improved.split('\n\n') if p.strip()])
    if imp_paragraphs > orig_paragraphs:
        suggestions.append({
            'type': 'structure',
            'message': '가독성을 위해 문단을 더 세분화했습니다'
        })
    
    suggestions.append({
        'type': 'quality',
        'message': 'AI가 글의 흐름과 표현을 자연스럽게 개선했습니다'
    })
    
    return suggestions

# ============================
# 🔍 블로거 도구 - 경쟁 블로그 분석
# ============================

@app.route('/api/analyze-competitors', methods=['POST'])
def analyze_competitors():
    """🔍 경쟁 블로그 분석 API"""
    try:
        data = request.get_json()
        url = data.get('keyword', '')  # 'keyword' 파라미터로 URL을 받음 (호환성)
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # URL에서 블로그 내용 크롤링
        blog_data = scrape_blog(url)
        if not blog_data or not blog_data.get('content'):
            return jsonify({'error': '블로그 내용을 가져올 수 없습니다'}), 400
        
        # AI로 블로그 분석
        analysis = analyze_competitor_blog_with_ai(blog_data)
        
        log(f"🔍 경쟁 블로그 분석 완료: {url}", "COMPETITOR")
        
        return jsonify({
            'success': True,
            'analysis': analysis
        }), 200
    
    except Exception as e:
        log(f"❌ 경쟁 블로그 분석 실패: {e}", "ERROR")
        import traceback
        log(f"📋 상세 에러: {traceback.format_exc()}", "ERROR")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def analyze_competitor_blog_with_ai(blog_data):
    """AI로 경쟁 블로그 분석"""
    try:
        title = blog_data.get('title', '')
        content = blog_data.get('content', '')
        
        # 기본 메트릭 계산
        word_count = len(content)
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        
        # AI 분석 프롬프트
        prompt = f"""다음 블로그 글을 분석하고, JSON 형식으로 결과를 제공하세요.

제목: {title}
본문: {content[:2000]}... (총 {word_count}자)

분석 항목:
1. 이 블로그의 주요 강점 3-5가지
2. 이 블로그의 약점 또는 개선점 3-5가지
3. 이 블로그를 이기기 위한 구체적인 전략

JSON 형식:
{{
    "metrics": {{
        "total_posts": "추정값",
        "avg_length": "{word_count}자",
        "posting_frequency": "추정 빈도"
    }},
    "strengths": ["강점1", "강점2", "강점3"],
    "weaknesses": ["약점1", "약점2", "약점3"],
    "strategy": "구체적인 승리 전략 (200자 이상)"
}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 블로그 마케팅 전문가입니다. 경쟁 블로그를 분석하고 실행 가능한 전략을 제시합니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        result = json.loads(response.choices[0].message.content)
        log(f"✅ AI 경쟁 블로그 분석 완료", "COMPETITOR")
        
        return result
        
    except Exception as e:
        log(f"❌ AI 분석 실패, 기본 분석 사용: {e}", "ERROR")
        # AI 실패 시 기본 분석
        return {
            "metrics": {
                "total_posts": "N/A",
                "avg_length": f"{len(content)}자",
                "posting_frequency": "N/A"
            },
            "strengths": [
                "체계적인 글 구성",
                "풍부한 정보 제공",
                "독자 친화적인 문체"
            ],
            "weaknesses": [
                "SEO 최적화 개선 필요",
                "시각 자료 보강 필요",
                "독창성 향상 가능"
            ],
            "strategy": "경쟁 블로그보다 더 상세한 정보와 실용적인 팁을 제공하고, SEO를 강화하여 검색 노출을 높이세요. 독자들이 궁금해하는 질문에 먼저 답하는 방식으로 차별화하세요."
        }

def analyze_top_blogs(keyword):
    """상위 블로그 분석 (시뮬레이션)"""
    import random
    
    # 실제로는 네이버 검색 API나 크롤링 필요
    # 여기서는 데이터 구조만 시뮬레이션
    
    # 통계 생성 (리얼한 범위로)
    avg_char_count = random.randint(1200, 2200)
    avg_image_count = random.randint(8, 18)
    avg_paragraph_count = random.randint(6, 12)
    
    # 공통 키워드 추출 (실제로는 형태소 분석 필요)
    common_keywords = generate_common_keywords(keyword)
    
    # 제목 패턴 분석
    title_patterns = analyze_title_patterns(keyword)
    
    # 구조 분석
    common_structure = {
        'intro_present': 85,  # 85%가 서론 있음
        'list_format': 72,  # 72%가 리스트 형식
        'conclusion_present': 78,  # 78%가 결론 있음
        'internal_links': 3.2,  # 평균 내부 링크 3.2개
        'external_links': 1.5  # 평균 외부 링크 1.5개
    }
    
    # 개선 제안 생성
    suggestions = generate_competitor_suggestions(
        avg_char_count,
        avg_image_count,
        common_keywords,
        title_patterns
    )
    
    return {
        'statistics': {
            'avg_char_count': avg_char_count,
            'avg_image_count': avg_image_count,
            'avg_paragraph_count': avg_paragraph_count,
            'avg_internal_links': common_structure['internal_links'],
            'avg_external_links': common_structure['external_links']
        },
        'common_keywords': common_keywords,
        'title_patterns': title_patterns,
        'structure_analysis': common_structure,
        'suggestions': suggestions,
        'competitive_score': calculate_competitive_score(suggestions)
    }

def generate_common_keywords(main_keyword):
    """공통 키워드 생성 (시뮬레이션)"""
    # 실제로는 상위 블로그에서 추출
    keyword_templates = {
        '맛집': ['추천', '가성비', '데이트', '분위기', '예약', '주차', '메뉴', '후기'],
        '여행': ['코스', '추천', '숙소', '맛집', '가볼만한곳', '관광지', '경치', '사진'],
        '제품': ['리뷰', '후기', '가격', '성능', '장단점', '비교', '추천', '구매']
    }
    
    base_keywords = []
    for key, keywords in keyword_templates.items():
        if key in main_keyword:
            base_keywords = keywords
            break
    
    if not base_keywords:
        base_keywords = ['추천', '후기', '정보', '방법', '가이드', '총정리']
    
    import random
    selected = random.sample(base_keywords, min(6, len(base_keywords)))
    
    return [
        {
            'keyword': kw,
            'frequency': random.randint(4, 12),
            'importance': random.choice(['high', 'medium'])
        }
        for kw in selected
    ]

def analyze_title_patterns(keyword):
    """제목 패턴 분석"""
    patterns = [
        {'pattern': 'TOP/BEST + 숫자', 'usage': 82, 'example': f'{keyword} BEST 10'},
        {'pattern': '숫자 + 추천', 'usage': 78, 'example': f'{keyword} 5곳 추천'},
        {'pattern': '완벽/총정리', 'usage': 65, 'example': f'{keyword} 완벽 가이드'},
        {'pattern': '궁금증 유발', 'usage': 58, 'example': f'{keyword} 어디가 좋을까?'},
        {'pattern': '혜택 명시', 'usage': 71, 'example': f'{keyword} 가성비 甲'}
    ]
    
    return sorted(patterns, key=lambda x: x['usage'], reverse=True)

def generate_competitor_suggestions(char_count, image_count, keywords, title_patterns):
    """경쟁 분석 기반 개선 제안"""
    suggestions = []
    
    # 글자수 제안
    suggestions.append({
        'category': 'content_length',
        'title': '글자수 최적화',
        'description': f'상위 블로그 평균: {char_count}자',
        'action': f'{char_count - 200}~{char_count + 200}자 범위로 작성하세요',
        'priority': 'high'
    })
    
    # 이미지 제안
    suggestions.append({
        'category': 'images',
        'title': '이미지 개수',
        'description': f'상위 블로그 평균: {image_count}장',
        'action': f'{image_count - 2}~{image_count + 2}장의 이미지를 사용하세요',
        'priority': 'high'
    })
    
    # 키워드 제안
    top_keywords = [kw['keyword'] for kw in keywords[:3]]
    suggestions.append({
        'category': 'keywords',
        'title': '필수 키워드',
        'description': f'상위 블로그 공통: {", ".join(top_keywords)}',
        'action': f'이 키워드들을 글에 자연스럽게 포함하세요',
        'priority': 'high'
    })
    
    # 제목 패턴 제안
    top_pattern = title_patterns[0]
    suggestions.append({
        'category': 'title',
        'title': '제목 패턴',
        'description': f'{top_pattern["usage"]}%가 사용: {top_pattern["pattern"]}',
        'action': f'예시: {top_pattern["example"]}',
        'priority': 'medium'
    })
    
    # 구조 제안
    suggestions.append({
        'category': 'structure',
        'title': '글 구조',
        'description': '72%가 리스트 형식 사용',
        'action': '리스트 형식으로 구성하면 가독성 UP',
        'priority': 'medium'
    })
    
    return suggestions

def calculate_competitive_score(suggestions):
    """경쟁력 점수 계산"""
    # 제안사항의 우선순위에 따라 점수 계산
    base_score = 50
    high_priority = len([s for s in suggestions if s['priority'] == 'high'])
    
    # 개선이 많이 필요할수록 점수 낮음
    score = max(30, base_score - (high_priority * 5))
    
    return {
        'score': score,
        'grade': 'A' if score >= 80 else 'B' if score >= 60 else 'C' if score >= 40 else 'D',
        'message': get_score_message(score)
    }

def get_score_message(score):
    """점수별 메시지"""
    if score >= 80:
        return '상위 블로그와 경쟁할 수 있는 수준입니다!'
    elif score >= 60:
        return '몇 가지만 개선하면 경쟁력이 높아집니다'
    elif score >= 40:
        return '개선이 많이 필요합니다. 제안사항을 참고하세요'
    else:
        return '경쟁 블로그 대비 많은 개선이 필요합니다'

# ============================
# 🔑 블로거 도구 - 키워드 추천
# ============================

@app.route('/api/recommend-keywords', methods=['POST'])
def recommend_keywords():
    """🔑 키워드 추천 API"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        
        if not topic:
            return jsonify({'error': 'topic is required'}), 400
        
        # 키워드 추천
        keywords = generate_keyword_recommendations(topic)
        
        log(f"🔑 키워드 추천 완료: {topic}", "KEYWORD")
        
        return jsonify({
            'success': True,
            'keywords': keywords
        }), 200
    
    except Exception as e:
        log(f"❌ 키워드 추천 실패: {e}", "ERROR")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_keyword_recommendations(topic):
    """키워드 추천 생성"""
    import random
    
    # 주제 기반 키워드 템플릿
    keyword_types = {
        'primary': [],  # 주요 키워드
        'secondary': [],  # 연관 키워드
        'long_tail': []  # 롱테일 키워드
    }
    
    # 주요 키워드 (검색량 높음)
    if '맛집' in topic:
        keyword_types['primary'] = [
            {'keyword': f'{topic}', 'volume': 'high', 'difficulty': 'hard'},
            {'keyword': f'{topic} 추천', 'volume': 'high', 'difficulty': 'hard'},
            {'keyword': f'{topic} 베스트', 'volume': 'medium', 'difficulty': 'medium'}
        ]
        keyword_types['secondary'] = [
            {'keyword': f'{topic} 데이트', 'volume': 'medium', 'difficulty': 'medium'},
            {'keyword': f'{topic} 가성비', 'volume': 'medium', 'difficulty': 'medium'},
            {'keyword': f'{topic} 예약', 'volume': 'low', 'difficulty': 'easy'}
        ]
        keyword_types['long_tail'] = [
            {'keyword': f'{topic} 주차 편한곳', 'volume': 'low', 'difficulty': 'easy'},
            {'keyword': f'{topic} 데이트 코스', 'volume': 'low', 'difficulty': 'easy'},
            {'keyword': f'{topic} 분위기 좋은', 'volume': 'low', 'difficulty': 'easy'}
        ]
    else:
        # 범용 키워드
        keyword_types['primary'] = [
            {'keyword': topic, 'volume': 'high', 'difficulty': 'hard'},
            {'keyword': f'{topic} 추천', 'volume': 'high', 'difficulty': 'hard'},
            {'keyword': f'{topic} 정보', 'volume': 'medium', 'difficulty': 'medium'}
        ]
        keyword_types['secondary'] = [
            {'keyword': f'{topic} 방법', 'volume': 'medium', 'difficulty': 'medium'},
            {'keyword': f'{topic} 가이드', 'volume': 'medium', 'difficulty': 'medium'},
            {'keyword': f'{topic} 후기', 'volume': 'low', 'difficulty': 'easy'}
        ]
        keyword_types['long_tail'] = [
            {'keyword': f'{topic} 초보자', 'volume': 'low', 'difficulty': 'easy'},
            {'keyword': f'{topic} 꿀팁', 'volume': 'low', 'difficulty': 'easy'},
            {'keyword': f'{topic} 총정리', 'volume': 'low', 'difficulty': 'easy'}
        ]
    
    # 검색량 추가 (추정치)
    volume_map = {'high': random.randint(5000, 15000), 'medium': random.randint(1000, 5000), 'low': random.randint(100, 1000)}
    
    all_keywords = []
    for category, kws in keyword_types.items():
        for kw in kws:
            kw['category'] = category
            kw['volume_estimate'] = volume_map[kw['volume']]
            kw['recommendation'] = get_keyword_recommendation(kw['difficulty'], kw['volume'])
            all_keywords.append(kw)
    
    return {
        'primary': keyword_types['primary'],
        'secondary': keyword_types['secondary'],
        'long_tail': keyword_types['long_tail'],
        'recommended_combination': generate_keyword_combination(keyword_types)
    }

def get_keyword_recommendation(difficulty, volume):
    """키워드별 추천 메시지"""
    if difficulty == 'hard' and volume == 'high':
        return '경쟁이 치열하지만 검색량이 많아 가치가 높습니다'
    elif difficulty == 'medium':
        return '적당한 경쟁도로 노출 가능성이 있습니다'
    else:
        return '경쟁이 낮아 상위 노출이 쉽습니다 (추천!)'

def generate_keyword_combination(keyword_types):
    """키워드 조합 추천"""
    primary = keyword_types['primary'][0]['keyword'] if keyword_types['primary'] else ''
    secondary = keyword_types['secondary'][0]['keyword'] if keyword_types['secondary'] else ''
    long_tail = keyword_types['long_tail'][0]['keyword'] if keyword_types['long_tail'] else ''
    
    combinations = []
    
    if primary:
        combinations.append({
            'title': f'{primary}',
            'keywords': [primary],
            'strategy': '메인 키워드 집중 공략'
        })
    
    if primary and secondary:
        combinations.append({
            'title': f'{primary} + {secondary.split()[-1]}',
            'keywords': [primary, secondary],
            'strategy': '메인 + 연관 키워드 조합'
        })
    
    if long_tail:
        combinations.append({
            'title': long_tail,
            'keywords': [long_tail],
            'strategy': '롱테일 키워드로 틈새 공략 (추천!)'
        })
    
    return combinations

# ============================
# 🔐 사용자 인증 시스템
# ============================

# 간단한 사용자 세션 체크 (Redis 기반)
def get_user_from_session():
    """세션에서 사용자 정보 가져오기"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    try:
        user_data = redis_client.get(f'user:{user_id}')
        if user_data:
            return json.loads(user_data)
        return None
    except:
        return None

def login_required_user(f):
    """사용자 로그인 필수 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_user_from_session():
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """회원가입"""
    if request.method == 'GET':
        return render_template('signup.html')
    
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        
        if not email or not password or not name:
            return jsonify({'success': False, 'error': '모든 필드를 입력해주세요'}), 400
        
        # 이메일 중복 체크
        existing_user = redis_client.get(f'user_email:{email}')
        if existing_user:
            return jsonify({'success': False, 'error': '이미 가입된 이메일입니다'}), 400
        
        # 사용자 생성
        user_id = f"user_{datetime.now().timestamp()}"
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        user_data = {
            'id': user_id,
            'email': email,
            'password': password_hash,
            'name': name,
            'plan': 'free',  # free, basic, pro
            'created_at': datetime.now(KST).isoformat(),
            'usage': {
                'text_analyzer': 0,
                'title_generator': 0,
                'seo_checker': 0,
                'ai_writer': 0,
                'competitor_analyzer': 0,
                'keyword_recommender': 0
            }
        }
        
        # Redis에 저장
        redis_client.set(f'user:{user_id}', json.dumps(user_data))
        redis_client.set(f'user_email:{email}', user_id)
        
        log(f"✅ 회원가입 성공: {email}", "AUTH")
        
        return jsonify({
            'success': True,
            'message': '회원가입이 완료되었습니다!'
        }), 200
    
    except Exception as e:
        log(f"❌ 회원가입 실패: {e}", "ERROR")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/login-page')
def login_page():
    """로그인 페이지"""
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """로그인"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': '이메일과 비밀번호를 입력해주세요'}), 400
        
        # 사용자 찾기
        user_id = redis_client.get(f'user_email:{email}')
        if not user_id:
            return jsonify({'success': False, 'error': '존재하지 않는 이메일입니다'}), 401
        
        user_id = user_id.decode() if isinstance(user_id, bytes) else user_id
        user_data_str = redis_client.get(f'user:{user_id}')
        if not user_data_str:
            return jsonify({'success': False, 'error': '사용자 정보를 찾을 수 없습니다'}), 401
        
        user_data = json.loads(user_data_str)
        
        # 비밀번호 확인
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user_data['password'] != password_hash:
            return jsonify({'success': False, 'error': '비밀번호가 일치하지 않습니다'}), 401
        
        # 세션 설정
        session['user_id'] = user_id
        session.permanent = True
        
        log(f"✅ 로그인 성공: {email}", "AUTH")
        
        return jsonify({
            'success': True,
            'user': {
                'name': user_data['name'],
                'email': user_data['email'],
                'plan': user_data['plan']
            }
        }), 200
    
    except Exception as e:
        log(f"❌ 로그인 실패: {e}", "ERROR")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/logout')
def logout():
    """로그아웃"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/mypage')
@login_required_user
def mypage():
    """마이페이지"""
    user = get_user_from_session()
    return render_template('mypage.html', user=user)

# ============================
# 💳 메인페이 결제 시스템 (키인)
# ============================

@app.route('/pricing')
def pricing():
    """요금제 페이지"""
    user = get_user_from_session()
    return render_template('pricing.html', user=user)

@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    """메인페이 결제 생성"""
    try:
        user = get_user_from_session()
        if not user:
            return jsonify({'success': False, 'error': '로그인이 필요합니다'}), 401
        
        data = request.get_json()
        plan = data.get('plan')  # 'basic' or 'pro'
        
        if plan not in ['basic', 'pro']:
            return jsonify({'success': False, 'error': '잘못된 플랜입니다'}), 400
        
        # 플랜 정보
        plans = {
            'basic': {'name': '베이직 플랜', 'price': 9900},
            'pro': {'name': '프로 플랜', 'price': 19900}
        }
        
        plan_info = plans[plan]
        
        # 주문번호 생성
        order_id = f"ORDER_{user['id']}_{datetime.now().timestamp()}"
        
        # 메인페이 결제 정보 생성
        payment_data = {
            'order_id': order_id,
            'user_id': user['id'],
            'plan': plan,
            'amount': plan_info['price'],
            'product_name': plan_info['name'],
            'created_at': datetime.now(KST).isoformat(),
            'status': 'pending'
        }
        
        # Redis에 임시 저장
        redis_client.setex(f'payment:{order_id}', 3600, json.dumps(payment_data))
        
        log(f"💳 결제 생성: {user['email']} - {plan} ({plan_info['price']}원)", "PAYMENT")
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'amount': plan_info['price'],
            'product_name': plan_info['name']
        }), 200
    
    except Exception as e:
        log(f"❌ 결제 생성 실패: {e}", "ERROR")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/payment-callback', methods=['POST'])
def payment_callback():
    """메인페이 결제 콜백"""
    try:
        # 메인페이에서 전달받은 데이터
        data = request.form.to_dict()
        order_id = data.get('order_id')
        status = data.get('status')  # 'success' or 'fail'
        
        # 결제 정보 조회
        payment_data_str = redis_client.get(f'payment:{order_id}')
        if not payment_data_str:
            return jsonify({'success': False, 'error': '결제 정보를 찾을 수 없습니다'}), 404
        
        payment_data = json.loads(payment_data_str)
        
        if status == 'success':
            # 사용자 플랜 업데이트
            user_id = payment_data['user_id']
            user_data_str = redis_client.get(f'user:{user_id}')
            user_data = json.loads(user_data_str)
            
            user_data['plan'] = payment_data['plan']
            user_data['plan_started_at'] = datetime.now(KST).isoformat()
            user_data['plan_expires_at'] = (datetime.now(KST) + timedelta(days=30)).isoformat()
            
            # 사용 횟수 초기화
            user_data['usage'] = {
                'text_analyzer': 0,
                'title_generator': 0,
                'seo_checker': 0,
                'ai_writer': 0,
                'competitor_analyzer': 0,
                'keyword_recommender': 0
            }
            
            redis_client.set(f'user:{user_id}', json.dumps(user_data))
            
            # 결제 정보 업데이트
            payment_data['status'] = 'completed'
            payment_data['completed_at'] = datetime.now(KST).isoformat()
            redis_client.set(f'payment:{order_id}', json.dumps(payment_data))
            
            log(f"✅ 결제 완료: {user_data['email']} - {payment_data['plan']}", "PAYMENT")
            
            return jsonify({'success': True, 'message': '결제가 완료되었습니다!'}), 200
        else:
            payment_data['status'] = 'failed'
            redis_client.set(f'payment:{order_id}', json.dumps(payment_data))
            log(f"❌ 결제 실패: {order_id}", "PAYMENT")
            return jsonify({'success': False, 'error': '결제가 실패했습니다'}), 400
    
    except Exception as e:
        log(f"❌ 결제 콜백 실패: {e}", "ERROR")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================
# 🎯 사용 제한 시스템
# ============================

def check_usage_limit(tool_name):
    """사용 제한 체크"""
    user = get_user_from_session()
    if not user:
        return {'allowed': False, 'error': '로그인이 필요합니다', 'redirect': '/login-page'}
    
    # 플랜별 제한
    limits = {
        'free': {
            'text_analyzer': 3,
            'title_generator': 2,
            'seo_checker': 1,
            'ai_writer': 0,  # 무료 불가
            'competitor_analyzer': 0,  # 무료 불가
            'keyword_recommender': 0  # 무료 불가
        },
        'basic': {
            'text_analyzer': 999999,  # 무제한
            'title_generator': 999999,
            'seo_checker': 999999,
            'ai_writer': 10,
            'competitor_analyzer': 5,
            'keyword_recommender': 20
        },
        'pro': {
            'text_analyzer': 999999,
            'title_generator': 999999,
            'seo_checker': 999999,
            'ai_writer': 999999,
            'competitor_analyzer': 999999,
            'keyword_recommender': 999999
        }
    }
    
    user_plan = user.get('plan', 'free')
    user_usage = user.get('usage', {})
    current_usage = user_usage.get(tool_name, 0)
    limit = limits[user_plan].get(tool_name, 0)
    
    if current_usage >= limit:
        return {
            'allowed': False,
            'error': f'{"무료 플랜에서는 사용할 수 없습니다" if limit == 0 else "이번 달 사용 한도를 초과했습니다"}',
            'current': current_usage,
            'limit': limit,
            'plan': user_plan
        }
    
    # 사용 횟수 증가
    user_usage[tool_name] = current_usage + 1
    user['usage'] = user_usage
    redis_client.set(f"user:{user['id']}", json.dumps(user))
    
    return {
        'allowed': True,
        'current': user_usage[tool_name],
        'limit': limit,
        'plan': user_plan
    }

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

