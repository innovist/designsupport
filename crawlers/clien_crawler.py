import pandas as pd
import time
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

# from crawlers.common import save_to_json, is_date_in_range, filter_by_date_range
# from crawlers.network_utils import NetworkUtils

from common import save_to_json, is_date_in_range, filter_by_date_range
from network_utils import NetworkUtils

# --- 설정 ---
CONTENT_COLUMNS = ['id', 'title', 'content', 'published_date', 'platform', 'link', 'view_count', 'like_count', 'smp_method', 'smp_score', 'inf_type', 'cls_id']
COMMENT_COLUMNS = ['id', 'blog_id', 'content', 'published_date', 'parent_id', 'like_count', 'platform']
OUTPUT_DIR = 'crawling_data'
BASE_URL = "https://www.clien.net/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Cache-Control': 'max-age=0'
}


class ClienCrawler:
    """클리앙 크롤러 클래스"""

    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS

    def run(self, keyword, max_posts=None, start_date=None, end_date=None):
        """크롤러 실행 메인 메서드"""
        all_posts = []
        all_comments = []

        try:
            post_urls = get_post_urls(keyword, start_date, end_date, max_posts)
            print(f"\n총 {len(post_urls)}개의 게시물을 대상으로 스크래핑을 시작합니다.")

            for i, url in enumerate(post_urls):
                print(f"({i+1}/{len(post_urls)}) 스크래핑 중: {url}")
                post, comments = get_post_and_comment_data(url, start_date, end_date)
                if post:
                    all_posts.append(post)
                    save_to_json("Clien", [post], comments)
                if comments:
                    all_comments.extend(comments)
                time.sleep(0.5)

        except Exception as e:
            print(f"크롤링 중 오류가 발생했습니다: {e}")

        return all_posts, all_comments


