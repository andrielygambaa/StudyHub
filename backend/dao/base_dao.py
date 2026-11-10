"""DAO base: acesso ao banco com SQL parametrizado.

Cada DAO pode ser criado de dois jeitos:
  - UsuarioDAO()       -> cada operação abre e fecha a própria conexão;
  - UsuarioDAO(conn)   -> usa uma conexão já aberta, para que vários DAOs
                          participem da MESMA transação (commit/rollback
                          ficam por conta de quem abriu a conexão).
"""

from contextlib import contextmanager

from db import Conexao
from erros import NaoEncontradoErro


class BaseDAO:
    TABELA = None
    MODELO = None
    NOME_ENTIDADE = "Registro"

    def __init__(self, conn=None):
        self._conn = conn

    @contextmanager
    def _sessao(self):
        if self._conn is not None:
            yield self._conn
        else:
            with Conexao() as conn:
                yield conn

    # --- utilitários de SQL -------------------------------------------------
    def _linhas(self, sql, params=()):
        with self._sessao() as conn:
            return conn.execute(sql, params).fetchall()

    def _linha(self, sql, params=()):
        with self._sessao() as conn:
            return conn.execute(sql, params).fetchone()

    def _escalar(self, sql, params=()):
        linha = self._linha(sql, params)
        return linha[0] if linha else None

    def _executar(self, sql, params=()):
        """Executa INSERT/UPDATE/DELETE e devolve (id_inserido, linhas_afetadas)."""
        with self._sessao() as conn:
            cursor = conn.execute(sql, params)
            return cursor.lastrowid, cursor.rowcount

    # --- operações comuns ---------------------------------------------------
    def buscar_por_id(self, id):
        linha = self._linha(f"SELECT * FROM {self.TABELA} WHERE id = ?", (id,))
        return self.MODELO.de_linha(linha) if linha else None

    def exigir(self, id):
        objeto = self.buscar_por_id(id)
        if objeto is None:
            raise NaoEncontradoErro(f"{self.NOME_ENTIDADE} não encontrado(a).")
        return objeto

    def listar_todos(self, ordem="id"):
        linhas = self._linhas(f"SELECT * FROM {self.TABELA} ORDER BY {ordem}")
        return [self.MODELO.de_linha(linha) for linha in linhas]

    def excluir(self, id):
        self.exigir(id)
        self._executar(f"DELETE FROM {self.TABELA} WHERE id = ?", (id,))
