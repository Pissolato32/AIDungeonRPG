"""
Game AI client module.

This module provides functionality for interacting with AI models for game responses.
"""

import logging
import json
import random
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class GameAIClient:
    """
    Client for interacting with AI models to generate game responses.
    """
    
    def __init__(self, ai_client=None):
        """
        Initialize the Game AI Client.
        
        Args:
            ai_client: External AI client to use (optional)
        """
        self.ai_client = ai_client
        self.system_prompt = """
        Você é o mestre de um jogo de RPG de fantasia medieval. Sua tarefa é responder às ações do jogador
        de forma imersiva e detalhada, criando uma experiência de jogo envolvente.
        
        Regras:
        1. Responda sempre como se fosse o narrador do jogo
        2. Seja descritivo e use linguagem imersiva
        3. Mantenha a consistência com o mundo de fantasia medieval
        4. Adapte-se ao contexto atual do jogador
        5. Crie NPCs interessantes e locais detalhados
        6. Responda SEMPRE em português do Brasil
        7. Nunca responda com "Você realizou a ação X: Y" - seja criativo e detalhado
        8. Descreva o que o jogador vê, ouve, sente e experimenta
        
        Responda no formato JSON:
        {
            "success": true/false,
            "message": "Descrição detalhada da resposta à ação do jogador",
            "new_location": "Nome do novo local (se o jogador se moveu)",
            "description": "Descrição do novo local (se aplicável)",
            "npcs": ["NPC 1", "NPC 2"],
            "events": ["Evento 1", "Evento 2"]
        }
        """
    
    def process_player_action(self, action: str, details: str, character: Any, game_state: Any) -> Dict[str, Any]:
        """
        Process a player action using AI.
        
        Args:
            action: Type of action (move, look, talk, etc.)
            details: Details of the action
            character: Player character data
            game_state: Current game state
            
        Returns:
            AI response as a dictionary
        """
        if not self.ai_client:
            # Fallback response if no AI client is available
            return self._generate_fallback_response(action, details, game_state)
        
        try:
            # Create prompt for AI
            prompt = self._create_action_prompt(action, details, character, game_state)
            
            # Get response from AI
            response = self.ai_client.generate_response(prompt)
            
            # Process the response
            from ai.response_processor import process_ai_response
            result = process_ai_response(response)
            
            # Ensure the response has the required fields
            if isinstance(result, dict):
                if "success" not in result:
                    result["success"] = True
                return result
            else:
                # If response is not a dict, wrap it
                return {"success": True, "message": str(result)}
                
        except Exception as e:
            logger.error(f"Error processing action with AI: {e}")
            return self._generate_fallback_response(action, details, game_state)
    
    def _create_action_prompt(self, action: str, details: str, character: Any, game_state: Any) -> str:
        """
        Create a prompt for the AI based on the player's action and game state.
        
        Args:
            action: Type of action
            details: Details of the action
            character: Player character data
            game_state: Current game state
            
        Returns:
            Formatted prompt string
        """
        # Extract character attributes
        char_dict = {
            "name": getattr(character, "name", "Aventureiro"),
            "race": getattr(character, "race", "Humano"),
            "class": getattr(character, "character_class", "Guerreiro"),
            "level": getattr(character, "level", 1),
            "strength": getattr(character, "strength", 10),
            "dexterity": getattr(character, "dexterity", 10),
            "constitution": getattr(character, "constitution", 10),
            "intelligence": getattr(character, "intelligence", 10),
            "wisdom": getattr(character, "wisdom", 10),
            "charisma": getattr(character, "charisma", 10),
            "inventory": getattr(character, "inventory", [])
        }
        
        # Extract game state information
        state_dict = {
            "current_location": game_state.current_location,
            "description": game_state.scene_description,
            "npcs_present": game_state.npcs_present,
            "events": game_state.events,
            "messages": game_state.messages[-5:] if hasattr(game_state, "messages") and game_state.messages else []
        }
        
        # Create the prompt with detailed context
        prompt = f"""
        {self.system_prompt}
        
        # Contexto Atual
        - Localização: {state_dict['current_location']}
        - Descrição: {state_dict['description']}
        - NPCs presentes: {', '.join(state_dict['npcs_present']) if state_dict['npcs_present'] else 'Nenhum'}
        - Eventos: {', '.join(state_dict['events']) if state_dict['events'] else 'Nenhum'}
        
        # Personagem do Jogador
        - Nome: {char_dict['name']}
        - Raça: {char_dict['race']}
        - Classe: {char_dict['class']}
        - Nível: {char_dict['level']}
        - Força: {char_dict['strength']}
        - Destreza: {char_dict['dexterity']}
        - Constituição: {char_dict['constitution']}
        - Inteligência: {char_dict['intelligence']}
        - Sabedoria: {char_dict['wisdom']}
        - Carisma: {char_dict['charisma']}
        - Inventário: {', '.join(char_dict['inventory']) if char_dict['inventory'] else 'Vazio'}
        
        # Histórico Recente
        {self._format_recent_messages(state_dict['messages'])}
        
        # Ação do Jogador
        O jogador está tentando: {action}: {details}
        
        Responda à ação do jogador de forma imersiva e detalhada, mantendo o formato JSON especificado.
        Lembre-se de NUNCA responder com "Você realizou a ação X: Y" - seja criativo e detalhado.
        """
        
        return prompt
    
    def _format_recent_messages(self, messages: List[str]) -> str:
        """Format recent messages for context."""
        if not messages:
            return "Nenhuma interação recente."
        
        formatted = "Interações recentes:\n"
        for i, msg in enumerate(messages):
            formatted += f"- {msg}\n"
        return formatted
    
    def _generate_fallback_response(self, action: str, details: str, game_state: Any) -> Dict[str, Any]:
        """
        Generate a fallback response when AI is not available.
        
        Args:
            action: Type of action
            details: Details of the action
            game_state: Current game state
            
        Returns:
            Fallback response dictionary
        """
        # Import fallback handler if available
        try:
            from ai.fallback_handler import generate_fallback_response
            return generate_fallback_response(f"{action}: {details}")
        except ImportError:
            # Basic fallback responses by action type
            fallback_responses = {
                "move": [
                    "Você se move cautelosamente pela área, observando os arredores com atenção.",
                    "Seus passos ecoam enquanto você avança pelo caminho indicado.",
                    "Você segue adiante, sentindo o terreno sob seus pés mudar sutilmente."
                ],
                "look": [
                    "Você examina o ambiente com cuidado, notando pequenos detalhes antes despercebidos.",
                    "Seus olhos percorrem o local, absorvendo cada detalhe da cena à sua frente.",
                    "Você observa atentamente, buscando qualquer coisa que possa ser importante."
                ],
                "talk": [
                    "A conversa flui naturalmente, embora você sinta que há mais a ser descoberto.",
                    "Seu interlocutor responde de forma educada, mas parece guardar alguns segredos.",
                    "As palavras são trocadas com cautela, como se ambos estivessem medindo cada resposta."
                ],
                "search": [
                    "Você procura minuciosamente, mas não encontra nada de especial desta vez.",
                    "Sua busca revela apenas o comum e o esperado, nada que chame a atenção.",
                    "Apesar de seu esforço, nada incomum é encontrado durante sua busca."
                ]
            }
            
            responses = fallback_responses.get(action, [
                "Você tenta a ação, mas o resultado não é imediatamente claro.",
                "Sua tentativa parece ter algum efeito, mas é difícil determinar exatamente qual.",
                "O ambiente responde à sua ação de forma sutil e ambígua."
            ])
            
            return {
                "success": True,
                "message": random.choice(responses)
            }