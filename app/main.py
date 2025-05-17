from app.app import GameApp
import os
import sys

# Adiciona o diretório raiz do projeto ao path do Python
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, root_dir)

# Importa a classe GameApp do módulo app
# Assuming 'app' is a package at the root_dir level, and 'app.py' is a module within it.
# If 'app.py' is directly in the 'app' directory (which is common for Flask):

if __name__ == "__main__":
    # Cria uma instância da aplicação e a executa
    app = GameApp()
    app.run()
