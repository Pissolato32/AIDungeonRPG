"""
Character utility functions for consistent attribute, gold, and inventory calculation.
"""

import random
from typing import Any, Dict, List, Union


def calculate_initial_gold() -> int:  # Removido race
    """
    Calculate initial "currency" for a survivor.
    """
    # Sobreviventes começam com poucos recursos "monetários"
    base_currency = random.randint(5, 30)
    return int(base_currency)


def generate_initial_inventory(
    # race: str, # Removido
    strength: int,
    dexterity: int,
    intelligence: int,
    description: str = "",
) -> List[Union[str, Dict[str, Any]]]:
    """
    Generate initial inventory for a survivor based on attributes and description.
    No longer depends on class or race.
    """
    inventory: List[Union[str, Dict[str, Any]]] = (
        [  # Itens básicos para qualquer sobrevivente
            "Faca de Cozinha Enferrujada",  # Já presente no CharacterManager, mas pode ser reforçado aqui
            "Bandagem Suja",
            "Lata de Comida Amassada",
            "Garrafa de Água (metade)",
            "Mochila Pequena e Gasta",
        ]
    )

    # Item padrão que antes poderia ser baseado na raça "Humano"
    inventory.append("Isqueiro (pouco gás)")

    # Itens baseados em atributos
    if strength >= 14:
        inventory.append("Pé de Cabra Pequeno")
    if dexterity >= 14:
        inventory.append(
            "Kit de Arrombamento Improvisado"
        )  # Ou "Grampos de Cabelo (para fechaduras)"
    if intelligence >= 14:
        inventory.append("Manual de Primeiros Socorros Danificado")

    # Itens baseados na descrição (palavras-chave para apocalipse zumbi)
    if description:
        keywords = {
            "médico": "Seringa Esterilizada (1)",  # Ou "Analgésicos (dose extra)"
            "engenheiro": "Rolo de Fita Adesiva Resistente",  # Ou "Multiferramenta Enferrujada"
            "policial": "Cassetete Policial Gasto",
            "militar": "Faca de Combate Desgastada",  # Ou "Cantil Militar"
            "cozinheiro": "Cutelo Afiado",
            "mecânico": "Chave Inglesa Ajustável",
            "professor": "Livro sobre Plantas Comestíveis (anotado)",
            "atleta": "Barra de Proteína (última)",
            "solitário": "Diário Vazio e Caneta Falhando",
            "cauteloso": "Pequeno Espelho Quebrado (para olhar esquinas)",
            "religioso": "Terço Desgastado",  # Ou "Bíblia Pequena"
            "artista": "Caderno de Desenho e Carvão",
        }
        lower_desc = description.lower()
        for k, v in keywords.items():
            if k in lower_desc and v not in inventory:
                inventory.append(v)
                if len(inventory) > 8:  # Limitar um pouco o inventário inicial
                    break
    return list(set(inventory))  # Garante itens únicos e remove duplicatas se houver
