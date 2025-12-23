"""
Pipeline generation steps for images and blueprints
"""

from datetime import datetime
from typing import List, Dict, Any, Callable

from app.services.image_generation_service import ImageGenerationRequest
from app.services.pipeline_utils import (
    build_master_prompt,
    build_model_prompt,
    append_master_result,
    append_model_results,
    ModelResultContext,
    encode_image
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
    for index, idea in enumerate(ideas[:3]):
        idea_title = idea.get("concept_name") or idea.get("concept") or idea.get("title") or f"Idea {index + 1}"
        prompt = idea.get("prompt") or idea.get("concept") or idea.get("concept_name") or "fashion design"
        master_prompt = build_master_prompt(prompt)
        request = ImageGenerationRequest(
            prompt=master_prompt,
            style="flat_lay",
            garment_type="design",
            num_variations=1
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
            model_prompt = build_model_prompt(prompt)
            context = ModelResultContext(
                model_prompt=model_prompt,
                master_bytes=master_bytes,
                idea_title=idea_title,
                index=index,
                model_preference=model_preference
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
    if not session_data.get("generate_blueprints", False):
        progress_cb("blueprint_generation", 93, "블루프린트 생성 스킵")
        return []
    size_system = session_data.get("blueprint_size_system", "KS")
    size = session_data.get("blueprint_size", "M")
    progress_cb("blueprint_generation", 93, "블루프린트 3종 생성 시작")
    results: List[Dict[str, Any]] = []
    for index, idea in enumerate(ideas[:2]):
        idea_title = idea.get("concept_name") or idea.get("concept") or idea.get("title") or f"Idea {index + 1}"
        description = idea.get("description") or idea.get("concept") or idea.get("prompt") or "fashion design"
        three_blueprints = await blueprint_service.generate_three_blueprints(
            design_image=b"",
            design_description=description,
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
                "prompt": description,
                "resolution": bp.resolution,
                "created_at": datetime.utcnow().isoformat(),
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
