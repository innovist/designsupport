import pandas as pd
import time
import os
import re
import random
import sys
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from crawlers.common import extract_numbers, add_today_if_time_only, save_to_json, is_date_in_range, filter_by_date_range
from crawlers.network_utils import NetworkUtils

# date_utils 임포트
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'utils'))
try:
    from date_utils import parse_relative_time
except ImportError:
    parse_relative_time = None

# --- 설정 ---
# TSV 파일 헤더 정의 (샘플 파일 기반)
CONTENT_COLUMNS = ['id', 'title', 'content', 'published_date', 'platform', 'link', 'view_count', 'like_count', 'smp_method', 'smp_score', 'inf_type', 'cls_id']
COMMENT_COLUMNS = ['id', 'blog_id', 'content', 'published_date', 'parent_id', 'like_count', 'platform']
OUTPUT_DIR = 'crawling_data'
BASE_URL = "https://www.ppomppu.co.kr/"


class PpomppuCrawler:
    """뽐뿌 크롤러 클래스"""

    def __init__(self):
        self.base_url = BASE_URL

    def run(self, keyword, max_posts=None, start_date=None, end_date=None):
        """크롤러 실행 메인 메서드"""
        all_posts = []
        all_comments = []

        # try:
        post_urls = get_post_urls(keyword, start_date, end_date, max_posts)
        print(f"\n총 {len(post_urls)}개의 게시물을 대상으로 스크래핑을 시작합니다.")

        for i, url in enumerate(post_urls):
            print(f"({i+1}/{len(post_urls)}) 스크래핑 중: {url}")
            post, comments = get_post_and_comment_data(url, start_date, end_date)
            print("post: ", post)
            if post:
                all_posts.append(post)
                save_to_json("Ppomppu", [post], comments)
            if comments:
                all_comments.extend(comments)
            time.sleep(0.5)

        # except Exception as e:
        #     print(f"크롤링 중 오류가 발생했습니다: {e}")

        return all_posts, all_comments


# --- 데이터 스크래핑 ---
def get_post_urls(keyword, start_date, end_date, max_posts=None):
    """뽐뿌 검색 결과에서 게시물 URL을 수집합니다. (개선된 지능적 종료 조건)"""
    urls = []
    page = 1
    empty_page_count = 0
    max_empty_pages = 5   # 연속 빈 페이지 제한
    consecutive_old_pages = 0
    max_old_pages = 15    # 연속 15페이지가 모두 목표 범위보다 오래되면 종료 (지능적 중단)
    duplicate_count = 0
    start_time = time.time()
    max_time_seconds = 3600  # 1시간 제한
    consecutive_failures = 0
    max_consecutive_failures = 3  # 연속 실패 3회 시 중단
    
    # 뽐뿌는 날짜 형식을 YYYY-MM-DD로 사용
    s_date = start_date
    e_date = end_date
    
    print(f"🔍 뽐뿌 검색 시작 (최대 게시물: {'무제한' if max_posts is None else max_posts}개)")

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

        # 검색어 인코딩 (EUC-KR)
        try:
            encoded_keyword = requests.utils.quote(keyword, encoding='EUC-KR')
        except:
            encoded_keyword = requests.utils.quote(keyword)

        # 뽐뿌 통합검색 URL - 올바른 페이지네이션 구조 (order_type=date로 최신순)
        search_url = f"{BASE_URL}search_bbs.php?search_type=sub_memo&page_no={page}&keyword={encoded_keyword}&page_size=20&bbs_id=&order_type=date&bbs_cate=2"
        print("search_url: ", search_url)
        
        try:
            # Rate limiting - 요청 간 랜덤 지연
            time.sleep(random.uniform(1.0, 2.5))
            
            response = NetworkUtils.safe_request(search_url, timeout=15)
            response.encoding = 'EUC-KR'  # 뽐뿌는 EUC-KR 인코딩 사용
            response.raise_for_status()
        except Exception as e:
            print(f"❌ URL 요청 중 오류 발생: {e}")
            consecutive_failures += 1
            if consecutive_failures >= max_consecutive_failures:
                print(f"❌ 연속 실패 {max_consecutive_failures}회 도달, 크롤링 중단")
                break
            time.sleep(2 * consecutive_failures)  # 실패 횟수만큼 대기 시간 증가
            continue

        # 성공하면 연속 실패 카운터 리셋
        consecutive_failures = 0
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 통합검색 결과에서 게시물 링크 추출 - 모든 게시판 포함
        post_links = soup.select('span.title > a')

        
        if not post_links:
            empty_page_count += 1
            break
        else:
            empty_page_count = 0  # 리셋

        new_urls = []
        for link in post_links:
            new_urls.append(f"{BASE_URL}{link.get('href')[1:]}")
        # 중복 URL 확인
        print("new_urls: ", new_urls)
        before_count = len(urls)
        urls.extend(new_urls)
        urls = list(dict.fromkeys(urls))  # 중복 제거
        after_count = len(urls)
        
        duplicates_found = len(new_urls) - (after_count - before_count)
        duplicate_count += duplicates_found
        
        # 중복 비율 확인 (20개 이상 수집한 후)
        if len(urls) > 20 and new_urls:
            duplicate_ratio = duplicates_found / len(new_urls)
            if duplicate_ratio >= 0.7:
                print(f"🔄 중복 URL 비율 높음 ({duplicate_ratio:.1%})")
                break
        
        print(f"📄 페이지 {page}: {len(new_urls)}개 수집 (총 {len(urls)}개, 중복 {duplicates_found}개)")
        
        page += 1
        
        # 극단적 페이지 제한 (안전장치)
        if page > 200:  # 뽐뿌 특성상 높은 제한
            print("⚠️ 안전장치: 페이지 200 도달")
            break

    final_time = time.time() - start_time
    print(f"✅ URL 수집 완료: {len(urls)}개 (소요시간: {final_time/60:.1f}분, 중복제거: {duplicate_count}개)")
    
    return urls if max_posts is None else urls[:max_posts]


