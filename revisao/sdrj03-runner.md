# sdrj03 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-23 | Artigos: 4
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/4 | % |
|-------|------|---|
| abstract | 4 | 100% |
| abstract_en | 0 | 0% |
| keywords | 0 | 0% |
| keywords_en | 0 | 0% |
| references | 0 | 0% |
| title_en | 0 | 0% |
| sections | 2 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint + commit
- [x] **0.1** abs 100%, abs_en/kw/refs/title_en 0%. 4 artigos: 2 editoriais + 2 pôsteres.
- [x] **0.2** Pôsteres 003/004 sem PDF → JPG convertido (img2pdf → ocrmypdf → plumber)
- [x] **0.3** Fonte: CD-ROM (PDFs 1p, JPGs pôsteres, MP4 mesa/momotur). Sem doc/docx.
- [x] **0.3b** Plumber: 4 PDFs (7+7+163+38 blocos). Pôsteres OCR'd.
- [x] **0.4** Seções: 2 (Geral hide_title=1, Pôsteres). Sem eixos.
- [x] **0.5** Lacunas: nenhuma preenchível. Abstracts no banco são editoriais manuais.
- [x] **0.6** EN: 0 extraídos (sem seção EN nos PDFs)
- [skip] **0.7** ES: 0 locale=es
- [x] **0.8** Validate: 0 problemas

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos: 0 alterações
- [skip] **1.1b/c** EN/ES [SKIP: title_en = 0]
- [x] **1.2a-c** Refs: 0 refs (genuíno — editoriais + pôsteres)
- [x] **1.3** Keywords: 0 (genuíno)
- [x] **1.5** Loop: 0 issues
- [x] **1.6** Cobertura: abs 100%, demais 0% (genuíno)
- [x] **1.7** Autores: 18 verificados
- [x] **1.8** Dedup: 0 merges
- [x] **1.9** ORCID: 2 novos (Viviane Matos, Ana Slade). 11/18 (61%)
- [x] **1.10** Revisão LLM: 4/4 OK (textos editoriais + pôsteres OCR'd, sem metadados extraíveis)

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação final (0 issues) + HTML (4 artigos) + dump + commit

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)
