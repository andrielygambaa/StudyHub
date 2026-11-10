from flask import Blueprint, jsonify

from dao.usuario_dao import UsuarioDAO
from models.usuario import Usuario
from routes.util import corpo_json

bp = Blueprint("usuarios", __name__, url_prefix="/api/usuarios")
dao = UsuarioDAO()


@bp.get("")
def listar():
    return jsonify([usuario.para_dict() for usuario in dao.listar_todos()])


@bp.post("")
def cadastrar():
    dados = corpo_json()
    usuario = dao.inserir(Usuario(nome=dados.get("nome"), email=dados.get("email")))
    return jsonify(usuario.para_dict()), 201


@bp.get("/<int:usuario_id>")
def consultar(usuario_id):
    return jsonify(dao.exigir(usuario_id).para_dict())


@bp.put("/<int:usuario_id>")
def atualizar(usuario_id):
    dados = corpo_json()
    usuario = dao.exigir(usuario_id)
    if "nome" in dados:
        usuario.nome = dados["nome"]
    if "email" in dados:
        usuario.email = dados["email"]
    return jsonify(dao.atualizar(usuario).para_dict())


@bp.delete("/<int:usuario_id>")
def excluir(usuario_id):
    dao.excluir(usuario_id)
    return "", 204
