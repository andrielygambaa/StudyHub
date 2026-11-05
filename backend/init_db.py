"""Cria o banco de dados do StudyHub a partir de database/schema.sql e seed.sql.

Uso (a partir da raiz do repositório):
    python backend/init_db.py            -> cria as tabelas e os dados iniciais
    python backend/init_db.py --reset    -> apaga o banco e recria do zero
"""

import sys

from config import DB_PATH, SCHEMA_PATH, SEED_PATH
from db import Conexao


def criar_banco(reset=False):
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Banco anterior removido: {DB_PATH.name}")

    conexao = Conexao()
    try:
        conexao.executar_script(SCHEMA_PATH)
        conexao.executar_script(SEED_PATH)
        conexao.conectar().commit()
        tabelas = conexao.listar_tabelas()
    finally:
        conexao.fechar()

    print(f"Banco criado em: {DB_PATH}")
    print(f"{len(tabelas)} tabelas: {', '.join(tabelas)}")


if __name__ == "__main__":
    criar_banco(reset="--reset" in sys.argv)
