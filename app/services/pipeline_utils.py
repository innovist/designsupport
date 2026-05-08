"""
Pipeline helper utilities
"""

# @MX:NOTE: [AUTO] Pipeline utilities - shared helper functions for data processing and formatting
# Provides URL fetching, file parsing, prompt building, and result formatting utilities

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable, Awaitable
import base64
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    PdfReader = None

from app.core.logging import get_logger
from app.core.config import get_local_now
from app.services.image_generation_service import ImageGenerationRequest

logger = get_logger(__name__)
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0 Safari/537.36"
    )
}


@dataclass
class ModelResultContext:
    model_prompt: str
    master_bytes: bytes
    idea_title: str
    index: int
    model_preference: Optional[str] = None
    is_children_clothing: bool = False


def detect_image_mime(image_bytes: bytes) -> str:
    if image_bytes.startswith(b"\x89PNG"):
        return "image/png"
    if image_bytes.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


def encode_image(image_bytes: bytes) -> Dict[str, Optional[str]]:
    if not image_bytes:
        return {"image_base64": None, "url": None}
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    mime = detect_image_mime(image_bytes)
    return {"image_base64": encoded, "url": f"data:{mime};base64,{encoded}"}


async def fetch_url_texts(urls: List[str]) -> List[Dict[str, str]]:
    texts: List[Dict[str, str]] = []
    for url in urls[:3]:
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=DEFAULT_HEADERS, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")
                text = " ".join(soup.stripped_strings)
                if text:
                    texts.append({"url": url, "text": text})
        except Exception as exc:
            logger.error(f"URL extraction failed: {url}, error={exc}")
    return texts


def extract_pdf_text(file_path: str) -> str:
    if not PYPDF_AVAILABLE or PdfReader is None:
        logger.warning(f"PDF reader not available: {file_path}")
        return ""
    try:
        reader = PdfReader(file_path)
        text = " ".join(page.extract_text() or "" for page in reader.pages)
        return " ".join(text.split())
    except Exception as exc:
        logger.error(f"PDF text extraction failed: {file_path}, error={exc}")
        return ""


async def extract_file_texts(
    files: List[Dict[str, Any]],
    describe_image: Callable[[str], Awaitable[Optional[str]]]
) -> List[Dict[str, str]]:
    texts: List[Dict[str, str]] = []
    for file_info in files:
        path = file_info.get("path")
        content_type = file_info.get("content_type", "")
        if not path:
            continue
        if content_type.startswith("image/"):
            summary = await describe_image(path)
            if summary:
                texts.append({"type": "image", "text": summary})
        elif content_type == "application/pdf":
            pdf_text = extract_pdf_text(path)
            if pdf_text:
                texts.append({"type": "pdf", "text": pdf_text})
        else:
            logger.warning(f"Unsupported file type: {content_type}")
    return texts


