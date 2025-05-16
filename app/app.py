from flask import (
    Flask,
    render_template,
    redirect,
    session,
    request,
    jsonify,
    url_for,
    flash,
)
from flask_session import Session
from typing import Dict, Any, List, Optional, Tuple
import os
import sys
import logging
import traceback

# Add the project root directory to the Python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)

from core.models import Character
from core.game_engine import GameEngine, GameState
from ai.groq_client import GroqClient
from web.config import Config
from web.session_manager import SessionManager
from web.logger import GameLogger
from core.error_handler import (
    ErrorHandler,
)  # Assuming core.error_handler is the one with get_text
from web.game_state_manager import GameStateManager
from web.character_manager import CharacterManager
from app.routes import bp as routes_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GameApp:
    """Main application class for the RPG game."""

    def __init__(self):
        try:
            self.app = Flask(
                __name__,
                template_folder=os.path.join(root_dir, "templates"),
                static_folder=os.path.join(root_dir, "static"),
            )
            self.app.register_blueprint(routes_bp)
            self._configure_app()
            self._register_routes()

            # Initialize clients and engines
            self.groq_client = GroqClient()
            self.game_engine = GameEngine()

            # Ensure data directory exists
            self.data_dir = os.path.join(root_dir, "data")
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
        except Exception as e:
            logger.error(f"Error during app initialization: {e}")
            raise

    def _configure_app(self):
        """Configure Flask application settings."""
        Config.configure_flask_app(self.app)
        self.app.config["SESSION_TYPE"] = os.environ.get("SESSION_TYPE", "filesystem")
        Session(self.app)

    def _register_routes(self):
        """Register all route handlers."""
        # Main routes
        self.app.route("/", methods=["GET"])(self.index)
        self.app.route("/character", methods=["GET", "POST"])(self.character)
        self.app.route("/game", methods=["GET"])(self.game)

        # API routes
        self.app.route("/api/action", methods=["POST"])(self.process_action)
        self.app.route("/api/reset", methods=["POST"])(self.reset_game)

        # Utility routes
        # self.app.route("/change_language/<lang>", methods=["GET"])(self.change_language) # Rota removida

    def run(self):
        """Run the Flask application."""
        config = self._get_app_config()
        GameLogger.log_game_action(
            "startup",
            f"Starting server on {config['host']}:{config['port']} (debug={config['debug']})",
        )
        self.app.run(**config)

    # Route handlers
    def index(self):
        """Handle the index route."""
        return render_template("index.html")

    def character(self):
        """Handle character creation and editing."""
        # Ensure session is initialized
        user_id = (
            SessionManager.ensure_session_initialized()
        )  # This already sets user_id and language in session

        try:
            if request.method == "POST":
                # Get form data
                character_data = request.form.to_dict()

                # Create and save character
                character = self._create_character_from_form(character_data)
                self.game_engine.save_character(user_id, character)

                # Initialize and save game state
                game_state = self._create_initial_game_state()
                self.game_engine.save_game_state(user_id, game_state)

                GameLogger.log_game_action(
                    "character_created",
                    f"Name: {character.name}, Class: {character.character_class}",
                    user_id,
                )
                return redirect(url_for("game"))
            else:
                # GET request - check if character exists
                character_data = self.game_engine.load_character(user_id)
                character = (
                    Character.from_dict(character_data) if character_data else None
                )
                if (
                    not character and user_id in session
                ):  # Only flash if a load was attempted for an existing session
                    flash("Falha ao carregar personagem existente.", "error")
                return render_template("character.html", character=character)

        except ValueError as e:
            logger.error(f"ValueError in character route: {e}")
            flash(f"Entrada inválida: {str(e)}", "error")
            return render_template("character.html", character=None, error=str(e))
        except Exception as e:
            logger.error(f"Unexpected error in character route: {e}")
            logger.error(traceback.format_exc())
            flash(f"Erro inesperado: {str(e)}", "error")
            return render_template("character.html", character=None, error=str(e))

    def game(self):
        """Handle the main game view."""
        if "user_id" not in session:
            session["user_id"] = os.urandom(16).hex()
            return redirect(url_for("character"))
        user_id = session["user_id"]
        character_data = self.game_engine.load_character(user_id)
        character = Character.from_dict(character_data) if character_data else None
        game_state = self._load_game_state(session["user_id"])
        if not character:
            return redirect(url_for("character"))

        return render_template("game.html", character=character, game_state=game_state)

    def process_action(self):
        """Process a game action from the API."""
        if "user_id" not in session:
            return self._error_response("no_active_session")

        action_name_for_log = "unknown_action"
        # Get action data
        try:
            data = request.json
            action = data.get("action")
            action_name_for_log = action if action else "unknown_action"
            details = data.get("details", "")

            GameLogger.log_game_action(action, details, session["user_id"])

            # Load character and game state
            character, game_state = self._load_character_and_state()

            if not character:
                return self._error_response("no_character_found")

            # Process action
            result = self.game_engine.process_action(
                action, details, character, game_state, self.groq_client
            )

            # Save updated character and game state
            self._save_character_and_state(character, game_state)

            return jsonify(result)
        except ValueError as e:
            GameLogger.log_game_action(
                action, f"ValueError: {str(e)}", session["user_id"], "error"
            )
            return self._error_response("invalid_input", str(e))
        except Exception as e:
            GameLogger.log_game_action(
                action_name_for_log,
                f"Unexpected error: {str(e)}",
                session["user_id"],
                "error",
            )
            logger.error(traceback.format_exc())
            return self._error_response("unexpected", str(e))

    def reset_game(self):
        """Reset the game state."""
        if "user_id" not in session:
            return self._error_response("no_active_session")

        try:
            # Delete character
            try:
                self.game_engine.delete_character(session["user_id"])
            except Exception as e:
                GameLogger.log_game_action(
                    "reset_game",
                    f"Error deleting character: {str(e)}",
                    session["user_id"],
                    "error",
                )
                return self._error_response("reset_error_character", str(e))

            # Delete game state
            try:
                self.game_engine.delete_game_state(session["user_id"])
            except Exception as e:
                GameLogger.log_game_action(
                    "reset_game",
                    f"Error deleting game state: {str(e)}",
                    session["user_id"],
                    "error",
                )
                return self._error_response("reset_error_game_state", str(e))

            # Generate new user ID
            session["user_id"] = os.urandom(16).hex()

            return jsonify({"success": True})
        except Exception as e:
            GameLogger.log_game_action(
                "reset_game", f"Unexpected error: {e}", session["user_id"], "error"
            )
            return self._error_response("reset_error", str(e))

    # def change_language(self, lang): # Método removido
    #     """Change the user's language preference."""
    #     # session["language"] = lang # Idioma agora é fixo
    #     # logger.info(f"Language change attempt to {lang} for session {session.get('user_id')}, but language is fixed.")
    #     return redirect(request.referrer or url_for("index"))
    # Helper methods

    def _create_initial_game_state(self) -> GameState:
        """
        Create an initial game state for a new character.

        Returns:
            GameState: A newly initialized game state
        """
        return GameStateManager.create_initial_game_state()

    def _create_character_from_form(self, character_data: Dict[str, Any]) -> Character:
        """
        Create a character object from form data.

        Args:
            character_data: Dictionary containing character form data

        Returns:
            Character: A newly created character object
        """
        # Use CharacterManager to process attributes and create character
        return CharacterManager.create_character_from_form(character_data)

    def _get_character_attributes(
        self, character_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract and convert character attributes from form data.

        Args:
            character_data: Dictionary containing character form data

        Returns:
            Dictionary with properly typed character attributes
        """
        # Use CharacterManager to process attributes
        return CharacterManager.get_character_attributes(character_data)

    def _load_game_state(self, user_id: str) -> GameState:
        """
        Load game state for a user.

        Args:
            user_id: The user's unique identifier

        Returns:
            GameState object
        """
        return GameStateManager.load_game_state(self.game_engine, user_id)

    def _load_character_and_state(
        self,
    ) -> Tuple[Optional[Character], Optional[GameState]]:
        """
        Load both character and game state for the current user.

        Returns:
            Tuple containing character and game state objects
        """
        character_data = self.game_engine.load_character(session["user_id"])
        character = Character.from_dict(character_data) if character_data else None
        game_state = self._load_game_state(session["user_id"])
        return character, game_state

    def _save_character_and_state(
        self, character: Character, game_state: GameState
    ) -> None:
        """
        Save both character and game state for the current user.

        Args:
            character: Character object to save
            game_state: GameState object to save
        """
        self.game_engine.save_character(session["user_id"], character)
        self.game_engine.save_game_state(session["user_id"], game_state)

    def _error_response(self, error_key: str, error_details: str = "") -> Any:
        """
        Create a standardized error response.

        Args:
            error_key: Key for the error message in translations
            error_details: Additional error details

        Returns:
            JSON response with error message
        """
        return ErrorHandler.create_error_response(
            error_key, "pt-br", error_details
        )  # Hardcode pt-br for now

    def _log_game_action(
        self, action: str, details: str = "", user_id: str = None, level: str = "info"
    ) -> None:
        """
        Log game actions with consistent formatting and optional context.

        Args:
            action: The action being performed
            details: Additional details about the action
            user_id: Optional user ID for context
            level: Log level ('debug', 'info', 'warning', 'error', 'critical')
        """
        GameLogger.log_game_action(action, details, user_id, level)

    def _get_app_config(self) -> Dict[str, Any]:
        """
        Get application configuration from environment variables with sensible defaults.

        Returns:
            Dictionary with application configuration
        """
        return Config.get_app_config()


# Create and run the application
_game_app_instance = GameApp()
application = _game_app_instance.app  # Export the Flask application object

if __name__ == "__main__":
    _game_app_instance.run()
