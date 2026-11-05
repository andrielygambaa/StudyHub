"""Aplicação Flask do StudyHub.

Na Etapa 1 existe apenas a rota /api/health, que confirma a conexão
com o banco. As rotas dos módulos entram na Etapa 2 (pasta /routes).

Execução (a partir da raiz do repositório):
    python backend/app.py
"""

from flask import Flask, jsonify

from config import DB_PATH, FRONTEND_DIR
from db import Conexao


def criar_app():
    # O Flask também serve o front-end, assim o Fetch usa o mesmo endereço (sem CORS)
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")

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

    return app


app = criar_app()

if __name__ == "__main__":
    app.run(debug=True)
