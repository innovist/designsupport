"""Django REST views for abstraction module."""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.abstraction.application.dtos import (
    AbstractionRuleDTO,
    SketchPromptDTO,
    PromptSafetyViolationDTO,
    PromptPatternDTO,
)
from apps.abstraction.application.use_cases.generate_abstraction_rules import (
    GenerateAbstractionRulesUseCase,
)
from apps.abstraction.application.use_cases.generate_sketch_prompts import (
    GenerateSketchPromptsUseCase,
)
from apps.abstraction.application.use_cases.validate_prompt_safety import (
    ValidatePromptSafetyUseCase,
)
from apps.abstraction.presentation.serializers import (
    GenerateAbstractionRulesSerializer,
    AbstractionRuleSerializer,
    GenerateSketchPromptsSerializer,
    SketchPromptSerializer,
    ValidatePromptSafetySerializer,
    PromptSafetyViolationSerializer,
    PromptPatternSerializer,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def generate_abstraction_rules(request):
    """Generate abstraction rules from a concept.

    REQ-03-ABSTRACT-002: At least 2 axes must have valid rules.
    """
    serializer = GenerateAbstractionRulesSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    request_dto = serializer.to_request_dto()

    # Initialize use case with dependencies (would be injected in production)
    # For now, this is a placeholder - production would use DI container
    use_case = _get_generate_abstraction_rules_use_case()

    import asyncio

    result = asyncio.run(use_case.execute(request_dto))

    if result.is_failure:
        error = result.error
        return Response(
            {"error": error.message, "details": error.details},
            status=status.HTTP_400_BAD_REQUEST if error.__class__.__name__ == "ValidationError" else status.HTTP_404_NOT_FOUND,
        )

    response_data = result.value
    rules_data = [
        AbstractionRuleSerializer.from_dto(rule).data
        for rule in response_data.rules
    ]

    return Response({
        "rules": rules_data,
        "rejected_count": response_data.rejected_count,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def generate_sketch_prompts(request):
    """Generate sketch prompts from abstraction rules.

    REQ-03-ABSTRACT-003: Uses SketchAnalysis to distinguish keep vs modifiable elements.
    REQ-03-ABSTRACT-004: Builds preserve_original and expand_concept prompts.
    """
    serializer = GenerateSketchPromptsSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    request_dto = serializer.to_request_dto()

    # Initialize use case with dependencies
    use_case = _get_generate_sketch_prompts_use_case()

    import asyncio

    result = asyncio.run(use_case.execute(request_dto))

    if result.is_failure:
        error = result.error
        return Response(
            {"error": error.message, "details": error.details},
            status=status.HTTP_400_BAD_REQUEST if error.__class__.__name__ == "ValidationError" else status.HTTP_404_NOT_FOUND,
        )

    response_data = result.value
    prompts_data = [
        SketchPromptSerializer.from_dto(prompt).data
        for prompt in response_data.prompts
    ]

    return Response({
        "prompts": prompts_data,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def validate_prompt_safety(request):
    """Validate prompt safety.

    REQ-03-PROMPT-006: Record safety violations for auditing.
    """
    serializer = ValidatePromptSafetySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    request_dto = serializer.to_request_dto()

    # Initialize use case with dependencies
    use_case = _get_validate_prompt_safety_use_case()

    import asyncio

    result = asyncio.run(use_case.execute(request_dto))

    if result.is_failure:
        error = result.error
        return Response(
            {"error": error.message, "details": error.details},
            status=status.HTTP_400_BAD_REQUEST,
        )

    response_data = result.value
    violations_data = [
        PromptSafetyViolationSerializer.from_dto(violation).data
        for violation in response_data.violations
    ]

    return Response({
        "is_safe": response_data.is_safe,
        "violations": violations_data,
    })


# Helper functions to get use case instances
# In production, these would use a DI container


def _get_generate_abstraction_rules_use_case():
    """Get or create the use case instance."""
    from apps.abstraction.infrastructure.repositories.abstraction_rule_repository import (
        DjangoAbstractionRuleRepository,
    )
    from apps.concepts.infrastructure.repositories.concept_repository import (
        DjangoConceptRepository,
    )

    rule_repository = DjangoAbstractionRuleRepository()
    concept_repository = DjangoConceptRepository()

    return GenerateAbstractionRulesUseCase(
        rule_repository=rule_repository,
        concept_port=concept_repository,
    )


def _get_generate_sketch_prompts_use_case():
    """Get or create the use case instance."""
    from apps.abstraction.infrastructure.repositories.abstraction_rule_repository import (
        DjangoAbstractionRuleRepository,
    )
    from apps.abstraction.infrastructure.repositories.sketch_prompt_repository import (
        DjangoSketchPromptRepository,
    )
    from apps.concepts.infrastructure.repositories.concept_repository import (
        DjangoConceptRepository,
    )
    from apps.sketch_analysis.infrastructure.repositories.sketch_analysis_repository import (
        DjangoSketchAnalysisRepository,
    )

    rule_repository = DjangoAbstractionRuleRepository()
    prompt_repository = DjangoSketchPromptRepository()
    concept_repository = DjangoConceptRepository()
    sketch_analysis_repository = DjangoSketchAnalysisRepository()

    return GenerateSketchPromptsUseCase(
        rule_repository=rule_repository,
        prompt_repository=prompt_repository,
        concept_port=concept_repository,
        sketch_analysis_port=sketch_analysis_repository,
    )


def _get_validate_prompt_safety_use_case():
    """Get or create the use case instance."""
    from apps.abstraction.infrastructure.repositories.prompt_safety_violation_repository import (
        DjangoPromptSafetyViolationRepository,
    )
    from apps.abstraction.infrastructure.repositories.prompt_pattern_repository import (
        DjangoPromptPatternRepository,
    )

    violation_repository = DjangoPromptSafetyViolationRepository()
    pattern_repository = DjangoPromptPatternRepository()

    return ValidatePromptSafetyUseCase(
        violation_repository=violation_repository,
        pattern_repository=pattern_repository,
    )
