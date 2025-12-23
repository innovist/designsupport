"""
Pipeline helper utilities
"""

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
    def _sanitize(value: str) -> str:
        return re.sub(r",\s*([}\]])", r"\1", value)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("JSON parse failed")
        snippet = text[start:end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            return json.loads(_sanitize(snippet))


def build_master_prompt(prompt: str) -> str:
    return f"""Professional fashion design flat lay photography.
{prompt}
Clean white background, centered composition, soft studio lighting,
high detail, 8k quality, fashion catalog style, no model, garment only."""


def build_model_prompt(prompt: str) -> str:
    return f"""Professional fashion photography, high-end editorial.
Fashion model wearing {prompt}.
Full body shot, studio lighting, clean background,
fashion magazine quality, 8k, sharp focus."""


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
        "created_at": datetime.utcnow().isoformat(),
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
        model_preference=context.model_preference
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
                "created_at": datetime.utcnow().isoformat(),
                "idea_index": context.index + 1,
                "pose": img_idx + 1,
                **payload
            })
    except Exception as exc:
        logger.warning(f"Model fitting generation failed: {exc}")
