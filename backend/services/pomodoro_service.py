import validacao
from dao.materia_dao import MateriaDAO
from dao.sessao_dao import SessaoDAO
from dao.topico_dao import TopicoDAO
from dao.usuario_dao import UsuarioDAO
from db import Conexao
from erros import ValidacaoErro
from models.sessao_estudo import SessaoEstudo
from services.gamificacao_service import GamificacaoService


class PomodoroService:
    def registrar_sessao(self, usuario_id, materia_id, duracao_min, topico_id=None, concluida=True):
        """Grava a sessão e, se foi concluída, concede XP (tudo na mesma transação)."""
        with Conexao() as conn:
            UsuarioDAO(conn).exigir(usuario_id)

            if topico_id is not None:
                topico_id = validacao.inteiro(topico_id, "topico_id", minimo=1)
                topico = TopicoDAO(conn).exigir(topico_id)
                if topico.usuario_id != usuario_id:
                    raise ValidacaoErro("O tópico informado não pertence a este usuário.")
                if materia_id is None:
                    materia_id = topico.materia_id
                elif validacao.inteiro(materia_id, "materia_id", minimo=1) != topico.materia_id:
                    raise ValidacaoErro("A matéria informada é diferente da matéria do tópico.")

            sessao = SessaoEstudo(usuario_id, materia_id, duracao_min, topico_id, concluida)
            MateriaDAO(conn).exigir(sessao.materia_id)
            salva = SessaoDAO(conn).inserir(sessao)

            gamificacao = None
            if salva.concluida:
                gamificacao = GamificacaoService(conn).conceder_xp(
                    usuario_id, "pomodoro",
                    GamificacaoService.pontos_sessao(salva.duracao_min),
                    f"Sessão de {salva.duracao_min} min",
                )
        return salva, gamificacao
