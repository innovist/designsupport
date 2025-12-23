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


class TheqooCrawler:
    def __init__(self):
        
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless")  # Headless 모드
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")  # GPU 가속 비활성화 (headless 안정성)
        self.options.add_argument("--window-size=800,600")  # 창 크기 설정
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
    

    def get_published_date(self, published_date):
        from datetime import timedelta


        if re.match(r"^\d{2}\:\d{2}$", published_date.strip()):
            hour, minute = published_date.strip().split(":")
            now = datetime.now()
            published_date = datetime(year=int(now.year), month=int(now.month), day=int(now.day), hour=int(hour), minute=int(minute), second=0)
            return published_date.strftime("%Y-%m-%d %H:%M")
        elif re.match(r"^\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}$", published_date.strip()):
            return datetime.strptime(published_date, "%Y.%m.%d %H:%M").strftime("%Y-%m-%d %H:%M")
        elif re.match(r"^\d{2}\.\d{2}$", published_date.strip()):
            month, day = published_date.strip().split(".")
            now = datetime.now()
            published_date = datetime(year=int(now.year), month=int(month), day=int(day), hour=0, minute=0, second=0)
            return published_date.strftime("%Y-%m-%d")

        return datetime.strptime(published_date, "%Y.%m.%d").strftime("%Y-%m-%d")

    def get_posts(self, url):
        self.driver.get(url)
        time.sleep(2)
        if "?" in url:
            post_id = url.split("/")[-1].split("?")[0]
        else:
            post_id = url.split("/")[-1]

        title = self.driver.find_element(By.CSS_SELECTOR, "span.title").text.strip()

        published_date = self.driver.find_element(By.CSS_SELECTOR, "div.rd.rd_nav_style2.clear > div.rd_hd.clear > div.board.clear > div > div.side.fr > span").text.strip()
        published_date = f"{self.get_published_date(published_date)}"

        view_count_elem = self.driver.find_element(By.CSS_SELECTOR, "div.count_container")
        view_count_html = view_count_elem.get_attribute('outerHTML').split('<i class="far fa-comment-dots"></i>')[0]
        view_count = re.sub(r'[^0-9]', '', view_count_html)
        
        content = self.driver.find_element(By.CSS_SELECTOR, 'article[itemprop="articleBody"]').text.strip()

        post_data = {
            "id": post_id,
            "title": title,
            "content": content,
            "published_date": published_date,
            "platform": "Theqoo",
            "link": url,
            "view_count": view_count,
            "like_count": None,
            "user_id": None,
        }
        # comments = self.get_comments(post_id)
        comments = []
        self.driver.back()
        time.sleep(2)
        return post_data, comments

    def click_comment_more_button(self):
        while True:
            try:
                comment_more_button = self.driver.find_elements(By.CSS_SELECTOR, ".show_more")
                if len(comment_more_button) > 0:
                    comment_more_button[0].click()
                    time.sleep(1)
                else:
                    break
                
            except:
                break
        

    def get_comments(self, post_id):
        comments = []
        comment_containers = self.driver.find_elements(By.CSS_SELECTOR, "li[id^='comment_']")
        print("댓글 개수: ", len(comment_containers))
        self.click_comment_more_button()
        for comment_container in comment_containers:
            comment_id = f"{post_id}_{comment_container.get_attribute('id').split('_')[-1]}"
            content = comment_container.find_element(By.CSS_SELECTOR, ".xe_content").text
            print("content: ", content)
            if "비회원은 작성한 지 1시간 이내의 댓글은 읽을 수 없습니다." in content or "삭제된 댓글입니다." in content:
                continue
            print("--------------------------------")

            published_date = comment_container.find_element(By.CSS_SELECTOR, ".date").text

            comment_data = {
                "id": comment_id,
                "username": None,
                "content": content,
                "blog_id": post_id,
                "platform": "Theqoo",
                "parent_id": None,
                "published_date": published_date,
                "like_count": None,
            }

            comments.append(comment_data)
        
        return comments


    def run(self, keyword, max_posts, start_date=None, end_date=None):
        import urllib.parse

        comment_data = []
        post_data = []
        count = 0

        # URL 직접 접근 방식으로 검색 (폼 제출보다 안정적)
        encoded_keyword = urllib.parse.quote(keyword)
        search_url = f"https://theqoo.net/index.php?mid=hot&search_keyword={encoded_keyword}&search_target=title_content"
        print("search_url: ", search_url)
        self.driver.get(search_url)
        time.sleep(3)

        while True:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr:not(.notice):not(.notice_expand)")

            urls = []

            for row in rows:
                # td 요소가 있는지 확인 (카테고리 행 제외)
                tds = row.find_elements(By.TAG_NAME, "td")
                if len(tds) < 4:
                    continue

                try:
                    published_date = row.find_element(By.CSS_SELECTOR, "td.time").text.strip()
                except NoSuchElementException:
                    continue

                published_date = self.get_published_date(published_date)

                date_match = re.match(r"(\d{4}-\d{2}-\d{2})", published_date)
                date = date_match.group(1) if date_match else published_date
                if start_date and end_date:
                    if not (start_date <= date <= end_date):
                        continue
                try:
                    url = row.find_element(By.CSS_SELECTOR, "td.title > a").get_attribute("href")
                    urls.append(url)
                except NoSuchElementException:
                    continue


            for url in urls:
                print("url: ", url)
                
                posts, comments = self.get_posts(url)
                post_data.append(posts)
                comment_data.extend(comments)

                
                save_to_json("Theqoo", [posts], comments)
                count += 1
                if max_posts and count >= max_posts:
                    return post_data, comment_data
            

            next_button = self.driver.find_element(By.CSS_SELECTOR, ".next > a")
            if  "disable" in  next_button.get_attribute("class"):
                break
            
            next_button.click()
            time.sleep(2)

        return post_data, comment_data


            

if __name__ == "__main__":
    crawler = TheqooCrawler()
    crawler.run("손흥민", None)

    
