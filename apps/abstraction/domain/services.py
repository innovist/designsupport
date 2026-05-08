"""Domain services for abstraction module.

This file is pure Python - no Django imports allowed.
"""
import re
from typing import Optional
from uuid import UUID

from shared.domain.exceptions import ValidationError

from .entities import AbstractionRule
from .value_objects import AbstractionAxis, RiskLevel


# @MX:ANCHOR: [AUTO] IP protection validator for brand mimicry and license risks
# @MX:REASON: Critical safety gate preventing legal/IP violations in abstraction rules
# @MX:SPEC: REQ-03-ABSTRACT-005, REQ-03-ABSTRACT-006
class AbstractionRuleValidator:
    """Validates abstraction rules for brand/style mimicry and license risks.

    REQ-03-ABSTRACT-005: Detect and reject rules that mimic specific brands/artists.
    REQ-03-ABSTRACT-006: Detect and reject high-risk license violations.
    """

    # Patterns that suggest direct brand/style mimicry
    BRAND_MIMICRY_PATTERNS = [
        r"in the style of\s+(\w+\s+){1,3}",  # "in the style of [brand/artist]"
        r"mimicking\s+(\w+\s+){1,3}",  # "mimicking [brand/artist]"
        r"copy\s+(\w+\s+){1,3}style",  # "copy [brand] style"
        r"resemble\s+(\w+\s+){1,3}",  # "resemble [brand/artist]"
        r"like\s+(\w+\s+){1,3}design",  # "like [brand] design"
        r"inspired by\s+(\w+\s+){1,3}(with|exactly)",  # "inspired by [brand] exactly"
    ]

    # Known brand and artist names (simplified list - would be expanded in production)
    KNOWN_BRANDS = {
        "apple", "samsung", "nike", "adidas", "coca-cola", "pepsi",
        "mcdonalds", "starbucks", "tesla", "bmw", "mercedes", "audi",
        "sony", "lg", "microsoft", "google", "amazon", "facebook",
        "disney", "pixar", "marvel", "dc", "lego", "nintendo",
    }

    KNOWN_ARTISTS = {
        "picasso", "monet", "van gogh", "dali", "warhol", "banksy",
        "kaws", "murakami", "haring", "basquiat", "klimt", "kahlo",
    }

    # Patterns that suggest high license risk
    HIGH_RISK_LICENSE_PATTERNS = [
        r"exact copy",  # Direct copying
        r"replicate",  # Replication
        r"duplicate",  # Duplication
        r"identical to",  # Identical copying
        r"same as",  # Direct copying
        r"trace",  # Tracing
        r"recreate exactly",  # Exact recreation
    ]

    @classmethod
    def validate_rule(
        cls,
        rule: AbstractionRule,
        license_risk: RiskLevel = RiskLevel.UNKNOWN
    ) -> tuple[bool, Optional[str]]:
        """Validate an abstraction rule for safety.

        Args:
            rule: The abstraction rule to validate
            license_risk: Risk level for license concerns

        Returns:
            Tuple of (is_valid, risk_reason)

        Raises:
            InvariantViolationError: If rule violates safety invariants
        """
        # Check for brand/style mimicry
        mimicry_reason = cls._check_brand_mimicry(rule)
        if mimicry_reason:
            rule.mark_risky(mimicry_reason)
            return False, mimicry_reason

        # Check for high license risk with direct style application
        if license_risk in [RiskLevel.HIGH, RiskLevel.UNKNOWN]:
            license_reason = cls._check_license_risk(rule)
            if license_reason:
                rule.mark_risky(license_reason)
                return False, license_reason

        return True, None

    @classmethod
    def _check_brand_mimicry(cls, rule: AbstractionRule) -> Optional[str]:
        """Check if rule mimics specific brand/artist style.

        REQ-03-ABSTRACT-005: Direct style mimicry → REJECT.
        """
        rule_text = f"{rule.observation} {rule.applied_rule}".lower()

        # Check for mimicry patterns
        for pattern in cls.BRAND_MIMICRY_PATTERNS:
            if re.search(pattern, rule_text, re.IGNORECASE):
                # Extract the potential brand/artist name
                match = re.search(pattern, rule_text, re.IGNORECASE)
                if match:
                    # Check if it's a known brand or artist
                    words = rule_text.split()
                    for word in words:
                        if word in cls.KNOWN_BRANDS or word in cls.KNOWN_ARTISTS:
                            return (
                                f"Rule directly mimics style of '{word}'. "
                                f"This violates intellectual property guidelines."
                            )

        return None

    @classmethod
    def _check_license_risk(cls, rule: AbstractionRule) -> Optional[str]:
        """Check if rule has high license risk with direct style application.

        REQ-03-ABSTRACT-006: High license risk + direct style application → REJECT.
        """
        rule_text = f"{rule.observation} {rule.applied_rule}".lower()

        # Check for high-risk license patterns
        for pattern in cls.HIGH_RISK_LICENSE_PATTERNS:
            if re.search(pattern, rule_text, re.IGNORECASE):
                return (
                    "Rule suggests direct copying or replication, "
                    "which poses high license risk."
                )

        return None


