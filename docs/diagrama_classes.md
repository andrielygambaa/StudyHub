# Diagrama de Classes (UML) - StudyHub

Diagrama de classes do domínio do sistema. O GitHub renderiza o bloco abaixo automaticamente.
O mesmo diagrama está em `diagrama_classes.mermaid`.

```mermaid
classDiagram
    direction TB

    class Usuario {
        -int id
        -str nome
        -str email
        -int xp_total
        -datetime criado_em
        +calcular_nivel() int
        +adicionar_xp(pontos) void
    }

    class Materia {
        -int id
        -str nome
        -str cor
    }

    class Topico {
        -int id
        -str titulo
        -str status
        -datetime criado_em
        +avancar_status() void
    }

    class SessaoEstudo {
        -int id
        -int duracao_min
        -bool concluida
        -datetime iniciada_em
        +concluir() void
    }

    class Baralho {
        -int id
        -str nome
        -datetime criado_em
        +cartoes_para_revisar() list
    }

    class Cartao {
        -int id
        -str frente
        -str verso
        -int intervalo_dias
        -date proxima_revisao
        +registrar_revisao(acertou) RevisaoCartao
    }

    class RevisaoCartao {
        -int id
        -bool acertou
        -datetime revisado_em
    }

    class XPLog {
        -int id
        -str origem
        -int pontos
        -str descricao
        -datetime criado_em
    }

    class Conquista {
        -int id
        -str codigo
        -str nome
        -str descricao
        -int xp_bonus
    }

    class UsuarioConquista {
        -datetime desbloqueada_em
    }

    class GamificacaoService {
        +conceder_xp(usuario_id, origem, pontos, descricao) XPLog
        +verificar_conquistas(usuario_id) list
    }


    Usuario "1" --> "*" Topico : planeja
    Usuario "1" --> "*" SessaoEstudo : realiza
    Usuario "1" --> "*" Baralho : cria
    Usuario "1" --> "*" XPLog : acumula
    Usuario "1" --> "*" UsuarioConquista : desbloqueia
    Conquista "1" --> "*" UsuarioConquista : e desbloqueada em

    Materia "1" --> "*" Topico : classifica
    Materia "1" --> "*" SessaoEstudo : classifica
    Materia "1" --> "*" Baralho : classifica

    Topico "0..1" <-- "*" SessaoEstudo : foco opcional

    Baralho "1" *-- "*" Cartao : contem
    Cartao "1" *-- "*" RevisaoCartao : historico

    GamificacaoService ..> Usuario : atualiza xp_total
    GamificacaoService ..> XPLog : registra
    GamificacaoService ..> UsuarioConquista : concede
    SessaoEstudo ..> GamificacaoService : concluir() gera XP
    Topico ..> GamificacaoService : status revisado gera XP
    Cartao ..> GamificacaoService : revisao gera XP
```

## Correspondência entre classes e tabelas do banco

| Classe | Tabela | Observação |
|---|---|---|
| Usuario | `usuario` | `xp_total` é atualizado pelo GamificacaoService |
| Materia | `materia` | catálogo compartilhado por todos os módulos |
| Topico | `topico` | status: `nao_visto`, `estudando`, `revisado` |
| SessaoEstudo | `sessao_estudo` | `topico_id` é opcional |
| Baralho | `baralho` | pertence a um usuário e a uma matéria |
| Cartao | `cartao` | `intervalo_dias` e `proxima_revisao` controlam a repetição espaçada |
| RevisaoCartao | `revisao_cartao` | histórico de acertos e erros |
| XPLog | `xp_log` | origem: `pomodoro`, `topico`, `flashcard`, `conquista` |
| Conquista | `conquista` | `codigo` identifica a regra no GamificacaoService |
| UsuarioConquista | `usuario_conquista` | tabela associativa N:N entre Usuario e Conquista |
| GamificacaoService | (sem tabela) | classe de serviço chamada pelos módulos Pomodoro, Planner e Flashcards |

## Relacionamentos

- **1:N**: Usuario com Topico, SessaoEstudo, Baralho e XPLog; Materia com Topico, SessaoEstudo e Baralho; Topico com SessaoEstudo (opcional).
- **N:N**: Usuario e Conquista, resolvido pela tabela `usuario_conquista`.
- **Composição**: Baralho contém Cartao, e Cartao contém RevisaoCartao (apagar o pai apaga os filhos).
