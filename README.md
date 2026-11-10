# StudyHub

Plataforma de estudos desenvolvida para o **Projeto Integrado (DWS + POO + BD)** do Colégio UNASP, 2º TI.

O StudyHub reúne quatro módulos ligados por uma camada de gamificação:

- **Pomodoro**: registro de sessões de estudo por matéria.
- **Planner**: tópicos por matéria, com status (não visto, estudando, revisado).
- **Flashcards**: baralhos e cartões com repetição espaçada.
- **Gamificação**: XP, níveis e conquistas. Os outros módulos concedem XP por meio do `GamificacaoService`.

## Tecnologias

- **Banco de dados:** SQLite (10 tabelas)
- **Back-end:** Python 3 com Flask, usando Programação Orientada a Objetos (models, DAOs, services e rotas)
- **Front-end:** HTML, CSS e JavaScript (consumo das rotas Flask via Fetch)

## Estrutura do repositório

```
studyhub/
├── database/
│   ├── schema.sql              # criação das 10 tabelas
│   └── seed.sql                # matérias, conquistas e usuário de demonstração
├── docs/
│   ├── diagrama_classes.md     # UML (renderizado pelo GitHub)
│   ├── diagrama_classes.mermaid
│   └── API.md                  # todas as rotas, regras de XP e conquistas
├── backend/
│   ├── app.py                  # aplicação Flask e tratamento de erros
│   ├── config.py               # caminhos e configurações
│   ├── db.py                   # classe Conexao (commit/rollback)
│   ├── init_db.py              # cria o banco a partir do schema.sql
│   ├── erros.py                # erros de negócio (400, 404, 409)
│   ├── validacao.py            # validações reutilizadas
│   ├── models/                 # classes do domínio
│   ├── dao/                    # acesso ao banco (SQL)
│   ├── services/               # regras entre módulos e transações
│   └── routes/                 # rotas Flask, um Blueprint por módulo
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── tests/                      # testes automatizados
├── requirements.txt
└── README.md
```

## Como executar

```bash
# 1. (opcional) criar e ativar um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. instalar as dependências
pip install -r requirements.txt

# 3. criar o banco de dados (tabelas e dados iniciais)
python backend/init_db.py

# 4. iniciar o servidor
python backend/app.py
```

Depois, abra http://127.0.0.1:5000 no navegador. A página inicial mostra se a conexão com o banco está funcionando. Para conferir pela API: http://127.0.0.1:5000/api/health

Para apagar o banco e recriar do zero: `python backend/init_db.py --reset`

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes usam um banco temporário e nunca alteram `database/studyhub.db`.

## API

Todas as rotas ficam em `/api` e estão documentadas em [`docs/API.md`](docs/API.md), com os corpos das requisições, as regras de XP, as conquistas e a repetição espaçada dos flashcards.

Exemplo, registrando uma sessão Pomodoro de 25 minutos (o usuário de demonstração tem id 1):

```bash
curl -X POST http://127.0.0.1:5000/api/usuarios/1/sessoes \
     -H "Content-Type: application/json" \
     -d '{"materia_id": 1, "duracao_min": 25}'
```

A resposta traz a sessão gravada e o campo `gamificacao`, com o XP ganho e as conquistas desbloqueadas.

## Modelagem

O diagrama de classes está em [`docs/diagrama_classes.md`](docs/diagrama_classes.md).

Tabelas: `usuario`, `materia`, `topico`, `sessao_estudo`, `baralho`, `cartao`, `revisao_cartao`, `xp_log`, `conquista` e `usuario_conquista` (N:N entre usuário e conquista).

## Etapas de entrega

| Etapa | Prazo | Conteúdo | Situação |
|---|---|---|---|
| Etapa 1 | 09/11/2026 | Modelagem e criação do banco: UML revisado, tabelas criadas e funcionando, conexão inicial do sistema com o banco | Concluída |
| Etapa 2 | 13/11/2026 | Back-end funcional em Python: classes, DAOs e rotas Flask (POO), cadastro e consulta no banco funcionando | Concluída |
| Entrega Final | 17/11/2026 | Sistema completo, com front-end (HTML/CSS/JS) consumindo as rotas Flask via Fetch, de ponta a ponta | Pendente |

## Autor

Projeto individual. Preencha aqui: nome, turma (2º TI-_) e data.
