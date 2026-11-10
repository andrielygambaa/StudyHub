from dao.base_dao import BaseDAO
from models.sessao_estudo import SessaoEstudo


class SessaoDAO(BaseDAO):
    TABELA = "sessao_estudo"
    MODELO = SessaoEstudo
    NOME_ENTIDADE = "Sessão de estudo"

    def inserir(self, sessao):
        novo_id, _ = self._executar(
            """INSERT INTO sessao_estudo (usuario_id, materia_id, topico_id, duracao_min, concluida)
               VALUES (?, ?, ?, ?, ?)""",
            (sessao.usuario_id, sessao.materia_id, sessao.topico_id,
             sessao.duracao_min, int(sessao.concluida)),
        )
        return self.exigir(novo_id)

    def listar_do_usuario(self, usuario_id, de=None, ate=None):
        sql = "SELECT * FROM sessao_estudo WHERE usuario_id = ?"
        params = [usuario_id]
        if de is not None:
            sql += " AND date(iniciada_em) >= ?"
            params.append(de)
        if ate is not None:
            sql += " AND date(iniciada_em) <= ?"
            params.append(ate)
        sql += " ORDER BY iniciada_em DESC, id DESC"
        return [SessaoEstudo.de_linha(linha) for linha in self._linhas(sql, params)]

    def contar_concluidas(self, usuario_id):
        return self._escalar(
            "SELECT COUNT(*) FROM sessao_estudo WHERE usuario_id = ? AND concluida = 1", (usuario_id,)
        )

    def minutos_por_materia(self, usuario_id, desde=None):
        sql = """SELECT m.id AS materia_id, m.nome AS materia, m.cor, SUM(s.duracao_min) AS minutos
                   FROM sessao_estudo s JOIN materia m ON m.id = s.materia_id
                  WHERE s.usuario_id = ? AND s.concluida = 1"""
        params = [usuario_id]
        if desde is not None:
            sql += " AND date(s.iniciada_em) >= ?"
            params.append(desde)
        sql += " GROUP BY m.id ORDER BY minutos DESC"
        return [dict(linha) for linha in self._linhas(sql, params)]

    def minutos_por_dia(self, usuario_id, desde):
        linhas = self._linhas(
            """SELECT date(iniciada_em) AS dia, SUM(duracao_min) AS minutos
                 FROM sessao_estudo
                WHERE usuario_id = ? AND concluida = 1 AND date(iniciada_em) >= ?
                GROUP BY dia""",
            (usuario_id, desde),
        )
        return {linha["dia"]: linha["minutos"] for linha in linhas}
