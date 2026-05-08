"""
Blueprint and pattern generation service for fashion designs
"""

# @MX:NOTE: [AUTO] Blueprint generation service - pattern creation and export
# Maintains 22 methods for garment pattern generation, layout, and PDF export

import io
import json
import math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from app.core.config import get_config
from app.core.logging import get_logger
from app.core.settings_storage import get_gemini_model
from ai_clients.gemini_client import get_gemini_client
from ai_clients.seedream_client import get_seedream_client
from ai_clients.nano_banana_client import get_nano_banana_client
from app.services.image_generation_service import get_image_generation_service

logger = get_logger(__name__)
config = get_config()


@dataclass
class Measurement:
    """치수 정보"""
    name: str
    value: float
    unit: str
    description: Optional[str] = None


@dataclass
class PatternPiece:
    """패턴 조각"""
    name: str
    image: bytes  # 패턴 이미지
    width: float
    height: float
    measurements: List[Measurement]
    instructions: str
    piece_count: int = 1


@dataclass
class BlueprintRequest:
    """블루프린트 생성 요청"""
    garment_type: str
    design_description: str
    size_system: str = "KS"  # KS, GB, ASTM, ISO
    size: str = "M"
    measurements: Optional[Dict[str, float]] = None
    include_instructions: bool = True
    include_seam_allowance: bool = True
    seam_allowance_width: float = 1.5  # cm
    output_format: str = "image"  # image, pdf, both


@dataclass
class BlueprintImage:
    """블루프린트 이미지 정보"""
    type: str  # 'sketch', 'layout', 'pattern'
    image_bytes: bytes
    url: Optional[str] = None
    resolution: str = "1024x1024"
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BlueprintResult:
    """블루프린트 생성 결과"""
    pattern_pieces: List[PatternPiece]
    layout_diagram: bytes
    instructions: str
    material_requirements: Dict[str, Any]
    metadata: Dict[str, Any]
    # 3종 블루프린트 (신규)
    sketch: Optional[BlueprintImage] = None
    layout_drawing: Optional[BlueprintImage] = None
    pattern_draft: Optional[BlueprintImage] = None


