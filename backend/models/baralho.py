import validacao
from models.base import Entidade


class Baralho(Entidade):
    _COLUNAS = ("id", "usuario_id", "materia_id", "nome", "criado_em")

    def __init__(self, usuario_id, materia_id, nome, id=None, criado_em=None):
        self._id = id
        self._usuario_id = validacao.inteiro(usuario_id, "usuario_id", minimo=1)
        self.materia_id = materia_id
        self.nome = nome
        self._criado_em = criado_em
        self._cartoes = []

    @property
    def id(self):
        return self._id

    @property
    def usuario_id(self):
        return self._usuario_id

    @property
    def materia_id(self):
        return self._materia_id

    @materia_id.setter
    def materia_id(self, valor):
        self._materia_id = validacao.inteiro(valor, "materia_id", minimo=1)

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valor):
        self._nome = validacao.texto(valor, "nome", maximo=100)

    @property
    def criado_em(self):
        return self._criado_em

    @property
    def cartoes(self):
        return list(self._cartoes)

    def definir_cartoes(self, cartoes):
        self._cartoes = list(cartoes)

    def cartoes_para_revisar(self, hoje=None):
        return [cartao for cartao in self._cartoes if cartao.precisa_revisar(hoje)]
