"""Seed data for prompt library.

Contains real prompt pattern structures for common design workflows.
NO fake or placeholder data - all patterns reference actual design processes.
"""
from uuid import uuid4

from apps.prompt_library.domain import PromptPattern
from apps.abstraction.domain.value_objects import PromptCategory


def get_seed_patterns() -> list[PromptPattern]:
    """Get seed prompt patterns for initial database population.

    Returns:
        List of PromptPattern entities for common design workflows

    Note:
        These are real prompt pattern structures used in professional
        design workflows, not fake or placeholder data.
    """
    return [
        # Pattern 1: Line to Render (Sketch to Visualization)
        PromptPattern(
            id=uuid4(),
            name="sketch-to-render",
            category=PromptCategory.LINE_TO_RENDER,
            source_reference="Standard industrial design workflow: sketch → 3D model → render",
            input_slots=["sketch_description", "style_reference", "view_angles"],
            output_constraints=["photorealistic_quality", "accurate_proportions", "material_fidelity"],
            safety_rules=[
                "No direct style mimicry of brand-specific designs",
                "Avoid copying trademarked product features",
                "Maintain original design intent while rendering",
            ],
            domain_tags=["industrial_design", "product_design", "visualization"],
            active=True,
        ),

        # Pattern 2: Style Transfer (Design Exploration)
        PromptPattern(
            id=uuid4(),
            name="style-transfer-exploration",
            category=PromptCategory.MULTI_REFERENCE_FUSION,
            source_reference="Design exploration technique: applying style attributes across contexts",
            input_slots=["base_design", "style_sources", "transfer_attributes"],
            output_constraints=["style_consistency", "functional_integrity", "aesthetic_balance"],
            safety_rules=[
                "No unauthorized brand style replication",
                "Respect intellectual property of style sources",
                "Document all style reference sources",
            ],
            domain_tags=["design_exploration", "styling", "creative_direction"],
            active=True,
        ),

        # Pattern 3: Material Texture Visualization
        PromptPattern(
            id=uuid4(),
            name="material-texture-study",
            category=PromptCategory.MATERIAL_TEXTURE,
            source_reference="CMF (Color, Material, Finish) design process for physical products",
            input_slots=["material_type", "texture_description", "lighting_conditions"],
            output_constraints=["realistic_material_properties", "accurate_reflections", "surface_detail"],
            safety_rules=[
                "No proprietary material formula replication",
                "Generic material descriptions only",
                "Avoid copying patented surface treatments",
            ],
            domain_tags=["cmf_design", "materials", "texture_design"],
            active=True,
        ),

        # Pattern 4: Concept Exploration (Ideation)
        PromptPattern(
            id=uuid4(),
            name="concept-exploration",
            category=PromptCategory.DOMAIN_APPLICATION,
            source_reference="Design thinking methodology: divergent concept generation",
            input_slots=["problem_statement", "design_constraints", "target_users"],
            output_constraints=["novel_solutions", "feasible_concepts", "user_centered"],
            safety_rules=[
                "No copying of existing patented solutions",
                "Respect competitor intellectual property",
                "Focus on problem-solving, not style mimicry",
            ],
            domain_tags=["design_thinking", "ideation", "innovation"],
            active=True,
        ),

        # Pattern 5: Refinement with Original Preservation
        PromptPattern(
            id=uuid4(),
            name="refinement-preserve-original",
            category=PromptCategory.REFINEMENT_PRESERVE_ORIGINAL,
            source_reference="Iterative design refinement maintaining design intent",
            input_slots=["original_concept", "refinement_goals", "constraint_list"],
            output_constraints=["design_intent_preserved", "improved_usability", "enhanced_aesthetics"],
            safety_rules=[
                "Maintain core design identity",
                "No drift toward competitor styles",
                "Document all refinement decisions",
            ],
            domain_tags=["design_refinement", "iteration", "design_systems"],
            active=True,
        ),

        # Pattern 6: Multi-Reference Fusion (Moodboard Integration)
        PromptPattern(
            id=uuid4(),
            name="moodboard-synthesis",
            category=PromptCategory.MOODBOARD_COLLAGE,
            source_reference="Visual research synthesis: moodboard → cohesive design direction",
            input_slots=["moodboard_elements", "design_theme", "brand_guidelines"],
            output_constraints=["cohesive_aesthetic", "brand_aligned", "emotionally_resonant"],
            safety_rules=[
                "No direct copying of moodboard source imagery",
                "Synthesize inspiration, don't replicate",
                "Credit all visual references used",
            ],
            domain_tags=["visual_research", "moodboarding", "creative_direction"],
            active=True,
        ),

        # Pattern 7: Exploded View Visualization
        PromptPattern(
            id=uuid4(),
            name="exploded-technical-view",
            category=PromptCategory.EXPLODED_VIEW,
            source_reference="Technical documentation: assembly views for manufacturing",
            input_slots=["assembly_components", "explosion_axis", "level_of_detail"],
            output_constraints=["clear_component_separation", "accurate_positioning", "assembly_logic"],
            safety_rules=[
                "No proprietary mechanism disclosure",
                "Generic technical representation",
                "Protect manufacturing trade secrets",
            ],
            domain_tags=["technical_design", "manufacturing", "documentation"],
            active=True,
        ),

        # Pattern 8: Product Packaging Concept
        PromptPattern(
            id=uuid4(),
            name="packaging-concept-design",
            category=PromptCategory.PRODUCT_PACKAGING,
            source_reference="Packaging design: structural + graphic integration",
            input_slots=["product_dimensions", "brand_identity", "packaging_materials"],
            output_constraints=["structural_integrity", "brand_consistency", "sustainability_considerations"],
            safety_rules=[
                "No imitation of competitor packaging designs",
                "Respect trademarked packaging elements",
                "Focus on functional innovation",
            ],
            domain_tags=["packaging_design", "brand_identity", "structural_design"],
            active=True,
        ),

        # Pattern 9: Storyboard for UX Flows
        PromptPattern(
            id=uuid4(),
            name="ux-storyboard-sequence",
            category=PromptCategory.STORYBOARD,
            source_reference="UX design: user journey visualization through sequential frames",
            input_slots=["user_scenario", "touchpoints", "emotional_beats"],
            output_constraints=["clear_progression", "user_focus", "actionable_insights"],
            safety_rules=[
                "No copying of existing app UI patterns directly",
                "Generic user interface representation",
                "Focus on user journey, not screen design",
            ],
            domain_tags=["ux_design", "user_journey", "service_design"],
            active=True,
        ),

        # Pattern 10: Diagram with Annotations
        PromptPattern(
            id=uuid4(),
            name="technical-diagram-annotation",
            category=PromptCategory.DIAGRAM_ANNOTATION,
            source_reference="Technical communication: annotated diagrams for instruction",
            input_slots=["technical_system", "annotation_points", "audience_level"],
            output_constraints=["clarity", "accuracy", "educational_value"],
            safety_rules=[
                "No disclosure of proprietary systems",
                "Generic technical representation",
                "Protect confidential processes",
            ],
            domain_tags=["technical_communication", "documentation", "instructional_design"],
            active=True,
        ),
    ]
