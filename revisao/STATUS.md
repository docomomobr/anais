# Controle de Revisão — Anais Docomomo

Última atualização: 2026-02-22

## Como revisar

1. Gerar a página HTML:
```bash
python3 scripts/gerar_revisao_html.py {slug}
xdg-open /tmp/revisao-{slug}.html
```

2. Anotar problemas em `revisao/obs_{slug}.md`:
```markdown
# {slug} — Observações de revisão

## {id-do-artigo}
- campo: descrição do problema

## Geral
- observações sobre o seminário inteiro
```

3. Só listar artigos que tiverem problema (sem notícia = OK).

4. Claude lê o arquivo, aplica correções, e marca como revisado no STATUS.

---

## Norte/Nordeste (Vol. 3)

| Slug | Artigos | Status | Observações |
|------|---------|--------|-------------|
| sdnne01 | 44 | ✅ Revisado | |
| sdnne02 | 33 | ✅ Revisado | |
| sdnne03 | 41 | ✅ Revisado | |
| sdnne04 | 45 | ❌ Pendente | Novo (2026-02-22). ISBN 978-85-63014-05-4. Publisher: UFRN |
| sdnne05 | 32 | ✅ Revisado | |
| sdnne06 | 104 | ✅ Revisado | 46 só resumo (sem PDF completo) |
| sdnne07 | 65 | ✅ Revisado | |
| sdnne08 | 41 | ✅ Revisado | |
| sdnne09 | 50 | ✅ Revisado | |
| sdnne10 | 85 | ❌ Pendente | |

## Sudeste (Vol. 2)

| Slug | Artigos | Status | Observações |
|------|---------|--------|-------------|
| sdmg01 | 26 | ❌ Pendente | 26 de 68 originais (subconjunto) |
| sdrj02 | 19 | ❌ Pendente | |
| sdrj03 | 4 | ❌ Pendente | Parcial (4 artigos localizados) |
| sdrj04 | 17 | ❌ Pendente | |
| sdsp03 | 74 | ❌ Pendente | |
| sdsp05 | 68 | ❌ Pendente | |
| sdsp06 | 37 | ❌ Pendente | |
| sdsp07 | 43 | ❌ Pendente | |
| sdsp08 | 40 | ❌ Pendente | |
| sdsp09 | 27 | ❌ Pendente | |

## Sul (Vol. 4)

| Slug | Artigos | Status | Observações |
|------|---------|--------|-------------|
| sdsul01 | 48 | ❌ Pendente | |
| sdsul02 | 35 | ❌ Pendente | |
| sdsul03 | 39 | ❌ Pendente | |
| sdsul04 | 46 | ❌ Pendente | |
| sdsul05 | 37 | ❌ Pendente | |
| sdsul06 | 24 | ❌ Pendente | |
| sdsul07 | 46 | ❌ Pendente | |
| sdsul08 | 51 | ❌ Pendente | |
| sdpr01 | 26 | ❌ Pendente | Novo (2026-02-22). Publisher: Núcleo Docomomo Paraná |
| sdpr02 | 19 | ❌ Pendente | Novo (2026-02-22). 10 seminário + 9 livro. Sem ISBN |

## Nacionais (Vol. 1)

Todos publicados no OJS de produção. Não precisam de revisão.

## Não localizados

- sdnne04: ~~não localizado~~ → localizado e importado (2026-02-22)
- sdsp04, sdrj01: não localizados
