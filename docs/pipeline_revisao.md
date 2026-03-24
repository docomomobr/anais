# Pipeline de Revisão Automática de Metadados

Pipeline para revisão automática dos metadados dos artigos no `anais.db`. Complementa o [pipeline de tratamento](pipeline_tratamento.md) (fases 1-8) e antecede o [pipeline de revisão humana](pipeline_revisao_humana.md) (Fases 3-5).

A revisão é necessária porque a extração automatizada dos PDFs produz erros sistemáticos: títulos com capitalização errada, resumos truncados, keywords faltantes, referências concatenadas ou ausentes. O pipeline automático corrige os problemas detectáveis por heurísticas; o que escapar vai para a revisão humana.

**IMPORTANTE:** Este pipeline roda **uma única vez** por seminário, **antes** da revisão humana. Após a revisão humana ter corrigido títulos, subtítulos e outros campos, **nunca** re-rodar este pipeline no mesmo seminário — scripts como `normalizar_maiusculas.py` sobrescreveriam os ajustes manuais.

Para procedimentos detalhados, código e edge cases, ver [modulos_pipeline.md](modulos_pipeline.md).

---

## Regras de execução

1. **R1 — Execução literal.** Cada etapa é obrigatória. Se diz "revisar TODOS" — revisar TODOS. Se diz "revisão LLM" — usar LLM. Antes de declarar fase concluída, reler a seção e confirmar cada sub-etapa.

2. **R2 — Registro imediato.** Após cada etapa, gravar no `revisao/{slug}-rev-status.md`. Formato: `✅ {ID} — {resumo}`. A etapa só está concluída quando o rev-status foi atualizado.

3. **R3 — Gates de transição.** Não avançar sem verificar que a etapa atual está ✅ no rev-status.

4. **R4 — Hierarquia de fontes.** (1) doc/docx — `python-docx`, (2) `fontes_plumber/` — `.jsonl`, (3) `fontes/` (pdftotext). SEMPRE verificar doc/docx antes de pdfplumber. NUNCA converter docx para txt — perde-se a estrutura.

5. **R5 — Salvar antes de inserir.** Dados extraídos — arquivo JSON primeiro, depois banco.

6. **R6 — Registrar correções automáticas.** Cada correção: artigo, campo, antes — depois, causa. Insumo da Fase 3.

7. **R7 — Retomada.** Ler rev-status — última ✅ — retomar próxima ⏳.

8. **R8 — Corrigir, não relatar.** Identificou problema — corrige na hora. Relatório sem correção = etapa não executada.

9. **R9 — Campo vazio ≠ genuinamente ausente.** Abrir PDF/docx para confirmar.

10. **R10 — Nenhuma etapa pode ser marcada com "OK" genérico.** Ao marcar `[x]` no runner, registrar o que foi feito e o resultado concreto (ex: "12 correções", "0 merges", "3 refs extraídas"). Se não há nada a registrar, a etapa não foi executada.

11. **R11 — Footnotes/endnotes NÃO vão no campo `references_`.** Se o artigo usa citação em nota de rodapé, o campo fica vazio (ou com as poucas refs bibliográficas que houver).

---

## Correspondência entre pipelines

| Etapa | Tratamento | Revisão | Rev. Humana |
|-------|-----------|---------|-------------|
| Aquisição/extração | Fases 1–6 | — | — |
| Banco + enriquecimento | Fase 7 | — | — |
| Revisão automática | Fase 7.3 (→ rev.) | Fases 0–2 | — |
| Revisão humana | — | — | Fases 3–5 |
| Aprendizado | Fase 8 (→ rev.) | Fase 3 | — |

---

## Template do rev-status

Criar em `revisao/{slug}-rev-status.md` na etapa 0.0:

```markdown
## Diagnóstico — {slug} ({N} artigos)

### Padrão de metadados
| Campo | Presença | Classificação | Ação |
|-------|----------|---------------|------|
| abstract | X% | PRESENTE/AUSENTE/INTERMEDIÁRIO | buscar nos PDFs / não buscar |
| abstract_en | X% | ... | ... |
| keywords | X% | ... | ... |
| keywords_en | X% | ... | ... |
| references | X% | ... | ... |

### Progresso
- ✅ 0.0 — Checkpoint inicial (commit abc1234)
- ✅ 0.1 — Padrão levantado
- ⏳ 0.2 — Artigos fora do padrão
- ...

### Log de correções automáticas
| Artigo | Campo | Antes | Depois | Causa |
|--------|-------|-------|--------|-------|
| sdbr13-143 | abstract | ES no campo PT | movido para abstract_es | extração sem verificação de idioma |
| sdbr13-024 | references_ | NULL | 29 refs | reinspecção pdfplumber |
```

---

## Checklist rápida

```
□ 0.0  Checkpoint inicial
□ 0.1  Levantar padrão de metadados
□ 0.2  Identificar artigos fora do padrão
□ 0.3  Reinspecionar PDFs
□ 0.3b Extrair fontes estruturadas (pdfplumber)
□ 0.4  Preencher lacunas no banco
□ 0.5  Verificar abstracts existentes
□ 0.6  Extrair metadados EN
□ 1.1a Títulos e subtítulos PT (normalização + LLM)
□ 1.1b Normalizar títulos EN e ES
□ 1.1c Revisão LLM de títulos EN e ES
□ 1.2a Referências: limpeza base
□ 1.2b Referências: sweep completo
□ 1.2b+ Re-rodar backfills
□ 1.2c Referências: revisão LLM
□ 1.3  Keywords
□ 1.4  Aplicar correções ao banco
□ 1.5  Loop de validação
□ 1.6  Cobertura de metadados + metadados do seminário
□ 1.7  Autores: completude vs PDF
□ 1.8  Dedup autores
□ 1.9  ORCID
□ 1.10 Revisão LLM final (TODOS artigos × TODOS campos vs plumber)
□ 2.0  Gerar HTML de revisão + checkpoint
□ 3.1  Diagnóstico unificado
□ 3.2  Atualizar dict.db
□ 3.3  Atualizar scripts
□ 3.4  Atualizar pipeline
□ 3.5  Verificar (dry-run + teste)
□ 3.6  Registrar aprendizado
□ 3.7  Revisão de engenharia
□ 3.8  Checklist de conclusão
□ 3.9  Fechar (commit + push)
```

