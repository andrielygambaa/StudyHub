import validacao
from models.base import Entidade


class RevisaoCartao(Entidade):
    _COLUNAS = ("id", "cartao_id", "acertou", "revisado_em")

    def __init__(self, cartao_id, acertou, id=None, revisado_em=None):
        self._id = id
        self._cartao_id = cartao_id
        self._acertou = validacao.booleano(acertou, "acertou")
        self._revisado_em = revisado_em

    @property
    def id(self):
        return self._id

    @property
    def cartao_id(self):
        return self._cartao_id

    @property
    def acertou(self):
        return self._acertou

    @property
    def revisado_em(self):
        return self._revisado_em
