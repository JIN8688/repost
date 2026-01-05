"""
데이터베이스 초기화 스크립트
실행: python init_db.py
"""
import os
from dotenv import load_dotenv
from database import db

def main():
    print("🗄️  Neon PostgreSQL 데이터베이스 초기화 중...")
    
    # .env 파일 로드
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL이 설정되지 않았습니다!")
        print("📝 .env 파일을 생성하고 DATABASE_URL을 추가해주세요.")
        print("예시: DATABASE_URL=postgresql://user:password@host/database?sslmode=require")
        return
    
    print(f"📍 연결 중: {database_url[:50]}...")
    
    try:
        # 테이블 생성
        db.init_tables()
        print("✅ 데이터베이스 테이블이 성공적으로 생성되었습니다!")
        print("\n📊 생성된 테이블:")
        print("  - users: 사용자 정보")
        print("  - usage_history: 사용 기록")
        print("\n🎉 초기화 완료! 이제 앱을 실행할 수 있습니다.")
        print("실행 명령: python app.py")
    
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")
        print("\n💡 해결 방법:")
        print("1. DATABASE_URL이 올바른지 확인")
        print("2. Neon 대시보드에서 데이터베이스가 활성화되어 있는지 확인")
        print("3. 네트워크 연결 확인")

if __name__ == '__main__':
    main()

