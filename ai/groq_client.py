"""
Groq API client module.

This module provides a client for interacting with the Groq API.
"""

import os
import logging
import time
from typing import Dict, Any, Optional, Union

import requests
from dotenv import load_dotenv

from .conversation_manager import ConversationManager
from .response_processor import process_ai_response
from .fallback_handler import generate_fallback_response

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)


class GroqClient:
    """
    Client for interacting with the Groq API, managing conversations and generating responses.
    
    Features:
    - Conversation history management
    - Token limit control
    - Error handling
    - Support for multiple languages and characters
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_history_length: int = 20
    ):
        """
        Initialize the Groq client.
        
        Args:
            api_key: API key (optional, fetched from environment if not provided)
            model: AI model to use
            max_history_length: Maximum number of messages in history
        """
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = model or os.environ.get("MODEL", "llama2-70b-4096")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # Validate API key
        if not self.api_key:
            raise EnvironmentError("GROQ_API_KEY not configured")
        
        # Create conversation manager
        self.conversation_manager = ConversationManager(max_history_length=max_history_length)
        
        # Configure security and performance settings
        self.request_timeout = 15  # seconds
        self.retry_delay = 2  # seconds between attempts
        self.max_retries = 3
    
    def generate_response(
        self,
        prompt: str,
        character_id: str = "default"
    ) -> Union[Dict[str, Any], str]:
        """
        Generate a response using the Groq API.
        
        Args:
            prompt: Input prompt
            character_id: Character identifier
            
        Returns:
            Processed response (dictionary or string)
        """
        # Add prompt to conversation history
        self.conversation_manager.add_user_message(character_id, prompt)
        
        # Get conversation history
        conversation_history = self.conversation_manager.get_conversation_history(character_id)
        
        # Prepare API request
        payload = self._prepare_api_payload(conversation_history)
        headers = self._prepare_api_headers()
        
        # Make API request with retries
        for attempt in range(self.max_retries):
            try:
                response = self._make_api_request(headers, payload)
                
                # Process successful response
                if "choices" in response and response["choices"]:
                    message = response["choices"][0]["message"]["content"]
                    
                    # Add response to conversation history
                    self.conversation_manager.add_assistant_message(character_id, message)
                    
                    # Process and return response
                    return process_ai_response(message)
                
                logger.warning("Response does not contain valid choices")
                return generate_fallback_response(prompt)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error (attempt {attempt + 1}): {e}")
                
                # If last attempt, generate fallback response
                if attempt == self.max_retries - 1:
                    return generate_fallback_response(prompt)
                
                # Pause before next attempt
                time.sleep(self.retry_delay)
        
        # If all attempts fail
        return generate_fallback_response(prompt)
    
    def _prepare_api_payload(self, conversation_history: list) -> Dict[str, Any]:
        """
        Prepare the API request payload.
        
        Args:
            conversation_history: Conversation history
            
        Returns:
            API request payload
        """
        return {
            "model": self.model,
            "messages": conversation_history,
            "temperature": 0.7,  # Default value for creativity
            "max_tokens": 1024   # Token limit
        }
    
    def _prepare_api_headers(self) -> Dict[str, str]:
        """
        Prepare the API request headers.
        
        Returns:
            API request headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_api_request(self, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make an API request to Groq.
        
        Args:
            headers: Request headers
            payload: Request payload
            
        Returns:
            API response data
            
        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=self.request_timeout
        )
        
        # Raise exception for HTTP errors
        response.raise_for_status()
        
        # Return JSON response
        return response.json()
    
    def set_system_message(self, system_message: str) -> None:
        """
        Set the system message for conversations.
        
        Args:
            system_message: System message content
        """
        self.conversation_manager.set_system_message({
            "role": "system",
            "content": system_message
        })
    
    def reset_conversation(self, character_id: str) -> None:
        """
        Reset the conversation history for a character.
        
        Args:
            character_id: Character identifier
        """
        self.conversation_manager.reset_conversation(character_id)