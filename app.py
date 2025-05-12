
from flask import Flask, render_template, session, request, jsonify, redirect, url_for
from flask_session import Session
import os

app = Flask(__name__)

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/character')
def character():
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON for AJAX requests
        return jsonify({'character': session.get('character', {})})
    return render_template('character.html')

@app.route('/game')
def game():
    if 'character' not in session:
        return redirect(url_for('character'))
    return render_template('game.html', character=session['character'], game_state={})
