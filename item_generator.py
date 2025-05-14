"""
Item Generator for the RPG game.

This module handles procedural generation of items with consistent attributes.
"""

import random
import json
import os
import logging
from typing import Dict, List, Any, Optional
from groq_client import GroqClient

logger = logging.getLogger(__name__)

class ItemGenerator:
    """Handles procedural generation of items with consistent attributes."""
    
    # Item types
    ITEM_TYPES = {
        "weapon": ["sword", "axe", "dagger", "bow", "staff", "mace", "spear", "hammer"],
        "armor": ["helmet", "chestplate", "gauntlets", "boots", "shield"],
        "consumable": ["potion", "food", "scroll", "elixir"],
        "material": ["ore", "herb", "gem", "leather", "cloth", "wood"],
        "quest": ["key", "artifact", "document", "map", "letter"]
    }
    
    # Item rarities and their modifiers
    RARITIES = {
        "common": {"modifier": 1.0, "chance": 0.6},
        "uncommon": {"modifier": 1.5, "chance": 0.25},
        "rare": {"modifier": 2.0, "chance": 0.1},
        "epic": {"modifier": 3.0, "chance": 0.04},
        "legendary": {"modifier": 5.0, "chance": 0.01}
    }
    
    # Item prefixes for different attributes
    PREFIXES = {
        "damage": ["Sharp", "Deadly", "Fierce", "Brutal", "Savage"],
        "defense": ["Sturdy", "Reinforced", "Protective", "Solid", "Impenetrable"],
        "magic": ["Enchanted", "Arcane", "Mystical", "Magical", "Ethereal"],
        "health": ["Vital", "Healthy", "Robust", "Vigorous", "Hearty"],
        "stamina": ["Energetic", "Enduring", "Tireless", "Invigorating", "Revitalizing"]
    }
    
    # Item suffixes for different attributes
    SUFFIXES = {
        "damage": ["of Slaying", "of Destruction", "of Power", "of Might", "of Strength"],
        "defense": ["of Protection", "of Shielding", "of Warding", "of Guarding", "of Defense"],
        "magic": ["of Sorcery", "of Wizardry", "of Magic", "of Spells", "of Enchantment"],
        "health": ["of Vitality", "of Life", "of Healing", "of Regeneration", "of Mending"],
        "stamina": ["of Endurance", "of Energy", "of Vigor", "of Stamina", "of Persistence"]
    }
    
    def __init__(self, data_dir: str):
        """
        Initialize the item generator.
        
        Args:
            data_dir: Directory to store item data
        """
        self.data_dir = data_dir
        self.items_file = os.path.join(data_dir, "items_database.json")
        self.ai_client = GroqClient()
        self.items_db = self.load_items_database()
    
    def load_items_database(self) -> Dict[str, Any]:
        """
        Load the items database from file.
        
        Returns:
            Items database dictionary
        """
        if os.path.exists(self.items_file):
            try:
                with open(self.items_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading items database: {e}")
        
        # Return empty database if file doesn't exist or has errors
        return {
            "items": {},
            "metadata": {
                "version": "1.0",
                "created": "procedural"
            }
        }
    
    def save_items_database(self) -> bool:
        """
        Save the items database to file.
        
        Returns:
            Success status
        """
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.items_file, 'w', encoding='utf-8') as f:
                json.dump(self.items_db, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving items database: {e}")
            return False
    
    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an item by its ID.
        
        Args:
            item_id: Item ID
            
        Returns:
            Item data or None if not found
        """
        return self.items_db.get("items", {}).get(item_id)
    
    def get_item_by_name(self, item_name: str) -> Optional[Dict[str, Any]]:
        """
        Get an item by its name.
        
        Args:
            item_name: Item name
            
        Returns:
            Item data or None if not found
        """
        for item_id, item_data in self.items_db.get("items", {}).items():
            if item_data.get("name", "").lower() == item_name.lower():
                return item_data
        return None
    
    def generate_item_id(self, item_name: str) -> str:
        """
        Generate a unique ID for an item.
        
        Args:
            item_name: Item name
            
        Returns:
            Unique item ID
        """
        base_id = item_name.lower().replace(" ", "_")
        item_id = base_id
        counter = 1
        
        # Ensure ID is unique
        while item_id in self.items_db.get("items", {}):
            item_id = f"{base_id}_{counter}"
            counter += 1
        
        return item_id
    
    def generate_weapon(self, level: int = 1, rarity: str = None) -> Dict[str, Any]:
        """
        Generate a weapon.
        
        Args:
            level: Character level
            rarity: Item rarity (if None, will be randomly selected)
            
        Returns:
            Weapon data
        """
        # Select rarity if not provided
        if not rarity:
            rarity = self._select_rarity()
        
        # Select weapon type
        weapon_type = random.choice(self.ITEM_TYPES["weapon"])
        
        # Generate base stats based on level and rarity
        rarity_mod = self.RARITIES[rarity]["modifier"]
        base_damage_min = max(1, int((level * 1.5) * rarity_mod))
        base_damage_max = max(2, int((level * 2.5) * rarity_mod))
        
        # Select attribute focus
        attribute = random.choice(["damage", "magic", "stamina"])
        
        # Generate name with prefix and/or suffix
        if random.random() < 0.7:  # 70% chance for special name
            if random.random() < 0.5:  # 50% chance for prefix only
                name = f"{random.choice(self.PREFIXES[attribute])} {weapon_type.capitalize()}"
            else:  # 50% chance for suffix only
                name = f"{weapon_type.capitalize()} {random.choice(self.SUFFIXES[attribute])}"
        else:  # 30% chance for basic name
            name = weapon_type.capitalize()
        
        # Generate durability
        durability = int(50 * rarity_mod)
        
        # Generate item data
        item_data = {
            "name": name,
            "type": "weapon",
            "subtype": weapon_type,
            "rarity": rarity,
            "level": level,
            "damage": [base_damage_min, base_damage_max],
            "durability": durability,
            "attributes": {
                attribute: int(level * rarity_mod)
            },
            "description": self._generate_item_description(name, weapon_type, rarity, attribute)
        }
        
        # Generate unique ID
        item_id = self.generate_item_id(name)
        
        # Add to database
        if "items" not in self.items_db:
            self.items_db["items"] = {}
        self.items_db["items"][item_id] = item_data
        
        # Save database
        self.save_items_database()
        
        return item_data
    
    def generate_armor(self, level: int = 1, rarity: str = None) -> Dict[str, Any]:
        """
        Generate armor.
        
        Args:
            level: Character level
            rarity: Item rarity (if None, will be randomly selected)
            
        Returns:
            Armor data
        """
        # Select rarity if not provided
        if not rarity:
            rarity = self._select_rarity()
        
        # Select armor type
        armor_type = random.choice(self.ITEM_TYPES["armor"])
        
        # Generate base stats based on level and rarity
        rarity_mod = self.RARITIES[rarity]["modifier"]
        base_defense = max(1, int((level * 2) * rarity_mod))
        
        # Select attribute focus
        attribute = random.choice(["defense", "health", "magic"])
        
        # Generate name with prefix and/or suffix
        if random.random() < 0.7:  # 70% chance for special name
            if random.random() < 0.5:  # 50% chance for prefix only
                name = f"{random.choice(self.PREFIXES[attribute])} {armor_type.capitalize()}"
            else:  # 50% chance for suffix only
                name = f"{armor_type.capitalize()} {random.choice(self.SUFFIXES[attribute])}"
        else:  # 30% chance for basic name
            name = armor_type.capitalize()
        
        # Generate durability
        durability = int(70 * rarity_mod)
        
        # Generate item data
        item_data = {
            "name": name,
            "type": "armor",
            "subtype": armor_type,
            "rarity": rarity,
            "level": level,
            "defense": base_defense,
            "durability": durability,
            "attributes": {
                attribute: int(level * rarity_mod)
            },
            "description": self._generate_item_description(name, armor_type, rarity, attribute)
        }
        
        # Generate unique ID
        item_id = self.generate_item_id(name)
        
        # Add to database
        if "items" not in self.items_db:
            self.items_db["items"] = {}
        self.items_db["items"][item_id] = item_data
        
        # Save database
        self.save_items_database()
        
        return item_data
    
    def generate_consumable(self, level: int = 1, rarity: str = None) -> Dict[str, Any]:
        """
        Generate a consumable item.
        
        Args:
            level: Character level
            rarity: Item rarity (if None, will be randomly selected)
            
        Returns:
            Consumable data
        """
        # Select rarity if not provided
        if not rarity:
            rarity = self._select_rarity()
        
        # Select consumable type
        consumable_type = random.choice(self.ITEM_TYPES["consumable"])
        
        # Generate base stats based on level and rarity
        rarity_mod = self.RARITIES[rarity]["modifier"]
        
        # Select effect type
        effect_types = ["health", "stamina", "magic", "strength", "defense"]
        effect_type = random.choice(effect_types)
        effect_value = max(5, int((level * 5) * rarity_mod))
        
        # Generate name
        if consumable_type == "potion":
            name = f"Poção de {effect_type.capitalize()}"
        elif consumable_type == "food":
            foods = ["Pão", "Carne", "Frutas", "Queijo", "Sopa"]
            name = f"{random.choice(foods)} {random.choice(self.PREFIXES[random.choice(list(self.PREFIXES.keys()))])}"
        elif consumable_type == "scroll":
            name = f"Pergaminho de {random.choice(['Proteção', 'Força', 'Velocidade', 'Invisibilidade', 'Cura'])}"
        else:
            name = f"Elixir de {effect_type.capitalize()}"
        
        # Generate item data
        item_data = {
            "name": name,
            "type": "consumable",
            "subtype": consumable_type,
            "rarity": rarity,
            "level": level,
            "effect": {
                "type": effect_type,
                "value": effect_value,
                "duration": int(30 * rarity_mod) if effect_type != "health" else 0
            },
            "quantity": 1,
            "description": self._generate_item_description(name, consumable_type, rarity, effect_type)
        }
        
        # Generate unique ID
        item_id = self.generate_item_id(name)
        
        # Add to database
        if "items" not in self.items_db:
            self.items_db["items"] = {}
        self.items_db["items"][item_id] = item_data
        
        # Save database
        self.save_items_database()
        
        return item_data
    
    def generate_quest_item(self, quest_name: str = None, level: int = 1) -> Dict[str, Any]:
        """
        Generate a quest item.
        
        Args:
            quest_name: Name of the quest (optional)
            level: Character level
            
        Returns:
            Quest item data
        """
        # Select quest item type
        item_type = random.choice(self.ITEM_TYPES["quest"])
        
        # Generate name
        if quest_name:
            if item_type == "key":
                name = f"Chave de {quest_name}"
            elif item_type == "artifact":
                name = f"Artefato de {quest_name}"
            elif item_type == "document":
                name = f"Documento de {quest_name}"
            elif item_type == "map":
                name = f"Mapa de {quest_name}"
            else:
                name = f"Carta de {quest_name}"
        else:
            locations = ["Dungeon", "Castle", "Temple", "Cave", "Forest", "Mountain"]
            if item_type == "key":
                name = f"Chave da {random.choice(locations)}"
            elif item_type == "artifact":
                name = f"Artefato Antigo"
            elif item_type == "document":
                name = f"Documento Secreto"
            elif item_type == "map":
                name = f"Mapa do Tesouro"
            else:
                name = f"Carta Misteriosa"
        
        # Generate item data
        item_data = {
            "name": name,
            "type": "quest",
            "subtype": item_type,
            "rarity": "rare",  # Quest items are always rare
            "level": level,
            "description": self._generate_item_description(name, item_type, "rare", "quest")
        }
        
        # Add content for documents, maps, and letters
        if item_type in ["document", "map", "letter"]:
            item_data["content"] = self._generate_document_content(item_type, quest_name)
        
        # Generate unique ID
        item_id = self.generate_item_id(name)
        
        # Add to database
        if "items" not in self.items_db:
            self.items_db["items"] = {}
        self.items_db["items"][item_id] = item_data
        
        # Save database
        self.save_items_database()
        
        return item_data
    
    def generate_random_item(self, level: int = 1) -> Dict[str, Any]:
        """
        Generate a random item.
        
        Args:
            level: Character level
            
        Returns:
            Item data
        """
        # Select item type
        item_types = ["weapon", "armor", "consumable"]
        weights = [0.4, 0.3, 0.3]  # 40% weapon, 30% armor, 30% consumable
        item_type = random.choices(item_types, weights=weights, k=1)[0]
        
        # Generate item based on type
        if item_type == "weapon":
            return self.generate_weapon(level)
        elif item_type == "armor":
            return self.generate_armor(level)
        else:
            return self.generate_consumable(level)
    
    def _select_rarity(self) -> str:
        """
        Select a random rarity based on chances.
        
        Returns:
            Rarity string
        """
        rarities = list(self.RARITIES.keys())
        chances = [self.RARITIES[r]["chance"] for r in rarities]
        return random.choices(rarities, weights=chances, k=1)[0]
    
    def _generate_item_description(self, name: str, item_type: str, rarity: str, attribute: str) -> str:
        """
        Generate a description for an item using AI.
        
        Args:
            name: Item name
            item_type: Item type
            rarity: Item rarity
            attribute: Main attribute
            
        Returns:
            Item description
        """
        try:
            prompt = f"""
            Gere uma descrição curta e atmosférica para um item de RPG medieval fantástico chamado '{name}'.
            
            Detalhes do item:
            - Tipo: {item_type}
            - Raridade: {rarity}
            - Atributo principal: {attribute}
            
            A descrição deve ter 1-2 frases e incluir:
            - Aparência visual
            - Alguma característica única ou história
            - Referência sutil ao seu efeito ou poder
            
            Responda apenas com a descrição, sem explicações adicionais.
            """
            
            response = self.ai_client.generate_response(prompt)
            if isinstance(response, str) and response.strip():
                return response.strip()
        except Exception as e:
            logger.error(f"Error generating item description: {e}")
        
        # Fallback descriptions
        fallbacks = {
            "weapon": f"Uma {item_type} de qualidade {rarity}. Parece ser eficaz em combate.",
            "armor": f"Uma peça de {item_type} de qualidade {rarity}. Oferece boa proteção.",
            "consumable": f"Um {item_type} de qualidade {rarity}. Parece ter propriedades úteis.",
            "quest": f"Um {item_type} importante para alguma missão. Parece valioso."
        }
        
        item_category = next((k for k, v in self.ITEM_TYPES.items() if item_type in v), "quest")
        return fallbacks.get(item_category, f"Um item de qualidade {rarity}.")
    
    def _generate_document_content(self, doc_type: str, quest_name: str = None) -> str:
        """
        Generate content for documents, maps, and letters using AI.
        
        Args:
            doc_type: Document type
            quest_name: Name of the quest (optional)
            
        Returns:
            Document content
        """
        try:
            context = f" relacionado à missão '{quest_name}'" if quest_name else ""
            
            if doc_type == "document":
                prompt = f"""
                Gere o conteúdo de um documento antigo{context} em um RPG medieval fantástico.
                O documento deve conter informações misteriosas ou históricas que possam ser úteis para o jogador.
                Mantenha o texto curto (3-5 frases) e atmosférico.
                """
            elif doc_type == "map":
                prompt = f"""
                Gere uma descrição textual de um mapa{context} em um RPG medieval fantástico.
                Descreva os principais pontos de referência, direções e possivelmente um tesouro ou local secreto.
                Mantenha o texto curto (3-5 frases) e atmosférico.
                """
            else:  # letter
                prompt = f"""
                Gere o conteúdo de uma carta misteriosa{context} em um RPG medieval fantástico.
                A carta deve conter informações intrigantes, possivelmente um pedido de ajuda ou um aviso.
                Mantenha o texto curto (3-5 frases) e atmosférico.
                """
            
            response = self.ai_client.generate_response(prompt)
            if isinstance(response, str) and response.strip():
                return response.strip()
        except Exception as e:
            logger.error(f"Error generating document content: {e}")
        
        # Fallback content
        fallbacks = {
            "document": "Este documento contém informações antigas sobre um tesouro escondido. Parece importante.",
            "map": "O mapa mostra um caminho através da floresta até uma caverna. Há uma marca de 'X' no final do caminho.",
            "letter": "Caro amigo, preciso de sua ajuda urgentemente. Encontre-me na taverna ao anoitecer. Tenha cuidado, estamos sendo observados."
        }
        
        return fallbacks.get(doc_type, "Este item contém informações importantes para sua jornada.")