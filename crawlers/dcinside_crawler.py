import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote
from selenium.common.exceptions import TimeoutException

from common import extract_numbers, save_to_json, is_date_in_range, filter_by_date_range

# 로그 시스템 임포트 (total_crawler가 아닌 경우 대비)
try:
    from total_crawler import crawler_logger, log_event
except ImportError:
    # 단독 실행시 간단한 로깅
    import logging
    crawler_logger = logging.getLogger('dcinside')
    handler = logging.StreamHandler()
    crawler_logger.addHandler(handler)
    crawler_logger.setLevel(logging.INFO)
    def log_event(logger, level, platform, message):
        logger.info(f"[{level}] [{platform}] {message}")
import pandas as pd

class DcinsideCrawler:
    """
    DCInside 게시물 및 댓글 크롤러 (requests.Session 사용)
    """
    def __init__(self, keyword=None, start_date=None, end_date=None, max_posts=100):

        self.keyword = keyword
        self.start_date = start_date
        self.end_date = end_date
        self.max_posts = 99999 if max_posts is None else max_posts
        self.base_url = "https://search.dcinside.com/post/p/{page}/q/{keyword}"
        self.comment_api_url = "https://gall.dcinside.com/mgallery/board/comment/"
        
        self.contents_data = []
        self.comments_data = []
        self.post_count = 0

        # --- requests.Session 객체 생성 ---
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        })
        self.driver = self._setup_driver()

    def _setup_driver(self):
        """Selenium 웹 드라이버를 설정하고 반환합니다. (선택적)"""
        try:
            options = Options()
            options.add_argument("--headless")  # Headless 모드
            options.add_argument("--window-size=800x600")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
            
            # 성능 최적화 옵션 추가 - 더 강력한 차단
            options.add_argument("--disable-images")
            options.add_argument("--disable-plugins")  
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-background-networking")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-client-side-phishing-detection")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-translate")
            options.add_argument("--hide-scrollbars")
            options.add_argument("--mute-audio")
            
            # 광고 차단
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.managed_default_content_settings.media_stream": 2,
            }

            options.add_argument('--blink-settings=imagesEnabled=false')
            options.add_experimental_option("prefs", prefs)
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            # 타임아웃 설정 (봇 탐지 우회를 위해 적절히 설정)
            driver.set_page_load_timeout(10)  # 페이지 로드 타임아웃 10초
            driver.implicitly_wait(3)  # 요소 대기 시간 3초
            print(" [정보] Selenium 드라이버 초기화 성공 (댓글 수집 가능)")
            return driver
        except Exception as e:
            print(f" [경고] Selenium 드라이버 초기화 실패 - 댓글 수집 건너뜀: {e}")
            return None
        # ------------------------------------

    def _get_post_details(self, post_url):
        """게시물 상세 페이지에서 정보 추출"""
        try:
            # URL에서 gall_id와 post_no 직접 추출
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(post_url)
            query_params = parse_qs(parsed_url.query)
            
            gall_id = query_params.get('id', [None])[0]
            post_no = query_params.get('no', [None])[0]
            
            if not gall_id or not post_no:
                print(f" [오류] URL에서 id 또는 no 파라미터를 찾을 수 없습니다: {post_url}")
                return None, None, None
            
            # --- session.get 사용 ---
            response = self.session.get(post_url)
            
            response.raise_for_status()
            # print(response.text)
            soup = BeautifulSoup(response.text, 'html.parser')

            title_elem = soup.select_one('.title_subject')
            content_elem = soup.select_one('.writing_view_box')
            date_elem = soup.select_one('.gall_date')

            title = title_elem.text.strip() if title_elem else "제목 없음"
            content = content_elem.text.strip() if content_elem else ""
            published_date = date_elem['title'] if date_elem and 'title' in date_elem.attrs else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 이미지만 있거나 내용이 의미 없는 경우 제목으로 대체
            if not content or len(content.strip()) < 10 or content.strip() in ["", "ㅋㅋㅋ", "ㅎㅎㅎ", "ㅠㅠㅠ", "...", "ㅇㅇ"]:
                content = title

            
            view_count = soup.select_one(".gall_count").get_text(strip=True)
            view_count = extract_numbers(view_count)
            view_count = view_count[0]

            like_count = soup.select_one(".gall_reply_num").get_text(strip=True)
            like_count = extract_numbers(like_count)
            like_count = like_count[0]

            post_data = {
                'id': post_no,
                'title': title,
                'content': content,
                'view_count': view_count,
                'like_count': like_count,
                'published_date': published_date,
                'link': post_url,
                'platform': 'dcinside',
                
            }
            
            return post_data, gall_id, post_no, soup

        except requests.RequestException as e:
            print(f" [오류] 게시물 상세 페이지 요청 실패: {post_url}, {e}")
            log_event(crawler_logger, 'ERROR', 'DC인사이드', f'게시물 상세 페이지 요청 실패: {post_url}, {e}')
            return None, None, None
        except Exception as e:
            print(f" [오류] 게시물 상세 페이지 파싱 실패: {post_url}, {e}")
            log_event(crawler_logger, 'ERROR', 'DC인사이드', f'게시물 상세 페이지 파싱 실패: {post_url}, {e}')
            return None, None, None

    def _get_comments(self, gall_id, post_no):
        """댓글 수집 - 시간 측정 포함"""
        import time
        
        start_total = time.time()
        print(f" [시도] 댓글 페이지 로드: https://gall.dcinside.com/board/view/?id={gall_id}&no={post_no}")
        
        # 1. 페이지 로드 시간 측정
        load_start = time.time()
        try:
            self.driver.get(f"https://gall.dcinside.com/board/view/?id={gall_id}&no={post_no}")
        except Exception as e:
            print(f" [오류] 댓글 페이지 로드 실패: {gall_id}, {post_no}, {e}")
            return []
        load_time = time.time() - load_start
        print(f" [시간측정] 페이지 로드: {load_time:.2f}초")
        
        # 2. 대기 시간
        sleep_start = time.time()
        time.sleep(1)  # 봇 탐지 우회를 위해 자연스러운 대기
        sleep_time = time.time() - sleep_start
        print(f" [시간측정] 대기 시간: {sleep_time:.2f}초")
        
        # 3. 댓글 요소 찾기 시간 측정
        find_start = time.time()
        comment_elements = self.driver.find_elements(By.CSS_SELECTOR, "li.ub-content")
        find_time = time.time() - find_start
        print(f" [시간측정] 댓글 요소 찾기: {find_time:.2f}초 (찾은 댓글: {len(comment_elements)}개)")
        
        comments = []
        # 4. 댓글 파싱 시간 측정
        parse_start = time.time()
        for comment_element in comment_elements:
            

            content_elements = comment_element.find_elements(By.CSS_SELECTOR, ".usertxt")
            if not content_elements:
                continue

            comment_id_attr = comment_element.get_attribute("id")
            content = content_elements[0].text.strip()
            published_date = comment_element.find_element(By.CSS_SELECTOR, ".date_time").text.strip()
            parent_id = None
            if "reply" in comment_id_attr:
                parent_id = comments[-1]["id"]

            # 작성자 정보 추출
            username = '익명'
            try:
                writer_element = comment_element.find_element(By.CSS_SELECTOR, ".gall_writer, .ub-writer")
                username = writer_element.get_attribute("data-nick")
                if not username:
                    nickname_element = writer_element.find_element(By.CSS_SELECTOR, ".nickname")
                    username = nickname_element.text.strip()
            except:
                pass

            comment_data = {
                "id": comment_id_attr.split("_")[-1],
                "blog_id": post_no,
                "content": content,
                "published_date": published_date,
                "parent_id": parent_id,
                "like_count": None,
                "platform": "dcinside",
                "username": username,
                "author": username
            }
            comments.append(comment_data)
        
        parse_time = time.time() - parse_start
        total_time = time.time() - start_total
        print(f" [시간측정] 댓글 파싱: {parse_time:.2f}초")
        print(f" [시간측정] 댓글 수집 총 시간: {total_time:.2f}초")
        
        if total_time > 30:
            print(f" [경고] 댓글 수집이 30초 이상 소요됨!")
            
        return comments

    def search(self):
        """키워드로 게시물을 검색하고 데이터를 수집"""
        import time
        
        # 3분 타임아웃 설정 (멀티스레딩 호환)
        start_time = time.time()
        timeout_seconds = 180  # 3분
        
        try:
            if self.start_date and self.start_date.strip():
                start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
            else:
                start_dt = datetime(1900, 1, 1) # Set to a very old date if not provided

            if self.end_date and self.end_date.strip():
                end_dt = datetime.strptime(self.end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
            else:
                end_dt = datetime.now() # Set to current date if not provided

            processed_urls = set()  # 중복 방지
            page = 1
            consecutive_empty_pages = 0
            # 연속 빈 페이지 제한 제거 (날짜 역순이므로 목표 범위까지 계속 탐색)
            consecutive_old_pages = 0
            max_old_pages = 3    # 연속 3페이지가 모두 시작일보다 과거면 종료
            max_pages = 100  # 날짜 기반 지능적 탐색으로 충분히 깊이 탐색

            
            while self.post_count < self.max_posts and page <= max_pages:
                # 타임아웃 체크 (멀티스레딩 호환)
                if time.time() - start_time > timeout_seconds:
                    print("⏰ DC인사이드 크롤러 3분 타임아웃 - 강제 종료")
                    break
                    
                # --- DC인사이드 검색 URL (페이지 포함) ---
                search_url = self.base_url.format(page=page, keyword=quote(self.keyword))

                
                try:
                    response = self.session.get(search_url, timeout=10)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    print(f" [정보] 검색 URL 접속 (페이지 {page}): {search_url}")
                    
                    # DC인사이드 검색 결과에서 게시물 링크와 날짜 정보를 함께 추출
                    post_items_with_date = []
                    
                    # 실제 디버그 결과에 따른 직접적인 링크 추출 방식
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        # 게시판 링크 패턴 확인 (debug 결과에서 확인됨)
                        if '/board/view/' in href or '/mgallery/board/view/' in href or '/mini/board/view/' in href:
                            # 링크 텍스트가 의미있는지 확인
                            text = link.get_text(strip=True)
                            if text and len(text) > 5:  # 의미있는 제목이 있는 경우만
                                # 날짜 정보는 근처 요소에서 찾기
                                date_elem = None
                                parent = link.parent
                                while parent and not date_elem:
                                    date_elem = parent.find('span', class_='date_time') or parent.find(class_='date_time')
                                    if not date_elem:
                                        parent = parent.parent
                                        if parent and parent.name == 'html':  # 너무 위로 올라가면 중단
                                            break
                                
                                date_str = date_elem.get_text(strip=True) if date_elem else None
                                post_items_with_date.append({'link': link, 'date': date_str, 'item': link.parent})
                    
                    # 날짜별 사전 필터링
                    filtered_post_items = []
                    for post_info in post_items_with_date:
                        date_str = post_info['date']
                        if date_str:
                            # 날짜 파싱 및 필터링
                            try:
                                post_dt = None
                                # DC인사이드는 실제로 년도를 포함해서 제공함 (2025.09.07 02:05 형식)
                                date_formats = [
                                    "%Y.%m.%d %H:%M",    # 2025.09.07 02:05 (DC인사이드 기본 형식)
                                    "%Y-%m-%d %H:%M:%S", # 2025-09-07 02:05:45
                                    "%Y-%m-%d",          # 2025-09-07
                                    "%Y.%m.%d",          # 2025.09.07
                                ]
                                
                                for fmt in date_formats:
                                    try:
                                        # DC인사이드는 년도를 포함하므로 직접 파싱
                                        post_dt = datetime.strptime(date_str, fmt)
                                        print(f" [파싱성공] 날짜: {date_str} → {post_dt.strftime('%Y-%m-%d %H:%M')}")
                                        break
                                    except ValueError:
                                        continue
                                
                                if post_dt:
                                    # 날짜가 파싱되었으면 범위 체크 (더 관대하게)
                                    if start_dt <= post_dt <= end_dt:
                                        filtered_post_items.append(post_info)
                                        current_page_has_target_range = True
                                        all_posts_too_old = False
                                        print(f" [필터링] 게시물 포함: {post_dt.strftime('%Y-%m-%d %H:%M')} (범위 내)")
                                    elif post_dt < start_dt:
                                        # 목표 범위보다 오래됨 (과거) - 엄격한 필터링
                                        print(f" [필터링] 게시물 제외: {post_dt.strftime('%Y-%m-%d %H:%M')} (목표 범위보다 과거)")
                                    else:
                                        # 목표 범위보다 최신 (미래) - 이 경우는 거의 없음
                                        all_posts_too_old = False
                                        print(f" [필터링] 게시물 제외: {post_dt.strftime('%Y-%m-%d %H:%M')} (목표 범위보다 최신)")
                                else:
                                    print(f" [경고] 날짜 파싱 결과가 None: {date_str}")
                                    
                            except Exception as e:
                                print(f" [경고] 날짜 파싱 실패: {date_str}, 오류: {e}")
                                log_event(crawler_logger, 'WARNING', 'DC인사이드', f'날짜 파싱 실패: {date_str}, 오류: {e}')
                                # 날짜 파싱 실패한 경우에도 포함
                                filtered_post_items.append(post_info)
                        else:
                            # 날짜 정보가 없으면 포함
                            filtered_post_items.append(post_info)
                    
                    post_links = [item['link'] for item in filtered_post_items]
                    
                    if not post_links:
                        # 날짜 필터링으로 모든 게시물이 제외된 경우, 대안적 선택자 시도하지 않음
                        # 대신 더 많은 페이지를 탐색하여 날짜 범위 내 게시물 찾기
                        print(f" [정보] 페이지 {page}에서 날짜 필터링 후 수집 가능한 게시물이 없음. 다음 페이지 탐색.")
                        
                    # 날짜 필터링 후 결과가 없어도 계속 페이지 탐색 (더 오래된 데이터 찾기 위해)
                    if not post_links:
                        print(f" [정보] 페이지 {page}에서 날짜 필터링 후 수집 가능한 게시물이 없음. 다음 페이지 탐색.")
                        if page == 1:
                            print(f" [디버그] 페이지에서 찾은 링크 수: {len(soup.find_all('a'))}")
                            print(" [디버그] 페이지 title:", soup.title.string if soup.title else "없음")
                        # break 제거 - 계속 다음 페이지 탐색
                    
                    total_links_on_page = len(post_items_with_date)
                    filtered_links_on_page = len(post_links)
                    print(f" [정보] 페이지 {page}에서 DC인사이드 게시물 {total_links_on_page}개 발견, 날짜 필터링 후 {filtered_links_on_page}개")
                    print(f" [디버그] post_items_with_date: {len(post_items_with_date)}, post_links: {len(post_links)}")
                    
                    # 페이지에 게시물이 아예 없으면 검색 종료 (더 이상 결과 없음)
                    # 단, 날짜 필터링으로 인한 0개는 제외하고 실제 HTML에서 게시물이 없는 경우만
                    if total_links_on_page == 0:
                        print(f" [정보] 페이지 {page}에서 게시물이 전혀 없음. 검색 종료.")
                        break
                    
                    # 날짜 기반 지능적 탐색 로직
                    current_page_has_target_range = False  # 현재 페이지에 목표 범위 내 게시물이 있는지
                    all_posts_too_old = True  # 현재 페이지의 모든 게시물이 목표 범위보다 오래된지
                    
                    for post_info in post_items_with_date:
                        date_str = post_info['date']
                        if date_str:
                            try:
                                post_dt = None
                                # DC인사이드는 실제로 년도를 포함해서 제공함 (2025.09.07 02:05 형식)
                                date_formats = [
                                    "%Y.%m.%d %H:%M",    # 2025.09.07 02:05 (DC인사이드 기본 형식)
                                    "%Y-%m-%d %H:%M:%S", # 2025-09-07 02:05:45
                                    "%Y-%m-%d",          # 2025-09-07
                                    "%Y.%m.%d",          # 2025.09.07
                                ]
                                
                                for fmt in date_formats:
                                    try:
                                        if fmt in ["%m.%d %H:%M", "%m/%d %H:%M"]:
                                            date_str_with_year = f"{datetime.now().year}.{date_str}" if "." in date_str else f"{datetime.now().year}/{date_str}"
                                            post_dt = datetime.strptime(date_str_with_year, f"{datetime.now().year}.{fmt}" if "." in fmt else f"{datetime.now().year}/{fmt}")
                                        else:
                                            post_dt = datetime.strptime(date_str, fmt)
                                        break
                                    except ValueError:
                                        continue
                                
                                if post_dt and post_dt >= start_dt:
                                    all_posts_too_old = False
                                    break
                            except:
                                # 날짜 파싱 실패시 계속 진행
                                all_posts_too_old = False
                                break
                    
                    # 모든 게시물이 시작 날짜보다 이전이면 검색 종료
                    if all_posts_too_old and total_links_on_page > 0:
                        consecutive_old_pages += 1
                        print(f" [정보] 페이지 {page}의 모든 게시물이 시작 날짜({self.start_date})보다 이전입니다.")
                        if consecutive_old_pages >= 3:  # 연속 3페이지가 모두 과거면 종료
                            print(f" [정보] 연속 3페이지가 모두 시작일보다 과거여서 검색 종료")
                            break
                    else:
                        consecutive_old_pages = 0
                    
                    posts_on_page = 0
                    for link in post_links:
                        if self.post_count >= self.max_posts:
                            break
                            
                        post_url = link.get('href', '')
                        
                        # 중복 방지
                        if post_url in processed_urls:
                            continue
                        processed_urls.add(post_url)
                        
                        # 절대 URL로 변환
                        if not post_url.startswith('http'):
                            if post_url.startswith('//'):
                                post_url = 'https:' + post_url
                            elif post_url.startswith('/'):
                                post_url = 'https://gall.dcinside.com' + post_url
                            else:
                                continue
                        
                        print(f" [시도] 게시물 URL: {post_url}")
                        post_data, gall_id, post_no, soup = self._get_post_details(post_url)

                        if post_data and gall_id and post_no:
                            try:
                                date_str = post_data['published_date']
                                print(f" [디버그] 추출된 날짜: {date_str}")
                                
                                # 다양한 날짜 형식 시도
                                post_dt = None
                                date_formats = [
                                    "%Y-%m-%d %H:%M:%S",
                                    "%Y-%m-%d",
                                    "%Y.%m.%d %H:%M:%S", 
                                    "%Y.%m.%d",
                                    "%m.%d %H:%M",
                                    "%m/%d %H:%M"
                                ]
                                
                                for fmt in date_formats:
                                    try:
                                        # DC인사이드는 년도를 포함하므로 직접 파싱
                                        post_dt = datetime.strptime(date_str, fmt)
                                        print(f" [파싱성공] 날짜: {date_str} → {post_dt.strftime('%Y-%m-%d %H:%M')}")
                                        break
                                    except ValueError:
                                        continue
                                
                                if post_dt is None:
                                    print(f" [경고] 날짜 형식을 파싱할 수 없습니다: {date_str}")
                                    continue
                                    
                                if not (start_dt <= post_dt <= end_dt):
                                    print(f" [필터링] 날짜({post_dt.date()})가 범위에 맞지 않아 건너뜁니다.")
                                    continue
                            except Exception as e:
                                print(f" [경고] 날짜 처리 중 오류: {e}")
                                continue

                            if self.post_count >= self.max_posts:
                                print(" [정보] 최대 수집 개수에 도달하여 중단합니다.")
                                break
                            
                            print(f" ({self.post_count + 1}/{self.max_posts}) 게시물 수집 성공: {post_data['title'][:30]}...")
                            
                            self.contents_data.append(post_data)
                            # DC인사이드 댓글 수집 비활성화 (성능 이슈로 인해 주석 처리)
                            comments = self._get_comments(gall_id, post_no)
                            # # 댓글 날짜 필터링
                            # filtered_comments = filter_by_date_range(comments, 'published_date', self.start_date, self.end_date)
                            # self.comments_data.extend(filtered_comments)
                            self.comments_data.extend(comments)
                            
                            
                            self.post_count += 1
                            posts_on_page += 1
                        else:
                            print(f" [실패] 게시물 상세 정보 추출 실패: {post_url}")
                        
                        time.sleep(0.3)
                    
                    # 최대 게시물 수에 도달했으면 페이지 루프도 중단
                    if self.post_count >= self.max_posts:
                        print(f" [정보] 최대 수집 개수({self.max_posts}개)에 도달하여 검색을 완전히 종료합니다.")
                        break
                    
                    # 빈 페이지 로그만 출력 (조기 종료하지 않음)
                    if posts_on_page == 0:
                        consecutive_empty_pages += 1
                        print(f" [정보] 페이지 {page}에서 수집 가능한 게시물이 없음. 다음 페이지 탐색.")
                    else:
                        consecutive_empty_pages = 0
                    
                    # 날짜 기반 지능적 중단: 연속으로 시작일보다 과거 페이지들이 나오면 중단
                    if all_posts_too_old and len(post_items_with_date) > 0:
                        consecutive_old_pages += 1
                        print(f" [날짜탐색] 페이지 {page}의 모든 게시물이 시작일({self.start_date})보다 과거 ({consecutive_old_pages}/{max_old_pages})")
                        if consecutive_old_pages >= max_old_pages:
                            print(f" [날짜탐색] 연속 {max_old_pages}페이지가 모두 시작일보다 과거여서 검색 종료")
                            break
                    elif current_page_has_target_range:
                        consecutive_old_pages = 0  # 목표 범위 내 게시물 발견 시 리셋
                    
                    # 무한 루프 방지: 연속 빈 페이지 제한
                    if posts_on_page == 0:
                        consecutive_empty_pages += 1
                        if consecutive_empty_pages >= 30:  # 연속 30페이지 빈 결과면 종료
                            print(f" [정보] 연속 {consecutive_empty_pages}페이지에서 수집 가능한 게시물이 없어 검색 종료")
                            break
                    else:
                        consecutive_empty_pages = 0
                    
                    # 다음 페이지로
                    page += 1
                    
                except requests.RequestException as e:
                    print(f" [오류] 검색 페이지 요청 실패 (페이지 {page}): {e}")
                    log_event(crawler_logger, 'ERROR', 'DC인사이드', f'검색 페이지 요청 실패 (페이지 {page}): {e}')
                    break
                except Exception as e:
                    print(f" [오류] 검색 처리 중 알 수 없는 오류 (페이지 {page}): {e}")
                    log_event(crawler_logger, 'ERROR', 'DC인사이드', f'검색 처리 중 알 수 없는 오류 (페이지 {page}): {e}')
                    break
        
            self.close()
            print(f"총 {self.post_count}개의 게시물과 {len(self.comments_data)}개의 댓글을 수집했습니다.")

            print("self.contents_data: ", self.contents_data)
            
            # 수집된 데이터 반환
            return self.contents_data, self.comments_data
            
        except TimeoutError as e:
            print(f"⏰ DC인사이드 크롤링 타임아웃: {e}")
            # 타임아웃 시에도 수집된 데이터는 반환
            self.close()
            print(f"타임아웃 전까지 수집: {self.post_count}개 게시물, {len(self.comments_data)}개 댓글")
            return self.contents_data, self.comments_data
        except Exception as e:
            print(f"❌ DC인사이드 크롤링 오류: {e}")
            self.close()
            return [], []
        finally:
            # 타임아웃 종료 (멀티스레딩에서는 별도 해제 불필요)
            pass

    def close(self):
        """셀레니움 드라이버를 종료합니다."""
        if self.driver:
            self.driver.quit()
            print(" [정보] Selenium 드라이버를 종료했습니다.")

    def save_to_tsv(self):
        """수집된 데이터를 TSV 및 JSON 파일로 저장"""
        if not self.contents_data:
            print(" [정보] 저장할 게시물 데이터가 없습니다.")
            return

        # JSON 파일로 저장 (통합 크롤러와 호환)
        save_to_json("DCInside", self.contents_data, self.comments_data)
        print(f"총 {len(self.contents_data)}개의 게시물과 {len(self.comments_data)}개의 댓글을 수집했습니다.")

        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        contents_df = pd.DataFrame(self.contents_data)
        contents_filename = f"dcinside_contents_{now}.tsv"
        contents_df.to_csv(contents_filename, sep='\t', index=False, encoding='utf-8')
        print(f"게시물 데이터 저장 완료: {contents_filename}")

        if self.comments_data:
            comments_df = pd.DataFrame(self.comments_data)
            comments_filename = f"dcinside_comments_{now}.tsv"
            comments_df.to_csv(comments_filename, sep='\t', index=False, encoding='utf-8')
            print(f"댓글 데이터 저장 완료: {comments_filename}")
        else:
            print(" [정보] 저장할 댓글 데이터가 없습니다.")

    def run(self, keyword, max_posts, start_date=None, end_date=None):
        """표준 크롤러 인터페이스를 위한 run 메서드"""
        # 매개변수로 받은 값으로 업데이트
        self.keyword = keyword
        self.max_posts = max_posts or 100
        self.start_date = start_date
        self.end_date = end_date
        
        # 기존 search() 메서드 호출
        posts, comments = self.search()
        return posts, comments

# 테스트 코드는 total_crawler.py에서 통합 실행됩니다.
if __name__ == '__main__':
    crawler = DcinsideCrawler(keyword="컴팩트 파우더", max_posts=100, start_date=None, end_date=None)
    crawler.search()

