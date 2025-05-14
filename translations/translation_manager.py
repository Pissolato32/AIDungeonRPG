"""
Translation manager module.

This module provides functionality for managing translations in the game.
"""

import logging
from typing import Dict, Any, Optional, Union, List
from .translation_data import TRANSLATIONS, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)


class TranslationManager:
    """
    Advanced translation manager with support for multiple languages.

    Features:
    - Dynamic translation loading
    - Fallback to default language
    - Translation caching
    - Logging of missing keys
    - Support for formatting with positional and named arguments
    - Translation of complete sections
    """

    # Default language for fallback
    DEFAULT_LANGUAGE = DEFAULT_LANGUAGE

    # Translations are imported from translation_data module
    TRANSLATIONS = TRANSLATIONS

    # Cache for processed translations
    _translation_cache: Dict[str, str] = {}

    @classmethod
    def get_text(
        cls,
        key: str,
        lang: str = None,
        *args: Union[str, int, float],
        **kwargs: Union[str, int, float]
    ) -> str:
        """
        Get translated text with formatting support.

        Args:
            key: Translation key (can be nested with dots)
            lang: Language code (uses default language if None)
            *args: Positional arguments for formatting
            **kwargs: Named arguments for formatting

        Returns:
            Translated text
        """
        # Normalize and validate language
        lang = cls._normalize_language(lang)

        # Check cache for non-formatted strings
        cache_key = f"{lang}:{key}"
        if cache_key in cls._translation_cache and not (args or kwargs):
            return cls._translation_cache[cache_key]

        # Get translation from nested dictionary
        translation = cls._get_nested_translation(key, lang)

        # If translation not found, return the key itself
        if translation is None:
            return key

        # Convert to string to ensure formatting works
        translation_str = str(translation)

        # Cache non-formatted strings
        if not (args or kwargs):
            cls._translation_cache[cache_key] = translation_str

        # Format with arguments if provided
        return cls._format_translation(translation_str, key, args, kwargs)

    @classmethod
    def _normalize_language(cls, lang: Optional[str]) -> str:
        """
        Normalize and validate language code.

        Args:
            lang: Language code or None

        Returns:
            Normalized language code
        """
        # Use default language if None
        if lang is None:
            return cls.DEFAULT_LANGUAGE

        # Normalize language code
        lang = lang.lower()

        # Fallback to default language if not supported
        if lang not in cls.TRANSLATIONS:
            logger.warning(f"Unsupported language: {lang}. Using {cls.DEFAULT_LANGUAGE}.")
            return cls.DEFAULT_LANGUAGE

        return lang

    @classmethod
    def _get_nested_translation(cls, key: str, lang: str) -> Optional[Any]:
        """
        Get translation from nested dictionary structure.

        Args:
            key: Translation key (can be nested with dots)
            lang: Language code

        Returns:
            Translation value or None if not found
        """
        # Navigate through nested dictionary
        translation = cls.TRANSLATIONS[lang]
        for k in key.split('.'):
            try:
                translation = translation[k]
            except (KeyError, TypeError):
                # Log missing key
                logger.warning(f"Translation key not found: {key} in {lang}")
                return None

        return translation

    @classmethod
    def _format_translation(
        cls, 
        translation: str, 
        key: str,
        args: tuple,
        kwargs: dict
    ) -> str:
        """
        Format translation with arguments.

        Args:
            translation: Translation string
            key: Original key (for error logging)
            args: Positional arguments
            kwargs: Named arguments

        Returns:
            Formatted translation
        """
        try:
            if args and kwargs:
                return translation.format(*args, **kwargs)
            elif args:
                return translation.format(*args)
            elif kwargs:
                return translation.format(**kwargs)
            else:
                return translation
        except (IndexError, KeyError, ValueError) as e:
            logger.error(f"Error formatting '{key}': {e}")
            return translation

    @classmethod
    def add_translation(
        cls,
        key: str,
        translation: str,
        lang: str = None
    ) -> None:
        """
        Add a translation dynamically.

        Args:
            key: Translation key
            translation: Translated text
            lang: Language code (uses default language if None)
        """
        # Normalize language
        lang = cls._normalize_language(lang)

        # Create language dictionary if it doesn't exist
        if lang not in cls.TRANSLATIONS:
            cls.TRANSLATIONS[lang] = {}

        # Support nested keys
        keys = key.split('.')
        current = cls.TRANSLATIONS[lang]

        # Navigate to the correct nesting level
        for k in keys[:-1]:
            current = current.setdefault(k, {})

        # Set the translation
        current[keys[-1]] = translation

        # Invalidate cache
        cls._clear_cache(lang)

    @classmethod
    def _clear_cache(cls, lang: Optional[str] = None) -> None:
        """
        Clear translation cache.

        Args:
            lang: Language code (optional, clears all if None)
        """
        if lang:
            # Remove specific language entries
            cls._translation_cache = {
                k: v for k, v in cls._translation_cache.items()
                if not k.startswith(f"{lang}:")
            }
        else:
            # Clear entire cache
            cls._translation_cache.clear()

    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """
        Get list of supported languages.

        Returns:
            List of language codes
        """
        return list(cls.TRANSLATIONS.keys())

    @classmethod
    def translate_section(
        cls,
        section: str,
        source_lang: str = None,
        target_lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Translate a complete section.

        Args:
            section: Section to translate (like 'combat', 'items')
            source_lang: Source language (uses default language if None)
            target_lang: Target language

        Returns:
            Dictionary of translations
        """
        try:
            # Normalize languages
            source_lang = cls._normalize_language(source_lang)
            target_lang = cls._normalize_language(target_lang)

            # Get source and target sections
            source_section = cls._get_nested_translation(section, source_lang)
            target_section = cls._get_nested_translation(section, target_lang)

            if source_section is None:
                return {}

            # Handle dictionary sections
            if isinstance(source_section, dict):
                return cls._translate_dict_section(
                    section, source_section, target_section, source_lang, target_lang
                )
            else:
                # For simple values
                return target_section or source_section

        except Exception as e:
            logger.error(f"Error translating section: {e}")
            return {}

    @classmethod
    def _translate_dict_section(
        cls,
        section_path: str,
        source_section: Dict[str, Any],
        target_section: Optional[Dict[str, Any]],
        source_lang: str,
        target_lang: str
    ) -> Dict[str, Any]:
        """
        Translate a dictionary section recursively.

        Args:
            section_path: Path to the section
            source_section: Source section dictionary
            target_section: Target section dictionary
            source_lang: Source language
            target_lang: Target language

        Returns:
            Translated section dictionary
        """
        # Initialize result
        translated_section = {}

        # Use empty dict if target section is None
        target_section = target_section or {}

        # Process each key in source section
        for k, v in source_section.items():
            if isinstance(v, dict) and k in target_section and isinstance(target_section[k], dict):
                # Recursively translate nested sections
                translated_section[k] = cls.translate_section(
                    f"{section_path}.{k}", source_lang, target_lang
                )
            else:
                # Use target translation if available, otherwise use source
                translated_section[k] = target_section.get(k, v)

        return translated_section


# Global function for compatibility
def get_text(
    key: str, 
    lang: str = TranslationManager.DEFAULT_LANGUAGE, 
    *args: Union[str, int, float], 
    **kwargs: Union[str, int, float]
) -> str:
    """
    Wrapper for class method to maintain compatibility.

    Args:
        key: Translation key
        lang: Language code
        *args: Positional arguments for formatting
        **kwargs: Named arguments for formatting

    Returns:
        Translated text
    """
    return TranslationManager.get_text(key, lang, *args, **kwargs)


# Alias for easier use
_ = get_text
