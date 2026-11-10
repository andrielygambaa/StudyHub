import validacao
from erros import ValidacaoErro
from models.base import Entidade

STATUS = ("nao_visto", "estudando", "revisado")


class Topico(Entidade):
    _COLUNAS = ("id", "usuario_id", "materia_id", "titulo", "status", "criado_em")

    def __init__(self, usuario_id, materia_id, titulo, status="nao_visto", id=None, criado_em=None):
        self._id = id
        self._usuario_id = validacao.inteiro(usuario_id, "usuario_id", minimo=1)
        self.materia_id = materia_id
        self.titulo = titulo
        self._status = self._validar_status(status)
        self._criado_em = criado_em

    @staticmethod
    def _validar_status(valor):
        if valor not in STATUS:
            raise ValidacaoErro(f"Status inválido. Use: {', '.join(STATUS)}.")
        return valor

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
    def titulo(self):
        return self._titulo

    @titulo.setter
    def titulo(self, valor):
        self._titulo = validacao.texto(valor, "titulo", maximo=150)

    @property
    def status(self):
        return self._status

    @property
    def criado_em(self):
        return self._criado_em

    def avancar_status(self):
        """nao_visto -> estudando -> revisado."""
        posicao = STATUS.index(self._status)
        if posicao == len(STATUS) - 1:
            raise ValidacaoErro("O tópico já está revisado.")
        self._status = STATUS[posicao + 1]

    def mudar_status(self, novo_status):
        """O status só pode avançar. Devolve True se houve mudança."""
        novo_status = self._validar_status(novo_status)
        if STATUS.index(novo_status) < STATUS.index(self._status):
            raise ValidacaoErro("O status só pode avançar: nao_visto, estudando, revisado.")
        mudou = novo_status != self._status
        self._status = novo_status
        return mudou
