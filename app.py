from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app)

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None

def scrape_blog_content(url):
    """네이버 블로그 내용 스크래핑"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 네이버 블로그의 iframe 구조 처리
        if 'blog.naver.com' in url:
            # iframe 내용이 있는 경우
            blog_id = url.split('blog.naver.com/')[1].split('/')[0] if 'blog.naver.com/' in url else None
            log_no = url.split('/')[-1] if '/' in url else None
            
            if blog_id and log_no:
                # 실제 콘텐츠 URL
                content_url = f'https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}'
                response = requests.get(content_url, headers=headers, timeout=10)
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
    """OpenAI를 사용하여 블로그 내용 기반 댓글 생성"""
    try:
        if not client:
            print("❌ OpenAI API 키가 설정되지 않았습니다!")
            return None
        
        # 블로그 내용 요약 (너무 길면 잘라내기)
        content_preview = content[:500] if len(content) > 500 else content
        
        prompt = f"""다음은 네이버 블로그 글입니다. 이 글을 실제로 읽은 사람처럼 자연스러운 댓글 8개를 한국어로 작성해주세요.

블로그 제목: {title}
블로그 내용: {content_preview}

요구사항:
1. 실제 블로그 내용을 구체적으로 언급하는 댓글
2. 자연스럽고 친근한 톤
3. 이모지 적절히 사용
4. 길이: 짧은 댓글 5개(10-25자), 긴 댓글 3개(30-50자)
5. 스팸처럼 보이지 않는 진심 어린 댓글
6. 각 댓글은 서로 다른 스타일로

JSON 형식으로 응답:
{{"comments": ["댓글1", "댓글2", ...]}}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 블로그 댓글을 작성하는 친근한 한국인입니다. 자연스럽고 진심 어린 댓글을 작성합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        return result.get('comments', [])
    
    except Exception as e:
        print(f"AI 댓글 생성 실패: {e}")
        return None

