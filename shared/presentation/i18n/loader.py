"""i18n key loader for existing static/i18n/*.json files."""
import json
from pathlib import Path
from typing import Any

# Supported languages
LANGUAGES = ['ko', 'en', 'zh-CN', 'zh-TW']

# Cache for loaded translations
_translation_cache: dict[str, dict[str, Any]] = {}


def load_i18n_keys(language: str = 'ko') -> dict[str, Any]:
    """Load i18n keys for a language from static/i18n/{language}.json.

    Args:
        language: Language code (ko, en, zh-CN, zh-TW)

    Returns:
        Dictionary of translation keys

    Raises:
        ValueError: If language is not supported
    """
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language}. Supported: {LANGUAGES}")

    # Check cache
    if language in _translation_cache:
        return _translation_cache[language]

    # Load from file
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    file_path = base_dir / 'static' / 'i18n' / f'{language}.json'

    if not file_path.exists():
        # Return empty dict if file doesn't exist
        _translation_cache[language] = {}
        return {}

    with open(file_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)

    # Cache and return
    _translation_cache[language] = translations
    return translations


def translate(key: str, language: str = 'ko', **kwargs: Any) -> str:
    """Get translation for a key.

    Args:
        key: Translation key (supports dot notation like 'common.save')
        language: Language code
        **kwargs: Variables for string formatting

    Returns:
        Translated string with variables applied

    Examples:
        >>> translate('common.save', language='ko')
        '저장'
        >>> translate('common.greeting', language='en', name='John')
        'Hello, John!'
    """
    translations = load_i18n_keys(language)

    # Navigate using dot notation
    parts = key.split('.')
    value = translations

    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            # Key not found, return the key itself
            return key

    # Apply variables if it's a string
    if isinstance(value, str) and kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, ValueError):
            return value

    return value if isinstance(value, str) else key


def get_supported_languages() -> list[str]:
    """Get list of supported language codes."""
    return LANGUAGES.copy()


def clear_cache() -> None:
    """Clear translation cache (useful for testing)."""
    _translation_cache.clear()
