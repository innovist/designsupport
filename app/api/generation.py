"""
Generation API endpoints for Fashion AI Generation System
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import base64
import io

import uuid
from app.services.image_generation_service import ImageGenerationService, ImageGenerationRequest
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Initialize generation service
image_service = ImageGenerationService()

# In-memory generation job store (use DB/Redis in production)
generation_jobs: Dict[str, Dict[str, Any]] = {}


class DesignGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Design description")
    garment_type: str = Field(default="dress", description="Type of garment")
    style: str = Field(default="modern", description="Style preference")
    color_scheme: Optional[str] = Field(None, description="Color scheme")
    fabric_type: Optional[str] = Field(None, description="Fabric type")
    quality: str = Field(default="high", description="Generation quality")
    num_variations: int = Field(default=1, ge=1, le=4, description="Number of variations")
    reference_image: Optional[str] = Field(None, description="Base64 encoded reference image")


class DesignGenerationResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    message: str
    estimated_time: Optional[int] = None  # in seconds
    data: Optional[Dict[str, Any]] = None


# @MX:ANCHOR: [AUTO] Fashion design generation API endpoint - core image generation interface
# @MX:REASON: Called from 5+ locations across frontend, workflow services, and test suites
@router.post("/fashion-design", response_model=DesignGenerationResponse)
async def generate_fashion_design(
    request: DesignGenerationRequest,
    background_tasks: BackgroundTasks
):
    """Generate fashion design images"""
    try:
        # Validate request
        if not request.prompt or len(request.prompt) < 10:
            raise HTTPException(
                status_code=400,
                detail="Design prompt must be at least 10 characters"
            )

        job_id = f"design_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        generation_jobs[job_id] = {
            "status": "processing",
            "progress": 0,
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None
        }

        # Estimate generation time based on quality and variations
        base_time = 30 if request.quality == "high" else 20
        estimated_time = base_time * request.num_variations

        reference_image = request.reference_image
        if isinstance(reference_image, str) and reference_image:
            try:
                reference_image = base64.b64decode(reference_image)
            except Exception as e:
                raise HTTPException(status_code=400, detail="Invalid reference image data") from e

        gen_request = ImageGenerationRequest(
            prompt=request.prompt,
            garment_type=request.garment_type,
            style=request.style,
            color_scheme=request.color_scheme,
            fabric_type=request.fabric_type,
            reference_image=reference_image,
            quality=request.quality,
            num_variations=request.num_variations
        )

        try:
            result = await image_service.generate_fashion_design(gen_request)
        except Exception as e:
            generation_jobs[job_id]["status"] = "failed"
            generation_jobs[job_id]["error"] = str(e)
            logger.error(f"Design generation failed: {e}")
            raise

        images_base64 = [base64.b64encode(img).decode('utf-8') for img in result.images]
        variations_base64 = None
        if result.variations:
            variations_base64 = [base64.b64encode(img).decode('utf-8') for img in result.variations]

        payload = {
            "images": images_base64,
            "variations": variations_base64,
            "model_used": result.model_used,
            "generation_time": result.generation_time,
            "metadata": result.metadata
        }

        generation_jobs[job_id]["status"] = "completed"
        generation_jobs[job_id]["progress"] = 100
        generation_jobs[job_id]["result"] = payload

        return DesignGenerationResponse(
            success=True,
            session_id=job_id,
            message="Design generation completed",
            estimated_time=estimated_time,
            data=payload
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start design generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fashion-design-with-reference")
async def generate_design_with_reference(
    prompt: str,
    garment_type: str = "dress",
    style: str = "modern",
    quality: str = "high",
    file: UploadFile = File(...)
):
    """Generate fashion design with reference image"""
    try:
        # Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )

        # Read and encode image
        image_data = await file.read()
        base64_image = base64.b64encode(image_data).decode()

        # Create request with reference
        request = DesignGenerationRequest(
            prompt=prompt,
            garment_type=garment_type,
            style=style,
            quality=quality,
            reference_image=base64_image
        )

        return await generate_fashion_design(request, BackgroundTasks())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process reference image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generation-status/{design_id}")
async def get_generation_status(design_id: str):
    """Get generation status for a design"""
    try:
        job = generation_jobs.get(design_id)
        if not job:
            return {
                "success": True,
                "status": "not_found",
                "message": "Design not found or not started"
            }

        return {
            "success": True,
            "design_id": design_id,
            "status": job["status"],
            "progress": job.get("progress", 0),
            "error": job.get("error")
        }

    except Exception as e:
        logger.error(f"Failed to get generation status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/design-results/{design_id}")
async def get_design_results(design_id: str):
    """Get completed design results"""
    try:
        job = generation_jobs.get(design_id)
        if not job:
            raise HTTPException(status_code=404, detail="Design not found")

        if job["status"] != "completed":
            return {
                "success": False,
                "message": "Design not completed yet",
                "status": job["status"],
                "progress": job.get("progress", 0)
            }

        return {
            "success": True,
            "results": job.get("result")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get design results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{design_id}/{stage}")
async def download_design_image(design_id: str, stage: str):
    """Download design image"""
    try:
        job = generation_jobs.get(design_id)
        if not job or job["status"] != "completed":
            raise HTTPException(status_code=404, detail="Design not found or not completed")

        result = job.get("result") or {}
        images = result.get("images", [])
        if not images:
            raise HTTPException(status_code=404, detail="No images available")

        image_index = 0
        if stage.isdigit():
            image_index = min(int(stage), len(images) - 1)

        image_bytes = base64.b64decode(images[image_index])

        from fastapi.responses import Response
        return Response(
            content=image_bytes,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename={design_id}_{stage}.png"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download design: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Model Information Endpoints =====

@router.get("/models/image")
async def get_image_generation_models():
    """Get available image generation models"""
    return {
        "models": [
            {
                "id": "zimage",
                "name": "Z-Image",
                "description": "Professional fashion image generation",
                "capabilities": ["fashion_design", "model_fitting", "upscale"],
                "status": "available"
            },
            {
                "id": "seedream",
                "name": "Seedream (Bytedance)",
                "description": "Advanced fashion collection generation",
                "capabilities": ["fashion_collection", "patterns", "textures"],
                "status": "available"
            },
            {
                "id": "nano_banana",
                "name": "Nano Banana",
                "description": "Technical fashion illustrations",
                "capabilities": ["sketch", "flat_lay", "fabric_simulation"],
                "status": "available"
            }
        ]
    }


@router.get("/models/text")
async def get_text_generation_models():
    """Get available text generation models"""
    return {
        "models": [
            {
                "id": "gemini",
                "name": "Gemini 2.5 Flash",
                "description": "Google's latest multimodal model",
                "capabilities": ["text", "multimodal", "analysis"],
                "status": "available"
            },
            {
                "id": "glm",
                "name": "GLM-4.7",
                "description": "Zhipu AI's powerful language model",
                "capabilities": ["text", "embedding"],
                "status": "available"
            }
        ]
    }
