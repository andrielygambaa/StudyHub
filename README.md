# StudyHub

Plataforma de estudos desenvolvida para o **Projeto Integrado (DWS + POO + BD)** do Colégio UNASP, 2º TI.

O StudyHub reúne quatro módulos ligados por uma camada de gamificação:

- **Pomodoro**: registro de sessões de estudo por matéria.
- **Planner**: tópicos por matéria, com status (não visto, estudando, revisado).
- **Flashcards**: baralhos e cartões com repetição espaçada.
- **Gamificação**: XP, níveis e conquistas. Os outros módulos concedem XP por meio do `GamificacaoService`.

## Tecnologias

- **Banco de dados:** MySQL (10 tabelas)
- **Back-end:** Python 3 com Flask e PyMySQL, usando Programação Orientada a Objetos (models, DAOs, services e rotas)
- **Front-end:** HTML, CSS e JavaScript (consumo das rotas Flask via Fetch)

## Como fazer funcionar

### O que instalar antes

1. **Python 3.9 ou superior** (https://www.python.org). No Windows, marque "Add Python to PATH" na instalação.
2. **MySQL** ligado no seu computador. Pode ser o **XAMPP** (clique em *Start* no MySQL) ou o **MySQL Server**.

### Passo a passo

```bash
# 1. Instalar as bibliotecas do projeto (na pasta do projeto)
pip install -r requirements.txt

# 2. Configurar o acesso ao MySQL
#    copie backend/.env.example para backend/.env e ajuste o usuário e a senha
#    (no XAMPP o usuário é "root" e a senha fica em branco)

# 3. Criar o banco, as tabelas e os dados iniciais
python backend/init_db.py

# 4. Iniciar o sistema
python backend/app.py
```

Depois abra **http://127.0.0.1:5000** no navegador. A página inicial mostra "Banco conectado (10 tabelas)" quando tudo está certo.

Para apagar tudo e recriar o banco do zero: `python backend/init_db.py --reset`

### O arquivo backend/.env

```
STUDYHUB_DB_HOST=localhost
STUDYHUB_DB_PORT=3306
STUDYHUB_DB_USER=root
STUDYHUB_DB_PASSWORD=sua_senha_aqui
STUDYHUB_DB_NAME=studyhub
```

Esse arquivo não vai para o GitHub (está no `.gitignore`), então a sua senha fica só no seu computador.

### Se der erro

| Mensagem | O que fazer |
|---|---|
| `O PyMySQL não está instalado` | rode `pip install -r requirements.txt` |
| `Usuário ou senha do MySQL incorretos` | corrija `STUDYHUB_DB_USER` e `STUDYHUB_DB_PASSWORD` no `backend/.env` |
| `Não consegui conectar ao MySQL` | ligue o MySQL (XAMPP: botão *Start*) e confira host e porta no `.env` |
| Página com "O banco não tem tabelas" | rode `python backend/init_db.py` |
| `cryptography` ou `caching_sha2_password` | rode `pip install cryptography` (já está no requirements) |

### Modo SQLite (opcional, para testar sem MySQL)

Se o MySQL ainda não estiver pronto, dá para rodar o sistema com um banco de arquivo, sem instalar nada. Coloque `STUDYHUB_BANCO=sqlite` no `backend/.env` e rode os passos 3 e 4. Os dados desse modo ficam em `database/studyhub.db`. Para o projeto valer na entrega, use o MySQL.

## Estrutura do repositório

```
studyhub/
├── database/
│   ├── schema.sql              # banco "studyhub" e as 10 tabelas (MySQL)
│   ├── seed.sql                # matérias, conquistas e usuário de demonstração
│   └── sqlite/                 # mesmos scripts para o modo de teste SQLite
├── docs/
│   ├── diagrama_classes.md     # UML (renderizado pelo GitHub)
│   ├── diagrama_classes.mermaid
│   ├── API.md                  # todas as rotas, regras de XP e conquistas
│   └── entrega/studyhub.sql    # script básico entregue ao professor
├── backend/
│   ├── app.py                  # aplicação Flask e tratamento de erros
│   ├── config.py               # configurações (lê o .env)
│   ├── db.py                   # classe Conexao (commit/rollback)
│   ├── init_db.py              # cria o banco a partir do schema.sql
│   ├── erros.py, validacao.py
│   ├── models/                 # classes do domínio
│   ├── dao/                    # acesso ao banco (SQL)
│   ├── services/               # regras entre módulos e transações
│   └── routes/                 # rotas Flask, um Blueprint por módulo
├── frontend/                   # HTML, CSS e JS
├── tests/                      # testes automatizados
├── requirements.txt
└── README.md
```

## Testes

```bash
python -m unittest discover -s tests -v
```

Com o MySQL ligado, os testes criam e apagam um banco separado chamado **`studyhub_teste`**. O banco `studyhub`, com os seus dados, nunca é tocado.

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

Tabelas: `usuario`, `materia`, `topico`, `sessao_estudo`, `baralho`, `cartao`, `revisao_cartao`, `xp_log`, `conquista` e `usuario_conquista` (N:N entre usuário e conquista, com chave primária composta).

## Etapas de entrega

| Etapa | Prazo | Conteúdo | Situação |
|---|---|---|---|
| Etapa 1 | 09/11/2026 | Modelagem e criação do banco: UML revisado, tabelas criadas e funcionando, conexão inicial do sistema com o banco | Concluída |
| Etapa 2 | 13/11/2026 | Back-end funcional em Python: classes, DAOs e rotas Flask (POO), cadastro e consulta no banco funcionando | Concluída |
| Entrega Final | 17/11/2026 | Sistema completo, com front-end (HTML/CSS/JS) consumindo as rotas Flask via Fetch, de ponta a ponta | Pendente |

## Autor
Andriely Gamba, turma (2º TIA) 
