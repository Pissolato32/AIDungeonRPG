"""
Item Generator for the RPG game.

This module handles procedural generation of items with consistent attributes.
"""

import json
import logging
import os
import random
from typing import Any, Dict, List, Optional, TypedDict, Union

# Assuming OpenRouter is in a top-level 'ai' directory or 'core.ai'
# Adjust the import path based on your project structure.
from ai.openrouter import OpenRouterClient  # Corrigido o caminho e nome da classe

logger = logging.getLogger(__name__)


class RarityInfo(TypedDict):
    """TypedDict for storing rarity information including modifier and chance."""

    modifier: float
    chance: float


class ItemGenerator:
    """
    Handles procedural generation of items with consistent attributes for a zombie apocalypse RPG.
    It can generate various item types like weapons, protection, consumables, tools, and materials.
    Item properties are influenced by rarity, level, and thematic prefixes/suffixes.
    """

    # Item types - ZOMBIE APOCALYPSE THEME
    ITEM_TYPES = {
        "weapon_melee": [
            "Faca Improvisada",
            "Cano de Metal",
            "Bastão com Pregos",
            "Pé de Cabra",
            "Machadinha",
            "Martelo de Garra",
        ],
        "weapon_ranged": [
            "Pistola Velha",
            "Espingarda de Cano Serrado",
            "Rifle de Caça",
            "Arco Improvisado",
            "Besta Reciclada",
        ],
        "weapon_thrown": [  # Nova categoria para Molotov, etc.
            "Coquetel Molotov",
            "Pedra Afiada",
            "Lata Vazia Barulhenta",  # Para distração
        ],
        "ammo": [
            "balas de pistola",
            "cartuchos de espingarda",
            "flechas rústicas",
            "virotes",
        ],
        "protection": [
            "Jaqueta de Couro Reforçada",
            "Protetores Improvisados de Canela",
            "Capacete de Obra",
            "Máscara de Gás Rachada",
        ],  # Replaces "armor"
        "consumable_medical": [
            "Bandagem Suja",
            "Kit de Primeiros Socorros",
            "Analgésicos Vencidos",
            "Antibióticos (dose única)",
            "Antisséptico Diluído",
        ],
        "consumable_food": [
            "Comida Enlatada (rótulo ilegível)",
            "Ração Militar Vencida",
            "Barra de Cereal Mofada",
            "Água Purificada (1L)",
            "Garrafa de Água Duvidosa",
        ],
        "tool": [
            "Lanterna Fraca",
            "Isqueiro (pouco gás)",
            "Kit de Arrombamento Rústico",
            "Corda Desgastada",
            "Rolo de Fita Adesiva",
        ],
        "material_crafting": [
            "Sucata de Metal (pequena)",
            "Tecido Rasgado Limpo",
            "Componentes Eletrônicos Queimados",
            "Pólvora Caseira",
            "Madeira Podre Útil",
            "Garrafa Vazia",  # Adicionado
            "Gasolina",  # Adicionado
            "Arame Fino",  # Adicionado
            "Cola Forte",
        ],
        "quest": [
            "Chave Enferrujada do Bunker",
            "Diário de um Sobrevivente Desesperado",
            "Mapa Rabiscado de um Ponto de Suprimentos",
            "Amostra de Tecido Infectado Selada",
            "Rádio Transmissor Danificado",
        ],
        "misc": [
            "Isqueiro Zippo Vazio",
            "Relógio de Pulso Quebrado",
            "Foto Desbotada de uma Família",
            "Livro Mofado sobre Botânica",
        ],
    }

    # Item rarities and their modifiers
    RARITIES: Dict[str, RarityInfo] = {
        "common": {"modifier": 1.0, "chance": 0.55},
        "uncommon": {"modifier": 1.5, "chance": 0.25},
        "rare": {"modifier": 2.0, "chance": 0.1},
        "epic": {"modifier": 3.0, "chance": 0.04},
        "legendary": {"modifier": 5.0, "chance": 0.01},
    }  # type: ignore # Mypy pode reclamar da atribuição direta aqui se não for inicializado em __init__ ou com Final

    # Item prefixes - ZOMBIE APOCALYPSE THEME
    PREFIXES = {
        "condition_good": ["Confiável", "Bem Conservado", "Reforçado", "Modificado"],
        "condition_bad": ["Enferrujado", "Danificado", "Sujo", "Frágil", "Improvisado"],
        "effect_positive": ["Potente", "Energizante", "Restaurador", "Protetor"],
        "effect_negative": [
            "Contaminado",
            "Vencido",
            "Instável",
        ],  # For potentially risky items
        "tactical": ["Silencioso", "Leve", "Pesado", "Compacto"],
    }

    # Item suffixes - ZOMBIE APOCALYPSE THEME
    SUFFIXES = {
        "origin": [
            "de Saque",
            "Militar Antigo",
            "Caseiro",
            "Pré-Apocalipse",
            "da Zona Contaminada",
        ],
        "purpose": [
            "de Sobrevivência",
            "de Combate",
            "de Defesa",
            "de Fuga",
            "de Precisão",
        ],
        "quirk": [
            "da Última Esperança",
            "do Desespero",
            "da Sorte Inesperada",
            "do Silêncio Mortal",
        ],
    }

    # Base stats for item types (can be expanded)
    BASE_ITEM_STATS = {
        "Faca Improvisada": {
            "damage_min": 2,
            "damage_max": 5,
            "durability": 30,
            "weight": 0.5,
        },
        "Cano de Metal": {
            "damage_min": 3,
            "damage_max": 7,
            "durability": 50,
            "weight": 1.5,
        },
        "Pistola Velha": {
            "damage_min": 5,
            "damage_max": 10,
            "durability": 40,
            "ammo_type": "balas de pistola",
            "capacity": 7,
            "weight": 1.0,
        },
        "Jaqueta de Couro Reforçada": {"defense": 3, "durability": 60, "weight": 2.0},
        "Bandagem Suja": {"heal_amount": 5, "infection_risk": 0.15, "weight": 0.1},
        "Comida Enlatada (rótulo ilegível)": {
            "hunger_restore": 30,
            "thirst_restore": 5,
            "weight": 0.4,
        },
        "Lança de Madeira Afiada": {
            "damage_min": 2,
            "damage_max": 6,
            "durability": 25,
            "weight": 0.8,
            "type": "weapon_melee",
        },
        "Coquetel Molotov": {
            "damage_min": 10,
            "damage_max": 25,
            "area_effect": "fire",
            "uses": 1,
            "weight": 0.5,
            "type": "weapon_thrown",
        },  # Dano em área, uso único
        "Kit de Arrombamento Rústico": {
            "durability": 5,
            "effectiveness": 0.3,
            "weight": 0.3,
            "type": "tool",
        },  # Baixa durabilidade, chance de sucesso
        "Garrafa Vazia": {
            "weight": 0.2,
            "stackable": True,
            "type": "material_crafting",
        },
        "Gasolina": {
            "weight": 0.8,
            "flammable": True,
            "type": "material_crafting",
        },  # Porção pequena
        "Arame Fino": {"weight": 0.1, "stackable": True, "type": "material_crafting"},
        # Add more base stats for other items as needed
    }

    def __init__(self, data_dir: str):
        """
        Initialize the item generator.
        Loads an existing item database or prepares to create a new one.

        Args:
            data_dir: The directory where item data (items_database.json) is stored or will be stored.
        """
        # TODO: Consider making ai_client injectable for better testability and flexibility.
        # For example, pass an instance of OpenRouterClient or a compatible AI client to the constructor.
        self.data_dir = data_dir
        self.items_file = os.path.join(data_dir, "items_database.json")
        self.ai_client = OpenRouterClient()  # Corrigida a instanciação da classe
        self.items_db = self.load_items_database()

    @staticmethod
    def _sanitize_for_id(name: str) -> str:
        """
        Sanitizes a given item name to create a file-system friendly and consistent ID.
        Converts to lowercase, replaces spaces with underscores, and removes special characters.

        Args:
            name: The original item name.
        Returns: A sanitized string suitable for use as an ID.
        """
        name = name.lower()
        replacements = {
            " ": "_",
            "ç": "c",
            "ã": "a",
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
            "ñ": "n",
            "'": "",
            '"': "",
        }
        for old, new in replacements.items():
            name = name.replace(old, new)
        name = "".join(char for char in name if char.isalnum() or char == "_")
        return name

    def load_items_database(self) -> Dict[str, Any]:
        """
        Loads the items database from the `items_database.json` file.
        If the file doesn't exist or an error occurs, returns a default empty database structure.

        Returns:
            A dictionary representing the items database.
        """
        if os.path.exists(self.items_file):
            try:
                with open(self.items_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading items database: {e}")

        return {"items": {}, "metadata": {"version": "1.0", "created": "procedural"}}

    def save_items_database(self) -> bool:
        """
        Saves the current in-memory items database to the `items_database.json` file.

        Returns:
            True if saving was successful, False otherwise.
        """
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.items_file, "w", encoding="utf-8") as f:
                json.dump(self.items_db, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving items database: {e}")
            return False

    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an item by its ID.

        Args:
            item_id: The unique ID of the item to retrieve.
        Returns:
            A dictionary containing the item's data if found, otherwise None.
        """
        return self.items_db.get("items", {}).get(item_id)

    def get_item_by_name(self, item_name: str) -> Optional[Dict[str, Any]]:
        """
        Get an item by its name.
        Performs a case-insensitive search.

        Args:
            item_name: The name of the item to retrieve.
        Returns:
            A dictionary containing the item's data if found, otherwise None.
        """
        for _, item_data in self.items_db.get("items", {}).items():
            if item_data.get("name", "").lower() == item_name.lower():
                return item_data
        return None

    def _generate_item_id(self, item_name: str) -> str:
        """
        Generates a unique ID for an item based on its name.
        If an ID based on the sanitized name already exists, appends a counter.

        Args:
            item_name: The name of the item.
        Returns: A unique string ID for the item.
        """
        base_id = self._sanitize_for_id(item_name)
        item_id = base_id
        counter = 1
        while item_id in self.items_db.get("items", {}):
            item_id = f"{base_id}_{counter}"
            counter += 1
        return item_id

    @staticmethod
    def _apply_rarity_modifiers(
        base_stats: Dict[str, Any], rarity_mod: float, level: int
    ) -> Dict[str, Any]:
        """
        Applies rarity and level-based modifiers to an item's base stats.

        Args:
            base_stats: The original base statistics of the item.
            rarity_mod: The multiplier associated with the item's rarity.
            level: The character level or item level, used for scaling.
        Returns:
            A new dictionary with the modified stats.
        """
        modified_stats = base_stats.copy()
        if "damage_min" in modified_stats:
            modified_stats["damage_min"] = max(
                1, int(modified_stats["damage_min"] * rarity_mod + level / 2)
            )
        if "damage_max" in modified_stats:
            modified_stats["damage_max"] = max(
                modified_stats.get("damage_min", 1) + 1,
                int(modified_stats["damage_max"] * rarity_mod + level),
            )
        if "defense" in modified_stats:
            modified_stats["defense"] = max(
                1, int(modified_stats["defense"] * rarity_mod + level / 2)
            )
        if "durability" in modified_stats:
            modified_stats["durability"] = max(
                10, int(modified_stats["durability"] * (rarity_mod * 0.5 + 0.5))
            )  # Rarity has less impact on durability increase
        if "heal_amount" in modified_stats:
            modified_stats["heal_amount"] = max(
                5, int(modified_stats["heal_amount"] * rarity_mod + level)
            )
        if "hunger_restore" in modified_stats:
            modified_stats["hunger_restore"] = max(
                10, int(modified_stats["hunger_restore"] * rarity_mod)
            )
        if "thirst_restore" in modified_stats:
            modified_stats["thirst_restore"] = max(
                10, int(modified_stats["thirst_restore"] * rarity_mod)
            )

        if "damage_min" in modified_stats and "damage_max" in modified_stats:
            if modified_stats["damage_min"] > modified_stats["damage_max"]:
                modified_stats["damage_max"] = modified_stats[
                    "damage_min"
                ] + random.randint(
                    1, 3
                )  # Ensure max is slightly higher
        return modified_stats

    def _generate_item_name(
        self, base_name: str, rarity: str, item_category: str
    ) -> str:
        """
        Generates a thematic and descriptive name for an item based on its base name,
        rarity, and category. Randomly adds prefixes and suffixes.

        Args:
            base_name: The fundamental name of the item (e.g., "Faca").
            rarity: The rarity of the item (e.g., "common", "rare").
            item_category: The general category of the item (e.g., "weapon", "consumable").
        Returns: A generated string name for the item.
        """
        name_parts = [base_name.capitalize()]

        if random.random() < 0.6:
            if rarity in ["common", "uncommon"] and random.random() < 0.7:
                name_parts.insert(0, random.choice(self.PREFIXES["condition_bad"]))
            elif rarity in ["rare", "epic", "legendary"] and random.random() < 0.5:
                name_parts.insert(0, random.choice(self.PREFIXES["condition_good"]))
            elif (
                item_category == "consumable" and random.random() < 0.4
            ):  # Consumables might have effect prefixes
                name_parts.insert(
                    0,
                    random.choice(self.PREFIXES.get("effect_positive", ["Melhorado"])),
                )
            elif (  # type: ignore
                item_category == "weapon" and random.random() < 0.3
            ):  # Weapons might have tactical prefixes
                name_parts.insert(0, random.choice(self.PREFIXES["tactical"]))

        if random.random() < 0.4:
            suffix_category = random.choice(list(self.SUFFIXES.keys()))
            name_parts.append(random.choice(self.SUFFIXES[suffix_category]))

        return " ".join(name_parts)

    def generate_weapon(
        self,
        level: int = 1,
        rarity: Optional[str] = None,
        weapon_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates a weapon item with stats scaled by level and rarity.

        Args:
            level: The level to scale the weapon for.
            rarity: Optional specific rarity. If None, a rarity is chosen randomly.
            weapon_category: Optional specific weapon category (e.g., "weapon_melee", "weapon_ranged").
                             If None, a category is chosen randomly.
        Returns:
            A dictionary representing the generated weapon.
        """
        if not rarity:
            rarity = self._select_rarity()  # type: ignore
        if not weapon_category:
            weapon_category = random.choice(
                ["weapon_melee", "weapon_ranged", "weapon_thrown"]
            )

        base_weapon_type = random.choice(
            self.ITEM_TYPES.get(weapon_category, self.ITEM_TYPES["weapon_melee"])
        )  # type: ignore
        if not base_weapon_type:  # Fallback if category was invalid
            base_weapon_type = random.choice(self.ITEM_TYPES["weapon_melee"])  # type: ignore

        base_stats = self.BASE_ITEM_STATS.get(base_weapon_type, {}).copy()
        if not base_stats:
            base_stats = {
                "damage_min": level,
                "damage_max": level + random.randint(2, 5),
                "durability": 20 + level * 5,
                "weight": 1.0,
            }
            if weapon_category == "weapon_ranged" or weapon_category == "weapon_thrown":
                base_stats["ammo_type"] = "munição genérica"
                base_stats["capacity"] = random.randint(3, 10)

        rarity_mod = self.RARITIES[rarity]["modifier"]  # type: ignore
        modified_stats = self._apply_rarity_modifiers(base_stats, rarity_mod, level)
        name = self._generate_item_name(base_weapon_type, rarity, "weapon")  # type: ignore

        item_data: Dict[str, Any] = {
            "name": name,
            "type": weapon_category,
            "subtype": base_weapon_type,
            "rarity": rarity,
            "level_req": level,
            "damage_min": modified_stats.get("damage_min"),
            "damage_max": modified_stats.get(
                "damage_max", modified_stats.get("damage_min", 1) + 1
            ),
            "durability": modified_stats.get("durability", 20),
            "weight": modified_stats.get("weight", 1.0),
            "description": self._generate_item_description(
                name,
                base_weapon_type,
                rarity,
                "arma",  # type: ignore
            ),
        }
        if weapon_category == "weapon_ranged" or weapon_category == "weapon_thrown":
            item_data["ammo_type"] = modified_stats.get(
                "ammo_type", "munição desconhecida"
            )
            item_data["capacity"] = modified_stats.get("capacity", 1)
            item_data["current_ammo"] = (
                random.randint(0, item_data["capacity"])
                if item_data["capacity"] > 0
                else 0
            )
        if weapon_category == "weapon_thrown":
            item_data["uses"] = modified_stats.get(
                "uses", 1
            )  # Thrown items might have uses
            item_data.pop(
                "capacity", None
            )  # Thrown items don't usually have capacity in the same way
        item_id = self._generate_item_id(name)
        if "items" not in self.items_db:
            self.items_db["items"] = {}
        self.items_db["items"][item_id] = item_data
        # self.save_items_database() # Removido para otimização de performance em lote
        return item_data

    def generate_protection(
        self, level: int = 1, rarity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a piece of protection (armor) with stats scaled by level and rarity.

        Args:
            level: The level to scale the protection for.
            rarity: Optional specific rarity. If None, a rarity is chosen randomly.
        Returns:
            A dictionary representing the generated protection item.
        """
        if not rarity:
            rarity = self._select_rarity()  # type: ignore

        protection_type = random.choice(self.ITEM_TYPES["protection"])  # type: ignore
        base_stats = self.BASE_ITEM_STATS.get(protection_type, {}).copy()
        if not base_stats:
            base_stats = {
                "defense": level,
                "durability": 30 + level * 10,
                "weight": 1.5,
            }

        rarity_mod = self.RARITIES[rarity]["modifier"]  # type: ignore
        modified_stats = self._apply_rarity_modifiers(base_stats, rarity_mod, level)
        name = self._generate_item_name(protection_type, rarity, "protection")  # type: ignore

        item_data: Dict[str, Any] = {
            "name": name,
            "type": "protection",
            "subtype": protection_type,
            "rarity": rarity,
            "level_req": level,
            "defense": modified_stats.get("defense"),
            "durability": modified_stats.get("durability"),
            "weight": modified_stats.get("weight", 1.0),
            "description": self._generate_item_description(
                name,
                protection_type,
                rarity,
                "proteção",  # type: ignore
            ),
        }
        item_id = self._generate_item_id(name)
        if "items" not in self.items_db:
            self.items_db["items"] = {}
        self.items_db["items"][item_id] = item_data
        # self.save_items_database() # Removido para otimização de performance em lote
        return item_data

    def generate_consumable(
        self,
        level: int = 1,
        rarity: Optional[str] = None,
        consumable_category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates a consumable item (medical or food) with effects scaled by level and rarity.

        Args:
            level: The level to scale the consumable for.
            rarity: Optional specific rarity. If None, a rarity is chosen randomly.
            consumable_category: Optional specific consumable category (e.g., "consumable_medical").
                                 If None, a category is chosen randomly.
        Returns:
            A dictionary representing the generated consumable item.
        """
        if not rarity:
            rarity = self._select_rarity()  # type: ignore
        if not consumable_category:
            consumable_category = random.choice(
                ["consumable_medical", "consumable_food"]
            )
        # type: ignore
        base_consumable_type = random.choice(self.ITEM_TYPES[consumable_category])  # type: ignore
        base_stats = self.BASE_ITEM_STATS.get(base_consumable_type, {}).copy()

        if not base_stats:
            if consumable_category == "consumable_medical":
                base_stats = {"heal_amount": 10 + level * 2, "weight": 0.2}
            else:
                base_stats = {
                    "hunger_restore": 20 + level * 2,
                    "thirst_restore": 15 + level,
                    "weight": 0.3,
                }

        rarity_mod = self.RARITIES[rarity]["modifier"]  # type: ignore
        modified_stats = self._apply_rarity_modifiers(base_stats, rarity_mod, level)
        name = self._generate_item_name(base_consumable_type, rarity, "consumable")  # type: ignore

        item_data: Dict[str, Any] = {
            "name": name,
            "type": "consumable",
            "subtype": base_consumable_type,
            "rarity": rarity,
            "level_req": level,
            "effects": [],
            "quantity": 1,
            "weight": modified_stats.get("weight", 0.2),
            "description": self._generate_item_description(
                name,
                base_consumable_type,
                rarity,
                "consumível",  # type: ignore
            ),
        }

        if "heal_amount" in modified_stats:
            item_data["effects"].append(
                {"type": "heal_hp", "value": modified_stats["heal_amount"]}
            )
        if "hunger_restore" in modified_stats:
            item_data["effects"].append(
                {"type": "restore_hunger", "value": modified_stats["hunger_restore"]}
            )
        if "thirst_restore" in modified_stats:
            item_data["effects"].append(
                {"type": "restore_thirst", "value": modified_stats["thirst_restore"]}
            )

        infection_risk_val = modified_stats.get("infection_risk", 0)
        if infection_risk_val > 0 and random.random() < infection_risk_val:
            item_data["effects"].append(
                {
                    "type": "apply_infection",
                    "chance": infection_risk_val,
                    "severity": random.randint(1, 3),
                }
            )
            item_data["name"] += " (Contaminado!)"
            item_data["description"] += " Parece arriscado consumir isto."

        if (
            rarity in ["rare", "epic", "legendary"]  # type: ignore
            and consumable_category == "consumable_medical"
        ):
            item_data["effects"].append({"type": "cure_infection_low", "value": 1})
        # Specific item effect
        if base_consumable_type == "Antibióticos (dose única)":
            item_data["effects"].append({"type": "cure_infection_high", "value": 1})

        item_id = self._generate_item_id(name)
        if "items" not in self.items_db:
            self.items_db["items"] = {}
        self.items_db["items"][item_id] = item_data
        # self.save_items_database() # Removido para otimização de performance em lote
        return item_data

    def generate_quest_item(
        self, quest_name: Optional[str] = None, level: int = 1
    ) -> Dict[str, Any]:
        """
        Generates a quest item, potentially linked to a specific quest name.

        Args:
            quest_name: Optional name of the quest this item is related to, for naming.
            level: The level associated with the quest item.
        Returns:
            A dictionary representing the generated quest item.
        """
        base_item_type = random.choice(self.ITEM_TYPES["quest"])  # type: ignore

        # Use the base_item_type directly for the name, or append quest_name if
        # provided
        if quest_name:
            name = f"{base_item_type} de '{quest_name}'"
        else:
            name = base_item_type  # Use the direct name from ITEM_TYPES for generic quest items

        # Quest items are often unique or at least rare
        rarity = "rare"

        item_data: Dict[str, Any] = {
            "name": name,
            "type": "quest",
            "subtype": base_item_type,
            "rarity": rarity,
            "level_req": level,
            "weight": 0.1,
            "description": self._generate_item_description(
                name,
                base_item_type,
                rarity,
                "item de missão",  # type: ignore
            ),
        }

        if base_item_type in [
            "Diário de um Sobrevivente Desesperado",
            "Mapa Rabiscado de um Ponto de Suprimentos",
            "Amostra de Tecido Infectado Selada",
            "Rádio Transmissor Danificado",
        ]:
            item_data["content"] = self._generate_document_content(
                base_item_type, quest_name
            )

        item_id = self._generate_item_id(name)
        if "items" not in self.items_db:
            self.items_db["items"] = {}
        self.items_db["items"][item_id] = item_data
        # self.save_items_database() # Removido para otimização de performance em lote
        return item_data

    def generate_tool(
        self, level: int = 1, rarity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a tool item with stats scaled by level and rarity.

        Args:
            level: The level to scale the tool for.
            rarity: Optional specific rarity. If None, a rarity is chosen randomly.
        Returns:
            A dictionary representing the generated tool item.
        """
        if not rarity:
            rarity = self._select_rarity()  # type: ignore

        base_tool_type = random.choice(
            self.ITEM_TYPES.get("tool", ["Ferramenta Quebrada"])
        )  # type: ignore
        base_stats = self.BASE_ITEM_STATS.get(base_tool_type, {}).copy()

        if not base_stats:  # Fallback if no specific base stats for this tool
            base_stats = {
                "durability": 10 + level * 2,
                "effectiveness": 0.1 * level,  # Generic effectiveness
                "weight": 0.5 + random.uniform(0.1, 0.5) * level,
            }

        rarity_mod = self.RARITIES[rarity]["modifier"]  # type: ignore
        modified_stats = self._apply_rarity_modifiers(base_stats, rarity_mod, level)
        name = self._generate_item_name(base_tool_type, rarity, "tool")  # type: ignore

        item_data: Dict[str, Any] = {
            "name": name,
            "type": "tool",
            "subtype": base_tool_type,
            "rarity": rarity,
            "level_req": level,
            "durability": modified_stats.get("durability", 10),
            "effectiveness": modified_stats.get("effectiveness", 0.1),
            "weight": modified_stats.get("weight", 0.5),
            "description": self._generate_item_description(
                name, base_tool_type, rarity, "ferramenta"
            ),  # type: ignore
        }
        item_id = self._generate_item_id(name)
        self.items_db.setdefault("items", {})[item_id] = item_data
        # self.save_items_database() # Removido para otimização de performance em lote
        return item_data

    def generate_material_crafting(
        self, level: int = 1, rarity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a crafting material. Rarity has less impact on direct stats for simple materials.

        Args:
            level: The level context (less impactful for basic materials).
            rarity: Optional specific rarity. If None, a rarity is chosen randomly.
        Returns:
            A dictionary representing the generated crafting material.
        """
        if not rarity:
            rarity = self._select_rarity()  # type: ignore

        base_material_type = random.choice(
            self.ITEM_TYPES.get("material_crafting", ["Sucata Variada"])
        )  # type: ignore
        base_stats = self.BASE_ITEM_STATS.get(base_material_type, {}).copy()

        if not base_stats:  # Fallback for materials
            base_stats = {"weight": random.uniform(0.1, 1.0), "stackable": True}

        # Rarity might influence quantity found or purity, but less so direct stats for simple materials
        name = self._generate_item_name(base_material_type, rarity, "material_crafting")  # type: ignore

        item_data: Dict[str, Any] = {
            "name": name,
            "type": "material_crafting",
            "subtype": base_material_type,
            "rarity": rarity,
            "weight": base_stats.get("weight", 0.1),
            "description": self._generate_item_description(
                name, base_material_type, rarity, "material de criação"
            ),  # type: ignore
        }
        item_id = self._generate_item_id(name)
        self.items_db.setdefault("items", {})[item_id] = item_data
        # self.save_items_database() # Removido para otimização de performance em lote
        return item_data

    def generate_random_item(self, level: int = 1) -> Dict[str, Any]:
        """
        Generates a random item from various categories, scaled by level.
        The type of item is chosen based on weighted probabilities.

        Args:
            level: The level to scale the item for.
        Returns:
            A dictionary representing the generated random item.
        """
        item_categories = [
            "weapon",
            "protection",
            "consumable",
            "tool",
            "material_crafting",
        ]
        # Adjusted weights: more consumables and materials, fewer tools
        # initially
        weights = [0.25, 0.15, 0.35, 0.10, 0.15]
        chosen_category_type = random.choices(item_categories, weights=weights, k=1)[0]

        if chosen_category_type == "weapon":
            return self.generate_weapon(level)
        if chosen_category_type == "protection":
            return self.generate_protection(level)
        if chosen_category_type == "consumable":
            return self.generate_consumable(level)  # type: ignore
        if chosen_category_type == "tool":
            return self.generate_tool(level)
        if chosen_category_type == "material_crafting":
            return self.generate_material_crafting(level)

        # Should not be reached if weights sum to 1 and all categories are
        # handled
        logger.error(
            f"Unhandled item category in generate_random_item: {chosen_category_type}"
        )  # No futuro, poderia levantar uma exceção ou ter um item "genérico desconhecido"
        return self.generate_consumable(level)  # Final fallback

    def _select_rarity(self) -> str:  # type: ignore
        """
        Selects an item rarity based on predefined chances.

        Returns:
            A string representing the chosen rarity (e.g., "common", "rare").
        """
        rarities = list(self.RARITIES.keys())
        chances = [self.RARITIES[r]["chance"] for r in rarities]  # type: ignore
        return random.choices(rarities, weights=chances, k=1)[0]

    def _generate_item_description(
        self, name: str, item_subtype: str, rarity: str, item_category_for_prompt: str
    ) -> str:
        """
        Generates a thematic description for an item using an AI model.
        Falls back to predefined descriptions if AI generation fails.

        Args:
            name: The full generated name of the item.
            item_subtype: The specific base type of the item (e.g., "Faca Improvisada").
            rarity: The rarity of the item.
            item_category_for_prompt: The general category for the AI prompt (e.g., "arma").
        Returns: A string description for the item.
        """
        try:
            prompt = f"""
            Gere uma descrição curta e atmosférica para um item de um RPG de apocalipse zumbi chamado '{name}'.

            Detalhes do item:
            - Tipo Específico: {item_subtype}
            - Categoria Geral: {item_category_for_prompt}
            - Raridade: {rarity}

            A descrição deve ter 1-2 frases e incluir:
            - Aparência visual (desgaste, improvisação, marcas de uso).
            - Alguma pista sobre sua utilidade, perigo ou origem no mundo pós-apocalíptico.

            Responda apenas com a descrição, sem explicações adicionais.
            Exemplo para '{name}': Este {item_subtype} {rarity} parece ter visto dias melhores, mas ainda pode ser útil.
            """
            prompt_dict = {"role": "user", "content": prompt}
            response = self.ai_client.generate_response([prompt_dict])
            if isinstance(response, str) and response.strip():
                return response.strip()
        except Exception as e:
            logger.error(f"Error generating item description for '{name}': {e}")

        fallbacks = {
            "Faca Improvisada": f"Uma {item_subtype} {rarity}. Parece que pode causar algum dano de perto.",
            "Pistola Velha": f"Uma {item_subtype} {rarity}. Útil para manter distância dos perigos, se tiver balas.",
            "Jaqueta de Couro Reforçada": f"Uma {item_subtype} {rarity}. Pode oferecer alguma proteção contra os perigos lá fora.",
            "Bandagem Suja": f"Uma {item_subtype} {rarity}. Parece ser algum tipo de suprimento médico, mas use com cautela.",
            "Comida Enlatada (rótulo ilegível)": f"Uma {item_subtype} {rarity}. Comida é comida neste mundo, mesmo que o rótulo esteja apagado.",
            "Lanterna Fraca": f"Uma {item_subtype} {rarity}. A luz é fraca, mas melhor que nada na escuridão.",
            "Sucata de Metal (pequena)": f"Um(a) {item_subtype} {rarity}. Pode ser usado para criar ou consertar algo.",
            "Chave Enferrujada do Bunker": f"Uma {item_subtype} {rarity}. Parece importante para alguma tarefa ou mistério.",
            "Isqueiro Zippo Vazio": f"Um(a) {item_subtype} {rarity}. Um pequeno lembrete do mundo antigo, ou talvez algo útil se encontrar combustível.",
        }
        # Try to get a specific fallback for the subtype, then for the
        # category, then a generic one.
        return fallbacks.get(
            item_subtype,
            fallbacks.get(
                item_category_for_prompt,
                f"Um item {rarity} interessante. Parece ser um(a) {item_subtype}.",
            ),
        )

    def _generate_document_content(
        self, doc_type: str, quest_name: Optional[str] = None
    ) -> str:
        """
        Generates thematic content for a document-type quest item (e.g., diary entry, map description)
        using an AI model. Falls back to predefined content if AI generation fails.

        Args:
            doc_type: The specific type of document (e.g., "Diário de um Sobrevivente Desesperado").
            quest_name: Optional name of the quest this document is related to, for context.
        Returns:
            A string containing the generated content for the document.
        """
        try:
            context = f" relacionado à tarefa '{quest_name}'" if quest_name else ""
            specific_doc_type = (
                doc_type  # Use the full name from ITEM_TYPES for more specific prompts
            )

            if "diário" in specific_doc_type.lower():
                prompt = f"""
                Gere um trecho do conteúdo de um '{specific_doc_type}'{context} em um RPG de apocalipse zumbi.
                O diário deve conter observações pessoais, medos, esperanças ou informações sobre o que aconteceu ou locais próximos.
                Mantenha o texto curto (3-5 frases), pessoal e atmosférico.
                """
            elif "mapa" in specific_doc_type.lower():
                prompt = f"""
                Gere uma descrição textual de um '{specific_doc_type}'{context} em um RPG de apocalipse zumbi.
                Descreva os principais pontos de referência (ruas, edifícios notáveis, perigos marcados), direções e possivelmente um local de interesse (suprimentos, abrigo).
                Mantenha o texto curto (3-5 frases), prático e com um tom de urgência ou esperança.
                """
            elif "amostra" in specific_doc_type.lower():
                prompt = f"""
                Gere uma breve nota de pesquisa ou observação anexada a um(a) '{specific_doc_type}'{context} em um RPG de apocalipse zumbi.
                A nota deve conter termos científicos básicos, observações sobre a progressão da infecção ou uma teoria.
                Mantenha o texto curto (2-3 frases), clínico e um pouco perturbador.
                """
            else:
                prompt = f"Descreva brevemente o estado ou uma pista sobre o item '{specific_doc_type}'{context} em um apocalipse zumbi. O item é crucial para uma tarefa."

            prompt_dict = {"role": "user", "content": prompt}
            response = self.ai_client.generate_response([prompt_dict])
            if isinstance(response, str) and response.strip():
                return response.strip()
        except Exception as e:
            logger.error(f"Error generating document content for '{doc_type}': {e}")

        fallbacks = {
            "Diário de um Sobrevivente Desesperado": "As páginas estão manchadas e a caligrafia é apressada. Fala de perda e da luta diária pela sobrevivência. '...eles estão em toda parte... não sei quanto tempo mais...'",
            "Mapa Rabiscado de um Ponto de Suprimentos": "Este mapa improvisado aponta para um 'local seguro?' a alguns quarteirões daqui, perto da velha torre de água. Há um grande 'X' vermelho sobre a área do antigo mercado, com a anotação 'MUITOS DELES!'.",
            "Amostra de Tecido Infectado Selada": "Nota anexada: 'Sujeito 037. Necrose tecidual acelerada. Nenhuma resposta aos antivirais convencionais. Mutação inesperada observada no estágio 3. Precisamos de mais amostras de...'",
            "Rádio Transmissor Danificado": "O rádio está danificado, com fios expostos e a carcaça rachada, mas parece que alguém tentou consertá-lo recentemente. Talvez algumas peças de outros eletrônicos possam fazê-lo funcionar novamente.",
            "Chave Enferrujada do Bunker": "Uma chave pesada e enferrujada. Tem uma pequena etiqueta quase ilegível que diz 'B-07'.",
        }
        return fallbacks.get(
            doc_type,
            "Este item parece conter alguma informação crucial, mas está difícil de decifrar no momento.",
        )
