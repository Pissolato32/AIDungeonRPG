# filepath: c:\Users\rodri\Desktop\REPLIT RPG\app\app.py

import logging
import os
import sys
import traceback
from typing import Any, Dict, Optional, Tuple

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
import uuid  # Import uuid at the top level
from dotenv import load_dotenv  # Importar dotenv

load_dotenv()  # Carregar variáveis de ambiente do arquivo .env

# Importar tanto o cliente de baixo nível quanto o wrapper/adaptador
from ai.openrouter import OpenRouterClient
from ai.game_ai_client import (
    GameAIClient,
)  # Importar o GameAIClient que o GameEngine espera
from app.routes import bp as routes_bp
from core.error_handler import ErrorHandler
from core.game_engine import GameEngine

# Import GameState from its new location
from core.game_state_model import GameState
from core.models import Character
from flask_session import Session
from web.character_manager import CharacterManager
from web.config import Config
from web.game_state_manager import GameStateManager
from web.logger import GameLogger
from web.session_manager import SessionManager

# Define the expected message format (AIPrompt) and an adapter if needed
# This definition should ideally be in a shared AI types file (e.g., ai/types.py)
# or where GameAIClient expects it. Adding it here for demonstration based on user request.
from typing import TypedDict, Protocol


class AIPrompt(TypedDict):
    role: str
    content: str


# Adapter class if OpenRouterClient doesn't directly match GameAIClient's expected interface
# (e.g., if GameAIClient expects list[AIPrompt] and OpenRouterClient expects list[dict])
class OpenRouterAdapter:
    def __init__(self, client: OpenRouterClient):
        self.client = client

    def generate_response(
        self, messages: list[AIPrompt], generation_params: dict | None = None
    ) -> str:
        # Convert AIPrompt list to dict list for the underlying client
        messages_dict = [
            {"role": msg["role"], "content": msg["content"]} for msg in messages
        ]
        return self.client.generate_response(messages_dict, generation_params)


# Add the project root directory to the Python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)


