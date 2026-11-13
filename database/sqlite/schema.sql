-- ============================================================
-- StudyHub - Projeto Integrado (DWS + POO + BD)
-- Script de criação do banco de dados (SQLite)
-- Etapa 1: estrutura das tabelas
-- ============================================================

PRAGMA foreign_keys = ON;

-- ------------------------------------------------------------
-- Base compartilhada: usuario e materia
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS usuario (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nome       TEXT    NOT NULL,
    email      TEXT    NOT NULL UNIQUE,
    xp_total   INTEGER NOT NULL DEFAULT 0 CHECK (xp_total >= 0),
    criado_em  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS materia (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome  TEXT NOT NULL UNIQUE,
    cor   TEXT NOT NULL DEFAULT '#6c757d'
);

-- ------------------------------------------------------------
-- Módulo Planner de estudos
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS topico (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL,
    materia_id  INTEGER NOT NULL,
    titulo      TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'nao_visto'
                CHECK (status IN ('nao_visto', 'estudando', 'revisado')),
    criado_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE,
    FOREIGN KEY (materia_id) REFERENCES materia (id) ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- Módulo Pomodoro (registro de sessões de estudo)
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sessao_estudo (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id   INTEGER NOT NULL,
    materia_id   INTEGER NOT NULL,
    topico_id    INTEGER,                         -- opcional
    duracao_min  INTEGER NOT NULL CHECK (duracao_min > 0),
    concluida    INTEGER NOT NULL DEFAULT 1 CHECK (concluida IN (0, 1)),
    iniciada_em  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE,
    FOREIGN KEY (materia_id) REFERENCES materia (id) ON DELETE RESTRICT,
    FOREIGN KEY (topico_id)  REFERENCES topico (id)  ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- Módulo Flashcards com repetição espaçada
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS baralho (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL,
    materia_id  INTEGER NOT NULL,
    nome        TEXT    NOT NULL,
    criado_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE,
    FOREIGN KEY (materia_id) REFERENCES materia (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS cartao (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    baralho_id       INTEGER NOT NULL,
    frente           TEXT    NOT NULL,
    verso            TEXT    NOT NULL,
    intervalo_dias   INTEGER NOT NULL DEFAULT 1 CHECK (intervalo_dias >= 1),
    proxima_revisao  TEXT    NOT NULL DEFAULT (date('now', 'localtime')),
    criado_em        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (baralho_id) REFERENCES baralho (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS revisao_cartao (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    cartao_id    INTEGER NOT NULL,
    acertou      INTEGER NOT NULL CHECK (acertou IN (0, 1)),
    revisado_em  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (cartao_id) REFERENCES cartao (id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Módulo Gamificação (camada que conecta todos os módulos)
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS xp_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL,
    origem      TEXT    NOT NULL
                CHECK (origem IN ('pomodoro', 'topico', 'flashcard', 'conquista')),
    pontos      INTEGER NOT NULL CHECK (pontos > 0),
    descricao   TEXT,
    criado_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conquista (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo     TEXT    NOT NULL UNIQUE,           -- usado pela regra em Python
    nome       TEXT    NOT NULL,
    descricao  TEXT    NOT NULL,
    xp_bonus   INTEGER NOT NULL DEFAULT 0 CHECK (xp_bonus >= 0)
);

-- Tabela associativa N:N entre usuario e conquista
CREATE TABLE IF NOT EXISTS usuario_conquista (
    usuario_id        INTEGER NOT NULL,
    conquista_id      INTEGER NOT NULL,
    desbloqueada_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (usuario_id, conquista_id),
    FOREIGN KEY (usuario_id)   REFERENCES usuario (id)   ON DELETE CASCADE,
    FOREIGN KEY (conquista_id) REFERENCES conquista (id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- Índices para as consultas mais comuns (dashboard e revisão)
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_topico_usuario_materia ON topico (usuario_id, materia_id);
CREATE INDEX IF NOT EXISTS idx_sessao_usuario_data    ON sessao_estudo (usuario_id, iniciada_em);
CREATE INDEX IF NOT EXISTS idx_cartao_revisao         ON cartao (baralho_id, proxima_revisao);
CREATE INDEX IF NOT EXISTS idx_xp_log_usuario         ON xp_log (usuario_id);
