"""
다음 카페 크롤러 (Daum Cafe Crawler)
=====================================

다음 카페에서 키워드 검색을 통해 게시글과 댓글을 수집하는 크롤러입니다.

주요 기능:
- 키워드 기반 다음 카페 게시글 검색 및 수집
- 게시글별 댓글 수집 (대댓글 포함)
- 날짜 범위 필터링
- TSV 파일 형태로 데이터 저장
- 기존 크롤러 시스템과 호환되는 데이터 스키마

필수 라이브러리:
- pandas: 데이터 처리 및 저장
- selenium: 웹 브라우저 자동화
- webdriver-manager: 크롬 드라이버 자동 관리
- beautifulsoup4: HTML 파싱

설치 명령어:
pip install pandas selenium webdriver-manager beautifulsoup4

사용 방법:
1. 독립 실행: python daum_cafe_crawler.py
2. 통합 실행: python total_crawler.py (다른 크롤러와 함께)

크롤링 전략:
- 다음 통합 검색을 활용한 카페 게시글 검색
- 모바일 버전 사용으로 안정성 확보 (m.cafe.daum.net)
- 다양한 CSS 선택자로 강력한 데이터 추출
- 페이지네이션 지원으로 전체 댓글 수집

주의사항:
- 크롤링 시 서버에 과부하를 주지 않도록 적절한 지연 시간 설정
- 다음 카페 이용약관 및 robots.txt 준수
- 개인정보가 포함될 수 있는 데이터 처리 시 주의
"""

import pandas as pd
import time
import os
import re
from datetime import datetime, timedelta
from urllib.parse import quote, urlparse, parse_qs
from crawlers.common import extract_numbers, save_to_json, is_date_in_range, filter_by_date_range

# 선택적 import를 위한 try-except
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
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


