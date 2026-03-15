# Revisão — sdbr14 (122 artigos)

Data: 2026-03-15

## Cobertura final
| Campo | Inicial | Final |
|-------|---------|-------|
| abstract | 121 (99%) | **122 (100%)** |
| abstract_en | 5 (4%) | 4 (3%) — AUSENTE |
| keywords | 120 (98%) | 121 (99%) |
| keywords_en | 4 (3%) | 4 (3%) — AUSENTE |
| references | 118 (96%) | 120 (98%) |
| seções | 0 (0%) | **122 (100%)** |
| autores | 122 (100%) | 122 (100%) — 1 fix hispânico |

## Validação final: 5 issues genuínos
- A11 (4): refs legislativas/multi-autor longas (legítimas: 048×2, 091, 099)
- A19 (1): sdbr14-042 abstract sem ponto (autor não colocou — ponto adicionado)

---

## Fase 0 — Diagnóstico e preenchimento
- ✅ 0.0 Checkpoint (estado limpo)
- ✅ 0.1 Padrão: abstract_en/kw_en/title_en AUSENTE (<30%)
- ✅ 0.2 Faltantes: 1 abstract (098), 2 kw (017,087), 4 refs (020,090,093,122)
- ✅ 0.3 PDFs inspecionados:
  - 098: abstract extraído (labels IMRAD inline confundiram regex)
  - 017, 087: keywords genuinamente ausentes
  - 020, 093: footnotes only, sem seção de refs
  - 090: 8 refs extraídas do PDF
  - 122: classificado erroneamente como "footnotes only" → tinha refs na p.15 (corrigido na revisão humana)
- ✅ 0.3b pdfplumber — 122/122
- ✅ 0.4 Lacunas preenchidas
- ✅ 0.5 validate --fix: 2 overflows (A20), 3 dupes (A17), 1 abstract_es lixo (A21), 1 EN separado (A23), 1 keywords colada (A25)

## Fase 1 — Revisão automática
- ✅ 1.1a normalizar_maiusculas.py — 24 artigos + revisão LLM 65 correções
- ✅ 1.2a clean_references — 3 splits, 12 backfills
- ✅ 1.2b sweep_refs — 61 artigos: 21 lixo, 43 fragmentos, 24 endnotes, 11 splits, 4 não-refs, 7 notas, 1 header
- ✅ 1.2b+ re-rodar clean_references — 2 backfills adicionais
- ✅ 1.2c Backfills manuais: 14 resolvidos. A11: 4 refs legislativas legítimas (sem ação). A14: email em abstract 004 (limpo). A19: ponto adicionado em 042.
- ✅ 1.3 Keywords — 2 splits
- ✅ 1.5 Loop validate — convergiu em 5 issues genuínos
- ✅ 1.6a Cobertura verificada
- ✅ 1.6b Metadados seminário: publisher=Universidade Federal do Pará, FAU, PPGAU. location=Belém. date=2021-10-27. ISBN=978-65-00-40027-4. editors=Celma Chaves, Cybelle Salvador Miranda. Description conforme ficha CIP do PDF.
- ✅ 1.6c Seções: 4 áreas temáticas, 122/122 mapeados. Títulos em sentence case.
  - Área 1 — A Arquitetura Moderna, cultura e natureza: 25
  - Área 2 — Documentar. Preservar. Conservar. O Patrimônio Moderno e seus usos e reusos: 54
  - Área 3 — Novas cartografias e cronologias da arquitetura e do urbanismo modernos no Brasil: 34
  - Área 4 — Espaços modernos e os novos desafios técnicos, ecológicos e sociais do legado da Arquitetura Moderna: 9
  - Artigos da Comissão Científica: publicados na Revista Docomomo Brasil (pendência pós-produção)
  - Vídeo-Posters: 11 MP4 baixados em videos/ (327MB). Pendência pós-produção.
- ✅ 1.6d Autores: 122/122 verificados. 1 fix: Jorge Herrera De La Torre (sobrenome hispânico). 4 casos mantidos (publicam com nome alternativo consistente).

## Fase 2 — HTML de revisão ✅
- revisao/revisao-sdbr14.html

## Revisão humana — 7 itens ✅
| # | Artigo | Campo | Problema | Causa raiz |
|---|--------|-------|----------|-----------|
| 1 | 087 | abstract | overflow (4412c) | Extração sem delimitação, <5000c (A20 não pegou) |
| 2 | 087 | keywords | faltantes | Extração falhou, existiam no PDF |
| 3 | 001 | abstract_en | keywords PT no campo EN | A27 não pegava keywords (só abstract narrativo) |
| 4 | 072 | references | split indevido na última ref | sweep passada 1 não juntou fragmento ambíguo |
| 5 | 004 | abstract | truncado + email | A14 detectou mas não limpou automaticamente |
| 6 | 022 | references | 2 backfills agrupados | clean_refs não reconhece "_. Título" como boundary |
| 7 | 097 | subtitle | "Revista" maiúscula | LLM não corrigiu — caso pontual |
| * | 122 | references | 25 refs faltantes | Classificado como "footnotes only" na Fase 0 — errado |

## Fase 3 — Aprendizado ✅
- 3.1 Diagnóstico unificado (automático + humano): tabela acima
- 3.2 Dict: seed_authors rodado, sem adições
- 3.3 Scripts: A27 expandido (keywords PT no EN), IGNORECASE
- 3.4 Pipeline: 0.3 verificar TODAS as páginas para refs, 1.6b verificar contra ficha CIP, "Disponível originalmente em"
- 3.5 Verificação: dry-run sdbr14+sdbr13+sdbr12 sem regressão
- 3.6 Aprendizado: revisao/sdbr14-titulos-aprendizado.json
- 3.7 Engenharia: A27 IGNORECASE, autoavaliação obrigatória, checklist 3.8
- 3.8 Checklist: ✅ todas as etapas 3.1-3.7 verificadas

## Dados genuinamente ausentes
- abstract_en: AUSENTE (4%, <30%)
- keywords: 017, 087 — sem keywords no PDF
- keywords_en: AUSENTE (3%, <30%)
- references: 020, 093 — footnotes only (confirmado em TODAS as páginas)
- title_en: AUSENTE (0%)
