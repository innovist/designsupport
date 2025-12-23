import time
from datetime import datetime
import os
import re
from common import get_url_query, save_to_json
import math
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
import undetected_chromedriver as uc
from urllib.parse import quote
from dotenv import load_dotenv
from urllib.parse import quote_plus

# .env 파일 로드 - 프로젝트 루트에서 찾기
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # 현재 작업 디렉토리에서도 시도
    load_dotenv()


class EtolandCrawler:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless=new")  # Headless 모드
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")  # GPU 가속 비활성화 (headless 안정성)
        self.options.add_argument("--window-size=800,600")  # 창 크기 설정
        self.options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.options.add_argument('--blink-settings=imagesEnabled=false')
        # self.options.add_argument("--autoplay-policy=user-gesture-required")
        # self.options.add_argument("--autoplay-policy=document-user-activation-required")

        self.driver = webdriver.Chrome(options=self.options)
        
        # 보안상 환경변수에서 인증정보 획득
        self.username = os.getenv('ETOLAND_USERNAME')  
        self.password = os.getenv('ETOLAND_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("에토랜드 크롤링을 위해 환경변수 ETOLAND_USERNAME, ETOLAND_PASSWORD 설정이 필요합니다.")

    def login(self):
        self.driver.get("https://www.etoland.co.kr/module/login.php?url=%2Findex.php")
        print("로그인 중....")

        time.sleep(3)
        print("로그인 폼 찾기: ",  self.driver.find_elements(By.CSS_SELECTOR, "input[name='mb_id']"))
        self.driver.find_element(By.CSS_SELECTOR, "input[name='mb_id']").send_keys(self.username)
        self.driver.find_element(By.CSS_SELECTOR, "#mb_password").send_keys(self.password)
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(3)
        print("로그인 완료")



    def get_published_date(self, published_date):
        from datetime import timedelta
        import sys
        import os

        # date_utils 임포트 (상위 디렉토리에서)
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'utils'))
            from date_utils import parse_relative_time
        except ImportError:
            # date_utils가 없는 경우 기본 처리
            parse_relative_time = None

        # 상대 시간 표현 처리 (수집 시점 기준)
        if parse_relative_time:
            try:
                result = parse_relative_time(published_date, datetime.now())
                if result:
                    return result.strftime("%Y-%m-%d")
            except Exception:
                pass  # 실패시 기존 로직으로 진행

        if re.match(r"^\d{2}\:\d{2}$", published_date.strip()):
            hour, minute = published_date.strip().split(":")
            now = datetime.now()
            published_date = datetime(year=int(now.year), month=int(now.month), day=int(now.day), hour=int(hour), minute=int(minute), second=0)
            return published_date.strftime("%Y-%m-%d")
        elif re.match(r"^\d{2}\-\d{2}$", published_date.strip()):
            month, day = published_date.strip().split("-")
            now = datetime.now()
            published_date = datetime(year=int(now.year), month=int(month), day=int(day), hour=0, minute=0, second=0)
            return published_date.strftime("%Y-%m-%d")

        return published_date

    def choose(self, selectors):
        for selector in selectors:
            try:
                return self.driver.find_element(By.CSS_SELECTOR, selector).text.strip()
            except:
                continue
        return None

    def get_posts(self, url):
        try:
            self.driver.set_page_load_timeout(60)  # 60초로 증가
            self.driver.get(url)
        except TimeoutException as e:
            print(f"타임아웃 발생: {e}")
            return [], []
        
        time.sleep(2)
        params = get_url_query(url)
        post_id = params["wr_id"]

        title_selectors = [
            ".mw_basic_view_subject",
            ".title_wrap >.title"
        ]
        
        title = self.choose(title_selectors)
        if not title:
            title = "제목 없음"

        
        print("post title: ", title)
        
        
        published_date_selectors = [
            ".mw_basic_view_datetime",
            ".info_wrap >.datetime"
        ]
        published_date = self.choose(published_date_selectors)
        if  published_date:
            
            # 한글 정규식으로 한글을 공백으로 치환
            published_date = re.sub(r'[가-힣]+', '', published_date)
            published_date = published_date.replace("(", "").replace(")", "")
            published_date = published_date.replace(" ", " ")
        else:
            published_date = None

        view_count_selectors = [
            ".mw_basic_view_hit",
            ".span.views"
        ]
        view_count = self.choose(view_count_selectors)
        if not view_count:
            view_count = None

        username_selectors = [
            ".mw_basic_view_name span.member",
            "span.writer span.member"
        ]
        username = self.choose(username_selectors)
        if not username:
            username = None
        
        try:
            content = self.driver.find_element(By.CSS_SELECTOR, "div#view_content").text.strip()
            if not content:
                # 내용이 없으면 제목을 내용으로 사용
                content = title
        except NoSuchElementException:
            # 내용을 찾을 수 없으면 제목을 내용으로 사용
            content = title

        like_count_selectors = [
            "#recent-hot-list-box > li:nth-child(1) > div.wr_good > span",
            ".good_count"
        ]
        like_count = self.choose(like_count_selectors)
        if not like_count:
            like_count = None

        post_data = {
            "id": post_id,
            "title": title,
            "content": content,
            "published_date": published_date,
            "platform": "Etoland",
            "link": url,
            "view_count": view_count,
            "like_count": like_count,
            "user_id": username,
        }

        comment_total_count = self.driver.find_element(By.CSS_SELECTOR, ".comment_list_title_count").text.strip()
        comment_total_count = int(comment_total_count.replace(",", ""))
        if comment_total_count > 0:
            comments = self.get_comments(post_id, comment_total_count)
        else:
            comments = []

        
        print("back")
        self.driver.back()
        time.sleep(3)
        print("back done")

        return post_data, comments

    def get_comments(self, post_id, comment_total_count):
        comments = []
        comment_ids = []
        total_page = math.ceil(comment_total_count / 50)
        current_url = self.driver.current_url
        for page in range(1, total_page + 1):
            comment_url = f"{current_url}&cpage={page}"

            # 댓글 페이지를 새 탭에서 열고, 작업 후 닫기
            try:
                self.driver.set_page_load_timeout(60)
                self.driver.execute_script(f"window.open('{comment_url}');")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.get(comment_url)
            except TimeoutException as e:
                print(f"댓글 페이지 타임아웃: {e}")
                # 타임아웃 시 열린 탭 정리 후 수집된 댓글 반환
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                return comments
            time.sleep(2)

            comment_containers = self.driver.find_elements(By.CSS_SELECTOR, "#comment_list_wrap > table:not(.border_table) > tbody> tr:nth-child(1)")

            for i, comment_container in enumerate(comment_containers):
                comment_id = f"{post_id}_{page}_{i}"
                username = comment_container.find_elements(By.CSS_SELECTOR, ".member")
                if len(username) == 0:
                    continue
                username = username[0].text.strip()

                try:
                    published_date = comment_container.find_element(By.CSS_SELECTOR, ".mw_basic_comment_datetime").text.strip()
                    published_date = re.sub(r'[가-힣]+', '', published_date)
                    published_date = published_date.replace("(", "").replace(")", "")
                    published_date = published_date.replace(" ", " ")
                except:
                    published_date = datetime.now()

                content = comment_container.find_element(By.CSS_SELECTOR, ".mw_basic_comment_content").text.strip()
                print(content)

                is_reply = comment_container.find_elements(By.CSS_SELECTOR, 'img[src="/img/reply_icon.gif"]')
                if comment_ids and len(is_reply) > 0:
                    parent_id = comment_ids[-1]
                else:
                    parent_id = None
                    comment_ids.append(comment_id)

                comments.append({
                    "id": comment_id,
                    "username": username,
                    "content": content,
                    "blog_id": post_id,
                    "platform": "Etoland",
                    "parent_id": parent_id,
                    "published_date": published_date,
                    "like_count": None,
                })

            # 각 페이지 처리 후 탭 닫기
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            time.sleep(1)

        return comments

    def click_next_button(self):
        next_button = self.driver.find_elements(By.CSS_SELECTOR, "div.prev_next_wrap > a")
        print("next_button: ", next_button)
        if len(next_button) > 1:
            next_button[1].click()
            time.sleep(2)
        elif len(next_button) > 0:
            next_button[0].click()
            time.sleep(2)
        
            
        

    def run(self, keyword, max_posts, start_date=None, end_date=None):
        post_data = []
        comment_data = []
        count = 0

        self.login()
        # EUC-KR 인코딩 처리 (Python 3 호환)
        
        encoded_keyword = quote_plus(keyword, encoding='euc-kr')
        self.driver.get(f"https://www.etoland.co.kr/bbs/new2.php?sfl=subject&sword={encoded_keyword}")
        time.sleep(2)
        
        page = 1
        max_pages = 100  # 최대 100페이지까지만 검색
        consecutive_empty_pages = 0
        max_empty_pages = 30
        consecutive_out_of_range = 0
        max_out_of_range = 20  # 연속 20개 게시물이 범위 밖이면 중단

        while page <= max_pages:
            print(f"이토랜드 페이지 {page} 검색 중...")

            rows = self.driver.find_elements(By.CSS_SELECTOR, ".board_new2_list > li:not(.board_new2_title):not(.middle_line)")
            if len(rows) == 0:
               break

            urls = []
            page_found_posts = 0
            
            for row in rows:
                try:
                    published_date = row.find_element(By.CSS_SELECTOR, "div.datetime").text.strip()
                    published_date = self.get_published_date(published_date)
                    
                    if start_date and end_date:
                        # 역시간순: 날짜가 start_date보다 이전이면 종료 (범위 지나침)
                        if published_date < start_date:
                            consecutive_out_of_range += 1
                            if consecutive_out_of_range >= max_out_of_range:
                                print(f"연속 {max_out_of_range}개 게시물이 날짜 범위를 지나쳐 검색 종료")
                                return post_data, comment_data
                            continue
                        # 날짜가 end_date보다 이후면 아직 범위 전 (계속 진행)
                        elif published_date > end_date:
                            consecutive_out_of_range = 0
                            continue
                        else:
                            # 범위 내 날짜
                            consecutive_out_of_range = 0
                    
                    url = row.find_element(By.CSS_SELECTOR, ".subject>a").get_attribute("href")
                    urls.append(url)
                    page_found_posts += 1
                except Exception as e:
                    print(f"게시물 정보 추출 실패: {e}")
                    continue

            for url in urls:
                if max_posts and count >= max_posts:
                    print(f"최대 게시물 수({max_posts})에 도달하여 종료")
                    return post_data, comment_data
                    
                print(url)
                posts, comments = self.get_posts(url)
                post_data.append(posts)
                comment_data.extend(comments)
                count += 1
            
            print(f"페이지 {page}: {page_found_posts}개 게시물 수집")
            page += 1
            
            if page <= max_pages:
                self.click_next_button()
                time.sleep(2)
        
        # 수집 완료 후 일괄 저장
        if post_data:
            save_to_json("Etoland", post_data, comment_data)
            print(f"이토랜드 크롤링 완료: 총 {len(post_data)}개 게시물, {len(comment_data)}개 댓글")
            
        return post_data, comment_data
                

            

                

if __name__ == "__main__":
    crawler = EtolandCrawler()
    url = "https://www.etoland.co.kr/bbs/board.php?bo_table=etohumor07&wr_id=1819706"

    
    crawler.run("병원", None)

    # encoded_keyword = quote_plus("센시아", encoding='euc-kr')
    # print(f"https://www.etoland.co.kr/bbs/new2.php?sfl=subject&sword={encoded_keyword}")