"""Use case: Create a spec document."""
from uuid import UUID

from shared.application.result import Result
from shared.domain.exceptions import NotFoundError, ValidationError

from apps.specs.application.dtos import SpecDocumentDTO, CreateSpecRequest
from apps.specs.application.ports import (
    AbstractionRulePort,
    ConceptPort,
    DomainPackRepositoryPort,
    GenerationJobPort,
    SessionPort,
    SpecDocumentRepositoryPort,
)
from apps.specs.domain.entities import REQUIRED_SECTION_TYPES, SpecDocument, SpecSection
from apps.specs.domain.services import DomainPackResolver


class CreateSpecDocumentUseCase:
    """Use case for creating a new spec document from session data."""

    def __init__(
        self,
        spec_repository: SpecDocumentRepositoryPort,
        domain_pack_repository: DomainPackRepositoryPort,
        session_port: SessionPort,
        concept_port: ConceptPort,
        abstraction_rule_port: AbstractionRulePort,
        generation_job_port: GenerationJobPort,
        domain_pack_resolver: DomainPackResolver,
    ):
        self.spec_repository = spec_repository
        self.domain_pack_repository = domain_pack_repository
        self.session_port = session_port
        self.concept_port = concept_port
        self.abstraction_rule_port = abstraction_rule_port
        self.generation_job_port = generation_job_port
        self.domain_pack_resolver = domain_pack_resolver

    async def execute(self, request: CreateSpecRequest) -> Result[SpecDocumentDTO]:
        """Execute the use case.

        Args:
            request: CreateSpecRequest with session_id and created_by

        Returns:
            Result with SpecDocumentDTO on success, error on failure
        """
        try:
            # Validate session exists
            if not await self.session_port.session_exists(request.session_id):
                return Result.failure(NotFoundError("DesignSession", str(request.session_id)))

            # Get session data
            session_data = await self.session_port.get_session(request.session_id)
            if not session_data:
                return Result.failure(NotFoundError("DesignSession", str(request.session_id)))

            # Get domain for session
            domain = await self.session_port.get_session_domain(request.session_id)
            if not domain:
                return Result.failure(ValidationError("domain", "Session has no domain specified"))

            # Get domain pack
            domain_pack = await self.domain_pack_repository.get_by_id(domain)
            if not domain_pack:
                return Result.failure(NotFoundError("DomainPack", domain))

            # Check if spec already exists for this session
            existing_spec = await self.spec_repository.get_by_session(request.session_id)
            if existing_spec and existing_spec.status.value == "approved":
                # Create new version
                spec = existing_spec.create_new_version()
                spec.created_by = request.created_by
            else:
                # Create first version
                spec = SpecDocument(
                    session_id=request.session_id,
                    domain=domain,
                    version=1,
                    created_by=request.created_by,
                )

            # Initialize required sections
            await self._initialize_sections(spec, domain_pack, request.session_id)

            # Add initial evidence links from session
            await self._add_session_evidence_links(spec, request.session_id)

            # Save spec
            saved_spec = await self.spec_repository.save(spec)

            return Result.success(SpecDocumentDTO.from_entity(saved_spec))

        except ValidationError as e:
            return Result.failure(e)
        except Exception as e:
            return Result.failure(ValidationError("spec", f"Failed to create spec document: {str(e)}"))

    async def _initialize_sections(self, spec: SpecDocument, domain_pack, session_id: UUID) -> None:
        """Initialize all required sections for the spec.

        Args:
            spec: Spec document to initialize
            domain_pack: Domain pack configuration
            session_id: Session UUID
        """
        # Get session brief data
        brief_data = await self.session_port.get_session_brief(session_id) or {}

        # Create required sections
        for section_type in REQUIRED_SECTION_TYPES:
            section = self._create_section(section_type, domain_pack, brief_data, session_id)
            spec.add_section(section)

        # Create domain-specific sections
        for section_type in domain_pack.spec_sections:
            if section_type not in REQUIRED_SECTION_TYPES:
                section = self._create_domain_section(section_type, domain_pack, brief_data)
                spec.add_section(section)

    def _create_section(
        self, section_type: str, domain_pack, brief_data: dict, session_id: UUID
    ) -> SpecSection:
        """Create a required section.

        Args:
            section_type: Type of section to create
            domain_pack: Domain pack configuration
            brief_data: Brief data
            session_id: Session UUID

        Returns:
            SpecSection instance
        """
        # Section titles mapping
        section_titles = {
            "project_brief": "Project Brief",
            "trend_evidence": "Trend Evidence",
            "concept_candidates_evaluation": "Concept Candidates and Evaluation",
            "final_concept_decision": "Final Concept Decision",
            "user_sketch_original": "User Sketch Original",
            "user_sketch_ai_interpretation": "User Sketch AI Interpretation",
            "reference_board": "Reference Board",
            "abstraction_rules": "Abstraction Rules",
            "sketch_and_generated_images": "Sketch and Generated Images",
            "final_comparison": "Final Comparison",
            "domain_specific_spec": "Domain-Specific Specification",
            "source_license_ai_disclosure": "Source/License/AI Usage Disclosure",
        }

        # Resolve content structure based on domain
        content = self.domain_pack_resolver.resolve_section_content(domain_pack, section_type, brief_data)

        return SpecSection(
            section_type=section_type,
            title=section_titles.get(section_type, section_type.replace("_", " ").title()),
            content=content,
            evidence_links=[],
            required=True,
            completed=False,
        )

    def _create_domain_section(self, section_type: str, domain_pack, brief_data: dict) -> SpecSection:
        """Create a domain-specific section.

        Args:
            section_type: Type of section to create
            domain_pack: Domain pack configuration
            brief_data: Brief data

        Returns:
            SpecSection instance
        """
        content = self.domain_pack_resolver.resolve_section_content(domain_pack, section_type, brief_data)

        return SpecSection(
            section_type=section_type,
            title=section_type.replace("_", " ").title(),
            content=content,
            evidence_links=[],
            required=True,  # Domain sections are also required
            completed=False,
        )

    async def _add_session_evidence_links(self, spec: SpecDocument, session_id: UUID) -> None:
        """Add evidence links from session data.

        Args:
            spec: Spec document to add links to
            session_id: Session UUID
        """
        # Add session ID as evidence link
        spec.add_evidence_link(str(session_id))

        # Try to add concept references
        try:
            concepts = await self.concept_port.get_concepts_by_session(session_id)
            for concept in concepts:
                if "id" in concept:
                    spec.add_evidence_link(str(concept["id"]))
        except Exception:
            pass  # Port might not be implemented yet

        # Try to add abstraction rule references
        try:
            rules = await self.abstraction_rule_port.get_rules_by_session(session_id)
            for rule in rules:
                if "id" in rule:
                    spec.add_evidence_link(str(rule["id"]))
        except Exception:
            pass  # Port might not be implemented yet

        # Try to add generation job references
        try:
            jobs = await self.generation_job_port.get_jobs_by_session(session_id)
            for job in jobs:
                if "id" in job:
                    spec.add_evidence_link(str(job["id"]))
        except Exception:
            pass  # Port might not be implemented yet