def parse_json(text: str) -> Dict[str, Any]:
    import json
    import re
    import logging
    logger = logging.getLogger(__name__)

    if not text or not isinstance(text, str):
        logger.error(f"parse_json: invalid input type={type(text)}, value={text}")
        raise ValueError("JSON parse failed: empty or invalid input")

    def _extract_json_block(raw: str) -> str:
        """마크다운 코드 블록에서 JSON 추출"""
        # ```json ... ``` 패턴
        pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
        matches = re.findall(pattern, raw, re.DOTALL | re.IGNORECASE)
        if matches:
            return matches[0].strip()
        return raw

    def _repair_json(json_str: str) -> str:
        """JSON 보정 - 흔한 실수 수정"""
        # 1. 후행 쉼표 제거 ({"a": 1,} → {"a": 1}, [1,2,] → [1,2])
        json_str = re.sub(r",\s*([}\]])", r"\1", json_str)

        # 2. 따옴표 누락된 키 보정 ({a: 1} → {"a": 1})
        json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', json_str)

        # 3. 작은따옴표를 큰따옴표로 변환 ({'a': 1} → {"a": 1})
        json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)

        # 4. 주석 제거 (// 주석, /* 주석 */)
        json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

        # 5. 제어 문자 제거
        json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)

        # 6. 불필요한 쉼표 정리 (,, → ,)
        json_str = re.sub(r',+,', ',', json_str)

        return json_str.strip()

    # 1. 직접 파싱 시도
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.debug(f"Direct JSON parse failed: {e}, attempting repair")

    # 2. 마크다운 코드 블록 제거 후 시도
    cleaned = _extract_json_block(text)
    if cleaned != text:
        try:
            result = json.loads(cleaned)
            logger.debug("Successfully parsed after extracting markdown block")
            return result
        except json.JSONDecodeError:
            pass

    # 3. 중괄호 추출
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        # 대괄호 배열 시도
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start == -1 or end == -1 or end <= start:
            logger.error(f"parse_json: no JSON structure found (length={len(text)}): {text[:300]}...")
            raise ValueError("JSON parse failed: no JSON structure found")

    snippet = cleaned[start:end + 1]

    # 4. 보정 후 파싱 시도
    repaired = _repair_json(snippet)
    try:
        result = json.loads(repaired)
        logger.debug("Successfully parsed after repair")
        return result
    except json.JSONDecodeError as e:
        # 5. 최후 시도: 중첩된 객체 처리
        try:
            # 가장 안쪽의 완전한 JSON 객체 찾기
            brace_count = 0
            json_start = -1
            for i, char in enumerate(snippet):
                if char == '{':
                    if brace_count == 0:
                        json_start = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and json_start != -1:
                        candidate = snippet[json_start:i + 1]
                        candidate_repaired = _repair_json(candidate)
                        try:
                            result = json.loads(candidate_repaired)
                            logger.debug("Successfully parsed after extracting innermost object")
                            return result
                        except json.JSONDecodeError:
                            continue
        except Exception:
            pass

        logger.error(f"parse_json: all repair attempts failed. Error: {e}. Snippet: {snippet[:300]}...")
        raise ValueError(f"JSON parse failed after repair attempts: {e}") from e


def is_children_clothing(filters: Dict[str, Any]) -> bool:
    """아동복 대상인지 확인 (연령 필터 및 카테고리 모두 확인)"""
    if not filters:
        return False

    # 1. 연령 필터 확인 (가장 중요!)
    age = filters.get("age", [])
    if isinstance(age, str):
        age = [age]

    children_ages = ["toddler", "child", "teen"]
    if any(a in children_ages for a in age):
        return True

    # 2. 카테고리 확인 (레거시 호환)
    category = filters.get("category", "")
    if isinstance(category, str):
        category = [category]

    children_keywords = [
        "아동복", "아동", "키즈", "키즈웨어", "유아복", "유아",
        "아이", "아이들", "어린이", "children", "kids", "toddler",
        "boy", "girl", "junior", "내복"
    ]

    category_text = " ".join(str(c).lower() for c in category if c)
    return any(kw in category_text for kw in children_keywords)


def _build_filter_context_for_prompt(filters: Dict[str, Any]) -> str:
    """필터 정보를 프롬프트용 컨텍스트로 변환 (필수 포함)"""
    if not filters:
        return ""

    parts = []

    # 연령대 (매우 중요!)
    age = filters.get("age", [])
    if isinstance(age, str):
        age = [age] if age else []
    if age:
        age_map = {
            "toddler": "toddler (0-5 years old)",
            "child": "child (6-12 years old)",
            "teen": "teenager (13-19 years old)",
            "20s": "young adult in 20s",
            "30s": "adult in 30s",
            "40s": "adult in 40s",
            "50s_plus": "adult 50+"
        }
        age_texts = [age_map.get(a, a) for a in age if a]
        if age_texts:
            parts.append(f"Target age: {', '.join(age_texts)}")

    # 성별
    gender = filters.get("gender", [])
    if isinstance(gender, str):
        gender = [gender] if gender else []
    if gender:
        gender_map = {"female": "women's/girls'", "male": "men's/boys'", "unisex": "unisex"}
        gender_texts = [gender_map.get(g, g) for g in gender if g]
        if gender_texts:
            parts.append(f"Gender: {', '.join(gender_texts)}")

    # 카테고리
    category = filters.get("category", [])
    if isinstance(category, str):
        category = [category] if category else []
    if category:
        parts.append(f"Category: {', '.join(category)}")

    # 계절
    season = filters.get("season", [])
    if isinstance(season, str):
        season = [season] if season else []
    if season:
        season_map = {
            "spring": "Spring", "summer": "Summer",
            "fall": "Fall/Autumn", "winter": "Winter"
        }
        season_texts = [season_map.get(s, s) for s in season if s]
        if season_texts:
            parts.append(f"Season: {', '.join(season_texts)}")

    return ". ".join(parts) + "." if parts else ""


