"""Configurações do StudyHub (caminhos do banco e dos scripts SQL)."""

import os
from pathlib import Path

# Raiz do repositório (pasta acima de /backend)
BASE_DIR = Path(__file__).resolve().parent.parent

# A variável de ambiente STUDYHUB_DB permite usar outro banco (usado nos testes)
DB_PATH = Path(os.environ.get("STUDYHUB_DB", BASE_DIR / "database" / "studyhub.db"))
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
SEED_PATH = BASE_DIR / "database" / "seed.sql"

FRONTEND_DIR = BASE_DIR / "frontend"
