# Pipeline de Revisão Automática de Metadados

Pipeline para revisão automática dos metadados dos artigos no `anais.db`. Complementa o [pipeline de tratamento](pipeline_tratamento.md) (fases 1-7) e antecede o [pipeline de revisão humana](pipeline_revisao_humana.md) (Fases 3–5).

A revisão é necessária porque a extração automatizada dos PDFs produz erros sistemáticos: títulos com capitalização errada, resumos truncados, keywords faltantes, referências concatenadas ou ausentes. O pipeline automático corrige os problemas detectáveis por heurísticas; o que escapar vai para a revisão humana.

**IMPORTANTE:** Este pipeline roda **uma única vez** por seminário, **antes** da revisão humana. Após a revisão humana ter corrigido títulos, subtítulos e outros campos, **nunca** re-rodar este pipeline no mesmo seminário — scripts como `normalizar_maiusculas.py` sobrescreveriam os ajustes manuais.

### Ciclo de aprendizado

O pipeline é cumulativo: cada seminário revisado melhora a revisão dos seguintes.

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
- **`MEMORY.md`**: padrões de capitalização confirmados na revisão humana (ex: "Arquitetura Moderna" sempre maiúscula, "modernismo" isolado em minúscula, "Centro" de cidade em maiúscula)
- **`regras_dados.md`**: regras formalizadas a partir de decisões tomadas durante a revisão

Quanto mais seminários forem revisados, menos correções manuais serão necessárias nos seguintes — a revisão automática (Fase 1) fica progressivamente mais precisa.

---

## Visão geral do fluxo

```
┌─────────────────────────────────────────────────────┐
│ Fase 0 — Diagnóstico de padrão e preenchimento      │
│   0.1 Levantar padrão de metadados do seminário     │
│   0.2 Identificar artigos fora do padrão            │
│   0.3 Reinspecionar PDFs dos artigos fora do padrão │
│   0.4 Preencher lacunas no banco                    │
│   0.5 Verificar abstracts existentes (truncamento)  │
│   0.6 Extrair metadados EN (title_en, subtitle_en)  │
├─────────────────────────────────────────────────────┤
│ Fase 1 — Revisão automática (Claude)                │
│   1.1a Títulos e subtítulos PT (LLM + PDF)          │
│   1.1b Normalizar títulos EN (Title Case)           │
│   1.1c Revisão LLM de títulos EN                    │
│   1.2  Referências (clean + check + extração)       │
│   1.3  Aplicar todas as correções ao banco          │
├─────────────────────────────────────────────────────┤
│ Fase 2 — Gerar HTML de revisão                      │
└─────────────────────────────────────────────────────┘
         ↓
   Pipeline de revisão humana (pipeline_revisao_humana.md)
```

---

## Fase 0 — Diagnóstico de padrão e preenchimento de lacunas

Antes de qualquer revisão, identificar o **padrão de metadados do seminário** e preencher as lacunas nos artigos que desviam desse padrão. A lógica é simples: se a maioria dos artigos tem um campo (ex: keywords), os poucos que não têm provavelmente tinham o dado no PDF e ele se perdeu na extração. Mas se nenhum artigo tem o campo, é porque o evento não exigia — e não adianta buscar.

### 0.0 Registro de diagnóstico

**ANTES de qualquer ação**, criar um registro de diagnóstico no formato abaixo. Este registro serve como checklist — nenhuma fase pode avançar enquanto houver itens pendentes.

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

### Artigos fora do padrão — {campo}
| Artigo | Status | Observação |
|--------|--------|------------|
| {file} | ⏳ pendente | |
...

