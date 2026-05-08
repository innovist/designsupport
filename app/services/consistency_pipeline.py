"""
Consistency Pipeline for Fashion AI Generation System
패션 디자인의 일관성을 유지하는 파이프라인
"""

# @MX:TODO: [AUTO] Missing integration tests for consistency validation workflow
# ConsistencyPipeline lacks end-to-end tests for reference image tracking and quality gates

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from app.core.logging import get_logger
from app.utils.system_detector import get_available_image_models
from ai_clients.zimage_client import ZImageClient
from ai_clients.seedream_client import SeedreamClient
from ai_clients.nano_banana_client import NanoBananaClient

logger = get_logger(__name__)


@dataclass
class ReferenceImage:
    """참조 이미지 정보"""
    id: str
    image_path: str
    image_bytes: bytes
    created_at: datetime
    design_id: str
    stage: str  # 'master', 'model', 'blueprint'
    metadata: Dict[str, Any]


@dataclass
class GenerationResult:
    """생성 결과"""
    success: bool
    image_path: Optional[str] = None
    image_bytes: Optional[bytes] = None
    generation_time: float = 0.0
    model_used: str = ""
    confidence_score: float = 0.0


class ReferenceImageStore:
    """참조 이미지 저장소"""

    def __init__(self):
        self.images: Dict[str, ReferenceImage] = {}
        self.base_path = Path("storage/references")
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save(self, image_bytes: bytes, design_id: str, stage: str, metadata: Dict = None) -> str:
        """이미지 저장 및 ID 반환"""
        import uuid
        ref_id = f"ref_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now()

        # 파일 저장
        image_path = self.base_path / f"{ref_id}.png"
        with open(image_path, "wb") as f:
            f.write(image_bytes)

        # 메모리에 저장
        ref_image = ReferenceImage(
            id=ref_id,
            image_path=str(image_path),
            image_bytes=image_bytes,
            created_at=timestamp,
            design_id=design_id,
            stage=stage,
            metadata=metadata or {}
        )

        self.images[ref_id] = ref_image
        return ref_id

    def get(self, ref_id: str) -> Optional[ReferenceImage]:
        """참조 이미지 조회"""
        return self.images.get(ref_id)

    def get_by_design(self, design_id: str) -> List[ReferenceImage]:
        """디자인 ID로 참조 이미지 목록 조회"""
        return [img for img in self.images.values() if img.design_id == design_id]


class ConsistencyController:
    """일관성 제어기"""

    def __init__(self):
        self.reference_strength = 0.8
        self.controlnet_type = "canny"  # canny, depth, pose

    def generate_controlnet_params(self, ref_type: str) -> Dict[str, Any]:
        """ControlNet 파라미터 생성"""
        base_params = {
            "reference_strength": self.reference_strength,
            "controlnet_type": self.controlnet_type,
            "guidance_strength": 7.5
        }

        # 참조 타입별 최적화
        if ref_type == "garment":
            base_params.update({
                "controlnet_type": "canny",
                "guidance_strength": 8.0
            })
        elif ref_type == "model":
            base_params.update({
                "controlnet_type": "pose",
                "guidance_strength": 6.0
            })
        elif ref_type == "blueprint":
            base_params.update({
                "controlnet_type": "lineart",
                "guidance_strength": 9.0
            })

        return base_params


class I2IGenerator:
    """Image-to-Image 생성기"""

    def __init__(self):
        self.zimage_client = ZImageClient()
        self.seedream_client = SeedreamClient()
        self.nano_client = NanoBananaClient()
        self.controller = ConsistencyController()

    async def generate_with_reference(
        self,
        prompt: str,
        reference_image: bytes,
        ref_type: str = "garment",
        model_preference: Optional[str] = None
    ) -> GenerationResult:
        """참조 이미지 기반 이미지 생성"""
        available_models = get_available_image_models()

        # 모델 선택
        if model_preference and model_preference in available_models:
            models = [model_preference] + [m for m in available_models if m != model_preference]
        else:
            models = available_models

        # ControlNet 파라미터
        cn_params = self.controller.generate_controlnet_params(ref_type)

        # 최적화된 프롬프트 생성
        optimized_prompt = self._optimize_prompt_for_consistency(prompt, reference_image)

        last_error = None
        for model_name in models:
            try:
                start_time = asyncio.get_event_loop().time()

                if model_name == "zimage":
                    result = await self._generate_with_zimage(
                        optimized_prompt,
                        reference_image,
                        cn_params
                    )
                elif model_name == "seedream":
                    result = await self._generate_with_seedream(
                        optimized_prompt,
                        reference_image
                    )
                elif model_name == "nano_banana":
                    result = await self._generate_with_nano_banana(
                        optimized_prompt,
                        reference_image
                    )
                else:
                    continue

                generation_time = asyncio.get_event_loop().time() - start_time
                result.generation_time = generation_time
                result.model_used = model_name

                # 품질 평가
                result.confidence_score = await self._evaluate_consistency(
                    result.image_bytes,
                    reference_image
                )

                if result.confidence_score >= 0.7:
                    logger.info(f"Generated with {model_name}, confidence: {result.confidence_score}")
                    return result

            except Exception as e:
                last_error = e
                logger.warning(f"Failed with {model_name}: {str(e)}")
                continue

        # 모든 모델 실패 시
        logger.error(f"All models failed. Last error: {last_error}")
        return GenerationResult(success=False, last_error=str(last_error))

    def _optimize_prompt_for_consistency(self, prompt: str, reference_image: bytes) -> str:
        """일관성을 위한 프롬프트 최적화"""
        # 참조 이미지의 주요 특징 추출 (Vision AI 활용)
        # 실제 구현 시에는 Vision API를 통해 색상, 형태 등 추출
        # 여기서는 단순화된 로직
        return f"""
        {prompt}

        Style guide: Maintain the exact silhouette, proportions, and key design elements from the reference.
        Ensure consistent material representation and color matching.
        """

    async def _generate_with_zimage(
        self, prompt: str, reference: bytes, cn_params: Dict
    ) -> GenerationResult:
        """Z-Image로 생성 (IP-Adapter + ControlNet)"""
        # 실제 Z-Image API 호출 로직
        # 여기서는 시뮬레이션
        return GenerationResult(
            success=True,
            image_path="generated_zimage.png",
            image_bytes=b"generated_image_bytes",
            model_used="zimage"
        )

    async def _generate_with_seedream(
        self, prompt: str, reference: bytes
    ) -> GenerationResult:
        """Seedream으로 생성"""
        # 실제 Seedream API 호출 로직
        return GenerationResult(
            success=True,
            image_path="generated_seedream.png",
            image_bytes=b"generated_image_bytes",
            model_used="seedream"
        )

    async def _generate_with_nano_banana(
        self, prompt: str, reference: bytes
    ) -> GenerationResult:
        """Nano Banana로 생성"""
        # 실제 Nano Banana API 호출 로직
        return GenerationResult(
            success=True,
            image_path="generated_nano.png",
            image_bytes=b"generated_image_bytes",
            model_used="nano_banana"
        )

    async def _evaluate_consistency(
        self, generated_image: bytes, reference_image: bytes
    ) -> float:
        """생성된 이미지의 일관성 평가"""
        # 실제로는 Vision API (Gemini 등)를 사용
        # 여기서는 시뮬레이션된 점수
        import random
        return random.uniform(0.6, 0.95)


