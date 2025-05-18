"""
Groq API client module.

This module re-exports the GroqClient class from the ai package
to maintain backward compatibility with existing code.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

import requests  # Você precisará instalar esta biblioteca: pip install requests

logger = logging.getLogger(__name__)


class GroqClient:
    """
    A client to interact with the Groq API.
    """

    api_key: Optional[str]  # Declare class attribute type

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama3-8b-8192",  # Modelo atualizado
    ):
        """
        Initializes the GroqClient.

        Args:
            api_key: Your Groq API key. Defaults to GROQ_API_KEY environment variable.
            model: The model to use for generation.
        """
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            logger.error(
                "Groq API key not found. Please set GROQ_API_KEY environment variable."
            )
            # Você pode querer levantar um erro aqui ou ter um modo de fallback
            # raise ValueError("Groq API key not found.")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = model

    def generate_response(self, prompt_data: Dict[str, Any]) -> str:
        """
        Generates a response from the Groq API based on the prompt data.

        Args:
            prompt_data: A dictionary usually containing 'role' and 'content' for the prompt.
                         Example: {"role": "user", "content": "Your prompt here"}

        Returns:
            A string containing the AI's response, or an error message string in JSON format.
        """
        if not self.api_key:
            logger.error("GroqClient initialized without an API key.")
            return json.dumps(
                {
                    "success": False,
                    "message": "Erro de configuração: Chave da API Groq não fornecida.",
                    "error": "API key missing",
                }
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [prompt_data],  # A API espera uma lista de mensagens
            "temperature": 0.7,  # Ajuste conforme necessário
            # Adicione outros parâmetros como max_tokens se desejar
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, json=payload, timeout=30
            )
            response.raise_for_status()  # Lança um erro para códigos de status 4xx/5xx
            response_json = response.json()
            # A estrutura exata da resposta pode variar, ajuste conforme a documentação do Groq
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

            logger.warning(f"Resposta inesperada da API Groq: {response_json}")
            return json.dumps(
                {
                    "success": False,
                    "message": "Resposta inesperada da IA.",
                    "error": "Unexpected API response structure",
                }
            )
        except requests.exceptions.HTTPError as http_err:
            logger.error(
                f"Erro HTTP ao chamar a API Groq: {http_err.response.status_code} - {http_err.response.text}",
                exc_info=True,
            )
            error_message = f"Erro na API Groq ({http_err.response.status_code})."
            if http_err.response.status_code == 401:
                error_message = (
                    "Erro de autenticação com a API Groq. Verifique sua chave."
                )
            elif http_err.response.status_code == 429:
                error_message = "Limite de taxa da API Groq excedido. Tente mais tarde."
            return json.dumps(
                {
                    "success": False,
                    "message": error_message,
                    "error": str(http_err.response.text),
                }
            )
        except requests.exceptions.RequestException as req_err:
            logger.error(
                f"Erro de requisição ao chamar a API Groq: {req_err}", exc_info=True
            )
            return json.dumps(
                {
                    "success": False,
                    "message": "Erro de conexão com a IA. Verifique sua rede.",
                    "error": str(req_err),
                }
            )
        except Exception as e:
            logger.error(f"Erro inesperado no GroqClient: {e}", exc_info=True)
            return json.dumps(
                {
                    "success": False,
                    "message": "Erro interno ao processar com a IA.",
                    "error": str(e),
                }
            )


# Re-export for backward compatibility
__all__ = ["GroqClient"]
