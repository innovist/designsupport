"""Sample trend source definitions.

Common design and fashion industry sources.
"""


def get_sample_sources() -> list[dict]:
    """Get sample trend source definitions.

    Returns:
        List of source definitions
    """
    return [
        {
            "name": "Dezeen",
            "url": "https://www.dezeen.com/",
            "domain": "industrial",
            "crawl_schedule": "0 */6 * * *",  # Every 6 hours
            "trust_level": "high",
            "license": "editorial",
        },
        {
            "name": "Design Milk",
            "url": "https://design-milk.com/",
            "domain": "industrial",
            "crawl_schedule": "0 */6 * * *",
            "trust_level": "high",
            "license": "editorial",
        },
        {
            "name": "WGSN",
            "url": "https://www.wgsn.com/",
            "domain": "fashion",
            "crawl_schedule": "0 2 * * *",  # Daily at 2 AM
            "trust_level": "high",
            "license": "subscription",
            "active": False,  # Requires authentication
        },
        {
            "name": "Vogue Runway",
            "url": "https://www.vogue.com/fashion-shows",
            "domain": "fashion",
            "crawl_schedule": "0 2 * * *",
            "trust_level": "high",
            "license": "editorial",
        },
        {
            "name": "Behance",
            "url": "https://www.behance.net/",
            "domain": "visual",
            "crawl_schedule": "0 */6 * * *",
            "trust_level": "medium",
            "license": "community",
        },
        {
            "name": "Dribbble",
            "url": "https://dribbble.com/",
            "domain": "visual",
            "crawl_schedule": "0 */6 * * *",
            "trust_level": "medium",
            "license": "community",
        },
        {
            "name": "AdWeek",
            "url": "https://www.adweek.com/",
            "domain": "advertising",
            "crawl_schedule": "0 */6 * * *",
            "trust_level": "high",
            "license": "editorial",
        },
        {
            "name": "Campaign Asia",
            "url": "https://www.campaignasia.com/",
            "domain": "advertising",
            "crawl_schedule": "0 */6 * * *",
            "trust_level": "high",
            "license": "editorial",
        },
    ]
