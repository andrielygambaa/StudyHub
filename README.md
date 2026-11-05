# StudyHub

Plataforma de estudos desenvolvida para o **Projeto Integrado (DWS + POO + BD)** do Colégio UNASP, 2º TI.

O StudyHub reúne quatro módulos ligados por uma camada de gamificação:

- **Pomodoro**: registro de sessões de estudo por matéria.
- **Planner**: tópicos por matéria, com status (não visto, estudando, revisado).
- **Flashcards**: baralhos e cartões com repetição espaçada.
- **Gamificação**: XP, níveis e conquistas. Todos os outros módulos concedem XP por meio do `GamificacaoService`.

## Tecnologias

- **Banco de dados:** SQLite (10 tabelas)
- **Back-end:** Python 3 com Flask, usando Programação Orientada a Objetos (classes, DAOs, services)
- **Front-end:** HTML, CSS e JavaScript (consumo das rotas Flask via Fetch)

## Estrutura do repositório

```
studyhub/
├── database/
│   ├── schema.sql          # criação das 10 tabelas
│   └── seed.sql            # matérias, conquistas e usuário de demonstração
├── docs/
│   ├── diagrama_classes.md       # UML (renderizado pelo GitHub)
│   └── diagrama_classes.mermaid  # código-fonte do UML
├── backend/
│   ├── app.py              # aplicação Flask
│   ├── config.py           # caminhos e configurações
│   ├── db.py               # classe Conexao
│   ├── init_db.py          # cria o banco a partir do schema.sql
│   ├── models/             # classes do domínio (Etapa 2)
│   ├── dao/                # DAOs (Etapa 2)
│   ├── services/           # GamificacaoService (Etapa 2)
│   └── routes/             # rotas Flask por módulo (Etapa 2)
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
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

## Modelagem

O diagrama de classes está em [`docs/diagrama_classes.md`](docs/diagrama_classes.md).

Tabelas: `usuario`, `materia`, `topico`, `sessao_estudo`, `baralho`, `cartao`, `revisao_cartao`, `xp_log`, `conquista` e `usuario_conquista` (N:N entre usuário e conquista).

## Etapas de entrega

| Etapa | Prazo | Conteúdo | Situação |
|---|---|---|---|
| Etapa 1 | 09/11/2026 | Modelagem e criação do banco: UML revisado, tabelas criadas e funcionando, conexão inicial do sistema com o banco | Em andamento |
| Etapa 2 | 13/11/2026 | Back-end funcional em Python: classes, DAOs e rotas Flask (POO), cadastro e consulta no banco funcionando | Pendente |
| Entrega Final | 17/11/2026 | Sistema completo, com front-end (HTML/CSS/JS) consumindo as rotas Flask via Fetch, de ponta a ponta | Pendente |

## Autor

Nome: Andriely Gamba, turma: (2º TIA)
