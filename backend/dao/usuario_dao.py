import sqlite3

from dao.base_dao import BaseDAO
from erros import ConflitoErro
from models.usuario import Usuario


class UsuarioDAO(BaseDAO):
    TABELA = "usuario"
    MODELO = Usuario
    NOME_ENTIDADE = "Usuário"

    def inserir(self, usuario):
        try:
            novo_id, _ = self._executar(
                "INSERT INTO usuario (nome, email) VALUES (?, ?)",
                (usuario.nome, usuario.email),
            )
        except sqlite3.IntegrityError:
            raise ConflitoErro("Já existe um usuário com esse e-mail.")
        return self.exigir(novo_id)

    def atualizar(self, usuario):
        try:
            self._executar(
                "UPDATE usuario SET nome = ?, email = ? WHERE id = ?",
                (usuario.nome, usuario.email, usuario.id),
            )
        except sqlite3.IntegrityError:
            raise ConflitoErro("Já existe um usuário com esse e-mail.")
        return self.exigir(usuario.id)

    def atualizar_xp(self, usuario):
        self._executar("UPDATE usuario SET xp_total = ? WHERE id = ?", (usuario.xp_total, usuario.id))

    def buscar_por_email(self, email):
        linha = self._linha("SELECT * FROM usuario WHERE email = ?", (email,))
        return Usuario.de_linha(linha) if linha else None

    def listar_todos(self, ordem="nome"):
        return super().listar_todos(ordem)
