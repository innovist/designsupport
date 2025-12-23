"""
Common utilities for crawlers
"""

import re
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class NetworkUtils:
    """네트워크 관련 유틸리티"""

    @staticmethod
    def get_session(
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> requests.Session:
        """
        기본 requests 세션 생성

        Args:
            headers: 요청 헤더
            timeout: 타임아웃 (초)

        Returns:
            requests Session 객체
        """
        session = requests.Session()

        # 기본 헤더
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

        if headers:
            default_headers.update(headers)

        session.headers.update(default_headers)
        session.timeout = timeout

        return session

    @staticmethod
    def request_get(
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 3,
        delay: float = 1.0
    ) -> Optional[requests.Response]:
        """
        GET 요청 실행 (재시도 포함)

        Args:
            url: 요청 URL
            params: 쿼리 파라미터
            headers: 요청 헤더
            retries: 재시도 횟수
            delay: 재시도 간격 (초)

        Returns:
            응답 객체 또는 None
        """
        session = NetworkUtils.get_session(headers=headers)

        for attempt in range(retries + 1):
            try:
                response = session.get(url, params=params)
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                if attempt < retries:
                    logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"Request failed after {retries} retries: {e}")
                    return None
            finally:
                session.close()

        return None


class DataUtils:
    """데이터 처리 유틸리티"""

    @staticmethod
    def save_to_json(data: Union[List, Dict], filepath: str) -> bool:
        """
        데이터를 JSON 파일로 저장

        Args:
            data: 저장할 데이터
            filepath: 파일 경로

        Returns:
            성공 여부
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
            return False

    @staticmethod
    def load_from_json(filepath: str) -> Optional[Union[List, Dict]]:
        """
        JSON 파일에서 데이터 로드

        Args:
            filepath: 파일 경로

        Returns:
            로드된 데이터 또는 None
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON: {e}")
            return None

    @staticmethod
    def json_to_tsv(data: List[Dict], filepath: str) -> bool:
        """
        JSON 데이터를 TSV 파일로 변환

        Args:
            data: 변환할 데이터
            filepath: 파일 경로

        Returns:
            성공 여부
        """
        if not data:
            return False

        try:
            # 모든 키 수집
            all_keys = set()
            for item in data:
                all_keys.update(item.keys())

            # TSV 작성
            with open(filepath, 'w', encoding='utf-8') as f:
                # 헤더
                f.write('\t'.join(all_keys) + '\n')

                # 데이터
                for item in data:
                    row = []
                    for key in all_keys:
                        value = item.get(key, '')
                        if isinstance(value, (list, dict)):
                            value = json.dumps(value, ensure_ascii=False)
                        row.append(str(value))
                    f.write('\t'.join(row) + '\n')

            return True
        except Exception as e:
            logger.error(f"Failed to convert to TSV: {e}")
            return False


