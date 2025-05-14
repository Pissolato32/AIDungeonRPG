from app import application
from web.config import Config
from web.logger import GameLogger

if __name__ == "__main__":
    config = Config.get_app_config()
    GameLogger.log_game_action('startup', f"Starting server on {config['host']}:{config['port']} (debug={config['debug']})")
    application.run(**config)
