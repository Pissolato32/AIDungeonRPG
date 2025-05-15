import sys
import os

# Adiciona o diretório raiz do projeto ao path do Python
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, root_dir)

# Importa a classe GameApp do módulo app
from rpg_game.app.app import GameApp

if __name__ == "__main__":
    # Cria uma instância da aplicação e a executa
    app = GameApp()
    app.run()