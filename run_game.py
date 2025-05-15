#!/usr/bin/env python
"""
Script de inicialização para o jogo RPG.
"""

import os
import sys
import logging
from flask import Flask, render_template, session

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adiciona o diretório raiz do projeto ao path do Python
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

# Importa a função de tradução simplificada
from translations.simple import get_text
from app.routes import bp as routes_bp

# Cria uma aplicação Flask simples para iniciar
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Adiciona a função get_text aos templates
app.jinja_env.globals.update(get_text=get_text)
app.register_blueprint(routes_bp)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
def game():
    # Inicializa a sessão se necessário
    if 'language' not in session:
        session['language'] = 'pt-br'
    return render_template('game.html')

@app.route('/character')
def character():
    # Inicializa a sessão se necessário
    if 'language' not in session:
        session['language'] = 'pt-br'
    return render_template('character.html')

if __name__ == "__main__":
    logger.info("Iniciando aplicação RPG")
    app.run(host='0.0.0.0', port=5000, debug=True)