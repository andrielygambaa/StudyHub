# API do StudyHub

Base: `http://127.0.0.1:5000/api`. Todas as rotas recebem e devolvem JSON.
Não há login: o front-end escolhe o usuário e o envia na URL (`/usuarios/<id>/...`).

## Arquitetura do back-end

```mermaid
flowchart LR
    F["Front-end<br/>HTML / CSS / JS<br/>(Fetch)"] --> R["Rotas Flask<br/>Blueprints por modulo"]
    R --> S["Services<br/>regras entre modulos<br/>e transacoes"]
    R --> D["DAOs<br/>SQL parametrizado"]
    S --> D
    S --> M["Models<br/>classes do dominio<br/>e validacoes"]
    D --> M
    D --> C["Conexao<br/>commit / rollback"]
    C --> B[("SQLite<br/>10 tabelas")]
```

- **Rotas** (`backend/routes`): recebem a requisição, validam o corpo e devolvem JSON.
- **Services** (`backend/services`): regras que envolvem mais de uma tabela. Cada ação (por exemplo, registrar sessão e dar XP) é **uma transação só**: se algo falhar, nada é gravado.
- **DAOs** (`backend/dao`): todo o SQL do projeto, sempre parametrizado.
- **Models** (`backend/models`): classes com atributos privados, validações e regras (nível, repetição espaçada, status do tópico).

## Códigos de resposta

| Código | Quando |
|---|---|
| 200 / 201 / 204 | sucesso / criado / apagado |
| 400 | dado inválido (`{"erro": "mensagem"}`) |
| 404 | usuário, matéria, tópico etc. não encontrado |
| 409 | conflito: e-mail ou nome repetido, matéria em uso |

## Regras de gamificação

| Ação | XP |
|---|---|
| Sessão Pomodoro concluída | `duracao_min × 2 ÷ 5` (25 min = 10 XP). Sessão interrompida não dá XP |
| Tópico marcado como `revisado` (só na primeira vez) | 15 |
| Cartão acertado | 3 |
| Cartão errado | 1 |

Nível = `1 + xp_total ÷ 100`. Conquistas (o bônus de XP é pago automaticamente):

| Código | Regra | Bônus |
|---|---|---|
| `primeira_sessao` | 1 sessão concluída | 20 |
| `dez_sessoes` | 10 sessões concluídas | 50 |
| `primeiro_topico` | 1 tópico revisado | 20 |
| `cinco_topicos` | 5 tópicos revisados | 50 |
| `primeiro_cartao` | 1 cartão revisado | 10 |
| `cinquenta_cartoes` | 50 cartões revisados | 60 |
| `nivel_5` | chegar ao nível 5 | 100 |

**Repetição espaçada:** ao acertar, o intervalo até a próxima revisão dobra (1, 2, 4, 8... até 365 dias); ao errar, volta para 1 dia.

As rotas que geram XP devolvem o campo `gamificacao`, pronto para o front-end mostrar avisos:

```json
{
  "origem": "pomodoro", "pontos": 10, "xp_bonus_conquistas": 20,
  "xp_total": 30, "nivel": 1, "subiu_de_nivel": false,
  "conquistas_desbloqueadas": [{"codigo": "primeira_sessao", "nome": "Primeiro Foco", "xp_bonus": 20}]
}
```

## Rotas

### Usuários
| Método | Rota | Corpo | Observação |
|---|---|---|---|
| GET | `/usuarios` | | lista |
| POST | `/usuarios` | `{nome, email}` | 409 se o e-mail já existe |
| GET | `/usuarios/<id>` | | inclui `nivel`, `xp_no_nivel`, `xp_para_proximo_nivel` |
| PUT | `/usuarios/<id>` | `{nome?, email?}` | campos omitidos não mudam |
| DELETE | `/usuarios/<id>` | | apaga também tópicos, sessões, baralhos, XP e conquistas dele |
| GET | `/usuarios/<id>/dashboard` | | dados da tela inicial (veja abaixo) |

