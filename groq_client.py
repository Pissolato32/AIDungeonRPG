import os
import json
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class GroqClient:
    """Client for interacting with the Groq API"""
    
    def __init__(self):
        """Initialize the Groq client with API key from environment"""
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "mixtral-8x7b-32768"  # Updated to a model available in Groq
        self.conversation_history = {}  # Store conversation history per character
    
    def generate_response(self, prompt, character_id="default"):
        """Generate a response using the Groq API"""
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. Using fallback response.")
            return self._generate_fallback_response(prompt)
        
        # Initialize history for this character if not exists
        if character_id not in self.conversation_history:
            self.conversation_history[character_id] = []
        
        # Add prompt to history
        self.conversation_history[character_id].append({
            "role": "user",
            "content": prompt
        })
        
        # Keep history limited to last 10 messages
        if len(self.conversation_history[character_id]) > 10:
            self.conversation_history[character_id] = self.conversation_history[character_id][-10:]
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": self.conversation_history[character_id],
                "temperature": 0.7,
                "max_tokens": 1024
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                result = response_data["choices"][0]["message"]["content"]
                
                # Add response to history
                self.conversation_history[character_id].append({
                    "role": "assistant",
                    "content": result
                })
                
                return result
            else:
                logger.error(f"Unexpected response format: {response_data}")
                return self._generate_fallback_response(prompt)
                
        except Exception as e:
            logger.error(f"Error generating response from Groq API: {str(e)}")
            return self._generate_fallback_response(prompt)
    
    def _generate_fallback_response(self, prompt):
        """Generate a fallback response when API is unavailable"""
        # Check if prompt is asking for JSON
        if "JSON" in prompt and "format" in prompt:
            # Simple JSON fallback for common scenarios
            if "move" in prompt.lower():
                return json.dumps({
                    "success": True,
                    "new_location": "Forest Path",
                    "description": "You walk along a winding path through a dense forest. Tall trees tower above you, and sunlight filters through the leaves.",
                    "npcs": ["Wandering Merchant"],
                    "events": ["A gentle breeze rustles the leaves."],
                    "message": "You move along the forest path.",
                    "combat": False
                })
            elif "look" in prompt.lower():
                return json.dumps({
                    "success": True,
                    "description": "You examine your surroundings carefully.",
                    "observations": ["The area seems peaceful."],
                    "message": "You look around and take in the details of your surroundings."
                })
            elif "talk" in prompt.lower():
                return json.dumps({
                    "success": True,
                    "dialogue": "Greetings, traveler! What brings you to these parts?",
                    "information": ["The village to the east has been having trouble with bandits."],
                    "quests": [{
                        "name": "Clear the Bandit Camp",
                        "description": "Defeat the bandits that have been troubling the village."
                    }],
                    "message": "The NPC greets you warmly and shares some information."
                })
            elif "search" in prompt.lower():
                return json.dumps({
                    "success": True,
                    "items": ["Small Health Potion"],
                    "gold": 5,
                    "secrets": ["There seems to be a hidden path to the north."],
                    "message": "You search the area and find a small health potion and 5 gold coins.",
                    "combat": False
                })
            elif "enemy" in prompt.lower():
                return json.dumps({
                    "enemy": {
                        "name": "Forest Wolf",
                        "description": "A large wolf with grey fur and sharp teeth.",
                        "level": 1,
                        "max_hp": 15,
                        "current_hp": 15,
                        "attack_damage": [2, 5],
                        "defense": 1,
                        "experience_reward": 30,
                        "gold_reward": [3, 8],
                        "loot_table": ["Wolf Pelt", "Sharp Tooth"]
                    },
                    "message": "A forest wolf approaches, growling menacingly!"
                })
            else:
                return json.dumps({
                    "success": True,
                    "description": "The action seems to work.",
                    "effects": {
                        "hp_change": 0,
                        "stamina_change": 0,
                        "gold_change": 0,
                        "items_gained": [],
                        "items_lost": []
                    },
                    "message": "You perform the action successfully."
                })
        else:
            # Generic text response
            return "The system processes your request and provides a response."
