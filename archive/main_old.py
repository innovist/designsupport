"""
Main FastAPI application for Fashion Image Generation System
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import uvicorn
from pydantic import BaseModel, Field
import logging
import io
import base64
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

from app.core.config import get_config
from app.core.logging import get_logger
from app.models.base import Base
from app.models.user import User
from app.models.project import Project, Session, Version
from app.models.crawler import CrawlJob, RawData, Comment

# Services
from app.services.analysis_service import AnalysisService, get_analysis_service_dep
from app.services.prompt_service import PromptService, get_prompt_service_dep
from app.services.data_processor import DataProcessor
from app.services.image_generation_service import (
    ImageGenerationService,
    ImageGenerationRequest,
    ImageGenerationResult,
    get_image_generation_service_dep
)
from app.services.blueprint_service import (
    BlueprintService,
    BlueprintRequest,
    BlueprintResult,
    get_blueprint_service_dep
)

# Crawlers
from crawlers.crawler_service import CrawlerService
from crawlers.crawler_manager import CrawlerManager

# API Routes
from app.api.routes import router as api_router

# AI Clients
from ai_clients.gemini_client import GeminiClient, get_gemini_client_dep
from ai_clients.glm_client import GLMClient, get_glm_client_dep
from ai_clients.zimage_client import ZImageClient, get_zimage_client_dep
from ai_clients.seedream_client import SeedreamClient, get_seedream_client_dep
from ai_clients.nano_banana_client import NanoBananaClient, get_nano_banana_client_dep

logger = get_logger(__name__)
config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 초기화
    logger.info("Starting Fashion AI Generator...")

    # 여기에 필요한 초기화 로직 추가
    # 예: 데이터베이스 연결, 캐시 웜업 등

    yield

    # 종료 시 정리
    logger.info("Shutting down Fashion AI Generator...")


# Custom OpenAPI configuration
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Fashion AI Generator",
        version="1.0.0",
        description="""
        ## Fashion AI Generator API

        AI 기반 패션 트렌드 분석 및 이미지 생성 시스템

        ### 주요 기능
        - 패션 트렌드 분석 (다양한 소스 데이터 수집 및 AI 분석)
        - 패션 디자인 이미지 생성 (다중 AI 모델 지원)
        - 패턴/블루프린트 생성 (표준 치수 시스템 기반)
        - 데이터 수집 (다양한 패션 플랫폼 크롤링)

        ### 인증
        현재 개발 환경에서는 인증이 필요 없습니다.
        프로덕션 환경에서는 API 키 기반 인증이 구현될 예정입니다.

        ### 언어 지원
        - 한국어 (ko)
        - English (en)
        - 简体中文 (zh-CN)
        - 繁體中文 (zh-TW)

        ### API 버전
        - 현재 버전: v1
        - URL 형식: `/api/v1/{resource}`

        ### 사용 제한
        - 분당 100 요청
        - 일일 10,000 요청

        ### 지원 모델
        **이미지 생성:**
        - Z-Image: 전문 패션 이미지 생성
        - Seedream: 패션 컬렉션 생성
        - Nano Banana: 기술적 패션 스케치

        **텍스트 생성:**
        - Gemini 2.5 Flash: 다중모달 분석
        - GLM-4.7: 언어 모델 및 임베딩
        """,
        routes=[
            {
                "name": "Projects",
                "description": "프로젝트 관리 API"
            },
            {
                "name": "Sessions",
                "description": "세션/파이프라인 실행 관리 API"
            },
            {
                "name": "Trend Analysis",
                "description": "패션 트렌드 분석 관련 API"
            },
            {
                "name": "Image Generation",
                "description": "패션 이미지 생성 관련 API"
            },
            {
                "name": "Blueprint",
                "description": "패턴/블루프린트 생성 관련 API"
            },
            {
                "name": "Crawler",
                "description": "데이터 수집 관련 API"
            },
            {
                "name": "Models",
                "description": "사용 가능한 모델 정보 API"
            }
        ],
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "개발 환경"
            },
            {
                "url": "https://api.fashion-ai.com",
                "description": "프로덕션 환경"
            }
        ],
        contact={
            "name": "Fashion AI Generator Team",
            "email": "support@fashion-ai.com"
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        }
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="Fashion AI Generator",
    description="AI-powered fashion trend analysis and image generation system",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

# API 라우터 등록 (프로젝트/세션 관리 포함)
app.include_router(api_router, prefix="/api/v1")


# Health Check
@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# Root
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Welcome to Fashion AI Generator API",
        "docs": "/docs",
        "health": "/health"
    }


# ===== Trend Analysis Endpoints =====

@app.post("/api/v1/analysis/analyze-trends")
async def analyze_trends(
    keywords: List[str],
    time_range: Optional[str] = "7d",
    analysis_service: AnalysisService = Depends(get_analysis_service_dep)
):
    """
    패션 트렌드 분석

    Args:
        keywords: 분석할 키워드 목록
        time_range: 분석 기간 (1d, 7d, 30d)
        analysis_service: 분석 서비스
    """
    try:
        result = await analysis_service.analyze_trends(
            keywords=keywords,
            time_range=time_range
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Trend analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analysis/analyze-image")
async def analyze_fashion_image(
    image: UploadFile = File(...),
    gemini_client: GeminiClient = Depends(get_gemini_client_dep)
):
    """
    패션 이미지 분석

    Args:
        image: 분석할 이미지 파일
        gemini_client: Gemini 클라이언트
    """
    try:
        # 이미지 읽기
        image_data = await image.read()

        # 이미지 임시 저장
        image_path = f"/tmp/{image.filename}"
        with open(image_path, "wb") as f:
            f.write(image_data)

        # Gemini로 이미지 분석
        prompt = """
        Analyze this fashion image and provide:
        1. Style category (e.g., casual, formal, streetwear)
        2. Color palette
        3. Key garments and accessories
        4. Pattern and texture details
        5. Overall aesthetic description
        6. Similar trending styles
        """

        response = await gemini_client.generate_with_image(
            prompt=prompt,
            image_path=image_path
        )

        return {
            "success": True,
            "analysis": response.text
        }
    except Exception as e:
        logger.error(f"Image analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Image Generation Endpoints =====

@app.post("/api/v1/generation/fashion-design")
async def generate_fashion_design(
    request: Dict[str, Any],
    image_service: ImageGenerationService = Depends(get_image_generation_service_dep)
):
    """
    패션 디자인 이미지 생성

    Args:
        request: 생성 요청 데이터
        image_service: 이미지 생성 서비스
    """
    try:
        # 요청 데이터 변환
        gen_request = ImageGenerationRequest(
            prompt=request.get("prompt", ""),
            style=request.get("style", "modern"),
            garment_type=request.get("garment_type", "dress"),
            color_scheme=request.get("color_scheme"),
            fabric_type=request.get("fabric_type"),
            num_variations=request.get("num_variations", 1),
            width=request.get("width", 1024),
            height=request.get("height", 1024),
            quality=request.get("quality", "high"),
            model_preference=request.get("model_preference")
        )

        # 참조 이미지 처리
        if "reference_image_url" in request:
            # URL에서 이미지 가져오기 로직
            pass

        result = await image_service.generate_fashion_design(gen_request)

        # 이미지를 base64로 변환
        images_base64 = []
        for img in result.images:
            img_base64 = base64.b64encode(img).decode('utf-8')
            images_base64.append(img_base64)

        variations_base64 = []
        if result.variations:
            for img in result.variations:
                img_base64 = base64.b64encode(img).decode('utf-8')
                variations_base64.append(img_base64)

        return {
            "success": True,
            "images": images_base64,
            "variations": variations_base64,
            "model_used": result.model_used,
            "generation_time": result.generation_time,
            "metadata": result.metadata
        }
    except Exception as e:
        logger.error(f"Fashion design generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/generation/collection")
async def generate_fashion_collection(
    request: Dict[str, Any],
    image_service: ImageGenerationService = Depends(get_image_generation_service_dep)
):
    """
    패션 컬렉션 생성

    Args:
        request: 생성 요청 데이터
        image_service: 이미지 생성 서비스
    """
    try:
        theme = request.get("theme", "")
        garments = request.get("garments", [])
        style = request.get("style", "modern")
        color_palette = request.get("color_palette")

        results = await image_service.generate_fashion_collection(
            theme=theme,
            garments=garments,
            style=style,
            color_palette=color_palette
        )

        # 결과 변환
        collection_data = []
        for result in results:
            images_base64 = [base64.b64encode(img).decode('utf-8') for img in result.images]
            collection_data.append({
                "images": images_base64,
                "garment": result.metadata.get("garment"),
                "model_used": result.model_used,
                "generation_time": result.generation_time
            })

        return {
            "success": True,
            "theme": theme,
            "collection": collection_data
        }
    except Exception as e:
        logger.error(f"Collection generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/generation/technical-sketch")
async def generate_technical_sketch(
    request: Dict[str, Any],
    image_service: ImageGenerationService = Depends(get_image_generation_service_dep)
):
    """
    기술적 스케치 생성

    Args:
        request: 생성 요청 데이터
        image_service: 이미지 생성 서비스
    """
    try:
        design_description = request.get("design_description", "")
        garment_type = request.get("garment_type", "dress")
        include_measurements = request.get("include_measurements", False)

        result = await image_service.generate_technical_sketch(
            design_description=design_description,
            garment_type=garment_type,
            include_measurements=include_measurements
        )

        # 이미지를 base64로 변환
        image_base64 = base64.b64encode(result.images[0]).decode('utf-8')

        return {
            "success": True,
            "image": image_base64,
            "model_used": result.model_used,
            "generation_time": result.generation_time,
            "metadata": result.metadata
        }
    except Exception as e:
        logger.error(f"Technical sketch generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Blueprint Generation Endpoints =====

@app.post("/api/v1/blueprint/generate")
async def generate_blueprint(
    request: Dict[str, Any],
    blueprint_service: BlueprintService = Depends(get_blueprint_service_dep)
):
    """
    패턴 블루프린트 생성

    Args:
        request: 생성 요청 데이터
        blueprint_service: 블루프린트 서비스
    """
    try:
        # 요청 데이터 변환
        bp_request = BlueprintRequest(
            garment_type=request.get("garment_type", "dress"),
            design_description=request.get("design_description", ""),
            size_system=request.get("size_system", "KS"),
            size=request.get("size", "M"),
            measurements=request.get("measurements"),
            include_instructions=request.get("include_instructions", True),
            include_seam_allowance=request.get("include_seam_allowance", True),
            seam_allowance_width=request.get("seam_allowance_width", 1.5),
            output_format=request.get("output_format", "image")
        )

        result = await blueprint_service.generate_blueprint(bp_request)

        # 이미지들을 base64로 변환
        pattern_pieces = []
        for piece in result.pattern_pieces:
            piece_image = base64.b64encode(piece.image).decode('utf-8')
            pattern_pieces.append({
                "name": piece.name,
                "image": piece_image,
                "width": piece.width,
                "height": piece.height,
                "piece_count": piece.piece_count,
                "instructions": piece.instructions
            })

        layout_diagram = base64.b64encode(result.layout_diagram).decode('utf-8')

        return {
            "success": True,
            "pattern_pieces": pattern_pieces,
            "layout_diagram": layout_diagram,
            "instructions": result.instructions,
            "material_requirements": result.material_requirements,
            "metadata": result.metadata
        }
    except Exception as e:
        logger.error(f"Blueprint generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/blueprint/export/{blueprint_id}")
async def export_blueprint_pdf(
    blueprint_id: str,
    blueprint_service: BlueprintService = Depends(get_blueprint_service_dep)
):
    """
    블루프린트 PDF 내보내기

    Args:
        blueprint_id: 블루프린트 ID
        blueprint_service: 블루프린트 서비스
    """
    try:
        # 여기서는 blueprint_id를 사용하여 저장된 블루프린트를 가져와야 함
        # 현재는 예시로 기능만 구현

        output_path = f"/tmp/blueprint_{blueprint_id}.pdf"

        # PDF 생성 로직 호출
        # await blueprint_service.export_pattern_pdf(blueprint, output_path)

        return {
            "success": True,
            "download_url": f"/api/v1/downloads/blueprint_{blueprint_id}.pdf"
        }
    except Exception as e:
        logger.error(f"PDF export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Crawler Endpoints =====

@app.post("/api/v1/crawler/start")
async def start_crawling(
    request: Dict[str, Any],
    crawler_service: CrawlerService = Depends(CrawlerService)
):
    """
    크롤링 시작

    Args:
        request: 크롤링 요청 데이터
        crawler_service: 크롤러 서비스
    """
    try:
        sources = request.get("sources", ["fashion_news", "instagram", "musinsa"])
        keywords = request.get("keywords", [])
        max_items = request.get("max_items", 100)

        # 크롤링 시작
        job_id = await crawler_service.start_crawling(
            sources=sources,
            keywords=keywords,
            max_items=max_items
        )

        return {
            "success": True,
            "job_id": job_id,
            "message": "Crawling started successfully"
        }
    except Exception as e:
        logger.error(f"Crawling start failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/crawler/status/{job_id}")
async def get_crawling_status(
    job_id: str,
    crawler_service: CrawlerService = Depends(CrawlerService)
):
    """
    크롤링 상태 조회

    Args:
        job_id: 크롤링 작업 ID
        crawler_service: 크롤러 서비스
    """
    try:
        status = await crawler_service.get_job_status(job_id)
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/crawler/results/{job_id}")
async def get_crawling_results(
    job_id: str,
    crawler_service: CrawlerService = Depends(CrawlerService)
):
    """
    크롤링 결과 조회

    Args:
        job_id: 크롤링 작업 ID
        crawler_service: 크롤러 서비스
    """
    try:
        results = await crawler_service.get_job_results(job_id)
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        logger.error(f"Results retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Model Info Endpoints =====

@app.get("/api/v1/models/image-generation")
async def get_image_generation_models():
    """사용 가능한 이미지 생성 모델 목록"""
    return {
        "success": True,
        "models": [
            {
                "name": "zimage",
                "display_name": "Z-Image",
                "capabilities": ["fashion_design", "model_fitting", "upscale"],
                "description": "Professional fashion image generation"
            },
            {
                "name": "seedream",
                "display_name": "Seedream (Bytedance)",
                "capabilities": ["fashion_collection", "patterns", "textures"],
                "description": "Advanced fashion collection generation"
            },
            {
                "name": "nano_banana",
                "display_name": "Nano Banana",
                "capabilities": ["sketch", "flat_lay", "fabric_simulation"],
                "description": "Technical fashion illustrations"
            }
        ]
    }


@app.get("/api/v1/models/text-generation")
async def get_text_generation_models():
    """사용 가능한 텍스트 생성 모델 목록"""
    return {
        "success": True,
        "models": [
            {
                "name": "gemini-2.5-flash",
                "display_name": "Gemini 2.5 Flash",
                "capabilities": ["text", "multimodal", "analysis"],
                "description": "Google's latest multimodal model"
            },
            {
                "name": "glm-4.7",
                "display_name": "GLM-4.7",
                "capabilities": ["text", "embedding"],
                "description": "Zhipu AI's powerful language model"
            }
        ]
    }


# ===== Error Handlers =====

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404 에러 핸들러"""
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """500 에러 핸들러"""
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )


# ===== Development Server =====

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.get("HOST", "0.0.0.0"),
        port=config.get("PORT", 8000),
        reload=config.get("DEBUG", False),
        log_level="info"
    )