from datetime import date

from flask import Blueprint, jsonify

from dao.baralho_dao import BaralhoDAO
from dao.cartao_dao import CartaoDAO
from dao.materia_dao import MateriaDAO
from dao.usuario_dao import UsuarioDAO
from erros import ValidacaoErro
from models.baralho import Baralho
from models.cartao import Cartao
from routes.util import corpo_json
from services.flashcard_service import FlashcardService

bp = Blueprint("flashcards", __name__, url_prefix="/api")
baralhos = BaralhoDAO()
cartoes = CartaoDAO()
service = FlashcardService()


# --- Baralhos ----------------------------------------------------------------
@bp.get("/usuarios/<int:usuario_id>/baralhos")
def listar_baralhos(usuario_id):
    UsuarioDAO().exigir(usuario_id)
    return jsonify(baralhos.listar_resumo_do_usuario(usuario_id, date.today().isoformat()))


@bp.post("/usuarios/<int:usuario_id>/baralhos")
def cadastrar_baralho(usuario_id):
    dados = corpo_json()
    UsuarioDAO().exigir(usuario_id)
    baralho = Baralho(usuario_id, dados.get("materia_id"), dados.get("nome"))
    MateriaDAO().exigir(baralho.materia_id)
    return jsonify(baralhos.inserir(baralho).para_dict()), 201


@bp.get("/baralhos/<int:baralho_id>")
def consultar_baralho(baralho_id):
    baralho = baralhos.buscar_com_cartoes(baralho_id)
    dados = baralho.para_dict()
    dados["cartoes"] = [cartao.para_dict() for cartao in baralho.cartoes]
    dados["para_revisar_hoje"] = len(baralho.cartoes_para_revisar())
    return jsonify(dados)


@bp.put("/baralhos/<int:baralho_id>")
def atualizar_baralho(baralho_id):
    dados = corpo_json()
    baralho = baralhos.exigir(baralho_id)
    if "nome" in dados:
        baralho.nome = dados["nome"]
    if "materia_id" in dados:
        baralho.materia_id = dados["materia_id"]
        MateriaDAO().exigir(baralho.materia_id)
    return jsonify(baralhos.atualizar(baralho).para_dict())


@bp.delete("/baralhos/<int:baralho_id>")
def excluir_baralho(baralho_id):
    baralhos.excluir(baralho_id)
    return "", 204


# --- Cartões -----------------------------------------------------------------
@bp.get("/baralhos/<int:baralho_id>/cartoes")
def listar_cartoes(baralho_id):
    baralhos.exigir(baralho_id)
    return jsonify([cartao.para_dict() for cartao in cartoes.listar_do_baralho(baralho_id)])


@bp.post("/baralhos/<int:baralho_id>/cartoes")
def cadastrar_cartao(baralho_id):
    dados = corpo_json()
    baralhos.exigir(baralho_id)
    cartao = Cartao(baralho_id, dados.get("frente"), dados.get("verso"))
    return jsonify(cartoes.inserir(cartao).para_dict()), 201


@bp.get("/baralhos/<int:baralho_id>/revisar")
def cartoes_para_revisar(baralho_id):
    """Cartões do baralho que vencem hoje ou já venceram."""
    baralho = baralhos.buscar_com_cartoes(baralho_id)
    return jsonify([cartao.para_dict() for cartao in baralho.cartoes_para_revisar()])


@bp.get("/usuarios/<int:usuario_id>/cartoes/pendentes")
def cartoes_pendentes(usuario_id):
    """Todos os cartões do usuário para revisar hoje, de todos os baralhos."""
    UsuarioDAO().exigir(usuario_id)
    pendentes = cartoes.listar_pendentes_do_usuario(usuario_id, date.today().isoformat())
    return jsonify([cartao.para_dict() for cartao in pendentes])


@bp.put("/cartoes/<int:cartao_id>")
def atualizar_cartao(cartao_id):
    dados = corpo_json()
    cartao = cartoes.exigir(cartao_id)
    if "frente" in dados:
        cartao.frente = dados["frente"]
    if "verso" in dados:
        cartao.verso = dados["verso"]
    return jsonify(cartoes.atualizar_conteudo(cartao).para_dict())


@bp.delete("/cartoes/<int:cartao_id>")
def excluir_cartao(cartao_id):
    cartoes.excluir(cartao_id)
    return "", 204


@bp.post("/cartoes/<int:cartao_id>/revisao")
def revisar_cartao(cartao_id):
    dados = corpo_json()
    if "acertou" not in dados:
        raise ValidacaoErro("O campo 'acertou' é obrigatório.")
    cartao, revisao, gamificacao = service.registrar_revisao(cartao_id, dados["acertou"])
    return jsonify({
        "cartao": cartao.para_dict(),
        "revisao": revisao.para_dict(),
        "gamificacao": gamificacao,
    })
