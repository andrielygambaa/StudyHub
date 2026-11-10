"""Cria o banco de dados do StudyHub (database/schema.sql + database/seed.sql).

Uso (a partir da raiz do repositório):
    python backend/init_db.py            -> cria o banco, as tabelas e os dados iniciais
    python backend/init_db.py --reset    -> apaga o banco e recria do zero
"""

import sys

import config
from db import Conexao


def criar_banco(reset=False):
    admin = Conexao(sem_banco=True)   # no MySQL, conecta antes de o banco existir
    try:
        if reset:
            admin.apagar_banco()
            print("Banco anterior removido.")
        admin.executar_script(config.SCHEMA_PATH)
        admin.executar_script(config.SEED_PATH)
        admin.conectar().commit()
    finally:
        admin.fechar()

    conexao = Conexao()
    try:
        tabelas = conexao.listar_tabelas()
    finally:
        conexao.fechar()

    onde = config.DB_NAME if config.TIPO_BANCO == "mysql" else config.DB_PATH
    print(f"Banco pronto ({config.TIPO_BANCO}): {onde}")
    print(f"{len(tabelas)} tabelas: {', '.join(tabelas)}")


def _explicar(erro):
    """Traduz os erros mais comuns do MySQL para uma dica em português."""
    codigo = erro.args[0] if erro.args and isinstance(erro.args[0], int) else None
    if codigo == 1045:
        return "Usuário ou senha do MySQL incorretos. Confira STUDYHUB_DB_USER e STUDYHUB_DB_PASSWORD no arquivo backend/.env."
    if codigo in (2003, 2002):
        return "Não consegui conectar ao MySQL. Confira se ele está ligado (XAMPP/serviço) e o host e a porta no arquivo backend/.env."
    if codigo == 1049:
        return "O banco ainda não existe. Rode: python backend/init_db.py"
    return None


if __name__ == "__main__":
    try:
        criar_banco(reset="--reset" in sys.argv)
    except RuntimeError as erro:
        sys.exit(f"ERRO: {erro}")
    except Exception as erro:
        dica = _explicar(erro)
        sys.exit(f"ERRO: {dica}\n(detalhe técnico: {erro})" if dica else f"ERRO: {erro}")
