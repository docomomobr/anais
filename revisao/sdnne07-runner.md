# sdnne07 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-25 | Artigos: 65
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/65 | % |
|-------|-------|---|
| abstract | 63 | 97% |
| abstract_en | 61 | 94% |
| keywords | 63 | 97% |
| keywords_en | 59 | 91% |
| references | 60 | 92% |
| title_en | 0 | 0% |
| sections | 1 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint: 1baa236
- [x] **0.1** Cobertura: abs 63/65, abs_en 61/65, kw 63/65, kw_en 59/65, refs 60/65, title_en 0/65
- [x] **0.2** Fora do padrão: 015/032 PDFs corrompidos (sem abstract/kw/refs), 007/037/042 sem refs no plumber
- [x] **0.3** 65 PDFs, sem docx. Fontes plumber extraídas (63 ok, 2 erros — 015/032 corrompidos)
- [x] **0.4** Seções: 1 seção única ("Artigos Completos"), site original sem eixos temáticos
- [x] **0.5** Lacunas: 015/032 corrompidos. 035 abstract_en extraído manualmente (typo "ABTRACT" no PDF)
- [x] **0.6** Extrair metadados EN: 4 keywords_en extras. 035 abstract_en + keywords_en preenchidos
- [x] **0.7** ES: sem artigos em espanhol (RESUMEN presente como 3o idioma, não indica locale ES)
- [x] **0.8** Validate --fix: 6 auto-fixes. 17 issues restantes

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 21 normalizer, 10 reversões (falsos positivos). 7 genéricos removidos do dict (tropical, banco, concurso, futebol, imóveis, três, urbanístico). "Plano urbanístico" corrigido manualmente. Maria Joaquina corrigido (initial lowercase)
- [x] **1.1b** Títulos EN: SKIP (0 title_en)
- [x] **1.1c** Revisão LLM títulos EN/ES: SKIP (0 title_en)
- [x] **1.2a** Refs limpeza base: 4 artigos, 6 backfills. 937 refs OK
- [x] **1.2b** Refs sweep: 25 artigos (22 joins, 7 endnotes, 6 splits, 1 lixo, 1 page break, 1 não-ref). 937→913 refs
- [x] **1.2b+** Re-backfills: 0 necessários
- [x] **1.2c** Refs revisão LLM: 10 issues — 006 split 1→3, 009 abstract_en expandido, 011 refs merge+backfill (17→14), 027 split 1→3, 042 abstract expandido (236→1202), 048 URL limpa, 065 abstract expandido (289→1305)
- [x] **1.3** Keywords: 0 alterações
- [x] **1.5** Loop validação: 3 issues genuínos (A02 art 007 kw_en sem abs_en, A19 011/055 falsos positivos)
- [x] **1.6** Cobertura OK. abs 97%, abs_en 95%, kw 97%, kw_en 97%, refs 92%, title_en 0%. Seminário: 7º Docomomo NNE, Manaus, 2018, ISBN 978-85-526-0057-2
- [x] **1.7** Autores: 10 name splits corrigidos + 8 autores adicionados em 6 artigos. Paulo Costa Sampaio/Sampaio Neto corrigido para Paulo Costa/Sampaio Neto
- [x] **1.8** Dedup: 0 merges (nenhum duplicado detectado)
- [x] **1.9** ORCID: +6 novos (4 auto + 2 manuais). Total: 94/127 (74%)
- [x] **1.10** Revisão LLM final: ~59 correções em 56 artigos (32 subtítulos adicionados, 8 títulos expandidos/corrigidos, 8 keywords corrigidas, 1 abstract_en com ES trocado, 3 abstracts expandidos, vários typos)

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação + HTML + commits

## Revisão humana

- [ ] Pendente

## Fase 3 — Aprendizado (após revisão humana)

- [ ] **3.1** Diagnóstico unificado (correções automáticas + humanas → causa raiz)
- [ ] **3.2** Atualizar dict.db (remover genéricos, adicionar nomes próprios)
- [ ] **3.3** Atualizar scripts (se >=3 artigos com mesmo erro não coberto)
- [ ] **3.4** Atualizar pipeline (se gaps na ordem de execução)
- [ ] **3.5** Verificar: dry-run sem regressão
- [ ] **3.6** Registrar aprendizado (JSON + MEMORY.md)
- [ ] **3.7** Revisão de engenharia (autoavaliação + lints)
- [ ] **3.8** Checklist de conclusão
- [ ] **3.9** Fechar: dump + commit + CLAUDE.md
