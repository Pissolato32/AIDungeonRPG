"""
Groq API client module.

This module re-exports the GroqClient class from the ai package
to maintain backward compatibility with existing code.
"""


class GroqClient:
    """
    Placeholder GroqClient implementation.
    Replace this with actual API integration as needed.
    """

    def generate_response(self, prompt: str) -> str:
        # Simula indisponibilidade da IA
        return '{"success": false, "message": "A inteligência artificial está temporariamente indisponível. Tente novamente mais tarde."}'


# Re-export for backward compatibility
__all__ = ["GroqClient"]
