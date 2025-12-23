import time
from datetime import datetime, timedelta
import os
import re
from common import get_url_query, save_to_json
import math
import sys

# date_utils import 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'utils'))
try:
    from date_utils import normalize_date_with_relative
except ImportError:
    normalize_date_with_relative = None
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
import undetected_chromedriver as uc
from urllib.parse import quote


class RuliwebCrawler:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless=new")  # Headless 모드
        self.options.add_argument("--page-load-strategy=eager")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-gpu")  # GPU 가속 비활성화 (headless 안정성)
        self.options.add_argument("--window-size=800,600")  # 창 크기 설정
        self.options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.options.add_argument('--blink-settings=imagesEnabled=false')
        self.driver = webdriver.Chrome(options=self.options)
        self.timeout=10  # 타임아웃을 10초로 설정 (멀티스레딩에서 빠른 실패)

    def parse_ruliweb_date(self, date_text):
        """
        루리웹 날짜 표시 형식을 표준 날짜로 변환
        - 2025.09.05 → 2025-09-05
        - 1시간 전, 25분 전 → 오늘 날짜
        - 어제 → 어제 날짜
        - HH:MM → 오늘 날짜 + 시간
        """
        now = datetime.now()
        today = now.date()
        
        # 공백 제거 및 소문자 변환
        date_text = date_text.strip()
        
        # 1. 정확한 날짜 형식 (2025.09.05, 2025-09-05, 25.09.05)
        if re.match(r'\d{2,4}[\.\-]\d{1,2}[\.\-]\d{1,2}', date_text):
            # 점을 하이픈으로 변환
            normalized = date_text.replace('.', '-')
            try:
                # 2자리 년도인 경우 4자리로 변환
                parts = normalized.split()[0].split('-')
                if len(parts) == 3 and len(parts[0]) == 2:
                    year = int(parts[0])
                    # 50 이하는 20xx년, 51 이상은 19xx년으로 처리 (하지만 현재는 대부분 20xx년)
                    if year <= 50:
                        parts[0] = str(2000 + year)
                    else:
                        parts[0] = str(1900 + year)
                    normalized = '-'.join(parts)
                else:
                    normalized = normalized.split()[0]
                    
                return datetime.strptime(normalized, '%Y-%m-%d').strftime('%Y-%m-%d')
            except:
                pass
        
        # 2. 상대 시간 표현 (정확한 계산)
        if '분' in date_text and '전' in date_text:
            try:
                minutes = int(re.search(r'(\d+)분', date_text).group(1))
                actual_time = now - timedelta(minutes=minutes)
                return actual_time.strftime('%Y-%m-%d')
            except:
                return today.strftime('%Y-%m-%d')

        if '시간' in date_text and '전' in date_text:
            try:
                hours = int(re.search(r'(\d+)시간', date_text).group(1))
                actual_time = now - timedelta(hours=hours)
                return actual_time.strftime('%Y-%m-%d')
            except:
                return today.strftime('%Y-%m-%d')
            
        if '어제' in date_text:
            # "어제" → 어제
            yesterday = today - timedelta(days=1)
            return yesterday.strftime('%Y-%m-%d')
            
        # 3. 시간만 표시 (HH:MM)
        if re.match(r'\d{1,2}:\d{2}', date_text):
            # 시간만 있으면 오늘로 간주
            return today.strftime('%Y-%m-%d')
            
        # 4. 파싱 실패 시 오늘로 처리
        print(f"⚠️ 날짜 파싱 실패, 오늘로 처리: {date_text}")
        return today.strftime('%Y-%m-%d')

        
    
    def get_id(self, url):
        if "?" in url:
            return url.split("/")[-1].split("?")[0]
        else:
            return url.split("/")[-1]


    def get(self, url):
        try:
            self.driver.set_page_load_timeout(self.timeout)
            
            self.driver.get(url)
            return True
        except TimeoutException as e:
            print(f"타임아웃 발생: {e}")
            return False

    def get_posts(self, url, start_date=None, end_date=None):
        if not self.get(url):
            return {}, []
        time.sleep(2)
        post_id = self.get_id(url)
        title = self.driver.find_element(By.CSS_SELECTOR, ".subject_inner_text").text.strip()

        published_date_raw = self.driver.find_element(By.CSS_SELECTOR, "span.regdate").text.strip()
        published_date = self.parse_ruliweb_date(published_date_raw)
        
        only_date = published_date

        if start_date and end_date:
            # 역시간순: 날짜가 start_date보다 이전이면 빈 데이터 반환 (범위 지나침)
            if only_date < start_date:
                return {}, []
            # 날짜가 end_date보다 이후면 빈 데이터 반환 (아직 범위 전)
            elif only_date > end_date:
                return {}, []


        actions = self.driver.find_element(By.CSS_SELECTOR, "#board_read > div > div.board_main > div.board_main_top > div.user_view > div.row.user_view_target > div.col.user_info_wrapper > div > p:nth-child(5)").text.strip()
        actions = actions.split("|")
        if actions:
            like_count = actions[0].strip()
            like_count = like_count.replace("추천", "")
            
            view_count = actions[1].strip()
            view_count = view_count.replace("조회", "")
        else:
            like_count = None
            view_count = None
        
        try:
            content = self.driver.find_element(By.CSS_SELECTOR, ".view_content").text.strip()
            if not content:
                # 내용이 없으면 제목을 내용으로 사용
                content = title
        except NoSuchElementException:
            # 내용을 찾을 수 없으면 제목을 내용으로 사용
            content = title
        username = self.driver.find_element(By.CSS_SELECTOR, "a.nick").text.strip()

        post_data = {
            "id": post_id,
            "title": title,
            "content": content,
            "published_date": published_date,
            "platform": "Ruliweb",
            "link": url,
            "view_count": view_count,
            "like_count": like_count,
            "user_id": username,
        }

        comments = self.get_comments(post_id)
        self.driver.set_page_load_timeout(-1)

        self.driver.back()
        time.sleep(3)
        return post_data, comments

    def get_comments(self, post_id):
        comments = []
        comment_ids = []
        comment_containers = self.driver.find_elements(By.CSS_SELECTOR, ".comment_element")

        for i, comment_container in enumerate(comment_containers):
            comment_id = f"{post_id}_{i}"
            
            try:
                username = comment_container.find_element(By.CSS_SELECTOR, ".nick_link").text.strip()
            except NoSuchElementException:
                username = "Unknown"
            
            try:
                # 다양한 날짜 선택자 시도
                date_selectors = [".time", ".date", ".regdate", "span.time", "span.date"]
                published_date = None
                for selector in date_selectors:
                    try:
                        published_date = comment_container.find_element(By.CSS_SELECTOR, selector).text.strip()
                        if published_date:
                            break
                    except NoSuchElementException:
                        continue
                
                if not published_date:
                    published_date = "Unknown"
                else:
                    # 루리웹 날짜 파싱 적용
                    published_date = self.parse_ruliweb_date(published_date)
            except Exception:
                published_date = "Unknown"

            try:
                like_count = comment_container.find_element(By.CSS_SELECTOR, ".btn_like").text.strip()
            except NoSuchElementException:
                like_count = "0"

            try:
                content = comment_container.find_element(By.CSS_SELECTOR, ".text_wrapper > .text").text.strip()
            except NoSuchElementException:
                content = "내용 없음"

            if comment_ids and "child" in comment_container.get_attribute("class"):
                parent_id = comment_ids[-1]
            else:
                parent_id = None
                comment_ids.append(comment_id)
            
            comments.append({
                "id": comment_id,
                "username": username,
                "content": content,
                "blog_id": post_id,
                "platform": "Ruliweb",
                "parent_id": parent_id,
                "published_date": published_date,
                "like_count": like_count,
                
            })

        return comments
    
    def _check_page_dates(self):
        """목록 페이지에서 날짜들을 확인해서 목표 날짜 범위에 있는지 판단"""
        try:
            # 목록 페이지의 모든 날짜 요소 찾기
            time_elements = self.driver.find_elements(By.CSS_SELECTOR, "span.time")
            
            if not time_elements:
                return True, False  # 날짜를 찾을 수 없으면 일단 계속 진행
            
            page_dates = []
            for elem in time_elements:
                date_text = elem.text.strip()
                if not date_text:
                    continue
                
                
                try:
                    # "2025.02.05" 형식을 "2025-02-05" 형식으로 변환
                    if '.' in date_text and len(date_text.split('.')) == 3:
                        year, month, day = date_text.split('.')
                        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                        page_dates.append(date_obj)
                except Exception as parse_error:
                    continue
            
            if not page_dates:
                return True, False  # 유효한 날짜가 없으면 일단 계속 진행
            
            start_dt = datetime.strptime(self.start_date, "%Y-%m-%d") if self.start_date else datetime.min
            end_dt = datetime.strptime(self.end_date, "%Y-%m-%d") if self.end_date else datetime.max
            
            # 페이지의 최신/최오래된 날짜 확인
            latest_date = max(page_dates)
            oldest_date = min(page_dates)
            
            
            # 목표 범위와 교집합 있는지 확인
            page_in_range = (oldest_date <= end_dt) and (latest_date >= start_dt)
            past_end_date = latest_date < start_dt  # 모든 게시글이 시작날짜보다 과거
            
            return page_in_range, past_end_date
            
        except Exception as e:
            return True, False  # 오류 시 일단 계속 진행

    def _get_list_page_url_dates(self):
        """목록 페이지에서 URL과 날짜 매핑 생성"""
        try:
            # 게시물 제목 링크와 날짜를 동시에 추출
            search_results = self.driver.find_elements(By.CSS_SELECTOR, "li.search_result_item")
            url_date_map = {}
            
            for result in search_results:
                try:
                    # 제목 링크 찾기
                    title_link = result.find_element(By.CSS_SELECTOR, ".title a")
                    url = title_link.get_attribute("href")
                    
                    # 같은 항목 내에서 날짜 찾기
                    time_elem = result.find_element(By.CSS_SELECTOR, "span.time")
                    date_text = time_elem.text.strip()
                    
                    if url and date_text and '.' in date_text:
                        # "2025.02.05" -> "2025-02-05" 형식으로 변환
                        year, month, day = date_text.split('.')
                        normalized_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        url_date_map[url] = normalized_date
                        
                except Exception:
                    continue
                    
            return url_date_map
            
        except Exception as e:
            return {}

    def run(self, keyword, max_posts, start_date=None, end_date=None):
        import time
        
        # 3분 타임아웃 설정 (멀티스레딩 호환)
        start_time = time.time()
        timeout_seconds = 180  # 3분
        
        try:
            self.start_date = start_date
            self.end_date = end_date
            post_data = []
            comment_data = []
            page = 1
            count = 0
            max_pages = 50  # 더 많은 페이지 검색 가능 (날짜 사전 확인으로 효율화)
            consecutive_empty_pages = 0
            max_empty_pages = 3
            consecutive_old_pages = 0  # 연속으로 날짜 범위를 벗어난 페이지 수
            max_old_pages = 3  # 연속 3페이지가 모두 범위 밖이면 종료

            while page <= max_pages:
                # 타임아웃 체크 (멀티스레딩 호환)
                if time.time() - start_time > timeout_seconds:
                    print("⏰ 루리웹 크롤러 3분 타임아웃 - 강제 종료")
                    break
                    
                print(f"루리웹 페이지 {page} 검색 중...")
                url = f"https://bbs.ruliweb.com/search?q={keyword}&op=&page={page}#board_search&gsc.tab=0&gsc.q={keyword}&gsc.page=1"
                
                try:
                    if not self.get(url):
                        print(f"페이지 {page} 로드 실패")
                        break
                    time.sleep(2)

                    # 다양한 제목 선택자 시도  
                    title_selectors = [
                        "#board_search .title",
                        ".search_result .title", 
                        ".board_search .title",
                        ".title a",
                        ".subject a",
                        "a[href*='read']",
                        ".list_subject a",          # 리스트 제목
                        ".board_list .subject a",   # 게시판 리스트 제목
                        ".article_subject a",       # 기사 제목
                        "li.search_result_item .title a",  # 검색 결과 아이템 제목
                        ".board_title a",           # 게시판 제목
                        "a[onclick*='read']"        # 읽기 onclick 링크
                    ]
                    a_tags = []
                    for selector in title_selectors:
                        try:
                            a_tags = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if a_tags:
                                print(f"루리웹 제목 선택자 '{selector}' 사용: {len(a_tags)}개 발견")
                                break
                        except NoSuchElementException:
                            continue
                    if len(a_tags) == 0:
                        consecutive_empty_pages += 1
                        print(f"빈 페이지 {consecutive_empty_pages}/{max_empty_pages}")
                        if consecutive_empty_pages >= max_empty_pages:
                            print("연속 빈 페이지로 인해 검색 종료")
                            break
                        page += 1
                        continue
                    else:
                        consecutive_empty_pages = 0

                    # 페이지 날짜 범위 사전 확인
                    if start_date and end_date:
                        page_in_range, past_end_date = self._check_page_dates()
                        if past_end_date:
                            print(f"페이지 {page}의 모든 게시물이 시작 날짜보다 과거, 검색 종료")
                            break
                        elif not page_in_range:
                            consecutive_old_pages += 1
                            print(f"페이지 {page}는 날짜 범위 밖 ({consecutive_old_pages}/{max_old_pages}), 다음 페이지로")
                            if consecutive_old_pages >= max_old_pages:
                                print(f"연속 {max_old_pages}페이지가 모두 날짜 범위 밖, 검색 종료")
                                break
                            page += 1
                            continue
                        else:
                            consecutive_old_pages = 0  # 범위 내 페이지 발견 시 리셋

                    # URL과 날짜 매핑 생성
                    url_date_map = self._get_list_page_url_dates()
                    urls = [a_tag.get_attribute("href") for a_tag in a_tags]
                    print(len(urls))
                    page_found_posts = 0
                    page_out_of_range_count = 0  # 이 페이지에서 범위 밖 게시물 수
                    
                    for url in urls:
                        if max_posts and count >= max_posts:
                            print(f"최대 게시물 수({max_posts})에 도달하여 종료")
                            return post_data, comment_data

                        # 목록에서 가져온 날짜로 사전 필터링
                        list_date = url_date_map.get(url)
                        if start_date and end_date and list_date:
                            # 역시간순: 범위 밖 게시물은 건너뛰기
                            if list_date < start_date or list_date > end_date:
                                page_out_of_range_count += 1
                                # 이 페이지에서 너무 많은 게시물이 범위 밖이면 다음 페이지로
                                if page_out_of_range_count >= 10:  # 한 페이지에서 10개 이상 범위 밖이면 스킵
                                    print(f"페이지 {page}에서 10개 이상 게시물이 날짜 범위 밖, 다음 페이지로")
                                    break
                                continue

                        print("page: ", page, "url: ", url)
                        posts, comments = self.get_posts(url, start_date, end_date)
                        
                        if posts:
                            page_found_posts += 1
                            
                            post_data.append(posts)
                            comment_data.extend(comments)
                            count += 1

                    print(f"페이지 {page}: {page_found_posts}개 게시물 수집")
                    page += 1
                    
                except Exception as e:
                    print(f"페이지 {page} 처리 중 오류: {e}")
                    break

            # 수집 완료 후 일괄 저장
            if post_data:
                save_to_json("Ruliweb", post_data, comment_data)
                print(f"루리웹 크롤링 완료: 총 {len(post_data)}개 게시물, {len(comment_data)}개 댓글")
            
            return post_data, comment_data
            
        except TimeoutError as e:
            print(f"⏰ 루리웹 크롤링 타임아웃: {e}")
            # 타임아웃 시에도 수집된 데이터는 저장
            if post_data:
                save_to_json("Ruliweb", post_data, comment_data) 
                print(f"타임아웃 전까지 수집: {len(post_data)}개 게시물, {len(comment_data)}개 댓글")
            return post_data, comment_data
        except Exception as e:
            print(f"❌ 루리웹 크롤링 오류: {e}")
            return [], []
        finally:
            # 타임아웃 종료 (멀티스레딩에서는 별도 해제 불필요)
            pass
            
if __name__ == "__main__":
    crawler = RuliwebCrawler()
    crawler.run("리니지", None)

            
    
        
    