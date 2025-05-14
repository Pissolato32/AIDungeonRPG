"""
Groq API client module.

This module re-exports the GroqClient class from the ai package
to maintain backward compatibility with existing code.
"""

from ai.groq_client import GroqClient

# Re-export for backward compatibility
__all__ = ['GroqClient']
