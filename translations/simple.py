"""
Módulo de tradução simplificado.
"""


def get_text(key, language=None, *args, **kwargs):
    """
    Função simplificada para obter texto traduzido.

    Args:
        key: Chave de tradução
        language: Idioma (ignorado nesta versão simplificada)
        *args, **kwargs: Argumentos para formatação

    Returns:
        Texto traduzido
    """
    # Dicionário simplificado de traduções
    translations = {
        "create_character": "Criar Personagem",
        "edit_character": "Editar Personagem",
        "character_name": "Nome do Personagem",
        "character_class": "Classe",
        "character_race": "Raça",
        "save_changes": "Salvar Alterações",
        "continue_game": "Continuar Jogo",
        "game_title": "WebChatRPG - Jogo de Aventura",
        "health": "Saúde",
        "stamina": "Energia",
        "hunger": "Fome",
        "thirst": "Sede",
        "strength": "Força",
        "dexterity": "Destreza",
        "constitution": "Constituição",
        "intelligence": "Inteligência",
        "wisdom": "Sabedoria",
        "charisma": "Carisma",
        "inventory": "Inventário",
        "quests": "Missões",
        "map": "Mapa",
        "attributes": "Atributos",
        "reset_game": "Reiniciar Jogo",
        "cancel": "Cancelar",
        "no_quests": "Sem missões ativas",
        "completed": "Concluída",
        "in_progress": "Em Progresso",
        "reset_game_confirmation": "Tem certeza que deseja reiniciar o jogo? Isso irá apagar seu progresso atual.",
    }

    # Retorna a tradução ou a própria chave se não encontrada
    text = translations.get(key, key)

    # Aplica formatação se necessário
    if args or kwargs:
        try:
            return text.format(*args, **kwargs)
        except:
            return text

    return text
