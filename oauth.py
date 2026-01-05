"""
OAuth 소셜 로그인 (구글, 카카오, 네이버)
"""
from authlib.integrations.flask_client import OAuth
import os

def init_oauth(app):
    """OAuth 초기화"""
    oauth = OAuth(app)
    
    # Google OAuth
    google = oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    
    # Kakao OAuth
    kakao = oauth.register(
        name='kakao',
        client_id=os.getenv('KAKAO_CLIENT_ID'),
        client_secret=os.getenv('KAKAO_CLIENT_SECRET'),
        access_token_url='https://kauth.kakao.com/oauth/token',
        authorize_url='https://kauth.kakao.com/oauth/authorize',
        api_base_url='https://kapi.kakao.com',
        client_kwargs={'scope': 'profile_nickname account_email'},
    )
    
    # Naver OAuth
    naver = oauth.register(
        name='naver',
        client_id=os.getenv('NAVER_CLIENT_ID'),
        client_secret=os.getenv('NAVER_CLIENT_SECRET'),
        access_token_url='https://nid.naver.com/oauth2.0/token',
        authorize_url='https://nid.naver.com/oauth2.0/authorize',
        api_base_url='https://openapi.naver.com',
        client_kwargs={'scope': 'email name'},
    )
    
    return oauth

def get_google_user_info(token):
    """Google 사용자 정보 가져오기"""
    import requests
    
    headers = {'Authorization': f'Bearer {token["access_token"]}'}
    response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return {
            'oauth_id': data['id'],
            'email': data['email'],
            'name': data.get('name', data['email'].split('@')[0]),
            'profile_image': data.get('picture')
        }
    return None

def get_kakao_user_info(token):
    """Kakao 사용자 정보 가져오기"""
    import requests
    
    headers = {'Authorization': f'Bearer {token["access_token"]}'}
    response = requests.get('https://kapi.kakao.com/v2/user/me', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        kakao_account = data.get('kakao_account', {})
        profile = kakao_account.get('profile', {})
        
        return {
            'oauth_id': str(data['id']),
            'email': kakao_account.get('email'),
            'name': profile.get('nickname', '카카오 사용자'),
            'profile_image': profile.get('profile_image_url')
        }
    return None

def get_naver_user_info(token):
    """Naver 사용자 정보 가져오기"""
    import requests
    
    headers = {'Authorization': f'Bearer {token["access_token"]}'}
    response = requests.get('https://openapi.naver.com/v1/nid/me', headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        user_data = data.get('response', {})
        
        return {
            'oauth_id': user_data['id'],
            'email': user_data.get('email'),
            'name': user_data.get('name', '네이버 사용자'),
            'profile_image': user_data.get('profile_image')
        }
    return None

