# sdbr16 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-31 | Artigos: 320
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/320 | % |
|-------|-------|---|
| abstract | 307 | 96% |
| abstract_en | 3 | 1% |
| keywords | 228 | 71% |
| keywords_en | 0 | 0% |
| references | 263 | 82% |
| title_en | 0 | 0% |
| sections | 39 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit (e3d75101c)
- [x] **0.1** Levantar padrao: abstract 96%, kw 71%, refs 82% (PRESENTE); abstract_en 1%, kw_en 0%, title_en 0% (AUSENTE). Norma: misto ABNT+Chicago
- [x] **0.2** 13 sem abstract, 57 artigos sem kw (excl 35 mesas), 22 artigos sem refs (excl 35 mesas)
- [x] **0.3** Reinspecionados: 8 abstracts inseridos (docx+caderno), 36 keywords inseridas (docx+caderno), 6 refs inseridas (docx). 5 artigos genuinamente sem abstract (019,054,201,233,272)
- [x] **0.3b** Plumber extraido: 271 PDFs processados (profile: corpo 11pt, abstract 10pt, heading 12-14pt)
- [x] **0.4** Secoes OK: 39 secoes, 320/320 artigos mapeados
- [x] **0.5** Validate --fix: 3 auto-fixes (A31 ES em campo PT). sdbr16-028 locale corrigido para 'es'. Abstract contaminado limpo. A19/A32 falsos positivos. 43 A11 para sweep
- [x] **0.6** SKIP: abstract_en = 1% (< 30%)
- [x] **0.7** ES: 10 artigos locale=es (dados nos campos principais). abstract_es residual limpo (3 redundantes removidos)
- [x] **0.8** Abstracts verificados: 0 truncados, 0 overflow, 0 com credenciais. sdbr16-028 abstract contaminado limpo

## Fase 1 — Revisão automática

- [x] **1.1a** Titulos PT: seed (+29 titulos), normalizar (52 alterados), revisao LLM (90 correcoes: siglas, nomes proprios, genéricos). Dict retroalimentado: 12 palavras removidas
- [x] **1.1b** SKIP: title_en = 0
- [x] **1.1c** SKIP: title_en = 0
- [x] **1.2a** Refs limpeza base: 0 backfills, 0 splits, 0 URLs. Check: 3 problemas / 2157 refs (0.1%)
- [x] **1.2b** Refs sweep: 2 splits em 2 artigos (073, 257)
- [x] **1.2b+** Re-backfills: 0 novos backfills. 2159 refs total
- [x] **1.2c** Refs revisao LLM: 43 splits + 9 biografias removidas em 36 artigos. 0 refs >500 chars restantes
- [x] **1.3** Keywords: 3 artigos, 6 ALL CAPS convertidos
- [x] **1.5** Loop validacao: convergiu em 2 iteracoes. 1 A19 fix (138 abstract). 1 A32 restante (falso positivo)
- [x] **1.6** Cobertura: abstract 306/320, kw 259/320, refs 264/320, locale 320/320, secoes 320/320. Description gerada. Metadados seminario OK
- [x] **1.7** Autores: ALL CAPS normalizados (201 gn + 227 fn + 39 mixed), 79 merges, 2 Hispanic surnames fixados, 1 bio removida. 104 issues verificados contra docx
- [x] **1.8** Dedup: seed +9, 0 auto-merges, 61 ambiguos → revisao LLM: 4 merges, 55 distintos, 2 incertos. expand_initials: 0 pilotis matches
- [x] **1.9** ORCID: 209 buscados, 56 confirmados + aplicados. 283/403 (70.2%) com ORCID
- [x] **1.10** Revisao LLM final: 4 agentes paralelos processaram 320 artigos vs plumber. Validate final: 1 A21 auto-fix, 1 A19 falso positivo (sdbr16-138 termina com reticencias legítimas). Estado limpo.

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validate (2 issues residuais: A04+A19 falsos positivos), HTML gerado (320 artigos, 39 secoes), commit bb704e868

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [ ] **3.1** Diagnóstico unificado (correções automáticas + humanas → causa raiz)
- [ ] **3.2** Atualizar dict.db (remover genéricos, adicionar nomes próprios)
- [ ] **3.3** Atualizar scripts (se >=3 artigos com mesmo erro não coberto)
- [ ] **3.4** Atualizar pipeline (se gaps na ordem de execução)
- [ ] **3.5** Verificar: dry-run sem regressão
- [ ] **3.6** Registrar aprendizado (JSON + MEMORY.md)
- [ ] **3.7** Revisão de engenharia (autoavaliação + lints)
- [ ] **3.8** Checklist de conclusão
- [ ] **3.9** Fechar: dump + commit + push + CLAUDE.md
