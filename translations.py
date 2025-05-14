"""
Compatibility module for translations.

This module re-exports the translation functionality from the translations package
to maintain backward compatibility with existing code.
"""

from translations import TranslationManager, get_text, _

# Re-export for backward compatibility
__all__ = ['TranslationManager', 'get_text', '_']