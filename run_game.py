# filepath: c:\Users\rodri\Desktop\REPLIT RPG\run_game.py
#!/usr/bin/env python
"""
Script de inicialização para o jogo RPG.
"""

import logging
import os
import sys

from app.app import _game_app_instance, application

# Configurar logging
# logging.basicConfig(level=logging.INFO) # Linha original
log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(
    level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Adiciona o diretório raiz do projeto ao path do Python
root_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__))
)  # Corrected root_dir definition
sys.path.insert(0, root_dir)

# Importa a instância principal da aplicação de app.app
# Esta instância já tem tudo configurado (rotas, blueprints, etc.)

if __name__ == "__main__":
    logger.info("Iniciando aplicação RPG")
    # Usa a configuração definida em app.app.py através do método run da instância GameApp
    # ou diretamente a configuração do Flask se preferir.
    # _game_app_instance.run() # Isso chamará o app.run com a configuração
    # interna

    # Ou, se você quiser controlar host/port/debug diretamente aqui:
    config = _game_app_instance.get_app_config()
    application.run(
        host=config.get("host", "127.0.0.1"),
        port=config.get("port", 5000),
        debug=config.get("debug", True),
    )
