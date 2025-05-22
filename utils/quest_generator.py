"""
Quest generator module.

This module provides functions for generating random quests.
"""

import logging
import os
import random
from typing import Any, Dict, List, Optional

# Para gerar recompensas de itens reais
from utils.item_generator import ItemGenerator

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
QUEST_REWARD_CATEGORIES_BY_TYPE = {
    "scavenge": ["consumable_food", "consumable_medical", "material_crafting"],
    "clear_area": ["weapon", "ammo", "protection"],
    "rescue": [
        "consumable_medical",
        "tool",
        "misc",
    ],  # Misc pode ser um item de valor sentimental
    "repair_fortify": ["material_crafting", "tool"],
    "investigate_signal": [
        "ammo",
        "tool",
        "quest",
    ],  # Quest pode ser um item que leva a outra pista
    "deliver_message": ["consumable_food", "misc"],  # Recompensa por um favor
}


def generate_quest(location: str, difficulty: int = 1) -> Dict[str, Any]:
    """
    Generate a random quest.

    Args:
        location: The general location context for the quest.
        difficulty: The difficulty level of the quest, influencing rewards.

    Returns:
        A dictionary containing the details of the generated quest.
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
        quest_type: The type of the quest (e.g., "scavenge", "rescue").
        location: The location context for the quest description.

    Returns:
        A dictionary containing the 'name' and 'description' of the quest.
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
        difficulty: The difficulty level of the quest.
        quest_type: The type of the quest, used to tailor appropriate reward categories.

    Returns:
        A list of item names as rewards.
    """
    # Inicializa o ItemGenerator. O path para 'data' precisa ser relativo ao local de execução
    # ou absoluto. Assumindo que 'data' está no mesmo nível que 'core' e 'utils'.
    # Se utils/quest_generator.py está em utils/, e data/ está em core/, o path precisa ser ajustado.
    # Para simplificar, vamos assumir que o ItemGenerator pode encontrar seu 'data_dir'
    # se chamado a partir de um script no diretório raiz do projeto.
    # Se este script for chamado de dentro de 'core', o path para 'data' seria '../core/data'
    # ou um path absoluto.
    # Para este exemplo, vamos construir um path relativo a partir da localização deste arquivo.
    base_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )  # REPLIT RPG/
    data_dir_for_items = os.path.join(base_dir, "core", "data")
    item_gen = ItemGenerator(data_dir=data_dir_for_items)

    reward_items_generated: List[Dict[str, Any]] = []
    num_rewards = 1 + difficulty // 2

    # Determina categorias de itens apropriadas para o tipo de missão
    reward_categories = QUEST_REWARD_CATEGORIES_BY_TYPE.get(
        quest_type, ["consumable_food", "material_crafting"]
    )

    for _ in range(num_rewards):
        # Seleciona uma categoria de recompensa aleatória apropriada para o tipo de missão
        chosen_category = random.choice(reward_categories)
        item: Optional[Dict[str, Any]] = None

        # Tenta gerar um item da categoria escolhida
        # O ItemGenerator já lida com raridade internamente com base em suas chances
        # A dificuldade da missão pode influenciar o 'level' do item gerado
        item_level_for_generation = max(1, difficulty)

        if chosen_category == "weapon":
            item = item_gen.generate_weapon(level=item_level_for_generation)
        elif chosen_category == "protection":
            item = item_gen.generate_protection(level=item_level_for_generation)
        elif chosen_category.startswith("consumable_"):
            item = item_gen.generate_consumable(
                level=item_level_for_generation, consumable_category=chosen_category
            )
        elif chosen_category == "tool":
            item = item_gen.generate_tool(level=item_level_for_generation)
        elif chosen_category == "material_crafting":
            item = item_gen.generate_material_crafting(level=item_level_for_generation)
        elif chosen_category == "ammo":
            # Gerar um tipo de munição específico ou um item "pacote de munição"
            item = item_gen.generate_consumable(
                level=item_level_for_generation, consumable_category="ammo"
            )  # Supondo que 'ammo' é um tipo de consumível
        elif (
            chosen_category == "misc" or chosen_category == "quest"
        ):  # Itens de quest como recompensa podem ser pistas
            item = item_gen.generate_random_item(
                level=item_level_for_generation
            )  # Mais genérico para misc

        if item and item.get("name"):
            reward_items_generated.append(item)

    # Retorna uma lista de nomes de itens por enquanto, mas idealmente seriam os objetos de item
    return [
        item.get("name", "Item Desconhecido")
        for item in reward_items_generated
        if item.get("name")
    ]


def _get_default_quest(location: str) -> Dict[str, Any]:
    """
    Get a default quest for fallback.

    Args:
        location: The location context for the default quest.

    Returns:
        A dictionary representing a default fallback quest.
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
