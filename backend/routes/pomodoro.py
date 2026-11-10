from flask import Blueprint, jsonify

from dao.sessao_dao import SessaoDAO
from dao.usuario_dao import UsuarioDAO
from routes.util import corpo_json, data_opcional
from services.pomodoro_service import PomodoroService

bp = Blueprint("pomodoro", __name__, url_prefix="/api")
dao = SessaoDAO()
service = PomodoroService()


@bp.get("/usuarios/<int:usuario_id>/sessoes")
def listar(usuario_id):
    UsuarioDAO().exigir(usuario_id)
    sessoes = dao.listar_do_usuario(usuario_id, data_opcional("de"), data_opcional("ate"))
    return jsonify([sessao.para_dict() for sessao in sessoes])


@bp.post("/usuarios/<int:usuario_id>/sessoes")
def registrar(usuario_id):
    dados = corpo_json()
    sessao, gamificacao = service.registrar_sessao(
        usuario_id=usuario_id,
        materia_id=dados.get("materia_id"),
        duracao_min=dados.get("duracao_min"),
        topico_id=dados.get("topico_id"),
        concluida=dados.get("concluida", True),
    )
    return jsonify({"sessao": sessao.para_dict(), "gamificacao": gamificacao}), 201


@bp.get("/sessoes/<int:sessao_id>")
def consultar(sessao_id):
    return jsonify(dao.exigir(sessao_id).para_dict())


@bp.delete("/sessoes/<int:sessao_id>")
def excluir(sessao_id):
    # O XP já concedido permanece (o xp_log funciona como um extrato)
    dao.excluir(sessao_id)
    return "", 204