def get_post_and_comment_data(post_url, start_date=None, end_date=None):
    """개별 게시물과 댓글 내용을 스크래핑합니다."""
    try:
        response = NetworkUtils.safe_request(post_url, timeout=15)
        response.encoding = 'EUC-KR'  # 뽐뿌는 EUC-KR 인코딩 사용
        response.raise_for_status()
    except Exception as e:
        print(f"게시물 요청 중 오류 발생: {e}")
        return None, []

    
    # print("response: ", response.text)
    # with open("response.html", "w", encoding="utf-8") as f:
    #     f.write(response.text)
    soup = BeautifulSoup(response.text, 'lxml')
    
    
    post_data = {}
    comments_data = []

    # --- 게시물 정보 추출 ---
    post_id_match = re.search(r'no=(\d+)', post_url)
    post_id = post_id_match.group(1) if post_id_match else datetime.now().strftime('%Y%m%d%H%M%S%f')
    
    # 제목 - 실제 뽐뿌 구조에 맞는 선택자
    title = soup.select_one('h1')
    if not title:
        title = soup.select_one('.view_title, .view_title2, .title')
    
    # 내용 - 테이블에서 실제 게시글 내용 추출
    content = None

    content = soup.select_one(".board-contents").text.strip()
    

    content = soup.select_one(".board-contents").text.strip()
    content = content.replace("\n", " ")
    content = content.split()
    
    content = ' '.join(content)
    content = content.replace("Your browser does not support the video tag", "")
    
    # 날짜 - 뽐뿌는 다양한 형태로 날짜 표시, Copyright 메시지 제외
    date_elem = soup.select_one('.sub-info-text, .date, .info')
    published_date = None
    
    if not date_elem:
        # 테이블에서 날짜 형태 텍스트 찾기 (Copyright 제외)
        tables = soup.find_all('table')
        for table in tables:
            tds = table.find_all('td')
            for td in tds:
                text = td.get_text(strip=True)
                if (re.search(r'\d{4}[-./]\d{1,2}[-./]\d{1,2}', text) and 
                    'Copyright' not in text and 'ppomppu' not in text.lower()):
                    date_elem = td
                    break

    post_data['id'] = post_id
    post_data['link'] = post_url
    post_data['title'] = title.get_text(strip=True) if title else "제목 없음"
    post_data['content'] = content
    
    if date_elem:
        date_text = date_elem.get_text(strip=True)
        # Copyright 메시지가 포함된 경우 제외
        if 'Copyright' not in date_text and 'ppomppu' not in date_text.lower():
            # 다양한 날짜 형식 매칭
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})',  # 2025-08-05 16:30
                r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2})',  # 2025.08.05 16:30
                r'(\d{4}[-./]\d{1,2}[-./]\d{1,2})',   # 2025-08-05
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, date_text)
                if date_match:
                    published_date = date_match.group(1)
                    break


    # 날짜 추출 개선
    date_elem = soup.select_one("#topTitle > div > ul > li:nth-child(2)")
    if date_elem:
        date_text_original = date_elem.text.strip()

        # 1. 상대 날짜 처리 ("오늘", "어제" 등)
        if parse_relative_time and any(word in date_text_original for word in ['오늘', '어제', '그제', '일 전', '시간 전', '분 전', '주 전', '달 전', '개월 전']):
            parsed_dt = parse_relative_time(date_text_original)
            if parsed_dt:
                post_data['published_date'] = parsed_dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                post_data['published_date'] = ""
        else:
            # 2. 한글 제거 후 날짜 패턴 추출
            published_date = re.sub(r'[가-힣ㄱ-ㅎㅏ-ㅣ]+', '', date_text_original).strip()

            # 콜론만 남은 경우 또는 날짜 패턴이 없는 경우 (약관 등)
            if published_date in [':', ''] or not re.search(r'\d', published_date):
                # 원본 텍스트에서 날짜 패턴 재검색
                date_match = re.search(r'(\d{4}[-./]\d{1,2}[-./]\d{1,2}[\s\w]*\d{1,2}:\d{2})', date_text_original)
                if date_match:
                    post_data['published_date'] = add_today_if_time_only(date_match.group(1))
                else:
                    post_data['published_date'] = ""  # 날짜 없는 문서
            else:
                post_data['published_date'] = add_today_if_time_only(published_date)
    else:
        # 디버깅에서 찾은 날짜 패턴 사용
        all_text = soup.get_text()
        date_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', all_text)
        if date_match:
            post_data['published_date'] = date_match.group(1)
        else:
            post_data['published_date'] = ""  # 날짜 없는 문서
        
    post_data['platform'] = 'Ppomppu'
    

    # 조회수와 추천수 추출 (안전하게)
    like_elem = soup.select_one("#vote_list_btn_txt")
    post_data['like_count'] = like_elem.get_text(strip=True) if like_elem else "0"
    
    view_elem = soup.select_one("#topTitle > div > ul > li:nth-child(3)")
    if view_elem:
        view_text = view_elem.get_text(strip=True)
        view_numbers = extract_numbers(view_text)
        post_data['view_count'] = view_numbers[0] if view_numbers else 0
    else:
        post_data['view_count'] = 0
    

    # --- 댓글 정보 추출 ---
    # 뽐뿌는 테이블 기반 구조로, 실제 댓글과 시스템 메시지를 구분해야 함
    query = get_url_query(post_url)
    id = query["id"]
    no = query["no"]
    comments_data = get_comment(id, no)

    # 날짜 필터링 적용 - 엄격한 날짜 필터링
    if start_date and end_date and not is_date_in_range(post_data.get('published_date'), start_date, end_date):
        print(f"  [날짜필터링] 제외된 게시물: {post_data.get('published_date')} (범위: {start_date}~{end_date})")
        return None, []
    else:
        print(f"  [날짜필터링] ✅ 포함된 게시물: {post_data.get('published_date')}")
    
    # 댓글도 날짜 필터링
    filtered_comments = filter_by_date_range(comments_data, 'published_date', start_date, end_date)
    
    return post_data, filtered_comments

