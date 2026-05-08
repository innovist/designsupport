"""
Pipeline generation steps for images and blueprints
"""

# @MX:NOTE: [AUTO] Pipeline generation steps - orchestrates image and blueprint generation
# Provides step-by-step generation workflow with progress tracking and error handling

from datetime import datetime
from typing import List, Dict, Any, Callable

from app.services.image_generation_service import ImageGenerationRequest
from app.core.config import get_local_now
from app.services.pipeline_utils import (
    build_master_prompt,
    build_model_prompt,
    append_master_result,
    append_model_results,
    ModelResultContext,
    encode_image,
    is_children_clothing
)

ProgressCallback = Callable[[str, float, str], None]


async def generate_images(
    session_data: Dict[str, Any],
    ideas: List[Dict[str, Any]],
    image_service: Any,
    progress_cb: ProgressCallback
) -> List[Dict[str, Any]]:
    if not session_data.get("generate_images", True):
        progress_cb("image_generation", 85, "이미지 생성 스킵")
        return []
    progress_cb("image_generation", 82, "이미지 생성 시작")
    results: List[Dict[str, Any]] = []
    model_preference = session_data.get("preferred_image_model")
    filters = session_data.get("filters", {})
    is_kids = is_children_clothing(filters)
    for index, idea in enumerate(ideas[:3]):
        idea_title = idea.get("concept_name") or idea.get("concept") or idea.get("title") or f"Idea {index + 1}"
        prompt = idea.get("prompt") or idea.get("concept") or idea.get("concept_name") or "fashion design"
        master_prompt = build_master_prompt(prompt, filters)
        request = ImageGenerationRequest(
            prompt=master_prompt,
            style="flat_lay",
            garment_type="design",
            num_variations=1,
            is_children_clothing=is_kids
        )
        master_result = await image_service.generate_fashion_design(request)
        master_bytes = append_master_result(
            results,
            master_result,
            idea_title,
            master_prompt,
            index
        )
        if master_bytes:
            model_prompt = build_model_prompt(prompt, filters)
            context = ModelResultContext(
                model_prompt=model_prompt,
                master_bytes=master_bytes,
                idea_title=idea_title,
                index=index,
                model_preference=model_preference,
                is_children_clothing=is_kids
            )
            await append_model_results(
                image_service,
                results,
                context
            )
        progress = 82 + ((index + 1) / min(len(ideas), 3)) * 10
        progress_cb("image_generation", progress, f"디자인 {index + 1} 완료 (마스터 + 착장)")
    progress_cb("image_generation", 92, "이미지 생성 완료")
    return results


async def generate_blueprints(
    session_data: Dict[str, Any],
    ideas: List[Dict[str, Any]],
    blueprint_service: Any,
    progress_cb: ProgressCallback
) -> List[Dict[str, Any]]:
    # 블루프린트는 기본적으로 생성 (명시적으로 끄지 않으면 생성)
    if session_data.get("skip_blueprints", False) is True:
        progress_cb("blueprint_generation", 93, "블루프린트 생성 스킵 (사용자 설정)")
        return []

    size_system = session_data.get("blueprint_size_system", "KS")
    size = session_data.get("blueprint_size", "M")

    # 필터 정보를 디자인 설명에 반영
    filters = session_data.get("filters") or {}
    filter_context = _build_filter_context(filters)

    progress_cb("blueprint_generation", 93, "블루프린트 3종 생성 시작")
    results: List[Dict[str, Any]] = []
    for index, idea in enumerate(ideas[:2]):
        idea_title = idea.get("concept_name") or idea.get("concept") or idea.get("title") or f"Idea {index + 1}"
        base_description = idea.get("description") or idea.get("concept") or idea.get("prompt") or "fashion design"

        # 필터 정보를 포함한 상세 설명 생성
        detailed_description = f"{filter_context} {base_description}".strip()

        three_blueprints = await blueprint_service.generate_three_blueprints(
            design_image=b"",
            design_description=detailed_description,
            size_system=size_system,
            size=size
        )
        for bp_type, label in (("sketch", "Sketch"), ("layout", "Layout"), ("pattern", "Pattern")):
            bp = three_blueprints.get(bp_type)
            if not bp or not bp.image_bytes:
                continue
            payload = encode_image(bp.image_bytes)
            item = {
                "type": bp_type,
                "title": f"{idea_title} - {label}",
                "prompt": detailed_description,
                "resolution": bp.resolution,
                "created_at": get_local_now().isoformat(),
                "idea_index": index + 1,
                **payload
            }
            if bp_type == "pattern":
                item["size_system"] = size_system
                item["size"] = size
            results.append(item)
        progress = 93 + ((index + 1) / min(len(ideas), 2)) * 7
        progress_cb("blueprint_generation", progress, f"블루프린트 {index + 1} (3종) 생성 완료")
    progress_cb("blueprint_generation", 100, "블루프린트 3종 생성 완료")
    return results


def _build_filter_context(filters: Dict[str, Any]) -> str:
    """필터 정보를 디자인 프롬프트용 컨텍스트로 변환"""
    parts = []

    # 연령대 (중요!)
    age = filters.get("age", [])
    if age:
        age_map = {
            "toddler": "유아(0-5세)",
            "child": "아동(6-12세)",
            "teen": "청소년(13-19세)",
            "20s": "20대",
            "30s": "30대",
            "40s": "40대",
            "50s_plus": "50대 이상"
        }
        age_text = ", ".join([age_map.get(a, a) for a in age if isinstance(a, str)])
        if age_text:
            parts.append(f"타겟 연령: {age_text}")

    # 성별
    gender = filters.get("gender", [])
    if gender:
        gender_map = {"female": "여성", "male": "남성", "unisex": "유니섹스"}
        gender_text = ", ".join([gender_map.get(g, g) for g in gender if isinstance(g, str)])
        if gender_text:
            parts.append(f"성별: {gender_text}")

    # 카테고리
    category = filters.get("category", [])
    if category:
        from app.services.pipeline_crawl_utils import FILTER_VALUE_MAP
        cat_map = FILTER_VALUE_MAP.get("category", {})
        cat_text = ", ".join([cat_map.get(c, c) for c in category if isinstance(c, str)])
        if cat_text:
            parts.append(f"카테고리: {cat_text}")

    # 계절
    season = filters.get("season", [])
    if season:
        season_map = {
            "spring": "봄", "summer": "여름", "fall": "가을", "winter": "겨울",
            "ss": "봄/여름", "fw": "가을/겨울"
        }
        season_text = ", ".join([season_map.get(s, s) for s in season if isinstance(s, str)])
        if season_text:
            parts.append(f"시즌: {season_text}")

    return " ".join(parts) + ". " if parts else ""
