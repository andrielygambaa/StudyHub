"""Classe base das entidades do domínio."""


class Entidade:
    """Cada subclasse declara em _COLUNAS os campos que existem no banco.

    Os parâmetros do __init__ têm o mesmo nome das colunas, então
    `de_linha` consegue montar o objeto direto a partir de uma linha do SQLite.
    """

    _COLUNAS = ()

    @classmethod
    def de_linha(cls, linha):
        return cls(**{coluna: linha[coluna] for coluna in cls._COLUNAS})

    def para_dict(self):
        return {coluna: getattr(self, coluna) for coluna in self._COLUNAS}

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.para_dict()}>"
