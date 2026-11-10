"""Funções auxiliares das rotas."""

from flask import request

import validacao
from erros import ValidacaoErro


def corpo_json():
    """Devolve o corpo da requisição como dicionário (ou erro 400)."""
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ValidacaoErro("Envie um corpo JSON válido (um objeto).")
    return dados


def inteiro_opcional(nome, minimo=None, maximo=None):
    """Lê um parâmetro inteiro opcional da query string (?nome=1)."""
    valor = request.args.get(nome)
    if valor is None:
        return None
    return validacao.inteiro(valor, nome, minimo=minimo, maximo=maximo)


def data_opcional(nome):
    valor = request.args.get(nome)
    return None if valor is None else validacao.data_iso(valor, nome)
