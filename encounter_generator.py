"""
Encounter Generator for the RPG game.

This module handles random encounters, challenges, and events.
"""

import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from groq_client import GroqClient

logger = logging.getLogger(__name__)

class EncounterGenerator:
    """Handles generation of random encounters and events."""

    # Encounter types and their relative frequencies
    ENCOUNTER_TYPES = {
        "combat": 0.3,       # Combat encounters
        "obstacle": 0.2,     # Physical obstacles or challenges
        "npc": 0.15,         # NPC interactions
        "treasure": 0.15,    # Finding items or resources
        "trap": 0.1,         # Traps or hazards
        "mystery": 0.1       # Mysterious events or phenomena
    }

    # Difficulty levels and their modifiers
    DIFFICULTIES = {
        "trivial": {"modifier": 0.5, "xp_mult": 0.5, "chance": 0.1},
        "easy": {"modifier": 0.8, "xp_mult": 0.8, "chance": 0.25},
        "normal": {"modifier": 1.0, "xp_mult": 1.0, "chance": 0.4},
        "hard": {"modifier": 1.5, "xp_mult": 1.5, "chance": 0.15},
        "challenging": {"modifier": 2.0, "xp_mult": 2.0, "chance": 0.07},
        "deadly": {"modifier": 3.0, "xp_mult": 3.0, "chance": 0.03}
    }

    # Enemy types by environment
    ENEMIES_BY_ENVIRONMENT = {
        "forest": ["Wolf", "Bandit", "Bear", "Giant Spider", "Goblin"],
        "mountain": ["Mountain Lion", "Troll", "Goat", "Eagle", "Rock Elemental"],
        "desert": ["Scorpion", "Sand Elemental", "Bandit", "Vulture", "Mummy"],
        "swamp": ["Crocodile", "Slime", "Witch", "Frog Man", "Zombie"],
        "cave": ["Bat", "Skeleton", "Slime", "Spider", "Goblin"],
        "ruins": ["Skeleton", "Ghost", "Zombie", "Cultist", "Gargoyle"],
        "village": ["Thief", "Drunk", "Guard", "Dog", "Mercenary"],
        "city": ["Thug", "Guard", "Assassin", "Cultist", "Noble"],
        "dungeon": ["Skeleton", "Zombie", "Goblin", "Orc", "Minotaur"]
    }

    # Trap types
    TRAP_TYPES = [
        "pit", "arrow", "poison", "spike", "falling", 
        "magical", "explosion", "cage", "net", "alarm"
    ]

    # Obstacle types
    OBSTACLE_TYPES = [
        "river", "chasm", "wall", "locked door", "rubble",
        "thorns", "quicksand", "ice", "fire", "magical barrier"
    ]

    def __init__(self):
        """Initialize the encounter generator."""
        self.ai_client = GroqClient()

    def should_trigger_random_encounter(self, location_type: str) -> bool:
        """
        Determine if a random encounter should trigger.

        Args:
            location_type: Type of location

        Returns:
            True if encounter should trigger, False otherwise
        """
        # Base chance depends on location type
        base_chance = {
            "city": 0.05,
            "village": 0.1,
            "road": 0.15,
            "forest": 0.2,
            "mountain": 0.25,
            "desert": 0.25,
            "swamp": 0.3,
            "cave": 0.35,
            "ruins": 0.4,
            "dungeon": 0.5
        }.get(location_type.lower(), 0.15)

        # Roll for encounter
        return random.random() < base_chance

    def generate_random_encounter(self, character_level: int, location_type: str) -> Dict[str, Any]:
        """
        Generate a random encounter.

        Args:
            character_level: Level of the character
            location_type: Type of location

        Returns:
            Encounter data
        """
        # Select encounter type based on weights
        encounter_types = list(self.ENCOUNTER_TYPES.keys())
        weights = list(self.ENCOUNTER_TYPES.values())
        encounter_type = random.choices(encounter_types, weights=weights, k=1)[0]

        # Select difficulty
        difficulty = self._select_difficulty()

        # Generate encounter based on type
        if encounter_type == "combat":
            return self._generate_combat_encounter(character_level, location_type, difficulty)
        elif encounter_type == "obstacle":
            return self._generate_obstacle_encounter(character_level, location_type, difficulty)
        elif encounter_type == "trap":
            return self._generate_trap_encounter(character_level, location_type, difficulty)
        elif encounter_type == "treasure":
            return self._generate_treasure_encounter(character_level, location_type, difficulty)
        elif encounter_type == "npc":
            return self._generate_npc_encounter(character_level, location_type, difficulty)
        else:  # mystery
            return self._generate_mystery_encounter(character_level, location_type, difficulty)

    def _select_difficulty(self) -> str:
        """
        Select a random difficulty based on chances.

        Returns:
            Difficulty string
        """
        difficulties = list(self.DIFFICULTIES.keys())
        chances = [self.DIFFICULTIES[d]["chance"] for d in difficulties]
        return random.choices(difficulties, weights=chances, k=1)[0]

    def _generate_combat_encounter(self, character_level: int, location_type: str, difficulty: str) -> Dict[str, Any]:
        """
        Generate a combat encounter.

        Args:
            character_level: Level of the character
            location_type: Type of location
            difficulty: Difficulty level

        Returns:
            Combat encounter data
        """
        # Determine environment for enemy selection
        environment = self._location_to_environment(location_type)

        # Select enemy type
        enemy_type = random.choice(self.ENEMIES_BY_ENVIRONMENT.get(environment, ["Bandit"]))

        # Determine enemy level based on character level and difficulty
        difficulty_mod = self.DIFFICULTIES[difficulty]["modifier"]
        enemy_level = max(1, int(character_level * difficulty_mod))

        # Determine number of enemies based on difficulty
        if difficulty in ["trivial", "easy"]:
            num_enemies = 1
        elif difficulty == "normal":
            num_enemies = random.randint(1, 2)
        elif difficulty == "hard":
            num_enemies = random.randint(1, 3)
        elif difficulty == "challenging":
            num_enemies = random.randint(2, 4)
        else:  # deadly
            num_enemies = random.randint(3, 5)

        # Generate encounter description using AI
        description = self._generate_encounter_description("combat", enemy_type, num_enemies, difficulty, location_type)

        # Calculate XP reward
        xp_mult = self.DIFFICULTIES[difficulty]["xp_mult"]
        xp_reward = int(25 * character_level * xp_mult * num_enemies)

        return {
            "type": "combat",
            "enemy_type": enemy_type,
            "enemy_level": enemy_level,
            "num_enemies": num_enemies,
            "difficulty": difficulty,
            "description": description,
            "rewards": {
                "xp": xp_reward,
                "gold": int(10 * character_level * difficulty_mod * num_enemies)
            }
        }

    def _generate_obstacle_encounter(self, character_level: int, location_type: str, difficulty: str) -> Dict[str, Any]:
        """
        Generate an obstacle encounter.

        Args:
            character_level: Level of the character
            location_type: Type of location
            difficulty: Difficulty level

        Returns:
            Obstacle encounter data
        """
        # Select obstacle type
        obstacle_type = random.choice(self.OBSTACLE_TYPES)

        # Determine difficulty check DC based on character level and difficulty
        difficulty_mod = self.DIFFICULTIES[difficulty]["modifier"]
        dc = 10 + int(character_level * difficulty_mod)

        # Determine primary attribute for the check
        attributes = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        primary_attribute = random.choice(attributes)

        # Generate encounter description using AI
        description = self._generate_encounter_description("obstacle", obstacle_type, 1, difficulty, location_type)

        # Calculate XP reward
        xp_mult = self.DIFFICULTIES[difficulty]["xp_mult"]
        xp_reward = int(15 * character_level * xp_mult)

        return {
            "type": "obstacle",
            "obstacle_type": obstacle_type,
            "difficulty": difficulty,
            "dc": dc,
            "primary_attribute": primary_attribute,
            "description": description,
            "rewards": {
                "xp": xp_reward
            }
        }

    def _generate_trap_encounter(self, character_level: int, location_type: str, difficulty: str) -> Dict[str, Any]:
        """
        Generate a trap encounter.

        Args:
            character_level: Level of the character
            location_type: Type of location
            difficulty: Difficulty level

        Returns:
            Trap encounter data
        """
        # Select trap type
        trap_type = random.choice(self.TRAP_TYPES)

        # Determine difficulty check DC based on character level and difficulty
        difficulty_mod = self.DIFFICULTIES[difficulty]["modifier"]
        dc = 10 + int(character_level * difficulty_mod)

        # Determine damage if triggered
        damage = int(character_level * 2 * difficulty_mod)

        # Determine detection and disarm attributes
        detection_attribute = random.choice(["wisdom", "intelligence"])
        disarm_attribute = random.choice(["dexterity", "intelligence"])

        # Generate encounter description using AI
        description = self._generate_encounter_description("trap", trap_type, 1, difficulty, location_type)

        # Calculate XP reward
        xp_mult = self.DIFFICULTIES[difficulty]["xp_mult"]
        xp_reward = int(20 * character_level * xp_mult)

        return {
            "type": "trap",
            "trap_type": trap_type,
            "difficulty": difficulty,
            "detection_dc": dc - 2,
            "disarm_dc": dc,
            "damage": damage,
            "detection_attribute": detection_attribute,
            "disarm_attribute": disarm_attribute,
            "description": description,
            "rewards": {
                "xp": xp_reward
            }
        }

    def _generate_treasure_encounter(self, character_level: int, location_type: str, difficulty: str) -> Dict[str, Any]:
        """
        Generate a treasure encounter.

        Args:
            character_level: Level of the character
            location_type: Type of location
            difficulty: Difficulty level

        Returns:
            Treasure encounter data
        """
        # Determine if treasure is guarded
        is_guarded = random.random() < 0.4  # 40% chance

        # Determine treasure quality based on difficulty
        difficulty_mod = self.DIFFICULTIES[difficulty]["modifier"]

        # Determine gold amount
        gold = int(25 * character_level * difficulty_mod * random.uniform(0.8, 1.2))

        # Determine number of items
        num_items = max(1, int(difficulty_mod))

        # Generate encounter description using AI
        description = self._generate_encounter_description("treasure", "chest" if is_guarded else "hidden", num_items, difficulty, location_type)

        # Calculate XP reward
        xp_mult = self.DIFFICULTIES[difficulty]["xp_mult"]
        xp_reward = int(10 * character_level * xp_mult)

        return {
            "type": "treasure",
            "is_guarded": is_guarded,
            "difficulty": difficulty,
            "description": description,
            "rewards": {
                "xp": xp_reward,
                "gold": gold,
                "num_items": num_items
            }
        }

    def _generate_npc_encounter(self, character_level: int, location_type: str, difficulty: str) -> Dict[str, Any]:
        """
        Generate an NPC encounter.

        Args:
            character_level: Level of the character
            location_type: Type of location
            difficulty: Difficulty level

        Returns:
            NPC encounter data
        """
        # Determine NPC disposition
        dispositions = ["friendly", "neutral", "suspicious", "hostile"]
        weights = [0.3, 0.4, 0.2, 0.1]
        disposition = random.choices(dispositions, weights=weights, k=1)[0]

        # Determine NPC type based on location
        npc_types = {
            "city": ["Merchant", "Guard", "Noble", "Beggar", "Artisan"],
            "village": ["Farmer", "Blacksmith", "Innkeeper", "Hunter", "Elder"],
            "road": ["Traveler", "Merchant", "Pilgrim", "Refugee", "Bandit"],
            "forest": ["Hunter", "Druid", "Ranger", "Hermit", "Elf"],
            "mountain": ["Miner", "Dwarf", "Hermit", "Goatherd", "Monk"],
            "desert": ["Nomad", "Merchant", "Explorer", "Mystic", "Bandit"],
            "swamp": ["Fisherman", "Witch", "Hermit", "Alchemist", "Lizardfolk"],
            "cave": ["Miner", "Refugee", "Hermit", "Cultist", "Monster Hunter"],
            "ruins": ["Archaeologist", "Treasure Hunter", "Ghost", "Cultist", "Historian"],
            "dungeon": ["Prisoner", "Guard", "Cultist", "Monster Hunter", "Adventurer"]
        }
        npc_type = random.choice(npc_types.get(location_type.lower(), ["Traveler"]))

        # Generate NPC name using AI
        npc_name = self._generate_npc_name(npc_type)

        # Generate encounter description using AI
        description = self._generate_encounter_description("npc", npc_type, 1, difficulty, location_type, npc_name, disposition)

        # Calculate XP reward
        xp_mult = self.DIFFICULTIES[difficulty]["xp_mult"]
        xp_reward = int(15 * character_level * xp_mult)

        return {
            "type": "npc",
            "npc_name": npc_name,
            "npc_type": npc_type,
            "disposition": disposition,
            "difficulty": difficulty,
            "description": description,
            "rewards": {
                "xp": xp_reward
            }
        }

    def _generate_mystery_encounter(self, character_level: int, location_type: str, difficulty: str) -> Dict[str, Any]:
        """
        Generate a mystery encounter.

        Args:
            character_level: Level of the character
            location_type: Type of location
            difficulty: Difficulty level

        Returns:
            Mystery encounter data
        """
        # Determine mystery type
        mystery_types = ["strange phenomenon", "magical effect", "ancient relic", "mysterious sound", "vision", "omen"]
        mystery_type = random.choice(mystery_types)

        # Generate encounter description using AI
        description = self._generate_encounter_description("mystery", mystery_type, 1, difficulty, location_type)

        # Calculate XP reward
        xp_mult = self.DIFFICULTIES[difficulty]["xp_mult"]
        xp_reward = int(20 * character_level * xp_mult)

        return {
            "type": "mystery",
            "mystery_type": mystery_type,
            "difficulty": difficulty,
            "description": description,
            "rewards": {
                "xp": xp_reward
            }
        }

    def _location_to_environment(self, location_type: str) -> str:
        """
        Convert location type to environment for enemy selection.

        Args:
            location_type: Type of location

        Returns:
            Environment string
        """
        location_lower = location_type.lower()

        if "forest" in location_lower or "wood" in location_lower:
            return "forest"
        elif "mountain" in location_lower or "hill" in location_lower:
            return "mountain"
        elif "desert" in location_lower or "waste" in location_lower:
            return "desert"
        elif "swamp" in location_lower or "marsh" in location_lower:
            return "swamp"
        elif "cave" in location_lower or "cavern" in location_lower:
            return "cave"
        elif "ruin" in location_lower or "temple" in location_lower:
            return "ruins"
        elif "village" in location_lower or "town" in location_lower:
            return "village"
        elif "city" in location_lower or "capital" in location_lower:
            return "city"
        elif "dungeon" in location_lower or "crypt" in location_lower:
            return "dungeon"
        else:
            return "forest"  # Default

    def _generate_encounter_description(self, encounter_type: str, entity_type: str, 
                                       num_entities: int, difficulty: str, 
                                       location_type: str, npc_name: str = None,
                                       disposition: str = None) -> str:
        """
        Generate a description for an encounter using AI.

        Args:
            encounter_type: Type of encounter
            entity_type: Type of entity involved
            num_entities: Number of entities
            difficulty: Difficulty level
            location_type: Type of location
            npc_name: Name of NPC (for NPC encounters)
            disposition: Disposition of NPC (for NPC encounters)

        Returns:
            Encounter description
        """
        try:
            # Prepare context based on encounter type
            if encounter_type == "combat":
                context = f"{num_entities} {entity_type}(s) de dificuldade {difficulty}"
            elif encounter_type == "obstacle":
                context = f"um(a) {entity_type} de dificuldade {difficulty}"
            elif encounter_type == "trap":
                context = f"uma armadilha de {entity_type} de dificuldade {difficulty}"
            elif encounter_type == "treasure":
                context = f"um tesouro {entity_type} de dificuldade {difficulty}"
            elif encounter_type == "npc":
                context = f"{npc_name}, um(a) {entity_type} com disposição {disposition}"
            else:  # mystery
                context = f"um(a) {entity_type} misterioso(a) de dificuldade {difficulty}"

            prompt = f"""
            Gere uma descrição curta e atmosférica para um encontro em um RPG medieval fantástico.
            
            Detalhes do encontro:
            - Tipo: {encounter_type}
            - Entidade: {context}
            - Local: {location_type}
            
            A descrição deve ter 2-3 frases e ser imersiva, descrevendo como o jogador encontra a situação.
            Para encontros de combate, descreva como os inimigos aparecem e sua postura.
            Para obstáculos ou armadilhas, descreva o desafio e sua aparência.
            Para tesouros, descreva como ele está escondido ou guardado.
            Para NPCs, descreva sua aparência e comportamento inicial.
            Para mistérios, descreva o fenômeno estranho e seu efeito imediato.
            
            Responda apenas com a descrição, sem explicações adicionais.
            """

            response = self.ai_client.generate_response(prompt)
            if isinstance(response, str) and response.strip():
                return response.strip()
        except Exception as e:
            logger.error(f"Error generating encounter description: {e}")

        # Fallback descriptions
        fallbacks = {
            "combat": f"Você encontra {num_entities} {entity_type}(s) hostis. Eles parecem prontos para atacar.",
            "obstacle": f"Um(a) {entity_type} bloqueia seu caminho. Você precisará superá-lo(a) para continuar.",
            "trap": f"Você nota uma armadilha de {entity_type} à sua frente. Parece perigosa.",
            "treasure": f"Você encontra o que parece ser um tesouro escondido. Pode conter itens valiosos.",
            "npc": f"Você encontra {npc_name}, um(a) {entity_type}. Ele(a) parece {disposition}.",
            "mystery": f"Você testemunha um(a) {entity_type} estranho(a). É algo que você nunca viu antes."
        }

        return fallbacks.get(encounter_type, "Você encontra algo interessante.")

    def _generate_npc_name(self, npc_type: str) -> str:
        """
        Generate a name for an NPC using AI.

        Args:
            npc_type: Type of NPC

        Returns:
            NPC name
        """
        try:
            prompt = f"""
            Gere um nome para um(a) {npc_type} em um RPG medieval fantástico.
            O nome deve ser adequado para o tipo de personagem e soar fantástico.
            Responda apenas com o nome, sem explicações adicionais.
            """

            response = self.ai_client.generate_response(prompt)
            if isinstance(response, str) and response.strip():
                return response.strip()
        except Exception as e:
            logger.error(f"Error generating NPC name: {e}")

        # Fallback names
        first_names = ["Thorne", "Elara", "Garrick", "Lyra", "Kael", "Seraphina", "Brom", "Isolde", "Darian", "Freya"]
        last_names = ["Ironheart", "Nightshade", "Stormborn", "Silverwood", "Blackthorn", "Frostbeard", "Sunseeker", "Moonshadow"]

        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def generate_critical_failure(self, action_type: str, character_level: int) -> Dict[str, Any]:
        """
        Generate a critical failure outcome.

        Args:
            action_type: Type of action (attack, skill, spell, etc.)
            character_level: Level of the character

        Returns:
            Critical failure data
        """
        # Determine severity based on random chance
        severity_options = ["minor", "moderate", "major"]
        weights = [0.6, 0.3, 0.1]  # 60% minor, 30% moderate, 10% major
        severity = random.choices(severity_options, weights=weights, k=1)[0]

        # Determine consequences based on action type and severity
        consequences = []

        if action_type == "attack":
            if severity == "minor":
                consequences = [
                    "Arma escorrega da mão",
                    "Perde o equilíbrio",
                    "Expõe-se ao contra-ataque"
                ]
            elif severity == "moderate":
                consequences = [
                    "Arma fica presa",
                    "Cai no chão",
                    "Atinge um aliado próximo"
                ]
            else:  # major
                consequences = [
                    "Arma quebra",
                    "Fere-se com a própria arma",
                    "Atrai atenção de inimigos próximos"
                ]
        elif action_type == "skill":
            if severity == "minor":
                consequences = [
                    "Falha constrangedora",
                    "Perde tempo valioso",
                    "Chama atenção indesejada"
                ]
            elif severity == "moderate":
                consequences = [
                    "Quebra equipamento",
                    "Causa dano colateral",
                    "Cria novo problema"
                ]
            else:  # major
                consequences = [
                    "Ferimento acidental",
                    "Piora drasticamente a situação",
                    "Cria perigo iminente"
                ]
        elif action_type == "spell":
            if severity == "minor":
                consequences = [
                    "Efeito invertido",
                    "Magia dissipa-se",
                    "Alvo errado"
                ]
            elif severity == "moderate":
                consequences = [
                    "Efeito colateral inesperado",
                    "Sobrecarga mágica",
                    "Atrai criatura mágica"
                ]
            else:  # major
                consequences = [
                    "Explosão mágica",
                    "Efeito permanente indesejado",
                    "Invoca entidade hostil"
                ]
        else:  # general
            if severity == "minor":
                consequences = [
                    "Tropeça e cai",
                    "Perde um item pequeno",
                    "Chama atenção indesejada"
                ]
            elif severity == "moderate":
                consequences = [
                    "Quebra equipamento importante",
                    "Sofre ferimento leve",
                    "Cria complicação significativa"
                ]
            else:  # major
                consequences = [
                    "Sofre ferimento grave",
                    "Perde item valioso",
                    "Cria perigo mortal"
                ]

        # Select a consequence
        consequence = random.choice(consequences)

        # Determine mechanical effect
        effect = {}
        if severity == "minor":
            effect = {
                "damage": 0,
                "status": "desvantagem na próxima ação",
                "duration": 1
            }
        elif severity == "moderate":
            effect = {
                "damage": int(character_level * 0.5),
                "status": "atordoado",
                "duration": 1
            }
        else:  # major
            effect = {
                "damage": int(character_level * 1.5),
                "status": "incapacitado",
                "duration": 2
            }

        # Generate description using AI
        description = self._generate_critical_failure_description(action_type, severity, consequence)

        return {
            "type": "critical_failure",
            "action_type": action_type,
            "severity": severity,
            "consequence": consequence,
            "effect": effect,
            "description": description
        }

    def _generate_critical_failure_description(self, action_type: str, severity: str, consequence: str) -> str:
        """
        Generate a description for a critical failure using AI.

        Args:
            action_type: Type of action
            severity: Severity of failure
            consequence: Consequence of failure

        Returns:
            Critical failure description
        """
        try:
            prompt = f"""
            Gere uma descrição vívida e detalhada para uma falha crítica em um RPG medieval fantástico.
            
            Detalhes da falha:
            - Tipo de ação: {action_type}
            - Severidade: {severity}
            - Consequência: {consequence}
            
            A descrição deve ter 2-3 frases e ser imersiva, descrevendo como a falha ocorre e suas consequências imediatas.
            Use linguagem colorida e detalhes sensoriais para tornar a cena memorável.
            
            Responda apenas com a descrição, sem explicações adicionais.
            """

            response = self.ai_client.generate_response(prompt)
            if isinstance(response, str) and response.strip():
                return response.strip()
        except Exception as e:
            logger.error(f"Error generating critical failure description: {e}")

        # Fallback description
        return f"Sua tentativa de {action_type} falha terrivelmente. {consequence}, causando problemas para você."
