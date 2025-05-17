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

from ai.groq_client import GroqClient
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

# Add the project root directory to the Python path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)


# Não importe 'routes_bp' aqui ainda para evitar importação circular

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
            self._configure_app()
            # O blueprint será registrado após a criação da instância
            # _game_app_instance

            # Initialize clients and engines
            self.groq_client = GroqClient()
            self.game_engine = GameEngine()  # GameEngine agora tem seu próprio data_dir

            # data_dir para GameApp, se necessário para outros fins (embora
            # GameEngine lide com saves)
            self.data_dir = os.path.join(root_dir, "data")
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
        except Exception as e:
            logger.error(f"Error during app initialization: {e}")
            logger.error(traceback.format_exc())
            raise

    def _configure_app(self):
        """Configure Flask application settings."""
        Config.configure_flask_app(self.app)
        self.app.config["SESSION_TYPE"] = os.environ.get("SESSION_TYPE", "filesystem")
        Session(self.app)

    def register_app_specific_routes(self):
        """Register any application-specific routes not handled by blueprints."""
        # Este método pode ser usado para rotas que não estão no blueprint principal.
        # Por enquanto, está vazio, pois as rotas principais estão em routes.py
        pass

    def run(self):
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
    def index(self):
        """Handle the index route."""
        return render_template("index.html")

    def character(self):
        """Handle character creation and editing."""
        user_id = SessionManager.ensure_session_initialized()

        try:
            if request.method == "POST":
                character_data = request.form.to_dict()
                character = self._create_character_from_form(character_data)

                # Safely check and set user_id.
                # Use getattr for reading the attribute to be explicit for type checkers
                # that 'user_id' might not be a statically known attribute.
                # The assignment character.user_id = user_id is a dynamic
                # attribute assignment.
                current_char_user_id = getattr(character, "user_id", None)
                if not current_char_user_id or current_char_user_id != user_id:
                    # Use setattr to explicitly set the attribute, satisfying
                    # type checkers
                    setattr(character, "user_id", user_id)

                self.game_engine.save_character(user_id, character)

                game_state = self._create_initial_game_state()
                self.game_engine.save_game_state(user_id, game_state)

                GameLogger.log_game_action(
                    "character_created",
                    f"Name: {
                        character.name}, Class: {
                        character.character_class}",
                    user_id,
                )
                flash(
                    f"Personagem '{
                        character.name}' criado com sucesso!",
                    "success",
                )
                return redirect(url_for("routes.game"))
            character_data = self.game_engine.load_character(user_id)
            character = Character.from_dict(character_data) if character_data else None
            # Para a seção "Personagens Existentes" no template.
            # Por enquanto, passaremos uma lista vazia.
            # A lógica para carregar múltiplos personagens precisaria ser implementada
            # no GameEngine e aqui, se essa funcionalidade for desejada.
            existing_characters_list = []
            # Se 'character' existe e você quer mostrá-lo na lista de "existentes" (para o user_id atual):
            # if character:
            #     char_obj_for_list = Character.from_dict({**character.to_dict(), "user_id": user_id})
            #     existing_characters_list = [char_obj_for_list]
            return render_template(
                "character.html",
                character=character,
                existing_characters=existing_characters_list,
            )

        except ValueError as e:
            logger.error(f"ValueError in character route: {e}")
            flash(f"Entrada inválida: {str(e)}", "error")
            # Ensure existing_characters is passed even in error cases
            return render_template(
                "character.html", character=None, error=str(e), existing_characters=[]
            )
        except Exception as e:
            logger.error(f"Unexpected error in character route: {e}")
            logger.error(traceback.format_exc())
            flash(
                f"Erro inesperado ao processar dados do personagem: {
                    str(e)}",
                "error",
            )
            # Ensure existing_characters is passed even in error cases
            return render_template(
                "character.html", character=None, error=str(e), existing_characters=[]
            )

    def game(self):
        """Handle the main game view."""
        user_id = session.get("user_id")
        if not user_id:
            flash(
                "Sessão não encontrada, por favor crie ou selecione um personagem.",
                "warning",
            )
            return redirect(url_for("routes.character"))

        character_data = self.game_engine.load_character(user_id)
        character = Character.from_dict(character_data) if character_data else None

        if not character:
            flash(
                "Personagem não encontrado. Por favor, crie ou selecione um personagem.",
                "warning",
            )
            return redirect(url_for("routes.character"))

        game_state = self._load_game_state(user_id)
        if not game_state:
            logger.warning(
                f"Game state not found for user {user_id}. Creating a new one."
            )
            game_state = self._create_initial_game_state()
            self.game_engine.save_game_state(user_id, game_state)

        return render_template("game.html", character=character, game_state=game_state)

    def process_action(self):
        """Process a game action from the API."""
        user_id = session.get("user_id")
        if not user_id:
            return self._error_response("no_active_session")

        action_name_for_log: str = "unknown_action"  # Ensure type for all paths
        try:
            data = request.json
            if not data:
                return self._error_response(
                    "invalid_input", "Nenhum dado JSON recebido."
                )

            action_input = data.get("action")
            # Garante que 'action' seja uma string para o GameEngine
            action_for_engine = (
                action_input if isinstance(action_input, str) else "unknown"
            )
            action_name_for_log = action_for_engine
            details = data.get("details", "")

            GameLogger.log_game_action(
                action_name_for_log, details, user_id or "unknown_user_process_action"
            )

            character, game_state = self._load_character_and_state()

            if not character:  # character pode ser None
                return self._error_response("no_character_found")
            if not game_state:
                logger.error(
                    f"Game state missing for user {user_id} in process_action. This should not happen."
                )
                game_state = self._create_initial_game_state()

            result = self.game_engine.process_action(
                action=action_for_engine,  # Usa a action garantida como string
                details=details,
                character=character,
                game_state=game_state,
                # action_handler é deixado como padrão (None)
                ai_client=self.groq_client,  # Passa groq_client para o parâmetro correto
            )

            self._save_character_and_state(character, game_state)

            return jsonify(result)
        except ValueError as e:
            GameLogger.log_game_action(
                action_name_for_log,  # Already guaranteed to be a string
                f"ValueError: {str(e)}",
                user_id or "unknown_user_value_error",
                "error",
            )
            return self._error_response("invalid_input", str(e))
        except Exception as e:
            GameLogger.log_game_action(
                action_name_for_log,  # Already guaranteed to be a string
                f"Unexpected error: {str(e)}",
                user_id or "unknown_user_exception",
                "error",
            )
            logger.error(traceback.format_exc())
            return self._error_response("unexpected", str(e))

    def reset_game(self):
        """Reset the game state but keeps character basic info for re-creation."""
        user_id = session.get("user_id")
        if not user_id:
            return self._error_response("no_active_session")

        try:
            try:
                self.game_engine.delete_game_state(user_id)
                GameLogger.log_game_action(
                    "reset_game_state", "Game state deleted.", user_id
                )
            except Exception as e:
                GameLogger.log_game_action(
                    "reset_game_state",
                    f"Error deleting game state: {str(e)}",
                    user_id,
                    "error",
                )
                logger.error(
                    f"Failed to delete game state for {user_id} during reset: {e}"
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
                user_id,  # user_id is checked at the beginning of the function
                "error",
            )
            logger.error(traceback.format_exc())
            return self._error_response("reset_error", str(e))

    def select_character(self, user_id: str):
        """Handle character selection (placeholder)."""
        # Implementar lógica para carregar o personagem com user_id
        # e definir na sessão, depois redirecionar para o jogo.
        logger.info(f"Attempting to select character with user_id: {user_id}")
        # Exemplo: session["user_id"] = user_id
        # self.game_engine.load_character(user_id) etc.
        flash(
            f"Seleção de personagem para {user_id} ainda não implementada.", "warning"
        )
        return redirect(
            url_for("routes.character")
        )  # Redireciona de volta para a criação/edição

    def delete_character(self, user_id: str):
        """Handle character deletion (placeholder)."""
        # Implementar lógica para deletar o personagem com user_id.
        logger.info(f"Attempting to delete character with user_id: {user_id}")
        # Exemplo: self.game_engine.delete_character(user_id)
        # self.game_engine.delete_game_state(user_id)
        flash(
            f"Exclusão de personagem para {user_id} ainda não implementada.", "warning"
        )
        return redirect(url_for("routes.character"))

    # Helper methods
    def _create_initial_game_state(self) -> GameState:
        return GameStateManager.create_initial_game_state()

    def _create_character_from_form(self, character_data: Dict[str, Any]) -> Character:
        return CharacterManager.create_character_from_form(character_data)

    def _get_character_attributes(
        self, character_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return CharacterManager.get_character_attributes(character_data)

    def _load_game_state(self, user_id: str) -> Optional[GameState]:
        gs = GameStateManager.load_game_state(self.game_engine, user_id)
        if not gs:
            logger.info(
                f"No game state found for user {user_id}, will create new if needed."
            )
        return gs

    def _load_character_and_state(
        self,
    ) -> Tuple[Optional[Character], Optional[GameState]]:
        user_id = session.get("user_id")
        if not user_id:
            return None, None

        character_data = self.game_engine.load_character(user_id)
        character = Character.from_dict(character_data) if character_data else None
        game_state = self._load_game_state(user_id)

        if character and not game_state:
            logger.warning(
                f"Character {
                    character.name if character else 'Unknown'} found but no game state for user {user_id}. Creating new game state."
            )
            game_state = self._create_initial_game_state()
            self.game_engine.save_game_state(user_id, game_state)

        return character, game_state

    def _save_character_and_state(
        self, character: Character, game_state: GameState
    ) -> None:
        user_id = session.get("user_id")
        if not user_id:
            logger.error(
                "Attempted to save character/state without user_id in session."
            )
            return
        self.game_engine.save_character(user_id, character)
        self.game_engine.save_game_state(user_id, game_state)

    def _error_response(self, error_key: str, error_details: str = "") -> Any:
        return ErrorHandler.create_error_response(error_key, "pt-br", error_details)

    def _log_game_action(
        self,
        action: str,
        details: str = "",
        user_id: Optional[str] = None,
        level: str = "info",
    ) -> None:
        # Determine effective_user_id, ensuring it's a string
        _effective_user_id: Optional[str] = user_id or session.get("user_id")
        effective_user_id_str: str = (
            _effective_user_id if _effective_user_id is not None else "anonymous"
        )

        # Ensure action and details are strings if they somehow become None
        GameLogger.log_game_action(
            action if action is not None else "unspecified_action",
            details if details is not None else "",
            effective_user_id_str,  # Pass the guaranteed string
            level,
        )

    def get_app_config(self) -> Dict[str, Any]:
        return Config.get_app_config()


# --- Application Setup ---
# 1. Create the GameApp instance (which creates the Flask app instance)
_game_app_instance = GameApp()

# 2. Get the Flask app from the GameApp instance
application = _game_app_instance.app

# 3. NOW import the blueprint from app.routes
# This import needs _game_app_instance to be defined.

# 4. Register the blueprint with the Flask app instance
application.register_blueprint(routes_bp)

# 5. Register any app-specific routes (if any)
_game_app_instance.register_app_specific_routes()  # Renamed for clarity

# --- Run the Application ---
if __name__ == "__main__":
    _game_app_instance.run()
