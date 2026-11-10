-- ============================================================
-- StudyHub - estrutura do banco de dados (MySQL 5.7+ / 8.x ou MariaDB 10.x)
-- Usado pelo sistema: python backend/init_db.py
--
-- Diferença para o arquivo entregue ao professor (studyhub.sql, versão básica):
-- aqui as chaves estrangeiras têm ON DELETE (CASCADE, SET NULL, RESTRICT), para o
-- sistema conseguir apagar um usuário, baralho etc. junto com os dados que dependem dele.
-- ============================================================

SET NAMES utf8mb4;

-- ------------------------------------------------------------
-- 1) Banco de dados
-- ------------------------------------------------------------

CREATE DATABASE IF NOT EXISTS studyhub
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE studyhub;

-- ------------------------------------------------------------
-- 2) Tabelas
-- ------------------------------------------------------------

-- Base compartilhada: usuario e materia

CREATE TABLE IF NOT EXISTS usuario (
    id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome       VARCHAR(100) NOT NULL,
    email      VARCHAR(120) NOT NULL,
    xp_total   INT UNSIGNED NOT NULL DEFAULT 0,
    criado_em  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_usuario_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS materia (
    id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nome  VARCHAR(60)  NOT NULL,
    cor   CHAR(7)      NOT NULL DEFAULT '#6c757d',
    PRIMARY KEY (id),
    UNIQUE KEY uq_materia_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Módulo Planner de estudos

CREATE TABLE IF NOT EXISTS topico (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    usuario_id  INT UNSIGNED NOT NULL,
    materia_id  INT UNSIGNED NOT NULL,
    titulo      VARCHAR(150) NOT NULL,
    status      ENUM('nao_visto', 'estudando', 'revisado') NOT NULL DEFAULT 'nao_visto',
    criado_em   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_topico_usuario_materia (usuario_id, materia_id),
    CONSTRAINT fk_topico_usuario FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE,
    CONSTRAINT fk_topico_materia FOREIGN KEY (materia_id) REFERENCES materia (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Módulo Pomodoro (registro de sessões de estudo)

CREATE TABLE IF NOT EXISTS sessao_estudo (
    id           INT UNSIGNED      NOT NULL AUTO_INCREMENT,
    usuario_id   INT UNSIGNED      NOT NULL,
    materia_id   INT UNSIGNED      NOT NULL,
    topico_id    INT UNSIGNED      NULL,                -- opcional
    duracao_min  SMALLINT UNSIGNED NOT NULL,
    concluida    TINYINT(1)        NOT NULL DEFAULT 1,
    iniciada_em  DATETIME          NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_sessao_usuario_data (usuario_id, iniciada_em),
    CONSTRAINT ck_sessao_duracao   CHECK (duracao_min > 0),
    CONSTRAINT ck_sessao_concluida CHECK (concluida IN (0, 1)),
    CONSTRAINT fk_sessao_usuario FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE,
    CONSTRAINT fk_sessao_materia FOREIGN KEY (materia_id) REFERENCES materia (id) ON DELETE RESTRICT,
    CONSTRAINT fk_sessao_topico  FOREIGN KEY (topico_id)  REFERENCES topico (id)  ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Módulo Flashcards com repetição espaçada

CREATE TABLE IF NOT EXISTS baralho (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    usuario_id  INT UNSIGNED NOT NULL,
    materia_id  INT UNSIGNED NOT NULL,
    nome        VARCHAR(100) NOT NULL,
    criado_em   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_baralho_usuario (usuario_id),
    CONSTRAINT fk_baralho_usuario FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE,
    CONSTRAINT fk_baralho_materia FOREIGN KEY (materia_id) REFERENCES materia (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS cartao (
    id               INT UNSIGNED      NOT NULL AUTO_INCREMENT,
    baralho_id       INT UNSIGNED      NOT NULL,
    frente           VARCHAR(500)      NOT NULL,
    verso            VARCHAR(500)      NOT NULL,
    intervalo_dias   SMALLINT UNSIGNED NOT NULL DEFAULT 1,
    proxima_revisao  DATE              NOT NULL,        -- informada pela aplicação (hoje + intervalo)
    criado_em        DATETIME          NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_cartao_revisao (baralho_id, proxima_revisao),
    CONSTRAINT ck_cartao_intervalo CHECK (intervalo_dias >= 1),
    CONSTRAINT fk_cartao_baralho FOREIGN KEY (baralho_id) REFERENCES baralho (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS revisao_cartao (
    id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
    cartao_id    INT UNSIGNED NOT NULL,
    acertou      TINYINT(1)   NOT NULL,
    revisado_em  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_revisao_cartao (cartao_id),
    CONSTRAINT ck_revisao_acertou CHECK (acertou IN (0, 1)),
    CONSTRAINT fk_revisao_cartao FOREIGN KEY (cartao_id) REFERENCES cartao (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Módulo Gamificação (camada que conecta todos os módulos)

CREATE TABLE IF NOT EXISTS xp_log (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    usuario_id  INT UNSIGNED NOT NULL,
    origem      ENUM('pomodoro', 'topico', 'flashcard', 'conquista') NOT NULL,
    pontos      INT UNSIGNED NOT NULL,
    descricao   VARCHAR(255) NULL,
    criado_em   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_xp_log_usuario (usuario_id),
    CONSTRAINT ck_xp_pontos CHECK (pontos > 0),
    CONSTRAINT fk_xp_usuario FOREIGN KEY (usuario_id) REFERENCES usuario (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS conquista (
    id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    codigo     VARCHAR(40)  NOT NULL,                   -- usado pela regra no sistema
    nome       VARCHAR(80)  NOT NULL,
    descricao  VARCHAR(255) NOT NULL,
    xp_bonus   INT UNSIGNED NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_conquista_codigo (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela associativa N:N entre usuario e conquista (chave primária composta)

CREATE TABLE IF NOT EXISTS usuario_conquista (
    usuario_id       INT UNSIGNED NOT NULL,
    conquista_id     INT UNSIGNED NOT NULL,
    desbloqueada_em  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, conquista_id),
    KEY idx_uc_conquista (conquista_id),
    CONSTRAINT fk_uc_usuario   FOREIGN KEY (usuario_id)   REFERENCES usuario (id)   ON DELETE CASCADE,
    CONSTRAINT fk_uc_conquista FOREIGN KEY (conquista_id) REFERENCES conquista (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
