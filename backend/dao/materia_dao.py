import sqlite3

from dao.base_dao import BaseDAO
from erros import ConflitoErro
from models.materia import Materia


class MateriaDAO(BaseDAO):
    TABELA = "materia"
    MODELO = Materia
    NOME_ENTIDADE = "Matéria"

    def inserir(self, materia):
        try:
            novo_id, _ = self._executar(
                "INSERT INTO materia (nome, cor) VALUES (?, ?)", (materia.nome, materia.cor)
            )
        except sqlite3.IntegrityError:
            raise ConflitoErro("Já existe uma matéria com esse nome.")
        return self.exigir(novo_id)

    def atualizar(self, materia):
        try:
            self._executar(
                "UPDATE materia SET nome = ?, cor = ? WHERE id = ?",
                (materia.nome, materia.cor, materia.id),
            )
        except sqlite3.IntegrityError:
            raise ConflitoErro("Já existe uma matéria com esse nome.")
        return self.exigir(materia.id)

    def excluir(self, id):
        self.exigir(id)
        try:
            self._executar("DELETE FROM materia WHERE id = ?", (id,))
        except sqlite3.IntegrityError:
            raise ConflitoErro("A matéria está em uso por tópicos, sessões ou baralhos e não pode ser excluída.")

    def listar_todos(self, ordem="nome"):
        return super().listar_todos(ordem)
