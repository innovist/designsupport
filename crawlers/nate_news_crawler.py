"""
네이트뉴스 크롤러
패션 관련 뉴스 수집
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
REQUEST_TIMEOUT_SECONDS = settings.crawler_timeout_seconds or 30
MAX_COMMENT_PAGES = 10



class NateNewsCrawler:

    def get_id(self, url):
        if '?' in url:
            url = url.split('?')[0]
        return url.split('/')[-1]

    def get_published_date(self, published_date):
        if re.match(r'\d{2}\.\d{2} \d{2}:\d{2}', published_date):
            # 연도 추가: 올해 연도를 붙여서 변환
            year = datetime.now().year
            return datetime.strptime(f"{year}.{published_date}", '%Y.%m.%d %H:%M').strftime('%Y-%m-%d %H:%M:%S')
        
        return published_date.replace(".", "-")
    
    def get_posts(self, url):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            soup = BeautifulSoup(response.text, 'lxml')
            id = self.get_id(url)
            title_elem = soup.select_one('h1.articleSubecjt')
            title = title_elem.get_text(strip=True) if title_elem else "제목 없음"
            username_elem = soup.select_one('#articleView > p > span.link > a.medium')
            username = username_elem.get_text(strip=True) if username_elem else "작성자 없음"
            published_date = soup.select_one("span.lastDate > em")
            if published_date:
                published_date = published_date.get_text(strip=True)
            else:
                first_date_elem = soup.select_one('span.firstDate > em')
                published_date = first_date_elem.get_text(strip=True) if first_date_elem else "날짜 없음"
            view_count = None
            like_count = None
            content_elem = soup.select_one('#realArtcContents')
            content = content_elem.get_text(strip=True) if content_elem else title
            comments = self.get_comments(id, username)

            post_data = {
            "id": id,
            "title": title,
            "content": content,
            "published_date": published_date,
            "platform": "네이트뉴스",
            "link": url,
            "view_count": view_count,
            "like_count": like_count,
            "user_id": username,
            }
            return post_data, comments

        except Exception as e:
            print(f"네이트뉴스 게시물 크롤링 오류: {url}, {e}")
            return {
                "id": self.get_id(url),
                "title": "크롤링 실패",
                "content": "크롤링 실패",
                "published_date": "날짜 없음",
                "platform": "네이트뉴스",
                "link": url,
                "view_count": None,
                "like_count": None,
                "user_id": "작성자 없음",
            }, []

    def get_comments(self, post_id, article_platform):
        comments = []
        page = 1
        while True:
            if page > MAX_COMMENT_PAGES:
                break
            url = f"https://comm.news.nate.com/Comment/ArticleComment/List?artc_sq={post_id}&page={page}"
            response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            soup = BeautifulSoup(response.text, 'lxml')
            comment_containers = soup.select(".cmt_list  .cmt_item")
            print("comment pages: ", page)
            if len(comment_containers) == 0:
                break
            for comment_container in comment_containers:
                try:
                    comment_id_attr = comment_container.get("id")
                    if not comment_id_attr:
                        continue
                    comment_id = comment_id_attr.split("_")[-1]
                    date_elem = comment_container.select_one(".date")
                    if date_elem:
                        published_date = date_elem.get_text(strip=True).replace("|", "")
                        published_date = self.get_published_date(published_date)
                    else:
                        published_date = "날짜 없음"
                    username_elem = comment_container.select_one(".nameui")
                    username = username_elem.get_text(strip=True) if username_elem else "사용자 없음"
                    content_elem = comment_container.select_one(".usertxt")
                    content = content_elem.get_text(strip=True) if content_elem else "내용 없음"
                    print(content)
                except Exception as e:
                    print(f"댓글 처리 오류: {e}")
                    continue
                comments.append({
                    "id": comment_id,
                    "username": username,
                    "content": content,
                    "blog_id": post_id,
                    "platform": "네이트뉴스",
                    "parent_id": None,
                    "published_date": published_date,
                    "like_count": None,
                })
            page += 1
        return comments

    def run(self, keyword, max_posts, start_date, end_date):
        post_data = []
        comment_data = []
        start_date = start_date.replace("-", "")
        end_date = end_date.replace("-", "")
        if not start_date:
            start_date = ""
        if not end_date:
            end_date = ""

        count = 0
        ##search-option > div.paging-search > a[title="다음"]
        page = 1
        while True:
            url = f"https://news.nate.com/search?q={keyword}&ps=3&ps1={start_date}&ps2={end_date}&page={page}"
            print("url: ", url)
            response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            soup = BeautifulSoup(response.text, 'lxml')
            
            print("page: ", page)
            
            a_tags = soup.select("#search-option > div.search-result > ul > li >a")
            urls = [f"https:{a_tag.get('href')}" for a_tag in a_tags]
            for url in urls:
                logger.debug(f"Crawling: {url}")
                posts, comments = self.get_posts(url)
                post_data.append(posts)
                comment_data.extend(comments)
                count += 1
                if max_posts and count >= max_posts:
                    return post_data, comment_data

            next_button = soup.select_one("#search-option > div.paging-search > a[title='다음']")
            print("next_button: ", next_button)
            if next_button:
                page += 1
            else:
                break
            
        return post_data, comment_data




if __name__ == "__main__":
    crawler = NateNewsCrawler()
    crawler.run("에스파", None, "", "")

                
        
        
