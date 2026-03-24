# Auditoria de engenharia — Pendências

Data: 2026-03-23
Contexto: Auditoria completa dos pipelines de tratamento e revisão + 11 scripts core.
Bugs corrigidos nesta sessão: 13 (5 na sessão sdrj02 + 8 na auditoria final).
Commit da auditoria: `ea29f91`

---

## Código — bugs pendentes

### 1. fetch_orcid.py:64 — API key hardcoded em repo público

```python
OPENALEX_API_KEY = os.environ.get('OPENALEX_API_KEY', '1Vt5PmYGDGSkDFiDTCrpLI')
```

**Problema:** Chave de API como valor default, visível no código-fonte de um repo público (GitHub docomomobr/anais).
**Fix:** Remover o default. OpenAlex aceita acesso sem chave via Polite Pool (basta email no User-Agent).
```python
OPENALEX_API_KEY = os.environ.get('OPENALEX_API_KEY', '')
```

### 2. validate_metadata.py — f-string SQL com coluna dinâmica (8 ocorrências)

Linhas: 1216, 1224, 1241, 1266, 1274, 1310, 1315, 1368

```python
cur.execute(f"UPDATE articles SET {field} = ? WHERE id = ?", ...)
# Pior caso (l.1310):
cur.execute(f"UPDATE articles SET {dst} = {src}, {src} = NULL WHERE id = ?", ...)
```

**Problema:** Nomes de coluna interpolados via f-string. Valores vêm de dicts hardcoded (não de input externo), então não é SQL injection explorável. Mas o padrão é frágil — qualquer refatoração que passe um campo não-validado causa crash ou corrupção.
**Fix:** Adicionar constante `_VALID_COLS` e `assert field in _VALID_COLS` antes de cada execução.

### 3. gerar_revisao_html.py:35 — default slug hardcoded

```python
slug = sys.argv[1] if len(sys.argv) > 1 else 'sdpr02'
```

**Problema:** Se chamado sem argumento, gera HTML do sdpr02 silenciosamente. Pode surpreender.
**Fix:** Usar argparse. Já existe lógica para `--articles` no mesmo arquivo (verificar e unificar).

### 4. gerar_revisao_html.py:633 — json.loads sem guard

```python
n = len(json.loads(art['references_']))
```

**Problema:** Se `references_` contém JSON malformado, crash. O `fmt_refs` na mesma função já fez parse com guard, mas o contagem duplica o parse.
**Fix:** Reusar o resultado do parse anterior, ou wrap em try/except.

### 5. normalizar_maiusculas.py:88 — conexão sem context manager

```python
conn = sqlite3.connect(DB_PATH)
# ... uso ...
# conn.close() no final, mas sem try/finally
```

**Problema:** Exceção entre connect e close vaza a conexão.
**Fix:** `with sqlite3.connect(DB_PATH) as conn:` ou try/finally.

### 6. extrair_fontes_plumber.py:59,188,255 — PDF handles sem context manager

```python
pdf = pdfplumber.open(pdf_path)
# ... uso ...
pdf.close()
```

**Problema:** Exceção entre open e close vaza file handle.
**Fix:** `with pdfplumber.open(pdf_path) as pdf:`.

### 7. dedup_authors.py:1398 — O(n²) na Fase 8 (coautores em comum)

```python
for i in range(len(authors)):
    for j in range(i + 1, len(authors)):
```

**Problema:** ~3500 autores = ~6M comparações, cada uma com queries ao banco.
**Fix:** Pré-filtrar por coautores em comum antes do loop aninhado (construir índice invertido artigo→autores).

---

## Documentação — inconsistências pendentes

### 8. pipeline_tratamento Fase 5 vs pipeline_revisao_humana — workflows incompatíveis

**pipeline_tratamento.md Fase 5** define revisão humana via 3 levas de .txt editáveis com neovim (fichas, seções, títulos/autores), com diff contra .orig.txt.

**pipeline_revisao_humana.md** define revisão humana via HTML no navegador + anotações em rev.md.

São workflows incompatíveis. A Fase 5 do tratamento parece ser o workflow original (usado nos sdsp/sdrj iniciais) que foi substituído pelo HTML.

**Fix proposto:** Marcar pipeline_tratamento Fase 5 como legacy/deprecated e cross-referenciar pipeline_revisao_humana.md.

### 9. pipeline_tratamento Fase 7.3-7.3f duplica pipeline_revisao Fases 0-1

As subseções 7.3a-7.3f do tratamento (refs cleanup, sweep, keywords, validation loop, LLM review) replicam quase todo o conteúdo das Fases 0-1 do pipeline de revisão. Manutenção duplicada — alteração num documento não propaga para o outro.

**Fix proposto:** Substituir 7.3-7.3f por cross-reference: "Executar o [pipeline de revisão](pipeline_revisao.md) Fases 0-2 neste ponto."

### 10. Numeração de fases colide entre documentos

| Conceito | Tratamento | Revisão | Rev. Humana |
|----------|-----------|---------|-------------|
| Extração/ingestão | Fases 1-4 | — | — |
| Rev. humana (levas .txt) | Fase 5 | — | — |
| PDFs | Fase 6 | — | — |
| Banco + enriquecimento | Fase 7 | — | — |
| Diagnóstico + preenchimento | — | Fase 0 | — |
| Revisão automática | — | Fase 1 | — |
| HTML de revisão | — | Fase 2 | — |
| Rev. humana (HTML) | — | — | Fases 3-4 |
| Fechar revisão | — | — | Fase 5 |
| Aprendizado pós-revisão | Fase 8 | Fase 3 | — |

**Fix proposto:** Adicionar tabela de correspondência no topo de cada documento.

### 11. pipeline_revisao §1.7-1.9 — no checklist mas sem seções no corpo

O checklist rápido (l.92-94) define §1.7 (Autores), §1.8 (Dedup), §1.9 (ORCID) como etapas separadas, mas no corpo do documento o conteúdo está todo dentro de §1.6d. O GATE de §1.10 referencia "1.9 done" mas §1.9 não tem seção formal.

**Fix proposto:** Criar seções ### 1.7, ### 1.8, ### 1.9 no corpo, extraindo o conteúdo de 1.6d.

### 12. Scripts não documentados em nenhum pipeline

| Script | Provável função | Ação |
|--------|----------------|------|
| `extrair_titulo_es.py` | Extrai títulos ES dos PDFs | Documentar em §1.1b (títulos ES) |
| `check_quality.py` | ? | Verificar se é legacy |
| `fix_capitalization.py` | ? | Provavelmente superseded por normalizar_maiusculas.py |
| `fix_references.py` | ? | Provavelmente superseded por fix_validation_issues.py |
| `split_concat_references.py` | ? | Provavelmente superseded por clean_references.py |
| `_post_pipeline.py` | ? | Verificar se é helper interno |
| `validar_abstracts.py` | Validação de abstracts | Superseded por validate_metadata.py? Documentar ou remover |

---

## Resumo

| Categoria | Total | Corrigidos | Pendentes |
|-----------|-------|-----------|-----------|
| CRITICAL | 2 | 2 | 0 |
| HIGH | 4 | 4 | 0 |
| MEDIUM (código) | 6 | 6 | 0 |
| MEDIUM (docs) | 4 | 4 | 0 |
| LOW (código) | 4 | 4 | 0 |
| LOW (docs) | 1 | 1 | 0 |

**Todos os 21 itens resolvidos.** Commits: `ea29f91` (8 bugs), `3209fd1` (12 pendências).
