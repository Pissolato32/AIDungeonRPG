# filepath: c:\Users\rodri\Desktop\REPLIT RPG\WebChatRPG\app\routes.py
"""
Routes for the RPG game.

This module defines the web routes for the RPG game.
"""

import os
import logging
import uuid
from flask import (
    flash,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
    Blueprint,
)

from core.models import Character
from core.game_engine import GameEngine
from utils.data_io import save_data, load_data
from web.error_handler import ErrorHandler

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("routes", __name__)

# Initialize game engine
game_engine = GameEngine()


@bp.route("/")
def index():
    """Render the index page."""
    return render_template("index.html")


@bp.route("/character", methods=["GET", "POST"])
def character():
    """Render the character creation/selection page."""
    if request.method == "POST":
        # Import CharacterManager here to avoid circular import
        from web.character_manager import CharacterManager

        user_id = str(uuid.uuid4().hex)
        session["user_id"] = user_id

        # Get form data
        character_data = dict(request.form)
        character_data["user_id"] = user_id

        # Create character using CharacterManager
        character = CharacterManager.create_character_from_form(character_data)
        character.user_id = user_id  # Ensure correct user_id

        # Save character data and init game state
        save_path = f"character_{user_id}.json"
        save_data(character.to_dict(), save_path)

        # Initialize game state with proper language
        game_state = game_engine.create_game_state(
            character_id=user_id, language=session.get("language", "pt")
        )
        save_data(game_state.to_dict(), f"game_state_{user_id}.json")

        return redirect(url_for("routes.game"))

    # GET request - show character creation form
    existing_characters = []
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    )

    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            is_char_file = filename.startswith("character_") and filename.endswith(
                ".json"
            )
            if is_char_file:
                char_data = load_data(filename)
                if char_data:
                    # Extract user_id from filename
                    uid = filename[10:-5]  # Remove 'character_' and '.json'
                    char_data["user_id"] = uid
                    existing_characters.append(char_data)

    flash(
        ErrorHandler.format_error_response(
            "character_creation_failed", session.get("language", "ptbr")
        )["error"]["message"],
        "error",
    )
    return render_template("character.html", existing_characters=existing_characters)


@bp.route("/select_character/<user_id>")
def select_character(user_id):
    """Select an existing character."""
    session["user_id"] = user_id
    return redirect(url_for("routes.game"))


@bp.route("/delete_character/<user_id>")
def delete_character(user_id):
    """Delete an existing character."""
    data_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    )

    # Delete character file
    char_file = os.path.join(data_dir, f"character_{user_id}.json")
    if os.path.exists(char_file):
        os.remove(char_file)

    # Delete game state file
    state_file = os.path.join(data_dir, f"game_state_{user_id}.json")
    if os.path.exists(state_file):
        os.remove(state_file)

    return redirect(url_for("routes.character"))


@bp.route("/game")
def game():
    """Render the main game page."""
    # Check if user has a character
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("routes.character"))

    # Load character data
    char_data = load_data(f"character_{user_id}.json")
    if not char_data:
        return redirect(url_for("routes.character"))

    # Create character object
    character = Character.from_dict(char_data)

    # Load game state
    state_data = load_data(f"game_state_{user_id}.json")
    if not state_data:
        # Initialize new game state
        game_state = game_engine.create_game_state(character_id=user_id)
        save_data(game_state.to_dict(), f"game_state_{user_id}.json")
    else:
        game_state = game_engine.load_game_state(state_data)

    # Render game template
    return render_template("game.html", character=character, game_state=game_state)


@bp.route("/api/action", methods=["POST"])
def api_action():
    """Handle game actions via API."""
    # Check if user has a character
    user_id = session.get("user_id")
    if not user_id:
        return ErrorHandler.create_error_response(
            "no_character_found", session.get("language")
        )

    # Load character data
    char_data = load_data(f"character_{user_id}.json")
    if not char_data:
        return ErrorHandler.create_error_response(
            "no_character_found", session.get("language")
        )

    # Create character object
    character = Character.from_dict(char_data)

    # Load game state
    state_data = load_data(f"game_state_{user_id}.json")
    if not state_data:
        return ErrorHandler.create_error_response(
            "no_game_state_found", session.get("language")
        )

    game_state = game_engine.load_game_state(state_data)

    # Get action from request
    data = request.get_json()
    action = data.get("action", "")
    details = data.get("details", "")

    # Log the action
    logger.info(f"Action: {action} | Details: {details} | User: {user_id[:8]}...")

    # Process action
    result = game_engine.process_action(action, details, character, game_state)

    # Save updated character and game state
    save_data(character.to_dict(), f"character_{user_id}.json")
    save_data(game_state.to_dict(), f"game_state_{user_id}.json")

    return jsonify(result)


@bp.route("/api/reset", methods=["POST"])
def api_reset():
    """Reset the game but keep the character."""
    user_id = session.get("user_id")
    if not user_id:
        return ErrorHandler.create_error_response(
            "no_character_found", session.get("language")
        )

    # Load character data
    char_data = load_data(f"character_{user_id}.json")
    if not char_data:
        return ErrorHandler.create_error_response(
            "no_character_found", session.get("language")
        )

    # Reset character stats but keep basic info
    basic_info = {
        "name": char_data.get("name", "Adventurer"),
        "race": char_data.get("race", "Human"),
        "character_class": char_data.get("character_class", "Warrior"),
        "user_id": user_id,
        "strength": char_data.get("strength", 10),
        "dexterity": char_data.get("dexterity", 10),
        "constitution": char_data.get("constitution", 10),
        "intelligence": char_data.get("intelligence", 10),
        "wisdom": char_data.get("wisdom", 10),
        "charisma": char_data.get("charisma", 10),
        "level": 1,
        "experience": 0,
        "gold": 50,
        "inventory": ["Basic Sword", "Health Potion"],
    }

    # Create a new character with the basic info
    character = Character(**basic_info)

    # Save the reset character and create new game state
    save_data(character.to_dict(), f"character_{user_id}.json")
    game_state = game_engine.create_game_state(character_id=user_id)
    save_data(game_state.to_dict(), f"game_state_{user_id}.json")

    return jsonify({"success": True})


@bp.route("/change_language/<lang>")
def change_language(lang):
    """Change the language."""
    session["language"] = lang
    return redirect(request.referrer or url_for("routes.index"))


@bp.route("/api/world_map")
def api_world_map():
    """Get the world map data."""
    # Check if user has a character
    user_id = session.get("user_id")
    if not user_id:
        return ErrorHandler.create_error_response(
            "no_character_found", session.get("language")
        )

    # Load game state
    state_data = load_data(f"game_state_{user_id}.json")
    if not state_data:
        return ErrorHandler.create_error_response(
            "no_game_state_found", session.get("language")
        )

    # Extract world map and player position
    world_map = state_data.get("world_map", {})
    coordinates = state_data.get("coordinates", {"x": 0, "y": 0, "z": 0})

    return jsonify(
        {"success": True, "world_map": world_map, "player_position": coordinates}
    )
