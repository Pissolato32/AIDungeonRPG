@echo off
echo ==> Rodando autopep8...
autopep8 . --in-place --recursive --aggressive --aggressive

echo ==> Rodando isort...
isort .

echo ==> Rodando black...
black .

echo ==> Rodando ruff (com correções)...
ruff check . --fix

echo ==> Formatação concluída!
