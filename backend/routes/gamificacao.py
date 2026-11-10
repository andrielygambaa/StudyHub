from flask import Blueprint, jsonify

from dao.conquista_dao import ConquistaDAO
from dao.usuario_dao import UsuarioDAO
from dao.xp_dao import XPLogDAO
from routes.util import inteiro_opcional

bp = Blueprint("gamificacao", __name__, url_prefix="/api")


@bp.get("/conquistas")
def catalogo():
    return jsonify([conquista.para_dict() for conquista in ConquistaDAO().listar_todas()])


@bp.get("/usuarios/<int:usuario_id>/conquistas")
def conquistas_do_usuario(usuario_id):
    UsuarioDAO().exigir(usuario_id)
    return jsonify([item.para_dict() for item in ConquistaDAO().listar_do_usuario(usuario_id)])


@bp.get("/usuarios/<int:usuario_id>/xp")
def extrato_de_xp(usuario_id):
    usuario = UsuarioDAO().exigir(usuario_id)
    limite = inteiro_opcional("limite", minimo=1, maximo=200) or 20
    registros = XPLogDAO().listar_do_usuario(usuario_id, limite)
    return jsonify({
        "usuario": usuario.para_dict(),
        "extrato": [registro.para_dict() for registro in registros],
    })
