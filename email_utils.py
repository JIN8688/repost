"""
Resend 이메일 발송 유틸리티
"""
import os
import resend
from datetime import datetime, timedelta
import random
import string

# Resend API 키 설정
resend.api_key = os.getenv('RESEND_API_KEY')

# 발신자 이메일 (Resend에서 인증된 도메인 또는 이메일)
FROM_EMAIL = os.getenv('FROM_EMAIL', 'onboarding@resend.dev')  # 개발용 기본값

def generate_verification_code():
    """6자리 인증 코드 생성"""
    return ''.join(random.choices(string.digits, k=6))

def generate_temp_password():
    """임시 비밀번호 생성 (10자리 영문+숫자)"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def send_verification_email(to_email, verification_code):
    """이메일 인증 코드 발송"""
    try:
        params = {
            "from": FROM_EMAIL,
            "to": to_email,
            "subject": "[Repost] 이메일 인증 코드",
            "html": f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
        .header {{ text-align: center; padding: 30px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px 20px 0 0; }}
        .header h1 {{ color: white; margin: 0; font-size: 28px; }}
        .content {{ background: white; padding: 40px; border-radius: 0 0 20px 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .code-box {{ background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 30px; text-align: center; border-radius: 16px; margin: 30px 0; }}
        .code {{ font-size: 42px; font-weight: bold; letter-spacing: 8px; color: #667eea; font-family: 'Courier New', monospace; }}
        .info {{ background: #f8f9fa; padding: 20px; border-radius: 12px; border-left: 4px solid #667eea; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 30px; color: #666; font-size: 14px; }}
        .button {{ display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 12px; font-weight: bold; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 이메일 인증</h1>
        </div>
        <div class="content">
            <p style="font-size: 18px; margin-bottom: 20px;">안녕하세요!</p>
            <p>Repost 회원가입을 위한 인증 코드입니다.</p>
            <p>아래 코드를 입력하여 이메일 인증을 완료해주세요.</p>
            
            <div class="code-box">
                <div style="color: #666; font-size: 14px; margin-bottom: 10px;">인증 코드</div>
                <div class="code">{verification_code}</div>
            </div>
            
            <div class="info">
                <strong>⏰ 유효 시간:</strong> 발송 후 10분<br>
                <strong>🔒 보안:</strong> 본인이 요청하지 않았다면 무시하세요
            </div>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                본인이 요청한 인증이 아니라면, 이 메일을 무시하셔도 됩니다.
            </p>
        </div>
        <div class="footer">
            <p>© 2026 Repost. All rights reserved.</p>
            <p>1만 명의 블로거가 선택한 AI 글쓰기 플랫폼</p>
        </div>
    </div>
</body>
</html>
            """
        }
        
        response = resend.Emails.send(params)
        print(f"✅ 인증 이메일 발송 성공: {to_email} / 코드: {verification_code}")
        return True
    
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {e}")
        # 개발 모드에서는 콘솔에 출력
        print(f"\n{'='*50}")
        print(f"📧 인증 코드 (개발 모드)")
        print(f"이메일: {to_email}")
        print(f"인증 코드: {verification_code}")
        print(f"{'='*50}\n")
        return False

