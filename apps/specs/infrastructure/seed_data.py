"""Seed data for DomainPack initial data.

Per REQ-03-DOMAIN-001: 4 initial domains provided.
Per INV-03-03: NO hardcoded domain branches - all behavior driven by this data.
"""

# Initial domain pack data
DOMAIN_PACK_SEED_DATA = [
    {
        "id": "industrial",
        "domain": "Industrial Design",
        "brief_schema": {
            "product_type": "string",
            "target_market": "string",
            "materials": "list<string>",
            "manufacturing": "string",
            "sustainability": "string",
        },
        "evaluation_axes": ["form", "structure", "surface", "usability"],
        "generation_outputs": ["product_render", "exploded_view", "material_swatches"],
        "spec_template_uri": "templates/specs/industrial_spec.md",
        "spec_sections": [
            "product_spec",
            "materials",
            "manufacturing_method",
            "sustainability_report",
            "cost_analysis",
        ],
    },
    {
        "id": "fashion",
        "domain": "Fashion Design",
        "brief_schema": {
            "item_type": "string",
            "season": "string",
            "target_demographic": "string",
            "style_keywords": "list<string>",
            "fabric_preferences": "list<string>",
        },
        "evaluation_axes": ["form", "surface", "color_material", "meaning"],
        "generation_outputs": ["look_render", "fabric_swatches", "color_palette", "styling_variations"],
        "spec_template_uri": "templates/specs/fashion_spec.md",
        "spec_sections": [
            "item_description",
            "fabric_specs",
            "color_palette",
            "pattern_details",
            "styling_guide",
            "season_rationale",
        ],
    },
    {
        "id": "visual",
        "domain": "Visual Design",
        "brief_schema": {
            "medium": "string",
            "purpose": "string",
            "audience": "string",
            "mood_keywords": "list<string>",
            "brand_constraints": "list<string>",
        },
        "evaluation_axes": ["form", "color_material", "meaning", "usability"],
        "generation_outputs": ["poster_render", "mood_board", "color_system", "typography_variations"],
        "spec_template_uri": "templates/specs/visual_spec.md",
        "spec_sections": [
            "visual_concept",
            "color_system",
            "typography",
            "layout_guide",
            "brand_alignment",
            "production_specs",
        ],
    },
    {
        "id": "advertising",
        "domain": "Advertising",
        "brief_schema": {
            "campaign_type": "string",
            "platform": "string",
            "target_audience": "string",
            "message": "string",
            "call_to_action": "string",
        },
        "evaluation_axes": ["form", "meaning", "usability"],
        "generation_outputs": ["campaign_cut", "storyboard", "social_variants", "print_ready"],
        "spec_template_uri": "templates/specs/advertising_spec.md",
        "spec_sections": [
            "campaign_concept",
            "message_hierarchy",
            "visual_system",
            "platform_specs",
            "production_timeline",
            "compliance_checklist",
        ],
    },
]


def get_domain_pack_seed_data():
    """Get all domain pack seed data.

    Returns:
        List of domain pack dictionaries
    """
    return DOMAIN_PACK_SEED_DATA


def get_domain_pack_by_id(domain_id: str):
    """Get domain pack seed data by ID.

    Args:
        domain_id: Domain pack ID (e.g., "industrial", "fashion")

    Returns:
        Domain pack dictionary if found, None otherwise
    """
    for pack in DOMAIN_PACK_SEED_DATA:
        if pack["id"] == domain_id:
            return pack
    return None


def get_all_domain_ids():
    """Get all domain pack IDs.

    Returns:
        List of domain pack IDs
    """
    return [pack["id"] for pack in DOMAIN_PACK_SEED_DATA]
