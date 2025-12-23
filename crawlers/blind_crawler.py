import time
from datetime import datetime
import os
import re
import subprocess
import platform
from common import get_url_query, save_to_json
import math
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def get_chrome_version():
    """시스템에 설치된 Chrome 버전을 감지합니다."""
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            cmd = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"]
        elif system == "Windows":
            cmd = ["reg", "query", "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon", "/v", "version"]
        else:  # Linux
            cmd = ["google-chrome", "--version"]

        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout.strip()

        # 버전 번호 추출 (예: "Google Chrome 142.0.6367.98" -> 142)
        version_match = re.search(r'(\d+)\.\d+\.\d+', output)
        if version_match:
            version = int(version_match.group(1))
            print(f"Chrome 버전 감지: {version}")
            return version
    except Exception as e:
        print(f"Chrome 버전 감지 실패: {e}")
    return None


class BlindCrawler:
    def __init__(self):
        self.options = uc.ChromeOptions()
        # self.options.add_argument("--headless")  # Headless 모드
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")  # GPU 가속 비활성화 (headless 안정성)
        self.options.add_argument("--window-size=800,600")  # 창 크기 설정

        # Chrome 버전 자동 감지
        chrome_version = get_chrome_version()

        try:
            if chrome_version:
                self.driver = uc.Chrome(use_subprocess=True, options=self.options, version_main=chrome_version)
            else:
                self.driver = uc.Chrome(use_subprocess=True, options=self.options)
        except Exception as e:
            print(f"블라인드 드라이버 초기화 오류: {e}")
            # 재시도
            try:
                self.driver = uc.Chrome(use_subprocess=False, options=self.options)
            except Exception as e2:
                print(f"블라인드 드라이버 재시도 실패: {e2}")
                raise

        self.wait = WebDriverWait(self.driver, 10)
        self.prev_posts = []
        self.new_posts = []

    def get_published_date(self, published_date):
        from datetime import timedelta
        import sys
        import os

        # date_utils 임포트 (상위 디렉토리에서)
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'utils'))
            from date_utils import parse_relative_time

            # 상대 시간 표현 처리 (수집 시점 기준)
            result = parse_relative_time(published_date, datetime.now())
            if result:
                return result
        except ImportError:
            pass  # date_utils가 없는 경우 기존 로직으로 진행
        except Exception:
            pass  # 실패시 기존 로직으로 진행

        now = datetime.now()

        # "오늘", "어제" 처리
        if published_date.strip() == "오늘":
            return now
        if published_date.strip() == "어제":
            return now - timedelta(days=1)

        if re.match(r"^\d{2}\.\d{2}$", published_date.strip()):
            month, day = published_date.strip().split(".")
            year = now.year
            published_date = datetime(year=int(year), month=int(month), day=int(day), hour=0, minute=0, second=0)
            return published_date

        time_map = {
            "분": ("minutes", 1),
            "시": ("hours", 1),
            "일": ("days", 1)
        }

        for key, (unit, _) in time_map.items():
            if key in published_date:
                num = int(re.sub(r'[^0-9]', '', published_date))
                delta = timedelta(**{unit: num})
                return now - delta

        # YYYY-MM-DD 또는 YYYY.MM.DD 형식 처리
        try:
            published_date = published_date.replace(".", "-")
            if published_date[-1] == "-":
                published_date = published_date[:-1]
            return datetime.strptime(published_date, "%Y-%m-%d")
        except ValueError:
            return now  # 파싱 실패시 현재 시간 반환


    
    def infinite_scroll(self, max_posts=10, max_scroll_attempts=20):
        """제한된 무한 스크롤 (안전 장치 포함)"""
        scroll_attempts = 0
        no_change_count = 0

        while scroll_attempts < max_scroll_attempts and no_change_count < 3:
            current_scroll = self.driver.execute_script("return window.pageYOffset;")
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")

            self.driver.execute_script(f"window.scrollTo(0, {scroll_height});")
            print(f"scrollTo(0, {scroll_height}); 스크롤 중 ({scroll_attempts + 1}/{max_scroll_attempts})")
            time.sleep(3)  # 대기 시간 단축

            new_height = self.driver.execute_script("return document.body.scrollHeight")

            # 페이지 높이가 더 이상 변하지 않으면 카운터 증가
            if new_height == scroll_height:
                no_change_count += 1
                print(f"높이 변화 없음: {no_change_count}/3")
            else:
                no_change_count = 0

            scroll_attempts += 1

            # 안전 장치: 최대 스크롤 횟수 도달하면 종료
            if scroll_attempts >= max_scroll_attempts:
                print("⚠️ 최대 스크롤 횟수 도달, 스크롤 종료")
                break

            # 안전 장치: 높이 변화 없이 3회 연속이면 종료
            if no_change_count >= 3:
                print("⚠️ 페이지 끝 도달, 스크롤 종료")
                break
                

    def get_post(self, url):
        self.driver.get(url)
        time.sleep(5)

        from urllib.parse import unquote
        post_id = unquote(url.split("/")[-1])

        # 제목 찾기 (여러 선택자 시도)
        title_selectors = [".article-view-head > h2", "h2.title", ".post-title", "h2"]
        title = "제목 없음"
        for sel in title_selectors:
            try:
                title = self.driver.find_element(By.CSS_SELECTOR, sel).text.strip()
                if title:
                    break
            except NoSuchElementException:
                continue

        # 날짜 찾기 (여러 선택자 시도)
        date_selectors = [".article-view-head .date", ".date", "[class*='date']", "time", ".time"]
        published_date = None
        for sel in date_selectors:
            try:
                published_date = self.driver.find_element(By.CSS_SELECTOR, sel).text.strip()
                if published_date:
                    break
            except NoSuchElementException:
                continue

        if published_date:
            published_date = self.clean_published_date(published_date)
            published_date = self.get_published_date(published_date)
        else:
            published_date = datetime.now()

        # datetime을 문자열로 변환 (JSON 직렬화용)
        if isinstance(published_date, datetime):
            published_date = published_date.strftime("%Y-%m-%d %H:%M:%S")

        # 조회수 찾기
        view_count = "0"
        view_selectors = [".article-view-head .pv", ".pv", "[class*='view']"]
        for sel in view_selectors:
            try:
                view_count = self.driver.find_element(By.CSS_SELECTOR, sel).text.strip()
                view_count = view_count.replace("조회수", "").strip()
                if view_count:
                    break
            except NoSuchElementException:
                continue

        # 좋아요 수 찾기
        like_count = "0"
        like_selectors = [".article_info .like", ".like", "[class*='like']"]
        for sel in like_selectors:
            try:
                like_count = self.driver.find_element(By.CSS_SELECTOR, sel).text.strip()
                like_count = re.sub(r'[^0-9]', '', like_count)
                if like_count:
                    break
            except NoSuchElementException:
                continue
        like_count = 0 if like_count == '' else like_count

        try:
            content = self.driver.find_element(By.CSS_SELECTOR, "#contentArea").text.strip()
            if not content:
                content = title
        except NoSuchElementException:
            content = title

        # 사용자명 찾기
        username = "익명"
        try:
            username = self.driver.find_element(By.CSS_SELECTOR, ".name").text.strip()
        except NoSuchElementException:
            pass

        post_data = {
            "id": post_id,
            "title": title,
            "content": content,
            "published_date": published_date,
            "platform": "Blind",
            "link": url,
            "view_count": view_count,
            "like_count": like_count,
            "user_id": username,
        }
        comments = self.get_comments(post_id)
        self.driver.back()
        time.sleep(2)
        return post_data, comments

    def get_comments(self, post_id):
        comments = []
        comment_ids = []
        comment_containers = self.driver.find_elements(By.CSS_SELECTOR, ".comment_area")
        for i, comment_container in enumerate(comment_containers):
            try:
                comment_id = f"{post_id}_{i}"
                username = comment_container.find_elements(By.CSS_SELECTOR, ".name")
                if len(username) == 0:
                    continue
                username = username[0].text.strip()

                # 날짜 찾기 (여러 선택자 시도)
                published_date = None
                for sel in [".date", "[class*='date']", "time", ".time"]:
                    try:
                        published_date = comment_container.find_element(By.CSS_SELECTOR, sel).text.strip()
                        if published_date:
                            break
                    except NoSuchElementException:
                        continue

                if published_date:
                    published_date = self.clean_published_date(published_date)
                    published_date = self.get_published_date(published_date)
                else:
                    published_date = datetime.now()

                # datetime을 문자열로 변환
                if isinstance(published_date, datetime):
                    published_date = published_date.strftime("%Y-%m-%d %H:%M:%S")

                # 좋아요 수
                like_count = "0"
                try:
                    like_count = comment_container.find_element(By.CSS_SELECTOR, ".like").text.strip()
                    like_count = re.sub(r'[^0-9]', '', like_count)
                except NoSuchElementException:
                    pass
                like_count = 0 if like_count == '' else like_count

                # 댓글 내용
                content = ""
                try:
                    content = comment_container.find_element(By.CSS_SELECTOR, ".cmt-txt").text.strip()
                except NoSuchElementException:
                    continue

                parent_element = comment_container.find_element(By.XPATH, "..")
                parent_class = parent_element.get_attribute("class")
                if comment_ids and parent_class == "wrap-reply":
                    parent_id = comment_ids[-1]
                else:
                    parent_id = None

                if parent_id is None:
                    comment_ids.append(comment_id)

                comments.append({
                    "id": comment_id,
                    "username": username,
                    "content": content,
                    "blog_id": post_id,
                    "platform": "Blind",
                    "parent_id": parent_id,
                    "published_date": published_date,
                    "like_count": like_count,
                })
            except Exception as e:
                print(f"댓글 파싱 오류: {e}")
                continue

        return comments

    def clean_published_date(self, published_date):
        published_date = published_date.replace("작성일", "").replace("작성시간", "").replace("북마크", "").strip()
        return published_date



            
        


    def run(self, keyword, max_posts, start_date, end_date):
        max_posts = max_posts if max_posts and max_posts > 0 else 50 
        comment_data = []
        post_data = []
        count = 0

        self.driver.get(f"https://www.teamblind.com/kr/search/{keyword}")
        time.sleep(10)  # 더 긴 대기 시간
        
        # JavaScript 완전 로딩 대기
        self.driver.execute_script("return document.readyState") 
        time.sleep(5)
        
        # 제한된 스크롤 (최대 게시글 수에 따라 스크롤 횟수 조정)
        max_scroll_attempts = min(max_posts * 2, 15)  # 게시글 수의 2배, 최대 15회
        self.infinite_scroll(max_posts, max_scroll_attempts)
        
        # 스크롤 후 추가 대기
        time.sleep(5)

        prev_posts_count = len(self.prev_posts)

        # 다양한 게시물 선택자 시도 (블라인드 실제 구조 기반)
        post_selectors = [
            "a[href*='post']",      # 일반적인 post 링크
            "[class*='SearchResult']",  # 검색 결과 컴포넌트
            "[class*='PostItem']",      # 게시물 아이템
            "[class*='Post_']",         # 게시물 클래스
            ".search-result",           # 검색 결과
            ".post",                    # 게시물
            "li[class*='Post']",        # 리스트 아이템 게시물
            "div[class*='Post']",       # div 게시물
            "a",                        # 모든 링크 (최후 수단)
            "*[href*='/topics/']",      # 토픽 링크
            "*[href*='/posts/']"        # 게시물 링크
        ]
        self.new_posts = []
        selected_selector = None
        for selector in post_selectors:
            try:
                self.new_posts = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if self.new_posts:
                    selected_selector = selector
                    print(f"블라인드 게시물 선택자 '{selector}' 사용: {len(self.new_posts)}개 발견")
                    break
            except NoSuchElementException:
                continue
        new_posts_count = len(self.new_posts)
        
        
        
        i = 0

        # URL 목록 먼저 수집
        urls_to_process = []
        while i < len(self.new_posts) and len(urls_to_process) < (max_posts * 3 if max_posts else 50):
            self.new_posts = self.driver.find_elements(By.CSS_SELECTOR, selected_selector or ".article-list-pre")

            if i >= len(self.new_posts):
                break

            post = self.new_posts[i]
            url = None

            # selected_selector가 앵커 태그인 경우 직접 href 추출
            if selected_selector and selected_selector.startswith("a"):
                try:
                    url = post.get_attribute("href")
                except:
                    pass

            # 그렇지 않으면 내부에서 URL 찾기
            if not url or "post" not in url:
                url_selectors = [
                    "a[href*='/post/']",
                    "a[href*='post']",
                    ".tit > h3 > a",
                    "h3 > a",
                    ".title > a",
                    "a"
                ]
                for url_selector in url_selectors:
                    try:
                        url_element = post.find_element(By.CSS_SELECTOR, url_selector)
                        url = url_element.get_attribute("href")
                        if url and "post" in url:
                            break
                    except:
                        continue

            if url and "post" in url and url not in urls_to_process:
                urls_to_process.append(url)

            i += 1

        print(f"블라인드: {len(urls_to_process)}개 URL 수집 완료")

        # 개별 게시글 방문하여 날짜 확인 후 수집
        for url in urls_to_process:
            if max_posts and count >= max_posts:
                break

            try:
                posts, comments = self.get_post(url)

                # 게시글 날짜로 필터링
                if posts and posts.get('published_date'):
                    post_date_str = str(posts['published_date'])
                    if isinstance(posts['published_date'], datetime):
                        post_date_str = posts['published_date'].strftime('%Y-%m-%d')
                    elif len(post_date_str) > 10:
                        post_date_str = post_date_str[:10]

                    if start_date and end_date:
                        if post_date_str < start_date:
                            print(f"날짜 범위 이전: {post_date_str} < {start_date}")
                            continue
                        if post_date_str > end_date:
                            print(f"날짜 범위 이후: {post_date_str} > {end_date}")
                            continue

                    post_data.append(posts)
                    comment_data.extend(comments)
                    count += 1
                    print(f"블라인드 게시글 수집: {posts.get('title', 'N/A')[:30]}... ({post_date_str})")

            except Exception as e:
                print(f"블라인드 게시글 처리 오류: {e}")
                continue

        # 수집 완료 후 일괄 저장
        if post_data:
            save_to_json("Blind", post_data, comment_data)
            print(f"블라인드 크롤링 완료: 총 {len(post_data)}개 게시물, {len(comment_data)}개 댓글")
        
        return post_data, comment_data



if __name__ == "__main__":
    crawler = BlindCrawler()

    crawler.run("에스파", None, None, None)
    # crawler.get_post("https://www.teamblind.com/kr/post/%EC%A0%A4-%EC%84%B1%EA%B3%B5%ED%95%9C-%EC%97%90%EC%8A%A4%ED%8C%8C-%EB%85%B8%EB%9E%98%EB%8A%94-wgyqed1l")



    


            

            
            
    
