from dao.cartao_dao import CartaoDAO
from db import Conexao
from services.gamificacao_service import GamificacaoService


class FlashcardService:
    def registrar_revisao(self, cartao_id, acertou):
        """Aplica a repetição espaçada, guarda o histórico e concede XP."""
        with Conexao() as conn:
            cartoes = CartaoDAO(conn)
            cartao = cartoes.exigir(cartao_id)
            usuario_id = cartoes.usuario_do_cartao(cartao_id)

            revisao = cartao.registrar_revisao(acertou)
            cartoes.atualizar_revisao(cartao)
            cartoes.inserir_revisao(revisao)

            pontos = (GamificacaoService.PONTOS_CARTAO_ACERTO if revisao.acertou
                      else GamificacaoService.PONTOS_CARTAO_ERRO)
            gamificacao = GamificacaoService(conn).conceder_xp(
                usuario_id, "flashcard", pontos,
                "Cartão acertado" if revisao.acertou else "Cartão revisado (errou)",
            )
        return cartao, revisao, gamificacao
