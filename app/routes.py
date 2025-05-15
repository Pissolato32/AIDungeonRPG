"""
Routes for the RPG game.

This module defines the web routes for the RPG game.
"""

import os
import logging
import uuid
from typing import Dict, Any, Optional, Union
from flask import (
    render_template, request, redirect, url_for, 
    session, jsonify, Blueprint
)

from core.models import Character
from core.game_engine import GameEngine
from utils.data_io import save_data, load_data

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('routes', __name__)

# Initialize game engine
game_engine = GameEngine()

@bp.route('/')
def index():
    """Render the index page."""
    return render_template('index.html')

@bp.route('/character', methods=['GET', 'POST'])
def character():
    """Render the character creation/selection page."""
    if request.method == 'POST':
        # Import CharacterManager here to avoid circular import
        from web.character_manager import CharacterManager
        # Generate a unique ID for the user
        user_id = str(uuid.uuid4().hex)
        session['user_id'] = user_id

        # Coletar todos os dados do formulário
        character_data = dict(request.form)
        character_data['user_id'] = user_id

        # Criar personagem usando o CharacterManager (garante ouro/inventário corretos)
        character = CharacterManager.create_character_from_form(character_data)
        character.user_id = user_id  # garantir user_id correto

        # Save character data
        save_data(character.to_dict(), f'character_{user_id}.json')

        # Initialize game state
        game_state = game_engine.create_game_state(character)
        save_data(game_state.to_dict(), f'game_state_{user_id}.json')

        # Redirect to game
        return redirect(url_for('routes.game'))

    # GET request - show character creation form
    # Get all existing characters
    existing_characters = []
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.startswith('character_') and filename.endswith('.json'):
                character_data = load_data(filename)
                if character_data:
                    # Extract user_id from filename
                    user_id = filename.replace('character_', '').replace('.json', '')
                    character_data['user_id'] = user_id
                    existing_characters.append(character_data)
    
    return render_template('character.html', existing_characters=existing_characters)

@bp.route('/select_character/<user_id>')
def select_character(user_id):
    """Select an existing character."""
    # Set the user_id in the session
    session['user_id'] = user_id
    
    # Redirect to game
    return redirect(url_for('routes.game'))

@bp.route('/delete_character/<user_id>')
def delete_character(user_id):
    """Delete an existing character."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    
    # Delete character file
    character_file = os.path.join(data_dir, f'character_{user_id}.json')
    if os.path.exists(character_file):
        os.remove(character_file)
    
    # Delete game state file
    game_state_file = os.path.join(data_dir, f'game_state_{user_id}.json')
    if os.path.exists(game_state_file):
        os.remove(game_state_file)
    
    # Redirect back to character page
    return redirect(url_for('routes.character'))

@bp.route('/game')
def game():
    """Render the main game page."""
    # Check if user has a character
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('routes.character'))

    # Load character data
    character_data = load_data(f'character_{user_id}.json')
    if not character_data:
        return redirect(url_for('routes.character'))

    # Create character object
    character = Character.from_dict(character_data)

    # Load game state
    game_state_data = load_data(f'game_state_{user_id}.json')
    if not game_state_data:
        # Initialize new game state
        game_state = game_engine.create_game_state(character)
        save_data(game_state.to_dict(), f'game_state_{user_id}.json')
    else:
        game_state = game_engine.load_game_state(game_state_data)

    # Render game template
    return render_template('game.html', character=character, game_state=game_state)

@bp.route('/api/action', methods=['POST'])
def api_action():
    """Handle game actions via API."""
    # Check if user has a character
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'No character found'})

    # Load character data
    character_data = load_data(f'character_{user_id}.json')
    if not character_data:
        return jsonify({'success': False, 'message': 'No character found'})

    # Create character object
    character = Character.from_dict(character_data)

    # Load game state
    game_state_data = load_data(f'game_state_{user_id}.json')
    if not game_state_data:
        return jsonify({'success': False, 'message': 'No game state found'})

    game_state = game_engine.load_game_state(game_state_data)

    # Get action from request
    data = request.get_json()
    action = data.get('action', '')
    details = data.get('details', '')

    # Log the action
    logger.info(f"Action: {action} | Details: {details} | User: {user_id[:8]}...")

    # Process action
    result = game_engine.process_action(action, details, character, game_state)

    # Save updated character and game state
    save_data(character.to_dict(), f'character_{user_id}.json')
    save_data(game_state.to_dict(), f'game_state_{user_id}.json')

    return jsonify(result)

@bp.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset the game but keep the character."""
    user_id = session.get('user_id')
    if user_id:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        
        # Load character data
        character_file = os.path.join(data_dir, f'character_{user_id}.json')
        character_data = load_data(f'character_{user_id}.json')
        
        if character_data:
            # Reset character stats but keep basic info
            basic_info = {
                'name': character_data.get('name', 'Adventurer'),
                'race': character_data.get('race', 'Human'),
                'character_class': character_data.get('character_class', 'Warrior'),
                'user_id': user_id,
                'strength': character_data.get('strength', 10),
                'dexterity': character_data.get('dexterity', 10),
                'constitution': character_data.get('constitution', 10),
                'intelligence': character_data.get('intelligence', 10),
                'wisdom': character_data.get('wisdom', 10),
                'charisma': character_data.get('charisma', 10),
                'level': 1,
                'experience': 0,
                'gold': 50,
                'inventory': ["Basic Sword", "Health Potion"]
            }
            
            # Create a new character with the basic info
            character = Character(**basic_info)
            
            # Save the reset character
            save_data(character.to_dict(), f'character_{user_id}.json')
            
            # Create new game state
            game_state = game_engine.create_game_state(character)
            save_data(game_state.to_dict(), f'game_state_{user_id}.json')

    return jsonify({'success': True})

@bp.route('/change_language/<lang>')
def change_language(lang):
    """Change the language."""
    session['language'] = lang
    return redirect(request.referrer or url_for('routes.index'))

@bp.route('/api/world_map')
def api_world_map():
    """Get the world map data."""
    # Check if user has a character
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'No character found'})

    # Load game state
    game_state_data = load_data(f'game_state_{user_id}.json')
    if not game_state_data:
        return jsonify({'success': False, 'message': 'No game state found'})

    # Extract world map and player position
    world_map = game_state_data.get('world_map', {})
    coordinates = game_state_data.get('coordinates', {'x': 0, 'y': 0, 'z': 0})

    return jsonify({
        'success': True,
        'world_map': world_map,
        'player_position': coordinates
    })