#!/usr/bin/env python3
"""
도구 페이지들의 HTML 파일에서 인라인 CSS/JS를 제거하고 외부 파일로 연결하는 스크립트
"""
import re
import os

# 리팩토링할 파일 목록
files_to_refactor = [
    'text-analyzer.html',
    'ai-writer.html',
    'seo-checker.html',
    'title-generator.html',
    'keyword-recommender.html'
]

templates_dir = 'templates'

for filename in files_to_refactor:
    filepath = os.path.join(templates_dir, filename)
    
    if not os.path.exists(filepath):
        print(f"❌ {filename} not found")
        continue
    
    print(f"🔧 Processing {filename}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # <style> 태그 제거
    content = re.sub(r'    <style>.*?</style>\n', '', content, flags=re.DOTALL)
    
    # </head> 앞에 CSS 링크 추가
    css_filename = filename.replace('.html', '.css')
    css_links = f'''    <!-- 🎨 CSS 파일 -->
    <link rel="stylesheet" href="{{{{ url_for('static', filename='css/common.css') }}}}">
    <link rel="stylesheet" href="{{{{ url_for('static', filename='css/{css_filename}') }}}}">
'''
    content = content.replace('</head>', f'{css_links}</head>')
    
    # <script> 태그 제거 (단, Chart.js 등 외부 스크립트는 유지)
    # body 태그 안의 마지막 script만 제거
    content = re.sub(r'    <script>\n(.*?)\n    </script>\n</body>', r'</body>', content, flags=re.DOTALL)
    
    # </body> 앞에 JS 링크 추가
    js_filename = filename.replace('.html', '.js')
    js_links = f'''    
    <!-- 🚀 JavaScript 파일 -->
    <script src="{{{{ url_for('static', filename='js/common.js') }}}}"></script>
    <script src="{{{{ url_for('static', filename='js/{js_filename}') }}}}"></script>
</body>'''
    content = content.replace('</body>', js_links)
    
    # 파일 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {filename} refactored successfully")

print("\n🎉 All files refactored!")

