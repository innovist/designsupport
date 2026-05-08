"""Category definitions for taxonomy seeding.

7 categories per SPEC-02 across 4 domains.
"""


def get_initial_categories() -> dict[str, list[dict]]:
    """Get initial category definitions.

    Returns:
        Dictionary mapping domain to list of category definitions

    Categories per SPEC-02:
    - 7 categories: Nature, Product, Architecture, Fashion, Graphic, Advertising, Material
    - 4 domains: industrial, fashion, visual, advertising
    """
    return {
        "industrial": [
            {
                "category": "nature",
                "label": "Nature-Inspired Design",
                "description": "Biomimetic and nature-based industrial design trends",
            },
            {
                "category": "product",
                "label": "Product Design",
                "description": "Consumer product and industrial design innovations",
            },
            {
                "category": "architecture",
                "label": "Architecture",
                "description": "Building and architectural design trends",
            },
            {
                "category": "fashion",
                "label": "Fashion Tech",
                "description": "Technology integration in fashion and wearables",
            },
            {
                "category": "graphic",
                "label": "Graphic Design",
                "description": "Visual communication and branding trends",
            },
            {
                "category": "advertising",
                "label": "Advertising",
                "description": "Marketing and advertising campaign trends",
            },
            {
                "category": "material",
                "label": "Materials",
                "description": "New materials and material science applications",
            },
        ],
        "fashion": [
            {
                "category": "nature",
                "label": "Sustainable Fashion",
                "description": "Eco-friendly and sustainable fashion trends",
            },
            {
                "category": "product",
                "label": "Apparel Design",
                "description": "Clothing and apparel design innovations",
            },
            {
                "category": "architecture",
                "label": "Fashion Architecture",
                "description": "Structural and architectural fashion elements",
            },
            {
                "category": "fashion",
                "label": "Haute Couture",
                "description": "High fashion and luxury couture trends",
            },
            {
                "category": "graphic",
                "label": "Print & Pattern",
                "description": "Textile prints and graphic patterns",
            },
            {
                "category": "advertising",
                "label": "Fashion Marketing",
                "description": "Fashion industry marketing campaigns",
            },
            {
                "category": "material",
                "label": "Smart Textiles",
                "description": "Advanced and interactive textile materials",
            },
        ],
        "visual": [
            {
                "category": "nature",
                "label": "Nature Photography",
                "description": "Nature and wildlife photography trends",
            },
            {
                "category": "product",
                "label": "Product Visualization",
                "description": "3D product rendering and visualization",
            },
            {
                "category": "architecture",
                "label": "Architectural Visualization",
                "description": "Archviz and architectural rendering",
            },
            {
                "category": "fashion",
                "label": "Fashion Photography",
                "description": "Editorial and commercial fashion photography",
            },
            {
                "category": "graphic",
                "label": "Digital Art",
                "description": "Digital illustration and artwork",
            },
            {
                "category": "advertising",
                "label": "Visual Advertising",
                "description": "Visual-first advertising campaigns",
            },
            {
                "category": "material",
                "label": "Texture & Material",
                "description": "Material textures and surface design",
            },
        ],
        "advertising": [
            {
                "category": "nature",
                "label": "Eco Branding",
                "description": "Environmental and sustainability branding",
            },
            {
                "category": "product",
                "label": "Product Advertising",
                "description": "Product-focused advertising strategies",
            },
            {
                "category": "architecture",
                "label": "Spatial Branding",
                "description": "Physical space and experiential advertising",
            },
            {
                "category": "fashion",
                "label": "Fashion Campaigns",
                "description": "Fashion and lifestyle advertising",
            },
            {
                "category": "graphic",
                "label": "Brand Identity",
                "description": "Logo and visual identity design",
            },
            {
                "category": "advertising",
                "label": "Digital Marketing",
                "description": "Online and digital advertising trends",
            },
            {
                "category": "material",
                "label": "Packaging Design",
                "description": "Product packaging and material design",
            },
        ],
    }