def get_url_query(url):
    query = url.split("?")[1]
    query = query.split("&")
    query = {q.split("=")[0]: q.split("=")[1] for q in query}
    return query
def request_get(url):
    response = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    })
    return response.text

def get_comment(id, no):
    comment_list = []
    url = f"https://www.ppomppu.co.kr/zboard/comment.php?id={id}&no={no}&c_page=1"
    html = request_get(url)
    soup = BeautifulSoup(html, "lxml")
    page_buttons = soup.select("#page_list > font > a")
    # text가 숫자이고 제일 큰 숫자 가져오기
    numbers = []
    for btn in page_buttons:
        text = btn.get_text(strip=True)
        if text.isdigit():
            numbers.append(int(text))
    max_number = max(numbers) if numbers else 1
    print(max_number)

    increment = 0
    
    for page in range(1, max_number + 1):
        url = f"https://www.ppomppu.co.kr/zboard/comment.php?id={id}&no={no}&c_page={page}"
        print("comments --> ", url)
        html = request_get(url)
        soup = BeautifulSoup(html, "lxml")
        comment_wrapper = soup.select(".comment_wrapper")
        for wrapper in comment_wrapper:
            comment = wrapper.select_one(".comment_template_depth1_vote")
            increment += 1
            comment_id = str(no)+"_"+str(increment)
            
            content = comment.select_one(".mid-text-area").text.strip()
            
            created_at = comment.select_one(".eng-day").text.strip()
            created_at = add_today_if_time_only(created_at)
            like_count = comment.select_one("[id^='vote_cnt_']").get_text(strip=True)
        
            reply_list = get_reply(wrapper, comment_id, no)
            
            
            comment_list.append({
                'id': comment_id,
                'blog_id': no,
                'content': content,
                'published_date': created_at,
                'parent_id': None,  # 뽐뿌는 대댓글 구조가 명확하지 않음
                'like_count': like_count,
                'platform': 'Ppomppu'
            })
            comment_list.extend(reply_list)
            
            # reply_list = self.get_reply(wrapper)
    
    return comment_list

