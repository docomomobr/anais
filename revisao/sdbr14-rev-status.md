# Revisão automática — sdbr14 (122 artigos)

Data: 2026-03-15

## Diagnóstico — sdbr14 (122 artigos)

### Padrão de metadados
| Campo | Presença | Classificação |
|-------|----------|---------------|
| abstract | 122/122 (100%) | PRESENTE |
| abstract_en | 5/122 (4%) | AUSENTE |
| keywords | 120/122 (98%) | PRESENTE |
| keywords_en | 4/122 (3%) | AUSENTE |
| references | 119/122 (97%) | PRESENTE |
| title_en | 0/122 (0%) | AUSENTE |

- **Locale**: 122 pt-BR (100%)
- **Norma**: ABNT (82%)
- **Fontes**: PDFs (122), fontes_plumber/ (122)

### Dados genuinamente ausentes
- abstract: ~~1 (098)~~ → extraído do PDF (abstract com labels IMRAD inline)
- keywords: 017, 087 — genuinamente ausentes no PDF
- references: 020, 093, 122 — footnotes only, sem seção de refs. 090 → 8 refs extraídas

---

## Progresso

### Fase 0
- ✅ 0.0 Checkpoint (estado limpo, nada a commitar)
- ✅ 0.1 Padrão levantado
- ✅ 0.2 Artigos fora do padrão: 1 abstract, 2 keywords, 4 refs
- ✅ 0.3 PDFs inspecionados: 098 abstract extraído, 017/087 kw ausentes, 020/093/122 footnotes only, 090 refs extraídas
- ✅ 0.3b pdfplumber — 122/122
- ✅ 0.4 Lacunas preenchidas
- ✅ 0.5 validate --fix: 2 overflows (A20), 3 dupes (A17), 1 abstract_es lixo (A21), 1 EN separado (A23), 1 keywords colada (A25)

### Fase 1
- ✅ 1.1a normalizar_maiusculas.py — 24 artigos
- 🔄 1.1a Revisão LLM títulos PT (agente em background)
- ✅ 1.2a clean_references — 3 splits, 12 backfills
- ✅ 1.2b sweep_refs — 61 artigos: 21 lixo, 43 fragmentos, 24 endnotes, 11 splits, 4 não-refs, 7 notas cortadas, 1 header
- ✅ 1.2b+ re-rodar clean_references — 2 backfills adicionais
- ⏳ 1.2c Revisão LLM refs (2 A10 + 4 A11 restantes)
- ✅ 1.3 Keywords — 2 splits
- ✅ 1.5 Loop validate — convergiu, 8 issues restantes (2 A10, 4 A11, 1 A14, 1 A19)
- ✅ 1.6b Metadados: publisher=UFPA FAU PPGAU, location=Belém, date=2021-10-27, ISBN=978-65-00-40027-4, editors=Celma Chaves; Cybelle Salvador Miranda
- ✅ 1.6c Seções: 4 áreas, 122/122 mapeados
  - Área 1 — A Arquitetura Moderna, Cultura e Natureza: 25
  - Área 2 — Documentar, Preservar, Conservar: 54
  - Área 3 — Novas Cartografias e Cronologias: 34
  - Área 4 — Espaços Modernos e os Novos Desafios: 9
  - Artigos da Comissão Científica: publicados na Revista Docomomo (não nos anais)
  - Vídeo-Posters: links de vídeo (não são artigos, não estão no banco)

### Fase 2
- ✅ HTML: revisao/revisao-sdbr14.html

### Issues restantes (8)
- A10 (2): backfills com autor não-detectável
- A11 (4): refs legislativas longas (legítimas)
- A14 (1): abstract possivelmente contaminado
- A19 (1): abstract possivelmente truncado