def build_master_prompt(prompt: str, filters: Dict[str, Any] = None) -> str:
    """마스터 디자인 프롬프트 생성 (필터 정보 필수 포함)"""
    filters = filters or {}
    is_kids = is_children_clothing(filters)
    filter_context = _build_filter_context_for_prompt(filters)

    # 필터 컨텍스트를 프롬프트 앞에 배치
    target_info = ""
    if filter_context:
        target_info = f"[TARGET SPECIFICATION: {filter_context}]\n"

    base_prompt = f"""{target_info}Professional fashion design flat lay photography.
{prompt}
Clean white background, centered composition, soft studio lighting,
high detail, 8k quality, fashion catalog style, no model, garment only."""

    if is_kids:
        base_prompt += "\nIMPORTANT: This is CHILDREN'S clothing. Size and proportion must be appropriate for kids, NOT adult clothing."

    # 네거티브 요소 추가 (텍스트, 잡지 표지 등 방지)
    base_prompt += "\nNo text, no letters, no watermarks, no logos, no magazine cover style."

    return base_prompt


def build_model_prompt(prompt: str, filters: Dict[str, Any] = None) -> str:
    """모델 착용 프롬프트 생성 (필터 정보 필수 포함)"""
    filters = filters or {}
    is_kids = is_children_clothing(filters)
    filter_context = _build_filter_context_for_prompt(filters)

    # 필터 컨텍스트를 프롬프트 앞에 배치
    target_info = ""
    if filter_context:
        target_info = f"[TARGET SPECIFICATION: {filter_context}]\n"

    if is_kids:
        # 아동 연령 세분화
        age = filters.get("age", [])
        if isinstance(age, str):
            age = [age] if age else []

        age_desc = "child (6-12 years old)"
        if "toddler" in age:
            age_desc = "toddler (2-5 years old)"
        elif "teen" in age:
            age_desc = "teenager (13-16 years old)"

        return f"""{target_info}Professional kids fashion photography, high-end editorial.
{age_desc.capitalize()} model wearing {prompt}.
Full body shot, studio lighting, clean background,
fashion magazine quality, 8k, sharp focus.
IMPORTANT: Age-appropriate {age_desc} model, kids fashion style.
Children's clothing proportions and sizing.
No adult features, no mature elements, no adult models.
No text, no letters, no watermarks, no logos in image."""

    return f"""{target_info}Professional fashion photography, high-end editorial.
Fashion model wearing {prompt}.
Full body shot, studio lighting, clean background,
fashion magazine quality, 8k, sharp focus.
No text, no letters, no watermarks, no logos in image."""


def append_master_result(
    results: List[Dict[str, Any]],
    master_result: Any,
    idea_title: str,
    master_prompt: str,
    index: int
) -> Optional[bytes]:
    if not master_result.images:
        return None
    master_bytes = master_result.images[0]
    payload = encode_image(master_bytes)
    results.append({
        "type": "design",
        "title": f"{idea_title} - Design",
        "prompt": master_prompt,
        "model_used": master_result.model_used,
        "created_at": get_local_now().isoformat(),
        "idea_index": index + 1,
        **payload
    })
    return master_bytes


async def append_model_results(
    image_service: Any,
    results: List[Dict[str, Any]],
    context: ModelResultContext
) -> None:
    model_request = ImageGenerationRequest(
        prompt=context.model_prompt,
        style="editorial",
        garment_type="model_fitting",
        num_variations=2,
        reference_image=context.master_bytes,
        model_preference=context.model_preference,
        is_children_clothing=context.is_children_clothing
    )
    try:
        model_result = await image_service.generate_fashion_design(model_request)
        for img_idx, img_bytes in enumerate(model_result.images[:2]):
            payload = encode_image(img_bytes)
            results.append({
                "type": "model",
                "title": f"{context.idea_title} - Model {img_idx + 1}",
                "prompt": context.model_prompt,
                "model_used": model_result.model_used,
                "created_at": get_local_now().isoformat(),
                "idea_index": context.index + 1,
                "pose": img_idx + 1,
                **payload
            })
    except Exception as exc:
        logger.warning(f"Model fitting generation failed: {exc}")