class DaumCafeCrawler:
    """
    다음 카페 게시물 및 댓글 크롤러 (Selenium 사용)
    다음 카페의 모바일 버전을 활용하여 게시글과 댓글을 수집합니다.
    """
    
    def __init__(self, keyword, start_date, end_date, max_posts=100):
        # 의존성 체크
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium이 설치되지 않았습니다. pip install selenium webdriver-manager로 설치하세요.")
        if not BS4_AVAILABLE:
            raise ImportError("BeautifulSoup4가 설치되지 않았습니다. pip install beautifulsoup4로 설치하세요.")
        
        self.keyword = keyword
        self.start_date = start_date
        self.end_date = end_date
        self.max_posts = max_posts
        
        # 다음 카페 검색 URL (실제 카페 검색 페이지)
        self.search_base_url = "https://top.cafe.daum.net/_c21_/search/cafe-table"
        self.mobile_cafe_base_url = "https://m.cafe.daum.net"
        
        self.contents_data = []
        self.comments_data = []
        self.post_count = 0
        
        # 셀레니움 드라이버 초기화
        self.driver = self._setup_driver()
        
    def _setup_driver(self):
        """Selenium 웹 드라이버를 설정하고 반환합니다."""
        options = Options()
        options.add_argument("--headless")  # 브라우저 창 숨기기
        options.add_argument("--window-size=800x600")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            print(f" [오류] Chrome 드라이버 초기화 실패: {e}")
            return None
    
    def _search_cafe_posts(self):
        """다음 통합 검색에서 카페 게시글 URL들을 수집합니다."""
        post_urls = []
        url_date_map = {}  # URL과 날짜 매핑
        page = 1
        max_pages = 10  # 최대 검색 페이지 수
        found_target_date_range = False
        
        print(f" [정보] 다음 카페 검색 시작: '{self.keyword}' ({self.start_date} ~ {self.end_date})")
        
        while len(post_urls) < self.max_posts * 2 and page <= max_pages:
            # 다음 카페 검색 URL 생성 (실제 카페 검색 API)
            search_url = f"{self.search_base_url}?searchOpt=CAFE_ARTICLE&articleSortType=RECENCY&q={quote(self.keyword)}&p={page}"
            print(f" [디버그] 검색 URL: {search_url}")
            
            try:
                self.driver.get(search_url)
                time.sleep(5)  # 페이지 로딩 대기 증가
                
                # 스크롤하여 동적 컨텐츠 로딩
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                # 페이지 소스 확인을 위한 디버깅
                page_source = self.driver.page_source
                if self.keyword not in page_source:
                    print(f" [경고] 페이지에 검색어 '{self.keyword}'가 포함되지 않음")
                else:
                    print(f" [정보] 페이지에 검색어 '{self.keyword}' 확인됨")
                
                # 다음 카페 검색 결과 페이지의 실제 선택자들
                link_selectors = [
                    # 메인 제목 링크 (실제 카페 검색 페이지 구조)
                    ".search_post .list_scafe li .link_tit",
                    ".list_scafe li a.link_tit",
                    ".search_post li .link_tit",
                    # 대안 선택자들
                    "a[href*='cafe.daum.net']",
                    ".list_scafe a[href*='cafe.daum.net']",
                    # 더 일반적인 패턴
                    "a[href*='cafe'][href*='daum']"
                ]
                
                cafe_links = []
                for selector in link_selectors:
                    try:
                        links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if links:
                            print(f" [정보] '{selector}' 선택자로 {len(links)}개 링크 발견")
                            cafe_links.extend(links)
                    except Exception as e:
                        print(f" [디버그] 선택자 '{selector}' 실패: {e}")
                        continue
                
                # 중복 제거
                unique_hrefs = set()
                unique_links = []
                for link in cafe_links:
                    try:
                        href = link.get_attribute('href')
                        if href and href not in unique_hrefs and 'cafe.daum.net' in href:
                            unique_hrefs.add(href)
                            unique_links.append(link)
                    except Exception:
                        continue
                
                print(f" [정보] 중복 제거 후: {len(unique_links)}개 유니크 링크")
                
                page_urls = []
                for link in unique_links:
                    try:
                        href = link.get_attribute('href')
                        print(f" [디버그] 발견된 링크: {href}")
                        
                        if href and 'cafe.daum.net' in href:
                            # 원본 URL 사용
                            if href not in post_urls:
                                page_urls.append(href)
                                post_urls.append(href)
                        elif href and href.startswith('/'):
                            # 상대 URL인 경우 절대 URL로 변환
                            full_url = f"https://cafe.daum.net{href}"
                            if full_url not in post_urls:
                                page_urls.append(full_url) 
                                post_urls.append(full_url)
                    except Exception as e:
                        print(f" [오류] 링크 처리 중 오류: {e}")
                        continue
                
                print(f" [정보] 페이지 {page}: {len(page_urls)}개 URL 수집 (총 {len(post_urls)}개)")
                
                # 페이지 날짜 범위 확인 (게시글 목록에서)
                if page_urls:
                    page_in_range, past_end_date = self._check_page_dates()
                    if page_in_range:
                        print(f" [정보] 페이지 {page}에서 목표 날짜 범위 발견")
                        found_target_date_range = True
                    elif past_end_date:
                        print(f" [정보] 페이지 {page}가 시작 날짜보다 과거, 검색 종료")
                        break
                    else:
                        print(f" [정보] 페이지 {page}는 날짜 범위 밖, 다음 페이지로")
                        # 이 페이지의 URL들은 post_urls에서 제거
                        post_urls = post_urls[:-len(page_urls)]
                
                if not page_urls:
                    print(f" [정보] 페이지 {page}에서 새로운 URL을 찾을 수 없어 검색 종료")
                    break
                
                # break
                page += 1
                time.sleep(3)  # 요청 간 대기
                
            except Exception as e:
                print(f" [오류] 검색 페이지 {page} 처리 중 오류: {e}")
                import traceback
                traceback.print_exc()
                break
        
        print(f" [정보] 총 {len(post_urls)}개의 카페 게시글 URL 수집 완료")
        
        # URL과 날짜 매핑: 게시글 목록 구조에 맞게 정확히 매핑
        try:
            # 다음 카페 검색 결과의 게시글 항목을 찾음
            post_items = self.driver.find_elements(By.CSS_SELECTOR, '.list_scafe li')
            print(f" [디버그] 게시글 항목: {len(post_items)}개")
            
            for item in post_items:
                try:
                    # 각 항목에서 링크와 날짜 찾기
                    link_elem = item.find_element(By.CSS_SELECTOR, 'a[href*="cafe.daum.net"]')
                    date_elem = item.find_element(By.CSS_SELECTOR, '.info_scafe')
                    
                    href = link_elem.get_attribute('href')
                    date_text = date_elem.text.strip()
                    
                    # URL이 수집된 목록에 있고, 날짜가 유효하면 매핑
                    if href and href in post_urls and date_text and date_text.count('.') == 2:
                        url_date_map[href] = date_text
                        print(f" [디버그] 매핑 성공: {href.split('/')[-1]} → {date_text}")
                        
                except Exception:
                    continue
                    
            print(f" [정보] URL-날짜 매핑 완료: {len(url_date_map)}개")
                    
        except Exception as e:
            print(f" [경고] URL-날짜 매핑 실패: {e}")
        
        return post_urls[:self.max_posts], url_date_map
    
    def _check_page_dates(self):
        """게시글 목록 페이지에서 날짜들을 확인해서 목표 날짜 범위에 있는지 판단"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 다음 카페 검색 결과 페이지의 게시글 목록에서 날짜 추출
            date_selectors = [
                '.info_scafe',  # 실제 다음 카페 날짜 선택자
                'span.info_scafe',
                '.list_scafe .info_scafe'
            ]
            
            page_dates = []
            for selector in date_selectors:
                date_elements = soup.select(selector)
                print(f" [디버그] '{selector}' 선택자로 {len(date_elements)}개 날짜 요소 발견")
                
                for elem in date_elements:
                    date_text = elem.get_text(strip=True)
                    if not date_text:
                        continue
                    
                    # 날짜 형식만 필터링 (2025.08.07 형태만)
                    if not (len(date_text.split('.')) == 3 and all(part.isdigit() for part in date_text.split('.'))):
                        continue
                    
                    print(f" [디버그] 발견된 날짜 텍스트: '{date_text}'")
                    
                    # 다음 카페 날짜 형식 파싱: "2025.08.07" 형식
                    try:
                        print("--------------------------------")
                        print("date_text: ", date_text)
                        year, month, day = date_text.split('.')
                        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)} 12:00:00"
                        print("date_str: ", date_str)
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        page_dates.append(date_obj)
                        print(f" [디버그] 파싱된 날짜: {date_obj}")
                    except Exception as parse_error:
                        print(f" [디버그] 날짜 파싱 실패: {date_text}, 오류: {parse_error}")
                        continue
                
                if page_dates:
                    break
            
            if self.start_date:
                start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
            else:
                start_dt = datetime.min # Use the earliest possible date

            if self.end_date:
                end_dt = datetime.strptime(self.end_date, "%Y-%m-%d") + timedelta(days=1)
            else:
                end_dt = datetime.max # Use the latest possible date
            
            # 페이지의 최신/최오래된 날짜 확인
            latest_date = max(page_dates)
            oldest_date = min(page_dates)
            
            print(f" [디버그] 페이지 날짜 범위: {oldest_date.date()} ~ {latest_date.date()}")
            print(f" [디버그] 목표 날짜 범위: {start_dt.date()} ~ {end_dt.date()}")
            
            # 목표 범위와 교집합 있는지 확인
            page_in_range = (oldest_date <= end_dt) and (latest_date >= start_dt)
            past_end_date = latest_date < start_dt  # 모든 게시글이 시작날짜보다 과거
            
            return page_in_range, past_end_date
            
        except Exception as e:
            print(f" [경고] 페이지 날짜 확인 실패: {e}")
            return False, False
    
    def _convert_to_mobile_url(self, desktop_url):
        """데스크톱 카페 URL을 모바일 URL로 변환합니다."""
        try:
            if 'm.cafe.daum.net' in desktop_url:
                return desktop_url
            
            # cafe.daum.net URL 패턴 분석
            if 'cafe.daum.net' in desktop_url:
                # URL에서 카페명과 게시글 번호 추출
                parsed = urlparse(desktop_url)
                query_params = parse_qs(parsed.query)
                
                # grpid와 boardid, 그리고 게시글 번호 추출
                grpid = query_params.get('grpid', [''])[0]
                articleid = query_params.get('articleid', [''])[0]
                boardid = query_params.get('boardid', [''])[0]
                
                if grpid and articleid:
                    # 모바일 URL 형식: https://m.cafe.daum.net/카페명/게시판명/게시글번호
                    # 실제 카페명과 게시판명은 API를 통해 확인해야 하지만,
                    # 우선 grpid와 boardid를 사용
                    mobile_url = f"https://m.cafe.daum.net/{grpid}/{boardid}/{articleid}"
                    return mobile_url
            
            return None
        except Exception:
            return None
    

    def _get_or_default_date(self, selector, default_value):
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            if element:
                text = element.text.strip()
                # 텍스트가 30자를 초과하면 앞 30자만 표시
                display_text = text[:30] + '...' if len(text) > 30 else text
                print(f" [디버그] 선택자 '{selector}'로 텍스트 발견: '{display_text}'")
                return text
            else:
                return default_value
        except Exception:
            return default_value

    def _get_post_details(self, post_url):
        """개별 게시글의 상세 정보를 추출합니다."""
        try:
            self.driver.get(post_url)
            time.sleep(3)  # 페이지 로딩 대기
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 게시글이 삭제되었거나 접근할 수 없는 경우 체크
            if "삭제된 글" in soup.text or "존재하지 않는" in soup.text:
                
                print(f" [건너뜀] 삭제되거나 접근할 수 없는 게시글: {post_url}----------------------------->")
                return None

            self.driver.switch_to.frame("down")
            
            url_parts = post_url.split('/')
            raw_post_id = url_parts[-1] if url_parts else datetime.now().strftime('%Y%m%d%H%M%S%f')
            # 쿼리 파라미터 제거하여 일관성 확보
            post_id = raw_post_id.split('?')[0] if '?' in raw_post_id else raw_post_id

            title = self._get_or_default_date('.article_title', "제목 없음")
            published_date = self._get_or_default_date('div.cover_info > span:nth-child(4)',None)
            if published_date:
                published_date = self._normalize_date(published_date)


            content = self._get_or_default_date('div#user_contents', "내용 없음")
            # TSV 형식을 위해 줄바꿈 문자를 공백으로 변환
            if content:
                content = content.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
            view_count = self.driver.find_elements(By.CSS_SELECTOR, "#primaryContent > div > div.bbs_read_tit > div.info_desc > div > span:nth-child(3)")
            if view_count:
                view_count = view_count[0].text.strip()
                view_count = extract_numbers(view_count)
                
                view_count = "".join(view_count)
            else:
                view_count = None

            like_count = self.driver.find_elements(By.CSS_SELECTOR, "#primaryContent > div > div.bbs_read_tit > div.info_desc > div > span:nth-child(2)")
            if like_count:
                like_count = like_count[0].text.strip()
                like_count = extract_numbers(like_count)
                like_count = "".join(like_count)
            else:
                like_count = None




            post_data = {
                'id': post_id,
                'title': title,
                'content': content,
                'published_date': published_date,
                'link': post_url,
                'view_count': view_count,
                'like_count': like_count,
                'platform': 'Daum Cafe',
     
            }
            
            return post_data
            
        except Exception as e:
            print(f" [오류] 게시글 상세 정보 추출 실패: {post_url}, {e}")
            return None
    
    def _get_comments(self, post_url, post_id):
        """게시글의 댓글들을 수집합니다."""
        comments = []
        
        try:
            

            page_tags = self.driver.find_elements(By.CSS_SELECTOR, "a.page-link")
            page_numbers = [tag.text.strip() for tag in page_tags if tag.text.strip().isdigit()]
            print(page_numbers)
            total_page = int(page_numbers[-1]) if page_numbers else 1

            comments = []
            loop = 0
            for page in range(1, total_page+1):
                print(page)
                comment_sections = self.driver.find_elements(By.CSS_SELECTOR, f".comment_section")
                for comment_section in comment_sections:
                    comment_id = f"{post_id}_{loop}"
                    contents = comment_section.find_elements(By.CSS_SELECTOR, f".original_comment")
                    if not contents:
                        continue

                    content = contents[0].text.strip()
                    # TSV 형식을 위해 줄바꿈 문자를 공백으로 변환
                    if content:
                        content = content.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

                    published_date = comment_section.find_element(By.CSS_SELECTOR, f".txt_date").text.strip()

                    # Username 수집 시도
                    username = None
                    try:
                        username_elem = comment_section.find_elements(By.CSS_SELECTOR, ".txt_name, .name, .writer, .user_name")
                        if username_elem:
                            username = username_elem[0].text.strip()
                    except Exception:
                        pass

                    parent = comment_section.find_element(By.XPATH, "..")
                    parent_class = parent.get_attribute("class")
                    if "reply_section" in parent_class and comments:
                        parent_id = comments[-1]['id']
                    else:
                        parent_id = None


                    comments.append({
                        'id': comment_id,
                        'blog_id': post_id,
                        'content': content,
                        'published_date': published_date,
                        'parent_id': parent_id,
                        'platform': 'Daum Cafe',
                        "like_count": None,
                        'username': username,
                    })
                    loop += 1

                # 다음 페이지로 이동 (마지막 페이지는 버튼 없음)
                if page < total_page:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, "a.next, .btn_next")
                        next_button.click()
                        time.sleep(3)
                    except NoSuchElementException:
                        print(f" [정보] 마지막 댓글 페이지 도달")
                        break



            
    

            
            print(f" [성공] {len(comments)}개의 댓글 수집 완료")
            
        except Exception as e:
            
            print(f" [오류] 댓글 수집 중 오류: {e}")
        
        return comments


    
    def _extract_comments_from_page(self, soup, post_id, page_num):
        """현재 페이지에서 댓글을 추출합니다."""
        comments = []
        
        comment_selectors = [
            '.cmt_list .cmt_item',
            '.comment_list .comment_item', 
            '.list_comment li',
            '.cmt_list li', 
            '.reply_list li',
            '[class*="comment"] li'
        ]
        
        comment_elements = []
        for selector in comment_selectors:
            comment_elements = soup.select(selector)
            if comment_elements:
                break
        
        for i, comment_elem in enumerate(comment_elements):
            try:
                # 댓글 내용 (다음 카페 구조)
                content_selectors = [
                    '.cmt_txt',
                    '.txt_comment',
                    '.comment_txt',
                    '.reply_txt',
                    '.txt_detail'
                ]
                comment_content = self._extract_text_by_selectors(comment_elem, content_selectors, "")
                
                if not comment_content.strip():
                    continue
                
                # 댓글 작성일
                date_selectors = [
                    '.date_info',
                    '.txt_date',
                    '.date',
                    'time'
                ]
                comment_date = self._extract_text_by_selectors(comment_elem, date_selectors, None)
                
                # 대댓글 여부 확인
                parent_id = None
                if 're' in str(comment_elem.get('class', [])).lower() or 'reply' in str(comment_elem.get('class', [])).lower():
                    parent_id = f"{post_id}_{i-1}" if i > 0 else None
                
                comment_id = f"{post_id}_{page_num}_{i}"
                
                comments.append({
                    'id': comment_id,
                    'blog_id': post_id,
                    'content': comment_content,
                    'published_date': self._normalize_date(comment_date),
                    'parent_id': parent_id,
                    'like_count': None,
                    'platform': 'Daum Cafe'
                })
                
            except Exception:
                continue
                
        return comments
    
    def _go_to_next_comment_page(self, current_page):
        """댓글의 다음 페이지로 이동합니다."""
        try:
            # 댓글 페이지네이션 버튼 찾기
            next_selectors = [
                '.btn_next',
                '.next',
                f'[data-page="{current_page + 1}"]',
                '.pagination .next'
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled():
                        next_button.click()
                        time.sleep(2)
                        return True
                except (NoSuchElementException, TimeoutException):
                    continue
            
            return False
            
        except Exception:
            return False

    
    def _normalize_date(self, date_str):
        """날짜 문자열을 표준 형식으로 변환합니다."""
        if not date_str:
            return None

        try:
            # 상대 시간 표현 처리 (수집 시점 기준)
            import sys
            import os
            try:
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared', 'utils'))
                from date_utils import parse_relative_time

                result = parse_relative_time(date_str, datetime.now())
                if result:
                    return result.strftime("%Y-%m-%d %H:%M:%S")
            except ImportError:
                pass  # date_utils가 없는 경우 기존 로직으로 진행
            except Exception:
                pass  # 실패시 기존 로직으로 진행

            # 다양한 날짜 형식 처리
            date_formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%Y.%m.%d %H:%M:%S",
                "%Y.%m.%d %H:%M",
                "%Y.%m.%d",
                "%y.%m.%d %H:%M",  # 25.06.29 19:59 형식
                "%m.%d %H:%M",
                "%m/%d %H:%M"
            ]
            
            for fmt in date_formats:
                try:
                    if fmt in ["%m.%d %H:%M", "%m/%d %H:%M"]:
                        # 년도가 없는 경우 현재 년도 추가
                        date_str_with_year = f"2025.{date_str}" if "." in date_str else f"2025/{date_str}"
                        date_obj = datetime.strptime(date_str_with_year, f"2025.{fmt}" if "." in fmt else f"2025/{fmt}")
                    else:
                        # Python의 %y는 이미 올바르게 변환 (00-68→2000-2068, 69-99→1969-1999)
                        date_obj = datetime.strptime(date_str, fmt)
                    try:
                        return date_obj.strftime("%Y-%m-%d %H:%M:%S")
                    except (ValueError, AttributeError):
                        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
            
            # 파싱 실패 시 None 반환
            return None
            
        except Exception:
            return None
    
    def _is_in_date_range(self, post_data):
        """게시글이 지정된 날짜 범위 내에 있는지 확인합니다."""
        try:
            if not post_data.get('published_date'):
                return False  # 날짜가 없으면 제외
                
            post_date = datetime.strptime(post_data['published_date'], "%Y-%m-%d %H:%M:%S")
            start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(self.end_date, "%Y-%m-%d") + timedelta(days=1)  # 종료일 포함
            
            return start_dt <= post_date < end_dt
        except Exception:
            return False  # 날짜 파싱 실패 시 제외
    
    def search(self):
        """키워드로 카페 게시물을 검색하고 데이터를 수집합니다."""
        if not self.driver:
            print(" [오류] 셀레니움 드라이버가 초기화되지 않았습니다.")
            return
        
        try:
            # 1단계: 카페 게시글 URL 수집
            post_urls, url_date_map = self._search_cafe_posts()
            
            if not post_urls:
                print(" [정보] 검색 결과가 없습니다.")
                return
            
            print(f" [정보] {len(post_urls)}개 게시글 상세 정보 수집 시작")
            print(f" [디버그] URL-날짜 매핑: {len(url_date_map)}개")
            
            # 2단계: 각 게시글 상세 정보 및 댓글 수집
            for i, url in enumerate(post_urls):
                if self.post_count >= self.max_posts:
                    break
                
                print(f" [{i+1}/{len(post_urls)}] 처리 중: {url}")
                
                # 게시글 상세 정보 추출 (목록 페이지 날짜 전달)
                list_page_date = url_date_map.get(url)
                post_data = self._get_post_details(url)
                print("post_data: ", post_data)
                
                if post_data:
                    # 날짜 범위 확인
                    if is_date_in_range(post_data.get('published_date'), self.start_date, self.end_date):
                        print(f" [성공] 게시글 수집: {post_data['title'][:50]}...")
                        
                        self.contents_data.append(post_data)
                        
                        # 댓글 수집
                        comments = self._get_comments(url, post_data['id'])
                        # 댓글도 날짜 필터링
                        filtered_comments = filter_by_date_range(comments, 'published_date', self.start_date, self.end_date)
                        self.comments_data.extend(filtered_comments)
                        
                        save_to_json("Daum Cafe", [post_data], filtered_comments)
                        self.post_count += 1
                    else:
                        print(f" [필터링] 날짜 범위 밖: {post_data['published_date']}")
                else:
                    print(f" [실패] 게시글 정보 추출 실패")
                
                time.sleep(2)  # 요청 간 대기
            
        except Exception as e:
            print(f" [오류] 검색 처리 중 오류 발생: {e}")
        
        finally:
            print(f"\n=== 다음 카페 크롤링 완료 ===")
            print(f"수집된 게시글: {len(self.contents_data)}개")
            print(f"수집된 댓글: {len(self.comments_data)}개")
    
    def close(self):
        """셀레니움 드라이버를 종료합니다."""
        if self.driver:
            self.driver.quit()
            print(" [정보] 셀레니움 드라이버를 종료했습니다.")
    
    def save_to_tsv(self):
        """수집된 데이터를 TSV 파일로 저장합니다."""
        if not os.path.exists('crawling_data'):
            os.makedirs('crawling_data')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 게시글 데이터 저장
        if self.contents_data:
            # 컬럼 순서 맞추기 (기존 크롤러와 동일)
            CONTENT_COLUMNS = ['id', 'title', 'content', 'published_date', 'platform', 'link', 'view_count', 'like_count', 'smp_method', 'smp_score', 'inf_type', 'cls_id']
            
            contents_df = pd.DataFrame(self.contents_data)
            for col in CONTENT_COLUMNS:
                if col not in contents_df.columns:
                    contents_df[col] = None
            contents_df = contents_df.reindex(columns=CONTENT_COLUMNS)
            
            contents_filename = f"crawling_data/{timestamp}_daum_cafe_contents.tsv"
            contents_df.to_csv(contents_filename, sep='\t', index=False, encoding='utf-8-sig')
            print(f"게시글 데이터 저장 완료: {contents_filename}")
        else:
            print(" [정보] 저장할 게시글 데이터가 없습니다.")
        
        # 댓글 데이터 저장
        if self.comments_data:
            # 컬럼 순서 맞추기 (username 필드 추가)
            COMMENT_COLUMNS = ['id', 'blog_id', 'content', 'published_date', 'parent_id', 'like_count', 'platform', 'username']

            comments_df = pd.DataFrame(self.comments_data)
            for col in COMMENT_COLUMNS:
                if col not in comments_df.columns:
                    comments_df[col] = None
            comments_df = comments_df.reindex(columns=COMMENT_COLUMNS)
            
            comments_filename = f"crawling_data/{timestamp}_daum_cafe_comments.tsv"
            comments_df.to_csv(comments_filename, sep='\t', index=False, encoding='utf-8-sig')
            print(f"댓글 데이터 저장 완료: {comments_filename}")
        else:
            print(" [정보] 저장할 댓글 데이터가 없습니다.")


# 독립 실행을 위한 메인 함수
def main():
    """메인 실행 함수 - 독립적으로 실행 가능"""
    print("=== 다음 카페 크롤러 ===")
    print("다음 카페에서 키워드 검색을 통해 게시글과 댓글을 수집합니다.\n")
    
    # 사용자 입력
    # keyword = input("검색할 키워드를 입력하세요: ").strip()
    # start_date = input("검색 시작일 (YYYY-MM-DD 형식)을 입력하세요: ").strip()
    # end_date = input("검색 종료일 (YYYY-MM-DD 형식)을 입력하세요: ").strip()
    
    # max_posts_input = input("최대 게시물 수 (기본값: 50): ").strip()
    # max_posts = int(max_posts_input) if max_posts_input else 50
    
    # print(f"\n설정 정보:")
    # print(f"키워드: {keyword}")
    # print(f"검색 기간: {start_date} ~ {end_date}")
    # print(f"최대 게시물 수: {max_posts}개")
    # print("\n크롤링을 시작합니다...")

    keyword = "컴팩트 파우더"
    start_date = None
    end_date = None
    max_posts = 100
    
    # 크롤러 실행
    crawler = None
    try:
        crawler = DaumCafeCrawler(keyword, start_date, end_date, max_posts)
        crawler.search()
        crawler.save_to_tsv()
        # url = "https://cafe.daum.net/subdued20club/ReHf/5520286?svc=cafeapi"
        # post_data = crawler._get_post_details(url)
        # comments = crawler._get_comments(url, post_data['id'])
        # print("post_data: ", post_data)
        # print("comments: ", comments)
    except KeyboardInterrupt:
        print("\n [중단] 사용자에 의해 크롤링이 중단되었습니다.")
    except Exception as e:
        print(f"\n [오류] 크롤링 중 예상치 못한 오류가 발생했습니다: {e}")
    finally:
        if crawler:
            crawler.close()
        print("\n크롤링이 완료되었습니다.")


if __name__ == "__main__":
    main()