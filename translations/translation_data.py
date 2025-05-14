"""
Translation data module.

This module contains the translation data for the game.
Separating this data from the translation manager improves maintainability.
"""

from typing import Dict, Any

# Default language for fallback
DEFAULT_LANGUAGE = "pt-br"

# Translation data dictionary
# Contains all translations for all supported languages
TRANSLATIONS: Dict[str, Dict[str, Any]] = {
    "pt-br": {
        # Character-related translations
        "character": {
            "not_enough_stamina": "{} não tem energia suficiente para {}"
        },
        "welcome": "Bem-vindo ao jogo!",
        "health": "Saúde",
        "stamina": "Energia",
        "hunger": "Fome",
        "thirst": "Sede",
        "inventory": "Inventário",
        "gold": "Ouro",
        "level": "Nível",
        "experience": "Experiência",
        "character": "Personagem",
        "attributes": "Atributos",
        "stats": "Estatísticas",
        "quests": "Missões",
        "empty_inventory": "Seu inventário está vazio",
        
        # Character attributes
        "strength": "Força",
        "dexterity": "Destreza",
        "constitution": "Constituição",
        "intelligence": "Inteligência",
        "wisdom": "Sabedoria",
        "charisma": "Carisma",
        
        # Character creation
        "create_character": "Criar Personagem",
        "edit_character": "Editar Personagem",
        "character_name": "Nome do Personagem",
        "character_class": "Classe",
        "character_race": "Raça",
        "character_description": "Descrição do Personagem",
        "save_changes": "Salvar Alterações",
        "continue_game": "Continuar Jogo",
        "roll_dice": "Jogar Dados",
        "remaining_rolls": "Jogadas Restantes",
        "total_points": "Pontos Totais",
        "character_info": "Informações do Personagem",
        
        # Classes
        "warrior": "Guerreiro",
        "mage": "Mago",
        "rogue": "Ladino",
        "cleric": "Clérigo",
        "ranger": "Patrulheiro",
        
        # Races
        "human": "Humano",
        "elf": "Elfo",
        "dwarf": "Anão",
        "halfling": "Halfling",
        "orc": "Orc",
        
        # Game UI
        "game_title": "WebChatRPG - Jogo de Aventura",
        "reset_game": "Reiniciar Jogo",
        "reset_confirm": "Tem certeza que deseja reiniciar o jogo? Isso irá apagar seu progresso atual e dados do personagem.",
        "cancel": "Cancelar",
        "confirm": "Confirmar",
        "loading": "Carregando...",
        "error_occurred": "Ocorreu um erro. Por favor, tente novamente.",
        "npcs_present": "NPCs Presentes",
        "events": "Eventos",
        "combat_log": "Registro de Combate",
        
        # Actions
        "move": "Mover",
        "look": "Olhar",
        "talk": "Falar",
        "search": "Procurar",
        "custom": "Personalizado",
        "rest": "Descansar",
        "enter_details": "Digite os detalhes...",
        
        # Combat
        "combat": {
            "attack": "Atacar",
            "flee": "Fugir",
            "use_item": "Usar Item",
            "enemy_appears": "Um {} aparece!",
            "victory": "Você derrotou o {}!",
            "defeat": "Você foi derrotado!",
            "combat_interface": "Interface de Combate",
            "enemy_description": "Descrição do inimigo",
            "basic_attack": "Ataque Básico",
            "light_attack": "Ataque Leve",
            "heavy_attack": "Ataque Pesado",
            "hit": "Você acertou o {} com um ataque {} por {} de dano!",
            "miss": "Seu ataque {} errou o {}!",
            "enemy_attack": "O {} ataca você por {} de dano!",
            "not_in_combat": "Você não está em combate.",
            "nothing_to_attack": "Não há nada para atacar.",
            "flee_success": "Você conseguiu fugir do {}.",
            "flee_fail": "Você falhou em fugir. O {} ataca você por {} de dano enquanto você tenta escapar!",
            "defeated_while_fleeing": "O {} derrotou você enquanto tentava escapar!",
            "not_enough_stamina": "Você não tem energia suficiente para {}. Você precisa de {} de energia."
        },
        
        # Items
        "items": {
            "use": "Usar",
            "health_potion": "Poção de Vida",
            "stamina_potion": "Poção de Energia",
            "antidote": "Antídoto",
            "bandages": "Bandagens",
            "torch": "Tocha",
            "rope": "Corda",
            "map_fragment": "Fragmento de Mapa",
            "basic_sword": "Espada Básica",
            "wolf_pelt": "Pele de Lobo",
            "sharp_tooth": "Dente Afiado",
            "bat_wing": "Asa de Morcego",
            "bat_fang": "Presa de Morcego",
            "goat_horn": "Chifre de Cabra",
            "tough_hide": "Couro Resistente",
            "stolen_coin_purse": "Bolsa de Moedas Roubada",
            "rusty_dagger": "Adaga Enferrujada",
            "empty_bottle": "Garrafa Vazia",
            "brass_knuckles": "Soco Inglês",
            "use_message": {
                "health_potion": "Você bebe a Poção de Vida e sente suas feridas se fechando. Você recupera {} de vida.",
                "stamina_potion": "Você bebe a Poção de Energia e se sente revigorado. Você recupera {} de energia.",
                "antidote": "Você usa o Antídoto. Quaisquer efeitos de veneno são neutralizados.",
                "bandages": "Você aplica as Bandagens em suas feridas. Você recupera {} de vida.",
                "torch": "Você acende a Tocha, iluminando a área ao seu redor.",
                "rope": "Você prepara a Corda para uso. Pode ser útil para escalar ou descer.",
                "map_fragment": "Você examina o Fragmento de Mapa. Ele revela parte da área ao redor."
            },
            "not_found": "Você não possui um {}.",
            "must_specify": "Você deve especificar um item para usar.",
            "cannot_use": "Você não pode usar esse item."
        },
        
        # Locations
        "locations": {
            "village_center": "Centro da Vila",
            "tavern": "Taverna",
            "blacksmith": "Ferreiro",
            "village_gate": "Portão da Vila",
            "forest_path": "Caminho da Floresta",
            "mountain_trail": "Trilha da Montanha",
            "cave_entrance": "Entrada da Caverna",
            "river_crossing": "Travessia do Rio",
            "abandoned_mine": "Mina Abandonada",
            "ancient_ruins": "Ruínas Antigas",
            "dark_forest": "Floresta Sombria",
            "swamp": "Pântano",
            "desert_oasis": "Oásis do Deserto",
            "frozen_tundra": "Tundra Congelada",
            "volcanic_region": "Região Vulcânica"
        },
        
        # NPCs
        "npcs": {
            "village_elder": "Ancião da Vila",
            "merchant": "Comerciante",
            "blacksmith": "Ferreiro",
            "innkeeper": "Taverneiro",
            "guard": "Guarda",
            "farmer": "Fazendeiro",
            "hunter": "Caçador",
            "wizard": "Mago",
            "priest": "Sacerdote",
            "wandering_merchant": "Comerciante Ambulante",
            "mysterious_stranger": "Estranho Misterioso",
            "old_beggar": "Velho Mendigo",
            "young_child": "Criança Jovem",
            "noble": "Nobre",
            "bandit": "Bandido"
        },
        
        # Enemies
        "enemies": {
            "wild_wolf": "Lobo Selvagem",
            "giant_bat": "Morcego Gigante",
            "mountain_goat": "Cabra da Montanha",
            "thief": "Ladrão",
            "drunk_brawler": "Brigão Bêbado",
            "goblin": "Goblin",
            "skeleton": "Esqueleto",
            "zombie": "Zumbi",
            "giant_spider": "Aranha Gigante",
            "slime": "Gosma",
            "bandit": "Bandido",
            "orc_warrior": "Guerreiro Orc",
            "troll": "Troll",
            "bear": "Urso",
            "wolf_pack": "Alcateia de Lobos"
        },
        
        # Action responses
        "action_responses": {
            "move_success": "Você se move para {}.",
            "move_fail": "Você não pode se mover para lá.",
            "look_around": "Você olha ao redor de {}, observando seus arredores.",
            "look_at": "Você olha para o {}.",
            "talk_to": "Você conversa com {}.",
            "no_one_to_talk": "Não há ninguém chamado {} aqui para conversar.",
            "search_success": "Você procura cuidadosamente.",
            "search_find_item": "Você encontra um {}.",
            "search_find_gold": "Você também encontra {} moedas de ouro.",
            "search_find_secret": "Você descobre um segredo: {}",
            "search_nothing": "Você procura minuciosamente, mas não encontra nada de interesse.",
            "rest_success": "Você descansa por um tempo e se sente revigorado. Você recupera alguma vida e energia.",
            "level_up": "Você subiu para o nível {}!"
        },
        
        # Custom actions
        "custom_actions": {
            "climb": "Você escala {} com sucesso, embora exija algum esforço.",
            "jump": "Você pula sobre {} com um salto ágil.",
            "swim": "Você nada através de {}, a água é refrescante mas cansativa.",
            "dance": "Você dança energicamente. É divertido, mas cansativo.",
            "sing": "Você canta {}. Sua voz ecoa nos arredores.",
            "generic": "Você {} {} com algum esforço."
        },
        
        # Error messages
        "errors": {
            "no_active_session": "Nenhuma sessão ativa",
            "no_character_found": "Nenhum personagem encontrado",
            "action_error": "Ocorreu um erro: {}",
            "reset_error": "Erro ao reiniciar o jogo: {}"
        }
    },
    
    # English translations
    "en": {
        "character": {
            "not_enough_stamina": "{} doesn't have enough stamina for {}"
        },
        "welcome": "Welcome to the game!",
        "health": "Health",
        "stamina": "Stamina",
        "hunger": "Hunger",
        "thirst": "Thirst",
        "inventory": "Inventory",
        "gold": "Gold",
        "level": "Level",
        "experience": "Experience",
        "character": "Character",
        "attributes": "Attributes",
        "stats": "Stats",
        "quests": "Quests",
        "empty_inventory": "Your inventory is empty",
        
        # Character attributes
        "strength": "Strength",
        "dexterity": "Dexterity",
        "constitution": "Constitution",
        "intelligence": "Intelligence",
        "wisdom": "Wisdom",
        "charisma": "Charisma",
        
        # Character creation
        "create_character": "Create Character",
        "edit_character": "Edit Character",
        "character_name": "Character Name",
        "character_class": "Class",
        "character_race": "Race",
        "character_description": "Character Description",
        "save_changes": "Save Changes",
        "continue_game": "Continue Game",
        "roll_dice": "Roll Dice",
        "remaining_rolls": "Remaining Rolls",
        "total_points": "Total Points",
        "character_info": "Character Info",
        
        # Classes
        "warrior": "Warrior",
        "mage": "Mage",
        "rogue": "Rogue",
        "cleric": "Cleric",
        "ranger": "Ranger",
        
        # Races
        "human": "Human",
        "elf": "Elf",
        "dwarf": "Dwarf",
        "halfling": "Halfling",
        "orc": "Orc",
        
        # Game UI
        "game_title": "WebChatRPG - Adventure Game",
        "reset_game": "Reset Game",
        "reset_confirm": "Are you sure you want to reset the game? This will delete your current game progress and character data.",
        "cancel": "Cancel",
        "confirm": "Confirm",
        "loading": "Loading...",
        "error_occurred": "An error occurred. Please try again.",
        "npcs_present": "NPCs Present",
        "events": "Events",
        "combat_log": "Combat Log",
        
        # Actions
        "move": "Move",
        "look": "Look",
        "talk": "Talk",
        "search": "Search",
        "custom": "Custom",
        "rest": "Rest",
        "enter_details": "Enter details...",
        
        # Combat
        "combat": {
            "attack": "Attack",
            "flee": "Flee",
            "use_item": "Use Item",
            "enemy_appears": "A {} appears!",
            "victory": "You defeated the {}!",
            "defeat": "You were defeated!",
            "combat_interface": "Combat Interface",
            "enemy_description": "Enemy description",
            "basic_attack": "Basic Attack",
            "light_attack": "Light Attack",
            "heavy_attack": "Heavy Attack",
            "hit": "You hit the {} with a {} attack for {} damage!",
            "miss": "Your {} attack missed the {}!",
            "enemy_attack": "The {} attacks you for {} damage!",
            "not_in_combat": "You are not in combat.",
            "nothing_to_attack": "There is nothing to attack.",
            "flee_success": "You successfully flee from the {}.",
            "flee_fail": "You failed to flee. The {} attacks you for {} damage as you try to escape!",
            "defeated_while_fleeing": "The {} defeated you as you tried to escape!",
            "not_enough_stamina": "You don't have enough stamina to {}. You need {} stamina."
        },
        
        # Items
        "items": {
            "use": "Use",
            "health_potion": "Health Potion",
            "stamina_potion": "Stamina Potion",
            "antidote": "Antidote",
            "bandages": "Bandages",
            "torch": "Torch",
            "rope": "Rope",
            "map_fragment": "Map Fragment",
            "basic_sword": "Basic Sword",
            "wolf_pelt": "Wolf Pelt",
            "sharp_tooth": "Sharp Tooth",
            "bat_wing": "Bat Wing",
            "bat_fang": "Bat Fang",
            "goat_horn": "Goat Horn",
            "tough_hide": "Tough Hide",
            "stolen_coin_purse": "Stolen Coin Purse",
            "rusty_dagger": "Rusty Dagger",
            "empty_bottle": "Empty Bottle",
            "brass_knuckles": "Brass Knuckles",
            "use_message": {
                "health_potion": "You drink the Health Potion and feel your wounds closing. You heal for {} HP.",
                "stamina_potion": "You drink the Stamina Potion and feel energized. You recover {} stamina.",
                "antidote": "You use the Antidote. Any poison effects are neutralized.",
                "bandages": "You apply the Bandages to your wounds. You heal for {} HP.",
                "torch": "You light the Torch, illuminating the area around you.",
                "rope": "You prepare the Rope for use. It might be helpful for climbing or descending.",
                "map_fragment": "You examine the Map Fragment. It reveals part of the surrounding area."
            },
            "not_found": "You do not have a {}.",
            "must_specify": "You must specify an item to use.",
            "cannot_use": "You cannot use that item."
        },
        
        # Locations
        "locations": {
            "village_center": "Village Center",
            "tavern": "Tavern",
            "blacksmith": "Blacksmith",
            "village_gate": "Village Gate",
            "forest_path": "Forest Path",
            "mountain_trail": "Mountain Trail",
            "cave_entrance": "Cave Entrance",
            "river_crossing": "River Crossing",
            "abandoned_mine": "Abandoned Mine",
            "ancient_ruins": "Ancient Ruins",
            "dark_forest": "Dark Forest",
            "swamp": "Swamp",
            "desert_oasis": "Desert Oasis",
            "frozen_tundra": "Frozen Tundra",
            "volcanic_region": "Volcanic Region"
        },
        
        # NPCs
        "npcs": {
            "village_elder": "Village Elder",
            "merchant": "Merchant",
            "blacksmith": "Blacksmith",
            "innkeeper": "Innkeeper",
            "guard": "Guard",
            "farmer": "Farmer",
            "hunter": "Hunter",
            "wizard": "Wizard",
            "priest": "Priest",
            "wandering_merchant": "Wandering Merchant",
            "mysterious_stranger": "Mysterious Stranger",
            "old_beggar": "Old Beggar",
            "young_child": "Young Child",
            "noble": "Noble",
            "bandit": "Bandit"
        },
        
        # Enemies
        "enemies": {
            "wild_wolf": "Wild Wolf",
            "giant_bat": "Giant Bat",
            "mountain_goat": "Mountain Goat",
            "thief": "Thief",
            "drunk_brawler": "Drunk Brawler",
            "goblin": "Goblin",
            "skeleton": "Skeleton",
            "zombie": "Zombie",
            "giant_spider": "Giant Spider",
            "slime": "Slime",
            "bandit": "Bandit",
            "orc_warrior": "Orc Warrior",
            "troll": "Troll",
            "bear": "Bear",
            "wolf_pack": "Wolf Pack"
        },
        
        # Action responses
        "action_responses": {
            "move_success": "You move to {}.",
            "move_fail": "You cannot move there.",
            "look_around": "You look around {}, taking in your surroundings.",
            "look_at": "You look at the {}.",
            "talk_to": "You have a conversation with {}.",
            "no_one_to_talk": "There is no {} here to talk to.",
            "search_success": "You search the area carefully.",
            "search_find_item": "You find a {}.",
            "search_find_gold": "You also find {} gold coins.",
            "search_find_secret": "You discover a secret: {}",
            "search_nothing": "You search the area thoroughly but find nothing of interest.",
            "rest_success": "You rest for a while and feel refreshed. You recover some health and stamina.",
            "level_up": "You leveled up to level {}!"
        },
        
        # Custom actions
        "custom_actions": {
            "climb": "You climb {} successfully, though it takes some effort.",
            "jump": "You jump over {} with a nimble leap.",
            "swim": "You swim through {}, the water is refreshing but tiring.",
            "dance": "You dance energetically. It's fun but tiring.",
            "sing": "You sing {}. Your voice echoes in the surroundings.",
            "generic": "You {} {} with some effort."
        },
        
        # Error messages
        "errors": {
            "no_active_session": "No active session",
            "no_character_found": "No character found",
            "action_error": "An error occurred: {}",
            "reset_error": "Error resetting game: {}"
        }
    }
}