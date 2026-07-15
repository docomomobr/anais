# Pipeline temporário — Revisão de referências sdbr16

Baseado nas etapas 1.2a, 1.2b, 1.2b+ e 1.2c do `pipeline_revisao.md`.

Estado atual: 323 artigos (288 artigos + 35 mesas).
- 271 com referências (total: 2404 refs, média 8.9/artigo)
- 17 artigos (não-mesa) sem referências
- 35 mesas sem referências
- 0 refs longas (>500 chars)
- 7 artigos com apenas 1 ref (suspeitos)
- 25 artigos com 2-3 refs
- 2 backfills pendentes
- 3 artigos com issues no sweep (1 split, 3 não-refs)
- 8 refs curtas (<25 chars) — verificar
- 6 refs com pontuação final (,;) — truncadas?

---

## Etapa 1 — Limpeza base (1.2a)

```bash
python3 scripts/clean_references.py --slug sdbr16 --dry-run
python3 scripts/clean_references.py --slug sdbr16
python3 scripts/check_references.py --slug sdbr16 --summary
```

Resolve: backfills (underscores ABNT), split de refs concatenadas, join de URLs órfãs.

**DONE**: □

---

## Etapa 2 — Sweep completo (1.2b)

```bash
python3 scripts/fix_validation_issues.py --slug sdbr16 --sweep-refs --dry-run
python3 scripts/fix_validation_issues.py --slug sdbr16 --sweep-refs
```

8 passadas: lixo grosso, headers, page breaks, fragmentos, endnotes, split, remoção, body text, near-dupes.

**DONE**: □

---

## Etapa 3 — Re-rodar backfills (1.2b+)

```bash
python3 scripts/clean_references.py --slug sdbr16 --dry-run
python3 scripts/clean_references.py --slug sdbr16
```

O sweep pode criar novos backfills ao splittar refs concatenadas.

**DONE**: □

---

## Etapa 4 — Verificação de refs curtas e truncadas

8 refs curtas (<25 chars) a investigar:

| id | ref | ação |
|----|-----|------|
| sdbr16-058 | "Sesc, Relatórios, 1992." | ref válida? verificar plumber |
| sdbr16-099 | "Abreu Filho, op. cit." | nota, não ref — remover |
| sdbr16-110 | "BIOGRAFIAS" | header infiltrado — remover |
| sdbr16-207 | "Murtinho 1990, 1." | ref Chicago abreviada — verificar plumber |
| sdbr16-207 | "Korngold 1943, 445–460." | ref Chicago abreviada — verificar plumber |
| sdbr16-207 | "Murtinho 1990, 3." | ref Chicago abreviada — verificar plumber |
| sdbr16-215 | "Ferraz, Affonso, 54." | ref Chicago abreviada — verificar plumber |
| sdbr16-222 | "Matossian, Xenakis, 48." | ref Chicago abreviada — verificar plumber |

6 refs com pontuação final (,;) — possivelmente truncadas:

| id | ref (preview) |
|----|---------------|
| sdbr16-001 | Munford, Lewis. Art and Technics. Nova York: Columbia Press, |
| sdbr16-073 | Abramson, Daniel M. Obsolescence: An Architectural History. Chicago: The Univers... |
| sdbr16-094 | Brandi, Cesare. Teoria da Restauração. São Paulo: Ateliê Editorial, |
| sdbr16-121 | Kamita, João Masao. Vilanova Artigas. São Paulo: Cosac Naify, 2000; |
| sdbr16-121 | Thomaz, Dalva. Um olhar sobre Vilanova Artigas... |
| sdbr16-210 | Crosby, Philip M. "Holey urbanisms: Team 10..." |

Verificar no plumber se estão truncadas ou se realmente terminam assim.

**DONE**: □

---

## Etapa 5 — Artigos com 0 refs: verificar nos PDFs

17 artigos (não-mesa) sem referências. Classificar cada um:

### 5a — Com plumber/PDF (4 artigos — verificar se há seção de referências)

| id | fontes | título |
|----|--------|--------|
| sdbr16-037 | plumber, pdf | O petróleo é nosso — REFAP, TEDUT, FAMP e EA |
| sdbr16-160 | plumber, pdf | Encruzilhadas modernas: Aldo van Eyck e a crítica humanista |
| sdbr16-201 | plumber, pdf | Monumentalidades americanas moderna e pré-moderna |
| sdbr16-271 | plumber, pdf | Arte sobre Arquitetura |

### 5b — Sem fontes (13 artigos — aceitar como sem refs)

| id | título |
|----|--------|
| sdbr16-042 | Niemeyer americano: 1938–1950 |
| sdbr16-054 | "Me dá nos nervos esse barulho" |
| sdbr16-072 | Arquitetura hospitalar: inovação e preservação urbana |
| sdbr16-082 | UNA II SP BR |
| sdbr16-085 | Cuidado e paridade: a Arquitetura de Barclay & Crousse |
| sdbr16-117 | Razões de uma última conversa: com Paulo Mendes da Rocha |
| sdbr16-172 | Humanidade e fé. Carla Juaçaba em exposição |
| sdbr16-173 | Participação feminina nos pavilhões da Serpentine Gallery |
| sdbr16-179 | A Taba contemporânea de Brasília |
| sdbr16-193 | Beyond the Forgotten Bonds: China-Brazil |
| sdbr16-229 | The living room / Miami 2001 |
| sdbr16-253 | O discurso urbano de Mendes da Rocha |
| sdbr16-272 | Modernização pelos trilhos |

