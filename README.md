# REPLIT RPG

Um jogo de RPG baseado em texto com interface web.

## Como iniciar o jogo

Para iniciar o jogo, execute o seguinte comando na raiz do projeto:

```bash
python run_game.py
```

Depois, acesse o jogo em seu navegador:
http://localhost:5000

## Estrutura do projeto

- `ai/` - Módulos relacionados à inteligência artificial
- `app/` - Aplicação principal e rotas
- `core/` - Funcionalidades principais do jogo
- `data/` - Dados do jogo
- `static/` - Arquivos estáticos (CSS, JavaScript)
- `templates/` - Templates HTML
- `translations/` - Sistema de tradução
- `utils/` - Utilitários diversos
- `web/` - Componentes web

## Solução de problemas

Se encontrar erros de importação ou outros problemas, tente:

1. Verificar se todos os módulos necessários estão instalados:
   ```bash
   pip install -r requirements.txt
   ```

2. Usar o script simplificado `run_game.py` que foi criado para contornar problemas de importação.

3. Verificar os logs para identificar erros específicos.