from models.base import Entidade


class UsuarioConquista(Entidade):
    """Associação N:N entre Usuario e Conquista (tabela usuario_conquista)."""

    _COLUNAS = ("usuario_id", "conquista_id", "desbloqueada_em")

    def __init__(self, usuario_id, conquista_id, desbloqueada_em=None, conquista=None):
        self._usuario_id = usuario_id
        self._conquista_id = conquista_id
        self._desbloqueada_em = desbloqueada_em
        self._conquista = conquista

    @property
    def usuario_id(self):
        return self._usuario_id

    @property
    def conquista_id(self):
        return self._conquista_id

    @property
    def desbloqueada_em(self):
        return self._desbloqueada_em

    @property
    def conquista(self):
        return self._conquista

    def para_dict(self):
        dados = super().para_dict()
        if self._conquista is not None:
            dados["conquista"] = self._conquista.para_dict()
        return dados
