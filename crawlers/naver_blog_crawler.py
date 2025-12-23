import pandas as pd
import time
import os
import re
from datetime import datetime
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
import math

from crawlers.common import save_to_json, is_date_in_range, filter_by_date_range

# --- 설정 ---
# TSV 파일 헤더 정의 (샘플 파일 기반)
CONTENT_COLUMNS = ['id', 'title', 'content', 'published_date', 'platform', 'link', 'like_count', 'smp_method', 'smp_score', 'inf_type', 'cls_id']
COMMENT_COLUMNS = ['id', 'blog_id', 'content', 'published_date', 'parent_id', 'like_count', 'platform']
OUTPUT_DIR = 'crawling_data'

# --- 웹 드라이버 설정 ---
def setup_driver():
    """Selenium 웹 드라이버를 설정하고 반환합니다."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 브라우저 창 숨기기
    options.add_argument("window-size=800x600")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        print("Chrome 드라이버를 초기화할 수 없습니다. chromedriver가 설치되어 있고, PATH에 있는지 확인하세요.")
        print(f"오류: {e}")
        return None
    return driver

# --- 데이터 스크래핑 ---
def get_post_urls(driver, keyword, start_date, end_date, max_posts=None):
    """네이버 검색 결과에서 블로그 게시물 URL을 수집합니다. (개선된 지능적 종료 조건)"""
    urls = []
    page = 1
    empty_page_count = 0
    max_empty_pages = 3
    duplicate_count = 0
    start_time = time.time()
    max_time_seconds = 3600  # 1시간 제한
    
    encoded_keyword = quote(keyword)
    
    print(f"🔍 네이버 블로그 검색 시작 (최대 게시물: {'무제한' if max_posts is None else max_posts}개)")

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
        
        # 네이버 블로그 탭 검색 URL (새로운 형식)
        start_index = 1 + (page - 1) * 10 
        nso_param = f"so:r,p:from{start_date.replace('-', '')}to{end_date.replace('-', '')}"
        print("---->",nso_param)
        
        # search.naver.com/search.naver 블로그 탭 URL 구조
        search_url = f"https://search.naver.com/search.naver?ssc=tab.blog.all&query={encoded_keyword}&sm=tab_opt&nso={quote(nso_param)}&start={start_index}"
        
        driver.get(search_url)
        time.sleep(2)

        # 실제 네이버 블로그 탭 검색 결과 선택자
        # 블로그 제목 링크: .title_link 또는 .api_txt_lines.total_tit
        blog_links = driver.find_elements(By.CSS_SELECTOR, ".title_link, .api_txt_lines.total_tit, .link_tit")
        new_urls = []
        for link in blog_links:
            href = link.get_attribute('href')
            if href and 'blog.naver.com' in href:
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
        if page > 200:  # 네이버 검색 특성상 높은 제한
            print("⚠️ 안전장치: 페이지 200 도달")
            break

    final_time = time.time() - start_time
    print(f"✅ URL 수집 완료: {len(urls)}개 (소요시간: {final_time/60:.1f}분, 중복제거: {duplicate_count}개)")
    
    return urls if max_posts is None else urls[:max_posts]


def get_post_and_comment_data(driver, post_url, start_date=None, end_date=None):
    """개별 블로그 게시물과 댓글 내용을 스크래핑합니다."""
    post_data = {}
    comments_data = []
    
    try:
        driver.get(post_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "mainFrame")))
        driver.switch_to.frame("mainFrame")
    except (TimeoutException, NoSuchElementException):
        print(f"메인 프레임을 찾을 수 없습니다: {post_url}")
        driver.switch_to.default_content()
        return None, []

    # --- 게시물 정보 추출 ---
    soup = BeautifulSoup(driver.page_source, 'lxml')
    
    post_id_match = re.search(r'\/(\d+)$', post_url)
    post_id = post_id_match.group(1) if post_id_match else datetime.now().strftime('%Y%m%d%H%M%S%f')
    
    title = soup.select_one('.pcol1_se_blog_title .se-title-text, .title_text, .se_title_text')
    content = soup.select_one('.se-main-container, #postViewArea')
    date_elem = soup.select_one('.se_publishDate, .date, .pcol2')
    
    post_data['id'] = post_id
    post_data['link'] = post_url
    post_data['title'] = title.get_text(strip=True) if title else "제목 없음"
    post_data['content'] = content.get_text(strip=True) if content else "내용 없음"
    post_data['published_date'] = date_elem.get_text(strip=True) if date_elem else None
    post_data['platform'] = 'Naver Blog'

    # --- 댓글 정보 추출 ---
    try:
        driver.switch_to.default_content()
        comment_frame = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "commentFrame")))
        driver.switch_to.frame(comment_frame)
        
        while True:
            try:
                more_button = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a.u_cbox_btn_more')))
                more_button.click()
                time.sleep(1)
            except (NoSuchElementException, TimeoutException):
                break

        comment_soup = BeautifulSoup(driver.page_source, 'lxml')
        comments = comment_soup.select('.u_cbox_comment_box')
        
        for i, comment in enumerate(comments):
            comment_id = f"{post_id}_{i+1}"
            comment_content = comment.select_one('.u_cbox_contents')
            comment_date = comment.select_one('.u_cbox_date')
            
            parent_id = None
            if "u_cbox_reply_area" in comment.get('class', []):
                if comments_data:
                    parent_id = comments_data[-1]['id']

            comments_data.append({
                'id': comment_id,
                'blog_id': post_id,
                'content': comment_content.get_text(strip=True) if comment_content else "",
                'published_date': comment_date.get_text(strip=True) if comment_date else None,
                'parent_id': parent_id,
                'platform': 'Naver Blog'
            })

    except (TimeoutException, NoSuchElementException):
        pass  # 댓글이 없는 경우는 정상적인 상황
    finally:
        driver.switch_to.default_content()

    # 날짜 필터링 적용 (기간 외 데이터는 None 반환)
    if not is_date_in_range(post_data.get('published_date'), start_date, end_date):
        return None, []
    
    # 댓글도 날짜 필터링
    filtered_comments = filter_by_date_range(comments_data, 'published_date', start_date, end_date)

    return post_data, filtered_comments

# --- 데이터 저장 ---
def save_data(posts, comments):
    """수집된 데이터를 TSV 파일로 저장합니다."""
    from total_crawler import save_total_data
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


def get_blog(driver, url, start_date=None, end_date=None):
    try:
        driver.switch_to.default_content()
        driver.get(url)
        
        # 페이지 로딩 대기
        time.sleep(3)

        post_id = url.split("/")[-1]
        
        # iframe 찾기 및 전환 - 여러 방법 시도
        try:
            # 먼저 mainFrame iframe 시도
            iframe = driver.find_element(By.ID, "mainFrame")
            driver.switch_to.frame(iframe)
        except NoSuchElementException:
            try:
                # 대체 iframe 선택자들 시도
                iframe_selectors = ["#mainFrame", "iframe[name='mainFrame']", "iframe"]
                iframe_found = False
                for iframe_selector in iframe_selectors:
                    try:
                        iframe = driver.find_element(By.CSS_SELECTOR, iframe_selector)
                        driver.switch_to.frame(iframe)
                        iframe_found = True
                        break
                    except NoSuchElementException:
                        continue
                
                if not iframe_found:
                    # iframe이 없는 경우 - 직접 페이지에서 처리
                    pass
            except:
                pass
        # 페이지 로딩 추가 대기
        time.sleep(2)
        
        # 제목 찾기 - 여러 선택자 시도
        title_selectors = [
            ".se-title-text",
            ".pcol1_se_blog_title .se-title-text", 
            ".title_text",
            ".se_title_text",
            "h1",
            "h2", 
            ".se-text-paragraph span",
            ".title",
            ".post-title",
            "[class*='title']",
            ".blog-title"
        ]
        
        title = "제목 없음"
        for selector in title_selectors:
            try:
                # WebDriverWait 사용해서 안정적으로 대기
                wait = WebDriverWait(driver, 5)
                title_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                if title_element.text.strip():
                    title = title_element.text.strip()
                    break
            except (NoSuchElementException, TimeoutException):
                continue
        # 내용 찾기 - 여러 선택자 시도
        content_selectors = [
            ".se-section-text > .se-module-text > .se-text-paragraph > span",
            ".se-text-paragraph span",
            ".se-module-text p",
            ".se-component-text",
            ".post-view p",
            "div[data-content] p"
        ]
        
        content_tags = []
        for selector in content_selectors:
            try:
                content_tags = driver.find_elements(By.CSS_SELECTOR, selector)
                if content_tags:
                    break
            except:
                continue
        
        # 날짜 찾기 - 여러 선택자 시도
        date_selectors = [
            ".se_publishDate",
            ".date",
            ".publish_date",
            "[data-date]",
            ".blog-date"
        ]
        
        blog_created_at = "날짜 없음"
        for selector in date_selectors:
            try:
                date_element = driver.find_element(By.CSS_SELECTOR, selector)
                if date_element.text.strip():
                    blog_created_at = date_element.text.strip()
                    break
            except NoSuchElementException:
                continue
        content = ""
        for tag in content_tags[1:]:
            text = tag.text
            if text.strip() == "":
                continue
            content += text


        
        like_count = driver.find_elements(By.CSS_SELECTOR, "#floating_bottom > div > div > div.area_sympathy > a > div > span > em.u_cnt._count")
        if like_count:
            like_count = like_count[0].text.strip()
        else:
            like_count = None
        
        comments = get_comments(driver, post_id)
        

        post_data = {
            "id": post_id,
            "title": title,
            "content": content,
            "published_date": blog_created_at,
            'link': url,
            'view_count': None,
            'like_count': like_count,
            "platform": "Naver Blog"
        }
        
        # 날짜 필터링 적용 (기간 외 데이터는 None 반환)
        if not is_date_in_range(post_data.get('published_date'), start_date, end_date):
            return None, []
        
        # 댓글도 날짜 필터링
        filtered_comments = filter_by_date_range(comments, 'published_date', start_date, end_date)

        return post_data, filtered_comments
        
    except Exception as e:
        print(f"네이버 블로그 크롤링 중 오류 발생: {url} - {str(e)}")
        return None, []


def get_comments(driver, post_id):
    results = []

    try:
        driver.switch_to.default_content()
        try:
            comment_frame = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "commentFrame"))
            )
        except TimeoutException:
            comment_frame = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id*='comment']"))
            )
        driver.switch_to.frame(comment_frame)
    except Exception:
        return results  # 댓글 영역 없음

    # 더보기 클릭하여 전체 로드
    try:
        while True:
            more_btn = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.u_cbox_btn_more"))
            )
            driver.execute_script("arguments[0].click();", more_btn)
            time.sleep(0.5)
    except Exception:
        pass

    soup = BeautifulSoup(driver.page_source, "lxml")
    comment_boxes = soup.select(".u_cbox_comment_box")

    for i, box in enumerate(comment_boxes):
        content_el = box.select_one(".u_cbox_contents")
        date_el = box.select_one(".u_cbox_date")
        if not content_el:
            continue

        comment_id = f"{post_id}_{i}"
        like_el = box.select_one("em.u_cbox_cnt_recomm")

        results.append({
            "id": comment_id,
            "blog_id": post_id,
            "content": content_el.get_text(strip=True),
            "published_date": date_el.get_text(strip=True) if date_el else None,
            "like_count": like_el.get_text(strip=True) if like_el else "0",
            "platform": "Naver Blog",
            "parent_id": None,
        })

    return results


def get_replies(comment_container, post_id, parent_id):
    results = []
    reply_containers = comment_container.find_elements(By.CSS_SELECTOR, ".u_cbox_reply_area")
    # print("대댓글 갯수: ", len(reply_containers))
    for i, reply_container in enumerate(reply_containers):
        try:
            reply_content = reply_container.find_element(By.CSS_SELECTOR, ".u_cbox_contents").text
            reply_created_at = reply_container.find_element(By.CSS_SELECTOR, ".u_cbox_date").text
            results.append({
                "id": f"{post_id}_{parent_id}_{i}",
                "blog_id": post_id,
                "content": reply_content,
                "published_date": reply_created_at,
                "parent_id": parent_id,
                "platform": "Naver Blog"
            })
        except:
            continue
    return results

def run(driver, keyword, start_date, end_date, max_posts=None):
    search_url = f"https://section.blog.naver.com/Search/Post.naver?pageNo=1&rangeType=PERIOD&orderBy=recentdate&startDate={start_date}&endDate={end_date}&keyword={quote(keyword)}"
    driver.get(search_url)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".search_number")))
    
    comments = []
    posts = []
    total_count = ''.join(filter(str.isdigit, driver.find_element(By.CSS_SELECTOR, ".search_number").text))
    total_count = int(total_count.replace(",", ""))
    total_pages = math.ceil(total_count / 7)

    count = 0
    for page in range(1, total_pages + 1):
        if page != 1:
            driver.switch_to.default_content()
            search_url = f"https://section.blog.naver.com/Search/Post.naver?pageNo={page}&rangeType=PERIOD&orderBy=recentdate&startDate={start_date}&endDate={end_date}&keyword={quote(keyword)}"
            print(search_url)
            driver.get(search_url)
            time.sleep(2)
        blog_links = driver.find_elements(By.CSS_SELECTOR, "#content > section > div.area_list_search > div> div > div.info_post > div.desc > a.desc_inner")
        blog_links = [blog_link.get_attribute("href") for blog_link in blog_links]
        
        for blog_link in blog_links:
            post, post_comments = get_blog(driver, blog_link, start_date, end_date)
            if post:  # 날짜 필터링 통과한 경우만 추가
                posts.append(post)
                comments.extend(post_comments)
                save_to_json("naver_blog",[post], post_comments)
                count += 1
            time.sleep(1)
            if max_posts and count >= max_posts:
                return posts, comments
            
    return posts, comments

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
        print(f"\n총 {len(post_urls)}개의 블로그 게시물을 대상으로 스크래핑을 시작합니다.")
        
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
    driver = setup_driver()
    posts, comments = get_blog(driver, "https://blog.naver.com/fine1177/224103107623", None, None)
    save_to_json("naver_blog",[posts], comments)
    print(len(comments))
    # print(f"수집 결과: 게시글 {len(posts)}개, 댓글 {len(comments)}개")
