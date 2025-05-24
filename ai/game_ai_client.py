# filepath: c:\Users\rodri\Desktop\REPLIT RPG\ai\game_ai_client.py
"""Game AI client module.

This module handles AI model interactions for generating game content
and responses."""

import json
import logging
from typing import Any, Dict, List, Optional, TypedDict, Union, cast
from typing import Protocol

from pydantic import ValidationError

from ai.openrouter import OpenRouterClient  # Import OpenRouterClient
from core.models import Character  # Import Character from core.models
from ai.prompt_builder import PromptBuilder, InstructionsBuilder

from .fallback_handler import (
    generate_fallback_response,
    FallbackResponse as FallbackResponseType,  # Importar fallback
)  # Importar fallback

# Importar schemas Pydantic
from .schemas import AIResponsePydantic

logger = logging.getLogger(__name__)


class AIPrompt(TypedDict):
    """Type definition for AI prompt data."""

    role: str
    content: str


# O TypedDict AIResponse é agora substituído por AIResponsePydantic
# Manterei a definição antiga comentada por um momento para referência durante a refatoração.
# class AIResponse(TypedDict):
#     ... (definição antiga)
from core.game_state_model import (
    GameState,
)  # Movido para cá para resolver import cycle se GameState importar AIResponse


# Define Protocols for external dependencies
class AIModelClientType(Protocol):
    """Protocol for AI model clients that can generate text responses."""

    def generate_response(
        self,
        messages: List[AIPrompt],
        generation_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generates a response from the AI model based on the prompt.

        Args:
            messages: A list of message dictionaries to send to the AI.
            generation_params: Optional dictionary of generation parameters.
        Returns:
            The raw string response from the AI (e.g., a JSON string or plain text).
        """
        ...


class GameAIClient:
    """Client for handling AI model interactions in the game."""

    def __init__(self, ai_client: Optional[AIModelClientType] = None) -> None:
        """Initialize the Game AI Client."""
        self.ai_client = ai_client

    @staticmethod
    def _create_action_prompt(
        action: str,
        details: str,
        character: Character,
        game_state: "GameState",  # Usar string literal para GameState
    ) -> List[AIPrompt]:
        """Create a formatted prompt for the AI model.

        Args:
            action: Type of action being performed
            details: Additional action details
            character: Player character data
            game_state: Current game state

        Returns:
            A list of prompt messages for the AI model, starting with the system prompt.
        """
        # Usa o PromptBuilder para construir o conteúdo do prompt do sistema e do usuário
        system_prompt_content = PromptBuilder.build_system_prompt()
        user_prompt_content = PromptBuilder.build_user_prompt_content(
            action, details, character, game_state
        )

        return [
            AIPrompt(role="system", content=system_prompt_content),
            AIPrompt(role="user", content=user_prompt_content),
        ]

    def _handle_ai_failure(
        self, action: str, details: str, game_state: GameState
    ) -> AIResponsePydantic:  # Alterado para retornar AIResponsePydantic
        """Handles failures from the primary AI.

        Currently, it generates a scripted fallback response.
        Future enhancements could include:
        1. Re-prompting the AI with context about the failure.
        2. Trying a different AI model.
        3. Using more sophisticated fallback logic based on the type of failure.

        Args:
            action: The original action type.
            details: The original action details.
            game_state: The current game state.
            original_bad_response: The problematic raw response from the AI, if available.
            failure_reason: A description of why the AI response failed (e.g., "Invalid JSON", "Missing required fields").
            attempt_reprompt: Whether to attempt a re-prompt to the AI.
        """
        logger.warning(
            f"AI failure for action '{action}'. Generating fallback response."
        )

        # O prompt para o fallback_handler atual é simples, focado em identificar o tipo de ação.
        fallback_prompt_for_identification = (
            f"{action}: {details if details else 'ação genérica'}"
        )

        fallback_data: FallbackResponseType = generate_fallback_response(
            fallback_prompt_for_identification
        )

        # Construir um AIResponsePydantic completo a partir do fallback_data
        # Garantir que todos os campos obrigatórios de AIResponsePydantic tenham valores.
        return AIResponsePydantic(
            success=fallback_data.get(
                "success", True
            ),  # Fallback geralmente é um "sucesso" em termos de dar uma resposta
            message=fallback_data.get(
                "message", "Ocorreu um problema, mas a aventura continua..."
            ),
            current_detailed_location=fallback_data.get("new_location")
            or (game_state.current_location if game_state else "Local Desconhecido")
            or "Local Desconhecido",
            scene_description_update=fallback_data.get("description")
            or (
                game_state.scene_description
                if game_state
                else "A cena parece inalterada."
            )
            or "A cena parece inalterada.",
            details={
                "fallback_details": fallback_data
            },  # Coloca todos os dados do fallback em 'details'
            error="AI_FALLBACK_TRIGGERED",  # Indica que este é um fallback
            interpreted_action_type=fallback_data.get(
                "interpreted_action_type"
            ),  # Se o fallback fornecer
            interpreted_action_details=fallback_data.get(
                "interpreted_action_details"
            ),  # Se o fallback fornecer
            suggested_roll=None,  # Fallbacks simples geralmente não sugerem rolagens
            interactable_elements=fallback_data.get("items")
            or fallback_data.get("npcs"),  # Exemplo
            suggested_location_data=None,  # Adicionar campo faltante
        )

    def process_action(
        self, action: str, details: str, character: Character, game_state: GameState
    ) -> AIResponsePydantic:  # Alterado para retornar AIResponsePydantic
        """Process a player action using AI.

        Args:
            action: Type of action being performed
            details: Additional action details
            character: Player character data
            game_state: Current game state

        Returns:
            AI response containing action results
        """
        logger.info(f"GameAIClient process_action called for: {action} - {details}")
        if not self.ai_client:
            logger.error(
                "AI client (e.g., GroqClient) not initialized in GameAIClient."
            )
            return AIResponsePydantic(
                success=False,
                message="Erro de configuração: O cliente de IA não está disponível.",
                error="No AI client available",
                # Ensure all required fields of AIResponsePydantic are present
                current_detailed_location=(
                    game_state.current_location
                    if game_state
                    else "Indisponível (Erro de Config.)"
                )
                or "Indisponível (Erro de Config.)",
                scene_description_update=(
                    game_state.scene_description
                    if game_state
                    else "Indisponível (Erro de Config.)"
                )
                or "Indisponível (Erro de Config.)",
                details={},
                interpreted_action_type=None,
                interpreted_action_details=None,
                interactable_elements=None,
                suggested_location_data=None,
                suggested_roll=None,  # Adicionado para completar a definição
            )

        try:
            # _create_action_prompt agora retorna uma lista de prompts
            list_of_prompts_for_ai: List[AIPrompt] = self._create_action_prompt(
                action, details, character, game_state
            )
            logger.debug(
                f"Generated AI User Prompt (first 500 chars): {list_of_prompts_for_ai[-1]['content'][:500]}"
            )

            # Você pode definir params específicos para certas ações aqui se desejar
            custom_gen_params = None
            # Exemplo: Se a ação for para gerar uma descrição de local, talvez queira mais criatividade
            if (
                action == "look_around_new_location"
            ):  # Este é um nome de ação hipotético
                custom_gen_params = {"temperature": 0.85, "presence_penalty": 0.4}
            elif action == "interpret_dialogue_heavy":  # Outro exemplo hipotético
                custom_gen_params = {
                    "temperature": 0.6,
                    "stop": ["\nJogador:", "\nVocê:"],
                }

            # Passa a lista de prompts diretamente para o cliente
            response_from_ai_service = self.ai_client.generate_response(
                messages=list_of_prompts_for_ai,
                generation_params=custom_gen_params,  # Passa os params personalizados ou None
            )
            logger.debug(
                f"Raw response from AI service type: {type(response_from_ai_service)}, content: {str(response_from_ai_service)[:500]}"
            )  # Importar validate_ai_response_structure

            # Usar response_processor apenas para extrair o JSON bruto
            from .response_processor import extract_json_from_text

            json_extraction_result = extract_json_from_text(response_from_ai_service)

            if not json_extraction_result.data:
                logger.warning(
                    f"Não foi possível extrair JSON da resposta da IA. Erro: {json_extraction_result.error}. Resposta bruta: {response_from_ai_service[:200]}. Usando fallback."
                )
                return self._handle_ai_failure(action, details, game_state)

            extracted_json_data = json_extraction_result.data
            logger.info(f"Extracted JSON from AI: {extracted_json_data}")

            try:
                validated_response = AIResponsePydantic(**extracted_json_data)
                logger.info(
                    f"Validated AIResponsePydantic data: {validated_response.model_dump_json(indent=2)}"
                )
                return validated_response
            except ValidationError as e:
                logger.warning(
                    f"Resposta da IA falhou na validação do schema Pydantic: {e}. JSON extraído: {extracted_json_data}. Usando fallback."
                )
                # Poderíamos tentar um re-prompt aqui no futuro, passando 'e' como failure_reason
                return self._handle_ai_failure(action, details, game_state)
            except (
                TypeError
            ) as te:  # Captura erros se extracted_json_data não for um dict (ex: None)
                logger.warning(
                    f"TypeError ao tentar validar resposta da IA (provavelmente JSON não era um dict): {te}. JSON extraído: {extracted_json_data}. Usando fallback."
                )
                return self._handle_ai_failure(action, details, game_state)

        except Exception as e:
            logger.error(
                f"Error processing action '{action}' with AI: {e}", exc_info=True
            )
            # Em caso de qualquer exceção durante a tentativa de usar a IA principal,
            # chame o _handle_ai_failure.
            return self._handle_ai_failure(action, details, game_state)
