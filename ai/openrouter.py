"""
OpenRouter API client module.

This module provides a client to interact with models via the OpenRouter.ai API.
"""

import os
import json
import logging
import requests  # Você precisará instalar esta biblioteca: pip install requests
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """
    A client to interact with models via the OpenRouter.ai API.
    """

    api_key: Optional[str]  # Declare class attribute type
    site_url: str  # For HTTP-Referer
    app_name: str  # For X-Title

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        site_url: str = "http://localhost:5000",  # Default, customize as needed
        app_name: str = "REPLIT RPG",  # Default, customize as needed
    ):
        """
        Initializes the OpenRouterClient.

        Args:
            api_key: Your OpenRouter API key. Defaults to OPENROUTER_API_KEY environment variable.
            model: The model to use for generation. Defaults to MODEL environment variable or a fallback.
            site_url: The URL of your site/application (for HTTP-Referer header).
            app_name: The name of your application (for X-Title header).
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.error(
                "OpenRouter API key not found. Please set OPENROUTER_API_KEY environment variable."
            )
            # Você pode querer levantar um erro aqui ou ter um modo de fallback
            # raise ValueError("OpenRouter API key not found.")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"  # Endpoint correto para chat
        self.model = (
            model
            or os.environ.get("OPENROUTER_MODEL")
            or "meta-llama/llama-3.3-8b-instruct:free"  # Sugestão: usar OPENROUTER_MODEL para consistência com .env
        )  # Fallback model
        self.site_url = site_url
        self.app_name = app_name

    def generate_response(
        self,
        messages: List[Dict[str, Any]],  # Changed from prompt_data: Dict[str, Any]
        generation_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generates a response from the OpenRouter API based on the prompt data.

        Args:
            messages: A list of message dictionaries, representing the conversation history.
                      Each dictionary should have 'role' and 'content'.
                      Example: [
                          {"role": "user", "content": "Hello"},
                          {"role": "assistant", "content": "Hi there!"},
                          {"role": "user", "content": "What's the weather?"}
                      ]
            generation_params: Optional dictionary of parameters to pass to the API,
                               such as temperature, max_tokens, top_p, etc.

        Returns:
            A string containing the AI's response, or an error message string in JSON format.
        """
        if not self.api_key:
            logger.error("OpenRouterClient initialized without an API key.")
            return json.dumps(
                {
                    "success": False,
                    "message": "Erro de configuração: Chave da API OpenRouter não fornecida.",
                    "error": "API key missing",
                }
            )

        if not messages:  # Adiciona esta verificação
            logger.error(
                "OpenRouterClient.generate_response foi chamado com uma lista de mensagens vazia."
            )
            return json.dumps(
                {
                    "success": False,
                    "message": "Erro interno: Nenhuma mensagem fornecida para a IA.",
                    "error": "Empty messages list",
                }
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
        }

        payload = {
            "model": self.model,
            "messages": messages,  # Use the provided list of messages directly
        }

        # Apply default and then override with provided generation_params
        default_gen_params = {
            "temperature": 0.7,  # Ajustado conforme sua sugestão
            "max_tokens": 450,  # Aumentado um pouco para permitir respostas mais longas
            "presence_penalty": 0.6,  # Conforme sua sugestão
            "frequency_penalty": 0.3,  # Conforme sua sugestão
            "top_p": 0.95,  # Conforme sua sugestão
            # "stop": ["\nJogador:", "Você:", "Mestre:"] # Exemplo de stop sequences
        }  # Sensible defaults
        # As stop sequences podem ser uma lista de strings.
        final_gen_params = {**default_gen_params, **(generation_params or {})}
        payload.update(final_gen_params)

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60,  # Increased timeout for potentially larger models
            )
            response.raise_for_status()  # Lança um erro para códigos de status 4xx/5xx
            response_json = response.json()
            # A estrutura exata da resposta pode variar, ajuste conforme a documentação da OpenRouter/OpenAI
            # Este é um exemplo comum para APIs de chat baseadas em OpenAI
            if response_json.get("choices") and len(response_json["choices"]) > 0:
                message_content = (
                    response_json["choices"][0].get("message", {}).get("content")
                )
                if message_content:
                    # O GameAIClient espera uma string que ele possa processar com process_ai_response
                    # Se a resposta da IA já for um JSON estruturado como AIResponse, retorne-o como string.
                    # Se for apenas texto, o process_ai_response precisará ser adaptado ou você constrói o JSON aqui.
                    # Para simplificar, vamos assumir que a IA retorna o texto da mensagem e o process_ai_response
                    # o envolve em um JSON de sucesso.
                    return (
                        message_content.strip()
                    )  # Retorna apenas o conteúdo da mensagem da IA

            logger.warning(f"Resposta inesperada da API OpenRouter: {response_json}")
            return json.dumps(
                {
                    "success": False,
                    "message": "Resposta inesperada da IA.",
                    "error": "Unexpected API response structure",
                }
            )
        except requests.exceptions.HTTPError as http_err:
            logger.error(
                f"Erro HTTP ao chamar a API OpenRouter: {http_err.response.status_code} - {http_err.response.text}",
                exc_info=True,
            )
            error_message = f"Erro na API OpenRouter ({http_err.response.status_code})."
            if http_err.response.status_code == 401:
                error_message = (
                    "Erro de autenticação com a API OpenRouter. Verifique sua chave."
                )
            elif http_err.response.status_code == 429:
                error_message = (
                    "Limite de taxa da API OpenRouter excedido. Tente mais tarde."
                )
            return json.dumps(
                {
                    "success": False,
                    "message": f"{error_message} Detalhes: {http_err.response.text}",
                    "error": str(http_err.response.text),
                }
            )
        except requests.exceptions.RequestException as req_err:
            logger.error(
                f"Erro de requisição ao chamar a API OpenRouter: {req_err}",
                exc_info=True,
            )
            return json.dumps(
                {
                    "success": False,
                    "message": "Erro de conexão com a IA. Verifique sua rede.",
                    "error": str(req_err),
                }
            )
        except Exception as e:
            logger.error(f"Erro inesperado no OpenRouterClient: {e}", exc_info=True)
            return json.dumps(
                {
                    "success": False,
                    "message": "Erro interno ao processar com a IA.",
                    "error": str(e),
                }
            )


# Re-export for backward compatibility
__all__ = ["OpenRouterClient"]
