
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


class InvenCrawler:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless=new")  # Headless 모드
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")  # GPU 가속 비활성화 (headless 안정성)
        self.options.add_argument("--window-size=800,600")  # 창 크기 설정
        self.options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.options.add_experimental_option("prefs", {
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2  # 이미지 차단
            })
        self.driver = webdriver.Chrome(options=self.options)
    

    def get_id(self, url):
        if "?" in url:
            return url.split("/")[-1].split("?")[0]
        else:
            return url.split("/")[-1]

    def get_posts(self, url):
        try:
            if not self.get(url):
                return None, []
            time.sleep(2)
            post_id = self.get_id(url)
            
            # 요소가 존재하지 않을 경우를 대비한 안전한 추출
            try:
                title = self.driver.find_element(By.CSS_SELECTOR, "div.articleTitle").text.strip()
            except NoSuchElementException:
                print(f"제목을 찾을 수 없습니다: {url}")
                return None, []

            try:
                published_date = self.driver.find_element(By.CSS_SELECTOR, "div.articleDate").text.strip()
            except NoSuchElementException:
                print(f"날짜를 찾을 수 없습니다: {url}")
                return None, []

            try:
                username = self.driver.find_element(By.CSS_SELECTOR, "div.articleWriter").text.strip()
            except NoSuchElementException:
                username = "Unknown"

            try:
                content = self.driver.find_element(By.CSS_SELECTOR, "div#powerbbsContent").text.strip()
                if not content:
                    # 내용이 없으면 제목을 내용으로 사용
                    content = title
            except NoSuchElementException:
                # 내용을 찾을 수 없으면 제목을 내용으로 사용
                content = title

            post_data = {
                "id": post_id,
                "title": title,
                "content": content,
                "published_date": published_date,
                "platform": "Inven",
                "link": url,
                "view_count": None,
                "like_count": None,
                "user_id": username,
            }
            comments = self.get_comments(post_id)
            print(f"수집 완료: {post_id}")

            self.driver.back()
            time.sleep(3)
            return post_data, comments
            
        except Exception as e:
            print(f"게시물 정보 추출 실패: {e}")
            try:
                self.driver.back()
                time.sleep(2)
            except:
                pass
            return None, []


    def get_published_date(self, published_date):
        from datetime import timedelta


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
    

    def get_comments(self, post_id):

        comments = []
        comment_ids = []
        comment_containers = self.driver.find_elements(By.CSS_SELECTOR, "li[id^='cmt']")
        for i, comment_container in enumerate(comment_containers):
            comment_id = f"{post_id}_{i}"
            username = comment_container.find_element(By.CSS_SELECTOR, ".nickname").text.strip()
            published_date = comment_container.find_element(By.CSS_SELECTOR, ".date").text.strip()
            like_count = comment_container.find_element(By.CSS_SELECTOR, "span[id^='likeCmt']").text.strip()
            content = comment_container.find_element(By.CSS_SELECTOR, ".content").text.strip()

            if comment_ids and "replyCmt" in comment_container.get_attribute("class"):
                parent_id = comment_ids[-1]
            else:
                parent_id = None
                comment_ids.append(comment_id)
            
            comments.append({
                "id": comment_id,
                "username": username,
                "content": content,
                "blog_id": post_id,
                "platform": "Inven",
                "parent_id": parent_id,
                "published_date": published_date,
                "like_count": like_count,
                
            })

        return comments

    def get(self, url):
        try:
            self.driver.set_page_load_timeout(10)
            
            self.driver.get(url)
            return True
        except TimeoutException as e:
            print(f"타임아웃 발생: {e}")
            return False

        

    def run(self, keyword, max_posts, start_date=None, end_date=None):
        post_data = []
        comment_data = []
        count = 0
        page = 1
        max_pages = 30  # 최대 30페이지까지만 검색
        consecutive_empty_pages = 0
        max_empty_pages = 3
        consecutive_no_urls = 0  # URL이 없는 페이지 카운터 (별도)
        max_no_url_pages = 3
        consecutive_out_of_range = 0
        max_out_of_range = 30  # 연속 30개 게시물이 범위 밖이면 중단
        
        while page <= max_pages:
            print(f"인벤 페이지 {page} 검색 중...")
            
            # 올바른 인벤 검색 URL 사용 (날짜 필터 포함)
            if start_date and end_date:
                # 날짜 형식을 인벤 형식으로 변환 (YYYY.MM.DD)
                start_formatted = start_date.replace('-', '.')
                end_formatted = end_date.replace('-', '.')
                url = f"https://www.inven.co.kr/search/webzine/article/{keyword}/{page}?sort=recency&dt=s&sDate={start_formatted}&eDate={end_formatted}"
            else:
                url = f"https://www.inven.co.kr/search/webzine/article/{keyword}/{page}?sort=recency"
            
            try:
                self.driver.get(url)
                time.sleep(2)

                # 실제 인벤 검색 결과 페이지 CSS 선택자 (스크린샷 기반)
                selectors_to_try = [
                    ".news_list .item",        # 뉴스 리스트 아이템 (스크린샷에서 확인됨)
                    ".item",                   # 아이템 클래스
                    "li.item",                 # li 태그의 item 클래스
                    "ul.news_list > li",       # 뉴스 리스트 하위 li
                    ".search-result-item",     # 일반적인 검색 결과
                    ".result-item", 
                    "a[href*='/webzine/']",    # 인벤 웹진 링크
                    "a[href*='/board/']"       # 게시판 링크
                ]
                
                rows = []
                for selector in selectors_to_try:
                    try:
                        rows = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if rows:
                            print(f"인벤 선택자 '{selector}' 사용: {len(rows)}개 발견")
                            break
                    except:
                        continue
                if len(rows) == 0:
                    consecutive_empty_pages += 1
                    print(f"빈 페이지 {consecutive_empty_pages}/{max_empty_pages}")
                    if consecutive_empty_pages >= max_empty_pages:
                        print("연속 빈 페이지로 인해 검색 종료")
                        break
                    page += 1
                    continue
                else:
                    consecutive_empty_pages = 0

                urls = []
                like_counts = []
                view_counts = []
                page_found_posts = 0
                
                # 실제 게시물 링크 직접 추출
                all_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href]')
                for link in all_links:
                    try:
                        href = link.get_attribute('href')
                        if not href:
                            continue
                            
                        # 게시물일 가능성이 높은 링크만 선택
                        if any(pattern in href for pattern in ['/board/', '/webzine/', '/article']):
                            text = link.text.strip()
                            if text and len(text) > 5:  # 의미있는 텍스트가 있는 링크만
                                urls.append(href)
                                like_counts.append("0")  # 기본값 설정
                                view_counts.append("0")  # 기본값 설정
                                print(f"인벤 게시물 링크 발견: {text[:30]}... | {href}")
                                if len(urls) >= 10:  # 페이지당 최대 10개
                                    break
                    except Exception as e:
                        continue
                
                # URL이 없는 페이지는 빈 페이지로 간주
                if len(urls) == 0:
                    consecutive_no_urls += 1
                    print(f"유효한 URL이 없는 페이지 {consecutive_no_urls}/{max_no_url_pages}")
                    if consecutive_no_urls >= max_no_url_pages:
                        print("연속 유효하지 않은 페이지로 인해 검색 종료")
                        break
                    page += 1
                    continue
                else:
                    consecutive_no_urls = 0  # URL이 있으면 초기화
                
                for url, like_count, view_count in zip(urls, like_counts, view_counts):
                    if max_posts and count >= max_posts:
                        print(f"최대 게시물 수({max_posts})에 도달하여 종료")
                        return post_data, comment_data
                        
                    print("page: ", page, "url: ", url)

                    try:
                        posts, comments = self.get_posts(url)
                        if posts is not None:  # None 체크 추가
                            posts["like_count"] = like_count
                            posts["view_count"] = view_count
                            post_data.append(posts)
                            comment_data.extend(comments)
                            # 개별 저장 제거 (일괄 저장으로 변경)
                            count += 1
                            # save_to_json("Inven", [posts], comments)
                    except Exception as e:
                        print(f"게시물 처리 중 오류: {e}")
                        continue

                print(f"페이지 {page}: {page_found_posts}개 게시물 수집")
                
            except Exception as e:
                print(f"페이지 {page} 처리 중 오류: {e}")
                # 오류 발생 시에도 다음 페이지로 진행
                
            # 반드시 페이지 증가 (무한루프 방지)
            page += 1
        
        # 수집 완료 후 일괄 저장
        if post_data:
            save_to_json("Inven", post_data, comment_data)
            print(f"인벤 크롤링 완료: 총 {len(post_data)}개 게시물, {len(comment_data)}개 댓글")
        
        return post_data, comment_data


                
if __name__ == "__main__":
    crawler = InvenCrawler()
    crawler.run(keyword="리니지", max_posts=None)