# c:\Users\rodri\Desktop\REPLIT RPG\core\recipes.py
from typing import Dict, List, Optional, Tuple

# Estrutura da Receita:
# "output_item_id_ref": { # Este ID deve corresponder a um item que pode ser gerado pelo ItemGenerator
#     "name": "Nome do Item Criado", # Nome que aparecerá para o jogador
#     "components": {"component_item_name_or_id": quantity, ...}, # Nomes/IDs dos itens e suas quantidades
#     "skill_required": ("skill_id", level_needed), # Opcional: tupla com (ID da skill, nível mínimo da skill)
#     "description": "Descrição do item criado.",
#     "output_quantity": 1 # Opcional, padrão 1
# }

CRAFTING_RECIPES: Dict[str, Dict] = {
    "sharpened_stick_recipe": {  # ID da receita
        "name": "Lança de Madeira Afiada",
        "components": {
            "Madeira Podre Útil": 1
        },  # Assume "Madeira Podre Útil" é um item_name
        "skill_required": None,
        "description": "Um pedaço de madeira afiado na ponta. Melhor que nada para se defender.",
        "output_item_id_ref": "Lança de Madeira Afiada",  # O nome do item que será criado
    },
    "crude_bandage_recipe": {
        "name": "Bandagem Crua",
        "components": {"Tecido Rasgado Limpo": 2},
        "skill_required": (
            "first_aid_basics",
            1,
        ),  # Requer a skill "first_aid_basics" no nível 1
        "description": "Alguns pedaços de tecido limpos, amarrados para estancar sangramentos leves.",
        "output_item_id_ref": "Bandagem Suja",  # Exemplo: cria uma "Bandagem Suja"
    },
    "molotov_cocktail_recipe": {
        "name": "Coquetel Molotov",
        "components": {
            "Garrafa Vazia": 1,
            "Tecido Rasgado Limpo": 1,
            "Gasolina": 1,
        },  # "Garrafa Vazia", "Gasolina"
        "skill_required": (
            "explosives_crafting",
            1,
        ),  # Supondo uma skill "explosives_crafting"
        "description": "Uma arma incendiária improvisada. Manuseie com cuidado e mire bem.",
        "output_item_id_ref": "Coquetel Molotov",
    },
    "lockpick_set_improvised_recipe": {
        "name": "Kit de Arrombamento Improvisado",
        "components": {
            "Sucata de Metal (pequena)": 3,
            "Arame Fino": 2,
        },
        "skill_required": ("lockpicking", 1),
        "description": "Ferramentas rústicas feitas de sucata para tentar abrir fechaduras simples.",
        "output_item_id_ref": "Kit de Arrombamento Rústico",
    },
    "basic_ammo_bullets_recipe": {
        "name": "Munição de Pistola Básica (x5)",
        "components": {"Sucata de Metal (pequena)": 2, "Pólvora Caseira": 1},
        "skill_required": ("ammo_crafter", 1),
        "description": "Algumas balas de pistola feitas às pressas. Podem falhar.",
        "output_quantity": 5,
        "output_item_id_ref": "balas de pistola",  # Nome do item de munição
    },
}