# @MX:ANCHOR: [AUTO] Prompt construction for sketch generation with abstraction rules
# @MX:REASON: Bridges abstraction rules to generation prompts; used by refinement workflows
# @MX:SPEC: REQ-03-ABSTRACT-003, REQ-03-ABSTRACT-004
class SketchPromptBuilder:
    """Builds sketch prompts from abstraction rules and sketch analysis data.

    REQ-03-ABSTRACT-003: Uses SketchAnalysis to distinguish keep vs modifiable elements.
    REQ-03-ABSTRACT-004: Builds preserve_original and expand_concept prompts.
    """

    @classmethod
    def build_preserve_original_prompt(
        cls,
        session_id: UUID,
        abstraction_rules: list[AbstractionRule],
        sketch_analysis: dict,
    ) -> tuple[str, dict[str, str], list[UUID]]:
        """Build a prompt that preserves original elements.

        Args:
            session_id: Design session ID
            abstraction_rules: List of abstraction rules
            sketch_analysis: Sketch analysis data with keep/modify elements

        Returns:
            Tuple of (template, variables, source_refs)

        Raises:
            ValidationError: If required data is missing
        """
        if not abstraction_rules:
            raise ValidationError("abstraction_rules", "At least one abstraction rule is required")

        # Extract keep and modifiable elements from sketch analysis
        keep_elements = sketch_analysis.get("keep_elements", [])
        modifiable_elements = sketch_analysis.get("modifiable_elements", [])

        # Build template
        template = (
            "Generate a design sketch that:\n"
            "1. PRESERVES the following core elements: {keep_elements}\n"
            "2. EXPLORES variations in these aspects: {modifiable_elements}\n\n"
            "Design principles to apply:\n"
            "{design_principles}\n\n"
            "Constraints:\n"
            "- Maintain the essential identity of the original concept\n"
            "- Innovate within the modifiable aspects only\n"
            "- Apply the specified design principles thoughtfully"
        )

        # Build variables
        variables = {
            "keep_elements": cls._format_elements(keep_elements),
            "modifiable_elements": cls._format_elements(modifiable_elements),
            "design_principles": cls._format_rules(abstraction_rules),
        }

        # Collect source refs
        source_refs = [rule.id for rule in abstraction_rules]

        return template, variables, source_refs

    @classmethod
    def build_expand_concept_prompt(
        cls,
        session_id: UUID,
        abstraction_rules: list[AbstractionRule],
        sketch_analysis: dict,
    ) -> tuple[str, dict[str, str], list[UUID]]:
        """Build a prompt that expands the concept.

        Args:
            session_id: Design session ID
            abstraction_rules: List of abstraction rules
            sketch_analysis: Sketch analysis data

        Returns:
            Tuple of (template, variables, source_refs)

        Raises:
            ValidationError: If required data is missing
        """
        if not abstraction_rules:
            raise ValidationError("abstraction_rules", "At least one abstraction rule is required")

        # Build template
        template = (
            "Generate a design sketch that EXPANDS the concept by:\n\n"
            "Core concept identity: {core_identity}\n\n"
            "Design principles to explore:\n"
            "{design_principles}\n\n"
            "Exploration directions:\n"
            "{exploration_directions}\n\n"
            "Constraints:\n"
            "- Push the boundaries while respecting the core concept\n"
            "- Apply design principles in innovative ways\n"
            "- Maintain coherence with the original concept's intent"
        )

        # Extract core identity from sketch analysis
        core_identity = sketch_analysis.get("core_identity", "the original concept")

        # Build exploration directions from rules
        exploration_directions = cls._build_exploration_directions(abstraction_rules)

        # Build variables
        variables = {
            "core_identity": core_identity,
            "design_principles": cls._format_rules(abstraction_rules),
            "exploration_directions": exploration_directions,
        }

        # Collect source refs
        source_refs = [rule.id for rule in abstraction_rules]

        return template, variables, source_refs

    @classmethod
    def _format_elements(cls, elements: list[str]) -> str:
        """Format a list of elements into a readable string."""
        if not elements:
            return "none"
        return "\n".join(f"- {elem}" for elem in elements)

    @classmethod
    def _format_rules(cls, rules: list[AbstractionRule]) -> str:
        """Format abstraction rules into a readable string."""
        formatted = []
        for rule in rules:
            formatted.append(f"- [{rule.axis.value}] {rule.applied_rule}")
        return "\n".join(formatted)

    @classmethod
    def _build_exploration_directions(cls, rules: list[AbstractionRule]) -> str:
        """Build exploration directions from abstraction rules."""
        directions = []
        for axis in AbstractionAxis:
            axis_rules = [r for r in rules if r.axis == axis]
            if axis_rules:
                directions.append(
                    f"- Explore {axis.value}: {', '.join(r.applied_rule for r in axis_rules)}"
                )
        return "\n".join(directions) if directions else "Explore all design dimensions"
