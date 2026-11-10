import validacao
from erros import ValidacaoErro
from models.base import Entidade

ORIGENS = ("pomodoro", "topico", "flashcard", "conquista")


class XPLog(Entidade):
    _COLUNAS = ("id", "usuario_id", "origem", "pontos", "descricao", "criado_em")

    def __init__(self, usuario_id, origem, pontos, descricao=None, id=None, criado_em=None):
        if origem not in ORIGENS:
            raise ValidacaoErro(f"Origem de XP inválida. Use: {', '.join(ORIGENS)}.")
        self._id = id
        self._usuario_id = usuario_id
        self._origem = origem
        self._pontos = validacao.inteiro(pontos, "pontos", minimo=1)
        self._descricao = descricao
        self._criado_em = criado_em

    @property
    def id(self):
        return self._id

    @property
    def usuario_id(self):
        return self._usuario_id

    @property
    def origem(self):
        return self._origem

    @property
    def pontos(self):
        return self._pontos

    @property
    def descricao(self):
        return self._descricao

    @property
    def criado_em(self):
        return self._criado_em
