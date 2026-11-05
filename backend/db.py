"""Camada de conexão com o banco de dados (POO).

Os DAOs da Etapa 2 vão usar a classe Conexao assim:

    with Conexao() as conn:
        conn.execute("INSERT INTO materia (nome) VALUES (?)", ("Artes",))

Ao sair do bloco `with`, o commit é feito automaticamente (ou o rollback,
se der erro) e a conexão é fechada.
"""

import sqlite3
from pathlib import Path

from config import DB_PATH


class Conexao:
    """Encapsula a conexão com o SQLite."""

    def __init__(self, caminho=DB_PATH):
        self._caminho = str(caminho)
        self._conn = None

    def conectar(self):
        """Abre a conexão (se ainda não estiver aberta) e a devolve."""
        if self._conn is None:
            self._conn = sqlite3.connect(self._caminho)
            self._conn.row_factory = sqlite3.Row          # acesso por nome da coluna
            self._conn.execute("PRAGMA foreign_keys = ON")  # ativa as chaves estrangeiras
        return self._conn

    def fechar(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def executar_script(self, caminho_sql):
        """Executa um arquivo .sql inteiro (usado para criar tabelas e dados iniciais)."""
        script = Path(caminho_sql).read_text(encoding="utf-8")
        self.conectar().executescript(script)

    def testar(self):
        """Retorna True se o banco responde a uma consulta simples."""
        try:
            self.conectar().execute("SELECT 1").fetchone()
            return True
        except sqlite3.Error:
            return False

    def listar_tabelas(self):
        """Nomes das tabelas criadas (ignora as tabelas internas do SQLite)."""
        linhas = self.conectar().execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [linha["name"] for linha in linhas]

    # Permite usar `with Conexao() as conn:`
    def __enter__(self):
        return self.conectar()

    def __exit__(self, tipo_erro, erro, traceback):
        if self._conn is not None:
            if tipo_erro is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        self.fechar()
        return False
