🧙‍♂️ AIDungeonRPG

Um RPG interativo baseado em texto, inspirado no AI Dungeon, desenvolvido com Python e Flask. Este projeto permite que jogadores embarquem em aventuras dinâmicas, interagindo com NPCs e explorando um mundo gerado proceduralmente.
🚀 Demonstração

oaicite:8
✨ Funcionalidades

    Criação e gerenciamento de personagens personalizados.

    Sistema de combate baseado em turnos.

    Exploração de locais com geração procedural.

    Interação com NPCs com diálogos dinâmicos.

    Sistema de inventário e coleta de itens.

    Histórico de mensagens para acompanhar a narrativa.

    Interface web responsiva utilizando Flask.

🛠️ Tecnologias Utilizadas

    Python 3.10+

    Flask

    Jinja2

    HTML/CSS/JavaScript

    Ruff, Black e isort para linting e formatação

    DeepSource para análise de código estático

📦 Instalação

    Clone o repositório:

    git clone https://github.com/Pissolato32/AIDungeonRPG.git
    cd AIDungeonRPG

    Crie e ative um ambiente virtual:

    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate

    Instale as dependências:

    pip install -r requirements.txt

    Configure as variáveis de ambiente (opcional):

    export FLASK_APP=run_game.py
    export FLASK_ENV=development

    Inicie o servidor:

    flask run

    Acesse o jogo em http://localhost:5000.

🧪 Testes

Para executar os testes automatizados:

pytest

📁 Estrutura do Projeto

AIDungeonRPG/
├── app/
│ ├── app.py
│ ├── routes.py
│ └── templates/
├── core/
│ ├── game_engine.py
│ ├── game_state_model.py
│ └── npc.py
├── tests/
├── run_game.py
├── requirements.txt
└── README.md

📌 Roadmap

Implementar sistema básico de combate

Adicionar geração procedural de locais

Integrar IA para diálogos mais realistas

Implementar sistema de missões e objetivos

    Adicionar suporte a múltiplos idiomas

🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.
📄 Licença

Este projeto está licenciado sob a Licença MIT. Consulte o arquivo LICENSE para mais detalhes.
