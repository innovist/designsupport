"""Value objects for abstraction module.

This file is pure Python - no Django imports allowed.
"""
from enum import Enum


class AbstractionAxis(str, Enum):
    """Axes of design abstraction for concept extraction.

    REQ-03-ABSTRACT-001: Six abstraction axes for analyzing design concepts.
    """
    FORM = "form"
    STRUCTURE = "structure"
    SURFACE = "surface"
    COLOR_MATERIAL = "color_material"
    MEANING = "meaning"
    USABILITY = "usability"

    @classmethod
    def all_axes(cls) -> list['AbstractionAxis']:
        """Get all abstraction axes."""
        return list(cls)


class SketchPromptKind(str, Enum):
    """Types of sketch prompts.

    REQ-03-ABSTRACT-004: Two kinds of sketch prompts.
    """
    PRESERVE_ORIGINAL = "preserve_original"
    EXPAND_CONCEPT = "expand_concept"


class PromptCategory(str, Enum):
    """Categories of prompt patterns.

    REQ-03-PROMPT-001: Prompt pattern library categories.
    """
    LINE_TO_RENDER = "line_to_render"
    MULTI_REFERENCE_FUSION = "multi_reference_fusion"
    PRODUCT_PACKAGING = "product_packaging"
    MATERIAL_TEXTURE = "material_texture"
    EXPLODED_VIEW = "exploded_view"
    STORYBOARD = "storyboard"
    MOODBOARD_COLLAGE = "moodboard_collage"
    DIAGRAM_ANNOTATION = "diagram_annotation"
    DOMAIN_APPLICATION = "domain_application"
    REFINEMENT_PRESERVE_ORIGINAL = "refinement_preserve_original"


class RiskLevel(str, Enum):
    """Risk levels for style mimicry detection.

    REQ-03-ABSTRACT-005: Risk assessment for brand/style mimicry.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"
