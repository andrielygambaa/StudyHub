from dao.base_dao import BaseDAO
from models.topico import Topico


class TopicoDAO(BaseDAO):
    TABELA = "topico"
    MODELO = Topico
    NOME_ENTIDADE = "Tópico"

    def inserir(self, topico):
        novo_id, _ = self._executar(
            "INSERT INTO topico (usuario_id, materia_id, titulo, status) VALUES (?, ?, ?, ?)",
            (topico.usuario_id, topico.materia_id, topico.titulo, topico.status),
        )
        return self.exigir(novo_id)

    def atualizar(self, topico):
        self._executar(
            "UPDATE topico SET titulo = ?, materia_id = ?, status = ? WHERE id = ?",
            (topico.titulo, topico.materia_id, topico.status, topico.id),
        )
        return self.exigir(topico.id)

    def listar_do_usuario(self, usuario_id, materia_id=None, status=None):
        sql = "SELECT * FROM topico WHERE usuario_id = ?"
        params = [usuario_id]
        if materia_id is not None:
            sql += " AND materia_id = ?"
            params.append(materia_id)
        if status is not None:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY id DESC"
        return [Topico.de_linha(linha) for linha in self._linhas(sql, params)]

    def contar_por_status(self, usuario_id, status):
        return self._escalar(
            "SELECT COUNT(*) FROM topico WHERE usuario_id = ? AND status = ?", (usuario_id, status)
        )

    def progresso_por_materia(self, usuario_id):
        linhas = self._linhas(
            """
            SELECT m.id AS materia_id, m.nome AS materia, m.cor,
                   COUNT(t.id) AS total,
                   SUM(t.status = 'revisado') AS revisados,
                   SUM(t.status = 'estudando') AS estudando,
                   SUM(t.status = 'nao_visto') AS nao_vistos
              FROM topico t JOIN materia m ON m.id = t.materia_id
             WHERE t.usuario_id = ?
             GROUP BY m.id
             ORDER BY m.nome
            """,
            (usuario_id,),
        )
        resultado = []
        for linha in linhas:
            item = dict(linha)
            item["percentual_revisado"] = round(100 * item["revisados"] / item["total"])
            resultado.append(item)
        return resultado