# --- 데이터 스크래핑 ---
def get_post_urls(keyword, start_date, end_date, max_posts=None):
    """클리앙 통합검색을 사용하여 키워드가 포함된 게시물 URL을 수집합니다."""
    urls = []
    duplicate_count = 0
    start_time = time.time()
    max_time_seconds = 3600  # 1시간 제한
    
    print(f"🔍 클리앙 통합검색 시작 (최대 게시물: {'무제한' if max_posts is None else max_posts}개)")
    print(f"검색 키워드: '{keyword}'")
    
    page = 0
    empty_pages = 0
    max_empty_pages = 3  # 연속으로 빈 페이지가 3개 나오면 중단
    no_new_urls_count = 0  # 새로운 URL이 추가되지 않은 페이지 수
    max_no_new_pages = 5   # 연속으로 새로운 URL이 없으면 중단
    
    while True:
        # 시간 제한 확인
        elapsed_time = time.time() - start_time
        if elapsed_time > max_time_seconds:
            print(f"⏰ 시간 제한 도달 ({elapsed_time/60:.1f}분)")
            break
        
        # 최대 게시물 수 확인
        if max_posts and len(urls) >= max_posts:
            print(f"📊 최대 게시물 수 도달 ({len(urls)}개)")
            break
        
        # 연속 빈 페이지 확인
        if empty_pages >= max_empty_pages:
            print(f"🔚 연속 {max_empty_pages}개 빈 페이지로 검색 종료")
            break
            
        # 연속으로 새로운 URL이 없는 페이지 확인
        if no_new_urls_count >= max_no_new_pages:
            print(f"🔄 연속 {max_no_new_pages}개 페이지에서 새로운 URL 없음으로 검색 종료")
            break
        
        print(f"\n📋 검색 페이지 {page + 1} 탐색 중...")
        
        # 통합검색 URL 구성
        search_url = f"{BASE_URL}service/search"
        params = {
            'q': keyword,
            'p': page  # 페이지 번호
        }
        
        # 날짜 범위가 지정된 경우 추가 (클리앙에서 지원하는지 확인 필요)
        if start_date and end_date:
            params['startDate'] = start_date
            params['endDate'] = end_date
        
        try:
            response = NetworkUtils.safe_request(search_url, params=params, headers=HEADERS, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"❌ 검색 요청 중 오류: {e}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 게시글 링크 찾기
        page_posts = []
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # 게시글 패턴 확인: /service/board/게시판명/숫자
            if '/service/board/' in href and re.search(r'/service/board/[^/]+/\d+', href):
                # URL 정리
                clean_url = href.split('?')[0].split('#')[0]
                if not clean_url.startswith('http'):
                    clean_url = BASE_URL.rstrip('/') + clean_url
                
                # 키워드가 제목에 포함된지 확인 (통합검색 결과이므로 이미 관련성이 높음)
                if keyword in text and text and len(text) > 3:
                    if not any(x in href for x in ['#comment', 'javascript']):
                        if clean_url not in page_posts:  # 페이지 내 중복 제거
                            page_posts.append(clean_url)
        
        # 페이지 결과 처리
        if not page_posts:
            empty_pages += 1
            no_new_urls_count += 1  # 새로운 URL도 없음
            print(f"    페이지 {page + 1}: 게시글 없음 (빈 페이지 {empty_pages}/{max_empty_pages})")
        else:
            empty_pages = 0  # 결과가 있으면 빈 페이지 카운터 리셋
            
            # 전체 목록에 추가 (중복 제거)
            before_count = len(urls)
            urls.extend(page_posts)
            urls = list(dict.fromkeys(urls))  # 중복 제거
            after_count = len(urls)
            
            new_count = after_count - before_count
            duplicates_found = len(page_posts) - new_count
            duplicate_count += duplicates_found
            
            # 새로운 URL이 있는지 확인
            if new_count > 0:
                no_new_urls_count = 0  # 새로운 URL이 있으면 리셋
            else:
                no_new_urls_count += 1  # 모두 중복이면 카운터 증가
            
            print(f"    페이지 {page + 1}: {len(page_posts)}개 발견 ({new_count}개 신규, {duplicates_found}개 중복)")
            
            # 발견된 게시글 정보 출력 (상위 3개)
            for i, url in enumerate(page_posts[:3], 1):
                board_id = url.split('/')[5] if len(url.split('/')) > 5 else 'unknown'
                print(f"      {i}. [{board_id}] {url}")
        
        page += 1
        time.sleep(0.5)  # 페이지간 간격
    
    final_time = time.time() - start_time
    print(f"✅ URL 수집 완료: {len(urls)}개 (소요시간: {final_time/60:.1f}분, 중복제거: {duplicate_count}개)")
    print(f"   검색된 페이지: {page}개, 빈 페이지: {empty_pages}개, 중복만 있던 페이지: {no_new_urls_count}개")
    
    return urls if max_posts is None else urls[:max_posts]


def get_post_and_comment_data(post_url, start_date=None, end_date=None):
    """개별 게시물과 댓글 내용을 스크래핑합니다."""
    try:
        response = NetworkUtils.safe_request(post_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"게시물 요청 중 오류 발생: {e}")
        return None, []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    post_data = {}
    comments_data = []

    # --- 게시물 정보 추출 ---
    # URL에서 게시글 ID 추출
    post_id_match = re.search(r'/service/board/[^/]+/(\d+)', post_url)
    post_id = post_id_match.group(1) if post_id_match else datetime.now().strftime('%Y%m%d%H%M%S%f')
    
    # 제목 - 클리앙 구조에 맞는 선택자
    title = soup.select_one('h3.subject_fixed, h3.subject, .post_title')
    if not title:
        title = soup.select_one('h3, h2, h1')
    
    # 내용 - 클리앙의 게시글 본문
    content = soup.select_one('.post_article')
    if not content:
        # 대체 선택자 시도
        content = soup.select_one('.post_content, .article_content, .content')
        if not content:
            # div 중에서 충분한 텍스트가 있는 것 찾기
            divs = soup.find_all('div')
            for div in divs:
                text = div.get_text(strip=True)
                if text and len(text) > 100 and '클리앙' not in text[:50]:
                    content = div
                    break
    
    # 날짜 - 클리앙의 날짜 표시 형식
    date_elem = soup.select_one('.date')
    if not date_elem:
        date_elem = soup.select_one('.timestamp, [class*="date"], [class*="time"]')

    post_data['id'] = post_id
    post_data['link'] = post_url
    post_data['title'] = title.get_text(strip=True) if title else "제목 없음"
    post_data['content'] = content.get_text(strip=True) if content else "내용 없음"
    
    # 날짜 처리
    if date_elem:
        date_text = date_elem.get_text(strip=True)
        # 클리앙 날짜 형식 처리 (예: "2025-08-05 16:25:57수정일 : 2025-08-05 16:27:53")
        date_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', date_text)
        post_data['published_date'] = date_match.group(1) if date_match else date_text.split('수정일')[0].strip()
    else:
        post_data['published_date'] = None
        
    post_data['platform'] = 'Clien'
    
    

    # --- 댓글 정보 추출 ---
    # 클리앙 댓글 구조
    comments = soup.select('.comment_content')
    for i, comment in enumerate(comments):
        comment_id = f"{post_id}_{i+1}"
        
        # 댓글 날짜 찾기
        comment_date = None
        parent_elem = comment.find_parent()
        if parent_elem:
            timestamp = parent_elem.select_one('.timestamp')
            if timestamp:
                comment_date = timestamp.get_text(strip=True)
        
        comments_data.append({
            'id': comment_id,
            'blog_id': post_id,
            'content': comment.get_text(strip=True) if comment else "",
            'published_date': comment_date,
            'parent_id': None,  # 클리앙 대댓글 구조 분석 필요시 추가
            'platform': 'Clien'
        })

    # 날짜 필터링 적용 - 엄격한 날짜 필터링
    if start_date and end_date and not is_date_in_range(post_data.get('published_date'), start_date, end_date):
        print(f"  [날짜필터링] 제외된 게시물: {post_data.get('published_date')} (범위: {start_date}~{end_date})")
        return None, []
    
    # 댓글도 날짜 필터링
    filtered_comments = filter_by_date_range(comments_data, 'published_date', start_date, end_date)
    

    return post_data, filtered_comments



# --- 데이터 저장 ---
def save_data(posts, comments):
    """수집된 데이터를 TSV 파일로 저장합니다."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if posts:
        posts_df = pd.DataFrame(posts)
        for col in CONTENT_COLUMNS:
            if col not in posts_df.columns:
                posts_df[col] = None
        posts_df = posts_df.reindex(columns=CONTENT_COLUMNS)
        posts_filename = os.path.join(OUTPUT_DIR, f"{timestamp}_clien_contents.tsv")
        posts_df.to_csv(posts_filename, sep='\t', index=False, encoding='utf-8-sig')
        print(f"게시글 데이터 저장 완료: {posts_filename}")
    else:
        print("저장할 게시글 데이터가 없습니다.")

    if comments:
        comments_df = pd.DataFrame(comments)
        for col in COMMENT_COLUMNS:
            if col not in comments_df.columns:
                comments_df[col] = None
        comments_df = comments_df.reindex(columns=COMMENT_COLUMNS)
        comments_filename = os.path.join(OUTPUT_DIR, f"{timestamp}_clien_comments.tsv")
        comments_df.to_csv(comments_filename, sep='\t', index=False, encoding='utf-8-sig')
        print(f"댓글 데이터 저장 완료: {comments_filename}")
    else:
        print("저장할 댓글 데이터가 없습니다.")

# --- 메인 실행 ---
def main():
    """메인 실행 함수"""

    crawler = ClienCrawler()
    crawler.run("아이온", max_posts=20, start_date=None, end_date=None)

    


if __name__ == "__main__":
    main()