# Não importe 'routes_bp' aqui ainda para evitar importação circular

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GameApp:
    """Main application class for the RPG game."""

    def __init__(self) -> None:
        try:
            self.app = Flask(
                __name__,
                template_folder=os.path.join(root_dir, "templates"),
                static_folder=os.path.join(root_dir, "static"),
            )
            self._configure_app()
            # O blueprint será registrado após a criação da instância
            # _game_app_instance
            # Initialize clients and engines
            # Primeiro, crie a instância do cliente LLM de baixo nível
            self.openrouter_client_instance = OpenRouterClient()
            self.openrouter_adapter_instance = OpenRouterAdapter(
                self.openrouter_client_instance
            )
            self.ai_client = GameAIClient(
                ai_client=self.openrouter_adapter_instance
            )  # Usar o adaptador
            self.game_engine = GameEngine()  # GameEngine agora tem seu próprio data_dir

            # data_dir para GameApp, se necessário para outros fins (embora
            # GameEngine lide com saves)
            self.data_dir = os.path.join(root_dir, "data")
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
        except Exception as e:
            # Adicionado logging mais detalhado para erros de inicialização
            logger.critical("--------------------------------------------------")
            logger.critical("CRITICAL ERROR DURING APP INITIALIZATION")
            logger.error(f"Error during app initialization: {e}")
            logger.error(traceback.format_exc())
            raise

    def _configure_app(self) -> None:
        """Configure Flask application settings."""
        Config.configure_flask_app(self.app)
        self.app.config["SESSION_TYPE"] = os.environ.get("SESSION_TYPE", "filesystem")
        Session(self.app)

    def register_app_specific_routes(self) -> None:
        """Register any application-specific routes not handled by blueprints."""
        # Este método pode ser usado para rotas que não estão no blueprint principal.
        # Por enquanto, está vazio, pois as rotas principais estão em routes.py
        pass

    def run(self) -> None:
        """Run the Flask application."""
        config = self.get_app_config()
        GameLogger.log_game_action(
            "startup",
            f"Starting server on {
                config['host']}:{
                config['port']} (debug={
                config['debug']})",
        )
        self.app.run(**config)

    # Route handlers (these methods will be called by the blueprint routes)
    @staticmethod
    def index() -> str:
        """Handle the index route."""
        return render_template("index.html")

    def character(self) -> Any:
        """Handle character creation and editing."""
        owner_session_id = SessionManager.ensure_session_initialized()
        # Assumes GameEngine is updated for multi-character support
        # e.g., game_engine.get_characters_by_owner(owner_session_id) -> List[Character]
        # e.g., game_engine.save_character(character_object_with_id_and_owner_id)
        # e.g., game_engine.load_character(character_id)

        existing_characters_list = self.game_engine.get_characters_by_owner(
            owner_session_id
        )  # Assumed method

        try:
            if request.method == "POST":
                if len(existing_characters_list) >= 3:
                    flash("Você atingiu o limite de 3 personagens.", "warning")
                    return redirect(url_for("routes.character"))

                character_data = request.form.to_dict()
                # CharacterManager should assign a unique ID (e.g., character.id = str(uuid.uuid4()))
                # Pass the current owner_session_id to the creation process.
                character = self._create_character_from_form(
                    character_data, owner_session_id
                )  # Pass owner_session_id

                self.game_engine.save_character(
                    character
                )  # Assumed method: saves the character object

                # Create and save initial game state for the new character
                game_state = self._create_initial_game_state()
                self.game_engine.save_game_state(
                    character.id, game_state
                )  # Save game state by character.id

                GameLogger.log_game_action(
                    "character_created",
                    f"Name: {character.name}, ID: {character.id}",
                    owner_session_id,
                )
                flash(
                    f"Personagem '{
                        character.name}' criado com sucesso!",
                    "success",
                )
                # Automatically select the new character
                session["active_character_id"] = character.id
                return redirect(url_for("routes.game"))

            # GET request
            return render_template(
                "character.html",
                # 'character' (singular) is no longer needed for form population
                existing_characters=existing_characters_list,
            )

        except ValueError as e:
            logger.error(f"ValueError in character route: {e}")
            flash(f"Entrada inválida: {str(e)}", "error")
            return render_template(
                "character.html",
                error=str(e),
                existing_characters=existing_characters_list,
            )
        except Exception as e:
            logger.error(f"Unexpected error in character route: {e}")
            logger.error(traceback.format_exc())
            flash(
                f"Erro inesperado: {str(e)}",
                "error",
            )
            return render_template(
                "character.html",
                error=str(e),
                existing_characters=existing_characters_list,
            )

    def game(self) -> Any:
        """Handle the main game view."""
        active_character_id = session.get("active_character_id")
        owner_session_id = session.get(
            "user_id"  # For logging or other session-wide checks
        )

        if not active_character_id or not owner_session_id:
            flash(
                "Nenhum personagem selecionado. Por favor, crie ou selecione um personagem.",
                "warning",
            )
            return redirect(url_for("routes.character"))

        # Assumes game_engine.load_character(character_id)
        character = self.game_engine.load_character(active_character_id)

        if not character:
            flash(
                "Personagem não encontrado. Por favor, crie ou selecione um personagem.",
                "warning",
            )
            return redirect(url_for("routes.character"))

        # Verify character ownership
        if character.owner_session_id != owner_session_id:
            logger.error(
                f"Ownership mismatch for character {active_character_id}. "
                f"Character owner: {character.owner_session_id}, "
                f"Session user: {owner_session_id}"
            )
            flash("Erro de permissão ao carregar personagem.", "error")
            session.pop("active_character_id", None)  # Clear invalid selection
            return redirect(url_for("routes.character"))

        game_state = self._load_game_state(active_character_id)
        if not game_state:
            logger.warning(
                f"Game state not found for character {active_character_id}. Creating a new one."
            )
            game_state = self._create_initial_game_state()
            self.game_engine.save_game_state(active_character_id, game_state)

        return render_template("game.html", character=character, game_state=game_state)

    def process_action(self) -> Any:
        """Process a game action from the API."""
        active_character_id = session.get("active_character_id")
        owner_session_id = session.get("user_id")
        if not active_character_id or not owner_session_id:
            return self._error_response("no_active_session")
        try:
            data = request.json
            if not data:
                return self._error_response(
                    "invalid_input", "Nenhum dado JSON recebido."
                )

            action_input = data.get("action")
            # Garante que 'action' seja uma string para o GameEngine
            action_name_for_log = (
                action_input if isinstance(action_input, str) else "unknown"
            )
            details = data.get("details", "")

            GameLogger.log_game_action(
                action_name_for_log,
                details,
                owner_session_id or "unknown_user_process_action",
            )
            character, game_state = self._load_character_and_state(active_character_id)

            if not character:  # character pode ser None
                return self._error_response("no_character_found")
            if not game_state:
                logger.error(
                    f"Game state missing for owner {owner_session_id} (char: {active_character_id}) in process_action. This should not happen."
                )
                game_state = self._create_initial_game_state()

            # Verify character ownership
            if character.owner_session_id != owner_session_id:
                GameLogger.log_game_action(
                    action_name_for_log, "Ownership mismatch", owner_session_id, "error"
                )
                return self._error_response(
                    "permission_denied", "Character ownership mismatch."
                )

            result = self.game_engine.process_action(
                action=action_name_for_log,
                details=details,
                character=character,
                game_state=game_state,
                ai_client=self.ai_client,  # Passa o cliente de IA correto
            )

            # game_state.messages is already updated by GameEngine.process_action
            # with the user's input (if non-empty) and the AI's response.
            # The calls below were redundant and used the old add_message signature.
            # Removed redundant message additions as GameEngine handles them.

            self._save_character_and_state(active_character_id, character, game_state)

            return jsonify(result)
        except ValueError as e:
            GameLogger.log_game_action(
                action_name_for_log,  # Already guaranteed to be a string
                f"ValueError: {str(e)}",
                owner_session_id or "unknown_user_value_error",
                "error",
            )
            return self._error_response("invalid_input", str(e))
        except Exception as e:
            GameLogger.log_game_action(
                action_name_for_log,  # Already guaranteed to be a string
                f"Unexpected error: {str(e)}",
                owner_session_id or "unknown_user_exception",
                "error",
            )
            logger.error(traceback.format_exc())
            return self._error_response("unexpected", str(e))

    def reset_game(self) -> Any:
        """Reset the game state but keeps character basic info for re-creation."""
        active_character_id = session.get("active_character_id")
        owner_session_id = session.get("user_id")

        if not active_character_id or not owner_session_id:
            return self._error_response("no_active_session")

        try:
            try:
                self.game_engine.delete_game_state(
                    active_character_id
                )  # Assumed method
                GameLogger.log_game_action(
                    "reset_game_state",
                    f"Game state deleted for char {active_character_id}.",
                    owner_session_id,
                )
            except Exception as e:
                GameLogger.log_game_action(
                    "reset_game_state",
                    f"Error deleting game state: {str(e)}",
                    owner_session_id,
                    "error",
                )
                logger.error(
                    f"Failed to delete game state for char {active_character_id} during reset: {e}"
                )

            flash(
                "Progresso do jogo resetado. Você pode editar seu personagem ou começar de novo.",
                "info",
            )
            return jsonify(
                {"success": True, "redirect_url": url_for("routes.character")}
            )

        except Exception as e:
            GameLogger.log_game_action(
                "reset_game",
                f"Unexpected error: {e}",
                owner_session_id,
                "error",
            )
            logger.error(traceback.format_exc())
            return self._error_response("reset_error", str(e))

    # Removed @staticmethod as this method uses self
    def select_character(self, character_id: str) -> Any:
        """Handle character selection."""
        # Ensure this method has a body. If it's not fully implemented yet,
        # you can use 'pass' as a placeholder.
        # The existing logic seems correct, so this diff just ensures proper indentation
        # if it was somehow lost or if the error was due to a preceding line.
        owner_session_id = session.get("user_id")
        if not owner_session_id:
            flash("Sessão inválida.", "error")
            return redirect(url_for("routes.index"))

        character = self.game_engine.load_character(character_id)  # Assumed method

        if character and character.owner_session_id == owner_session_id:
            session["active_character_id"] = character.id
            flash(f"Personagem '{character.name}' selecionado.", "success")
            return redirect(url_for("routes.game"))
        else:
            flash("Personagem não encontrado ou não pertence a você.", "error")
            return redirect(url_for("routes.character"))

    # Removed @staticmethod as this method uses self
    def delete_character(self, character_id: str) -> Any:
        """Handle character deletion."""
        owner_session_id = session.get("user_id")
        if not owner_session_id:
            flash("Sessão inválida.", "error")
            return redirect(url_for("routes.index"))

        character_to_delete = self.game_engine.load_character(
            character_id
        )  # Assumed method

        if (
            character_to_delete
            and character_to_delete.owner_session_id == owner_session_id
        ):
            try:
                self.game_engine.delete_character(character_id)  # Assumed method
                self.game_engine.delete_game_state(character_id)  # Assumed method
                flash(
                    f"Personagem '{character_to_delete.name}' excluído com sucesso.",
                    "success",
                )
                if session.get("active_character_id") == character_id:
                    session.pop(
                        "active_character_id", None
                    )  # Clear active if it was deleted
            except Exception as e:
                logger.error(f"Error deleting character {character_id}: {e}")
                flash("Erro ao excluir personagem.", "error")
        else:
            flash("Personagem não encontrado ou não pertence a você.", "error")

        return redirect(url_for("routes.character"))

    # Helper methods
    @staticmethod
    def _create_initial_game_state() -> GameState:
        return GameStateManager.create_initial_game_state()

    @staticmethod
    def _create_character_from_form(
        character_data: Dict[str, Any], owner_session_id: str
    ) -> Character:
        # This manager should now also handle setting a unique character.id
        # and potentially character.owner_session_id if passed in character_data or as an arg.
        return CharacterManager.create_character_from_form(
            character_data, owner_session_id  # Pass owner_session_id
        )

    def _load_game_state(self, character_id: str) -> Optional[GameState]:
        # GameStateManager.load_game_state needs to accept character_id
        # Correção: Usar diretamente o método do GameEngine para carregar o estado do jogo.
        # Correção: Usar diretamente o método do GameEngine para carregar o estado do jogo.
        gs: Optional[GameState] = self.game_engine.load_game_state(character_id)
        if not gs:
            logger.info(
                f"No game state found for character {character_id}, will create new if needed."
            )

        return gs

    def _load_character_and_state(
        self, active_character_id: Optional[str]
    ) -> Tuple[Optional[Character], Optional[GameState]]:
        if not active_character_id:
            return None, None

        character = self.game_engine.load_character(active_character_id)
        game_state = self._load_game_state(active_character_id)

        if character and not game_state:
            logger.warning(
                f"Character {character.name} found but no game state for char_id {active_character_id}. Creating new game state."
            )
            game_state = self._create_initial_game_state()
            self.game_engine.save_game_state(active_character_id, game_state)

        return character, game_state

    def _save_character_and_state(
        self, active_character_id: str, character: Character, game_state: GameState
    ) -> None:
        owner_session_id = session.get("user_id")
        if not owner_session_id or not active_character_id:
            logger.error(
                "Attempted to save character/state without user_id in session."
            )
            return
        # Ensure the character being saved matches the active one and owner
        if (
            character.id != active_character_id
            or character.owner_session_id != owner_session_id
        ):
            logger.error(
                f"Mismatch in saving character data. Active: {active_character_id}, Char ID: {character.id}, Owner: {owner_session_id}"
            )
            return

        self.game_engine.save_character(character)
        self.game_engine.save_game_state(active_character_id, game_state)

    @staticmethod
    def _error_response(error_key: str, error_details: str = "") -> Any:
        return ErrorHandler.create_error_response(error_key, "pt-br", error_details)

    @staticmethod
    def get_app_config() -> Dict[str, Any]:
        return Config.get_app_config()


# --- Application Setup ---
# 1. Create the GameApp instance (which creates the Flask app instance)
_game_app_instance = GameApp()

# 2. Get the Flask app from the GameApp instance
application = _game_app_instance.app

# Attach the GameApp instance to the Flask app for access in routes via current_app
application.game_app_instance = _game_app_instance  # type: ignore

# 3. NOW import the blueprint from app.routes
# This import needs _game_app_instance to be defined.

# 4. Register the blueprint with the Flask app instance
application.register_blueprint(routes_bp)

# 5. Register any app-specific routes (if any)
_game_app_instance.register_app_specific_routes()  # Renamed for clarity

# --- Run the Application ---
if __name__ == "__main__":
    _game_app_instance.run()
