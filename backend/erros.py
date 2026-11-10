"""Erros de negócio da API. Cada um carrega o código HTTP que a rota deve devolver."""


class ErroApp(Exception):
    status = 400

    def __init__(self, mensagem):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ValidacaoErro(ErroApp):
    """Dado inválido enviado pelo cliente (400)."""
    status = 400


class NaoEncontradoErro(ErroApp):
    """Registro inexistente (404)."""
    status = 404


class ConflitoErro(ErroApp):
    """Operação conflita com o estado atual do banco (409)."""
    status = 409
