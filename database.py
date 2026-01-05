"""
Neon PostgreSQL 데이터베이스 연결 및 사용자 관리
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.connection_string = os.getenv('DATABASE_URL')
        
    def get_connection(self):
        """데이터베이스 연결 가져오기"""
        return psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)
    
    def init_tables(self):
        """테이블 초기화"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        # 사용자 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                name VARCHAR(100) NOT NULL,
                plan VARCHAR(20) DEFAULT 'free',
                marketing_consent BOOLEAN DEFAULT FALSE,
                oauth_provider VARCHAR(20),
                oauth_id VARCHAR(255),
                profile_image VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # 사용 기록 테이블
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usage_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                action_type VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB
            )
        """)
        
        # 인덱스 생성
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_oauth ON users(oauth_provider, oauth_id);
            CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_history(user_id);
        """)
        
        conn.commit()
        cur.close()
        conn.close()
    
    def create_user(self, email, password, name, marketing_consent=False, oauth_provider=None, oauth_id=None, profile_image=None):
        """사용자 생성"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            # 비밀번호 해시화 (OAuth가 아닌 경우만)
            password_hash = None
            if password:
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cur.execute("""
                INSERT INTO users (email, password_hash, name, marketing_consent, oauth_provider, oauth_id, profile_image)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, email, name, plan, created_at
            """, (email, password_hash, name, marketing_consent, oauth_provider, oauth_id, profile_image))
            
            user = cur.fetchone()
            conn.commit()
            return dict(user)
        except psycopg2.IntegrityError:
            conn.rollback()
            return None
        finally:
            cur.close()
            conn.close()
    
    def verify_user(self, email, password):
        """사용자 인증"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, email, password_hash, name, plan, profile_image
            FROM users
            WHERE email = %s AND is_active = TRUE
        """, (email,))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user or not user['password_hash']:
            return None
        
        # 비밀번호 검증
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            user_dict = dict(user)
            del user_dict['password_hash']  # 비밀번호 해시는 반환하지 않음
            return user_dict
        
        return None
    
    def get_user_by_email(self, email):
        """이메일로 사용자 조회"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, email, name, plan, profile_image, oauth_provider, created_at
            FROM users
            WHERE email = %s AND is_active = TRUE
        """, (email,))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        return dict(user) if user else None
    
    def get_user_by_oauth(self, oauth_provider, oauth_id):
        """OAuth로 사용자 조회"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, email, name, plan, profile_image, oauth_provider, created_at
            FROM users
            WHERE oauth_provider = %s AND oauth_id = %s AND is_active = TRUE
        """, (oauth_provider, oauth_id))
        
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        return dict(user) if user else None
    
    def update_last_login(self, user_id):
        """마지막 로그인 시간 업데이트"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE users
            SET last_login = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (user_id,))
        
        conn.commit()
        cur.close()
        conn.close()
    
    def log_usage(self, user_id, action_type, metadata=None):
        """사용 기록 저장"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        import json
        metadata_json = json.dumps(metadata) if metadata else None
        
        cur.execute("""
            INSERT INTO usage_history (user_id, action_type, metadata)
            VALUES (%s, %s, %s)
        """, (user_id, action_type, metadata_json))
        
        conn.commit()
        cur.close()
        conn.close()
    
    def get_usage_count(self, user_id, action_type, days=30):
        """사용 횟수 조회"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT COUNT(*)
            FROM usage_history
            WHERE user_id = %s 
            AND action_type = %s
            AND created_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
        """, (user_id, action_type, days))
        
        count = cur.fetchone()['count']
        cur.close()
        conn.close()
        
        return count

# 전역 데이터베이스 인스턴스
db = Database()

