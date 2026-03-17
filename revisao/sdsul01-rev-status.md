# sdsul01 — Rev-status

## Fase 0 — Diagnóstico (2026-03-17)

### 0.0 Checkpoint ✅
- Commit `837cf59` (títulos e refs já normalizados de sessão anterior)

### 0.1 Padrão de metadados ✅

48 artigos, 42 pt-BR + 6 es

| Campo | Presença | Classificação | Ação |
|-------|----------|---------------|------|
| abstract | 48/48 (100%) | PRESENTE | nenhuma |
| abstract_en | 1/48 (2%) | AUSENTE | não buscar |
| abstract_es | 0/48 | AUSENTE | não buscar |
| keywords | 1/48 (2%) | AUSENTE | verificado nos PDFs: 1/48 tem |
| keywords_en | 1/48 (2%) | AUSENTE | não buscar |
| references | 43→44/48 (92%) | PRESENTE | 4 genuinamente sem refs |
| pages | 0/48 | AUSENTE | não buscar |
| title_en | 0/48 | AUSENTE | não buscar |

**Norma de citação**: ABNT (71% das refs em amostra de 20 artigos)

### 0.2 Artigos fora do padrão (refs) ✅

| Artigo | Status | Observação |
|--------|--------|------------|
| sdsul01-001 | ⬜ sem refs | 1 página, texto introdutório |
| sdsul01-009 | ⬜ sem refs | artigo descritivo sem bibliografia |
| sdsul01-021 | ⬜ sem refs | texto sem bibliografia formal |
| sdsul01-039 | ✅ 📚 extraído | 59 refs (pdfplumber, fragmentadas — precisa join na 1.2c) |
| sdsul01-047 | ⬜ 📄 footnotes | notas de rodapé com citações, sem seção formal |

Refs extraídas salvas em `revisao/sdsul01-refs-extraidas.json`

### 0.3 Reinspecionar PDFs ✅
- PDFs dos 5 artigos verificados manualmente
- sdsul01-039 tinha refs, extraídas

### 0.3b Fontes estruturadas ✅
- pdfplumber extraído: 48/48 artigos em `regionais/sul/sdsul01/fontes_plumber/`
- Sem doc/docx originais

### 0.4 Preencher lacunas ✅
- sdsul01-039: 59 refs inseridas (fragmentadas, a corrigir em 1.2c)

### 0.5 Verificar abstracts ✅
- 22/48 abstracts possivelmente truncados (cortam no fim da página 1)
- Confirmado: extração cortou na quebra de página. Abstract continua na p.2
- Sem problema de idioma cruzado
- Correção: re-extração multi-página na Fase 1

### 0.6 Extrair metadados EN ✅
- Padrão AUSENTE (0/48 title_en, 1/48 abstract_en)
- Nada a fazer

---

## Fase 1 — Revisão automática

### 1.1a Títulos e subtítulos PT ✅ (sessão anterior)
- normalizar_maiusculas.py: 19/48 alterados
- Falsos positivos corrigidos: "La" (artigo ES), "Luz" (genérico), "Reitoria" (genérico)

### 1.1b Normalizar títulos EN/ES ✅
- Sem title_en. 6 artigos em ES — títulos já verificados na normalização

### 1.1c Revisão LLM de títulos ⏳
- Pendente: verificar títulos PT contra PDFs (LLM)

### 1.2a clean_references ✅ (sessão anterior)
- 2 autores backfilled, 1 URL juntada

### 1.2b sweep_refs ⏳
- Pendente

### 1.2c Revisão LLM de refs ⏳
- Pendente
- Nota: refs do sdsul01-039 estão fragmentadas (quebra de página no pdfplumber)
- Nota: 22 abstracts truncados precisam re-extração

### 1.3 Keywords ✅
- 1/48 tem keywords (padrão AUSENTE). Nada a fazer.

### 1.5 validate --fix ✅ (sessão anterior)
- 2 auto-fix (A17 refs duplicadas)
- 36 issues reportados (A10, A11, A12, A19)

### 1.6 Auditoria final ⏳

---

## Estado atual

Fase 0 completa mas Fase 1 precisa ser **refeita na ordem correta**. As etapas 1.1a, 1.2a e 1.5 foram executadas fora de ordem na sessão anterior. Na próxima sessão:

1. ⏳ 0.5 — Re-rodar validate --fix (agora com fontes_plumber disponível)
2. ⏳ 1.1c — Revisão LLM de títulos PT vs PDF
3. ⏳ 1.2b — sweep_refs (agora com fontes_plumber)
4. ⏳ 1.2c — Revisão LLM de refs (join fragmentadas, re-extração abstracts truncados)
5. ⏳ 1.5 — Re-rodar validate após correções
6. ⏳ 1.6 — Auditoria final
7. ⏳ Fase 2 — HTML de revisão

**NOTA**: Seguir o pipeline_revisao.md **literalmente**, item por item, sem pular.
