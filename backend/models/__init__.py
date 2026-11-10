"""Classes do domínio do StudyHub."""

from models.baralho import Baralho
from models.cartao import Cartao
from models.conquista import Conquista
from models.materia import Materia
from models.revisao_cartao import RevisaoCartao
from models.sessao_estudo import SessaoEstudo
from models.topico import Topico
from models.usuario import Usuario
from models.usuario_conquista import UsuarioConquista
from models.xp_log import XPLog

__all__ = [
    "Baralho", "Cartao", "Conquista", "Materia", "RevisaoCartao",
    "SessaoEstudo", "Topico", "Usuario", "UsuarioConquista", "XPLog",
]