def get_reply(comment_wrapper, comment_id, no):
    reply_list = []
    reply_wrapper = comment_wrapper.select_one(".comment_template_depth2_vote")

    if reply_wrapper:
        
        
        created_at = reply_wrapper.select_one(".eng-day").text.strip()
        created_at = add_today_if_time_only(created_at)
        content = reply_wrapper.select_one(".mid-text-area").text.strip()
        like_count = reply_wrapper.select_one("[id^='vote_cnt_']").get_text(strip=True)
        reply_list.append({
            'id': comment_id,
            'blog_id': no,
            'content': content,
            'published_date': created_at,
            'parent_id': comment_id,  # 뽐뿌는 대댓글 구조가 명확하지 않음
            'like_count': like_count,
            'platform': 'Ppomppu'
        })
    return reply_list

# --- 데이터 저장 ---
def save_data(posts, comments):
    """수집된 데이터를 TSV 및 JSON 파일로 저장합니다."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # JSON 파일로 저장 (통합 크롤러와 호환)
    save_to_json("Ppomppu", posts, comments)
    
    if posts:
        posts_df = pd.DataFrame(posts)
        for col in CONTENT_COLUMNS:
            if col not in posts_df.columns:
                posts_df[col] = None
        posts_df = posts_df.reindex(columns=CONTENT_COLUMNS)
        posts_filename = os.path.join(OUTPUT_DIR, f"{timestamp}_contents.tsv")
        posts_df.to_csv(posts_filename, sep='\t', index=False, encoding='utf-8-sig')
        print(f"게시글 데이터 저장 완료: {posts_filename}")
        print(f"JSON 게시글 데이터 저장 완료: {OUTPUT_DIR}/Ppomppu.json")
    else:
        print("저장할 게시글 데이터가 없습니다.")

    if comments:
        comments_df = pd.DataFrame(comments)
        for col in COMMENT_COLUMNS:
            if col not in comments_df.columns:
                comments_df[col] = None
        comments_df = comments_df.reindex(columns=COMMENT_COLUMNS)
        comments_filename = os.path.join(OUTPUT_DIR, f"{timestamp}_comments.tsv")
        comments_df.to_csv(comments_filename, sep='\t', index=False, encoding='utf-8-sig')
        print(f"댓글 데이터 저장 완료: {comments_filename}")
        print(f"JSON 댓글 데이터 저장 완료: {OUTPUT_DIR}/Ppomppu_comments.json")
    else:
        print("저장할 댓글 데이터가 없습니다.")

# --- 메인 실행 ---
def main():
    """메인 실행 함수"""

    crawler = PpomppuCrawler()
    crawler.run("아이온", max_posts=20, start_date=None, end_date=None)
    # get_post_and_comment_data("https://www.ppomppu.co.kr/zboard/view.php?id=ppomppu&no=670437&keyword=%BE%C6%C0%CC%BF%C2")

if __name__ == "__main__":
    main()