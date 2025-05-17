"""
Quest generator module.

This module provides functions for generating random quests.
"""

import logging
import random
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# Quest types and targets
QUEST_TYPES = [
    "scavenge",  # Coletar suprimentos
    "clear_area",  # Eliminar ameaças
    "rescue",  # Resgatar alguém
    "repair_fortify",  # Consertar ou fortalecer algo
    "investigate_signal",  # Investigar um sinal, barulho, etc.
    "deliver_message",  # Levar uma mensagem ou item pequeno
]
QUEST_TARGETS = {
    "scavenge": [
        "comida enlatada",
        "água purificada",
        "suprimentos médicos",
        "munição",
        "combustível",
        "peças de rádio",
    ],
    "clear_area": [
        "ninho de zumbis",
        "grupo de saqueadores",
        "zumbis bloqueando rota",
        "ameaça desconhecida",
    ],
    "rescue": [
        "sobrevivente preso",
        "criança perdida",
        "médico capturado",
        "engenheiro desaparecido",
    ],
    "repair_fortify": [
        "gerador do abrigo",
        "barricadas externas",
        "sistema de purificação de água",
        "torre de rádio",
    ],
    "investigate_signal": [
        "sinal de rádio fraco",
        "fumaça distante",
        "barulho estranho à noite",
        "local de queda de helicóptero",
    ],
    "deliver_message": [
        "mensagem para outro abrigo",
        "mapa de rotas seguras",
        "aviso sobre horda",
        "pedido de ajuda",
    ],
}
QUEST_LOCATIONS_CONTEXT = {  # For adding context to quest descriptions
    "hospital abandonado": "no perigoso hospital abandonado",
    "shopping center saqueado": "no traiçoeiro shopping center saqueado",
    "ruas devastadas da cidade": "nas ruas infestadas da cidade",
    "abrigo subterrâneo": "dentro do nosso próprio abrigo",
    # Placeholder
    "posto avançado de sobreviventes": "no posto avançado aliado de {nome_posto_avancado}",
}


def generate_quest(location: str, difficulty: int = 1) -> Dict[str, Any]:
    """
    Generate a random quest.

    Args:
        location: Quest location
        difficulty: Quest difficulty

    Returns:
        Dictionary with quest details
    """
    try:
        # Select random quest type
        quest_type = random.choice(QUEST_TYPES)

        # Generate quest details based on type
        location_context = QUEST_LOCATIONS_CONTEXT.get(
            location.lower(), f"em {location}"
        )  # Get specific context or generic
        quest_details = _generate_quest_details(quest_type, location_context)

        # Create quest data
        quest = {
            "name": quest_details["name"],
            "description": quest_details["description"],
            "difficulty": difficulty,
            "reward_gold": 50 * difficulty,
            "reward_xp": 100 * difficulty,  # XP can still be a thing
            "reward_items": _generate_quest_rewards(
                difficulty, quest_type
            ),  # Rewards can depend on quest type
            "status": "active",
            "progress": 0,
        }

        logger.info(f"Quest generated: {quest['name']}")
        return quest

    except Exception as e:
        logger.error(f"Error generating quest: {e}")
        # Return fallback quest
        return _get_default_quest(location)


def _generate_quest_details(quest_type: str, location: str) -> Dict[str, str]:
    """
    Generate quest name and description based on type.

    Args:
        quest_type: Quest type
        location: Quest location

    Returns:
        Dictionary with quest name and description
    """
    target_key = random.choice(QUEST_TARGETS[quest_type])
    target_name = target_key  # Using the key directly as we removed translations

    # Generic quest name and description structure
    # Specific quest types can override this if needed
    # Example: "Coletar: Comida Enlatada" or "Limpar Área: Ninho de Zumbis"
    name = f"{
        quest_type.replace(
            '_', ' ').capitalize()}: {
        target_name.capitalize()}"
    # Example: "Precisamos de Comida Enlatada. Procure por algumas em {location}."
    description = (
        f"Complete a tarefa relacionada a {target_name.lower()} em {location}."
    )

    # Specific adjustments for certain quest types
    if quest_type == "rescue":
        rescued_person_type = target_name  # e.g. "Sobrevivente Preso"
        name = f"Resgatar: {rescued_person_type.capitalize()}"
        description = f"Alguém precisa de resgate ({
                rescued_person_type.lower()}) em {location}."

    elif quest_type == "repair_fortify":
        item_to_fix = target_name  # e.g. "Gerador do Abrigo"
        name = f"Reparar: {item_to_fix.capitalize()}"
        description = f"O {
                item_to_fix.lower()} em {location} precisa de reparos urgentes."

    return {"name": name, "description": description}


def _generate_quest_rewards(difficulty: int, quest_type: str) -> List[str]:
    """
    Generate quest rewards based on difficulty and quest type.

    Args:
        difficulty: Quest difficulty
        quest_type: The type of quest, to tailor rewards

    Returns:
        List of reward items (as strings for now, could be item objects later)
    """
    rewards = []
    num_rewards = 1 + difficulty // 2

    # Base rewards pool
    possible_rewards = {
        "low_tier": [
            "Comida Enlatada",
            "Bandagens Sujas (x2)",
            "Algumas Balas de Pistola",
            "Pequena Sucata de Metal",
        ],
        "mid_tier": [
            "Kit de Primeiros Socorros Simples",
            "Garrafa de Água Purificada",
            "Alguns Cartuchos de Espingarda",
            "Fita Adesiva",
        ],
        "high_tier": [
            "Faca de Combate decente",  # Placeholder for actual item generation
            "Um curso de Antibióticos",
            "Peças Eletrônicas Valiosas",
            "Caixa de Balas de Rifle",
        ],
    }

    # Tailor rewards based on quest type
    if quest_type == "scavenge":
        # Scavenge quests might give more of what was scavenged or related
        # tools
        if (
            "munição" in quest_type
        ):  # Simple check, ideally use target_name from _generate_quest_details
            possible_rewards["low_tier"].append("Mais Balas de Pistola")
        else:
            possible_rewards["low_tier"].append("Comida Enlatada Extra")
    elif quest_type == "clear_area":
        possible_rewards["mid_tier"].append("Cano Reforçado")

    for _ in range(num_rewards):
        if difficulty <= 1:
            rewards.append(random.choice(possible_rewards["low_tier"]))
        elif difficulty <= 3:
            rewards.append(
                random.choice(
                    possible_rewards["low_tier"] + possible_rewards["mid_tier"]
                )
            )
        else:
            rewards.append(
                random.choice(
                    possible_rewards["mid_tier"] + possible_rewards["high_tier"]
                )
            )

    return list(set(rewards))  # Ensure unique rewards if multiple are chosen


def _get_default_quest(location: str) -> Dict[str, Any]:
    """
    Get a default quest for fallback.

    Args:
        location: Quest location

    Returns:
        Default quest data
    """
    return {
        "name": "Tarefa Simples de Sobrevivência",
        "description": f"Ajude com o que for preciso em {location} para sobreviver mais um dia.",
        "difficulty": 1,
        "reward_gold": 10,  # Could be "caps", "scrap", etc.
        "reward_xp": 25,
        "reward_items": ["Uma Lata de Comida"],
        "status": "active",
        "progress": 0,
    }
