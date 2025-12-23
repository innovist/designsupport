"""
Service unit tests (no external API calls)
"""

import asyncio

import pytest

from app.services.analysis_service import AnalysisService
from app.services.image_generation_service import ImageGenerationService
from app.services.blueprint_service import BlueprintService, PatternPiece


class TestAnalysisService:
    """Analysis service tests (local logic only)"""

    @pytest.fixture
    def analysis_service(self):
        return AnalysisService()

    @pytest.mark.asyncio
    async def test_preprocess_requires_data(self, analysis_service):
        """Empty input should fail fast"""
        with pytest.raises(ValueError):
            await analysis_service._preprocess_data_flexible([], {}, "")

    @pytest.mark.asyncio
    async def test_preprocess_and_extract_keywords(self, analysis_service):
        """Preprocess data and extract keywords from tags/content"""
        raw_data = [
            {
                "title": "Spring Fashion Trends",
                "content": "Minimalist silhouettes and linen fabrics are trending strongly this season.",
                "source": "fashion_news",
                "keywords": ["minimalist", "linen", "spring"]
            }
        ]

        processed = await analysis_service._preprocess_data_flexible(
            raw_data=raw_data,
            filters={"season": "spring"},
            user_input="spring fashion"
        )

        keywords = analysis_service._extract_keywords(processed)
        assert "minimalist" in keywords
        assert "linen" in keywords

    @pytest.mark.asyncio
    async def test_generate_design_concepts(self, analysis_service):
        """Generate concepts from synthesis data"""
        analysis_result = {
            "synthesis": {
                "concepts": [
                    {
                        "concept_name": "Sustainable Minimal",
                        "design_approach": "clean lines",
                        "key_elements": ["linen", "cotton"],
                        "differentiators": ["zero waste"],
                        "commercial_feasibility": "high",
                        "market_opportunity": "medium"
                    },
                    {
                        "concept_name": "Tech Utility",
                        "design_approach": "modular silhouettes",
                        "key_elements": ["nylon"],
                        "differentiators": ["convertible"],
                        "commercial_feasibility": "medium",
                        "market_opportunity": "high"
                    }
                ]
            }
        }

        concepts = await analysis_service.generate_design_concepts(
            analysis_result=analysis_result,
            num_concepts=2
        )

        assert len(concepts) == 2
        assert concepts[0]["concept_name"] == "Sustainable Minimal"
        assert "prompt" in concepts[0]


class TestImageGenerationService:
    """Image generation service tests (local logic only)"""

    @pytest.fixture
    def image_service(self):
        return ImageGenerationService()

    def test_select_models(self, image_service):
        models = image_service._select_models(task_type="fashion_design")
        assert models[0] == "zimage"
        assert "seedream" in models
        assert "nano_banana" in models

    def test_post_process_image(self, image_service):
        from PIL import Image
        import io
        import numpy as np

        img_array = np.zeros((100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        image_data = img_bytes.getvalue()

        processed = asyncio.run(image_service._post_process_image(image_data))
        assert processed


class TestBlueprintService:
    """Blueprint service tests (local logic only)"""

    @pytest.fixture
    def blueprint_service(self):
        return BlueprintService()

    def test_get_base_measurements(self, blueprint_service):
        measurements = blueprint_service._get_base_measurements("KS", "M")
        assert measurements["bust"] == 92
        assert measurements["waist"] == 76

    @pytest.mark.asyncio
    async def test_calculate_material_requirements(self, blueprint_service):
        pattern_pieces = [
            PatternPiece(
                name="Front",
                image=b"image",
                width=50,
                height=60,
                measurements=[],
                instructions="",
                piece_count=1
            ),
            PatternPiece(
                name="Back",
                image=b"image",
                width=50,
                height=60,
                measurements=[],
                instructions="",
                piece_count=2
            )
        ]

        requirements = await blueprint_service._calculate_material_requirements(
            pattern_pieces=pattern_pieces,
            garment_type="dress"
        )

        assert requirements["total_pieces"] == 3
        assert "fabric" in requirements