def send_password_reset_email(to_email, temp_password):
    """임시 비밀번호 발송"""
    try:
        params = {
            "from": FROM_EMAIL,
            "to": to_email,
            "subject": "[Repost] 임시 비밀번호 안내",
            "html": f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
        .header {{ text-align: center; padding: 30px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px 20px 0 0; }}
        .header h1 {{ color: white; margin: 0; font-size: 28px; }}
        .content {{ background: white; padding: 40px; border-radius: 0 0 20px 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .password-box {{ background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 30px; text-align: center; border-radius: 16px; margin: 30px 0; }}
        .password {{ font-size: 32px; font-weight: bold; letter-spacing: 4px; color: #667eea; font-family: 'Courier New', monospace; }}
        .warning {{ background: #fff3cd; padding: 20px; border-radius: 12px; border-left: 4px solid #ffc107; margin: 20px 0; color: #856404; }}
        .button {{ display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 12px; font-weight: bold; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 30px; color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔑 임시 비밀번호</h1>
        </div>
        <div class="content">
            <p style="font-size: 18px; margin-bottom: 20px;">안녕하세요!</p>
            <p>요청하신 임시 비밀번호를 안내해드립니다.</p>
            
            <div class="password-box">
                <div style="color: #666; font-size: 14px; margin-bottom: 10px;">임시 비밀번호</div>
                <div class="password">{temp_password}</div>
            </div>
            
            <div class="warning">
                <strong>⚠️ 보안 주의사항</strong><br>
                • 로그인 후 <strong>반드시 비밀번호를 변경</strong>해주세요<br>
                • 임시 비밀번호는 타인에게 공유하지 마세요<br>
                • 본인이 요청하지 않았다면 contact@repost.kr로 문의해주세요
            </div>
            
            <div style="text-align: center;">
                <a href="https://repost.kr/login-page" class="button">로그인하기 →</a>
            </div>
        </div>
        <div class="footer">
            <p>© 2026 Repost. All rights reserved.</p>
            <p>1만 명의 블로거가 선택한 AI 글쓰기 플랫폼</p>
        </div>
    </div>
</body>
</html>
            """
        }
        
        response = resend.Emails.send(params)
        print(f"✅ 임시 비밀번호 발송 성공: {to_email}")
        return True
    
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {e}")
        # 개발 모드에서는 콘솔에 출력
        print(f"\n{'='*50}")
        print(f"📧 임시 비밀번호 (개발 모드)")
        print(f"이메일: {to_email}")
        print(f"임시 비밀번호: {temp_password}")
        print(f"{'='*50}\n")
        return False

def send_welcome_email(to_email, name):
    """환영 이메일 발송"""
    try:
        params = {
            "from": FROM_EMAIL,
            "to": to_email,
            "subject": "[Repost] 가입을 환영합니다! 🎉",
            "html": f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
        .header {{ text-align: center; padding: 40px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px 20px 0 0; }}
        .header h1 {{ color: white; margin: 0; font-size: 32px; }}
        .content {{ background: white; padding: 40px; border-radius: 0 0 20px 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .feature {{ background: #f8f9fa; padding: 20px; border-radius: 12px; margin: 15px 0; }}
        .feature-icon {{ font-size: 32px; margin-bottom: 10px; }}
        .button {{ display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 12px; font-weight: bold; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 30px; color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 환영합니다!</h1>
        </div>
        <div class="content">
            <p style="font-size: 20px; margin-bottom: 20px;">안녕하세요, <strong>{name}</strong>님!</p>
            <p>Repost 가입을 진심으로 환영합니다.</p>
            <p>1만 명의 블로거가 선택한 AI 글쓰기 플랫폼에서 최고의 경험을 누려보세요!</p>
            
            <div style="margin: 30px 0;">
                <div class="feature">
                    <div class="feature-icon">📊</div>
                    <strong>실시간 텍스트 분석</strong><br>
                    <span style="color: #666;">글의 가독성, 감정, 키워드를 실시간 분석</span>
                </div>
                
                <div class="feature">
                    <div class="feature-icon">💡</div>
                    <strong>AI 제목 생성</strong><br>
                    <span style="color: #666;">클릭률 높은 매력적인 제목 자동 생성</span>
                </div>
                
                <div class="feature">
                    <div class="feature-icon">🎯</div>
                    <strong>SEO 최적화</strong><br>
                    <span style="color: #666;">검색 엔진 상위 노출을 위한 완벽 분석</span>
                </div>
            </div>
            
            <div style="text-align: center;">
                <a href="https://repost.kr/tools" class="button">도구 사용하기 →</a>
            </div>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px;">
                궁금한 점이 있으시면 언제든지 contact@repost.kr로 문의해주세요!
            </p>
        </div>
        <div class="footer">
            <p>© 2026 Repost. All rights reserved.</p>
            <p>1만 명의 블로거가 선택한 AI 글쓰기 플랫폼</p>
        </div>
    </div>
</body>
</html>
            """
        }
        
        response = resend.Emails.send(params)
        print(f"✅ 환영 이메일 발송 성공: {to_email}")
        return True
    
    except Exception as e:
        print(f"❌ 환영 이메일 발송 실패: {e}")
        return False

