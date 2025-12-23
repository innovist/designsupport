import pandas as pd
import time
import os
import re
from datetime import datetime
from urllib.parse import quote
from crawlers.common import extract_numbers, save_to_json, is_date_in_range, filter_by_date_range

# 선택적 import를 위한 try-except
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import NoSuchElementException, TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    print("[경고] Selenium이 설치되지 않았습니다. 다음 명령어로 설치하세요:")
    print("pip install selenium webdriver-manager")
    SELENIUM_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    print("[경고] BeautifulSoup4가 설치되지 않았습니다. 다음 명령어로 설치하세요:")
    print("pip install beautifulsoup4")
    BS4_AVAILABLE = False

# --- 설정 ---
# TSV 파일 헤더 정의 (샘플 파일 기반)
CONTENT_COLUMNS = ['id', 'title', 'content', 'published_date', 'platform', 'link', 'view_count', 'like_count', 'smp_method', 'smp_score', 'inf_type', 'cls_id']
COMMENT_COLUMNS = ['id', 'blog_id', 'content', 'published_date', 'parent_id', 'like_count', 'platform']
OUTPUT_DIR = 'crawling_data'

# --- 웹 드라이버 설정 ---
def setup_driver():
    """Selenium 웹 드라이버를 설정하고 반환합니다."""
    if not SELENIUM_AVAILABLE:
        print("[오류] Selenium이 설치되지 않아 드라이버를 초기화할 수 없습니다.")
        return None
        
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # 브라우저 창 숨기기
        options.add_argument("--window-size=800x600")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
        
        driver = webdriver.Chrome(options=options)
        # 페이지 로드 타임아웃 설정 (공백시간 180초)
        driver.set_page_load_timeout(180)
        driver.implicitly_wait(180)

        return driver
    except Exception as e:
        print(f"[오류] Chrome 드라이버를 초기화할 수 없습니다: {e}")
        print("Chrome 드라이버가 설치되어 있고, PATH에 있는지 확인하세요.")
        return None

# --- 데이터 스크래핑 ---
def get_post_urls(driver, keyword, start_date, end_date, max_posts=None):
    """네이버 검색 결과에서 카페 게시물 URL을 수집합니다. (개선된 지능적 종료 조건)"""
    urls = []
    page = 1
    empty_page_count = 0
    max_empty_pages = 3
    duplicate_count = 0
    start_time = time.time()
    max_time_seconds = 3600  # 1시간 제한

    encoded_keyword = quote(keyword)

    print(f"🔍 네이버 카페 검색 시작 (최대 게시물: {'무제한' if max_posts is None else max_posts}개)")
    print(f"   키워드: {keyword}, 기간: {start_date} ~ {end_date}")

    try:
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

            # 네이버 카페 탭 검색 URL
            start_index = 1 + (page - 1) * 10
            nso_param = f"so:r,p:from{start_date.replace('-', '')}to{end_date.replace('-', '')}"

            search_url = f"https://search.naver.com/search.naver?ssc=tab.cafe.all&query={encoded_keyword}&sm=tab_opt&nso={quote(nso_param)}&start={start_index}"

            driver.get(search_url)
            time.sleep(2)

            # 카페 게시글 링크 수집
            blog_links = driver.find_elements(By.CSS_SELECTOR, ".title_link, .api_txt_lines.total_tit, .link_tit")
            new_urls = []
            for link in blog_links:
                href = link.get_attribute('href')
                if href and 'cafe.naver.com' in href:
                    new_urls.append(href)

            if not new_urls:
                empty_page_count += 1
                if empty_page_count >= max_empty_pages:
                    print(f"📭 연속 빈 페이지 {max_empty_pages}회 도달")
                    break
            else:
                empty_page_count = 0  # 리셋

            # 중복 URL 확인
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

            # 페이지네이션 확인 로직
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, ".btn_next")
                if next_button.get_attribute('aria-disabled') == 'true':
                    print("📄 네이버 검색 마지막 페이지 도달")
                    break
            except NoSuchElementException:
                print("📄 다음 버튼을 찾을 수 없어 검색 종료")
                break

            page += 1

            # 극단적 페이지 제한 (안전장치)
            if page > 200:
                print("⚠️ 안전장치: 페이지 200 도달")
                break

    except Exception as e:
        print(f"❌ 네이버 카페 URL 수집 중 오류: {str(e)}")
        import traceback
        print(f"   상세 오류:\n{traceback.format_exc()}")

    final_time = time.time() - start_time
    print(f"✅ URL 수집 완료: {len(urls)}개 (소요시간: {final_time/60:.1f}분, 중복제거: {duplicate_count}개)")

    return urls if max_posts is None else urls[:max_posts]