### Matérias
| Método | Rota | Corpo | Observação |
|---|---|---|---|
| GET | `/materias` | | lista, em ordem alfabética |
| POST | `/materias` | `{nome, cor?}` | `cor` no formato `#RRGGBB`; 409 se o nome já existe |
| GET / PUT / DELETE | `/materias/<id>` | `{nome?, cor?}` | DELETE dá 409 se a matéria estiver em uso |

### Planner (tópicos)
| Método | Rota | Corpo | Observação |
|---|---|---|---|
| GET | `/usuarios/<id>/topicos` | | filtros: `?materia_id=` e `?status=` |
| POST | `/usuarios/<id>/topicos` | `{materia_id, titulo}` | nasce como `nao_visto` |
| GET / PUT / DELETE | `/topicos/<id>` | `{titulo?, materia_id?}` | |
| PATCH | `/topicos/<id>/status` | `{status}` | só avança; ao virar `revisado` gera XP |
| POST | `/topicos/<id>/avancar` | | vai para o próximo status |

Resposta de status e avançar: `{"topico": {...}, "gamificacao": {...} ou null}`.

### Pomodoro (sessões)
| Método | Rota | Corpo | Observação |
|---|---|---|---|
| GET | `/usuarios/<id>/sessoes` | | filtros: `?de=AAAA-MM-DD&ate=AAAA-MM-DD` |
| POST | `/usuarios/<id>/sessoes` | `{materia_id, duracao_min, topico_id?, concluida?}` | duração de 1 a 240 min; `concluida` é `true` por padrão; se vier `topico_id` sem `materia_id`, usa a matéria do tópico |
| GET / DELETE | `/sessoes/<id>` | | apagar a sessão não retira o XP já ganho |

Resposta do POST: `{"sessao": {...}, "gamificacao": {...} ou null}`.

### Flashcards
| Método | Rota | Corpo | Observação |
|---|---|---|---|
| GET | `/usuarios/<id>/baralhos` | | traz `materia`, `total_cartoes` e `para_revisar` |
| POST | `/usuarios/<id>/baralhos` | `{materia_id, nome}` | |
| GET / PUT / DELETE | `/baralhos/<id>` | `{nome?, materia_id?}` | o GET traz os `cartoes` |
| GET | `/baralhos/<id>/cartoes` | | |
| POST | `/baralhos/<id>/cartoes` | `{frente, verso}` | já fica disponível para revisar hoje |
| GET | `/baralhos/<id>/revisar` | | cartões que vencem hoje ou antes |
| GET | `/usuarios/<id>/cartoes/pendentes` | | pendentes de todos os baralhos |
| PUT / DELETE | `/cartoes/<id>` | `{frente?, verso?}` | |
| POST | `/cartoes/<id>/revisao` | `{acertou: true/false}` | reagenda o cartão e gera XP |

Resposta da revisão: `{"cartao": {...}, "revisao": {...}, "gamificacao": {...}}`.

### Gamificação
| Método | Rota | Observação |
|---|---|---|
| GET | `/conquistas` | catálogo com todas as conquistas |
| GET | `/usuarios/<id>/conquistas` | as que o usuário já desbloqueou |
| GET | `/usuarios/<id>/xp` | extrato de XP (`?limite=`, padrão 20) |

### Dashboard
`GET /usuarios/<id>/dashboard` devolve, em uma chamada: `usuario` (com nível), `pomodoro` (minutos na semana, minutos por dia dos últimos 7 dias, minutos por matéria), `planner` (progresso por matéria), `flashcards` (cartões para revisar hoje e resumo dos baralhos) e `gamificacao` (conquistas e últimos XP).

## Como testar

```bash
python -m unittest discover -s tests -v
```

Os testes usam um banco temporário e nunca alteram `database/studyhub.db`.