**DONE**: □

---

## Etapa 6 — Artigos com 1 ref: verificar no plumber

7 artigos com apenas 1 referência — muito provável que a extração perdeu refs:

| id | ref atual | título |
|----|-----------|--------|
| sdbr16-008 | Artigas, Vilanova. "Le Corbusier e o Imperialismo"... | Fascistas, comunistas, racistas... |
| sdbr16-123 | Paula, Franklin Roberto Ferreira de. "O lugar do edifício..." | Décio Tozzi e o moderno em transformação... |
| sdbr16-136 | Robin George Collingwood, The Historical Imagination... | Edifício João Brícola... |
| sdbr16-153 | "Exposição." Jornal do Brasil (1904). | Exposições de Arquitetura... |
| sdbr16-208 | Renato Fiori, "O espaço da Praça da Matriz..." | A mão e sua impressão |
| sdbr16-211 | "Project Report", Cruz y Ortiz... | Desejos e realidade: concursos... |
| sdbr16-260 | Revista Manchete, Número Especial (nº 678)... | Entre o real e o ideal... |

Todos têm plumber. Verificar se há mais refs no documento.

**DONE**: □

---

## Etapa 7 — Artigos com 2 refs: verificar amostra no plumber

15 artigos com 2 refs — verificar se extração está incompleta:

| id | título |
|----|--------|
| sdbr16-002 | ... |
| sdbr16-010 | ... |
| sdbr16-019 | ... |
| sdbr16-099 | ... |
| sdbr16-116 | ... |
| sdbr16-135 | ... |
| sdbr16-275 | ... |
| sdbr16-277 | ... |

**DONE**: □

---

## Etapa 8 — Revisão LLM de referências (1.2c)

**REGRA ABSOLUTA**: Revisão LLM real — ler o plumber de cada artigo e comparar com as refs no banco.

**Foco principal (não é necessário ler todos os 271 artigos):**
1. Artigos com poucas refs (etapas 6-7 acima)
2. Artigos com refs curtas/truncadas (etapa 4)
3. Artigos cujo sweep encontrou problemas
4. Amostra aleatória para verificar qualidade geral

**Tipos de problema que escapam ao sweep:**
- Concatenação Chicago (boundary mixed-case, ref <500 chars)
- Notas sem número (narrativa que parece ref)
- Notas com ref embutida (nome próprio no início)
- Headers infiltrados
- Ponto de corte BIBLIOGRAFIA→NOTAS errado
- Near-dupes com variação

**DONE**: □

---

## Etapa 9 — Validação final e regeneração

```bash
python3 scripts/check_references.py --slug sdbr16 --summary
python3 scripts/validate_metadata.py --slug sdbr16
python3 scripts/gerar_revisao_html.py sdbr16
python3 scripts/dump_anais_db.py
```

**DONE**: □

---

## Checklist final

- [x] Etapa 1: clean_references — 1 split aplicado
- [x] Etapa 2: sweep_refs — 3 artigos (1 split, 3 não-refs removidas)
- [x] Etapa 3: re-rodar backfills — 0 novos
- [x] Etapa 4: refs curtas e truncadas — 10 artigos corrigidos (footnotes removidos, truncadas completadas, headers removidos, sdbr16-207 reconstruído com 20 refs)
- [x] Etapa 5: 4 artigos com 0 refs e PDF verificados — sdbr16-271 ganhou 13 refs; sdbr16-160 footnotes only (R11); sdbr16-037 e sdbr16-201 sem citações
- [x] Etapa 6: 7 artigos com 1 ref — sdbr16-123 (1→3), sdbr16-260 (1→7); 4 reclassificados como endnotes (R11→NULL); sdbr16-008 endnotes (R11→NULL)
- [x] Etapa 7: 8 artigos com 2 refs — sdbr16-002 (2→3), sdbr16-099 (0→7), sdbr16-116 (2→3), sdbr16-135 (2→11), sdbr16-275 (2→5), sdbr16-277 (2→14); sdbr16-010 e sdbr16-019 endnotes (R11→NULL)
- [x] Etapa 8: revisão LLM — spot-check confirmou artigos com REFERÊNCIAS OK; sdbr16-181 corrigido (sweep removeu 7 web refs legítimas, restaurado 4→11); sdbr16-021 e sdbr16-256 reclassificados como endnotes (R11→NULL)
- [x] Etapa 9: 0 issues check_references, 2 issues validate (A03+A19 preexistentes), HTML + dump OK

Estado final: 263 artigos com refs (2461 refs), 25 artigos sem refs (10 endnotes-only R11, 15 sem citações), 35 mesas sem refs.
