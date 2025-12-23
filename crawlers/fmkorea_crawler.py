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


class FmkoreaCrawler:

    def __init__(self):
        self.options = uc.ChromeOptions()
        self.options.add_argument("--headless")  # Headless 모드
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")  # GPU 가속 비활성화 (headless 안정성)
        self.options.add_argument("--window-size=800,600")  # 창 크기 설정
        # 브라우저 크래시 방지 옵션 추가
        self.options.add_argument("--disable-web-security")
        self.options.add_argument("--disable-features=VizDisplayCompositor")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-plugins")
        self.options.add_argument("--remote-debugging-port=0")  # 디버깅 포트 비활성화

        # Chrome 버전 자동 감지
        chrome_version = get_chrome_version()

        try:
            if chrome_version:
                self.driver = uc.Chrome(use_subprocess=True, options=self.options, version_main=chrome_version)
            else:
                self.driver = uc.Chrome(use_subprocess=True, options=self.options)
        except Exception as e:
            print(f"에펨코리아 드라이버 초기화 오류: {e}")
            # 재시도 (버전 없이)
            try:
                self.driver = uc.Chrome(use_subprocess=False, options=self.options)
            except Exception as e2:
                print(f"에펨코리아 드라이버 재시도 실패: {e2}")
                raise
        self.wait = WebDriverWait(self.driver, 10)
    

    def get_published_date(self, published_date):
        from datetime import timedelta

        now = datetime.now()
        time_map = {
            "분": ("minutes", 1),
            "시": ("hours", 1),
            "일": ("days", 1)
        }

        for key, (unit, _) in time_map.items():
            if key in published_date:
                num = int(re.sub(r'[^0-9]', '', published_date))
                delta = timedelta(**{unit: num})
                return (now - delta).strftime("%Y-%m-%d %H:%M:%S")
        return published_date

    def get_posts(self, url):
        self.driver.get(url)
        time.sleep(2)  # 페이지 로딩 대기
        
        post_id = url.split("/")[-1]
        
        try:
            title = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#bd_capture > div > div > div > h1 > span")
            )).text.strip()
        except TimeoutException:
            title = "제목 없음"
        
        try:
            published_date = self.driver.find_element(
                By.CSS_SELECTOR, "#bd_capture > div > div > div > span"
            ).text.strip()
            published_date = published_date.replace(".", "-")
        except NoSuchElementException:
            published_date = ""

        try:
            view_count = self.driver.find_element(
                By.CSS_SELECTOR, "#bd_capture > div > div > div > div > span:nth-child(1) > b"
            ).text.strip()
        except NoSuchElementException:
            view_count = "0"

        try:
            like_count = self.driver.find_element(
                By.CSS_SELECTOR, "#bd_capture > div > div > div > div > span:nth-child(2) > b"
            ).text.strip()
        except NoSuchElementException:
            like_count = "0"

        try:
            content = self.driver.find_element(By.CSS_SELECTOR, ".rd_body").text.strip()
        except NoSuchElementException:
            content = ""

        try:
            username = self.driver.find_element(
                By.CSS_SELECTOR, "#bd_capture > div.rd_hd.clear > div.board.clear > div.btm_area.clear > div:nth-child(1) > a"
            ).text.strip()
        except NoSuchElementException:
            username = "익명"

        post_data = {
            "id": post_id,
            "title": title,
            "content": content,
            "published_date": published_date,
            "platform": "FMKorea",
            "link": url,
            "view_count": view_count,
            "like_count": like_count,
            "user_id": username,
        }

        try:
            commment_total_page_element = self.driver.find_element(
                By.CSS_SELECTOR, "#cmtPosition > div.fdb_tag.bg_f_f9.css3pie > a > b"
            )
            commment_total_page = int(commment_total_page_element.text.strip())
            
            
            comment_visible_count = 100
            comment_total_page = math.ceil(commment_total_page / comment_visible_count)
            comments = self.get_comments(url, post_id, comment_total_page)
        except NoSuchElementException:
            comments = []

        return post_data, comments

    def find_comment_parent_id(self, comment_id, comments, depth):
        comment_reverse = comments[::-1]
        for comment in comment_reverse:
            if comment['depth'] == depth:
                return comment['id']
        return None

    def get_comments(self, url, post_id, total_page):
        comments = []
        for page in range(1, total_page + 1):
            comment_url = f"https://www.fmkorea.com/?mid=best&document_srl={post_id}&cpage={page}"
            self.driver.get(comment_url)
            time.sleep(5)
            print("comment page: ", page)

            try:
                comment_containers = self.driver.find_elements(By.CSS_SELECTOR, "li[id^='comment_']")
                
                for i, comment_container in enumerate(comment_containers):
                    try:
                        comment_id = comment_container.get_attribute('id')
                        
                        username = comment_container.find_element(By.CSS_SELECTOR, ".member_plate").text.strip()
                        
                        published_date = comment_container.find_element(By.CSS_SELECTOR, ".date").text.strip()
                        
                        content = comment_container.find_element(By.CSS_SELECTOR, ".comment-content").text.strip()

                        try:
                            like_count = comment_container.find_element(By.CSS_SELECTOR, ".voted_count").text.strip()
                        except NoSuchElementException:
                            like_count = "0"

                        depth = comment_container.get_attribute("style")
                        
                        if depth and "margin-left" in depth:
                            depth = depth.split("margin-left:")[1].split("%")[0]
                            parent_depth = int(depth) - 2
                            parent_id = self.find_comment_parent_id(comment_id, comments, parent_depth)
                        else:
                            parent_id = None
                            depth = 0
                        
                        comments.append({
                            "id": comment_id,
                            "username": username,
                            "start_count": None,
                            "content": content,
                            "blog_id": post_id,
                            "platform": "FMKorea",
                            "parent_id": parent_id,
                            "published_date": self.get_published_date(published_date),
                            "like_count": like_count,
                            "depth": depth,
                        })
                    except NoSuchElementException as e:
                        print(f"댓글 파싱 중 오류: {e}")
                        continue
                        
            except NoSuchElementException:
                print(f"페이지 {page}에서 댓글을 찾을 수 없습니다.")

        # depth 키 제거
        for comment in comments:
            if "depth" in comment:
                del comment["depth"]
        return comments

    def run(self, keyword, max_posts, start_date, end_date):
        search_url = f"https://www.fmkorea.com/search.php?act=IS&is_keyword={keyword}&mid=home&where=document&page=1"
        self.driver.get(search_url)
        time.sleep(3)
        
        try:
            total_page_element = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h3.subTitle > span")
            ))
            total_page_text = total_page_element.text.strip()
            total_page = int(total_page_text.replace(",", "").replace("(", "").replace(")", ""))
            
            visible_count = 10
            total_page = math.ceil(total_page / visible_count)
        except TimeoutException:
            print("검색 결과를 찾을 수 없습니다.")
            return [], []

        post_data = []
        comment_data = []
        count = 0

        for page in range(1, total_page + 1):
            print("page: ", page)
            url = f"https://www.fmkorea.com/search.php?act=IS&is_keyword={keyword}&mid=home&where=document&page={page}"
            self.driver.get(url)
            time.sleep(2)
            

            try:
                li_containers = self.driver.find_elements(By.CSS_SELECTOR, "#content > div > main > ul.searchResult > li")
                urls = []

                for li_container in li_containers:

                    published_date = li_container.find_element(By.CSS_SELECTOR, "span.time").text.strip()
                    
                    if start_date and end_date:
                        if not (start_date <= published_date <= end_date):
                            continue
                    urls.append(li_container.find_element(By.CSS_SELECTOR, "a").get_attribute("href"))

                
                for url in urls:
                    print("url: ", url)
                    posts, comments = self.get_posts(url)
                    post_data.append(posts)
                    comment_data.extend(comments)
                    save_to_json("FMKorea", [posts], comments)
                    count += 1
                    if max_posts and count >= max_posts:
                        return post_data, comment_data
                   
            except NoSuchElementException:
                print(f"페이지 {page}에서 검색 결과를 찾을 수 없습니다.")

        self.close()
        return post_data, comment_data

    def close(self):
        """브라우저 드라이버 종료"""
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    crawler = FmkoreaCrawler()
    try:
        post_data, comment_data = crawler.run("손흥민", None, None, None)
        print(f"수집된 게시글: {len(post_data)}개")
        print(f"수집된 댓글: {len(comment_data)}개")
    finally:
        crawler.close()