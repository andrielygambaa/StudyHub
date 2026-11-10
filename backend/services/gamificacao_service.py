"""Camada de gamificação: concede XP, calcula nível e desbloqueia conquistas.

É chamada pelos módulos Pomodoro, Planner e Flashcards. Recebe a conexão
da transação em andamento, então o XP e a ação que o gerou são gravados
juntos (ou nenhum dos dois).
"""

from dao.cartao_dao import CartaoDAO
from dao.conquista_dao import ConquistaDAO
from dao.sessao_dao import SessaoDAO
from dao.topico_dao import TopicoDAO
from dao.usuario_dao import UsuarioDAO
from dao.xp_dao import XPLogDAO
from models.xp_log import XPLog


class GamificacaoService:
    # Tabela de pontos (XP) de cada ação
    PONTOS_TOPICO_REVISADO = 15
    PONTOS_CARTAO_ACERTO = 3
    PONTOS_CARTAO_ERRO = 1

    @staticmethod
    def pontos_sessao(duracao_min):
        """0,4 XP por minuto (25 min = 10 XP), no mínimo 1."""
        return max(1, duracao_min * 2 // 5)

    def __init__(self, conn):
        self._usuarios = UsuarioDAO(conn)
        self._xp = XPLogDAO(conn)
        self._conquistas = ConquistaDAO(conn)
        sessoes = SessaoDAO(conn)
        topicos = TopicoDAO(conn)
        cartoes = CartaoDAO(conn)

        # Regra de cada conquista, identificada pelo "codigo" da tabela conquista
        self._regras = {
            "primeira_sessao":   lambda uid: sessoes.contar_concluidas(uid) >= 1,
            "dez_sessoes":       lambda uid: sessoes.contar_concluidas(uid) >= 10,
            "primeiro_topico":   lambda uid: topicos.contar_por_status(uid, "revisado") >= 1,
            "cinco_topicos":     lambda uid: topicos.contar_por_status(uid, "revisado") >= 5,
            "primeiro_cartao":   lambda uid: cartoes.contar_revisoes(uid) >= 1,
            "cinquenta_cartoes": lambda uid: cartoes.contar_revisoes(uid) >= 50,
            "nivel_5":           lambda uid: self._usuarios.exigir(uid).calcular_nivel() >= 5,
        }

    def conceder_xp(self, usuario_id, origem, pontos, descricao=None):
        """Registra o XP, atualiza o total do usuário e confere as conquistas."""
        nivel_antes = self._usuarios.exigir(usuario_id).calcular_nivel()
        self._registrar_xp(usuario_id, origem, pontos, descricao)
        desbloqueadas = self.verificar_conquistas(usuario_id)

        usuario = self._usuarios.exigir(usuario_id)
        return {
            "origem": origem,
            "pontos": pontos,
            "xp_bonus_conquistas": sum(c.xp_bonus for c in desbloqueadas),
            "xp_total": usuario.xp_total,
            "nivel": usuario.calcular_nivel(),
            "subiu_de_nivel": usuario.calcular_nivel() > nivel_antes,
            "conquistas_desbloqueadas": [c.para_dict() for c in desbloqueadas],
        }

    def verificar_conquistas(self, usuario_id):
        """Desbloqueia as conquistas cujas regras foram atingidas e paga o bônus de XP.

        O bônus pode, por sua vez, desbloquear outra conquista (ex.: nível 5),
        por isso o laço repete até não aparecer nenhuma nova.
        """
        desbloqueadas = []
        while True:
            novas = []
            ja_tem = self._conquistas.ids_desbloqueados(usuario_id)
            for conquista in self._conquistas.listar_todas():
                regra = self._regras.get(conquista.codigo)
                if conquista.id in ja_tem or regra is None or not regra(usuario_id):
                    continue
                if self._conquistas.desbloquear(usuario_id, conquista.id):
                    novas.append(conquista)
                    if conquista.xp_bonus > 0:
                        self._registrar_xp(usuario_id, "conquista", conquista.xp_bonus,
                                           f"Conquista: {conquista.nome}")
            if not novas:
                return desbloqueadas
            desbloqueadas.extend(novas)

    def _registrar_xp(self, usuario_id, origem, pontos, descricao):
        usuario = self._usuarios.exigir(usuario_id)
        usuario.adicionar_xp(pontos)
        self._xp.inserir(XPLog(usuario_id, origem, pontos, descricao))
        self._usuarios.atualizar_xp(usuario)
