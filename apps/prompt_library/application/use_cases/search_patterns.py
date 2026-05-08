"""Use case: Search prompt patterns by category and domain.

REQ-03-PROMPT-002: Search patterns by category and domain.
"""
from typing import Optional

from shared.application.result import Result
from shared.domain.exceptions import ValidationError

from apps.prompt_library.application.ports import PromptPatternRepositoryPort
from apps.prompt_library.domain import PromptPattern, PromptCategory


class SearchPatternsUseCase:
    """Search for prompt patterns in the library.

    This use case provides flexible search capabilities for finding
    relevant prompt patterns based on category and domain tags.
    """

    def __init__(
        self,
        pattern_repository: PromptPatternRepositoryPort,
    ):
        self.pattern_repository = pattern_repository

    async def execute(
        self,
        category: Optional[str] = None,
        domain_tags: Optional[list[str]] = None,
    ) -> Result[list[PromptPattern]]:
        """Execute the use case.

        Args:
            category: Optional category filter (PromptCategory enum value)
            domain_tags: Optional list of domain tags to match

        Returns:
            Result with list of matching patterns or error

        Raises:
            ValidationError: If category is invalid
        """
        # Validate category if provided
        if category:
            try:
                PromptCategory(category)
            except ValueError:
                return Result.failure(
                    ValidationError(
                        "category",
                        f"Invalid category: {category}. Must be one of {[c.value for c in PromptCategory]}"
                    )
                )

        # Build result set
        results: list[PromptPattern] = []

        if category and domain_tags:
            # Both filters: get patterns matching category AND any tag
            category_patterns = await self.pattern_repository.search_by_category(category)
            tag_patterns = await self.pattern_repository.search_by_domain_tags(domain_tags)

            # Intersect: patterns that match both
            category_ids = {p.id for p in category_patterns}
            results = [p for p in tag_patterns if p.id in category_ids]

        elif category:
            # Category only
            results = await self.pattern_repository.search_by_category(category)

        elif domain_tags:
            # Tags only
            results = await self.pattern_repository.search_by_domain_tags(domain_tags)

        else:
            # No filters: return all active patterns
            results = await self.pattern_repository.list_active()

        return Result.success(results)
