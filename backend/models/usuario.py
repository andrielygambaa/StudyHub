import validacao
from erros import ValidacaoErro
from models.base import Entidade

XP_POR_NIVEL = 100


class Usuario(Entidade):
    _COLUNAS = ("id", "nome", "email", "xp_total", "criado_em")

    def __init__(self, nome, email, id=None, xp_total=0, criado_em=None):
        self._id = id
        self.nome = nome
        self.email = email
        self._xp_total = validacao.inteiro(xp_total, "xp_total", minimo=0)
        self._criado_em = criado_em

    @property
    def id(self):
        return self._id

    @property
    def nome(self):
        return self._nome

    @nome.setter
    def nome(self, valor):
        self._nome = validacao.texto(valor, "nome", maximo=100)

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        self._email = validacao.email(valor)

    @property
    def xp_total(self):
        return self._xp_total

    @property
    def criado_em(self):
        return self._criado_em

    def adicionar_xp(self, pontos):
        if pontos <= 0:
            raise ValidacaoErro("Os pontos de XP devem ser positivos.")
        self._xp_total += pontos

    def calcular_nivel(self):
        return 1 + self._xp_total // XP_POR_NIVEL

    def xp_para_proximo_nivel(self):
        return XP_POR_NIVEL - (self._xp_total % XP_POR_NIVEL)

    def para_dict(self):
        dados = super().para_dict()
        dados["nivel"] = self.calcular_nivel()
        dados["xp_no_nivel"] = self._xp_total % XP_POR_NIVEL
        dados["xp_para_proximo_nivel"] = self.xp_para_proximo_nivel()
        return dados
