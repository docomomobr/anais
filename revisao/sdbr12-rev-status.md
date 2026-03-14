## Registro de revisão — sdbr12 (82 artigos)

### Diagnóstico (Fase 0)
- ✅ 0.1 Padrão: 100% abstract, 100% kw, 96% refs, 100% abstract_en, 0% title_en
- ✅ 0.2 Faltantes: 3 refs (002, 059, 064)
- ✅ 0.3 Fontes: 91 doc/docx + plumber 82/82
- ✅ 0.4 Lacunas: 002 (10 refs docx), 059 (18 refs docx), 064 (footnotes, sem lista)
- ✅ 0.5 Abstracts: 005 título removido, 033/049/081 falsos positivos
- ✅ 0.6 title_en AUSENTE (0%) — N/A

### Revisão automática (Fase 1)
- ✅ 1.1a Títulos PT: 17 normalizados + revisão LLM (0 problemas)
- ✅ 1.1b/c Títulos EN/ES: 002 subtitle corrigido (us→US), sem title_es
- ✅ 1.2a clean_references: 1 split, 1 backfill
- ✅ 1.2b sweep_refs: 36 artigos (21 junk, 38 fragmentos, 5 splits, 16 não-refs, 2 dedup)
- ✅ 1.2c Revisão LLM: 82/82 artigos (refs + abstracts + keywords todos idiomas)
  - 006: 19 refs re-extraídas da imagem do PDF (concatenações separadas)
  - 014, 049, 081: abstract_en/keywords_en eram ES → movidos para _es
  - 082: keywords_en split
  - 023: 18 notas cortadas
  - 022: 4 backfills, 072: 9 backfills
- ✅ 1.3 Keywords: 9 artigos, 17 splits, 3 dedup
- ✅ 1.5 Validate: 0 issues
- ✅ 1.6a Cobertura: 100% title/abstract/keywords/locale/autores/seções
- ✅ 1.6b Metadados: publisher=EDUFU, location=Uberlândia
- ✅ 1.6c Seções: 4 eixos

### HTML de revisão (Fase 2)
- ✅ revisao/revisao-sdbr12.html

### Resultado final
- 0 issues validate_metadata.py
- Pronto para revisão humana
