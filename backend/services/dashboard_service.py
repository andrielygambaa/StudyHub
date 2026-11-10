from datetime import date, timedelta

from dao.baralho_dao import BaralhoDAO
from dao.cartao_dao import CartaoDAO
from dao.conquista_dao import ConquistaDAO
from dao.sessao_dao import SessaoDAO
from dao.topico_dao import TopicoDAO
from dao.usuario_dao import UsuarioDAO
from dao.xp_dao import XPLogDAO
from db import Conexao


class DashboardService:
    """Reúne em uma única consulta os dados da tela inicial do StudyHub."""

    def montar(self, usuario_id):
        hoje = date.today()
        desde = (hoje - timedelta(days=6)).isoformat()

        with Conexao() as conn:
            usuario = UsuarioDAO(conn).exigir(usuario_id)
            sessoes = SessaoDAO(conn)

            por_dia = sessoes.minutos_por_dia(usuario_id, desde)
            minutos_por_dia = []
            for i in range(6, -1, -1):
                dia = (hoje - timedelta(days=i)).isoformat()
                minutos_por_dia.append({"data": dia, "minutos": por_dia.get(dia, 0)})

            conquistas = ConquistaDAO(conn)
            desbloqueadas = conquistas.listar_do_usuario(usuario_id)

            return {
                "usuario": usuario.para_dict(),
                "pomodoro": {
                    "minutos_na_semana": sum(item["minutos"] for item in minutos_por_dia),
                    "minutos_por_dia": minutos_por_dia,
                    "minutos_por_materia": sessoes.minutos_por_materia(usuario_id, desde),
                    "sessoes_concluidas": sessoes.contar_concluidas(usuario_id),
                },
                "planner": {
                    "progresso_por_materia": TopicoDAO(conn).progresso_por_materia(usuario_id),
                    "topicos_revisados": TopicoDAO(conn).contar_por_status(usuario_id, "revisado"),
                },
                "flashcards": {
                    "cartoes_para_revisar_hoje": CartaoDAO(conn).contar_pendentes_do_usuario(
                        usuario_id, hoje.isoformat()),
                    "baralhos": BaralhoDAO(conn).listar_resumo_do_usuario(usuario_id, hoje.isoformat()),
                },
                "gamificacao": {
                    "conquistas_desbloqueadas": len(desbloqueadas),
                    "total_conquistas": len(conquistas.listar_todas()),
                    "ultimos_xp": [r.para_dict() for r in XPLogDAO(conn).listar_do_usuario(usuario_id, 5)],
                },
            }
