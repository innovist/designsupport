"""Adapters for specs module.

Implements cross-module port adapters for accessing design_sessions,
concepts, abstraction, and generation modules.
"""
from apps.specs.infrastructure.adapters.design_session_adapter import DjangoORMSessionAdapter
from apps.specs.infrastructure.adapters.concept_adapter import DjangoORMConceptAdapter
from apps.specs.infrastructure.adapters.abstraction_rule_adapter import DjangoORMAbstractionRuleAdapter
from apps.specs.infrastructure.adapters.generation_job_adapter import DjangoORMGenerationJobAdapter

__all__ = [
    "DjangoORMSessionAdapter",
    "DjangoORMConceptAdapter",
    "DjangoORMAbstractionRuleAdapter",
    "DjangoORMGenerationJobAdapter",
]
