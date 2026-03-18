# Revisão — 3 artigos novos (sdbr01-001, sdbr02-001, sdbr02-002)

## Diagnóstico

Artigos introdutórios/editoriais do livro que compilou os anais dos 1º e 2º Seminários Docomomo Brasil.

### Padrão de metadados (contexto do seminário)

| Campo | sdbr01 (7 arts) | sdbr02 (24 arts) | Ação |
|-------|-----------------|------------------|------|
| abstract | 0% (AUSENTE) | 67% (INTERMEDIÁRIO) | não buscar — textos editoriais sem resumo |
| abstract_en | 0% | 0% | não buscar |
| keywords | 0% | 0% | não buscar |
| keywords_en | 0% | 0% | não buscar |
| references | 71% (PRESENTE) | 79% (PRESENTE) | extrair do PDF quando houver |

### Estado final dos artigos

| Artigo | Título | Abstract | Keywords | Refs | Afiliação | ORCID |
|--------|--------|----------|----------|------|-----------|-------|
| sdbr01-001 | ✅ | ⬜ genuinamente ausente | ⬜ ausente | ✅ 2 refs extraídas | ✅ UFBA×2 | ✅ Espinoza |
| sdbr02-001 | ✅ corrigido | ⬜ genuinamente ausente | ⬜ ausente | ⬜ sem seção refs | ✅ UFBA×2+UFPI | ✅ Espinoza, Thiscianne |
| sdbr02-002 | ✅ | ⬜ genuinamente ausente | ⬜ ausente | ⬜ sem seção refs | ✅ UFBA×2 | — |

## Execução

### Fase 0.0 — Checkpoint
- ✅ dump_anais_db.py

### Fase 0.1 — Padrão de metadados
- ✅ Padrão levantado

### Fase 0.2 — Artigos fora do padrão
- ✅ Identificados

### Fase 0.3 — Reinspecionar PDFs
- ✅ Texto completo extraído via pdfplumber
- sdbr01-001: 6 páginas, 2 refs na p.6, 3 notas
- sdbr02-001: 9 páginas (inc. capa), sem refs, notas de imagens
- sdbr02-002: 7 páginas, sem refs, 2 notas de rodapé

### Fase 0.4 — Preencher lacunas
- ✅ Referências sdbr01-001: 2 refs inseridas
- ✅ Afiliações: 7 pares autor-artigo preenchidos (UFBA×6, UFPI×1)
- ✅ Título sdbr02-001: "Apresentação: O 2º Seminário Docomomo_Brasil", subtitle "proposta, realização, memória"
- ✅ Dedup autor: Caio Anderson da Silva Almeida (3334) → Caio Anderson da Silva de Almeida (1090)
- ✅ ORCID: Thiscianne Pessoa 0000-0002-1459-2460

### Fase 0.5 — Verificar abstracts
- ✅ N/A (nenhum abstract)

### Fase 0.6 — Metadados EN
- ✅ N/A (sem título/abstract EN)

### Fase 1.1a — Títulos PT
- ✅ normalizar_maiusculas.py — sem alterações necessárias

### Fase 1.2–1.4 — Refs, keywords
- ✅ Refs sdbr01-001 já limpas (2 refs curtas, ABNT)
- ✅ Keywords N/A (padrão ausente)

### Fase 1.5 — validate_metadata.py
- ✅ Zero issues para os 3 artigos

### Fase 1.6 — Auditoria final
- ✅ Autores verificados, afiliações preenchidas, ORCIDs buscados
- Sem ORCID confirmado: Caio Almeida, Rômulo Marques, Gabriela Otremba

## Conclusão

3 artigos revisados. Prontos para upload ao Zenodo (aguardando autorização).
