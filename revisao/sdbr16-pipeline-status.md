# sdbr16 — Status do pipeline de tratamento

Data: 2026-03-31

## Extrato

| Tipo | Qtd |
|------|-----|
| Artigos | 270 |
| Resumos (sem texto completo) | 15 |
| Mesas (textos de coordenadores) | 35 |
| **Total** | **320** |
| Sessões | 39 |
| Autores únicos | 446 |

Artigos sem abstract: 4 | sem keywords: 21 | sem referências: 5

## Concluído

- [x] Fase 1 — Aquisição: 272 docx, 271 PDFs em `nacionais/sdbr16/`
- [x] Fase 2.1 — Extração de metadados (títulos, autores, abstracts, keywords, referências) via docx
- [x] Fase 2.1b — Extração de referências (265/270, 5 genuinamente sem refs)
- [x] Fase 2.3 — Sessões: 270/270 artigos atribuídos (39 sessões, fonte: programação definitiva + caderno de resumos)
- [x] Mesas: 35 textos de coordenadores extraídos do caderno de resumos
- [x] Resumos: 15 artigos da programação sem texto completo registrados no DB
- [x] Sessões: duplicatas unificadas, typos corrigidos, capitalização normalizada + revisão LLM
- [x] Seminário criado no DB (ISBN 978-65-993024-6-6)
- [x] Verificação cruzada: programação (285) = DB artigos+resumos (285), arquivos (271) = DB artigos (270) + 1 resumo com docx

## Concluído (sessão 2 — 2026-03-31)

- [x] Fase 4.2 — Normalização de travessões: 6 títulos corrigidos (` - ` → ` — `)
- [x] Fase 4.3 — Capitalização de títulos: `normalizar_maiusculas.py` (3 artigos) + revisão LLM (70+ correções: nomes próprios, siglas, instituições, topônimos, subtítulos)
- [x] Fase 4.4a — `clean_references.py --slug sdbr16`: 0 mudanças (refs já limpas)
- [x] Fase 4.4b — `check_references.py --slug sdbr16 --summary`: 7/2130 (0.3%)
- [x] Fase 5-7 — `validate_metadata.py --slug sdbr16`: 85 issues (0 fix, todos report)
- [x] Revisão HTML: `revisao/revisao-sdbr16.html` (320 artigos, 39 seções)
- [x] Dump do banco (anais.sql)

- [x] Fase 2.1d — Metadados EN: N/A (organização não exigiu abstract/title em inglês)
- [x] Atualizar devlog.md

## Pendente (pós-pipeline)

- [ ] PDFs individuais (artigos em docx apenas)
- [ ] Zenodo upload (depende dos PDFs)
- [ ] NÃO publicar no site até comando explícito do usuário

## Notas

- Fonte primária: docx (NÃO rodar pdfplumber — fontes são editáveis)
- sdbr16 NÃO publicar no site até comando explícito do usuário
- Artigo 019 tem PDF mas não docx (veio só como PDF no segundo lote)
- Artigo 084 (Binato de Castro): título no docx difere totalmente da programação (autor mudou título)
- Artigo 037: tem docx mas é `resumo` (não artigo completo)
