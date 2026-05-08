"""Value objects for model catalog domain.

This module contains value objects used across the model catalog domain.
Value objects are immutable objects that represent concepts in the domain
and are identified by their attributes rather than an ID.

REQ-04-POLICY-001: 9 fixed feature keys for the fashion AI system.
"""
from enum import Enum

from apps.model_catalog.domain.entities import ModelType


class FeatureKey(str, Enum):
    """Feature key enumeration for fashion AI system.

    Implements REQ-04-POLICY-001: Fixed set of 9 feature keys.

    These keys represent the core features of the fashion AI system and are
    used to map features to specific models with fallback chains.

    Attributes:
        TREND_RESEARCH: Trend research and analysis
        CONCEPT_CHAT: Concept development chat
        USER_SKETCH_ANALYSIS: User sketch analysis
        REFERENCE_ANALYSIS: Reference image analysis
        ABSTRACTION: Design abstraction
        SKETCH_PROMPT: Sketch prompt generation
        IMAGE_GENERATION: Image generation (primary feature)
        SPEC_WRITING: Specification writing
        VERIFICATION: Design verification

    Example:
        >>> key = FeatureKey.IMAGE_GENERATION
        >>> key.value
        'ImageGeneration'
        >>> key.model_type_expectation
        <ModelType.IMAGE: 'image'>
    """

    TREND_RESEARCH = "TrendResearch"
    CONCEPT_CHAT = "ConceptChat"
    USER_SKETCH_ANALYSIS = "UserSketchAnalysis"
    REFERENCE_ANALYSIS = "ReferenceAnalysis"
    ABSTRACTION = "Abstraction"
    SKETCH_PROMPT = "SketchPrompt"
    IMAGE_GENERATION = "ImageGeneration"
    SPEC_WRITING = "SpecWriting"
    VERIFICATION = "Verification"

    def __str__(self) -> str:
        """Return string representation."""
        return self.value

    @property
    def model_type_expectation(self) -> ModelType:
        """Get expected ModelType for this feature.

        Returns the model type that is most appropriate for this feature.
        This is used for validation and policy configuration.

        Returns:
            ModelType: Expected model type for this feature

        Example:
            >>> FeatureKey.IMAGE_GENERATION.model_type_expectation
            <ModelType.IMAGE: 'image'>
            >>> FeatureKey.CONCEPT_CHAT.model_type_expectation
            <ModelType.CHAT: 'chat'>
        """
        # Map features to their expected model types
        type_mapping = {
            FeatureKey.TREND_RESEARCH: ModelType.CHAT,
            FeatureKey.CONCEPT_CHAT: ModelType.CHAT,
            FeatureKey.USER_SKETCH_ANALYSIS: ModelType.VISION,
            FeatureKey.REFERENCE_ANALYSIS: ModelType.VISION,
            FeatureKey.ABSTRACTION: ModelType.CHAT,
            FeatureKey.SKETCH_PROMPT: ModelType.CHAT,
            FeatureKey.IMAGE_GENERATION: ModelType.IMAGE,
            FeatureKey.SPEC_WRITING: ModelType.CHAT,
            FeatureKey.VERIFICATION: ModelType.CHAT,
        }
        return type_mapping[self]

    def is_image_generation_feature(self) -> bool:
        """Check if this feature requires image generation models.

        Returns:
            True if this feature generates images, False otherwise

        Example:
            >>> FeatureKey.IMAGE_GENERATION.is_image_generation_feature()
            True
            >>> FeatureKey.CONCEPT_CHAT.is_image_generation_feature()
            False
        """
        return self == FeatureKey.IMAGE_GENERATION

    def is_vision_required(self) -> bool:
        """Check if this feature requires vision/image analysis capabilities.

        Returns:
            True if feature processes images, False otherwise

        Example:
            >>> FeatureKey.USER_SKETCH_ANALYSIS.is_vision_required()
            True
            >>> FeatureKey.TREND_RESEARCH.is_vision_required()
            False
        """
        return self in {
            FeatureKey.USER_SKETCH_ANALYSIS,
            FeatureKey.REFERENCE_ANALYSIS,
        }

    @classmethod
    def all_keys(cls) -> list[str]:
        """Get all feature key values as strings.

        Returns:
            List of all feature key string values

        Example:
            >>> FeatureKey.all_keys()
            ['TrendResearch', 'ConceptChat', 'UserSketchAnalysis', ...]
        """
        return [key.value for key in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a string value is a valid feature key.

        Args:
            value: String value to validate

        Returns:
            True if value is a valid feature key, False otherwise

        Example:
            >>> FeatureKey.is_valid("ImageGeneration")
            True
            >>> FeatureKey.is_valid("InvalidFeature")
            False
        """
        try:
            cls(value)
            return True
        except ValueError:
            return False

    @classmethod
    def from_string(cls, value: str) -> "FeatureKey":
        """Create FeatureKey from string value.

        Args:
            value: String representation of feature key

        Returns:
            FeatureKey enum instance

        Raises:
            ValueError: If value is not a valid feature key

        Example:
            >>> FeatureKey.from_string("ImageGeneration")
            <FeatureKey.IMAGE_GENERATION: 'ImageGeneration'>
        """
        try:
            return cls(value)
        except ValueError as e:
            valid_keys = ", ".join(cls.all_keys())
            raise ValueError(
                f"Invalid feature key '{value}'. "
                f"Valid keys are: {valid_keys}"
            ) from e
