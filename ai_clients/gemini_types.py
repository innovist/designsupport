"""
Gemini response types
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class GenerationConfig:
    """Generation settings"""
    temperature: float = 0.7
    top_p: float = 0.8
    top_k: int = 40
    max_output_tokens: int = 8192
    candidate_count: int = 1


@dataclass
class GenerationResponse:
    """Generation response"""
    text: str
    model: str
    usage_metadata: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    safety_ratings: Optional[List[Dict[str, str]]] = None
