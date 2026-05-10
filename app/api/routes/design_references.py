"""Design reference image search API (Unsplash/Pexels/Pixabay)."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.infrastructure.search.design_reference_client import get_design_reference_client

router = APIRouter(tags=["design-references"])


class DesignRefSearchRequest(BaseModel):
    query: str
    per_page: int = 10


@router.post("/design-references/search")
async def search_design_references(body: DesignRefSearchRequest):
    client = get_design_reference_client()
    images = await client.search(body.query, body.per_page)
    return {
        "count": len(images),
        "images": [
            {
                "id": img.id,
                "source": img.source,
                "title": img.title,
                "image_url": img.image_url,
                "thumbnail_url": img.thumbnail_url,
                "photographer": img.photographer,
                "source_url": img.source_url,
                "width": img.width,
                "height": img.height,
            }
            for img in images
        ],
    }