class BlueprintService:
    """블루프린트 생성 서비스"""

    def __init__(self):
        """초기화"""
        self.gemini_client = get_gemini_client()
        self.seedream_client = get_seedream_client()
        self.nano_banana_client = get_nano_banana_client()
        self.image_service = get_image_generation_service()

        # 표준 치수 시스템
        self.size_systems = {
            "KS": {
                "M": {
                    "bust": 92, "waist": 76, "hip": 98, "shoulder": 42,
                    "arm_length": 58, "back_length": 41, "inseam": 76
                },
                "L": {
                    "bust": 96, "waist": 80, "hip": 102, "shoulder": 44,
                    "arm_length": 60, "back_length": 42, "inseam": 78
                }
            },
            "GB": {
                "M": {
                    "bust": 91, "waist": 75, "hip": 97, "shoulder": 41,
                    "arm_length": 57, "back_length": 40, "inseam": 75
                }
            },
            "ASTM": {
                "M": {
                    "bust": 94, "waist": 78, "hip": 100, "shoulder": 43,
                    "arm_length": 59, "back_length": 41.5, "inseam": 77
                }
            },
            "ISO": {
                    "M": {
                    "bust": 90, "waist": 74, "hip": 96, "shoulder": 40.5,
                    "arm_length": 56.5, "back_length": 39.5, "inseam": 74
                }
            }
        }

    async def generate_blueprint(
        self,
        request: BlueprintRequest
    ) -> BlueprintResult:
        """
        패턴 블루프린트 생성

        Args:
            request: 블루프린트 생성 요청

        Returns:
            생성된 블루프린트 결과
        """
        # 1. 기본 치수 가져오기
        base_measurements = self._get_base_measurements(
            request.size_system,
            request.size
        )

        # 사용자 제공 치수로 업데이트
        if request.measurements:
            base_measurements.update(request.measurements)

        # 2. 패턴 조각 분석 및 생성 계획
        pattern_plan = await self._analyze_pattern_pieces(
            request.garment_type,
            request.design_description,
            base_measurements
        )

        # 3. 패턴 조각 생성
        pattern_pieces = []
        for piece_info in pattern_plan:
            piece = await self._generate_pattern_piece(
                piece_info,
                base_measurements,
                request.include_seam_allowance,
                request.seam_allowance_width
            )
            pattern_pieces.append(piece)

        # 4. 레이아웃 다이어그램 생성
        layout_diagram = await self._generate_layout_diagram(
            pattern_pieces,
            request.garment_type
        )

        # 5. 재료 소요량 계산
        material_requirements = await self._calculate_material_requirements(
            pattern_pieces,
            request.garment_type
        )

        # 6. 제작 지시문 생성
        instructions = ""
        if request.include_instructions:
            instructions = await self._generate_instructions(
                request.garment_type,
                pattern_pieces,
                request.design_description
            )

        metadata = {
            "garment_type": request.garment_type,
            "size_system": request.size_system,
            "size": request.size,
            "measurements": base_measurements,
            "created_at": datetime.now().isoformat()
        }

        return BlueprintResult(
            pattern_pieces=pattern_pieces,
            layout_diagram=layout_diagram,
            instructions=instructions,
            material_requirements=material_requirements,
            metadata=metadata
        )

    def _get_base_measurements(
        self,
        size_system: str,
        size: str
    ) -> Dict[str, float]:
        """기본 치수 가져오기"""

        if size_system not in self.size_systems:
            raise ValueError(f"Unsupported size system: {size_system}")

        if size not in self.size_systems[size_system]:
            raise ValueError(f"Size {size} not found in {size_system}")

        return self.size_systems[size_system][size].copy()

    async def _analyze_pattern_pieces(
        self,
        garment_type: str,
        design_description: str,
        measurements: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """패턴 조각 분석 및 생성 계획"""

        # Gemini를 사용한 패턴 조각 분석
        analysis_prompt = f"""
        Analyze and list the pattern pieces needed for a {garment_type} with this design:

        Design: {design_description}
        Measurements: {measurements}

        For each pattern piece, provide:
        1. Piece name (e.g., Front Bodice, Back Bodice, Sleeve)
        2. Approximate width and height in cm
        3. Key measurements needed
        4. Number of pieces to cut
        5. Special features (e.g., dart, pleat, gathers)

        Format as JSON array of objects.
        """

        try:
            response = await self.gemini_client.generate_content(
                analysis_prompt,
                model=get_gemini_model()
            )

            # JSON 파싱
            import re
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                pieces_info = json.loads(json_match.group())
            else:
                # 기본 패턴 조각으로 폴백
                pieces_info = self._get_default_pattern_pieces(garment_type)

            return pieces_info

        except Exception as e:
            logger.warning(f"Pattern analysis failed: {str(e)}")
            return self._get_default_pattern_pieces(garment_type)

    def _get_default_pattern_pieces(self, garment_type: str) -> List[Dict[str, Any]]:
        """기본 패턴 조각 목록"""

        default_pieces = {
            "dress": [
                {
                    "name": "Front Bodice",
                    "width": 50,
                    "height": 60,
                    "measurements": ["bust", "waist", "shoulder"],
                    "piece_count": 1,
                    "features": ["dart"]
                },
                {
                    "name": "Back Bodice",
                    "width": 50,
                    "height": 60,
                    "measurements": ["bust", "waist", "back_length"],
                    "piece_count": 1,
                    "features": ["dart"]
                },
                {
                    "name": "Sleeve",
                    "width": 40,
                    "height": 60,
                    "measurements": ["arm_length", "bust"],
                    "piece_count": 2,
                    "features": []
                },
                {
                    "name": "Front Skirt",
                    "width": 50,
                    "height": 70,
                    "measurements": ["waist", "hip"],
                    "piece_count": 1,
                    "features": ["dart"]
                },
                {
                    "name": "Back Skirt",
                    "width": 50,
                    "height": 70,
                    "measurements": ["waist", "hip"],
                    "piece_count": 2,
                    "features": ["dart"]
                }
            ],
            "shirt": [
                {
                    "name": "Front Bodice",
                    "width": 50,
                    "height": 70,
                    "measurements": ["bust", "waist", "shoulder"],
                    "piece_count": 1,
                    "features": ["placket", "dart"]
                },
                {
                    "name": "Back Bodice",
                    "width": 50,
                    "height": 70,
                    "measurements": ["bust", "waist", "back_length"],
                    "piece_count": 1,
                    "features": ["pleat", "dart"]
                },
                {
                    "name": "Sleeve",
                    "width": 40,
                    "height": 60,
                    "measurements": ["arm_length", "bust"],
                    "piece_count": 2,
                    "features": ["placket", "cuff"]
                },
                {
                    "name": "Collar",
                    "width": 40,
                    "height": 15,
                    "measurements": ["neck"],
                    "piece_count": 2,
                    "features": []
                }
            ]
        }

        return default_pieces.get(garment_type, [])

    async def _generate_pattern_piece(
        self,
        piece_info: Dict[str, Any],
        measurements: Dict[str, float],
        include_seam_allowance: bool,
        seam_allowance_width: float
    ) -> PatternPiece:
        """개별 패턴 조각 생성"""

        # 1. 패턴 이미지 생성
        pattern_image = await self._generate_pattern_image(
            piece_info,
            measurements,
            include_seam_allowance,
            seam_allowance_width
        )

        # 2. 치수 라벨 생성
        measurements_list = []
        for meas_name in piece_info["measurements"]:
            if meas_name in measurements:
                measurements_list.append(
                    Measurement(
                        name=meas_name,
                        value=measurements[meas_name],
                        unit="cm",
                        description=f"Pattern {meas_name} measurement"
                    )
                )

        # 3. 제작 지시문 생성
        instructions = await self._generate_piece_instructions(
            piece_info,
            measurements
        )

        return PatternPiece(
            name=piece_info["name"],
            image=pattern_image,
            width=piece_info["width"],
            height=piece_info["height"],
            measurements=measurements_list,
            instructions=instructions,
            piece_count=piece_info.get("piece_count", 1)
        )

    async def _generate_pattern_image(
        self,
        piece_info: Dict[str, Any],
        measurements: Dict[str, float],
        include_seam_allowance: bool,
        seam_allowance_width: float
    ) -> bytes:
        """패턴 이미지 생성"""

        # 실제 크기(단위: pixel) 계산 (1cm = 10 pixels)
        scale = 10
        width_px = int(piece_info["width"] * scale)
        height_px = int(piece_info["height"] * scale)

        # 시드림으로 패턴 이미지 생성
        prompt = f"""
        Technical flat pattern of {piece_info["name"]},
        {piece_info.get("features", "")} features,
        black lines on white background,
        measurements: {piece_info["measurements"]},
        professional pattern drafting,
        clean lines,
        {include_seam_allowance and "with seam allowance" or "without seam allowance"}
        """

        try:
            from ai_clients.seedream_client import SeedreamGenerationConfig

            config = SeedreamGenerationConfig(
                width=width_px,
                height=height_px,
                steps=30,
                guidance_scale=8.0,
                negative_prompt="color, shading, 3d, realistic, blurry"
            )

            response = await self.seedream_client.generate_image(
                prompt=prompt,
                config=config
            )

            if response.images:
                return response.images[0]

        except Exception as e:
            logger.warning(f"Pattern generation with Seedream failed: {str(e)}")

        # 폴백: 수동 패턴 생성
        return self._generate_fallback_pattern(piece_info, scale)

    def _generate_fallback_pattern(
        self,
        piece_info: Dict[str, Any],
        scale: int
    ) -> bytes:
        """폴백 패턴 이미지 생성"""

        width = int(piece_info["width"] * scale)
        height = int(piece_info["height"] * scale)

        # 흰색 배경 이미지
        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)

        # 기본 패턴 형태 그리기
        if "Bodice" in piece_info["name"]:
            # 보디스 패턴
            # 어깨 선
            draw.line([(0, 50), (width, 50)], fill='black', width=2)
            # 사이드 선
            draw.line([(width//2, 50), (width//2, height-20)], fill='black', width=2)
            # 하단 선
            draw.line([(0, height-20), (width, height-20)], fill='black', width=2)
            # 센터 라인
            draw.line([(width//2, 0), (width//2, height)], fill='black', width=1, dash=(5, 5))

        elif "Sleeve" in piece_info["name"]:
            # 소매 패턴 (삼각형)
            draw.polygon(
                [(width//2, 0), (0, height-20), (width, height-20)],
                outline='black',
                width=2
            )

        elif "Skirt" in piece_info["name"]:
            # 스커트 패턴 (사다리꼴)
            draw.polygon(
                [(width//3, 0), (2*width//3, 0), (width, height), (0, height)],
                outline='black',
                width=2
            )

        # 이미지를 바이트로 변환
        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)

        return output.read()

    async def _generate_piece_instructions(
        self,
        piece_info: Dict[str, Any],
        measurements: Dict[str, float]
    ) -> str:
        """패턴 조각별 제작 지시문 생성"""

        instruction_prompt = f"""
        Create sewing instructions for the {piece_info["name"]} pattern piece.

        Piece details: {piece_info}
        Measurements: {measurements}

        Include:
        1. Preparation steps
        2. Key points to mark
        3. Special techniques (darts, pleats, etc.)
        4. Assembly order
        5. Tips for best results

        Keep it clear and concise for a sewist.
        """

        try:
            response = await self.gemini_client.generate_content(
                instruction_prompt,
                model=get_gemini_model()
            )
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Instruction generation failed: {str(e)}")
            return f"Standard sewing instructions for {piece_info['name']}."

    async def _generate_layout_diagram(
        self,
        pattern_pieces: List[PatternPiece],
        garment_type: str
    ) -> bytes:
        """레이아웃 다이어그램 생성"""

        # 패턴 배치 최적화 계산
        total_width = sum(p.width for p in pattern_pieces) * 1.2  # 여백 포함
        max_height = max(p.height for p in pattern_pieces) * 1.2

        # 시드림으로 레이아웃 다이어그램 생성
        prompt = f"""
        Professional pattern layout diagram for {garment_type},
        {len(pattern_pieces)} pattern pieces arranged efficiently,
        black outlines on white background,
        pattern pieces labeled: {', '.join(p.name for p in pattern_pieces)},
        grain lines indicated,
        technical drawing style
        """

        try:
            from ai_clients.seedream_client import SeedreamGenerationConfig

            config = SeedreamGenerationConfig(
                width=int(total_width * 10),
                height=int(max_height * 10),
                steps=30,
                guidance_scale=7.5,
                negative_prompt="color, 3d, realistic, cluttered"
            )

            response = await self.seedream_client.generate_image(
                prompt=prompt,
                config=config
            )

            if response.images:
                return response.images[0]

        except Exception as e:
            logger.warning(f"Layout diagram generation failed: {str(e)}")

        # 폴백: 간단한 레이아웃 이미지
        return self._generate_fallback_layout(pattern_pieces, int(total_width * 5), int(max_height * 5))

    def _generate_fallback_layout(
        self,
        pattern_pieces: List[PatternPiece],
        width: int,
        height: int
    ) -> bytes:
        """폴백 레이아웃 이미지 생성"""

        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)

        # 간단한 패턴 배치
        x_offset = 50
        y_offset = 50

        for piece in pattern_pieces:
            piece_width = int(piece.width * 5)
            piece_height = int(piece.height * 5)

            # 패턴 조각 사각형 그리기
            draw.rectangle(
                [x_offset, y_offset, x_offset + piece_width, y_offset + piece_height],
                outline='black',
                width=2
            )

            # 라벨 추가
            try:
                font = ImageFont.load_default()
                draw.text(
                    (x_offset + 5, y_offset + 5),
                    piece.name,
                    fill='black',
                    font=font
                )
            except:
                pass

            # 다음 위치로 이동
            x_offset += piece_width + 50
            if x_offset + piece_width > width:
                x_offset = 50
                y_offset += piece_height + 50

        # 이미지를 바이트로 변환
        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)

        return output.read()

    async def _calculate_material_requirements(
        self,
        pattern_pieces: List[PatternPiece],
        garment_type: str
    ) -> Dict[str, Any]:
        """재료 소요량 계산"""

        # 총면적 계산
        total_area = sum(
            p.width * p.height * p.piece_count
            for p in pattern_pieces
        )  # cm²

        # 소요량 계산 (여백 및 손실 포함)
        fabric_width = 150  # cm (표준 패브릭 너비)
        fabric_length = (total_area / fabric_width) * 1.2  # 20% 여유
        fabric_length = math.ceil(fabric_length / 10) * 10  # 10cm 단위 반올림

        # 기타 재료
        other_materials = {
            "thread": {"amount": "1 spool", "unit": "spool"},
            "interfacing": {"amount": 50, "unit": "cm"},
            "buttons": {"amount": garment_type == "shirt" and 7 or 5, "unit": "pieces"},
            "zipper": {"amount": garment_type == "dress" and 1 or 0, "unit": "pieces"}
        }

        return {
            "fabric": {
                "width": fabric_width,
                "length": fabric_length,
                "area": fabric_width * fabric_length,
                "unit": "cm"
            },
            "other_materials": other_materials,
            "total_pieces": sum(p.piece_count for p in pattern_pieces)
        }

    async def _generate_instructions(
        self,
        garment_type: str,
        pattern_pieces: List[PatternPiece],
        design_description: str
    ) -> str:
        """전체 제작 지시문 생성"""

        instruction_prompt = f"""
        Create comprehensive sewing instructions for a {garment_type}.

        Design description: {design_description}
        Pattern pieces: {[p.name for p in pattern_pieces]}

        Include:
        1. Material preparation
        2. Pattern layout and cutting
        3. Step-by-step assembly order
        4. Finishing techniques
        5. Pressing instructions
        6. Tips for professional results

        Format as clear, numbered steps.
        """

        try:
            response = await self.gemini_client.generate_content(
                instruction_prompt,
                model=get_gemini_model()
            )
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Full instructions generation failed: {str(e)}")
            return f"Standard sewing instructions for {garment_type}."

    async def export_pattern_pdf(
        self,
        blueprint: BlueprintResult,
        output_path: str
    ) -> str:
        """패턴을 PDF로 내보내기"""

        try:
            # PDF 라이브러리 사용 (reportlab 또는 fpdf)
            from fpdf import FPDF
            import os
            import tempfile

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            # 제목
            pdf.cell(0, 10, f"Pattern: {blueprint.metadata['garment_type']}", ln=1)
            pdf.cell(0, 10, f"Size: {blueprint.metadata['size']} ({blueprint.metadata['size_system']})", ln=1)
            pdf.ln(10)

            # 각 패턴 조각
            for piece in blueprint.pattern_pieces:
                pdf.add_page()
                pdf.cell(0, 10, f"Pattern Piece: {piece.name}", ln=1)
                pdf.cell(0, 10, f"Cut {piece.piece_count} pieces", ln=1)
                pdf.ln(5)

                # 이미지 추가
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(piece.image)
                        tmp_path = tmp.name

                    pdf.image(tmp_path, x=10, y=50, w=180)
                except Exception:
                    pdf.cell(0, 10, "[Pattern image]", ln=1)
                finally:
                    if "tmp_path" in locals() and os.path.exists(tmp_path):
                        os.unlink(tmp_path)

                pdf.add_page()
                pdf.cell(0, 10, "Instructions:", ln=1)
                pdf.multi_cell(0, 10, piece.instructions)

            # 재료 목록
            pdf.add_page()
            pdf.cell(0, 10, "Material Requirements:", ln=1)
            pdf.cell(0, 10, f"Fabric: {blueprint.material_requirements['fabric']['length']}cm x {blueprint.material_requirements['fabric']['width']}cm", ln=1)

            # PDF 저장
            pdf.output(output_path)
            logger.info(f"Pattern saved to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"PDF export failed: {str(e)}")
            raise

    async def generate_three_blueprints(
        self,
        design_image: bytes,
        design_description: str,
        size_system: str = "KS",
        size: str = "M"
    ) -> Dict[str, BlueprintImage]:
        """
        3종 블루프린트 생성 (스케치, 레이아웃 도면, 패턴 제도도)

        Args:
            design_image: 마스터 디자인 이미지 바이트
            design_description: 디자인 설명
            size_system: 치수 시스템 (KS, GB, ASTM, ISO)
            size: 사이즈 (S, M, L, XL)

        Returns:
            3종 블루프린트 딕셔너리
        """
        results = {}

        # 1. 스케치 생성
        try:
            sketch = await self._generate_sketch(design_image, design_description)
            results["sketch"] = sketch
            logger.info("Sketch generated successfully")
        except Exception as e:
            logger.error(f"Sketch generation failed: {e}")
            results["sketch"] = None

        # 2. 레이아웃 도면 생성
        try:
            layout = await self._generate_layout_drawing(
                design_image, design_description
            )
            results["layout"] = layout
            logger.info("Layout drawing generated successfully")
        except Exception as e:
            logger.error(f"Layout drawing generation failed: {e}")
            results["layout"] = None

        # 3. 패턴 제도도 생성
        try:
            pattern = await self._generate_pattern_draft(
                design_image, design_description, size_system, size
            )
            results["pattern"] = pattern
            logger.info("Pattern draft generated successfully")
        except Exception as e:
            logger.error(f"Pattern draft generation failed: {e}")
            results["pattern"] = None

        return results

    async def _generate_sketch(
        self,
        design_image: bytes,
        design_description: str
    ) -> BlueprintImage:
        """패션 디자인 스케치 생성"""
        prompt = f"""
        Fashion design sketch illustration.
        {design_description}
        Hand-drawn style, fashion illustration,
        pencil and marker technique, dynamic pose hint,
        fabric texture indication, professional fashion sketch,
        white background, clean lines, artistic style.
        """

        try:
            from ai_clients.seedream_client import SeedreamGenerationConfig

            config = SeedreamGenerationConfig(
                width=1024,
                height=1024,
                steps=30,
                guidance_scale=7.5,
                negative_prompt="photo, realistic, 3d render, blurry"
            )

            response = await self.seedream_client.generate_image(
                prompt=prompt,
                config=config
            )

            if response.images:
                return BlueprintImage(
                    type="sketch",
                    image_bytes=response.images[0],
                    resolution="1024x1024",
                    metadata={"style": "fashion illustration"}
                )

        except Exception as e:
            logger.warning(f"Seedream sketch failed, trying Nano Banana: {e}")

        # 폴백: Nano Banana 시도
        try:
            result = await self.nano_banana_client.generate_fashion_sketch(
                design_description=design_description,
                sketch_style="fashion illustration"
            )
            if result.images:
                return BlueprintImage(
                    type="sketch",
                    image_bytes=result.images[0],
                    resolution="1024x1024",
                    metadata={"style": "fashion illustration"}
                )
        except Exception as e:
            logger.warning(f"Nano Banana sketch failed: {e}")

        raise ValueError("Sketch generation failed for both Seedream and Nano Banana")

    async def _generate_layout_drawing(
        self,
        design_image: bytes,
        design_description: str
    ) -> BlueprintImage:
        """레이아웃 도면(평면 전개도) 생성"""
        prompt = f"""
        Technical flat pattern layout drawing.
        {design_description}
        Flat lay technical drawing, front and back views,
        labeled parts, seam lines indicated,
        professional pattern drafting style,
        clean white background, CAD-like precision,
        black lines, technical illustration.
        """

        try:
            from ai_clients.seedream_client import SeedreamGenerationConfig

            config = SeedreamGenerationConfig(
                width=1024,
                height=1024,
                steps=35,
                guidance_scale=8.5,
                negative_prompt="color, shading, 3d, realistic, artistic"
            )

            response = await self.seedream_client.generate_image(
                prompt=prompt,
                config=config
            )

            if response.images:
                return BlueprintImage(
                    type="layout",
                    image_bytes=response.images[0],
                    resolution="1024x1024",
                    metadata={"views": ["front", "back"]}
                )

        except Exception as e:
            logger.warning(f"Seedream layout failed: {e}")

        # 폴백: Nano Banana 시도
        try:
            from ai_clients.nano_banana_client import NanoBananaGenerationConfig

            config = NanoBananaGenerationConfig(
                width=1024,
                height=1024,
                steps=30,
                guidance_scale=7.5
            )
            response = await self.nano_banana_client.generate_image(
                prompt=prompt,
                config=config
            )
            if response.images:
                return BlueprintImage(
                    type="layout",
                    image_bytes=response.images[0],
                    resolution="1024x1024",
                    metadata={"views": ["front", "back"]}
                )
        except Exception as e:
            logger.warning(f"Nano Banana layout failed: {e}")

        raise ValueError("Layout drawing generation failed for both Seedream and Nano Banana")

    async def _generate_pattern_draft(
        self,
        design_image: bytes,
        design_description: str,
        size_system: str,
        size: str
    ) -> BlueprintImage:
        """패턴 제도도 생성"""
        measurements = self._get_base_measurements(size_system, size)

        prompt = f"""
        Sewing pattern technical draft.
        {design_description}
        Pattern pieces with seam allowance,
        grain line arrows, notches marked,
        size {size} ({size_system} standard),
        measurement annotations, cutting instructions,
        professional pattern maker style,
        black lines on white background,
        technical precision, numbered pieces.
        """

        try:
            from ai_clients.seedream_client import SeedreamGenerationConfig

            config = SeedreamGenerationConfig(
                width=2048,
                height=2048,
                steps=40,
                guidance_scale=9.0,
                negative_prompt="color, shading, artistic, blurry"
            )

            response = await self.seedream_client.generate_image(
                prompt=prompt,
                config=config
            )

            if response.images:
                return BlueprintImage(
                    type="pattern",
                    image_bytes=response.images[0],
                    resolution="2048x2048",
                    metadata={
                        "size_system": size_system,
                        "size": size,
                        "measurements": measurements
                    }
                )

        except Exception as e:
            logger.warning(f"Seedream pattern failed: {e}")

        # 폴백: Nano Banana 시도
        try:
            from ai_clients.nano_banana_client import NanoBananaGenerationConfig

            config = NanoBananaGenerationConfig(
                width=2048,
                height=2048,
                steps=35,
                guidance_scale=8.0
            )
            response = await self.nano_banana_client.generate_image(
                prompt=prompt,
                config=config
            )
            if response.images:
                return BlueprintImage(
                    type="pattern",
                    image_bytes=response.images[0],
                    resolution="2048x2048",
                    metadata={
                        "size_system": size_system,
                        "size": size,
                        "measurements": measurements
                    }
                )
        except Exception as e:
            logger.warning(f"Nano Banana pattern failed: {e}")

        raise ValueError("Pattern draft generation failed for both Seedream and Nano Banana")

    def _create_placeholder_blueprint(
        self,
        bp_type: str,
        size_system: str = "KS",
        size: str = "M"
    ) -> BlueprintImage:
        """플레이스홀더 블루프린트 이미지 생성"""
        if bp_type == "pattern":
            width, height = 2048, 2048
        else:
            width, height = 1024, 1024

        img = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(img)

        # 타입별 기본 도형 그리기
        if bp_type == "sketch":
            # 간단한 드레스 스케치 형태
            center_x = width // 2
            draw.ellipse([center_x-50, 50, center_x+50, 150], outline='black', width=2)
            draw.polygon([
                (center_x-100, 150),
                (center_x+100, 150),
                (center_x+150, height-100),
                (center_x-150, height-100)
            ], outline='black', width=2)
            draw.text((50, 50), "Fashion Design Sketch", fill='gray')

        elif bp_type == "layout":
            # 전면/후면 레이아웃
            draw.rectangle([50, 50, width//2-25, height-50], outline='black', width=2)
            draw.rectangle([width//2+25, 50, width-50, height-50], outline='black', width=2)
            draw.text((width//4, height//2), "FRONT", fill='gray')
            draw.text((3*width//4, height//2), "BACK", fill='gray')

        elif bp_type == "pattern":
            # 패턴 조각들
            draw.rectangle([50, 50, width//3, height//2], outline='black', width=2)
            draw.rectangle([width//3+50, 50, 2*width//3, height//2], outline='black', width=2)
            draw.rectangle([2*width//3+50, 50, width-50, height//2], outline='black', width=2)
            draw.text((100, 100), f"Pattern - {size} ({size_system})", fill='gray')

        # 바이트로 변환
        output = io.BytesIO()
        img.save(output, format='PNG')
        output.seek(0)

        return BlueprintImage(
            type=bp_type,
            image_bytes=output.read(),
            resolution=f"{width}x{height}",
            metadata={"placeholder": True}
        )

    async def cleanup(self):
        """리소스 정리"""
        await self.gemini_client.cleanup()
        await self.seedream_client.cleanup()
        await self.nano_banana_client.cleanup()
        await self.image_service.cleanup()
        logger.info("Blueprint service cleaned up")


# 전역 서비스 인스턴스
_blueprint_service = None


def get_blueprint_service() -> BlueprintService:
    """블루프린트 서비스 인스턴스 가져오기"""
    global _blueprint_service
    if _blueprint_service is None:
        _blueprint_service = BlueprintService()
    return _blueprint_service


# FastAPI 의존성 주입용
async def get_blueprint_service_dep():
    """FastAPI 의존성 주입용 블루프린트 서비스"""
    service = get_blueprint_service()
    try:
        yield service
    finally:
        await service.cleanup()
