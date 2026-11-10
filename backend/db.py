"""Camada de conexão com o banco de dados (POO).

O banco padrão é o MySQL. O SQLite existe só como "modo de teste", para rodar
o sistema sem instalar nada (STUDYHUB_BANCO=sqlite).

Os DAOs usam a classe Conexao assim, nos dois bancos:

    with Conexao() as conn:
        conn.execute("INSERT INTO materia (nome, cor) VALUES (?, ?)", ("Artes", "#ff8800"))

Ao sair do bloco `with`, o commit é feito automaticamente (ou o rollback, se der
erro) e a conexão é fechada. Nos SQLs o parâmetro é sempre "?".
"""

import re
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import config

MYSQL = config.TIPO_BANCO == "mysql"

# Comando de inserção que ignora duplicados (muda de nome entre os bancos)
INSERT_IGNORE = "INSERT IGNORE" if MYSQL else "INSERT OR IGNORE"

_erros_integridade = [sqlite3.IntegrityError]
if MYSQL:
    try:
        import pymysql
        _erros_integridade.append(pymysql.err.IntegrityError)
    except ImportError:      # a mensagem de ajuda aparece em Conexao.conectar()
        pass
# Erro de chave duplicada, chave estrangeira etc. (use em `except ErroIntegridade`)
ErroIntegridade = tuple(_erros_integridade)


def comandos_sql(texto):
    """Divide um script .sql em comandos (ignora comentários "--")."""
    texto = re.sub(r"--[^\n]*", "", texto)
    return [c.strip() for c in texto.split(";") if c.strip()]


# ============================================================================
# MySQL
# ============================================================================
class Linha(dict):
    """Linha de resultado: acessa por nome (linha["id"]) ou por posição (linha[0])."""

    def __getitem__(self, chave):
        if isinstance(chave, int):
            return list(self.values())[chave]
        return super().__getitem__(chave)


def _converter(valor):
    """Datas viram texto ISO e somas (Decimal) viram número, como no SQLite."""
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return int(valor) if valor == valor.to_integral_value() else float(valor)
    return valor


class _Cursor:
    def __init__(self, cursor):
        self._cursor = cursor

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @staticmethod
    def _linha(dados):
        return Linha({chave: _converter(valor) for chave, valor in dados.items()})

    def fetchone(self):
        dados = self._cursor.fetchone()
        return None if dados is None else self._linha(dados)

    def fetchall(self):
        return [self._linha(dados) for dados in self._cursor.fetchall()]


class _Sessao:
    """Envolve a conexão do PyMySQL para ter o mesmo jeito de uso do SQLite."""

    def __init__(self, conexao):
        self._conexao = conexao

    def execute(self, sql, params=()):
        cursor = self._conexao.cursor()
        if params:
            cursor.execute(sql.replace("?", "%s"), tuple(params))
        else:
            cursor.execute(sql)
        return _Cursor(cursor)

    def commit(self):
        self._conexao.commit()

    def rollback(self):
        self._conexao.rollback()

    def close(self):
        self._conexao.close()


class ConexaoMySQL:
    _driver = None   # o PyMySQL é carregado só quando precisa (e pode ser trocado nos testes)

    def __init__(self, sem_banco=False, banco=None):
        self._banco = None if sem_banco else (banco or config.DB_NAME)
        self._sessao = None

    @classmethod
    def _carregar_driver(cls):
        if cls._driver is None:
            try:
                import pymysql
            except ImportError:
                raise RuntimeError("O PyMySQL não está instalado. Rode: pip install -r requirements.txt")
            cls._driver = pymysql
        return cls._driver

    def conectar(self):
        """Abre a conexão (se ainda não estiver aberta) e a devolve."""
        if self._sessao is None:
            driver = self._carregar_driver()
            parametros = dict(host=config.DB_HOST, port=config.DB_PORT, user=config.DB_USER,
                              password=config.DB_PASSWORD, charset="utf8mb4",
                              cursorclass=driver.cursors.DictCursor, autocommit=False)
            if self._banco:
                parametros["database"] = self._banco
            self._sessao = _Sessao(driver.connect(**parametros))
        return self._sessao

    def fechar(self):
        if self._sessao is not None:
            self._sessao.close()
            self._sessao = None

    def executar_bruto(self, sql):
        """Executa um comando sem trocar parâmetros (usado para criar o banco)."""
        self.conectar().execute(sql)

    def executar_script(self, caminho_sql):
        """Executa um arquivo .sql inteiro (cria o banco, as tabelas e os dados iniciais)."""
        texto = Path(caminho_sql).read_text(encoding="utf-8")
        # o script traz "studyhub" como nome padrão; troca pelo banco configurado
        texto = texto.replace("CREATE DATABASE IF NOT EXISTS studyhub", f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME}")
        texto = re.sub(r"\bUSE studyhub\b", f"USE {config.DB_NAME}", texto)
        for comando in comandos_sql(texto):
            self.executar_bruto(comando)

    def apagar_banco(self):
        self.executar_bruto(f"DROP DATABASE IF EXISTS {config.DB_NAME}")

    def testar(self):
        """Retorna True se o banco responde a uma consulta simples."""
        try:
            self.conectar().execute("SELECT 1").fetchone()
            return True
        except Exception:
            self.fechar()
            return False

    def listar_tabelas(self):
        linhas = self.conectar().execute("SHOW TABLES").fetchall()
        return sorted(linha[0] for linha in linhas)

    def __enter__(self):
        return self.conectar()

    def __exit__(self, tipo_erro, erro, traceback):
        if self._sessao is not None:
            if tipo_erro is None:
                self._sessao.commit()
            else:
                self._sessao.rollback()
        self.fechar()
        return False


# ============================================================================
# SQLite (modo de teste)
# ============================================================================
class ConexaoSQLite:
    def __init__(self, caminho=None, sem_banco=False, banco=None):
        self._caminho = str(caminho or config.DB_PATH)
        self._conn = None

    def conectar(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self._caminho)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def fechar(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def executar_bruto(self, sql):
        self.conectar().execute(sql)

    def executar_script(self, caminho_sql):
        self.conectar().executescript(Path(caminho_sql).read_text(encoding="utf-8"))

    def apagar_banco(self):
        self.fechar()
        if Path(self._caminho).exists():
            Path(self._caminho).unlink()

    def testar(self):
        try:
            self.conectar().execute("SELECT 1").fetchone()
            return True
        except sqlite3.Error:
            return False

    def listar_tabelas(self):
        linhas = self.conectar().execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [linha["name"] for linha in linhas]

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


Conexao = ConexaoMySQL if MYSQL else ConexaoSQLite
