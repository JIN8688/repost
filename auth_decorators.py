"""
인증 및 사용 제한 데코레이터
"""
from functools import wraps
from flask import session, jsonify

# 요금제별 제한
PLAN_LIMITS = {
    'free': {
        'text_analyzer': 5,      # 일 5회
        'title_generator': 5,    # 일 5회
        'seo_checker': 3,        # 일 3회
        'ai_writer': 0,          # 불가
        'competitor_analyzer': 0,  # 불가
        'keyword_recommender': 0   # 불가
    },
    'basic': {
        'text_analyzer': 100,
        'title_generator': 100,
        'seo_checker': 50,
        'ai_writer': 30,
        'competitor_analyzer': 20,
        'keyword_recommender': 20
    },
    'pro': {
        'text_analyzer': float('inf'),  # 무제한
        'title_generator': float('inf'),
        'seo_checker': float('inf'),
        'ai_writer': float('inf'),
        'competitor_analyzer': float('inf'),
        'keyword_recommender': float('inf')
    },
    'master': {
        'text_analyzer': float('inf'),  # 무제한
        'title_generator': float('inf'),
        'seo_checker': float('inf'),
        'ai_writer': float('inf'),
        'competitor_analyzer': float('inf'),
        'keyword_recommender': float('inf')
    }
}

def login_required(f):
    """로그인 필수 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': '로그인이 필요합니다',
                'login_required': True
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def check_usage_limit(action_type):
    """사용 제한 확인 데코레이터"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from database import db
            from flask import request
            
            if 'user_id' not in session:
                return jsonify({
                    'success': False,
                    'error': '로그인이 필요합니다',
                    'login_required': True
                }), 401
            
            user_id = session['user_id']
            
            # 사용자 정보 가져오기
            user = db.get_user_by_email(session.get('user_email'))
            if not user:
                return jsonify({
                    'success': False,
                    'error': '사용자 정보를 찾을 수 없습니다'
                }), 401
            
            plan = user.get('plan', 'free')
            
            # 🔑 마스터 계정 체크 (세션 또는 요청 데이터)
            is_admin = session.get('is_admin', False) or \
                      (request.is_json and request.json.get('isAdmin', False))
            
            if is_admin or plan == 'master':
                # 마스터 계정은 무제한 사용 (사용 기록은 저장)
                db.log_usage(user_id, action_type)
                return f(*args, **kwargs)
            
            limit = PLAN_LIMITS.get(plan, {}).get(action_type, 0)
            
            # 무제한인 경우
            if limit == float('inf'):
                return f(*args, **kwargs)
            
            # 사용 횟수 확인 (최근 30일)
            usage_count = db.get_usage_count(user_id, action_type, days=30)
            
            if usage_count >= limit:
                return jsonify({
                    'success': False,
                    'error': f'사용 제한에 도달했습니다 ({usage_count}/{limit})',
                    'limit_reached': True,
                    'current_plan': plan,
                    'usage': usage_count,
                    'limit': limit
                }), 429
            
            # 사용 기록 저장
            db.log_usage(user_id, action_type)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

