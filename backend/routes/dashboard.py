from flask import Blueprint, jsonify

from services.dashboard_service import DashboardService

bp = Blueprint("dashboard", __name__, url_prefix="/api")
service = DashboardService()


@bp.get("/usuarios/<int:usuario_id>/dashboard")
def dashboard(usuario_id):
    return jsonify(service.montar(usuario_id))
