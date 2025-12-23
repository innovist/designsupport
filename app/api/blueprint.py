"""
Blueprint API endpoints for Fashion AI Generation System
Pattern generation and export functionality
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import base64
import uuid

from app.services.blueprint_service import (
    get_blueprint_service,
    BlueprintRequest,
    BlueprintResult
)
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# In-memory storage for blueprint jobs (use Redis/DB in production)
blueprint_jobs: Dict[str, Dict[str, Any]] = {}


class BlueprintGenerateRequest(BaseModel):
    garment_type: str = Field(..., description="Type of garment (dress, shirt, etc.)")
    design_description: str = Field(..., description="Design description")
    size_system: str = Field(default="KS", description="Size system: KS, GB, ASTM, ISO")
    size: str = Field(default="M", description="Size code")
    measurements: Optional[Dict[str, float]] = Field(None, description="Custom measurements")
    include_instructions: bool = Field(default=True)
    include_seam_allowance: bool = Field(default=True)
    seam_allowance_width: float = Field(default=1.5, description="Seam allowance in cm")
    output_format: str = Field(default="image", description="Output: image, pdf, both")


class BlueprintGenerateResponse(BaseModel):
    success: bool
    blueprint_id: Optional[str] = None
    message: str
    estimated_time: Optional[int] = None
    data: Optional[Dict[str, Any]] = None


@router.post("/generate", response_model=BlueprintGenerateResponse)
async def generate_blueprint(
    request: BlueprintGenerateRequest,
    background_tasks: BackgroundTasks
):
    """Generate pattern blueprint for a garment design"""
    try:
        blueprint_id = f"bp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Initialize job status
        blueprint_jobs[blueprint_id] = {
            "status": "processing",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "request": request.model_dump(),
            "result": None,
            "raw_result": None,
            "error": None
        }

        # Create service request
        service_request = BlueprintRequest(
            garment_type=request.garment_type,
            design_description=request.design_description,
            size_system=request.size_system,
            size=request.size,
            measurements=request.measurements,
            include_instructions=request.include_instructions,
            include_seam_allowance=request.include_seam_allowance,
            seam_allowance_width=request.seam_allowance_width,
            output_format=request.output_format
        )

        # Run generation synchronously for immediate results
        await _generate_blueprint_task(blueprint_id, service_request)

        # Estimate time based on complexity
        estimated_time = 30 if request.include_instructions else 20

        job = blueprint_jobs.get(blueprint_id, {})
        return BlueprintGenerateResponse(
            success=True,
            blueprint_id=blueprint_id,
            message="Blueprint generation completed",
            estimated_time=estimated_time,
            data=job.get("result")
        )

    except Exception as e:
        logger.error(f"Failed to start blueprint generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_blueprint_task(blueprint_id: str, request: BlueprintRequest):
    """Background task for blueprint generation"""
    try:
        service = get_blueprint_service()

        # Update progress
        blueprint_jobs[blueprint_id]["progress"] = 10

        # Generate blueprint
        result = await service.generate_blueprint(request)

        # Convert result to serializable format
        pattern_pieces_data = []
        for piece in result.pattern_pieces:
            piece_data = {
                "name": piece.name,
                "width": piece.width,
                "height": piece.height,
                "piece_count": piece.piece_count,
                "instructions": piece.instructions,
                "image": base64.b64encode(piece.image).decode() if piece.image else None,
                "measurements": [
                    {"name": m.name, "value": m.value, "unit": m.unit}
                    for m in piece.measurements
                ]
            }
            pattern_pieces_data.append(piece_data)

        blueprint_jobs[blueprint_id]["result"] = {
            "pattern_pieces": pattern_pieces_data,
            "layout_diagram": base64.b64encode(result.layout_diagram).decode() if result.layout_diagram else None,
            "instructions": result.instructions,
            "material_requirements": result.material_requirements,
            "metadata": result.metadata
        }
        blueprint_jobs[blueprint_id]["raw_result"] = result
        blueprint_jobs[blueprint_id]["status"] = "completed"
        blueprint_jobs[blueprint_id]["progress"] = 100

    except Exception as e:
        logger.error(f"Blueprint generation failed: {str(e)}")
        blueprint_jobs[blueprint_id]["status"] = "failed"
        blueprint_jobs[blueprint_id]["error"] = str(e)


@router.get("/status/{blueprint_id}")
async def get_blueprint_status(blueprint_id: str):
    """Get blueprint generation status"""
    if blueprint_id not in blueprint_jobs:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    job = blueprint_jobs[blueprint_id]
    return {
        "success": True,
        "blueprint_id": blueprint_id,
        "status": job["status"],
        "progress": job["progress"],
        "created_at": job["created_at"],
        "error": job.get("error")
    }


@router.get("/results/{blueprint_id}")
async def get_blueprint_results(blueprint_id: str):
    """Get completed blueprint results"""
    if blueprint_id not in blueprint_jobs:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    job = blueprint_jobs[blueprint_id]

    if job["status"] != "completed":
        return {
            "success": False,
            "message": "Blueprint not completed yet",
            "status": job["status"],
            "progress": job["progress"]
        }

    return {
        "success": True,
        "blueprint_id": blueprint_id,
        "results": job["result"]
    }


@router.get("/export/{blueprint_id}")
async def export_blueprint_pdf(blueprint_id: str):
    """Export blueprint as PDF"""
    if blueprint_id not in blueprint_jobs:
        raise HTTPException(status_code=404, detail="Blueprint not found")

    job = blueprint_jobs[blueprint_id]

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Blueprint not completed yet")

    try:
        # Generate PDF
        from pathlib import Path
        output_dir = Path("storage/blueprints")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{blueprint_id}.pdf"

        result_obj = job.get("raw_result")
        if not result_obj:
            raise HTTPException(status_code=404, detail="Blueprint result not available")

        service = get_blueprint_service()
        await service.export_pattern_pdf(result_obj, str(output_path))

        from fastapi.responses import JSONResponse
        return JSONResponse({
            "success": True,
            "message": "PDF export ready",
            "download_url": f"/api/v1/blueprint/download/{blueprint_id}",
            "filename": f"{blueprint_id}.pdf"
        })

    except Exception as e:
        logger.error(f"PDF export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{blueprint_id}")
async def download_blueprint(blueprint_id: str):
    """Download blueprint PDF file"""
    from fastapi.responses import FileResponse
    from pathlib import Path

    pdf_path = Path(f"storage/blueprints/{blueprint_id}.pdf")

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        path=str(pdf_path),
        filename=f"{blueprint_id}.pdf",
        media_type="application/pdf"
    )


@router.get("/size-systems")
async def get_size_systems():
    """Get available size systems and their sizes"""
    service = get_blueprint_service()

    size_systems = {}
    for system_name, sizes in service.size_systems.items():
        size_systems[system_name] = {
            "name": system_name,
            "sizes": list(sizes.keys()),
            "default_size": "M" if "M" in sizes else list(sizes.keys())[0]
        }

    return {
        "success": True,
        "size_systems": size_systems
    }


@router.get("/garment-types")
async def get_garment_types():
    """Get supported garment types"""
    garment_types = [
        {"id": "dress", "name": "Dress", "description": "Full dress patterns"},
        {"id": "shirt", "name": "Shirt/Blouse", "description": "Shirt and blouse patterns"},
        {"id": "skirt", "name": "Skirt", "description": "Skirt patterns"},
        {"id": "pants", "name": "Pants/Trousers", "description": "Pants patterns"},
        {"id": "jacket", "name": "Jacket/Blazer", "description": "Jacket patterns"},
        {"id": "coat", "name": "Coat", "description": "Coat patterns"}
    ]

    return {
        "success": True,
        "garment_types": garment_types
    }
