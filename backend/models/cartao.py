from datetime import date, timedelta

import validacao
from models.base import Entidade
from models.revisao_cartao import RevisaoCartao

INTERVALO_MAXIMO_DIAS = 365


def _como_data(valor):
    if valor is None:
        return date.today()
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor)[:10])


class Cartao(Entidade):
    """Flashcard com repetição espaçada.

    Acertou: o intervalo até a próxima revisão dobra (1, 2, 4, 8... dias).
    Errou: o intervalo volta para 1 dia.
    """

    _COLUNAS = ("id", "baralho_id", "frente", "verso", "intervalo_dias", "proxima_revisao", "criado_em")

    def __init__(self, baralho_id, frente, verso, id=None, intervalo_dias=1,
                 proxima_revisao=None, criado_em=None):
        self._id = id
        self._baralho_id = baralho_id
        self.frente = frente
        self.verso = verso
        self._intervalo_dias = validacao.inteiro(intervalo_dias, "intervalo_dias", minimo=1)
        self._proxima_revisao = _como_data(proxima_revisao)
        self._criado_em = criado_em

    @property
    def id(self):
        return self._id

    @property
    def baralho_id(self):
        return self._baralho_id

    @property
    def frente(self):
        return self._frente

    @frente.setter
    def frente(self, valor):
        self._frente = validacao.texto(valor, "frente", maximo=500)

    @property
    def verso(self):
        return self._verso

    @verso.setter
    def verso(self, valor):
        self._verso = validacao.texto(valor, "verso", maximo=500)

    @property
    def intervalo_dias(self):
        return self._intervalo_dias

    @property
    def proxima_revisao(self):
        return self._proxima_revisao

    @property
    def criado_em(self):
        return self._criado_em

    def precisa_revisar(self, hoje=None):
        return self._proxima_revisao <= (hoje or date.today())

    def registrar_revisao(self, acertou, hoje=None):
        """Atualiza o agendamento e devolve o registro da revisão."""
        acertou = validacao.booleano(acertou, "acertou")
        hoje = hoje or date.today()
        if acertou:
            self._intervalo_dias = min(self._intervalo_dias * 2, INTERVALO_MAXIMO_DIAS)
        else:
            self._intervalo_dias = 1
        self._proxima_revisao = hoje + timedelta(days=self._intervalo_dias)
        return RevisaoCartao(cartao_id=self._id, acertou=acertou)

    def para_dict(self):
        dados = super().para_dict()
        dados["proxima_revisao"] = self._proxima_revisao.isoformat()
        return dados