def get_post_and_comment_data(driver, post_url, start_date=None, end_date=None):
    """개별 카페 게시물과 댓글 내용을 스크래핑합니다."""
    post_data = {}
    comments_data = []
    
    try:
        driver.get(post_url)
        time.sleep(3)
        try:
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "cafe_main")))
        except TimeoutException:
            print(f"[네이버 카페] 메인 프레임을 찾을 수 없습니다: {post_url}")
            driver.switch_to.default_content()
            return None, []
            
        driver.switch_to.frame("cafe_main")
        
        # --- 게시물 정보 추출 ---
        post_id_match = re.search(r'\/(\d+)$', post_url)
        post_id = post_id_match.group(1) if post_id_match else datetime.now().strftime('%Y%m%d%H%M%S%f')
        
        # 제목 추출 (여러 선택자 시도)
        title = driver.find_element(By.CSS_SELECTOR, ".title_text").text.strip()

        content_selectors = [
            ".se-viewer",
            ".article_viewer"
        ]
        content = None
        for selector in content_selectors:
            content = driver.find_elements(By.CSS_SELECTOR, selector)
            if content:
                content = content[0].text.strip()
                break
        
        
        date_text = driver.find_element(By.CSS_SELECTOR, ".date").text.strip()

        view_count = driver.find_element(By.CSS_SELECTOR, ".count").text.strip()
        view_count = extract_numbers(view_count)
        view_count = view_count[0]

        like_count = driver.find_element(By.CSS_SELECTOR, "#app > div > div > div.ArticleContentBox > div.article_container > div.ReplyBox > div.box_left > div > div > a > em.u_cnt._count").text.strip()
        
        # 필수 필드 포함한 완전한 데이터 구조
        post_data = {
            'id': post_id,
            'title': title if title else "제목 없음",
            'link': post_url,
            'view_count': view_count,
            'like_count': like_count,
            'content': content if content else "내용 없음",
            'published_date': date_text,
            'platform': 'Naver Cafe',
            
        }

        # --- 댓글 정보 추출 ---
        comments_data = []
        
        try:
            comments_data = get_comment_data(driver, post_id)
        except Exception as e:
            print(f"[네이버 카페] 댓글 수집 중 오류: {e}")
        
        finally:
            driver.switch_to.default_content()
            

    except Exception as e:
        print(f"[네이버 카페] 게시물 처리 중 오류: {post_url}, {e}")
        return None, []

    # 날짜 필터링 적용 (기간 외 데이터는 None 반환)
    if not is_date_in_range(post_data.get('published_date'), start_date, end_date):
        return None, []
    
    # 댓글도 날짜 필터링
    filtered_comments = filter_by_date_range(comments_data, 'published_date', start_date, end_date)

    return post_data, filtered_comments



def get_comment_data(driver, post_id):

    comment_seletors = driver.find_elements(By.CSS_SELECTOR, ".CommentItem")

    comment_ids = []
    comment_data = []

    for i, selector in enumerate(comment_seletors):
        class_name = selector.get_attribute("class")


        published_date = selector.find_elements(By.CSS_SELECTOR, ".comment_info_date")
        if published_date:
            published_date = published_date[0].text.strip()
        else:
            continue

        content = selector.find_element(By.CSS_SELECTOR, ".comment_text_view").text.strip()

        like_count = selector.find_element(By.CSS_SELECTOR, ".u_cnt").text.strip()
        if like_count:
            like_count = extract_numbers(like_count)
            like_count = like_count[0]
        else:
            like_count = None

        # 작성자 정보 추출 (find_elements로 implicit wait 회피)
        nickname = None

        # 1순위: a.comment_nickname 직접 탐색 (댓글/대댓글 공통)
        nodes = selector.find_elements(By.CSS_SELECTOR, "a.comment_nickname")
        if nodes:
            nickname = nodes[0].text.strip()

        # 2순위: 컨테이너 속성 확인
        if not nickname:
            nickname = selector.get_attribute("data-nickname") or selector.get_attribute("data-user-id")

        # 3순위: .comment_nickname 폴백 (태그 무관)
        if not nickname:
            nodes = selector.find_elements(By.CSS_SELECTOR, ".comment_nickname")
            if nodes:
                nickname = nodes[0].text.strip()

        # 최종 기본값
        if not nickname or nickname == '':
            nickname = '익명'

        if "CommentItem--reply" in class_name and comment_ids:
            parent_id = comment_ids[-1]
            comment_data.append({
                "id":f"{post_id}_{parent_id}_{i}",
                "blog_id": post_id,
                "content": content,
                "published_date": published_date,
                "parent_id": parent_id,
                "like_count": like_count,
                "platform": "Naver Cafe",
                "username": nickname,
                "author": nickname
            })
            continue


        comment_id = f"{post_id}_{i}"

        comment_data.append({
            "id": comment_id,
            "blog_id": post_id,
            "content": content,
            "published_date": published_date,
            "parent_id": None,
            "like_count": like_count,
            "platform": "Naver Cafe",
            "username": nickname,
            "author": nickname
        })

        comment_ids.append(comment_id)

    return comment_data

    

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
        posts_filename = os.path.join(OUTPUT_DIR, f"{timestamp}_contents.tsv")
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
        comments_filename = os.path.join(OUTPUT_DIR, f"{timestamp}_comments.tsv")
        comments_df.to_csv(comments_filename, sep='\t', index=False, encoding='utf-8-sig')
        print(f"댓글 데이터 저장 완료: {comments_filename}")
    else:
        print("저장할 댓글 데이터가 없습니다.")

# --- 메인 실행 ---
def main():
    """메인 실행 함수"""
    keyword = input("검색할 키워드를 입력하세요: ")
    start_date = input("검색 시작일 (YYYY-MM-DD 형식)을 입력하세요: ")
    end_date = input("검색 종료일 (YYYY-MM-DD 형식)을 입력하세요: ")
    
    driver = setup_driver()
    if not driver:
        return

    all_posts = []
    all_comments = []

    try:
        post_urls = get_post_urls(driver, keyword, start_date, end_date)
        print(f"\n총 {len(post_urls)}개의 카페 게시물을 대상으로 스크래핑을 시작합니다.")
        
        for i, url in enumerate(post_urls):
            print(f"({i+1}/{len(post_urls)}) 스크래핑 중: {url}")
            post, comments = get_post_and_comment_data(driver, url)
            if post:
                all_posts.append(post)
            if comments:
                all_comments.extend(comments)
            time.sleep(1)

    except Exception as e:
        print(f"크롤링 중 오류가 발생했습니다: {e}")
    finally:
        driver.quit()
        print("\n크롤링 완료.")
        save_data(all_posts, all_comments)

if __name__ == "__main__":
    main()