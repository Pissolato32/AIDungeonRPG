# filepath: c:\Users\rodri\Desktop\REPLIT RPG\ai\game_ai_client.py
"""Game AI client module.

This module handles AI model interactions for generating game content
and responses."""

import json
import logging
from typing import Protocol  # Added Protocol for AIModelClientType
from typing import Any, Dict, List, Optional, TypedDict, Union, cast

from ai.openrouter import OpenRouterClient  # Import OpenRouterClient
from ai.prompt_builder import InstructionsBuilder, PromptBuilder
from core.game_state_model import GameState, MessageDict
from core.models import Character  # Import Character from core.models

from .fallback_handler import (
    FallbackResponse as FallbackResponseType,  # Importar fallback
)
from .fallback_handler import generate_fallback_response

logger = logging.getLogger(__name__)
from core.game_state_model import (  # Mover importação para evitar potencial ciclo
    GameState,
)


class AIPrompt(TypedDict):
    """Type definition for AI prompt data."""

    role: str
    content: str


class AIResponse(TypedDict):
    """Type definition for AI response data."""

    success: bool
    message: str
    current_detailed_location: str
    scene_description_update: str
    details: Dict[str, Any]  # Detalhes gerais da IA ou do processamento
    error: Optional[str]
    interpreted_action_type: Optional[str]  # Novo: Ação interpretada pela IA
    interpreted_action_details: Optional[
        Dict[str, Any]
    ]  # Novo: Detalhes da ação interpretada
    suggested_roll: Optional[
        Dict[str, Any]
    ]  # Novo: Sugestão de rolagem de dados pela IA
    interactable_elements: Optional[List[str]]  # Novo: Elementos interativos na cena


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
        action: str, details: str, character: Character, game_state: GameState
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
    ) -> AIResponse:
        """
        Handles failures from the primary AI by generating a fallback response.
        """
        logger.warning(
            f"AI failure for action '{action}'. Generating fallback response."
        )
        # O prompt para o fallback pode ser simples, apenas para identificar o tipo de ação.
        # Ou você pode passar o prompt do usuário completo se o fallback_handler for mais sofisticado.
        # Para o fallback_handler atual, uma string simples com ação e detalhes é suficiente.
        fallback_prompt_for_identification = (
            f"{action}: {details if details else 'ação genérica'}"
        )

        fallback_data: FallbackResponseType = generate_fallback_response(
            fallback_prompt_for_identification
        )

        # Construir um AIResponse completo a partir do fallback_data
        # Garantir que todos os campos obrigatórios de AIResponse tenham valores.
        return AIResponse(
            success=fallback_data.get(
                "success", True
            ),  # Fallback geralmente é um "sucesso" em termos de dar uma resposta
            message=fallback_data.get(
                "message", "Ocorreu um problema, mas a aventura continua..."
            ),
            current_detailed_location=fallback_data.get("new_location")
            or game_state.current_location
            or "Local Desconhecido",
            scene_description_update=fallback_data.get("description")
            or game_state.scene_description
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
        )

    def process_action(
        self, action: str, details: str, character: Character, game_state: GameState
    ) -> AIResponse:
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
            return AIResponse(
                success=False,
                message="Erro de configuração: O cliente de IA não está disponível.",
                error="No AI client available",
                # Ensure all required fields of AIResponse are present
                current_detailed_location=game_state.current_location
                or "Indisponível (Erro de Config.)",
                scene_description_update=game_state.scene_description
                or "Indisponível (Erro de Config.)",
                details={},
                interpreted_action_type=None,
                interpreted_action_details=None,
                interactable_elements=None,
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

            from .response_processor import (
                process_ai_response,
                validate_ai_response_structure,
            )

            parsed_ai_dict = process_ai_response(response_from_ai_service)
            logger.info(f"Parsed AI response dictionary: {parsed_ai_dict}")

            # Validar a estrutura da resposta da IA
            if not isinstance(
                parsed_ai_dict, dict
            ) or not validate_ai_response_structure(
                cast(Dict[str, Any], parsed_ai_dict)
            ):
                logger.warning(
                    f"Resposta da IA com estrutura inválida ou campos essenciais faltando: {str(parsed_ai_dict)[:500]}. Usando fallback."
                )
                return self._handle_ai_failure(action, details, game_state)

            # Extrair valores do parsed_ai_dict, preparando para fallbacks
            is_successful = parsed_ai_dict.get("success", False)
            ai_message_val = parsed_ai_dict.get("message")  # Pode ser str ou None
            ai_error_val = parsed_ai_dict.get("error")  # Pode ser str ou None
            ai_current_loc_val = parsed_ai_dict.get(
                "current_detailed_location"
            )  # Pode ser str ou None
            ai_scene_update_val = parsed_ai_dict.get(
                "scene_description_update"
            )  # Pode ser str ou None

            # Determinar final_message garantindo que seja sempre uma string
            if is_successful:
                final_message_str = (
                    ai_message_val
                    or "A ação foi processada, mas a IA não forneceu uma narrativa detalhada."
                )
            else:
                # Se não for bem-sucedido, a mensagem deve refletir o erro.
                # Priorizar a mensagem da IA, depois o detalhe do erro da IA, depois um fallback.
                final_message_str = (
                    ai_message_val
                    or ai_error_val
                    or "Falha ao processar a resposta da IA."
                )

            # Garantir que current_detailed_location seja sempre uma string
            final_current_detailed_location_str = (
                ai_current_loc_val
                or game_state.current_location
                or "Localização Indefinida"
            )

            # Garantir que scene_description_update seja sempre uma string
            final_scene_description_update_str = (
                ai_scene_update_val
                or game_state.scene_description
                or "A cena permanece como antes."
            )

            # Garantir que details seja um dict
            details_data = parsed_ai_dict.get("details")
            if not isinstance(details_data, dict):
                details_data = {}

            # Construir o AIResponse garantindo a conformidade dos tipos
            response_data: AIResponse = {
                "success": is_successful,
                "message": final_message_str,
                "current_detailed_location": final_current_detailed_location_str,
                "scene_description_update": final_scene_description_update_str,
                "details": details_data,
                "error": ai_error_val if not is_successful else None,
                "interpreted_action_type": parsed_ai_dict.get(
                    "interpreted_action_type"
                ),
                "interactable_elements": parsed_ai_dict.get("interactable_elements"),
                "interpreted_action_details": parsed_ai_dict.get(
                    "interpreted_action_details"
                ),
                "suggested_roll": parsed_ai_dict.get(
                    "suggested_roll"
                ),  # Adicionar suggested_roll aqui também
            }

            logger.info(f"Final AIResponse data: {response_data}")
            return response_data  # O cast pode não ser mais estritamente necessário se o mypy inferir corretamente

        except Exception as e:
            logger.error(
                f"Error processing action '{action}' with AI: {e}", exc_info=True
            )
            # Em caso de qualquer exceção durante a tentativa de usar a IA principal,
            # chame o _handle_ai_failure.
            return self._handle_ai_failure(action, details, game_state)
