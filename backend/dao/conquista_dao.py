from dao.base_dao import BaseDAO
from models.conquista import Conquista
from models.usuario_conquista import UsuarioConquista


class ConquistaDAO(BaseDAO):
    TABELA = "conquista"
    MODELO = Conquista
    NOME_ENTIDADE = "Conquista"

    def listar_todas(self):
        return self.listar_todos("id")

    def ids_desbloqueados(self, usuario_id):
        linhas = self._linhas(
            "SELECT conquista_id FROM usuario_conquista WHERE usuario_id = ?", (usuario_id,)
        )
        return {linha["conquista_id"] for linha in linhas}

    def desbloquear(self, usuario_id, conquista_id):
        """Registra a conquista para o usuário. Devolve False se ele já tinha."""
        _, afetadas = self._executar(
            "INSERT OR IGNORE INTO usuario_conquista (usuario_id, conquista_id) VALUES (?, ?)",
            (usuario_id, conquista_id),
        )
        return afetadas > 0

    def listar_do_usuario(self, usuario_id):
        linhas = self._linhas(
            """SELECT uc.usuario_id, uc.conquista_id, uc.desbloqueada_em,
                      c.id, c.codigo, c.nome, c.descricao, c.xp_bonus
                 FROM usuario_conquista uc JOIN conquista c ON c.id = uc.conquista_id
                WHERE uc.usuario_id = ?
                ORDER BY uc.desbloqueada_em, c.id""",
            (usuario_id,),
        )
        resultado = []
        for linha in linhas:
            conquista = Conquista.de_linha(linha)
            resultado.append(UsuarioConquista(
                usuario_id=linha["usuario_id"],
                conquista_id=linha["conquista_id"],
                desbloqueada_em=linha["desbloqueada_em"],
                conquista=conquista,
            ))
        return resultado
