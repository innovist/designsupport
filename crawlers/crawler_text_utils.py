"""
Text utility helpers for crawlers
"""

from typing import List
import re


def extract_fashion_keywords(text: str) -> List[str]:
    """텍스트에서 패션 관련 키워드 추출"""
    if not text:
        return []

    fashion_keywords = {
        '상의': ['티셔츠', '셔츠', '블라우스', '니트', '스웨터', '후드', '맨투맨'],
        '하의': ['바지', '청바지', '스커트', '치마', '숏팬츠', '슬랙스'],
        '외투': ['코트', '자켓', '점퍼', '블레이저', '가디건', '무스탕'],
        '원피스': ['드레스', '원피스', '점프수트'],
        '신발': ['운동화', '구두', '부츠', '샌들', '힐', '플랫폼'],
        '소재': ['코튼', '린넨', '울', '실크', '데님', '레이스', '가죽'],
        '색상': ['블랙', '화이트', '베이지', '그레이', '네이비', '브라운'],
        '스타일': ['미니멀', '스트릿', '캐주얼', '포멀', '빈티지', '레트로'],
        '패턴': ['체크', '스트라이프', '도트', '플로럴', '카모', '아니멀'],
    }

    found_keywords = []
    text_lower = text.lower()

    for keywords in fashion_keywords.values():
        for keyword in keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)

    return list(set(found_keywords))


def extract_product_links(text: str, base_url: str = "") -> List[str]:
    """텍스트에서 상품 링크 추출"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)

    shopping_domains = [
        'musinsa', '29cm', 'abcmart', 'nike', 'adidas', 'zara',
        'uniqlo', 'h&m', 'gap', 'forever21', 'spao'
    ]

    product_links = []
    for url in urls:
        url_lower = url.lower()
        if any(domain in url_lower for domain in shopping_domains):
            product_links.append(url)

    return product_links


def extract_image_urls(text: str, base_url: str = "") -> List[str]:
    """텍스트에서 이미지 URL 추출"""
    img_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\\.(?:jpg|jpeg|png|gif|webp)'
    img_urls = re.findall(img_pattern, text, re.IGNORECASE)
    return list(set(img_urls))


def clean_text(text: str) -> str:
    """텍스트 정제"""
    if not text:
        return ""

    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\u3131-\u3163\uac00-\ud7a3.!?~,\-]', '', text)
    return text.strip()
