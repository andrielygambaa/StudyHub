"""Testes da camada de conexão MySQL usando um driver SIMULADO (não precisa de MySQL instalado).

Eles verificam a parte que é código nosso: troca de "?" por "%s", conversão de datas e
somas (Decimal), acesso às linhas por nome e por posição, e a execução dos scripts .sql.
O teste de verdade contra o MySQL é rodar os demais testes (test_api.py) com o MySQL ligado.
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import _ambiente  # noqa: F401
import db


class CursorFalso:
    def __init__(self, gravador, linhas):
        self.gravador, self.linhas = gravador, list(linhas)
        self.lastrowid, self.rowcount = 7, 1

    def execute(self, sql, args=None):
        self.gravador.append((sql, args))

    def fetchone(self):
        return self.linhas.pop(0) if self.linhas else None

    def fetchall(self):
        linhas, self.linhas = self.linhas, []
        return linhas


class ConexaoFalsa:
    def __init__(self, gravador, linhas):
        self.gravador, self.linhas = gravador, linhas
        self.commits = self.rollbacks = 0
        self.fechada = False

    def cursor(self):
        return CursorFalso(self.gravador, self.linhas)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.fechada = True


class DriverFalso:
    """Imita o módulo pymysql só no que a nossa Conexao usa."""

    class cursors:
        DictCursor = object

    def __init__(self, linhas=()):
        self.gravador, self.linhas, self.conexoes, self.parametros = [], list(linhas), [], []

    def connect(self, **parametros):
        self.parametros.append(parametros)
        conexao = ConexaoFalsa(self.gravador, self.linhas)
        self.conexoes.append(conexao)
        return conexao


class TestConexaoMySQL(unittest.TestCase):
    def setUp(self):
        self.driver = DriverFalso()
        db.ConexaoMySQL._driver = self.driver

    def tearDown(self):
        db.ConexaoMySQL._driver = None

    def test_interrogacao_vira_s_e_parametros_vao_juntos(self):
        with db.ConexaoMySQL() as conn:
            conn.execute("SELECT * FROM usuario WHERE id = ? AND email = ?", (1, "a@b.com"))
        self.assertEqual(self.driver.gravador, [("SELECT * FROM usuario WHERE id = %s AND email = %s", (1, "a@b.com"))])

    def test_sem_parametros_o_sql_vai_intacto(self):
        with db.ConexaoMySQL() as conn:
            conn.execute("SELECT 1 WHERE 'a' LIKE '%x'")
        self.assertEqual(self.driver.gravador, [("SELECT 1 WHERE 'a' LIKE '%x'", None)])

    def test_linhas_por_nome_e_por_posicao_com_tipos_convertidos(self):
        self.driver.linhas.append({"id": 3, "criado_em": datetime(2026, 11, 9, 14, 5, 7),
                                   "dia": date(2026, 11, 9), "minutos": Decimal("75"), "media": Decimal("2.5")})
        with db.ConexaoMySQL() as conn:
            linha = conn.execute("SELECT ...").fetchone()
        self.assertEqual(linha["criado_em"], "2026-11-09 14:05:07")
        self.assertEqual(linha["dia"], "2026-11-09")
        self.assertEqual(linha["minutos"], 75)
        self.assertIsInstance(linha["minutos"], int)
        self.assertEqual(linha["media"], 2.5)
        self.assertEqual(linha[0], 3)          # acesso por posição, como no SQLite
        self.assertEqual(dict(linha)["id"], 3)

    def test_fetchone_sem_resultado_devolve_none(self):
        with db.ConexaoMySQL() as conn:
            self.assertIsNone(conn.execute("SELECT ...").fetchone())

    def test_lastrowid_e_rowcount(self):
        with db.ConexaoMySQL() as conn:
            cursor = conn.execute("INSERT INTO x VALUES (?)", (1,))
            self.assertEqual((cursor.lastrowid, cursor.rowcount), (7, 1))

    def test_commit_no_sucesso_e_rollback_no_erro(self):
        with db.ConexaoMySQL() as conn:
            conn.execute("UPDATE x SET a = ?", (1,))
        self.assertEqual((self.driver.conexoes[0].commits, self.driver.conexoes[0].rollbacks), (1, 0))
        self.assertTrue(self.driver.conexoes[0].fechada)
        with self.assertRaises(ValueError):
            with db.ConexaoMySQL() as conn:
                conn.execute("UPDATE x SET a = ?", (2,))
                raise ValueError("falha no meio da transação")
        self.assertEqual((self.driver.conexoes[1].commits, self.driver.conexoes[1].rollbacks), (0, 1))
        self.assertTrue(self.driver.conexoes[1].fechada)

    def test_parametros_de_conexao_e_modo_sem_banco(self):
        with db.ConexaoMySQL():
            pass
        with db.ConexaoMySQL(sem_banco=True):
            pass
        com_banco, sem_banco = self.driver.parametros
        self.assertEqual(com_banco["database"], "studyhub_teste")
        self.assertEqual(com_banco["charset"], "utf8mb4")
        self.assertFalse(com_banco["autocommit"])
        self.assertNotIn("database", sem_banco)

    def test_listar_tabelas_usa_show_tables(self):
        self.driver.linhas.extend([{"Tables_in_studyhub_teste": "usuario"}, {"Tables_in_studyhub_teste": "materia"}])
        conexao = db.ConexaoMySQL()
        self.assertEqual(conexao.listar_tabelas(), ["materia", "usuario"])
        self.assertEqual(self.driver.gravador[-1][0], "SHOW TABLES")

    def test_script_vira_comandos_sem_comentarios_e_troca_o_nome_do_banco(self):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "t.sql"
            arquivo.write_text(
                "-- comentario; com ponto e virgula\nSET NAMES utf8mb4;\n"
                "CREATE DATABASE IF NOT EXISTS studyhub CHARACTER SET utf8mb4;\nUSE studyhub;\n"
                "CREATE TABLE a (id INT, -- inline\n x INT);\nINSERT IGNORE INTO a VALUES (1, 2);\n", encoding="utf-8")
            conexao = db.ConexaoMySQL(sem_banco=True)
            conexao.executar_script(arquivo)
        sqls = [s for s, _ in self.driver.gravador]
        self.assertEqual(len(sqls), 5)
        self.assertEqual(sqls[1], "CREATE DATABASE IF NOT EXISTS studyhub_teste CHARACTER SET utf8mb4")
        self.assertEqual(sqls[2], "USE studyhub_teste")
        self.assertNotIn("inline", sqls[3])

    def test_scripts_do_projeto_sao_divididos_corretamente(self):
        for nome, esperado in (("schema.sql", 10), ("seed.sql", 3)):
            texto = (Path(db.config.BASE_DIR) / "database" / nome).read_text(encoding="utf-8")
            comandos = db.comandos_sql(texto)
            self.assertEqual(sum(c.startswith(("CREATE TABLE", "INSERT IGNORE")) for c in comandos), esperado, nome)
            self.assertTrue(all("--" not in c for c in comandos))


class TestErrosDeIntegridade(unittest.TestCase):
    def test_erro_de_integridade_aceita_os_dois_bancos(self):
        import sqlite3
        self.assertIn(sqlite3.IntegrityError, db.ErroIntegridade)
        self.assertIn("INSERT", db.INSERT_IGNORE)


if __name__ == "__main__":
    unittest.main()
