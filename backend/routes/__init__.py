"""Rotas Flask (um Blueprint por módulo)."""

from routes import dashboard, flashcards, gamificacao, materias, planner, pomodoro, usuarios


def registrar_rotas(app):
    for modulo in (usuarios, materias, planner, pomodoro, flashcards, gamificacao, dashboard):
        app.register_blueprint(modulo.bp)