---

## Visão geral do fluxo

```
┌─────────────────────────────────────────────────────┐
│ Fase 0 — Diagnóstico de padrão e preenchimento      │
│   0.1 Levantar padrão de metadados do seminário     │
│   0.2 Identificar artigos fora do padrão            │
│   0.3 Reinspecionar PDFs dos artigos fora do padrão │
│   0.3b Extrair fontes estruturadas (pdfplumber)     │
│   0.4 Preencher lacunas no banco                    │
│   0.5 Verificar abstracts existentes (truncamento   │
│       e lixo de cruzamento de idiomas)              │
│   0.6 Extrair metadados EN (title_en, subtitle_en)  │
├─────────────────────────────────────────────────────┤
│ Fase 1 — Revisão automática (Claude)                │
│   1.1a Títulos e subtítulos PT (LLM + PDF)          │
│   1.1b Normalizar títulos EN (Title Case) e ES (RAE)│
│   1.1c Revisão LLM de títulos EN e ES               │
│   1.2  Referências (limpeza completa)               │
│     1.2a clean_references.py (backfills, split,     │
│          join URLs)                                  │
│     1.2b sweep_refs (8 passadas: lixo grosso,       │
│          headers, page breaks, fragmentos,           │
│          endnotes, split, remoção, body text         │
│          truncado, near-duplicates)                  │
│     1.2c Revisão LLM de TODAS as refs (agente)      │
│          (concatenações, splits, notas, junk —       │
│          tudo que escapou ao sweep heurístico)       │
│   1.3  Keywords (split, garbage, capitalização)     │
│   1.4  Aplicar correções ao banco                   │
│                                                      │
│   ┌─── LOOP até convergir (max 5 iterações) ──────┐ │
│   │ 1.5a validate_metadata.py --fix (auto-fixes)   │ │
│   │ 1.5b fix handlers: A07 abs_en, A08 kw_en,      │ │
│   │      A19 abstract truncado (extração fontes/)   │ │
│   │ 1.5c Se zero issues corrigíveis: sair do loop  │ │
│   └────────────────────────────────────────────────┘ │
│                                                      │
│   1.6  Auditoria final                               │
│     1.6a Cobertura de metadados (artigos)            │
│     1.6b Metadados do seminário (verificar+preencher)│
│     1.6c Seções (eixos) ou sessões (programa)        │
│   1.7  Autores (completude vs PDF)                   │
│   1.8  Dedup autores                                 │
│   1.9  ORCID                                         │
├─────────────────────────────────────────────────────┤
│ Fase 2 — Gerar HTML de revisão                      │
├─────────────────────────────────────────────────────┤
│ Fase 3 — Aprendizado pós-revisão                    │
│   3.1–3.9 Diagnóstico, dict, scripts, pipeline,    │
│   verificação, registro, engenharia, fechar          │
├─────────────────────────────────────────────────────┤
│ Registro — revisao/{slug}-rev-status.md             │
│   Criar no início da Fase 0, atualizar a cada etapa │
│   Registrar ✅/⚠️ para cada ação concreta realizada  │
└─────────────────────────────────────────────────────┘
         ↓
   Pipeline de revisão humana (pipeline_revisao_humana.md)
```

**Princípio do loop 1.2-1.5:** A revisão automática (1.2-1.4) e a validação (1.5) formam um ciclo. A validação é o checkpoint — se ainda encontra problemas que a revisão automática deveria resolver, volta-se às etapas relevantes. Só se sai do loop quando os issues restantes são **fatos** (dado genuinamente ausente no PDF), não **erros** (dado extraível ou corrigível).

**Princípio da Fase 3 (aprendizado):** Após a revisão humana, cada correção manual é analisada: por que o pipeline não resolveu isso? A resposta é incorporada aos scripts, ao dict.db ou à documentação. O pipeline é **cumulativo** — melhora a cada seminário revisado.

### Ciclo de aprendizado

```
Seminário N                          Seminário N+1
┌──────────┐                         ┌──────────┐
│ Revisão  │──→ novos nomes próprios  │ Revisão  │
│ automát. │    novos topônimos  ──→  │ automát. │ (mais precisa)
│          │    novas expressões      │          │
│ Revisão  │──→ padrões confirmados   │ Revisão  │
│ humana   │    regras de exceção ──→ │ humana   │ (menos correções)
└──────────┘                         └──────────┘
       │                                    │
       ▼                                    ▼
   dict.db                              dict.db
   (+N entradas)                        (+N entradas)
   MEMORY.md                            MEMORY.md
   (padrões confirmados)                (padrões confirmados)
```

Fontes de aprendizado:
- **`dict.db`** (~5.300 entradas): nomes de autores (`seed_authors.py`), nomes próprios extraídos dos títulos (`seed_titles.py`), expressões consolidadas e topônimos adicionados manualmente durante a revisão
- **`MEMORY.md`**: padrões de capitalização confirmados na revisão humana
- **`regras_dados.md`**: regras formalizadas a partir de decisões tomadas durante a revisão

---

## Fase 0 — Diagnóstico de padrão e preenchimento de lacunas

Antes de qualquer revisão, identificar o **padrão de metadados do seminário** e preencher as lacunas nos artigos que desviam desse padrão. Se a maioria dos artigos tem um campo (ex: keywords), os poucos que não têm provavelmente tinham o dado no PDF e ele se perdeu na extração. Mas se nenhum artigo tem o campo, é porque o evento não exigia.

### 0.0 Checkpoint inicial

> **GATE**: nenhum
> **DONE**: dump + commit gravados; rev-status criado

```bash
python3 scripts/dump_anais_db.py
python3 dict/dump_db.py
git add anais.sql dict/dict.sql
git commit -m "{slug} pré-revisão: estado inicial"
```

Criar `revisao/{slug}-rev-status.md` usando o template acima.

### 0.1 Levantar padrão de metadados

