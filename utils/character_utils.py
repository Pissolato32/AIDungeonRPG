"""
Character utility functions for consistent attribute, gold, and inventory calculation.
"""
from typing import List, Dict
import random

def calculate_initial_gold(character_class: str, race: str) -> int:
    """
    Calculate initial gold based on class and race, matching frontend logic.
    """
    class_gold = {
        'Warrior': lambda: sum(random.randint(1, 4) for _ in range(5)) * 10,
        'Mage': lambda: sum(random.randint(1, 4) for _ in range(4)) * 10,
        'Rogue': lambda: sum(random.randint(1, 4) for _ in range(4)) * 10,
        'Cleric': lambda: sum(random.randint(1, 4) for _ in range(5)) * 10,
        'Ranger': lambda: sum(random.randint(1, 4) for _ in range(5)) * 10,
        'Barbarian': lambda: sum(random.randint(1, 4) for _ in range(3)) * 10,
    }
    base = class_gold.get(character_class, lambda: 100)()
    race_mod = {
        'Human': 1.0,
        'Elf': 1.1,
        'Dwarf': 1.2,
        'Halfling': 0.9,
        'Orc': 0.8
    }.get(race, 1.0)
    return int(base * race_mod)

def generate_initial_inventory(character_class: str, race: str, strength: int, dexterity: int, intelligence: int, description: str = "") -> List[str]:
    """
    Generate initial inventory based on class, race, attributes, and description (matches frontend logic).
    """
    inventory = []
    # Class items
    if character_class == 'Warrior':
        inventory += ['Basic Sword', 'Wooden Shield', 'Leather Armor']
    elif character_class == 'Mage':
        inventory += ['Apprentice Staff', 'Basic Grimoire', 'Mage Robe']
    elif character_class == 'Rogue':
        inventory += ['Dagger', 'Thieves Tools', 'Dark Cloak']
    elif character_class == 'Cleric':
        inventory += ['Mace', 'Holy Symbol', 'Light Armor']
    elif character_class == 'Ranger':
        inventory += ['Short Bow', 'Quiver with 20 Arrows', 'Leather Armor']
    # Race items
    if race == 'Human':
        inventory += ['Kit de Viagem', 'Cantil']
    elif race == 'Elf':
        inventory += ['Pão Élfico', 'Capa Élfica']
    elif race == 'Dwarf':
        inventory += ['Cerveja Anã', 'Picareta']
    elif race == 'Halfling':
        inventory += ['Cozido em Pote', 'Cachimbo']
    elif race == 'Orc':
        inventory += ['Amuleto Tribal', 'Dente de Troféu']
    # Attribute-based items
    if strength >= 14:
        inventory.append('Machado de Batalha')
    if dexterity >= 14:
        inventory.append('Kit de Armadilhas')
    if intelligence >= 14:
        inventory.append('Pergaminho Mágico')
    # Basic potions
    inventory += ['Poção de Vida Pequena', 'Poção de Stamina Pequena']
    # Description-based items (keywords)
    if description:
        keywords = {
            'guerreiro': 'Espada Afiada',
            'nobre': 'Anel da Família',
            'fazendeiro': 'Enxada Robusta',
            'caçador': 'Faca de Caça',
            'montanha': 'Corda de Escalada',
            'floresta': 'Bússola',
            'mágico': 'Varinha da Sorte',
            'curandeiro': 'Ervas Medicinais',
            'artesão': 'Ferramentas de Artesão',
            'mercenário': 'Medalha de Veterano',
            'fogo': 'Pederneira',
            'água': 'Frasco de Água Benta',
            'comerciante': 'Balança de Comerciante',
            'sobrevivente': 'Kit de Sobrevivência',
            'antigo': 'Relíquia de Família',
            'academia': 'Livro de Conhecimento',
            'templo': 'Amuleto Religioso',
            'instrumento': 'Flauta de Madeira',
            'música': 'Ocarina',
            'arco': 'Arco Longo',
            'machado': 'Machado de Lenhador',
            'facas': 'Conjunto de Facas',
            'oculto': 'Amuleto Misterioso',
            'guerra': 'Insígnia Militar'
        }
        lower_desc = description.lower()
        for k, v in keywords.items():
            if k in lower_desc and v not in inventory:
                inventory.append(v)
                if len(inventory) > 10:
                    break
    return inventory
