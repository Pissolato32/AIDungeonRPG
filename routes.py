"""
Routes for the RPG game.

This module defines the web routes for the RPG game.
"""

import os
import json
import logging
import uuid
from typing import Dict, Any, Optional, Union
from flask import (
    Flask, render_template, request, redirect, url_for, 
    session, jsonify, flash, Blueprint
)

from models import Character
from game_engine import GameEngine
from utils.data_io import save_data, load_data
from translations import get_text, TranslationManager

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('routes', __name__)

# Initialize game engine
game_engine = GameEngine(data_dir='data')

@bp.route('/')
def index():
    """Render the index page."""
    return render_template('index.html')

@bp.route('/character', methods=['GET', 'POST'])
def character():
    """Render the character creation/selection page."""
    if request.method == 'POST':
        # Create a new character
        name = request.form.get('name', 'Adventurer')
        race = request.form.get('race', 'Human')
        character_class = request.form.get('class', 'Warrior')

        # Generate a unique ID for the user
        user_id = str(uuid.uuid4().hex)
        session['user_id'] = user_id

        # Create character
        character = Character(
            name=name,
            race=race,
            character_class=character_class,
            user_id=user_id
        )

        # Save character data
        save_data(character.to_dict(), f'character_{user_id}.json')

        # Initialize game state
        game_state = game_engine.create_game_state(character)
        save_data(game_state.to_dict(), f'game_state_{user_id}.json')

        # Redirect to game
        return redirect(url_for('routes.game'))

    # GET request - show character creation form
    return render_template('character.html')

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
    """Reset the game."""
    user_id = session.get('user_id')
    if user_id:
        # Delete character and game state files
        character_file = os.path.join('data', f'character_{user_id}.json')
        game_state_file = os.path.join('data', f'game_state_{user_id}.json')

        if os.path.exists(character_file):
            os.remove(character_file)

        if os.path.exists(game_state_file):
            os.remove(game_state_file)

        # Clear session
        session.pop('user_id', None)

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