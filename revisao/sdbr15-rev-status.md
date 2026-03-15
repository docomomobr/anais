# Revisão — sdbr15 (101 artigos)

Data: 2026-03-15

## Diagnóstico — sdbr15 (101 artigos)

### Padrão de metadados
| Campo | Presença | Classificação |
|-------|----------|---------------|
| abstract | 99/101 (98%) | PRESENTE |
| abstract_en | 99/101 (98%) | PRESENTE |
| abstract_es | 98/101 (97%) | PRESENTE |
| keywords | 100/101 (99%) | PRESENTE |
| keywords_en | 99/101 (98%) | PRESENTE |
| keywords_es | 97/101 (96%) | PRESENTE |
| references | 99/101 (98%) | PRESENTE |
| title_en | 96/101 (95%) | PRESENTE |

- **Locale**: 100 pt-BR + 1 es
- **Norma**: ABNT (68%)
- **Fontes**: PDFs (101), fontes/ (101). Sem fontes_plumber/.
- **Even3**: dados estruturados (3 idiomas, title_en, DOI)

### Artigos fora do padrão
- abstract (2): sdbr15-089, sdbr15-090
- keywords (1): sdbr15-089
- references (2): sdbr15-076, sdbr15-090
- title_en (5): a verificar

---

## Progresso

- ✅ 0.0 Checkpoint inicial (estado limpo)
- ✅ 0.1 Padrão levantado
- ✅ 0.2 Artigos fora do padrão identificados
- ✅ 0.3 Reinspecionar PDFs:
  - 089: Mesa Especial (relatoria) — sem abstract/keywords genuíno ⬜
  - 090: Resenhas de livros — sem abstract/refs genuíno ⬜
  - 076: refs extraídas do PDF
- ⏳ 0.3b pdfplumber (rodando em background)
- ✅ 0.4 Lacunas: 076 refs extraídas (6)
- ✅ 0.5 validate --fix: 1 overflow (A20), 1 dupe (A17), 1 body text (A22). 9 issues restantes.
- ✅ 1.1a normalizar_maiusculas.py — 11 artigos
- ✅ 1.1a Revisão LLM títulos PT — 48 correções
- ✅ 1.1b Títulos EN — 85 normalizados + 11 garbled/typos + 18 partículas/acentos/acronyms
- ✅ 1.1b Títulos ES — 12 normalizados RAE + nomes próprios corrigidos
- ✅ 1.1c Revisão LLM títulos EN + ES concluída (99 title_es verificados, 9 corrigidos RAE)
- ✅ 1.2a clean_references — 6 backfills
- ✅ 1.2b sweep_refs — 56 artigos: 27 lixo, 30 fragmentos, 11 endnotes, 7 splits, 5 não-refs, 1 dedup
- ✅ 1.2b+ re-rodar clean_references — 0 backfills adicionais
- ⏳ 1.2c Revisão LLM refs (pendente — agente)
- ✅ 1.3 Keywords — 12 artigos, 38 splits, 3 garbage, 1 dedup
- ✅ 1.5 Loop validate — convergiu, 9 issues (4 A10, 2 A11, 1 A03, 1 A09, 1 A19)
- ✅ 1.6b Metadados: publisher=IAU-USP; FAU-USP, location=São Carlos SP, date=2023-10-17, DOI=10.29327/1344945
- ⏳ 1.6c Seções: 4 eixos criados, mapeamento pendente (PDFs sem eixo no header, Even3 JS-only)
- ⏳ 1.6d Autores
