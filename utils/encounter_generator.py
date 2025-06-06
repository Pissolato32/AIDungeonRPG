"""
Módulo de geração de encontros.

Este módulo é responsável por gerar encontros dinâmicos baseados no ambiente,
nível do personagem e condições do jogo.
"""

import random
from typing import Any, Dict, List, Optional, TypedDict


class EncounterEnemy(TypedDict):
    """Tipo para inimigos em um encontro."""

    name: str
    level: int
    health: int
    damage: int
    type: str
    abilities: List[str]
    loot: Dict[str, float]  # item: chance de drop


class EncounterReward(TypedDict):
    """Tipo para recompensas de encontro."""

    experience: int
    gold: int
    items: List[Dict[str, Any]]
    reputation: Optional[Dict[str, int]]


class Encounter(TypedDict):
    """Tipo para encontros completos."""

    type: str
    difficulty: int
    enemies: List[EncounterEnemy]
    description: str
    environment_effects: Dict[str, Any]
    rewards: EncounterReward
    escape_chance: float


class EncounterGenerator:
    """
    Generates dynamic encounters for an RPG, including enemies, rewards,
    and environmental effects based on player level and location.
    """

    def __init__(self) -> None:
        """Inicializa o gerador de encontros."""
        self._enemy_templates = {
            "goblin": {
                "base_health": 30,
                "base_damage": 5,
                "abilities": ["Ataque Furtivo", "Fuga"],
                "loot": {
                    "Moedas de Cobre": 0.8,
                    "Adaga Enferrujada": 0.3,
                    "Poção Menor": 0.2,
                },
            },
            "lobo": {
                "base_health": 25,
                "base_damage": 8,
                "abilities": ["Mordida", "Uivo Aterrorizante"],
                "loot": {"Pele de Lobo": 0.9, "Presas Afiadas": 0.6},
            },
            "bandido": {
                "base_health": 40,
                "base_damage": 7,
                "abilities": ["Golpe Traiçoeiro", "Roubar"],
                "loot": {
                    "Moedas de Prata": 0.7,
                    "Arma Comum": 0.4,
                    "Poção de Cura": 0.3,
                },
            },
            "esqueleto": {
                "base_health": 35,
                "base_damage": 6,
                "abilities": ["Ataque Ossudo", "Resistência Mórbida"],
                "loot": {"Ossos": 1.0, "Gema Antiga": 0.2, "Arma Enferrujada": 0.5},
            },
        }

        self._environment_effects = {
            "forest": {"cover": True, "escape_bonus": 0.2, "vision_penalty": -2},
            "mountain": {
                "high_ground": True,
                "damage_bonus": 2,
                "movement_penalty": -1,
            },
            "desert": {"heat": True, "stamina_drain": 2, "accuracy_penalty": -1},
            "cave": {"darkness": True, "vision_penalty": -3, "echo": True},
        }

    def generate_encounter(
        self, player_level: int, location_type: str, time_of_day: str = "day"
    ) -> Encounter:
        """
        Generates a complete encounter based on player level, location type, and time of day.

        Args:
            player_level: The current level of the player.
            location_type: The type of location where the encounter occurs (e.g., "forest", "cave").
            time_of_day: The current time of day (e.g., "day", "night").

        Returns:
            An Encounter TypedDict containing all details of the generated encounter.
        """
        # Determinar dificuldade
        difficulty = self._calculate_difficulty(player_level, time_of_day)

        # Selecionar inimigos apropriados
        enemies = self._generate_enemies(difficulty, player_level, location_type)

        # Gerar recompensas
        rewards = self._generate_rewards(difficulty, player_level, len(enemies))

        # Aplicar efeitos ambientais
        env_effects = self._get_environmental_effects(location_type, time_of_day)

        # Calcular chance de fuga
        escape_chance = self._calculate_escape_chance(difficulty, location_type)

        return {
            "type": self._determine_encounter_type(enemies),
            "difficulty": difficulty,
            "enemies": enemies,
            "description": self._generate_description(
                enemies, location_type, time_of_day
            ),
            "environment_effects": env_effects,
            "rewards": rewards,
            "escape_chance": escape_chance,
        }

    @staticmethod
    def _calculate_difficulty(player_level: int, time_of_day: str) -> int:
        """
        Calculates the difficulty rating for an encounter.

        Args:
            player_level: The player's current level.
            time_of_day: The current time of day ("day" or "night").
        Returns:
            An integer representing the calculated difficulty.
        """
        base_difficulty = random.randint(max(1, player_level - 2), player_level + 2)

        # Modificadores de dificuldade
        if time_of_day == "night":
            base_difficulty += 1

        return base_difficulty

    def _generate_enemies(
        self, difficulty: int, player_level: int, location_type: str
    ) -> List[EncounterEnemy]:
        """
        Generates a list of enemies for the encounter, scaled by difficulty and player level.

        Args:
            difficulty: The calculated difficulty of the encounter.
            player_level: The player's current level.
            location_type: The type of location, influencing enemy types.
        Returns:
            A list of EncounterEnemy TypedDicts.
        """
        num_enemies = random.randint(1, max(2, difficulty // 2))
        enemies: List[EncounterEnemy] = []

        for _ in range(num_enemies):
            enemy_type = self._select_enemy_type(location_type)
            template = self._enemy_templates[enemy_type]

            # Escalar estatísticas com dificuldade
            level = max(1, player_level + random.randint(-2, 2))
            scale = level / 5  # Fator de escala

            enemy: EncounterEnemy = {
                "name": self._generate_enemy_name(enemy_type),
                "level": level,
                "health": int(template["base_health"] * scale),
                "damage": int(template["base_damage"] * scale),
                "type": enemy_type,
                "abilities": template["abilities"].copy(),
                "loot": template["loot"].copy(),
            }

            enemies.append(enemy)

        return enemies

    def _generate_rewards(
        self, difficulty: int, player_level: int, num_enemies: int
    ) -> EncounterReward:
        """
        Generates rewards for successfully completing the encounter.

        Args:
            difficulty: The difficulty of the encounter.
            player_level: The player's level (can influence reward quality, though not directly used here yet).
            num_enemies: The number of enemies in the encounter.
        Returns:
            An EncounterReward TypedDict.
        """
        base_xp = 50 * difficulty
        base_gold = 10 * difficulty

        # Escalar com número de inimigos
        total_xp = base_xp * num_enemies
        total_gold = base_gold * num_enemies

        # Adicionar variação aleatória
        total_xp = int(total_xp * random.uniform(0.8, 1.2))
        total_gold = int(total_gold * random.uniform(0.8, 1.2))

        return {
            "experience": total_xp,
            "gold": total_gold,
            "items": self._generate_loot(difficulty, num_enemies),
            "reputation": self._generate_reputation_rewards(difficulty),
        }

    def _select_enemy_type(self, location_type: str) -> str:
        """
        Selects an appropriate enemy type based on the location.

        Args:
            location_type: The type of location.
        Returns:
            A string representing the chosen enemy type (e.g., "goblin", "lobo").
        """
        location_enemies = {
            "forest": ["goblin", "lobo"],
            "mountain": ["bandido", "lobo"],
            "desert": ["bandido", "esqueleto"],
            "cave": ["goblin", "esqueleto"],
        }

        enemies = location_enemies.get(
            location_type, list(self._enemy_templates.keys())
        )
        return random.choice(enemies)

    @staticmethod
    def _generate_enemy_name(enemy_type: str) -> str:
        """
        Generates a descriptive name for an enemy by adding a prefix to its type.

        Args:
            enemy_type: The base type of the enemy.
        Returns:
            A string name for the enemy (e.g., "Astuto Goblin").
        """
        prefixes = {
            "goblin": ["Astuto", "Cruel", "Sorrateiro"],
            "lobo": ["Feroz", "Selvagem", "Faminto"],
            "bandido": ["Violento", "Perigoso", "Impiedoso"],
            "esqueleto": ["Antigo", "Corrompido", "Sombrio"],
        }

        prefix = random.choice(prefixes.get(enemy_type, ["Normal"]))
        return f"{prefix} {enemy_type.title()}"

    def _get_environmental_effects(
        self, location_type: str, time_of_day: str
    ) -> Dict[str, Any]:
        """
        Determines environmental effects based on location and time of day.

        Args:
            location_type: The type of location.
            time_of_day: The current time of day.
        Returns:
            A dictionary of environmental effects (e.g., vision penalties, cover bonuses).
        """
        effects = self._environment_effects.get(location_type, {}).copy()

        # Modificadores baseados no período do dia
        if time_of_day == "night":
            effects["vision_penalty"] = effects.get("vision_penalty", 0) - 2
            effects["stealth_bonus"] = 2

        return effects

    @staticmethod
    def _calculate_escape_chance(difficulty: int, location_type: str) -> float:
        """
        Calculates the chance for the player to escape the encounter.

        Args:
            difficulty: The difficulty of the encounter.
            location_type: The type of location.
        Returns:
            A float representing the escape chance (0.0 to 1.0).
        """
        base_chance = 0.5  # 50% base

        # Modificar baseado na dificuldade
        difficulty_mod = max(0.1, 1 - (difficulty * 0.1))

        # Modificar baseado no ambiente
        location_mod = {
            "forest": 0.2,  # Mais fácil escapar
            "mountain": -0.1,
            "desert": 0.1,
            "cave": -0.2,  # Mais difícil escapar
        }.get(location_type, 0)

        return min(0.9, max(0.1, base_chance * difficulty_mod + location_mod))

    @staticmethod
    def _generate_description(
        enemies: List[EncounterEnemy], location_type: str, time_of_day: str
    ) -> str:
        """
        Generates a narrative description for the start of the encounter.

        Args:
            enemies: A list of enemies in the encounter.
            location_type: The type of location.
            time_of_day: The current time of day.
        Returns:
            A string describing the encounter setup.
        """
        time_desc = (
            "Sob a luz do dia" if time_of_day == "day" else "Na escuridão da noite"
        )

        enemy_desc = []
        for enemy in enemies:
            enemy_desc.append(f"um {enemy['name']}")

        if len(enemy_desc) == 1:
            enemies_text = enemy_desc[0]
        else:
            enemies_text = ", ".join(enemy_desc[:-1]) + f" e {enemy_desc[-1]}"

        location_desc = {
            "forest": "entre as árvores da floresta",
            "mountain": "nas encostas rochosas",
            "desert": "nas dunas do deserto",
            "cave": "nas profundezas da caverna",
        }.get(location_type, "na área")

        return (
            f"{time_desc}, {enemies_text} surge(m) {location_desc}, "
            "preparado(s) para o combate!"
        )

    def _generate_loot(self, difficulty: int, num_enemies: int) -> List[Dict[str, Any]]:
        """
        Generates loot items for the encounter.
        Currently generates simple item dictionaries; TODO: Integrate with ItemGenerator.

        Args:
            difficulty: The difficulty of the encounter.
            num_enemies: The number of enemies (can influence quantity/quality of loot).
        Returns:
            A list of dictionaries, each representing a loot item.
        """
        # TODO: Integrar com ItemGenerator para gerar itens mais ricos e consistentes
        #       com o sistema de itens do jogo. Atualmente, gera dicts simples.
        items = []
        num_items = random.randint(1, max(2, num_enemies))

        for _ in range(num_items):
            if random.random() < 0.7:  # 70% chance de item comum
                items.append(self._generate_common_item())
            else:  # 30% chance de item raro
                items.append(self._generate_rare_item(difficulty))

        return items

    @staticmethod
    def _generate_common_item() -> Dict[str, Any]:
        """
        Generates a random common item from a predefined list.
        Returns:
            A dictionary representing a common item.
        """
        common_items = [
            {"name": "Poção de Cura", "type": "consumable", "value": 10},
            {"name": "Faca", "type": "weapon", "value": 5},
            {"name": "Escudo de Madeira", "type": "armor", "value": 8},
            {"name": "Ervas Medicinais", "type": "crafting", "value": 3},
        ]
        return random.choice(common_items)

    @staticmethod
    def _generate_rare_item(difficulty: int) -> Dict[str, Any]:
        """
        Generates a random rare item from a predefined list, with a bonus scaled by difficulty.

        Args:
            difficulty: The difficulty of the encounter, used to scale item bonus.
        Returns:
            A dictionary representing a rare item.
        """
        rare_items = [
            {
                "name": "Espada Mágica",
                "type": "weapon",
                "value": 50,
                "bonus": difficulty,
            },
            {
                "name": "Armadura Encantada",
                "type": "armor",
                "value": 60,
                "bonus": difficulty,
            },
            {
                "name": "Anel de Proteção",
                "type": "accessory",
                "value": 45,
                "bonus": difficulty // 2,
            },
        ]
        return random.choice(rare_items)

    @staticmethod
    def _generate_reputation_rewards(difficulty: int) -> Optional[Dict[str, int]]:
        """
        Optionally generates reputation changes with factions based on the encounter.

        Args:
            difficulty: The difficulty of the encounter, influencing the amount of reputation change.
        Returns:
            A dictionary mapping faction names to reputation changes, or None if no
            reputation change occurs.
        """
        if random.random() < 0.3:  # 30% chance de afetar reputação
            factions = ["Vila", "Guilda", "Mercadores"]
            faction = random.choice(factions)
            return {faction: difficulty * 2}
        return None

    @staticmethod
    def _determine_encounter_type(enemies: List[EncounterEnemy]) -> str:
        """
        Determines a descriptive type for the encounter based on the number and types of enemies.

        Args:
            enemies: A list of enemies in the encounter.
        Returns:
            A string describing the encounter type (e.g., "empty", "goblin_group", "horde").
        """
        if not enemies:
            return "empty"

        # Verificar tipo único
        enemy_types = {enemy["type"] for enemy in enemies}
        if len(enemy_types) == 1:
            return f"{next(iter(enemy_types))}_group"

        # Verificar quantidade
        if len(enemies) == 1:
            return "single"
        if len(enemies) == 2:
            return "duo"
        if len(enemies) <= 4:
            return "group"
        return "horde"
