import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from game_engine import GameEngine
from groq_client import GroqClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")

# Configure server-side session
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 24 hours
Session(app)

# Initialize game engine and Groq client
game_engine = GameEngine()
groq_client = GroqClient()

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/character", methods=["GET", "POST"])
def character():
    if request.method == "POST":
        # Create or update character
        character_data = {
            "name": request.form.get("name"),
            "class": request.form.get("class"),
            "race": request.form.get("race"),
            "strength": int(request.form.get("strength", 10)),
            "dexterity": int(request.form.get("dexterity", 10)),
            "constitution": int(request.form.get("constitution", 10)),
            "intelligence": int(request.form.get("intelligence", 10)),
            "wisdom": int(request.form.get("wisdom", 10)),
            "charisma": int(request.form.get("charisma", 10)),
            "max_hp": int(request.form.get("max_hp", 20)),
            "current_hp": int(request.form.get("current_hp", 20)),
            "max_stamina": int(request.form.get("max_stamina", 10)),
            "current_stamina": int(request.form.get("current_stamina", 10)),
            "inventory": request.form.get("inventory", "").split(",") if request.form.get("inventory") else ["Basic Sword", "Health Potion"],
            "gold": int(request.form.get("gold", 50)),
            "experience": int(request.form.get("experience", 0)),
            "level": int(request.form.get("level", 1)),
        }
        
        # Set character data in session
        session["character"] = character_data
        
        # Save character data to file for persistence
        user_id = session.get("user_id", "default_user")
        game_engine.save_character(user_id, character_data)
        
        flash("Character saved successfully!", "success")
        return redirect(url_for("game"))
    
    # Check if character exists in session
    character_data = session.get("character")
    
    # If not in session, try to load from file
    if character_data is None:
        user_id = session.get("user_id", "default_user")
        character_data = game_engine.load_character(user_id)
    
    return render_template("character.html", character=character_data)

@app.route("/game")
def game():
    # Check if character exists in session
    character = session.get("character")
    
    # If no character, redirect to character creation
    if not character:
        flash("Please create a character first!", "warning")
        return redirect(url_for("character"))
    
    # Load game state if exists
    user_id = session.get("user_id", "default_user")
    game_state = game_engine.load_game_state(user_id)
    
    # If no game state, create a new one
    if not game_state:
        game_state = {
            "current_location": "Village Square",
            "scene_description": "You stand in the center of a small village. There's a tavern to the north, a blacksmith to the east, and the village gate to the south.",
            "npcs_present": ["Village Elder", "Merchant"],
            "events": ["A festival is being prepared in the village square."],
            "messages": ["Welcome to the village of Eldermist! Your adventure begins now."],
            "combat": None
        }
        game_engine.save_game_state(user_id, game_state)
    
    return render_template("game.html", character=character, game_state=game_state)

@app.route("/api/action", methods=["POST"])
def perform_action():
    data = request.json
    action = data.get("action")
    action_details = data.get("details", "")
    
    # Get character and game state
    character = session.get("character")
    user_id = session.get("user_id", "default_user")
    game_state = game_engine.load_game_state(user_id)
    
    if not character or not game_state:
        return jsonify({"error": "Character or game state not found"}), 400
    
    try:
        # Process the action using the game engine and AI
        result = game_engine.process_action(action, action_details, character, game_state, groq_client)
        
        # Update character in session
        session["character"] = character
        
        # Save updated character and game state
        game_engine.save_character(user_id, character)
        game_engine.save_game_state(user_id, game_state)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing action: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/combat/attack", methods=["POST"])
def combat_attack():
    data = request.json
    attack_type = data.get("attack_type", "basic")
    
    # Get character and game state
    character = session.get("character")
    user_id = session.get("user_id", "default_user")
    game_state = game_engine.load_game_state(user_id)
    
    if not character or not game_state or not game_state.get("combat"):
        return jsonify({"error": "Character, game state, or combat not found"}), 400
    
    try:
        # Process combat attack
        result = game_engine.process_combat_attack(attack_type, character, game_state)
        
        # Update character in session
        session["character"] = character
        
        # Save updated character and game state
        game_engine.save_character(user_id, character)
        game_engine.save_game_state(user_id, game_state)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing combat attack: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/use-item", methods=["POST"])
def use_item():
    data = request.json
    item_name = data.get("item")
    
    # Get character and game state
    character = session.get("character")
    user_id = session.get("user_id", "default_user")
    game_state = game_engine.load_game_state(user_id)
    
    if not character or not game_state:
        return jsonify({"error": "Character or game state not found"}), 400
    
    try:
        # Use the item via game engine
        result = game_engine.use_item(item_name, character, game_state)
        
        # Update character in session
        session["character"] = character
        
        # Save updated character and game state
        game_engine.save_character(user_id, character)
        game_engine.save_game_state(user_id, game_state)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error using item: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/rest", methods=["POST"])
def rest():
    # Get character and game state
    character = session.get("character")
    user_id = session.get("user_id", "default_user")
    game_state = game_engine.load_game_state(user_id)
    
    if not character or not game_state:
        return jsonify({"error": "Character or game state not found"}), 400
    
    try:
        # Process resting action
        result = game_engine.process_rest(character, game_state)
        
        # Update character in session
        session["character"] = character
        
        # Save updated character and game state
        game_engine.save_character(user_id, character)
        game_engine.save_game_state(user_id, game_state)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing rest: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/reset-game", methods=["POST"])
def reset_game():
    # Clear character and game state
    user_id = session.get("user_id", "default_user")
    session.pop("character", None)
    
    try:
        # Reset game state
        game_engine.delete_game_state(user_id)
        game_engine.delete_character(user_id)
        
        return jsonify({"success": True, "message": "Game reset successfully"})
    except Exception as e:
        logger.error(f"Error resetting game: {str(e)}")
        return jsonify({"error": str(e)}), 500
