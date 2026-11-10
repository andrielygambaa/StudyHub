from dao.topico_dao import TopicoDAO
from db import Conexao
from services.gamificacao_service import GamificacaoService


class PlannerService:
    def mudar_status(self, topico_id, novo_status):
        return self._atualizar(topico_id, lambda topico: topico.mudar_status(novo_status))

    def avancar_status(self, topico_id):
        def avancar(topico):
            topico.avancar_status()
            return True
        return self._atualizar(topico_id, avancar)

    def _atualizar(self, topico_id, alteracao):
        """Aplica a alteração no tópico; ao ficar 'revisado' pela primeira vez, concede XP."""
        with Conexao() as conn:
            dao = TopicoDAO(conn)
            topico = dao.exigir(topico_id)
            mudou = alteracao(topico)
            dao.atualizar(topico)

            gamificacao = None
            if mudou and topico.status == "revisado":
                gamificacao = GamificacaoService(conn).conceder_xp(
                    topico.usuario_id, "topico",
                    GamificacaoService.PONTOS_TOPICO_REVISADO,
                    f"Tópico revisado: {topico.titulo}",
                )
        return topico, gamificacao
