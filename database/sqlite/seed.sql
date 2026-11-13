-- ============================================================
-- StudyHub - Dados iniciais (podem ser executados mais de uma vez)
-- ============================================================

PRAGMA foreign_keys = ON;

-- Usuário de demonstração (o front-end usa um seletor de usuário)
INSERT OR IGNORE INTO usuario (nome, email) VALUES
    ('Aluno Demo', 'demo@studyhub.com');

-- Matérias padrão
INSERT OR IGNORE INTO materia (nome, cor) VALUES
    ('Matemática',   '#e63946'),
    ('Português',    '#f4a261'),
    ('Física',       '#2a9d8f'),
    ('Química',      '#8338ec'),
    ('Biologia',     '#38b000'),
    ('História',     '#b5838d'),
    ('Geografia',    '#0077b6'),
    ('Inglês',       '#ff006e'),
    ('Programação',  '#3a86ff');

-- Conquistas (a regra de cada uma fica no GamificacaoService, pelo "codigo")
INSERT OR IGNORE INTO conquista (codigo, nome, descricao, xp_bonus) VALUES
    ('primeira_sessao',  'Primeiro Foco',      'Conclua sua primeira sessão Pomodoro.',        20),
    ('dez_sessoes',      'Maratonista',        'Conclua 10 sessões Pomodoro.',                 50),
    ('primeiro_topico',  'Revisor',            'Marque seu primeiro tópico como revisado.',    20),
    ('cinco_topicos',    'Estudioso',          'Revise 5 tópicos do planner.',                 50),
    ('primeiro_cartao',  'Memória Ativa',      'Revise seu primeiro flashcard.',               10),
    ('cinquenta_cartoes','Mestre das Cartas',  'Revise 50 flashcards.',                        60),
    ('nivel_5',          'Veterano',           'Alcance o nível 5.',                          100);