def generate_comments(blog_data):
    """블로그 내용을 기반으로 댓글 추천 생성 (AI 우선, 실패시 기본 로직)"""
    title = blog_data['title']
    content = blog_data['content']
    
    # AI 댓글 생성 시도
    ai_comments = generate_comments_with_ai(title, content)
    if ai_comments and len(ai_comments) >= 5:
        print("✅ AI 댓글 생성 성공!")
        return ai_comments[:8]  # 최대 8개
    
    print("⚠️ AI 댓글 생성 실패 - 기본 템플릿 사용")
    
    # AI 실패시 기본 로직 사용
    comments = []
    text = (title + ' ' + content).lower()
    
    # 제목에서 핵심 키워드 추출 (명사형 단어들)
    title_words = [word for word in title.split() if len(word) > 1]
    
    # 상세 키워드 기반 맞춤형 댓글
    keyword_patterns = {
        # 맛집 관련
        ('맛집', '음식점', '카페', '레스토랑', '식당'): [
            f'{title_words[0] if title_words else "여기"} 정말 가보고 싶네요! 상세한 후기 감사합니다 😊',
            f'와 {title_words[0] if title_words else "이곳"} 분위기 좋아보이네요! 다음에 꼭 방문해볼게요!',
            '메뉴 구성이 정말 괜찮아 보이네요! 리뷰 보고 가고 싶어졌어요 👍',
            '사진만 봐도 맛있어 보이네요! 상세한 리뷰 너무 감사합니다!',
        ],
        ('맛있', '맛나', '맛집', '먹', '음식'): [
            '포스팅 보니까 정말 맛있어 보이네요! 꼭 가봐야겠어요!',
            '이렇게 자세한 리뷰 남겨주셔서 감사해요! 메뉴 선택에 도움이 많이 됐어요!',
            '사진 보니까 침이 고이네요 ㅎㅎ 좋은 정보 감사합니다!',
        ],
        
        # 여행 관련
        ('여행', '관광', '여행지', '투어'): [
            f'{title_words[0] if title_words else "여기"} 여행 계획 중인데 정말 유용한 정보네요!',
            '여행 코스 참고하겠습니다! 자세한 후기 너무 좋아요 ✈️',
            '사진 보니까 정말 가고 싶네요! 일정 짤 때 참고할게요!',
            '이런 숨은 명소가 있었다니! 포스팅 감사합니다!',
        ],
        ('힐링', '휴양', '휴가', '쉼', '풍경'): [
            '힐링 제대로 되겠어요! 저도 꼭 가보고 싶네요 🌿',
            '풍경이 정말 아름답네요! 좋은 곳 공유해주셔서 감사해요!',
        ],
        
        # 제품 리뷰/후기
        ('후기', '리뷰', '사용기', '체험'): [
            '솔직한 후기 너무 감사합니다! 구매 결정하는데 큰 도움이 됐어요!',
            '이런 상세한 리뷰 찾고 있었는데 딱이네요! 감사합니다 👏',
            '장단점을 잘 정리해주셔서 이해하기 쉬웠어요! 좋은 정보 감사합니다!',
            '실사용 후기라서 더 신뢰가 가네요! 포스팅 감사드려요!',
        ],
        ('추천', '강추', '인정', '좋'): [
            '추천해주신 내용 꼼꼼히 읽어봤어요! 정말 도움이 많이 됐습니다!',
            '이렇게 자세히 알려주시니 고민이 해결됐어요! 감사합니다!',
        ],
        
        # 정보성 글
        ('정보', '팁', 'tip', '방법', '노하우'): [
            '유익한 정보 공유해주셔서 감사합니다! 바로 적용해볼게요!',
            '이런 꿀팁이! 포스팅 보고 많이 배웠어요 👍',
            '정말 필요한 정보였는데 감사합니다! 저장해뒀어요!',
            '자세한 설명 덕분에 이해가 쏙쏙 되네요! 감사해요!',
        ],
        
        # 레시피/요리
        ('레시피', '요리', '만들', '조리'): [
            '레시피 너무 자세해서 좋아요! 저도 만들어봐야겠어요 🍳',
            '이렇게 간단하게 만들 수 있다니! 주말에 도전해볼게요!',
            '사진이랑 설명이 너무 잘 되어있어서 따라하기 쉬울 것 같아요!',
        ],
        
        # 일상/공감
        ('일상', '하루', '오늘', '요즘'): [
            '공감가는 내용이 많네요! 잘 읽고 갑니다 😊',
            '저도 비슷한 경험이 있어서 더 공감이 가네요!',
        ],
        
        # 뷰티/패션
        ('화장', '메이크업', '뷰티', '코스메틱', '스킨케어'): [
            '제품 정보 너무 상세하게 알려주셔서 감사해요! 구매 리스트에 추가했어요!',
            '사용 후기가 궁금했는데 딱 원하던 정보네요! 감사합니다 💄',
        ],
        ('패션', '옷', '코디', '스타일'): [
            '스타일링 센스가 너무 좋으세요! 참고할게요 👗',
        ],
        
        # 육아/교육
        ('육아', '아이', '아기', '엄마', '교육'): [
            '육아 정보 너무 유익해요! 저도 적용해봐야겠어요!',
            '같은 고민 하고 있었는데 도움이 많이 됐어요! 감사합니다!',
        ],
        
        # 운동/건강
        ('운동', '헬스', '다이어트', '건강', '피트니스'): [
            '운동 루틴 참고하겠습니다! 동기부여 받고 가요 💪',
            '자세한 운동 방법 알려주셔서 감사해요! 따라해볼게요!',
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

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_blog():
    """블로그 분석 및 댓글 추천 API"""
    try:
        data = request.json
        blog_url = data.get('url', '').strip()
        
        if not blog_url:
            return jsonify({'error': 'URL을 입력해주세요.'}), 400
        
        # 블로그 내용 스크래핑
        blog_data = scrape_blog_content(blog_url)
        
        # 댓글 생성
        comments = generate_comments(blog_data)
        
        return jsonify({
            'success': True,
            'blog': blog_data,
            'comments': comments
        })
    
    except Exception as e:
        return jsonify({'error': f'오류가 발생했습니다: {str(e)}'}), 500

if __name__ == '__main__':
    # 로컬 개발용
    app.run(debug=True, port=5001)

