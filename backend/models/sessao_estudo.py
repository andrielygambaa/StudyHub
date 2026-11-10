import validacao
from models.base import Entidade

DURACAO_MAXIMA_MIN = 240


class SessaoEstudo(Entidade):
    _COLUNAS = ("id", "usuario_id", "materia_id", "topico_id", "duracao_min", "concluida", "iniciada_em")

    def __init__(self, usuario_id, materia_id, duracao_min, topico_id=None,
                 concluida=True, id=None, iniciada_em=None):
        self._id = id
        self._usuario_id = validacao.inteiro(usuario_id, "usuario_id", minimo=1)
        self._materia_id = validacao.inteiro(materia_id, "materia_id", minimo=1)
        self._topico_id = None if topico_id is None else validacao.inteiro(topico_id, "topico_id", minimo=1)
        self._duracao_min = validacao.inteiro(duracao_min, "duracao_min", minimo=1, maximo=DURACAO_MAXIMA_MIN)
        self._concluida = validacao.booleano(concluida, "concluida")
        self._iniciada_em = iniciada_em

    @property
    def id(self):
        return self._id

    @property
    def usuario_id(self):
        return self._usuario_id

    @property
    def materia_id(self):
        return self._materia_id

    @property
    def topico_id(self):
        return self._topico_id

    @property
    def duracao_min(self):
        return self._duracao_min

    @property
    def concluida(self):
        return self._concluida

    @property
    def iniciada_em(self):
        return self._iniciada_em

    def concluir(self):
        self._concluida = True