class MasterDesignGenerator:
    """마스터 디자인 생성기"""

    def __init__(self):
        self.i2i_generator = I2IGenerator()

    async def generate_flat_lay(
        self,
        design_concept: Dict[str, Any],
        style: str = "studio photography"
    ) -> GenerationResult:
        """평면도(Flat Lay) 생성"""
        prompt = f"""
        Fashion design flat lay photography.
        {design_concept.get('description', '')}
        Style: {style}
        View: Top-down, centered
        Lighting: Soft, even
        Background: White
        """

        # I2I 없이 직접 생성 (마스터 디자인은 참조 없이 시작)
        available_models = get_available_image_models()

        # Z-Image가 없는 경우 체크
        if "zimage" not in available_models:
            logger.warning("Z-Image not available, using alternative model")

        # 실제 생성 로직 구현 필요
        return GenerationResult(
            success=True,
            image_path="master_design.png",
            image_bytes=b"master_design_bytes",
            model_used=available_models[0]
        )


class ConsistencyPipeline:
    """일관성 파이프라인 메인 클래스"""

    def __init__(self):
        self.reference_store = ReferenceImageStore()
        self.i2i_generator = I2IGenerator()
        self.master_generator = MasterDesignGenerator()
        self.logger = get_logger(__name__)

    async def generate_design_series(
        self, design_concept: Dict[str, Any]
    ) -> Dict[str, Any]:
        """디자인 시리즈 생성 (마스터 → 모델 → 도면)"""
        design_id = design_concept.get('id', 'default')

        try:
            # Step 1: 마스터 디자인 생성
            self.logger.info(f"Step 1: Generating master design for {design_id}")
            master_result = await self.master_generator.generate_flat_lay(
                design_concept,
                style="high fashion editorial"
            )

            if not master_result.success:
                raise Exception("Master design generation failed")

            # 마스터 디자인 저장
            master_ref_id = await self.reference_store.save(
                master_result.image_bytes,
                design_id,
                'master',
                {'concept': design_concept}
            )

            # Step 2: 모델 착장 생성
            self.logger.info("Step 2: Generating model fitting images")
            model_prompt = design_concept.get('model_prompt',
                f"Fashion model wearing the design in {design_concept.get('style', 'casual')} style")

            model_results = []
            num_variations = design_concept.get('num_variations', 3)

            for i in range(num_variations):
                pose_prompt = f"{model_prompt}, pose {i+1}, fashion photography"
                model_result = await self.i2i_generator.generate_with_reference(
                    pose_prompt,
                    master_result.image_bytes,
                    "model"
                )

                if model_result.success:
                    model_ref_id = await self.reference_store.save(
                        model_result.image_bytes,
                        design_id,
                        f'model_pose_{i+1}',
                        {'pose': i+1}
                    )
                    model_results.append({
                        'ref_id': model_ref_id,
                        'result': model_result
                    })

            # Step 3: 도면 생성
            self.logger.info("Step 3: Generating blueprint")
            blueprint_prompt = f"""
            Technical fashion blueprint.
            Based on the master design.
            Include measurements, seam lines, and construction details.
            Style: Technical drawing, black and white lines.
            """

            blueprint_result = await self.i2i_generator.generate_with_reference(
                blueprint_prompt,
                master_result.image_bytes,
                "blueprint"
            )

            blueprint_ref_id = None
            if blueprint_result.success:
                blueprint_ref_id = await self.reference_store.save(
                    blueprint_result.image_bytes,
                    design_id,
                    'blueprint',
                    {'size_standard': design_concept.get('size_standard', 'KS')}
                )

            # 결과 반환
            return {
                'design_id': design_id,
                'master_design': {
                    'ref_id': master_ref_id,
                    'result': master_result
                },
                'model_fittings': model_results,
                'blueprint': {
                    'ref_id': blueprint_ref_id,
                    'result': blueprint_result
                },
                'success': True
            }

        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}")
            return {
                'design_id': design_id,
                'success': False,
                'error': str(e)
            }