(repetir para cada campo classificado como PRESENTE ou INTERMEDIÁRIO)
```

O registro é preenchido progressivamente:
- **0.1** preenche a tabela de padrão
- **0.2** preenche as listas de artigos fora do padrão (todos com status ⏳)
- **0.3** atualiza cada artigo para ✅ (preenchido) ou ⬜ (genuinamente ausente)
- **0.4** salva no banco apenas os ✅, confirma que não restam ⏳

**Regra de transição**: só avançar para a Fase 1 quando **zero** itens ⏳ restarem no registro.

### 0.1 Levantar padrão de metadados

Consultar o banco para cada campo relevante:

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
- **Padrão presente** (≥70% dos artigos têm): buscar nos PDFs dos artigos faltantes
- **Padrão ausente** (<30% dos artigos têm): não buscar — é característica do evento
- **Intermediário** (30-70%): avaliar caso a caso, pode ser um subconjunto (ex: pôsteres sem abstract)

### 0.2 Identificar artigos fora do padrão

Para cada campo classificado como "padrão presente", listar os artigos que **não** têm o campo. Esses são os candidatos a reinspecção de PDF.

```sql
-- Exemplo: artigos sem abstract num seminário onde abstract é padrão
SELECT file, title FROM articles
WHERE seminar_slug = '{slug}' AND (abstract IS NULL OR abstract = '');
```

### 0.3 Reinspecionar PDFs

**REGRA: Inspecionar TODOS os artigos fora do padrão, sem exceção.** Não avançar para a Fase 0.4 nem para a Fase 1 enquanto todos os PDFs não tiverem sido inspecionados. Verificar parcialmente e prosseguir é o erro mais comum nesta etapa.

**Extração de texto**: Extrair texto de TODOS os PDFs do seminário com `pdftotext` e salvar na pasta `fontes/` do seminário. Os txts ficam disponíveis para todas as etapas seguintes e para uso futuro.

```bash
mkdir -p nacionais/{slug}/fontes  # ou regionais/{grupo}/{slug}/fontes
for pdf in nacionais/{slug}/pdfs/*.pdf; do
  pdftotext "$pdf" "nacionais/{slug}/fontes/$(basename "$pdf" .pdf).txt" 2>/dev/null
done
```

Para PDFs escaneados, verificar com `pdfinfo` e usar `ocrmypdf` antes do `pdftotext`.

Para **cada** artigo fora do padrão, buscar o campo faltante no txt extraído:
- **Abstract/resumo**: geralmente após o título e autores, antes das keywords
- **Keywords**: geralmente após o abstract, marcadas com "Palavras-chave:" ou "Keywords:"
- **Referências**: ver subetapas abaixo
- **Abstract EN**: após o abstract PT ou no final do artigo

#### Subetapas para referências faltantes

O diagnóstico de referências é mais granular que os demais campos, porque existem três tipos de fonte no PDF:

**Passo 1 — Extrair texto e classificar todos os artigos sem refs:**

| Artigo | Tipo | Status |
|--------|------|--------|
| {file} | 📚 bibliografia explícita / 📝 endnotes / 📄 footnotes / ⬜ sem refs | ⏳ |

Onde:
- **📚 bibliografia explícita**: seção "Referências", "Bibliografia", "Referências Bibliográficas" etc.
- **📝 endnotes (notas de fim)**: seção "Notas", "Notas ao Texto" com citações numeradas
- **📄 footnotes (notas de rodapé)**: citações dispersas no rodapé das páginas, sem seção dedicada
- **⬜ sem refs**: PDF inspecionado, nenhuma referência encontrada

**Passo 2 — Extrair na ordem de facilidade:**
1. Primeiro: 📚 bibliografias explícitas (extração direta)
2. Depois: 📝 endnotes (extração + limpeza de numeração)
3. Por último: 📄 footnotes (extração complexa, pode não valer o esforço)

**Passo 3 — Salvar extração em arquivo antes de inserir no banco:**

```bash
# Salvar refs extraídas em JSON para não perder na compactação de sessão
# Arquivo: revisao/{slug}-refs-extraidas.json
{
    "sdbr06-006.pdf": ["ref1", "ref2", ...],
    "sdbr06-012.pdf": ["ref1", "ref2", ...],
    ...
}
```

Só depois de salvo o arquivo, inserir no banco. Isso garante que a extração não se perde se a sessão for compactada.

**Checklist obrigatório** antes de prosseguir: todos os artigos devem estar marcados como:
- ✅ preenchido (dado encontrado no PDF, salvo em arquivo e no banco)
- ⬜ genuinamente ausente (PDF inspecionado, campo não existe no documento)
- 📄 footnotes (flagged para avaliação futura — não bloqueia a transição)

Só avançar quando **zero** itens ⏳ restarem.

### 0.4 Preencher lacunas no banco

Aplicar os dados extraídos ao banco **a partir do arquivo JSON salvo na etapa anterior**. Reportar:
- Quantos artigos estavam fora do padrão por campo
- Quantos foram preenchidos com sucesso
- Quantos genuinamente não têm o dado (confirmado no PDF)
- **Lista completa** com status de cada artigo (checklist ✅/⬜/📄)

### 0.5 Verificar abstracts existentes (truncamento e lixo)

Após preencher as lacunas (0.4), varrer **todos** os abstracts do seminário — tanto os já existentes quanto os recém-inseridos — para detectar problemas de extração. A varredura deve cobrir 100% dos artigos, não apenas os que foram preenchidos na Fase 0.

**Problemas a detectar:**

1. **Truncamento por quebra de página**: o `pdftotext` insere números de página como linhas isoladas (`\n\n3\n\n`). Quando o abstract cruza a fronteira de uma página, o extrator pode parar no número de página e truncar o texto. **Tratamento**: antes de extrair, limpar o texto com `re.sub(r'\n\s*\n\s*\d{1,3}\s*\n\s*\n', '\n\n', text)` para remover números de página soltos. Após extração, verificar se o abstract termina com pontuação de fim de frase.
2. **Truncamento genérico**: abstract termina no meio de uma frase (sem `.`, `?`, `!`, `"`, `)` no final)
3. **Texto PT colado no abstract_en**: palavras em português após o fim do abstract em inglês (padrão mais comum: abstract_en seguido de "A historiografia...", "O presente trabalho...", "Palavras-chave:...")
4. **Keywords vazadas**: "Palavras-chave:", "Keywords:", "Key words:" no final do abstract
5. **Cabeçalhos e metadados**: títulos de seções, nomes de autores, números de página misturados
6. **Início truncado**: abstract começa no meio de uma frase (faltando o início)
7. **Abstract muito curto**: < 100 caracteres para PT ou < 80 para EN (pode ser genuíno, mas verificar)

**Procedimento:**

```python
# 1. Detecção automática
import sqlite3, re
conn = sqlite3.connect('anais.db')
cur = conn.cursor()
cur.execute("""SELECT file, abstract, abstract_en FROM articles
               WHERE seminar_slug = ? AND (abstract IS NOT NULL OR abstract_en IS NOT NULL)""", (slug,))

for file, abs_pt, abs_en in cur.fetchall():
    issues = []
    for field, text in [('abstract', abs_pt), ('abstract_en', abs_en)]:
        if not text:
            continue
        text = text.strip()
        # Truncamento: não termina com pontuação de fim de frase
        if text and text[-1] not in '.?!"\')':
            issues.append(f"{field}: possível truncamento (termina com '{text[-20:]}')")
        # Muito curto
        if len(text) < 100:
            issues.append(f"{field}: muito curto ({len(text)} chars)")
        # PT no abstract_en
        if field == 'abstract_en':
            pt_markers = ['Palavras-chave', 'Resumo', 'O presente trabalho',
                         'Este artigo', 'Este trabalho', 'A pesquisa']
            for marker in pt_markers:
                if marker in text:
                    issues.append(f"abstract_en: possível texto PT ('{marker}')")
                    break
    if issues:
        print(f"{file}: {'; '.join(issues)}")
```

```bash
# 2. Para cada caso suspeito, conferir no fontes/ e corrigir
# Ler nacionais/{slug}/fontes/{file%.pdf}.txt
# Localizar o abstract correto e fazer o trim/substituição no banco
```

**Regra**: Corrigir diretamente no banco. Não deixar para a revisão humana — problemas de truncamento e lixo são mecânicos e devem ser resolvidos nesta fase.

**Script de validação automática** (complementa a detecção manual):

```bash
# Detectar todos os problemas de abstract do seminário
python3 scripts/validar_abstracts.py --slug {slug}

# Corrigir automaticamente swaps abstract PT↔EN
python3 scripts/validar_abstracts.py --slug {slug} --fix-swap
```

O script `validar_abstracts.py` implementa 9 regras de validação aprendidas das revisões humanas anteriores. Rodar **antes** da detecção manual para resolver os problemas mais comuns automaticamente.

### 0.6 Extrair metadados EN (title_en, subtitle_en, abstract_en, keywords_en)

Se o diagnóstico (0.1) mostrar presença de `abstract_en` ≥ 30%, extrair metadados em inglês dos textos:

```bash
python3 scripts/extrair_metadados_en.py --slug {slug} --dry-run
python3 scripts/extrair_metadados_en.py --slug {slug}
```

O script busca nos fontes/ a seção EN de cada artigo (delimitada pelo marcador "Abstract") e extrai:
- **title_en**: título em inglês (entre keywords_PT e "Abstract", ou em ALL CAPS após o header)
- **subtitle_en**: subtítulo (separado do title_en por `: `, ` — ` ou ` – `)
- **abstract_en**: texto do abstract (se ainda não preenchido)
- **keywords_en**: palavras-chave EN (se ainda não preenchidas)

Flags: `--force` re-extrai mesmo se o campo já tem valor; `--only-title` extrai apenas title_en/subtitle_en.

**Nota:** A extração automática não captura todos os títulos EN — muitos PDFs têm o título inline com o abstract ou em formato não-padrão. Os títulos não capturados serão revisados na Fase 1.1c (revisão LLM).

---

## Fase 1 — Revisão automática

O Claude executa verificações automatizadas e aplica correções ao banco **antes** de gerar o HTML de revisão, para que o humano revise o estado já corrigido.

### 1.1a Títulos e subtítulos PT

**Objetivo:** Corrigir capitalização conforme norma brasileira (sentence case com dict.db).

```bash
# 1. Alimentar dicionário com nomes novos
python3 dict/seed_authors.py
python3 dict/seed_titles.py --apply
python3 dict/dump_db.py

# 2. Normalizar
python3 scripts/normalizar_maiusculas.py --slug {slug} --dry-run
python3 scripts/normalizar_maiusculas.py --slug {slug}
```

**Verificação adicional com LLM:** Após a normalização automática, o Claude compara cada título com o PDF original para detectar:
- Nomes próprios de edifícios/lugares que ficaram em minúscula
- Termos genéricos que ficaram em maiúscula indevida
- Subtítulos que deveriam começar com minúscula (ou vice-versa)
- Separação incorreta entre título e subtítulo
- **Expressões consolidadas com toponímico:** "Arquitetura Moderna", "Arquitetura Modernista", "Arquitetura Contemporânea", "Arquitetura Vernacular" etc. são expressões consolidadas e ficam com maiúscula quando referem o movimento/conceito. Porém, quando seguidas de toponímico ou locativo, funcionam como descritivas e devem ficar em **minúscula**:
  - ✅ "Os princípios da Arquitetura Moderna no Brasil" (conceito)
  - ✅ "a arquitetura moderna de Recife" (descritiva + toponímico)
  - ✅ "Patrimônio da Arquitetura Modernista" (conceito)
  - ✅ "a arquitetura modernista em Belém do Pará" (descritiva + toponímico)
  - O dict/normalizer força maiúscula em todas as ocorrências — a revisão LLM deve rebaixar para minúscula quando o contexto é descritivo (tipicamente: "a/da/na arquitetura moderna/modernista de/em [cidade/estado/país]").

Os critérios de capitalização estão em [`docs/regras_dados.md`](regras_dados.md) e na memória do projeto.

**Registro granular de aprendizado:** Durante a revisão LLM, **cada correção e cada aprendizado devem ser salvos em arquivo** progressivamente, à medida que são identificados. Isso evita perder o trabalho numa compactação de sessão.

Arquivo: `revisao/{slug}-titulos-aprendizado.json`

```json
{
  "correcoes": [
    {
      "file": "sdbr06-008.pdf",
      "campo": "title",
      "de": "esplanada em Santos",
      "para": "Esplanada em Santos",
      "motivo": "nome próprio de edifício",
      "dict_acao": "add_nome:Esplanada"
    },
    {
      "file": "sdbr06-019.pdf",
      "campo": "title",
      "de": "Arquitetura Brasileira",
      "para": "arquitetura brasileira",
      "motivo": "termo genérico, não é 'Arquitetura Moderna'",
      "dict_acao": null
    }
  ],
  "dict_additions": {
    "nomes": ["Esplanada", "Pedregulho"],
    "expressoes": ["Plano Agache", "Brutalismo Paulista"],
    "remover": []
  },
  "padroes_confirmados": [
    "'Arquitetura Moderna' sempre maiúscula",
    "'arquitetura' isolada sempre minúscula"
  ]
}
```

**Procedimento:**
1. Analisar títulos em lotes (ex: 10 por vez)
2. **Após cada lote**, salvar as correções e aprendizados no arquivo JSON
3. Ao final de todos os lotes, aplicar correções ao banco e dict_additions ao dict.db
4. Se a sessão for compactada no meio, o próximo ciclo lê o arquivo e continua de onde parou

**Retroalimentação do dicionário:** Após aplicar as correções do LLM, incorporar os aprendizados ao `dict.db` **a partir do arquivo JSON** (campo `dict_additions`):

1. **Novos nomes próprios** (`dict_additions.nomes`):
   - Edifícios, lugares, instituições → adicionar à tabela `nomes` ou `expressoes`
   - Ex: "Esplanada" (nome de edifício), "Vila Operária" (nome próprio)
2. **Novas expressões consolidadas** (`dict_additions.expressoes`):
   - Ex: "Brutalismo Paulista", "Plano Agache"
   - Adicionar à tabela `expressoes` do `dict.db`
3. **Falsos positivos** (`dict_additions.remover`):
   - Palavras que estão no `dict.db` como nome próprio mas não deveriam estar
   - Remover a entrada
4. **Padrões confirmados** (`padroes_confirmados`): registrar em `MEMORY.md` para referência futura

```bash
# Aplicar aprendizados do arquivo JSON ao dict.db:
python3 -c "
import json, sqlite3
with open('revisao/{slug}-titulos-aprendizado.json') as f:
    data = json.load(f)
conn = sqlite3.connect('dict/dict.db')
cur = conn.cursor()
# Adicionar expressões novas
for expr in ['Nova Expressão', ...]:
    cur.execute('INSERT OR IGNORE INTO expressoes (expressao) VALUES (?)', (expr,))
# Adicionar nomes novos
for nome in ['NovoNome', ...]:
    cur.execute('INSERT OR IGNORE INTO nomes (nome) VALUES (?)', (nome,))
conn.commit()
"
python3 dict/dump_db.py
```

### 1.1b Normalizar títulos EN (Title Case)

**Objetivo:** Aplicar Title Case inglês (Chicago/APA) a `title_en` e `subtitle_en`.

```bash
python3 scripts/normalizar_titulos_en.py --slug {slug} --dry-run
python3 scripts/normalizar_titulos_en.py --slug {slug}
```

Regras de Title Case:
- Capitalizar todas as palavras **exceto** artigos (a, an, the), preposições curtas (in, of, at, by, to, for, with, on), conjunções coordenativas (and, but, or, nor)
- **Primeira e última palavra**: sempre maiúscula
- **Primeira palavra após `:` ou `—`**: sempre maiúscula
- **Acrônimos**: preservar ALL CAPS (IPHAN, UNESCO, CIAM) — via `dict.db` categoria `sigla`
- **Nomes próprios**: preservar forma canônica (Brasilia, Niemeyer) — via `dict.db` categorias `nome`, `lugar`

Usa a biblioteca Python `titlecase` com callback que consulta `dict.db`.

### 1.1c Revisão LLM de títulos EN

**Objetivo:** O Claude compara cada `title_en` com o PDF original para detectar:
- Títulos truncados (extração cortou no meio)
- Title Case incorreto em nomes próprios
- Separação errada título/subtítulo
- Título que é na verdade a primeira frase do abstract (falso positivo)
- Artigos com seção EN no PDF mas sem `title_en` no banco (extração não capturou)

Salvar aprendizado em `revisao/{slug}-titulos-en-aprendizado.json`:

```json
{
  "correcoes": [
    {
      "file": "sdbr08-020.pdf",
      "campo": "title_en",
      "de": null,
      "para": "The City of Recife as Artistic Object in the Interventions of Paulo Bruscky",
      "motivo": "título não extraído automaticamente (inline com abstract)"
    }
  ],
  "dict_additions": {
    "nomes": ["Bruscky"],
    "siglas": []
  }
}
```

### 1.2 Referências

**Objetivo:** Limpar, verificar e extrair referências faltantes.

```bash
# Limpeza automática
python3 scripts/clean_references.py --slug {slug} --dry-run
python3 scripts/clean_references.py --slug {slug}

# Verificação
python3 scripts/check_references.py --slug {slug} --summary
```

**Artigos com 0 referências:** Verificar nos PDFs se há seção de referências ou notas de rodapé com citações. Se houver, extrair seguindo o procedimento documentado em `pipeline_tratamento.md` §2.1b (referências) ou §2.1c (notas de rodapé).

**Varredura completa de TODAS as referências:** O `check_references.py` detecta apenas padrões específicos (concatenadas, fragmentos curtos). Ele **não detecta**: notas de rodapé misturadas, agradecimentos, cabeçalhos de seção ("FONTES PRIMÁRIAS:", "Artigos de jornais:"), créditos de ilustração, refs quebradas em múltiplas linhas, nem backfills pendentes com padrões incomuns (`---------`, `––––––`). É obrigatório varrer as referências de **todos os artigos** do seminário, não apenas os sinalizados pelos scripts. Fazer isso programaticamente:

```python
# Verificação completa: backfills, não-refs, fragmentos, quebras de linha
for art in articles:
    for ref in art.references:
        # Backfill pendente (qualquer variante de underscores/traços)
        if re.match(r'^[-–—_.]{2,}', ref.strip()):
            flag("backfill pendente")
        # Não-referência (agradecimentos, créditos, cabeçalhos)
        if any(x in ref.lower() for x in ['crédito', 'ilustraç', 'agradec',
               'fapesp', 'cnpq', 'capes', 'fontes primárias', 'artigos de jornais']):
            flag("possível não-referência")
        # Ref quebrada em linha (começa com minúscula, ou < 30 chars sem ser URL)
        if ref[0].islower() or (len(ref) < 30 and not ref.startswith('http')):
            flag("possível fragmento / quebra de linha")
```

**Meta:** < 2% de problemas por seminário.

### 1.3 Aplicar correções ao banco

Todas as correções das etapas 1.1–1.2 são aplicadas ao `anais.db`. Reportar contagens (N títulos, N refs corrigidas).

**Nota:** Resumos, abstracts e keywords faltantes já foram tratados na Fase 0. A Fase 1 foca apenas em **corrigir** dados existentes (capitalização de títulos, limpeza de refs), não em preencher lacunas.

---

## Fase 2 — Gerar HTML de revisão

```bash
python3 scripts/gerar_revisao_html.py {slug}
```

Gera `revisao/revisao-{slug}.html` com:
- Capa do seminário (se houver)
- Ficha catalográfica
- Artigos agrupados por seção
- Para cada artigo: título, subtítulo, autores (com afiliação), resumo PT, abstract EN, keywords PT/EN, referências

Abrir no navegador para revisão humana.

**Próximo passo:** Executar o [pipeline de revisão humana](pipeline_revisao_humana.md).

---

## Classificação dos seminários por esforço

Diagnóstico gerado em 2026-02-28. Critérios: % de artigos sem abstract, sem referências, sem keywords.

### Revisão leve — 1.307 artigos (52%)

Precisam apenas de normalização automática de títulos + revisão rápida no HTML. Poucos campos faltantes.

| Slug | Arts | s/abs | s/ref | s/kw | Observações |
|------|------|-------|-------|------|-------------|
| sdbr05 | 56 | 0% | 0% | 18% | Correções aplicadas, aguarda revisão humana |
| sdbr11 | 101 | 3% | 3% | 2% | |
| sdbr12 | 82 | 0% | 4% | 0% | |
| sdbr13 | 181 | 5% | 5% | 5% | |
| sdbr14 | 122 | 1% | 3% | 2% | |
| sdbr15 | 101 | 2% | 2% | 1% | |
| sdnne01 | 44 | 0% | 2% | 0% | |
| sdnne02 | 33 | 3% | 9% | 6% | |
| sdnne03 | 41 | 0% | 0% | 7% | |
| sdnne05 | 32 | 0% | 6% | 0% | |
| sdnne07 | 65 | 3% | 8% | 3% | |
| sdnne08 | 41 | 0% | 0% | 2% | |
| sdnne09 | 50 | 0% | 0% | 2% | |
| sdnne10 | 85 | 0% | 4% | 0% | |
| sdsp03 | 74 | 0% | 16% | 1% | |
| sdsp05 | 68 | 0% | 7% | 0% | |
| sdsp06 | 37 | 0% | 3% | 0% | |
| sdsp07 | 43 | 0% | 2% | 0% | |
| sdsp09 | 27 | 0% | 7% | 4% | |
| sdsul06 | 24 | 4% | 0% | 8% | |

### Revisão moderada — 589 artigos (24%)

Lacunas pontuais: keywords faltantes, algumas referências, poucos abstracts ausentes. Requer extração parcial dos PDFs.

| Slug | Arts | s/abs | s/ref | s/kw | Observações |
|------|------|-------|-------|------|-------------|
| sdbr10 | 118 | 22% | 24% | 14% | |
| sdnne04 | 45 | 0% | 27% | 2% | |
| sdnne06 | 104 | 0% | 44% | 1% | 46 artigos só resumo (sem texto completo) |
| sdrj04 | 17 | 6% | 12% | 12% | |
| sdsp08 | 40 | 10% | 8% | 10% | |
| sdsul01 | 48 | 0% | 10% | 98% | Keywords quase totalmente faltantes |
| sdsul02 | 35 | 20% | 3% | 29% | |
| sdsul03 | 39 | 15% | 15% | 23% | |
| sdsul04 | 46 | 7% | 22% | 17% | |
| sdsul07 | 46 | 15% | 2% | 100% | Keywords totalmente faltantes |
| sdsul08 | 51 | 4% | 4% | 100% | Keywords totalmente faltantes |

### Revisão pesada — 611 artigos (24%)

Muitos abstracts e/ou referências faltantes. Requer extração extensiva dos PDFs.

| Slug | Arts | s/abs | s/ref | s/kw | Observações |
|------|------|-------|-------|------|-------------|
| sdbr06 | 64 | 91% | 31% | 22% | Quase todos sem abstract |
| sdbr07 | 62 | 31% | 18% | 34% | |
| sdbr08 | 184 | 49% | 24% | 22% | Maior seminário, muitas lacunas |
| sdbr09 | 170 | 20% | 69% | 20% | 69% sem referências |
| sdmg01 | 26 | 35% | 23% | 31% | |
| sdpr01 | 26 | 31% | 31% | 35% | |
| sdpr02 | 19 | 47% | 0% | 74% | |
| sdrj02 | 19 | 58% | 63% | 100% | |
| sdrj03 | 4 | 0% | 100% | 100% | Apenas 4 artigos |
| sdsul05 | 37 | 30% | 3% | 5% | |

---

## Estratégia de publicação em ondas

Para não bloquear a publicação pelo esforço de revisão dos seminários mais problemáticos:

1. **Onda 1** — Seminários em bom estado (1.307 artigos, 20 seminários): rodar Fase 1 automática + revisão humana rápida. Publicar.
2. **Onda 2** — Seminários com lacunas pontuais (589 artigos, 11 seminários): extrair campos faltantes dos PDFs + revisão humana. Publicar.
3. **Onda 3** — Seminários problemáticos (611 artigos, 10 seminários): extração extensiva, possivelmente com GROBID ou LLM para referências. Publicar.

Cada onda segue o mesmo fluxo (Fases 0-2 automáticas + Fases 3-5 humanas). Os seminários já revisados (sdbr01-07) e os nacionais já publicados no OJS não entram no pipeline.

---

## Notas sobre uso de agentes em background

A Fase 0 envolve leitura e extração de dezenas de arquivos de texto. É tentador delegar tudo a agentes em background, mas na prática os agentes travam frequentemente ao gerar scripts longos de extração. As regras abaixo evitam desperdício de tempo:

### O que funciona em agentes
- **Keywords**: extração por regex simples (buscar "Palavras-chave:" e "Keywords:"), pouca variação → agente funciona bem
- **References**: extração da seção "Bibliografia"/"Referências" no final do texto → agente funciona bem
- **Verificação de truncamento**: detecção por padrão (terminação, comprimento, marcadores PT em EN) → agente funciona bem

### O que NÃO funciona em agentes
- **Abstracts**: extração difícil porque a maioria dos artigos não tem header "Resumo"/"Abstract" em linha separada. O abstract é o bloco de texto entre os dados dos autores e "Palavras-chave:", sem delimitador explícito. Casos especiais frequentes:
  - Abstract EN antes do PT (ordem invertida)
  - "Abstract:" inline na mesma linha do texto (não em linha separada)
  - Artigo em espanhol (com "Resumen") ou francês (com "Résumé")
  - Comunicação curta sem header de abstract
  - Notas de rodapé coladas no final do abstract

### Estratégia recomendada
1. **Primeiro passo**: rodar script de detecção de marcadores em todos os fontes/ (localizar posições de "Resumo", "Abstract", "Palavras-chave", "Keywords" em cada arquivo)
2. **Segundo passo**: extrair automaticamente os casos simples (marcadores em linha separada, padrão claro)
3. **Terceiro passo**: para os casos que falharam, ler manualmente os primeiros 60-80 linhas do fontes/ e extrair com lógica específica

Esse fluxo em 3 passos é mais rápido que delegar tudo a um agente e esperar ele travar.

---

## Referência rápida

| Comando | Fase | Função |
|---------|------|--------|
| `scripts/extrair_metadados_en.py --slug {slug}` | 0.6 | Extrair title_en, subtitle_en, abstract_en, keywords_en |
| `scripts/validar_abstracts.py --slug {slug}` | 0.5 | Validar abstracts (9 regras heurísticas) |
| `scripts/validar_abstracts.py --slug {slug} --fix-swap` | 0.5 | Corrigir swaps abstract PT↔EN |
| `dict/seed_authors.py` + `seed_titles.py --apply` + `dump_db.py` | 1.1a | Alimentar dicionário |
| `scripts/normalizar_maiusculas.py --slug {slug}` | 1.1a | Normalizar títulos PT |
| `scripts/normalizar_titulos_en.py --slug {slug}` | 1.1b | Normalizar títulos EN (Title Case) |
| `scripts/clean_references.py --slug {slug}` | 1.2 | Limpar referências |
| `scripts/check_references.py --slug {slug} --summary` | 1.2 | Verificar referências |
| `scripts/gerar_revisao_html.py {slug}` | 2 | Gerar HTML de revisão |
