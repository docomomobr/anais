# sdsul01 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-20 | Artigos: 48
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/48 | % |
|-------|-------|---|
| abstract | 48 | 100% |
| abstract_en | 1 | 2% |
| keywords | 1 | 2% |
| keywords_en | 1 | 2% |
| references | 44 | 92% |
| title_en | 0 | 0% |
| sections | 6 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [x] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit
- [x] **0.1** Levantar padrão de metadados (query cobertura → classificar campos)
- [x] **0.2** Listar artigos fora do padrão (campos esperados mas ausentes)
- [x] **0.3** Reinspecionar PDFs dos artigos fora do padrão (hierarquia: docx → plumber → pdftotext)
- [x] **0.3b** Extrair fontes plumber (já existiam para 48/48)
- [x] **0.4** Preencher lacunas no banco (3 refs→047, 4 abstracts limpos de credenciais: 009/013/019/048)
- [x] **0.5** Verificar abstracts + auto-fix (36 issues, 21 A19 esperados — sem RESUMO nos PDFs)
- [skip] **0.6** Extrair metadados EN `[SKIP: abstract_en < 30%]`

## Fase 1 — Revisão automática

- [x] **1.1a** Títulos PT: 20 correções de capitalização (nomes próprios, instituições, siglas)
- [skip] **1.1b** Títulos EN/ES `[SKIP: title_en < 30%]`
- [skip] **1.1c** Revisão LLM títulos EN/ES `[SKIP: title_en < 30%]`
- [x] **1.2a** Refs limpeza base (669 refs, 0 problemas)
- [x] **1.2b** Refs sweep (23 arts, 26 joins, 8 splits, 22 endnotes, 13 não-refs)
- [x] **1.2b+** Re-backfills (2 backfills)
- [x] **1.2c** Refs revisão LLM (003 split, 013 backfill, 027 img credits, 048 rebuilt)
- [x] **1.3** Keywords (só 1/48 tem keywords — sem limpeza necessária)
- [x] **1.5** Loop validação (22 restantes: 21 A19 esperados, 1 A14 falso positivo)
- [x] **1.6a** Cobertura final: abs 4% (2/48 genuínos), refs 94% (45/48), kw/EN ~2%
- [x] **1.6b** Metadados do seminário OK (ISBN 85-60188-00-2, PROPAR-UFRGS, editors 3)
- [x] **1.6c** Seções/sessões: 6 seções já atribuídas, 48/48 artigos mapeados
- [x] **1.6d** Autores: 60 autores, 41 com ORCID (68%), 0 dedup, 19 sem ORCID (todos já checados)

## Fase 2 — HTML de revisão + checkpoint

- [x] **2.0** Validação final (0 issues) + HTML + dump

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [x] **3.1** Diagnóstico: 6 refs splits (formato livre), 1 notas≠refs, 1 legendas, 2 títulos lowercase
- [x] **3.2** dict.db: sem alterações necessárias
- [x] **3.3** Scripts: sem alterações (erros de refs são formato-livre, não automatizável)
- [x] **3.4** Pipeline: documentar check "RESUMO label" na Fase 0 (sdsul01 = 96% sem abstract)
- [x] **3.5** Validação: 0 issues. Normalizador: não re-rodar (reverteria correções manuais)
- [x] **3.6** Aprendizado registrado
- [x] **3.7** Revisão de engenharia: OK
- [x] **3.8** Checklist de conclusão: 10/10 itens humanos ✅
- [x] **3.9** Fechar: dump + commit
