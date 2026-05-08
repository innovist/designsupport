"""Use case: Generate sketch prompts from abstraction rules.

REQ-03-ABSTRACT-003: Uses SketchAnalysis to distinguish keep vs modifiable elements.
REQ-03-ABSTRACT-004: Builds preserve_original and expand_concept prompts.
"""
from typing import Optional
from uuid import UUID

from shared.application.result import Result
from shared.domain.exceptions import NotFoundError, ValidationError

from apps.abstraction.application.dtos import (
    GenerateSketchPromptsRequest,
    GenerateSketchPromptsResponse,
    SketchPromptDTO,
)
from apps.abstraction.application.ports import (
    AbstractionRuleRepositoryPort,
    SketchPromptRepositoryPort,
    ConceptPort,
    SketchAnalysisPort,
)
from apps.abstraction.domain.entities import SketchPrompt
from apps.abstraction.domain.services import SketchPromptBuilder
from apps.abstraction.domain.value_objects import SketchPromptKind


class GenerateSketchPromptsUseCase:
    """Generate sketch prompts from abstraction rules.

    This use case builds prompts for generating sketches based on
    abstraction rules and sketch analysis data.
    """

    def __init__(
        self,
        rule_repository: AbstractionRuleRepositoryPort,
        prompt_repository: SketchPromptRepositoryPort,
        concept_port: ConceptPort,
        sketch_analysis_port: SketchAnalysisPort,
    ):
        self.rule_repository = rule_repository
        self.prompt_repository = prompt_repository
        self.concept_port = concept_port
        self.sketch_analysis_port = sketch_analysis_port

    async def execute(self, request: GenerateSketchPromptsRequest) -> Result[GenerateSketchPromptsResponse]:
        """Execute the use case.

        Args:
            request: Request with session_id, concept_id

        Returns:
            Result with GenerateSketchPromptsResponse or error
        """
        # Validate concept exists
        concept = await self.concept_port.get_by_id(request.concept_id)
        if not concept:
            return Result.failure(
                NotFoundError("Concept", str(request.concept_id))
            )

        # Get abstraction rules for the concept
        rules = await self.rule_repository.list_by_concept(request.concept_id)
        if not rules:
            return Result.failure(
                ValidationError(
                    "concept_id",
                    "No abstraction rules found for this concept. "
                    "Generate abstraction rules first."
                )
            )

        # Get sketch analysis data
        sketch_analysis = await self.sketch_analysis_port.get_latest_by_session(
            request.session_id
        )
        if not sketch_analysis:
            # Use default sketch analysis if not available
            sketch_analysis = {
                "keep_elements": ["core concept identity", "primary visual elements"],
                "modifiable_elements": ["color palette", "secondary details", "layout variations"],
                "core_identity": concept.get("title", "the concept"),
            }

        # Generate prompts
        generated_prompts = []

        # Build preserve_original prompt
        try:
            template, variables, source_refs = SketchPromptBuilder.build_preserve_original_prompt(
                session_id=request.session_id,
                abstraction_rules=rules,
                sketch_analysis=sketch_analysis,
            )
            preserve_prompt = SketchPrompt(
                session_id=request.session_id,
                kind=SketchPromptKind.PRESERVE_ORIGINAL,
                template=template,
                variables=variables,
                source_refs=source_refs,
            )
            saved_preserve = await self.prompt_repository.save(preserve_prompt)
            generated_prompts.append(saved_preserve)
        except ValidationError as e:
            # Log and continue - don't fail entire operation
            pass

        # Build expand_concept prompt
        try:
            template, variables, source_refs = SketchPromptBuilder.build_expand_concept_prompt(
                session_id=request.session_id,
                abstraction_rules=rules,
                sketch_analysis=sketch_analysis,
            )
            expand_prompt = SketchPrompt(
                session_id=request.session_id,
                kind=SketchPromptKind.EXPAND_CONCEPT,
                template=template,
                variables=variables,
                source_refs=source_refs,
            )
            saved_expand = await self.prompt_repository.save(expand_prompt)
            generated_prompts.append(saved_expand)
        except ValidationError as e:
            # Log and continue
            pass

        if not generated_prompts:
            return Result.failure(
                ValidationError(
                    "prompts",
                    "Failed to generate any sketch prompts"
                )
            )

        # Convert to DTOs
        prompt_dtos = [
            SketchPromptDTO(
                id=prompt.id,
                session_id=prompt.session_id,
                kind=prompt.kind.value,
                template=prompt.template,
                variables=prompt.variables,
                source_refs=prompt.source_refs,
                rendered=prompt.render(),
                created_at=prompt.created_at,
            )
            for prompt in generated_prompts
        ]

        response = GenerateSketchPromptsResponse(
            prompts=prompt_dtos,
        )

        return Result.success(response)