class DateUtils:
    """날짜 처리 유틸리티"""

    # 한글 숫자 단위
    KOREAN_NUMBERS = {
        '만': 10000,
        '천': 1000,
        '백': 100,
        '십': 10,
        '개': 1,
    }

    # 날짜 형식 패턴
    DATE_PATTERNS = [
        # ISO 형식
        (r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', lambda m: datetime(int(m[1]), int(m[2]), int(m[3]))),
        # 한국 형식
        (r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', lambda m: datetime(int(m[1]), int(m[2]), int(m[3]))),
        # 월/일 형식
        (r'(\d{1,2})월\s*(\d{1,2})일', lambda m: datetime(datetime.now().year, int(m[1]), int(m[2]))),
        # 미국 형식
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: datetime(int(m[3]), int(m[1]), int(m[2]))),
    ]

    @staticmethod
    def parse_date_string(date_str: str) -> Optional[datetime]:
        """
        다양한 형식의 날짜 문자열 파싱

        Args:
            date_str: 날짜 문자열

        Returns:
            datetime 객체 또는 None
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        for pattern, converter in DateUtils.DATE_PATTERNS:
            match = re.search(pattern, date_str)
            if match:
                try:
                    return converter(match)
                except ValueError:
                    continue

        return None

    @staticmethod
    def parse_relative_time(time_str: str) -> Optional[datetime]:
        """
        상대 시간 파싱 ("3분 전", "2시간 전" 등)

        Args:
            time_str: 상대 시간 문자열

        Returns:
            datetime 객체 또는 None
        """
        if not time_str:
            return None

        now = datetime.utcnow()
        time_str = time_str.lower().strip()

        # 방금 전
        if '방금' in time_str or 'just now' in time_str:
            return now - timedelta(minutes=1)

        # 분 단위
        min_match = re.search(r'(\d+)\s*분', time_str)
        if min_match:
            minutes = int(min_match.group(1))
            return now - timedelta(minutes=minutes)

        # 시간 단위
        hour_match = re.search(r'(\d+)\s*시', time_str)
        if hour_match:
            hours = int(hour_match.group(1))
            return now - timedelta(hours=hours)

        # 일 단위
        day_match = re.search(r'(\d+)\s*일', time_str)
        if day_match:
            days = int(day_match.group(1))
            return now - timedelta(days=days)

        # 주 단위
        week_match = re.search(r'(\d+)\s*주', time_str)
        if week_match:
            weeks = int(week_match.group(1))
            return now - timedelta(weeks=weeks)

        # 월 단위 (대략 30일)
        month_match = re.search(r'(\d+)\s*개?월', time_str)
        if month_match:
            months = int(month_match.group(1))
            return now - timedelta(days=months * 30)

        # 년 단위
        year_match = re.search(r'(\d+)\s*년', time_str)
        if year_match:
            years = int(year_match.group(1))
            return now - timedelta(days=years * 365)

        return None

    @staticmethod
    def is_date_in_range(
        date: datetime,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bool:
        """
        날짜가 범위 내에 있는지 확인

        Args:
            date: 확인할 날짜
            start_date: 시작일
            end_date: 종료일

        Returns:
            범위 내 여부
        """
        if start_date and date < start_date:
            return False
        if end_date and date > end_date:
            return False
        return True

    @staticmethod
    def clean_date_string_for_crawler(date_str: str) -> str:
        """
        크롤링용 날짜 문자열 정제

        Args:
            date_str: 정제할 날짜 문자열

        Returns:
            정제된 날짜 문자열
        """
        if not date_str:
            return ""

        # 불필요한 문자 제거
        cleaned = re.sub(r'[^\d\s년월일시분초]', '', date_str)

        # 여러 공백을 단일 공백으로
        cleaned = re.sub(r'\s+', ' ', cleaned)

        return cleaned.strip()


class NumberUtils:
    """숫자 처리 유틸리티"""

    @staticmethod
    def parse_korean_number(number_str: str) -> int:
        """
        한글 숫자 변환 ("7.3천" → 7300)

        Args:
            number_str: 한글 숫자 문자열

        Returns:
            변환된 숫자
        """
        if not number_str:
            return 0

        number_str = number_str.strip().replace(',', '')

        # 이미 숫자면 그대로 반환
        if number_str.isdigit():
            return int(number_str)

        # 소수점 처리
        if '.' in number_str:
            parts = number_str.split('.')
            if len(parts) == 2 and parts[0].isdigit():
                base = int(parts[0])
                unit = parts[1]

                if unit in DateUtils.KOREAN_NUMBERS:
                    return int(base * DateUtils.KOREAN_NUMBERS[unit])

        # 한글 단위 처리
        total = 0
        current = 0

        for char in number_str:
            if char.isdigit():
                current = current * 10 + int(char)
            elif char in DateUtils.KOREAN_NUMBERS:
                if current == 0:
                    current = 1
                total += current * DateUtils.KOREAN_NUMBERS[char]
                current = 0

        total += current
        return total

    @staticmethod
    def extract_numbers(text: str) -> List[int]:
        """
        텍스트에서 모든 숫자 추출

        Args:
            text: 텍스트

        Returns:
            추출된 숫자 목록
        """
        # 정수 패턴
        integers = re.findall(r'\b\d+\b', text)
        # 소수 패턴
        decimals = re.findall(r'\b\d+\.\d+\b', text)
        # 한글 숫자 패턴
        korean_numbers = re.findall(r'\d+[.]*\d*\s*[천백만십개]', text)

        numbers = []

        # 정수 추가
        for num in integers:
            numbers.append(int(num))

        # 소수 추가 (정수로 변환)
        for num in decimals:
            numbers.append(int(float(num)))

        # 한글 숫자 추가
        for num_str in korean_numbers:
            numbers.append(NumberUtils.parse_korean_number(num_str))

        return numbers


class TextUtils:
    """텍스트 처리 유틸리티"""

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """
        텍스트에서 모든 URL 추출

        Args:
            text: 텍스트

        Returns:
            추출된 URL 목록
        """
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(url_pattern, text)

    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """
        텍스트에서 해시태그 추출

        Args:
            text: 텍스트

        Returns:
            추출된 해시태그 목록
        """
        hashtag_pattern = r'#(\w+)'
        return re.findall(hashtag_pattern, text)

    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """
        텍스트에서 멘션 추출

        Args:
            text: 텍스트

        Returns:
            추출된 멘션 목록
        """
        mention_pattern = r'@(\w+)'
        return re.findall(mention_pattern, text)

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        텍스트 정규화

        Args:
            text: 정규화할 텍스트

        Returns:
            정규화된 텍스트
        """
        if not text:
            return ""

        # 공백 정규화
        text = re.sub(r'\s+', ' ', text)

        # 특수문자 주변 공백 추가
        text = re.sub(r'([.,!?;:])', r' \1 ', text)

        # 여러 공백을 단일 공백으로
        text = re.sub(r'\s+', ' ', text)

        return text.strip()


class FileUtils:
    """파일 처리 유틸리티"""

    @staticmethod
    def ensure_directory(filepath: str) -> bool:
        """
        디렉토리 생성

        Args:
            filepath: 파일 경로

        Returns:
            성공 여부
        """
        import os
        try:
            directory = os.path.dirname(filepath)
            if directory:
                os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory: {e}")
            return False

    @staticmethod
    def get_file_extension(url: str) -> str:
        """
        URL에서 파일 확장자 추출

        Args:
            url: 파일 URL

        Returns:
            파일 확장자
        """
        parsed = urlparse(url)
        path = parsed.path

        if '.' in path:
            return path.split('.')[-1].lower()

        return ''

    @staticmethod
    def generate_filename(
        prefix: str,
        extension: str = '',
        timestamp: bool = True
    ) -> str:
        """
        파일 이름 생성

        Args:
            prefix: 접두사
            extension: 확장자
            timestamp: 타임스탬프 포함 여부

        Returns:
            생성된 파일 이름
        """
        filename = prefix

        if timestamp:
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename += f'_{timestamp_str}'

        if extension:
            if not extension.startswith('.'):
                extension = '.' + extension
            filename += extension

        return filename


# ===== 레거시 호환 함수 =====
# youtube_crawler.py 등 기존 코드와의 호환성 유지

import os


def save_to_json(platform: str, post_data: List, comments_data: List, output_dir: str = "crawling_data") -> None:
    """레거시 호환: 플랫폼별 JSON 파일 저장 (원본 시그니처 유지)"""
    os.makedirs(output_dir, exist_ok=True)

    content_path = f"{output_dir}/{platform}.json"
    comment_path = f"{output_dir}/{platform}_comments.json"

    contents = []
    comments = []

    if os.path.exists(content_path):
        try:
            with open(content_path, "r", encoding="utf-8") as f:
                contents = json.load(f)
        except Exception:
            contents = []

    if os.path.exists(comment_path):
        try:
            with open(comment_path, "r", encoding="utf-8") as f:
                comments = json.load(f)
        except Exception:
            comments = []

    contents.extend(post_data)
    comments.extend(comments_data)

    with open(content_path, "w", encoding="utf-8") as f:
        json.dump(contents, f, ensure_ascii=False, indent=4, default=str)

    with open(comment_path, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=4, default=str)


def parse_korean_number(number_str: str) -> int:
    """레거시 호환: NumberUtils.parse_korean_number 래핑"""
    return NumberUtils.parse_korean_number(number_str)