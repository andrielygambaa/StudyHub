from flask import Blueprint, jsonify, request

from dao.materia_dao import MateriaDAO
from dao.topico_dao import TopicoDAO
from dao.usuario_dao import UsuarioDAO
from erros import ValidacaoErro
from models.topico import STATUS, Topico
from routes.util import corpo_json, inteiro_opcional
from services.planner_service import PlannerService

bp = Blueprint("planner", __name__, url_prefix="/api")
dao = TopicoDAO()
service = PlannerService()


def _resposta(topico, gamificacao):
    return jsonify({"topico": topico.para_dict(), "gamificacao": gamificacao})


@bp.get("/usuarios/<int:usuario_id>/topicos")
def listar(usuario_id):
    UsuarioDAO().exigir(usuario_id)
    status = request.args.get("status")
    if status is not None and status not in STATUS:
        raise ValidacaoErro(f"Status inválido. Use: {', '.join(STATUS)}.")
    topicos = dao.listar_do_usuario(usuario_id, inteiro_opcional("materia_id", minimo=1), status)
    return jsonify([topico.para_dict() for topico in topicos])


@bp.post("/usuarios/<int:usuario_id>/topicos")
def cadastrar(usuario_id):
    dados = corpo_json()
    UsuarioDAO().exigir(usuario_id)
    topico = Topico(usuario_id, dados.get("materia_id"), dados.get("titulo"))
    MateriaDAO().exigir(topico.materia_id)
    return jsonify(dao.inserir(topico).para_dict()), 201


@bp.get("/topicos/<int:topico_id>")
def consultar(topico_id):
    return jsonify(dao.exigir(topico_id).para_dict())


@bp.put("/topicos/<int:topico_id>")
def atualizar(topico_id):
    dados = corpo_json()
    topico = dao.exigir(topico_id)
    if "titulo" in dados:
        topico.titulo = dados["titulo"]
    if "materia_id" in dados:
        topico.materia_id = dados["materia_id"]
        MateriaDAO().exigir(topico.materia_id)
    return jsonify(dao.atualizar(topico).para_dict())


@bp.patch("/topicos/<int:topico_id>/status")
def mudar_status(topico_id):
    dados = corpo_json()
    return _resposta(*service.mudar_status(topico_id, dados.get("status")))


@bp.post("/topicos/<int:topico_id>/avancar")
def avancar_status(topico_id):
    return _resposta(*service.avancar_status(topico_id))


@bp.delete("/topicos/<int:topico_id>")
def excluir(topico_id):
    dao.excluir(topico_id)
    return "", 204
