from models.base import Entidade


class Conquista(Entidade):
    _COLUNAS = ("id", "codigo", "nome", "descricao", "xp_bonus")

    def __init__(self, codigo, nome, descricao, xp_bonus=0, id=None):
        self._id = id
        self._codigo = codigo
        self._nome = nome
        self._descricao = descricao
        self._xp_bonus = xp_bonus

    @property
    def id(self):
        return self._id

    @property
    def codigo(self):
        return self._codigo

    @property
    def nome(self):
        return self._nome

    @property
    def descricao(self):
        return self._descricao

    @property
    def xp_bonus(self):
        return self._xp_bonus
