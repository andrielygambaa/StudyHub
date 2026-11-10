"""Funções de validação reutilizadas pelos models e pelas rotas."""

import re
from datetime import date

from erros import ValidacaoErro

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_COR = re.compile(r"^#[0-9a-fA-F]{6}$")


def texto(valor, campo, minimo=1, maximo=100):
    if valor is None or not isinstance(valor, str):
        raise ValidacaoErro(f"O campo '{campo}' é obrigatório e deve ser um texto.")
    valor = valor.strip()
    if len(valor) < minimo:
        raise ValidacaoErro(f"O campo '{campo}' é obrigatório.")
    if len(valor) > maximo:
        raise ValidacaoErro(f"O campo '{campo}' deve ter no máximo {maximo} caracteres.")
    return valor


def inteiro(valor, campo, minimo=None, maximo=None):
    if valor is None:
        raise ValidacaoErro(f"O campo '{campo}' é obrigatório.")
    if isinstance(valor, str) and valor.strip().lstrip("-").isdigit():
        valor = int(valor)
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValidacaoErro(f"O campo '{campo}' deve ser um número inteiro.")
    if minimo is not None and valor < minimo:
        raise ValidacaoErro(f"O campo '{campo}' deve ser no mínimo {minimo}.")
    if maximo is not None and valor > maximo:
        raise ValidacaoErro(f"O campo '{campo}' deve ser no máximo {maximo}.")
    return valor


def booleano(valor, campo):
    if isinstance(valor, bool):
        return valor
    if valor in (0, 1):
        return bool(valor)
    raise ValidacaoErro(f"O campo '{campo}' deve ser verdadeiro ou falso.")


def email(valor):
    valor = texto(valor, "email", maximo=120).lower()
    if not _EMAIL.match(valor):
        raise ValidacaoErro("O campo 'email' não é um e-mail válido.")
    return valor


def cor_hex(valor):
    valor = texto(valor, "cor", maximo=7)
    if not _COR.match(valor):
        raise ValidacaoErro("O campo 'cor' deve estar no formato #RRGGBB.")
    return valor.lower()


def data_iso(valor, campo):
    """Aceita 'AAAA-MM-DD' e devolve a mesma string validada."""
    try:
        return date.fromisoformat(str(valor)).isoformat()
    except ValueError:
        raise ValidacaoErro(f"O campo '{campo}' deve estar no formato AAAA-MM-DD.")
