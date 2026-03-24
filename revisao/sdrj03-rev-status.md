# sdrj03 — Status da revisão

Data de início: 2026-03-23
Seminário: 3º Encontro Docomomo Rio, Rio de Janeiro, 2014
Artigos: 4 | Autores: 18 | Seções: 2
ISBN: 978-85-88341-63-0

## Cobertura inicial

| Campo | N/4 | % |
|-------|-----|---|
| abstract | 4 | 100% |
| abstract_en | 0 | 0% |
| keywords | 0 | 0% |
| keywords_en | 0 | 0% |
| references | 0 | 0% |
| title_en | 0 | 0% |

## Log progressivo

### Fase 0 — Diagnóstico
- [x] §0.0 Checkpoint + commit (12e51d2)
- [x] §0.1 4 artigos: 2 textos editoriais (001 Apresentação, 002 Milton Roberto) + 2 pôsteres (003, 004)
- [x] §0.2 Pôsteres 003/004 originalmente JPGs sem PDF. Convertidos: JPG → PDF (img2pdf) → OCR (ocrmypdf) → plumber.
- [x] §0.3 Fonte: CD-ROM com PDFs (textos 1p), JPGs (pôsteres), MP4 (mesa redonda, momotur). Sem doc/docx.
- [x] §0.3b Plumber: 4 PDFs extraídos (7+7+163+38 blocos). Profile adaptado (4 PDFs, fontes grandes de poster).
- [x] §0.4 Seções: 2 (Geral hide_title=1, Pôsteres). Correto.
- [x] §0.5 Abstracts: 4/4 já no banco (editoriais manuais). Nenhuma lacuna preenchível.
- [x] §0.6 EN: fontes_plumber sem seção EN identificável. 0 extraídos.
- [skip] §0.7 ES: 0 artigos locale=es
- [x] §0.8 Validate: 0 problemas

### Fase 1 — Revisão automática
- [x] §1.1a Títulos: normalização 0 alterações. Todos corretos.
- [skip] §1.1b/c EN/ES: title_en = 0
- [x] §1.2a Refs: 0 refs no banco (genuíno — textos editoriais + pôsteres sem bibliografia)
- [x] §1.2b Sweep: n/a (0 refs)
- [x] §1.3 Keywords: 0 (genuíno)
- [x] §1.5 Loop: 0 issues
- [x] §1.6 Cobertura: abs 100%, demais 0% (genuíno). Seminário: ISBN, editores, descrição OK.
- [x] §1.7 Autores: 18, verificados vs YAML original
- [x] §1.8 Dedup: 0 merges
- [x] §1.9 ORCID: 9 buscados. 2 aplicados (Viviane Matos OA, Ana Slade UFRJ). 11/18 (61%).
- [x] §1.10 Revisão LLM:
  - [x] sdrj03-001: OK (Apresentação, texto editorial 1p, sem refs/kw)
  - [x] sdrj03-002: OK (Milton Roberto, texto biográfico 1p, sem refs/kw)
  - [x] sdrj03-003: OK (pôster OCR'd, texto fragmentado multi-coluna, sem refs extraíveis)
  - [x] sdrj03-004: OK (pôster OCR'd, desenhos técnicos, sem refs extraíveis)

### Fase 2
- [x] §2.0 Validate 0 issues + HTML (4 artigos, 2 seções) + dump + commit
