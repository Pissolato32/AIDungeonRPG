
TRANSLATIONS = {
    "pt-br": {
        "welcome": "Bem-vindo ao jogo!",
        "health": "Saúde",
        "stamina": "Energia",
        "inventory": "Inventário",
        "gold": "Ouro",
        "level": "Nível",
        "experience": "Experiência",
        "combat": {
            "attack": "Atacar",
            "flee": "Fugir",
            "use_item": "Usar Item",
            "enemy_appears": "Um {} aparece!",
            "victory": "Você derrotou o {}!",
            "defeat": "Você foi derrotado!"
        }
    },
    "en": {
        "welcome": "Welcome to the game!",
        "health": "Health",
        "stamina": "Stamina",
        "inventory": "Inventory",
        "gold": "Gold",
        "level": "Level",
        "experience": "Experience",
        "combat": {
            "attack": "Attack",
            "flee": "Flee",
            "use_item": "Use Item",
            "enemy_appears": "A {} appears!",
            "victory": "You defeated the {}!",
            "defeat": "You were defeated!"
        }
    }
}

def get_text(key, lang="pt-br", *args):
    """Get translated text for given key and language"""
    keys = key.split('.')
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    
    for k in keys:
        text = text.get(k, key)
        
    if isinstance(text, str) and args:
        return text.format(*args)
    return text
