"""Aplicação Flask do StudyHub.

Execução (a partir da raiz do repositório):
    python backend/app.py

As rotas da API ficam em /api (veja docs/API.md). O Flask também serve o
front-end, então o Fetch usa o mesmo endereço (sem CORS).
"""

import sqlite3

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from config import DB_PATH, FRONTEND_DIR
from db import Conexao
from erros import ErroApp
from routes import registrar_rotas


def criar_app():
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    app.json.ensure_ascii = False   # acentos legíveis no JSON
    app.json.sort_keys = False      # mantém a ordem dos campos

    @app.get("/")
    def pagina_inicial():
        return app.send_static_file("index.html")

    @app.get("/api/health")
    def health():
        if not DB_PATH.exists():
            return jsonify(
                status="erro",
                mensagem="Banco não encontrado. Rode: python backend/init_db.py",
            ), 503

        conexao = Conexao()
        try:
            if not conexao.testar():
                return jsonify(status="erro", mensagem="Banco não respondeu."), 503
            tabelas = conexao.listar_tabelas()
        finally:
            conexao.fechar()

        return jsonify(status="ok", banco="conectado", total_tabelas=len(tabelas), tabelas=tabelas)

    registrar_rotas(app)

    # --- Erros sempre em JSON ---------------------------------------------
    @app.errorhandler(ErroApp)
    def erro_de_negocio(erro):
        return jsonify(erro=erro.mensagem), erro.status

    @app.errorhandler(sqlite3.IntegrityError)
    def erro_de_integridade(erro):
        return jsonify(erro="A operação viola uma regra de integridade do banco de dados."), 409

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        return jsonify(erro=erro.description), erro.code

    return app


app = criar_app()

if __name__ == "__main__":
    app.run(debug=True)