> **GATE**: 0.0 ✅
> **DONE**: tabela de padrão preenchida no rev-status

```sql
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN abstract IS NOT NULL AND abstract != '' THEN 1 ELSE 0 END) as tem_abstract,
  SUM(CASE WHEN abstract_en IS NOT NULL AND abstract_en != '' THEN 1 ELSE 0 END) as tem_abstract_en,
  SUM(CASE WHEN keywords IS NOT NULL AND keywords != '' AND keywords != '[]' THEN 1 ELSE 0 END) as tem_kw,
  SUM(CASE WHEN keywords_en IS NOT NULL AND keywords_en != '' AND keywords_en != '[]' THEN 1 ELSE 0 END) as tem_kw_en,
  SUM(CASE WHEN references_ IS NOT NULL AND references_ != '' AND references_ != '[]' THEN 1 ELSE 0 END) as tem_refs
FROM articles WHERE seminar_slug = '{slug}';
```

Classificar cada campo como:
- **Padrão presente** (>=70% dos artigos têm): buscar nos PDFs dos artigos faltantes
- **Padrão ausente** (<30% dos artigos têm): não buscar — é característica do evento
- **Intermediário** (30-70%): avaliar caso a caso

Identificar norma de citação predominante (ABNT / Chicago / Misto / Footnotes). Ver [ref S-B.1](modulos_pipeline.md#b1-norma-de-citação) para procedimento de amostragem.

### 0.2 Identificar artigos fora do padrão

> **GATE**: 0.1 ✅
> **DONE**: listas com status ⏳ no rev-status

Para cada campo classificado como "padrão presente", listar os artigos que **não** têm o campo:

```sql
SELECT file, title FROM articles
WHERE seminar_slug = '{slug}' AND (abstract IS NULL OR abstract = '');
```

Repetir para cada campo relevante. Registrar no rev-status com status ⏳.

### 0.3 Reinspecionar PDFs

> **GATE**: 0.2 ✅
> **DONE**: zero ⏳ — todos ✅ (preenchido) ou ⬜ (genuinamente ausente)

Inspecionar **TODOS** os artigos fora do padrão, sem exceção. Usar hierarquia de fontes (R4). Ver [ref S-A](modulos_pipeline.md#a-hierarquia-de-fontes-para-extração) para detalhes de extração.

Pós-processamento obrigatório após extrair abstract e refs:

```python
from scripts.extrair_fontes_plumber import post_process_abstract, post_process_refs

abstract_limpo, keywords_extraidas = post_process_abstract(abstract_bruto)
refs_limpas = post_process_refs(refs_brutas)
```

Salvar dados extraídos em `revisao/{slug}-refs-extraidas.json` antes de inserir no banco (R5).

Para referências: classificar cada artigo (📚 bibliografia / 📝 endnotes / 📄 footnotes / ⬜ sem refs). Ver [ref S-B.2](modulos_pipeline.md#b2-subetapas-para-referências-faltantes) para detalhes.

### 0.3b Extrair fontes estruturadas — OBRIGATÓRIO

> **GATE**: 0.3 em andamento ou concluído
> **DONE**: fontes estruturadas para 100% dos artigos

**Hierarquia de fontes (R4):**

| Prioridade | Fonte | Ferramenta | Qualidade |
|------------|-------|-----------|-----------|
| 1 | doc/docx/odt/rtf | `extrair_metadados_doc.py` | Melhor (estilos preservados) |
| 2 | PDF texto | `extrair_fontes_plumber.py` | Boa (roles por font_size) |
| 3 | PDF imagem | `ocrmypdf` → plumber | Razoável |
| 4 | pdftotext | fallback | Básico |

```bash
# 1. Verificar se existem editáveis
find {base}/{slug}/fontes/ -name "*.doc" -o -name "*.docx" -o -name "*.odt" -o -name "*.rtf" | wc -l

# 2a. Se existem editáveis → extrair via docx (fonte primária)
python3 scripts/extrair_metadados_doc.py --slug {slug}           # diagnóstico
python3 scripts/extrair_metadados_doc.py --slug {slug} --apply   # extrair e gravar

# 2b. Extrair plumber TAMBÉM (fallback + verificação cruzada)
python3 scripts/extrair_fontes_plumber.py --slug {slug} --profile-only
python3 scripts/extrair_fontes_plumber.py --slug {slug}

# 2c. OCR para PDFs imagem (pôsteres, escaneados)
ocrmypdf -l por --force-ocr input.pdf output-ocr.pdf
```

Quando existem editáveis, `extrair_metadados_doc.py` é a **fonte primária** — preserva estilos de parágrafo e não tem problemas de colunas/OCR. O plumber serve como **fallback** para artigos sem docx e para **verificação cruzada**.

Completar SEMPRE o plumber para 100% dos artigos, mesmo quando existem docx. Na revisão LLM (§1.10), usar a melhor fonte disponível para cada artigo (docx > plumber > pdftotext).

### 0.4 Preencher lacunas no banco

> **GATE**: 0.3 ✅ (zero ⏳)
> **DONE**: dados inseridos; contadores no rev-status

Aplicar os dados extraídos ao banco **a partir dos arquivos JSON salvos**. Reportar quantos artigos foram preenchidos, quantos genuinamente não têm o dado.

**Verificação de idioma ao inserir abstracts:** Antes de inserir um abstract, verificar o idioma. Se o texto é em espanhol e o `locale` do artigo é `pt-BR`, inserir em `abstract_es`, **não** em `abstract`. (Aprendido com sdbr13-143.)

**Extrair também metadados ES:** Buscar `abstract_es` e `keywords_es` nos PDFs, não apenas EN. Artigos em PT podem ter seção Resumen/Palabras clave. (Aprendido com sdbr13-123.)

**Rodar sweep_refs DEPOIS de inserir refs:** Refs extraídas do pdfplumber frequentemente vêm splitadas por `\n` e precisam que a passada 1 (fragmentos) as junte. (Aprendido com sdbr13-024.)

### 0.5 Verificar abstracts existentes

> **GATE**: 0.4 ✅
> **DONE**: todos os abstracts verificados

**PRIMEIRO**, rodar o validate para corrigir automaticamente os problemas mais grossos:

```bash
# Pega: A20 (overflow >5000c), A25 (keywords coladas), A26 (idioma errado), A27 (PT no EN)
python3 scripts/validate_metadata.py --slug {slug} --fix
```

(Aprendido com sdbr13: 11 overflows de abstract_en detectados manualmente — A20 já sabia corrigir mas só rodava na Fase 1.5.)

Após o validate, varrer **todos** os abstracts do seminário para detectar: truncamento por quebra de página, texto PT colado no abstract_en, keywords vazadas, cabeçalhos/metadados misturados, abstract_es com lixo de cruzamento de idiomas. Ver [ref S-K](modulos_pipeline.md#k-verificação-de-abstracts--detalhes) para detalhes e código de detecção.

**Regra**: Corrigir diretamente no banco. Não deixar para a revisão humana — problemas de truncamento e lixo são mecânicos.

**Resumos expandidos (aprendido com sdsul07/08):** Seminários Sul frequentemente têm artigos marcados como "(Resumo expandido)" no PDF (label no footnote da p1). Esses artigos:
- Não têm seção "Resumo" separada — o corpo inteiro (3-10 páginas, 5000-12000c) é o resumo expandido
- A extração original captura o corpo inteiro como abstract → **overflow** (limpar)
- Solução: extrair o **1o parágrafo** (~1500-2500c) como abstract descritivo, cortando na última frase completa dentro de ~2500c
- Detecção: verificar label "(Resumo expandido)" nos blocos footnote da p1 do plumber
- Artigos completos sem seção Resumo: mesmo procedimento (1o parágrafo)
- sdsul08: 19/51 (37%) eram resumo expandido; sdsul07: 7/46 (15%) sem abstract genuíno

### 0.6 Extrair metadados EN

> **GATE**: 0.5 ✅
> **DONE**: title_en, abstract_en, keywords_en extraídos

Se o diagnóstico (0.1) mostrar presença de `abstract_en` >= 30%:

```bash
python3 scripts/extrair_metadados_en.py --slug {slug} --dry-run
python3 scripts/extrair_metadados_en.py --slug {slug}
```

Flags: `--force` re-extrai; `--only-title` extrai apenas title_en/subtitle_en. Títulos não capturados automaticamente serão revisados na 1.1c.

O script suporta `fontes/` (.txt) e `fontes_plumber/` (.jsonl). Para plumber, usa extração estruturada com verificação de blocos adjacentes (role=footnote/small) para continuação de abstract_en.

---

## Fase 1 — Revisão automática

O Claude executa verificações automatizadas e aplica correções ao banco **antes** de gerar o HTML de revisão.

### 1.1a Títulos e subtítulos PT

> **GATE**: Fase 0 ✅
> **DONE**: todos os títulos revisados palavra por palavra; JSON salvo

```bash
# 1. Alimentar dicionário com nomes novos
python3 dict/seed_authors.py
python3 dict/seed_titles.py --apply

# 2. Normalizar
python3 scripts/normalizar_maiusculas.py --slug {slug} --dry-run
python3 scripts/normalizar_maiusculas.py --slug {slug}
```

**Verificação com LLM — OBRIGATÓRIA.** Após a normalização automática, listar todos os títulos e analisar **cada palavra** de cada um. Procedimento:

1. `SELECT id, title, subtitle FROM articles WHERE seminar_slug = ? ORDER BY id`
2. Processar **um artigo por vez**. Para cada artigo, imprimir o julgamento de CADA palavra:
   ```
   sdbr12-041:
     T: O Habitat moderno em São Luís do Maranhão
     → "Habitat": conceito genérico → CORRIGIR para "habitat"
     → "São Luís": cidade → OK
     RESULTADO: O habitat moderno em São Luís do Maranhão
   ```
3. Para cada palavra com maiúscula (exceto a primeira): "por que está maiúscula?" — nome próprio, sigla, expressão consolidada — manter. Todo o resto — minúscula.
4. Subtítulos: verificar que começa com **minúscula** (exceto nome próprio, sigla).
5. Verificar separação título/subtítulo contra o PDF original.
6. **Aplicar correções escrevendo o título completo**, não por replace parcial. Reler após aplicar.

**Expressões consolidadas com toponímico:** "Arquitetura Moderna", "Arquitetura Modernista" etc. ficam maiúsculas quando referem o conceito. Porém, quando seguidas de toponímico, funcionam como descritivas e ficam em **minúscula**:
- ✅ "Os princípios da Arquitetura Moderna no Brasil" (conceito)
- ✅ "a arquitetura moderna de Recife" (descritiva + toponímico)

Ver [ref S-D](modulos_pipeline.md#d-revisão-llm-de-títulos-pt--procedimento-detalhado) para formato completo, retroalimentação do dict.db e registro de aprendizado.

Salvar aprendizado em `revisao/{slug}-titulos-aprendizado.json`.

### 1.1b Normalizar títulos EN e ES

> **GATE**: 1.1a ✅
> **DONE**: EN Title Case, ES sentence case RAE

```bash
python3 scripts/normalizar_titulos_en.py --slug {slug} --dry-run
python3 scripts/normalizar_titulos_en.py --slug {slug}
```

**Títulos EN** — Title Case (Chicago/APA): capitalizar tudo exceto artigos (a, an, the), preposições curtas (in, of, at...), conjunções (and, but, or). Primeira/última palavra e após `:` ou `—` sempre maiúscula.

**Títulos ES** — Sentence case RAE: maiúscula somente para primeira palavra, nomes próprios e siglas. NÃO usar expressões consolidadas em maiúscula — em espanhol não existem. NÃO usar `normalizar_maiusculas.py` (dict.db calibrado para PT).

**Títulos de artigos em locale=es**: o título principal (`title`) está em espanhol — aplicar regras RAE, não PT.

Ver [ref S-E](modulos_pipeline.md#e-regras-de-capitalização-en-e-es) para regras completas.

### 1.1c Revisão LLM de títulos EN e ES

> **GATE**: 1.1b ✅
> **DONE**: cada título comparado com PDF

Revisão LLM real — ler CADA título contra o PDF. Problemas que só uma leitura real pega: palavras coladas ("Destructionorconstruction..."), lixo vazado de outros campos, typos de OCR, acentos faltantes em nomes próprios.

Salvar aprendizado em `revisao/{slug}-titulos-en-aprendizado.json`. Ver [ref S-E.1](modulos_pipeline.md#e1-revisão-llm-de-títulos-en-e-es) para procedimento.

### 1.2a Referências: limpeza base

> **GATE**: 1.1c ✅
> **DONE**: backfills, splits, URLs resolvidos

```bash
python3 scripts/clean_references.py --slug {slug} --dry-run
python3 scripts/clean_references.py --slug {slug}
python3 scripts/check_references.py --slug {slug} --summary
```

Resolve: backfills (underscores ABNT — autor anterior), split de refs concatenadas por underscores, join de URLs órfãs.

**Artigos com 0 referências:** Verificar nos PDFs se há seção de referências. Se houver, extrair.

### 1.2b Referências: sweep completo

> **GATE**: 1.2a ✅
> **DONE**: < 2% problemas

```bash
python3 scripts/fix_validation_issues.py --slug {slug} --sweep-refs --dry-run
python3 scripts/fix_validation_issues.py --slug {slug} --sweep-refs
```

Varredura completa de TODAS as refs em 8 passadas. Ver [ref S-C](modulos_pipeline.md#c-sweep_refs--passadas-e-heurísticas) para detalhes de cada passada.

| Passada | Ação |
|---------|------|
| 0. Lixo grosso | Remover body text, figure captions, headers, NOTAS |
| 0b. Headers prefixo | Strip headers de seção prepostos/apostos |
| 0c. Page breaks | Split em marcadores ⏐ + número de página |
| 1. Fragmentos | Juntar à ref anterior |
| 2. Endnotes | Se contém ref: extrair; senão: remover |
| 3. Split | Separar concatenadas > 300 chars |
| 4. Remoção | Remover não-referências restantes |
| 5. Body text | Truncar body text do final de refs mistas |
| 6. Near-dupes | Remover near-duplicates |

### 1.2b+ Re-rodar backfills

> **GATE**: 1.2b ✅
> **DONE**: zero backfills pendentes

```bash
python3 scripts/clean_references.py --slug {slug} --dry-run
python3 scripts/clean_references.py --slug {slug}
```

Aprendido com sdbr13: o sweep cria novos backfills ao splittar refs concatenadas. Re-rodar resolve sem intervenção manual.

### 1.2c Referências: revisão LLM

> **GATE**: 1.2b+ ✅
> **DONE**: TODOS artigos revisados; relatório gerado

**REGRA ABSOLUTA**: Esta é uma revisão LLM real — um agente que lê CADA artigo contra a fonte e compara com o banco. NÃO é rodar scripts heurísticos. O sweep resolve ~70% dos problemas; os ~30% restantes escapam às heurísticas.

Tipos de problema que escapam: concatenação Chicago, notas sem número, notas com ref embutida, backfill concatenado, fragmento contextual, near-dupes com variação, headers infiltrados.

**Procedimento:**
1. Para cada artigo, ler `fontes_plumber/{id}.jsonl` (preferencial) ou `fontes/{id}.txt`. NUNCA reconstruir texto fragmentado do pdftotext.
2. **PASSO CRÍTICO**: Identificar o **ponto de corte** entre BIBLIOGRAFIA e NOTAS (heading "NOTAS", numeração sequencial, mudança de padrão, mudança de font_size no plumber).
3. Definir a lista de refs válidas (até o ponto de corte) e descartar notas.
4. Corrigir: concatenações, splits, headers.
5. Gravar no banco.
6. Gerar relatório.

**REGRA**: A 1.2c **corrige** — não apenas relata. Relatório sem correção = etapa não executada.

**NOTA**: A verificação completa de TODOS os campos (títulos, abstracts, keywords) é feita na etapa 1.10 — a revisão LLM final. A 1.2c foca nas referências.

**Refs longas (A11) que o sweep não resolveu:** Resolver na revisão LLM — ler o PDF/plumber, identificar se é concatenação, lista de fontes/URLs, ou ref legítima longa. Não deixar para revisão humana.

Ver [ref S-F](modulos_pipeline.md#f-revisão-llm-de-referências--procedimento-detalhado) para prompt e critérios.

### 1.3 Keywords

> **GATE**: 1.2c ✅
> **DONE**: limpas, normalizadas, sem inconsistências

```bash
python3 scripts/fix_validation_issues.py --slug {slug} --clean-keywords --dry-run
python3 scripts/fix_validation_issues.py --slug {slug} --clean-keywords
```

O `--clean-keywords` executa: remover template garbage, separar keywords aglutinadas, trim de pontuação final, dedup.

Capitalização: PT — regras dos títulos (expressões consolidadas maiúsculas, genéricos minúsculas); EN — Title Case para movimentos; ES — mesma lógica que PT. Verificar inconsistências (mesmo keyword com casing diferente) e padronizar.

Ver [ref S-J](modulos_pipeline.md#j-keywords--detalhes) para código de detecção de inconsistências.

### 1.4 Aplicar correções ao banco

> **GATE**: 1.1-1.3 ✅
> **DONE**: contagens no rev-status

Todas as correções das etapas 1.1-1.3 são aplicadas ao `anais.db`. Reportar contagens (N títulos, N refs corrigidas, N keywords corrigidas).

### 1.5 Loop de validação

> **GATE**: 1.4 ✅
> **DONE**: zero issues corrigíveis (ou max 5 iterações)

```bash
python3 scripts/fix_validation_issues.py --slug {slug} --loop
```

```
         ┌───────────────────────────────────────────┐
         │  validate_metadata.py --fix (auto-fixes)   │
         │  A15 locale mismatch                       │
         │  A16 control chars                         │
         │  A17 refs duplicadas                       │
         │  A20 abstract overflow                     │
         │  A21 abstract_es lixo EN / redundante      │
         │  A22 body text em refs (remove entradas)   │
         └──────────────┬────────────────────────────┘
                        │
                        ▼
         ┌───────────────────────────────────────────┐
         │  fix handlers (extração de fontes/)        │
         │  A07 extrair abstract_en                   │
         │  A08 extrair keywords_en                   │
         │  A19 re-extrair abstracts truncados         │
         └──────────────┬────────────────────────────┘
                        │
                        ▼
              Algo foi corrigido?
              ╱              ╲
            sim               não → sair do loop → 1.6
              ╲              ╱
               ▼
              volta ao topo (max 5×)

**NOTA:** A10 (backfills), A11 (split), A12 (não-refs), A13 (URLs órfãs)
são resolvidos pelo sweep_refs (1.2b) — NÃO fazem parte do loop.
```

O `--loop` **NÃO** re-roda `clean_references.py` nem `--sweep-refs`. Esses devem ser executados antes (1.2a e 1.2b). Critério de saída: issues restantes são fatos (dado ausente no PDF), não erros.

Ver [ref S-G](modulos_pipeline.md#g-checks-de-validação-a01a27) para tabela completa de checks A01-A27.

### 1.6a Cobertura de metadados

> **GATE**: 1.5 ✅
> **DONE**: tabela de cobertura no rev-status

| Campo | Obrigatório | Observação |
|-------|-------------|------------|
| title | ✅ sim | Deve ter 100% |
| subtitle | ❌ não | Nem todo artigo tem subtítulo |
| abstract | ✅ sim | Exceções: artigos só resumo sem abstract no PDF |
| abstract_en | condicional | Se >=30% do seminário tem, buscar nos faltantes |
| abstract_es | condicional | Só artigos em espanhol |
| keywords | ✅ sim | Exceções: template vazio no PDF |
| keywords_en | condicional | Se >=30% do seminário tem |
| keywords_es | condicional | Só artigos em espanhol |
| references_ | ✅ sim | Exceções: artigos com footnotes (sem lista de refs) |
| locale | ✅ sim | Deve ter 100% |
| title_en | ❌ não | Só se o artigo tem seção EN no PDF |
| autores | ✅ sim | Deve ter 100% |

### 1.6b Metadados do seminário

> **GATE**: 1.6a ✅
> **DONE**: campos verificados contra ficha catalográfica

Verificar contra a ficha catalográfica original (PDF dos anais, primeiras páginas): title, subtitle, publisher, isbn, date_published, location, description, editors.

**"Disponível originalmente em:"**: se os anais foram publicados em site externo ao docomomobrasil.com, adicionar ao final da description.

Gerar/atualizar a `description` (ficha catalográfica ABNT). Prioridade: transcrever a ficha CIP do PDF; se não houver, construir a partir dos campos. Ver [ref S-H](modulos_pipeline.md#h-metadados-do-seminário--detalhes) para formato e código.

### 1.6c Seções/sessões

> **GATE**: 1.6b ✅
> **DONE**: seções criadas e artigos mapeados

**Hierarquia de preferência:** Primeiro eixos temáticos (divisão editorial), depois sessões (divisão logística) se eixos não encontrados.

**Fontes (em ordem de prioridade):**
1. `fontes/` do seminário — HTML/XML de DVDs originais, sumários, programas impressos
2. Folha de rosto dos artigos — muitos PDFs indicam o eixo/sessão no cabeçalho
3. Site original (campo `source` na tabela `seminars`) — site de onde os PDFs foram baixados
4. Busca na internet / Wayback Machine — programação do evento
5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
6. Caderno de resumos

**NUNCA** manter seção genérica "Artigos" sem esgotar todas as fontes acima. Documentar qual fonte foi usada.

**Quando artigos ficam sem seção após esgotar as fontes acima:** verificar subtítulos dos artigos — podem conter referência direta ao subtema/eixo (ex: "projeto, restauro e retrofit" → subtema Restauro). Atribuir nesses casos.

**Procedimento:** Verificar PDFs — extrair eixos — criar seções no banco (`INSERT INTO sections`) — mapear artigos — seções sem artigos ficam para documentar a estrutura. Capitalização: sentence case (converter ALL CAPS do PDF).

### 1.7 Autores: completude vs PDF

> **GATE**: 1.6c ✅
> **DONE**: autores verificados para TODOS os artigos

Verificação **exaustiva** — comparar CADA artigo com o PDF. Direção: fonte — banco.

Verificar: completude (todos os autores do PDF estão no banco?), nomes (givenname/familyname, partículas), afiliação (sigla), ordem.

Se autores novos foram adicionados, rodar:

```bash
python3 dict/seed_authors.py
```

Ver [ref S-I](modulos_pipeline.md#i-autores--detalhes) para código de verificação comparativa.

### 1.8 Dedup autores

> **GATE**: 1.7 ✅
> **DONE**: zero merges pendentes

```bash
python3 scripts/dedup_authors.py --dry-run
python3 scripts/dedup_authors.py
python3 scripts/expand_initials.py --report
python3 scripts/expand_initials.py --pilotis
```

### 1.9 ORCID

> **GATE**: 1.8 ✅
> **DONE**: ORCIDs buscados e aplicados

```bash
python3 scripts/fetch_orcid.py --search
python3 scripts/fetch_orcid.py --review
python3 scripts/fetch_orcid.py --apply
```

**REGRA**: Se um autor novo foi adicionado, SEMPRE rodar o fluxo completo (seed — dedup — iniciais — ORCID).

### 1.10 Revisão LLM final — TODOS os artigos, TODOS os campos

> **GATE**: 1.9 ✅
> **DONE**: CADA artigo confrontado com o plumber, CADA campo verificado

**REGRA ABSOLUTA**: Esta é a ÚLTIMA etapa antes do HTML. Confrontar **CADA artigo** com o plumber e verificar **TODOS os campos**: título, subtítulo, abstract, abstract_en, keywords, keywords_en, referências. Corrigir na hora (R8).

**Diferença da 1.2c**: A 1.2c foca nas refs durante a fase de limpeza. A 1.10 é o passo final que verifica tudo — incluindo campos que podem ter sido corrompidos por auto-fixes, abstracts truncados que escaparam, títulos com discrepância vs PDF, keywords com lixo.

**Procedimento — UM artigo por vez:**

Para cada artigo, na ordem do HTML:

1. **Ler o plumber INTEIRO** — `cat fontes_plumber/{id}.jsonl`. Não "primeiras/últimas linhas". O arquivo inteiro.
2. **Título e subtítulo**: o texto na primeira página com font_size grande (≥12) é o título do PDF. Comparar com o campo `title` no banco. Verificar capitalização, acentos, truncamento.
3. **Abstract PT**: localizar o bloco de texto após "Resumo" (font_size ~10). Comparar com `abstract` no banco. Verificar:
   - Começa no mesmo ponto? (Truncamento no início é o erro mais comum)
   - Termina no mesmo ponto? (Truncamento no final)
   - Contém credenciais/afiliação em vez de abstract?
   - Contém subtítulo duplicado no início?
4. **Abstract EN**: localizar "Abstract" no plumber. Mesmo checklist do item 3.
5. **Keywords**: localizar "Palavras-chave" / "Keywords". Comparar com `keywords` / `keywords_en`. Verificar se são keywords reais (não fragmentos de texto, não numeração).
6. **Title EN**: se existe no banco, verificar que NÃO é um footnote, referência bibliográfica, ou fragmento de abstract. Se o PDF não tem título em EN, o campo deve ser NULL.
7. **Refs**: localizar "Referências" / "Bibliografia" no plumber. Comparar com `references_` no banco. Verificar:
   - Refs são bibliográficas (não notas de rodapé, não legendas de figuras)
   - Lista está completa (conferir primeira e última ref vs plumber)
   - Sem concatenações (refs coladas sem separação)
   - Artigos com 0 refs: confirmar que o PDF realmente não tem referências
8. **Registrar resultado**: `{id}: {N} correções` ou `{id}: OK (verificado)`. Cada artigo deve ter uma linha no runner.

**PROIBIDO:**
- Rodar heurísticas em batch e marcar como "revisão LLM" — isso NÃO é revisão
- Processar artigos sem ler o plumber — ler é obrigatório, não opcional
- Marcar 1.10 como concluída sem listar o resultado de CADA artigo no runner

**Após a 1.10**, rodar validate + gerar HTML. Nenhuma etapa de conteúdo pode ser feita após a 1.10 — apenas etapas mecânicas (validate, HTML, dump, commit).

---

## Fase 2 — Gerar HTML de revisão + checkpoint

> **GATE**: TODAS as etapas Fase 0 e 1 (incluindo 1.10) ✅
> **DONE**: HTML gerado, dump + commit

**ANTES de gerar**, reler o rev-status e confirmar que não há etapas ⏳.

```bash
# 1. Validação final
python3 scripts/validate_metadata.py --slug {slug} --fix

# 2. Gerar HTML
python3 scripts/gerar_revisao_html.py {slug}

# 3. Checkpoint
python3 scripts/dump_anais_db.py
python3 dict/dump_db.py
git add anais.sql dict/dict.sql revisao/{slug}-*
git commit -m "{slug} revisão automática concluída (Fases 0-2)"
```

Gera `revisao/revisao-{slug}.html` com capa, ficha, artigos por seção, alertas inline.

**Próximo passo:** Executar o [pipeline de revisão humana](pipeline_revisao_humana.md).

---

## Fase 3 — Aprendizado pós-revisão

Executar **após** a conclusão da revisão humana. Usa como insumo **todas** as correções: tanto as da fase automática (Fases 0-1) quanto as da revisão humana.

**Princípio:** Para cada correção, perguntar: "por que o pipeline não resolveu isso automaticamente?" O aprendizado só existe se resultar em **alteração concreta**: entrada no dict, regra no script, ou instrução documentada.

**REGRA CRÍTICA:** A Fase 3 **NÃO é um registro passivo**. É a fase onde se **modificam scripts, dict.db e pipeline** para que os mesmos erros não ocorram no próximo seminário. Se a Fase 3 não produz nenhuma alteração em código ou dados, ela falhou — significa que ou os erros foram ignorados, ou o diagnóstico foi superficial. "Não automatizável" só é aceitável se o problema for genuinamente único (1 artigo, sem padrão). Se >=2 seminários tiveram o mesmo tipo de erro manual, é automatizável.

### 3.1 Diagnóstico unificado

> **GATE**: revisão humana concluída
> **DONE**: log de causa raiz no rev-status

Agregar TODAS as correções num log único:
1. **Correções automáticas** (do rev-status): overflows, keywords com lixo, backfills, idioma errado, refs com notas
2. **Correções humanas** (do rev.md): títulos, refs, dados faltantes
3. **Cruzamento com seminários anteriores**: problemas que se repetiram

Para cada problema, classificar:
- **Padrão recorrente** — automatizar (novo check, nova heurística)
- **Caso único** — só aplicar a correção
- **Dado faltante no dict.db** — adicionar
- **Gap na ordem de execução** — ajustar pipeline

### 3.2 Atualizar dict.db

> **GATE**: 3.1 ✅
> **DONE**: dict.db atualizado

| Tipo | Ação no dict.db | Exemplo |
|------|----------------|---------|
| Palavra genérica forçando maiúscula | **REMOVER** | `obra`, `restauração`, `tradição` |
| Gentílico/adjetivo forçando maiúscula | **REMOVER** | `carioca`, `metropolitana` |
| Nome próprio faltando | **ADICIONAR** | `Bienal`, `Esplanada`, `Centenário` |
| Expressão consolidada faltando | **ADICIONAR** como expressão | `Centro Administrativo`, `Base Naval` |

Critério de remoção: revisão corrigiu para minúscula em >=2 artigos e não é nome próprio.
Critério de adição: revisão corrigiu para maiúscula e é nome de edifício/instituição/evento/lugar.

### 3.3 Atualizar scripts de validação

> **GATE**: 3.2 ✅
> **DONE**: scripts atualizados (ou N/A)

Se um tipo de erro apareceu em >=3 artigos e **não** é coberto pelos scripts existentes, adicionar a regra.

### 3.4 Atualizar pipeline

> **GATE**: 3.3 ✅
> **DONE**: pipeline atualizado (ou N/A)

Se o diagnóstico identificou gaps na ordem de execução, atualizar este documento.

### 3.5 Verificar

> **GATE**: 3.4 ✅
> **DONE**: dry-run sem regressão

Re-rodar scripts alterados em dry-run no mesmo seminário. Testar também num seminário não revisado.

### 3.6 Registrar aprendizado

> **GATE**: 3.5 ✅
> **DONE**: JSON + MEMORY.md atualizados

Arquivo: `revisao/{slug}-aprendizado-revisao.json`. Atualizar MEMORY.md com padrões confirmados novos.

### 3.7 Revisão de engenharia

> **GATE**: 3.6 ✅
> **DONE**: achados listados no runner (ver R10)

**Se houve alteração de código na Fase 3** (checks novos, fix_actions, heurísticas), verificar:
- Novos fix_actions têm handler correspondente no bloco de aplicação?
- Novos checks estão registrados no `check_desc`?
- Novos checks estão na lista de chamadas (`issues.extend(...)`)?
- Dry-run em seminário revisado: 0 regressões?
- Dry-run em seminário não revisado: 0 falsos positivos?

**Sempre:**
- Autoavaliação: "executei **todas** as etapas do pipeline para este seminário?"
- Lints: inconsistências pipeline vs scripts
- Erros de lógica: checks que se contradizem, auto-fixes que desfazem correções manuais
- Redundância: mesma verificação em dois lugares, código morto
- Riscos de loop: auto-fixes que criam problemas para outros auto-fixes
- Ordem de execução: checks que dependem de dados que só existem após outra etapa
- Cobertura: gaps entre promessa e implementação
- Robustez: scripts que crasham com dados inesperados

### 3.8 Checklist de conclusão

> **GATE**: 3.7 ✅
> **DONE**: todos os itens abaixo verificados

- [ ] 3.1 Diagnóstico unificado — tabela de causa raiz no rev-status
- [ ] 3.2 Dict atualizado (remoções + adições)
- [ ] 3.3 Scripts corrigidos (se aplicável)
- [ ] 3.4 Pipeline atualizado (se aplicável)
- [ ] 3.5 Verificação (dry-run + teste em outro seminário)
- [ ] 3.6 Aprendizado registrado (JSON + MEMORY.md)
- [ ] 3.7 Revisão de engenharia

Se algum item não foi feito, **parar e fazer antes de commitar**.

### 3.9 Fechar

> **GATE**: 3.8 ✅
> **DONE**: commit + push + CLAUDE.md atualizado

1. Adicionar seminário à tabela de revisados em `CLAUDE.md` (status ✅, data)
2. Adicionar entrada no devlog do `CLAUDE.md`
3. Dump, commit e push:

```bash
python3 scripts/dump_anais_db.py
python3 dict/dump_db.py
git add anais.sql dict/dict.sql CLAUDE.md docs/pipeline_revisao.md docs/pipeline_revisao_humana.md \
       scripts/*.py revisao/{slug}-*
git commit -m "{slug} revisado + melhorias pipeline"
git push
```

**Exemplos concretos:**

| Seminário | Correção | Falha identificada | Incorporação |
|-----------|----------|-------------------|-------------|
| sdbr10 | "la" maiúscula em título ES | `dict.db` tinha "la" como `nome` | Removido do dict |
| sdbr10 | NOTAS misturadas com refs | sweep_refs sem passada 0 | Adicionados padrões body text e figure captions |
| sdbr13 | 11 overflows abstract_en | A20 só rodava na Fase 1.5 | Rodar validate --fix na Fase 0.5 |
| sdbr13 | 31 keywords_en com lixo | clean_keywords sem filtros ALL CAPS/junk | KW_JUNK_RE, ALL CAPS >=15, >80c |
| sdbr13 | abstract ES no campo PT | Não existia check para idioma errado | A26 novo (auto-fix) |
| sdbr13 | PT colado no abstract_en | A23 só detecta EN→PT | A27 novo (auto-fix) |

---

## Referência rápida de comandos

| Comando | Fase | Função |
|---------|------|--------|
| `scripts/extrair_fontes_plumber.py --slug {slug}` | 0.3b | Extrair fontes estruturadas (pdfplumber — .jsonl com roles semânticos) |
| `scripts/extrair_metadados_en.py --slug {slug}` | 0.6 | Extrair title_en, subtitle_en, abstract_en, keywords_en |
| `scripts/validar_abstracts.py --slug {slug}` | 0.5 | Validar abstracts (9 regras + lixo ES) |
| `scripts/validar_abstracts.py --slug {slug} --fix-swap` | 0.5 | Corrigir swaps abstract PT<>EN |
| `dict/seed_authors.py` + `seed_titles.py --apply` | 1.1a | Alimentar dicionário |
| `scripts/normalizar_maiusculas.py --slug {slug}` | 1.1a | Normalizar títulos PT |
| `scripts/normalizar_titulos_en.py --slug {slug}` | 1.1b | Normalizar títulos EN (Title Case) |
| `scripts/clean_references.py --slug {slug}` | 1.2a | Limpar referências (backfills, split ABNT, URLs) |
| `scripts/check_references.py --slug {slug} --summary` | 1.2a | Verificar referências |
| `scripts/fix_validation_issues.py --slug {slug} --sweep-refs` | 1.2b | Varredura completa de refs (8 passadas) |
| `scripts/fix_validation_issues.py --slug {slug} --clean-keywords` | 1.3 | Limpeza de keywords (split, garbage, trim, dedup) |
| `scripts/validate_metadata.py --slug {slug} --fix` | 1.5a | Validar + auto-fix (checkpoint do loop) |
| `scripts/fix_validation_issues.py --slug {slug} --loop` | 1.5 | Loop validate — fix — validate até convergir |
| `scripts/gerar_revisao_html.py {slug}` | 2 | Gerar HTML de revisão (com alertas de validação) |
