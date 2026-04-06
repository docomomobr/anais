# Pipeline temporário — Revisão de abstracts sdbr16

Baseado nas etapas 0.5, 1.5 e 1.10 do `pipeline_revisao.md` e módulo K do `modulos_pipeline.md`.

Estado atual: 323 artigos.
- 309 com abstract (96%)
- 3 com abstract_en (1% — abaixo do threshold 30%, não buscar faltantes)
- 12 com abstract_es
- 13 artigos sem abstract: 11 locale=es (correto — abstract_es preenchido), 2 locale=pt-BR
- 5 abstracts truncados (sem pontuação final)
- 1 keyword colada (sdbr16-m25)
- 1 título no abstract (sdbr16-282)

Fontes: docx em `fontes/artigos/` (prioridade), plumber em `fontes_plumber/`, IDML (artigos sem docx/pdf).

---

## Etapa 1 — validate --fix (auto-fixes A20, A25, A26, A27)

```bash
python3 scripts/validate_metadata.py --slug sdbr16 --fix --dry-run
python3 scripts/validate_metadata.py --slug sdbr16 --fix
```

**DONE**: [ ]

---

## Etapa 2 — Corrigir keywords coladas (sdbr16-m25)

Abstract termina com "Palavras-chave: RESTAURO DE" — cortar no marcador.

**DONE**: [ ]

---

## Etapa 3 — Corrigir abstracts truncados (IDML)

4 abstracts de artigos sem docx/plumber (extraídos do IDML). Conteúdo vazado no final:

| id | lixo vazado | ação |
|----|-------------|------|
| sdbr16-042 | "SESSÃO" (título da sessão) | trim no "." antes |
| sdbr16-172 | "PARTICIPAÇÃO FEMININA NOS PAVILHÕES DA" (título seguinte) | trim no "." antes |
| sdbr16-173 | "ESPETÁCULO EXPOSITIVO, DIREÇÃO FEMININA, LINA POR EXEMPLO" (keywords?) | trim no "." antes |

Para cada um: localizar a última frase completa e cortar.

**DONE**: [ ]

---

## Etapa 4 — Verificar sdbr16-138 (ellipsis ending)

Abstract termina com `"cachorro com muitos donos morre de fome..."`. Verificar no docx se é genuíno.

Docx: `fontes/artigos/138_SCHLEE_cachorro-com-muitos-donos.docx`

**DONE**: [ ]

---

## Etapa 5 — Corrigir sdbr16-282 (título no abstract)

Abstract começa com "Será que existiu um CIAM Brasileiro?" — coincide com o título mas pode ser a primeira frase do abstract. Verificar no docx.

Docx: `fontes/artigos/282_BENDER_existiu-um-ciam-brasileiro.docx`

**DONE**: [ ]

---

## Etapa 6 — Extrair abstract de artigos PT faltantes

2 artigos locale=pt-BR sem abstract:

| id | fontes | título |
|----|--------|--------|
| sdbr16-019 | docx + plumber | Cinco anos de implementação do plano de gestão... |
| sdbr16-201 | docx + plumber | Monumentalidades americanas moderna e pré-moderna... |

Extrair do docx (prioridade) ou plumber.

**DONE**: [ ]

---

## Etapa 7 — Verificar abstract_en (3 artigos)

Apenas 3 artigos com abstract_en. Verificar se estão corretos:

| id | chars | verificar |
|----|-------|-----------|
| sdbr16-174 | 1903 | no docx/plumber |
| sdbr16-193 | 1037 | file=None (IDML) |
| sdbr16-229 | 902 | file=None (IDML) |

**DONE**: [ ]

---

## Etapa 8 — Verificar abstract_es (12 artigos)

12 artigos com abstract_es. Verificar truncamento e idioma correto. Validar_abstracts.py já checou e deu OK em todos.

**DONE**: [ ]

---

## Etapa 9 — Spot-check amostra de abstracts existentes

Verificar 5-10 artigos aleatórios contra docx/plumber para confirmar qualidade geral.

**DONE**: [ ]

---

## Etapa 10 — Validação final e regeneração

```bash
python3 scripts/validar_abstracts.py --slug sdbr16
python3 scripts/validate_metadata.py --slug sdbr16
python3 scripts/gerar_revisao_html.py sdbr16
python3 scripts/dump_anais_db.py
```

**DONE**: [ ]

---

## Checklist final

- [x] Etapa 1: validate --fix — 0 auto-fixes (A03+A19 são reports)
- [x] Etapa 2: keywords coladas — sdbr16-m25 cortado em "Palavras-chave:" (626→598c)
- [x] Etapa 3: truncados IDML — 042 (lixo "SESSÃO"), 172 (título seguinte), 173 (keywords seguintes) cortados na última frase
- [x] Etapa 4: sdbr16-138 — reticências legítimas ("fome...") confirmado no docx
- [x] Etapa 5: sdbr16-282 — falso positivo (1a frase coincide com título, mas é o abstract real)
- [x] Etapa 6: abstracts PT faltantes — 019 e 201 sem resumo no docx (confirmado), campo fica vazio
- [x] Etapa 7: abstract_en — 3 artigos OK (174 confirmado contra docx, 193 e 229 sem truncamento)
- [x] Etapa 8: abstract_es — sdbr16-106 cortado (ES+PT colados, 3910→1949c); sdbr16-139 abstract_es removido (contaminação do sdbr16-006 via IDML); 11 restantes OK
- [x] Etapa 9: spot-check — 6 artigos conferidos contra docx, todos OK
- [x] Etapa 10: validação final — 1 A19 restante (falso positivo), 0 A03; HTML + dump OK

Estado final: 309 com abstract, 3 com abstract_en, 11 com abstract_es (era 12, removido 1 contaminação).
