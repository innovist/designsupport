

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import os
import re
from common import get_url_query, save_to_json

class MlbparkCrawler:
    

    def get_posts(self, url, correct_published_date=None):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://mlbpark.donga.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        response = requests.get(url, headers=headers, timeout=15)
        # print(response.text)

        soup = BeautifulSoup(response.text, "lxml")
        
        params = get_url_query(url)
       
        title = soup.select_one(".titles")
        if title is None:
            return None, None
        title = title.get_text().strip()
        

        # 목록에서 전달받은 올바른 날짜를 사용하거나, 상세페이지에서 추출
        if correct_published_date:
            published_date = correct_published_date
        else:
            # 기존 로직 (더 정확한 셀렉터 사용)
            try:
                # 먼저 text3 div에서 날짜 관련 span.val 찾기
                date_element = soup.select_one("div.text3 span.val")
                if date_element:
                    published_date = date_element.get_text().strip()
                else:
                    # 대안 셀렉터들
                    alt_selectors = [
                        ".text_right .text3 .val",
                        "div.text_right div.text3 span.val",
                        "#container div.text3 span.val"
                    ]
                    published_date = "날짜 없음"
                    for selector in alt_selectors:
                        elem = soup.select_one(selector)
                        if elem and "202" in elem.get_text():  # 2024, 2025 등이 포함된 경우만
                            published_date = elem.get_text().strip()
                            break
            except Exception as e:
                published_date = f"날짜 추출 오류: {e}"

        view_count = soup.select_one("#container > div.contents > div.left_cont > ul > li > div.text > div.text_left > div.text2 > span:nth-child(4)").get_text().strip()
        view_count = view_count.replace(",", "")

        like_count = soup.select_one("#likeCnt").get_text().strip()
        like_count = like_count.replace(",", "")
        
        content = soup.select_one(".view_context").get_text().strip()

        post_data = {
            "id": params["id"],
            "title": title,
            "content": content,
            "published_date": published_date,
            "platform": "MLBPARK",
            "link": url,
            "view_count": view_count,
            "like_count": like_count,
            "user_id": None,
        }
        comments = self.get_comments(soup, params["id"])
        return post_data, comments
    
    def get_comments(self, soup, post_id):
        comment_containers = soup.select("div[id^='reply_']")[1:]
        comment_ids = []
        comments = []

        for i, comment_container in enumerate(comment_containers):
            comment_id = f"{post_id}_{i}"
            username = comment_container.select_one(".name").get_text().strip()
            content = comment_container.select_one(".re_txt").get_text().strip()
            published_date = comment_container.select_one(".date").get_text().strip()

            if "replied" in comment_container.get("class") or "replied_re" in comment_container.get("class"):
                parent_id = comment_ids[-1]
            else:
                parent_id = None

            if parent_id is None:
                comment_ids.append(comment_id)

            comments.append({
                "id": comment_id,
                "username": username,
                "start_count": None,
                "content": content,
                "platform": "MLBPARK",
                "blog_id": post_id,
                "parent_id": None,
                "published_date": published_date,
                "like_count": None,
            })

        return comments


    def is_time_only(self, published_date):
        return bool(re.match(r"^\d{1,2}:\d{1,2}:\d{1,2}$", published_date))

    def run(self, keyword, max_posts, start_date=None, end_date=None):

        page = 1
        visible_count = 30
        post_data = []
        comment_data = []
        count = 0

        # 공통 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://mlbpark.donga.com',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }

        while True: 
            url = f"https://mlbpark.donga.com/mp/b.php?p={page}&search_select=sct&search_input={keyword}&x=0&y=0&select=sct&m=search&b=bullpen&query={keyword}&h="
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, "html.parser")
            trs = soup.select("#container > div.contents > div.left_cont > div.tbl_box > table > tbody > tr")

            if len(trs) == 0:
                break
            for tr in trs:
                
                a = tr.select_one(".tit > a")
                url = a.get("href")
                published_date = tr.select_one("td:nth-child(4)").get_text().strip()
                
                # 목록에서 추출한 원본 날짜 문자열 저장
                original_date_str = published_date
                
                if self.is_time_only(published_date):
                    published_date = datetime.now().date()
                    formatted_date_str = str(published_date)
                else:
                    published_date = datetime.strptime(published_date, "%Y-%m-%d").date()
                    formatted_date_str = str(published_date)

                if start_date and end_date:
                    if not (start_date <= str(published_date) <= end_date):
                        # 날짜 범위 밖 게시물 건너뛰기 (로그 생략)
                        continue
                print(published_date)
                print(url)
                # 목록에서 추출한 올바른 날짜를 get_posts에 전달
                posts, comments = self.get_posts(url, formatted_date_str)
                if posts is None:
                    continue
                # save_to_json("MLBPARK", [posts], comments)
                post_data.append(posts)
                comment_data.extend(comments)
                count += 1
                if max_posts and count >= max_posts:
                    return post_data, comment_data

            page += visible_count

            print(page)
        
        # 수집 완료 후 일괄 저장
        if post_data:
            save_to_json("MLBPARK", post_data, comment_data)
            print(f"총 {len(post_data)}개의 게시물과 {len(comment_data)}개의 댓글을 수집했습니다.")
        
        return post_data, comment_data
                        
                        
                    
if __name__ == "__main__":
    crawler = MlbparkCrawler()
    crawler.run("아이온", None)

    
    


        

