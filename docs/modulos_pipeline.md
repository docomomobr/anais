# Módulos Comuns dos Pipelines

Procedimentos detalhados, código, heurísticas e edge cases compartilhados entre os pipelines de [tratamento](pipeline_tratamento.md) e [revisão](pipeline_revisao.md).

Cada seção é um **módulo independente** que pode ser invocado por qualquer pipeline. Os módulos não assumem ordem de execução — o pipeline que invoca é responsável pela sequência.

---

## A. Hierarquia de fontes para extração

A qualidade da extração depende da fonte. Verificar **nesta ordem** antes de qualquer extração:

1. **doc/docx originais** — qualidade máxima. O formato .docx é XML estruturado: preserva estilos de parágrafo (Heading, Title, Normal), negrito, itálico. Com `python-docx` é possível separar título, abstract, keywords e referências **pelo estilo**, sem depender de regex. Os originais podem estar em `fontes/anais/`, organizados por eixo. Arquivos .doc (formato binário antigo) podem ser convertidos para .docx com LibreOffice antes de processar.
2. **pdfplumber** → `fontes_plumber/` — boa qualidade, preserva estrutura tipográfica (separa refs de notas por font_size). Usar quando não há doc/docx.
3. **pdftotext** → `fontes/` — fallback. Não lida com colunas, fragmenta texto.

```bash
# 1. PRIMEIRO: verificar se existem doc/docx/rtf/odt originais
find nacionais/{slug}/fontes/ -name "*.doc" -o -name "*.docx" -o -name "*.rtf" -o -name "*.odt" | wc -l

# Se existem .docx: ler diretamente com python-docx (preserva estilos)
# Se existem .doc: converter para .docx primeiro
#   soffice --headless --convert-to docx --outdir nacionais/{slug}/fontes_doc/ "{arquivo}.doc"
# Mapear nomes dos .docx para IDs dos artigos:
#   - O YAML pode ter campo source_file com o nome do arquivo original
#   - Se não tem, cruzar por autor (familyname no nome do arquivo) ou título
#   - VALIDAR o mapeamento: abrir o docx e confirmar que o título do artigo
#     corresponde ao título no banco. Se dois docx mapeiam para o mesmo autor,
#     usar o título para desambiguar. NUNCA substituir dados sem confirmar.
#   - Registrar o mapeamento no YAML (campo source_file) para reuso futuro
#
# REGRA: Ao substituir refs de um artigo por dados de outra fonte (docx, plumber),
#   SEMPRE comparar o conteúdo antes de sobrescrever. Se a fonte nova tem MENOS
#   refs que o banco, investigar — pode ser extração incompleta. Não sobrescrever
#   cegamente.

# 2. SE NÃO existem doc/docx: extrair com pdfplumber
python3 scripts/extrair_fontes_plumber.py --slug {slug} --profile-only  # calibrar
python3 scripts/extrair_fontes_plumber.py --slug {slug}                 # extrair
```

### A.1 Pdfplumber — output e calibração

O pdfplumber preserva metadados tipográficos (tamanho de fonte, bold, posição Y), permitindo distinguir automaticamente:

- **Corpo** (maior tamanho) vs **abstract/refs** (tamanho intermediário) vs **notas de rodapé** (menor tamanho)
- **Headings** (bold, tamanho > corpo) vs **texto normal**
- **Referências bibliográficas** (após heading "Referências") vs **notas** (após heading "NOTAS" ou na parte inferior da página)

```bash
# Profile: analisa amostra do seminário para calibrar tamanhos
python3 scripts/extrair_fontes_plumber.py --slug {slug} --profile-only

# Extração completa: gera .jsonl por artigo com blocos anotados
python3 scripts/extrair_fontes_plumber.py --slug {slug}
```

**Output:** `{slug}/fontes_plumber/{id}.jsonl` — cada linha é um bloco de texto com campos:
- `page`, `font_size`, `font_name`, `role`, `text`, `bold`, `lines`
- `role`: `body`, `abstract`, `reference`, `footnote`, `heading`, `subheading`, `pagenum`, `small`

**Calibração automática:** O script faz profiling do seminário (amostra de 10 PDFs) para detectar os tamanhos de cada role. Depois adapta per-artigo, recalibrando quando o artigo usa template diferente do seminário. Pós-classificação posicional reclassifica blocos com base em headings semânticos ("Resumo", "Referências", "NOTAS").

### A.2 Uso em outros módulos

- **Verificação de abstracts (§K)**: usar blocos `abstract` do `.jsonl` para detectar truncamento — o abstract termina quando o role muda de `abstract` para `body`
- **Limpeza de referências (§C)**: usar blocos `reference` como fonte preferencial — já exclui notas de rodapé (`footnote`) e corpo (`body`)
- **fix_validation_issues.py**: `find_alt_source()` consulta `fontes_plumber/` como fonte intermediária entre `fontes_doc/` e `fontes/`

`fontes_plumber/` é a **fonte primária**, não complementar. O pdftotext (`fontes/`) serve como fallback, mas o pdfplumber é sempre preferido — especialmente para delimitação de abstract, separação refs/notas, e PDFs com layout em colunas.

---

## B. Extração de referências

### B.1 Norma de citação

Verificar nos fontes/ qual norma de citação predomina no seminário. Isso afeta a extração e split de referências nas fases seguintes.

```python
# Amostrar 10-20 artigos com referências e classificar
import re, json

ABNT_RE = re.compile(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ]{2,},\s+[A-Z]')          # SOBRENOME, Nome
CHICAGO_RE = re.compile(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóú]+,\s+[A-Z]')  # Sobrenome, Nome
FOOTNOTE_RE = re.compile(r'^\d{1,3}\s+[A-Z]')                       # 1 Autor...

for art_id, refs_text in sample:
    refs = json.loads(refs_text)
    abnt = sum(1 for r in refs if ABNT_RE.match(r.strip()))
    chicago = sum(1 for r in refs if CHICAGO_RE.match(r.strip()) and not ABNT_RE.match(r.strip()))
    footnote = sum(1 for r in refs if FOOTNOTE_RE.match(r.strip()))
    # Classificar: ABNT / Chicago / Misto / Footnotes
```

Registrar no diagnóstico:
- **Norma predominante**: ABNT / Chicago / Misto
- **Artigos com footnotes/endnotes**: lista (esses terão notas no campo refs que devem ser removidas)
- **Idiomas das refs**: pt-BR, en, es (afeta os padrões de split)

### B.2 Subetapas para referências faltantes

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

**REGRA**: Ao classificar um artigo como 📄 footnotes ou ⬜ sem refs, verificar **TODAS** as páginas do PDF, não só as últimas 2-3. Alguns artigos têm a seção de referências em páginas intermediárias (ex: sdbr14-122 tinha refs na p.15 de 17). Classificar errado como "footnotes only" causa perda de dados.

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

### B.3 Pós-processamento obrigatório

O script `extrair_fontes_plumber.py` fornece funções de pós-processamento (`post_process_abstract`, `post_process_refs`) que devem ser aplicadas antes de inserir no banco:

1. **Abstract + keywords coladas**: o PDF pode ter "Palavras-chave:" grudado no final do abstract. `post_process_abstract()` separa e retorna `(abstract, keywords)`.
2. **Hifenização de PDF**: "movimen- to" → "movimento". Corrigido automaticamente.
3. **Quebras de linha espúrias**: linhas quebradas por coluna do PDF são juntadas (preserva `\n\n` como parágrafo).
4. **Refs concatenadas**: refs >300 chars com padrão ABNT duplo são splitadas por `post_process_refs()`.
5. **Underscores ABNT**: `________` no início de ref é substituído pelo autor da ref anterior.
6. **Refs curtas**: <25 chars são removidas (lixo de extração).

```python
from scripts.extrair_fontes_plumber import post_process_abstract, post_process_refs

# Ao inserir abstract no banco:
abstract_limpo, keywords_extraidas = post_process_abstract(abstract_bruto)

# Ao inserir refs no banco:
refs_limpas = post_process_refs(refs_brutas)
```

---

## C. Sweep_refs — passadas e heurísticas

### C.1 Visão geral (8 passadas)

| Passada | Ação | Heurística |
|---------|------|------------|
| 0. Lixo grosso | Remover body text, figure captions, headers standalone, NOTAS | `is_body_text()`, `FIGURE_RE`, `SECTION_HEADER_STANDALONE`, `NON_REF_CONTENT` |
| 0b. Headers prefixo | Strip headers de seção prepostos/apostos | `SECTION_HEADER_PREFIXES`: "Escritos ", "Teses e Dissertações ", etc. |
| 0c. Page breaks | Split em marcadores ⏐ + número de página | `PAGE_BREAK_RE`: `\s*[⏐│\|][\uf000-\uf8ff]*\s*\d+\s+` |
| 1. Fragmentos | Juntar à ref anterior | `is_fragment()`: começa com minúscula, ano isolado (`2003.`), URL isolada (`http://...`), `Disponível em:` isolado, curto (<60) com padrão de cidade/ano/página, começa com "In:", "Editora", "vol.", "n." |
| 2. Endnotes | Se contém ref: extrair; senão: remover | `is_numbered_endnote()`: prefixo `^\d{1,3}\s+` seguido de texto classificado por `is_bibliographic_ref()` |
| 3. Split | Separar concatenadas > 300 chars | `split_concatenated_refs()`: boundaries ABNT (`SOBRENOME, Nome`), Chicago (`Sobrenome, Nome`), ano+ponto, publisher (`Press,` `Editora,`), pipe (`\|`) |
| 4. Remoção | Remover não-referências restantes | `is_bibliographic_ref()`: aceita ABNT/Chicago/APA; rejeita se começa com marcador narrativo, tem `has_narrative_structure()` ≥ 3 (PT/EN/ES), ou é nota numerada |
| 5. Body text | Truncar body text do final de refs mistas | `truncate_body_text()`: detecta início de narrativa após dados bibliográficos |
| 6. Near-dupes | Remover near-duplicates | `normalize_ref_for_dedup()`: normaliza pontuação, URLs, meses PT/EN/ES |

### C.2 Passada 0 — lixo grosso

Esses padrões indicam que a extração errou o início da seção de referências e capturou conteúdo que não é ref:

```python
# Figure captions (legendas de figuras capturadas como refs)
FIGURE_RE = re.compile(r'^(Figura|Fig\.?|Figure|Imagem)\s*\d', re.IGNORECASE)

# Section headers standalone (removidos inteiramente)
SECTION_HEADER_STANDALONE = re.compile(
    r'^(Escritos|Livros|Revistas e Periódicos|...)\.?\s*$')

# Body text (>200 chars + narrativa + sem padrão de autor)
def is_body_text(ref):
    return (len(ref) > 200
            and has_narrative_structure(ref)
            and not ABNT_AUTHOR_RE.match(ref)
            and not re.match(r'^[A-Z][a-z]+,\s+[A-Z]', ref))

# Agradecimentos, créditos, CVs, cabeçalhos de subseção
NON_REF_CONTENT = ['agradec', 'crédito', 'ilustraç', 'currículo',
    'fapesp', 'cnpq', 'capes', 'bolsista',
    'fontes primárias', 'artigos de jornais',
    'engenheiro e proprietário']
```

### C.3 Passada 0b — headers de seção

Quando a extração pega um header de subseção bibliográfica ("Escritos", "Teses e Dissertações", "Revistas e Periódicos") junto com a primeira ref daquela subseção, o header fica preposto: `"Escritos Banham, Reyner..."`. A passada 0b detecta e remove o header, preservando a ref. Funciona também para headers no final: `"Rowe, Colin. ... 1999. Revistas e Periódicos"`.

### C.4 Passada 0c — page breaks

Entradas como `"USP. São Carlos, 2003 ⏐ 27 Zein, Ruth Verde..."` contêm marcador de page break (⏐ U+23D0 ou │ U+2502, às vezes com PUA chars) seguido de número de página. A passada 0c divide essas entradas em duas.

### C.5 Passada 2 — NOTAS/footnotes

A extração captura a seção BIBLIOGRAFÍA + a seção NOTAS que vem depois. As NOTAS contêm: texto narrativo, citações abreviadas (Ibid., Op. cit.), comentários. A passada 2 detecta endnotes numeradas e extrai apenas a ref bibliográfica embutida, descartando o número e o texto narrativo.

Problema mais frequente em artigos ES.

### C.6 Passada 5 — body text truncado

Quando body text se juntou ao final de uma referência (ex: `"Tese de doutorado. ETSAB-UPC. Pag. 145. Vilanova Artigas já utilizava..."`), a passada 5 detecta o início da narrativa via regex e trunca a ref no boundary.

### C.7 Passada 6 — near-duplicates

Normaliza refs removendo URLs, pontuação, e mapeando meses PT/EN/ES para forma canônica antes de comparar. Detecta duplicatas que diferem apenas em: presença/ausência de URL, formato do mês (dez/dec/dic), pontuação.

### C.8 has_narrative_structure()

Conta marcadores de discurso em 3 idiomas (PT, EN, ES). Threshold ≥ 3 marcadores = texto narrativo, não referência.

**Safeguard (passada 1):** fragmentos que `is_bibliographic_ref()` classifica como ref legítima NÃO são juntados — preserva refs curtas independentes (ex: "Banham, Reyner. op. cit. p. 361").

---

## D. Revisão LLM de títulos PT

### D.1 Formato obrigatório de análise

Processar **um artigo por vez** — NÃO em lote. Para cada artigo, imprimir título e subtítulo e escrever o julgamento de CADA palavra antes de passar ao próximo. Formato obrigatório:

```
sdbr12-041:
  T: O Habitat moderno em São Luís do Maranhão
  → "Habitat": conceito genérico (moradia), não revista → CORRIGIR para "habitat"
  → "São Luís": cidade → OK
  → "Maranhão": estado → OK
  RESULTADO: O habitat moderno em São Luís do Maranhão
```

Se não escreveu o julgamento de cada palavra, não revisou. Pular direto para a correção sem este registro = revisão não feita.

### D.2 Regras de capitalização

1. Para **cada palavra com maiúscula** (exceto a primeira do título): perguntar "por que está maiúscula?"
   - Nome próprio de pessoa, edifício, instituição, cidade, país → **manter**
   - Nome de revista, periódico, evento → **manter**
   - Expressão consolidada (Arquitetura Moderna, Movimento Moderno, Educação Patrimonial) → **manter**
   - Sigla (SUDENE, IPHAN, GT) → **manter**
   - **Todo o resto → minúscula** (obra, norte/sul como direção, ensino, conservação, tombamento, apartamento, imaginário, intervenção, escolar, edificado, brutalista como adjetivo isolado, arquiteto/a como profissão genérica...)
2. Para **cada palavra com minúscula** que deveria ser maiúscula: perguntar "deveria ser maiúscula?"
   - Nome de cidade (madri → Madri), edifício (congresso nacional → Congresso Nacional), monumento (cristo redentor → Cristo Redentor), periódico (le carré bleu → Le Carré Bleu), apelido (petit paris → Petit Paris), coletivo/grupo artístico (grupo arquitetura nova → Grupo Arquitetura Nova) → **corrigir**
3. Para **cada subtítulo**: verificar que começa com **minúscula** (exceto nome próprio, sigla). "Elementos iniciais..." → "elementos iniciais..."
4. Verificar **separação título/subtítulo** contra o PDF original. Conferir se o split no `:` ou ` — ` corresponde à intenção do autor. Para PDFs escaneados (sem OCR), ler a IMAGEM do PDF para conferir.
5. Verificar **formatação**: hífens soltos ("1970- as" → split em título+subtítulo), travessões, dois pontos
6. Verificar **typos e acentuação**: São Luis → São Luís, preservaçâo → preservação, madri → Madri
7. Verificar **pontuação anômala** que indica separação título/subtítulo mal feita:
   - `//` → split em título + subtítulo
   - `––` ou `--` → substituir por `—` (em-dash) ou split
   - `- ` (hífen+espaço) no meio do título → split ou `—`
   - `:` no meio → pode indicar subtítulo não separado
   - `.` seguido de frase nova no mesmo campo → split título/subtítulo

Para cada correção: aplicar no banco. Se a causa foi o dict.db (forçou maiúscula em palavra comum), remover a entrada do dict.

**Aplicar correções escrevendo o título completo**, não por replace parcial de string. Replace parcial causa erros: falha silenciosamente ("a Obra" ≠ "A Obra"), ou rebaixa a primeira palavra do título para minúscula. Escrever o título inteiro garante que o resultado é o correto.

**Após aplicar, reler o título corrigido** para confirmar. A primeira palavra do título é SEMPRE maiúscula.

**COMPARAR COM O ORIGINAL:** Para cada título, comparar com o docx (python-docx) ou PDF original. O `normalizar_maiusculas.py` rebaixa nomes que não estão no dict — a comparação com o original revela o que foi rebaixado indevidamente. Tipos comuns de erro:
- Nomes de edifícios/equipamentos: Hospital de Clínicas, Centro de Convenções, Estação Rodoviária, Plenário Legislativo
- Nomes de lugares/loteamentos: Jardim do Embaixador, Vila dos Operadores, Campus Central
- Períodos/movimentos históricos: Estado Novo, Novecento
- Nomes de revistas/periódicos: Módulo, A Casa, Le Carré Bleu
- Nomes próprios com grafia incomum: Mallet-Stevens, São Luís (acento)
- Adjetivos gentílicos que não devem ser maiúsculas: capixaba, sul-americano

### D.3 Expressões consolidadas com toponímico

"Arquitetura Moderna", "Arquitetura Modernista", "Arquitetura Contemporânea", "Arquitetura Vernacular" etc. são expressões consolidadas e ficam com maiúscula quando referem o movimento/conceito. Porém, quando seguidas de toponímico ou locativo, funcionam como descritivas e devem ficar em **minúscula**:

- ✅ "Os princípios da Arquitetura Moderna no Brasil" (conceito)
- ✅ "a arquitetura moderna de Recife" (descritiva + toponímico)
- ✅ "Patrimônio da Arquitetura Modernista" (conceito)
- ✅ "a arquitetura modernista em Belém do Pará" (descritiva + toponímico)

O dict/normalizer força maiúscula em todas as ocorrências — a revisão LLM deve rebaixar para minúscula quando o contexto é descritivo (tipicamente: "a/da/na arquitetura moderna/modernista de/em [cidade/estado/país]").

### D.4 Registro de aprendizado (JSON)

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

### D.5 Retroalimentação do dicionário

Após aplicar as correções do LLM, incorporar os aprendizados ao `dict.db` **a partir do arquivo JSON** (campo `dict_additions`):

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
```

---

## E. Revisão LLM de títulos EN e ES

### E.1 Problemas que só leitura real detecta

- Palavras coladas sem espaço ("Destructionorconstruction..." — garbled da extração)
- Lixo vazado de outros campos ("— Unidentified", "NÃO IDENTIFICADO" colado no título)
- Texto de outro idioma misturado (espanhol no title_en, português no title_es)
- Typos de OCR ("Refletion", "Funcional", "T He")
- Acentos faltantes em nomes próprios ("Brasilia" → "Brasília", "Joao" → "João")
- Títulos truncados (extração cortou no meio)
- Títulos garbled (palavras coladas, espaços perdidos)
- Title Case incorreto em nomes próprios (EN) ou sentence case incorreto (ES)
- Separação errada título/subtítulo
- Título que é na verdade a primeira frase do abstract (falso positivo)
- Artigos com seção EN/ES no PDF mas sem `title_en`/`title_es` no banco
- Títulos de artigos locale=es que foram normalizados incorretamente pelo dict.db (calibrado para PT)

### E.2 Regras Title Case EN

Regras de Title Case (Chicago/APA):
- Capitalizar todas as palavras **exceto** artigos (a, an, the), preposições curtas (in, of, at, by, to, for, with, on), conjunções coordenativas (and, but, or, nor)
- **Primeira e última palavra**: sempre maiúscula
- **Primeira palavra após `:` ou `—`**: sempre maiúscula
- **Acrônimos**: preservar ALL CAPS (IPHAN, UNESCO, CIAM) — via `dict.db` categoria `sigla`
- **Nomes próprios**: preservar forma canônica (Brasilia, Niemeyer) — via `dict.db` categorias `nome`, `lugar`

Usa a biblioteca Python `titlecase` com callback que consulta `dict.db`.

### E.3 Regras sentence case ES (RAE)

Sentence case com regras RAE (Real Academia Española). Ver [`docs/regras_cap_es.md`](regras_cap_es.md) para regras completas.
- Maiúscula **somente** para: primeira palavra do título, nomes próprios (pessoas, cidades, países, instituições, edifícios), siglas
- **NÃO** usar expressões consolidadas em maiúscula — em espanhol não existem ("arquitectura moderna", não "Arquitectura Moderna"; "movimiento moderno", não "Movimiento Moderno")
- **NÃO** usar `normalizar_maiusculas.py` — o dict.db é calibrado para PT e forçaria maiúsculas erradas
- Normalizar manualmente ou com revisão LLM específica para ES

**Títulos de artigos em locale=es**: o título principal (`title`) está em espanhol — aplicar regras RAE, não PT. O `normalizar_maiusculas.py` pode ter normalizado incorretamente (dict.db é PT).

### E.4 Registro de aprendizado EN

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

---

## F. Revisão LLM de referências

### F.1 Tipos de problema que escapam às heurísticas

| Tipo | Exemplo | Por que escapa |
|------|---------|----------------|
| Concatenação Chicago | `"...MIT Press, 2003. Sobrenome, Nome. Title..."` | Boundary mixed-case, ref <500 chars |
| Notas sem número | `"O autor argumenta que a técnica construtiva..."` | Não começa com `\d+`, não flaggado como endnote |
| Notas com ref embutida | `"Depoimento de Bucci em: Cotrim, M. (org.)..."` | Começa com nome próprio, parece ref |
| Concatenação backfill | `"______. Obra 1. 1990. ______. Obra 2. 1995."` | Backfill resolveu só o primeiro `______` |
| Fragmento contextual | `"Tese de doutorado. PROPAR-UFRGS, 2005."` | Parece ref independente mas é continuação |
| Near-dupes com variação | Duas versões da mesma ref, uma com URL | `normalize_ref_for_dedup()` não normaliza tudo |
| Headers infiltrados | `"Livros e revistas"` colado como ref | Não está na lista `SECTION_HEADER_STANDALONE` |

### F.2 Procedimento (agente)

1. **PRIMEIRO**: Para cada artigo, ler `fontes_plumber/{id}.jsonl` (se existir) ou `fontes/{id}.txt`. Se fontes/ estiver fragmentado (colunas), rodar pdfplumber antes. **NUNCA tentar reconstruir texto fragmentado do pdftotext.**
2. **SEGUNDO — PASSO CRÍTICO**: No texto fonte, identificar o **ponto de corte** entre BIBLIOGRAFIA e NOTAS. Indicadores:
   - Heading "NOTAS", "Notes", "Notas de fim", "Notas ao texto"
   - Numeração sequencial (1, 2, 3... ou ¹, ², ³...) que inicia após a última ref
   - Quebra na ordem alfabética dos autores
   - Mudança de padrão: refs são "AUTOR. Título. Editora, Ano." / notas são "Ver Fulano (2003)...", "Op. cit.", "Ibid.", narrativa
   - No pdfplumber: mudança de font_size (refs em size maior, notas em size menor)
3. Definir a lista de refs válidas (até o ponto de corte) e descartar notas
4. Dentro das refs válidas, corrigir: concatenações, splits, headers
5. Gravar no banco
6. Ao final, gerar relatório

### F.3 Prompt para agente

```
Review ALL references in {slug}.

CRITICAL FIRST STEP: For each article, identify WHERE THE BIBLIOGRAPHY ENDS
and WHERE THE NOTES BEGIN. Many articles have a BIBLIOGRAPHY section followed
by a NOTES section — the notes MUST be removed. Indicators:
- Numbered entries (1., 2., 3. or ¹²³) after the last proper reference
- "Op. cit.", "Ibid.", "Idem", "Cfr.", "Ver" — these are notes, not refs
- Narrative text ("O autor argumenta...", "Segundo Fulano...") — notes
- Break in alphabetical order of authors
- In fontes_plumber/: font_size change (refs larger, notes smaller)

PREFERRED SOURCE: Use fontes_plumber/{id}.jsonl when available — it separates
reference blocks from footnote blocks by font size. Only fall back to
fontes/{id}.txt when plumber data is unavailable.
If fontes/ text is fragmented (each word on a separate line), the PDF has
column layout — extract with pdfplumber, do NOT try to reconstruct manually.

For each article:
1. Read fontes_plumber/ or fontes/ and identify the bibliography boundary
2. Read current refs from DB
3. Set refs = only the bibliography entries (cut notes)
4. Within bibliography: fix concatenated refs, split refs, junk
5. Write corrected refs to DB
6. Track all changes for final report
```

### F.4 Critérios de decisão LLM

- **Ponto de corte BIBLIOGRAFIA→NOTAS**: o critério mais importante. Identificar ANTES de analisar ref a ref.
- **Concatenação**: duas estruturas bibliográficas na mesma entrada → separar
- **Split**: entrada que começa com minúscula, "In:", URL, ano isolado, cidade/editora → juntar à anterior. Quebra na ordem alfabética indica split.
- **Nota vs ref**: entrada com narrativa, "Op. cit.", "Ibid.", "Ver também", numeração sequencial → remover
- **Header**: entrada que é nome de seção ("Livros", "Revistas e Periódicos") → remover
- **Backfill em-dash**: `—.` ou `–.` entre refs = mesmo autor, obra diferente → separar e prepor o autor

### F.5 Escopo (não só refs)

A revisão LLM NÃO é só de referências. Verificar TODOS os campos:
- **abstract, abstract_en, abstract_es**: ler cada um e julgar:
  - Está no idioma correto? (abstract=PT, abstract_en=EN, abstract_es=ES)
  - Está completo? (não truncado no meio da frase)
  - Não tem lixo? (formulários, tabelas, legendas, dados de questionário, título colado)
  - Não tem outro idioma misturado? (EN no PT, keywords coladas)
  - Faz sentido como resumo acadêmico?
- **keywords, keywords_en, keywords_es**: ler cada lista e julgar:
  - São palavras-chave reais? (não lixo, não texto corrido, não citação ABNT)
  - Estão no idioma correto?
  - Não estão splitadas demais ou aglutinadas?
- Se qualquer campo parece errado → re-extrair do docx (python-docx) ou da imagem do PDF (pdftoppm)
- Se o abstract parece lixo → extrair da imagem do PDF
- **Cada artigo deve ser verificado, sem exceção.** Heurísticas (A23, A25, A14) pegam padrões comuns; o LLM pega o resto.

### F.6 Relatório final

O agente deve produzir:
1. Lista de **todos** os artigos modificados com contagem antes/depois
2. Estatísticas por tipo de correção (concatenação, split, nota cortada, junk removido, backfill resolvido)
3. **Para cada artigo onde cortou notas**: indicar o ponto de corte (ref N → nota N+1)
4. Lista de artigos revisados **sem problemas** (confirma que foram verificados)
5. Análise de padrões: erros que se repetem → candidatos a nova heurística

**Retroalimentação do pipeline**: após a revisão LLM, analisar os padrões de erro encontrados e implementar novas heurísticas no sweep para evitar os mesmos problemas nos seminários seguintes. Testar as melhorias em outro seminário (não no que acabou de ser revisado).

### F.7 Refs longas (A11)

Refs >500 chars que `split_concatenated_refs()` não conseguiu separar (sem boundary ABNT/Chicago claro) devem ser resolvidas na revisão LLM. Para cada uma: ler o PDF/plumber, identificar se é concatenação, lista de fontes/URLs, ou ref legítima longa (capítulo em livro com editora longa). Ações: separar, remover URLs órfãs, remover listas de fontes não-bibliográficas, ou marcar como legítima. Não deixar para revisão humana.

---

## G. Checks de validação A01–A27

### G.1 Tabela de checks

| Check | Descrição | Modo |
|-------|-----------|------|
| A01 | abstract_en existe mas keywords_en falta | REPORT |
| A02 | keywords_en existe mas abstract_en falta | REPORT |
| A03 | abstract_es existe mas keywords_es falta | REPORT |
| A04 | keywords_es existe mas abstract_es falta | REPORT |
| A05 | ~~REMOVIDO~~ — em locale=es, `abstract` já contém o resumo em espanhol; copiar para abstract_es criava ciclo com A21 | — |
| A06 | ~~REMOVIDO~~ — mesma lógica: `keywords` já está em espanhol para locale=es | — |
| A07 | Marcador "Abstract" no fontes/ mas abstract_en vazio | REPORT |
| A08 | Marcador "Keywords" no fontes/ mas keywords_en vazio | REPORT |
| A09 | Marcador "Resumen" no fontes/ mas abstract_es vazio | REPORT |
| A10 | Backfill pendente (refs com `__`, `---`, etc.) | REPORT |
| A11 | Ref > 500 chars (provavelmente concatenada) | REPORT |
| A12 | Não-referência nas refs (créditos, CVs, agradecimentos) | REPORT |
| A13 | URLs órfãs (ref é só URL) | REPORT |
| A14 | Abstract contém email, afiliação ou CV | REPORT |
| A15 | Locale mismatch (abstract em ES mas locale=pt-BR) | AUTO-FIX |
| A16 | Control characters em campos de texto | AUTO-FIX |
| A17 | Referências duplicadas no mesmo artigo | AUTO-FIX |
| A18 | Artigo sem autores vinculados | REPORT |
| A19 | Abstract possivelmente truncado (sem pontuação final) | REPORT |
| A20 | Abstract overflow (>5000 chars — corpo do texto vazado) | AUTO-FIX |
| A21 | abstract_es com lixo EN (marcadores Abstract/Keywords/⏐) ou redundante (== abstract em locale=es) | AUTO-FIX |
| A22 | Refs com body text (>200 chars narrativo) ou figure captions | AUTO-FIX (remove entradas) + LLM (ambíguos) |
| A23 | abstract_en colado no abstract PT (extração capturou PT+EN como bloco único) | AUTO-FIX (separa PT e EN no boundary "Abstract:"/"The present paper"/etc.) |
| A24 | Encoding ruim (caracteres substitutos ĕ/ė, espaços entre letras) — fonte do PDF com encoding não-padrão | REPORT (requer extração via imagem: `pdftoppm` + leitura visual) |
| A25 | Keywords coladas no final de abstract/abstract_en/abstract_es ("Palavras-chave:", "Keywords:", "Palabras clave:") | AUTO-FIX (corta no marcador). **Guard**: se o marcador aparece no meio de uma frase narrativa (precedido por palavra em minúscula), NÃO corta — é parte do texto, não label de seção. |
| A26 | Abstract em idioma diferente do locale: campo `abstract` (PT) contém texto em espanhol (Resumen inserido no campo errado) | AUTO-FIX (move abstract → abstract_es, seta abstract = NULL) |
| A27 | Texto PT colado no abstract_en: extração capturou EN + notas/texto em PT no mesmo campo | AUTO-FIX (corta no boundary EN→PT, detectado por marcadores PT como "Este artigo", "Palavras-chave:") |

### G.2 Responsabilidades

| Check | Descrição | Quem resolve | Método |
|-------|-----------|-------------|--------|
| A01-A04 | Mismatches EN/ES | revisão humana | conferência no PDF |
| A05, A06 | ~~REMOVIDOS~~ — ciclo com A21 | — | — |
| A07 | abstract_en faltante (marcador no fontes/) | fix handler | `extract_abstract_en()` |
| A08 | keywords_en faltante (marcador no fontes/) | fix handler | `extract_keywords_en()` |
| A09 | abstract_es faltante (marcador no fontes/) | revisão humana | extração manual |
| A10 | Backfill pendente (___) | sweep_refs (1.2b) | `clean_references.py` + sweep passada 1 |
| A11 | Ref > 500 chars (concatenada) | sweep_refs (1.2b, threshold 300) + validate (report >500) | `split_concatenated_refs()` passada 3 |
| A12 | Não-referência nas refs | sweep_refs (1.2b) | `is_bibliographic_ref()` passada 4 |
| A13 | URLs órfãs | sweep_refs (1.2b) | passada 1 (fragmentos) |
| A14 | Abstract contaminado | revisão humana | falsos positivos frequentes |
| A15 | Locale mismatch | auto-fix (validate) | detecção de idioma |
| A16 | Control characters | auto-fix (validate) | remoção automática |
| A17 | Refs duplicadas | auto-fix (validate) | dedup automático |
| A18 | Sem autores | revisão humana | investigação manual |
| A19 | Abstract truncado | fix handler | `re_extract_abstract()` (prioriza fontes_doc/) |
| A20 | Abstract overflow (>5000 chars) | auto-fix (validate) | trunca no marcador de keywords |
| A21 | abstract_es com lixo EN | auto-fix (validate) | truncar no marcador de keywords ES, ou NULL se redundante |
| A22 | Refs com body text/figure captions | sweep_refs passada 0 | `is_body_text()`, `FIGURE_RE` |

### G.3 Loop de validação (diagrama)

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
Se restarem após o sweep, são casos ambíguos para revisão LLM (1.2c).
```

### G.4 Critério de saída

O `--loop` **NÃO** re-roda `clean_references.py` nem `--sweep-refs`. Esses devem ser executados **antes** do loop (etapas 1.2a e 1.2b). O loop trata apenas extração de fontes/ (A07, A08, A19) — issues de refs (A10-A13) são resolvidos pelo sweep e pela revisão LLM (1.2c).

**Máximo 5 iterações.** Se não convergir, os issues restantes vão para revisão humana.

**Sem risco de loop infinito:** cada fix handler só aplica correções idempotentes (extrair texto mais longo, remover não-ref, substituir backfill). Nenhuma correção pode criar um issue que outra correção desfaz.

**Critério de conclusão**: os issues restantes são **fatos** (dado não existe no documento original), não **erros** (dado errado ou extraível). Se um issue é corrigível, o script deve corrigi-lo — não deixar para revisão humana.

---

## H. Metadados do seminário

### H.1 Campos e fontes

| Campo | Obrigatório | Fonte | Como preencher |
|-------|-------------|-------|----------------|
| title | ✅ | Capa/ficha catalográfica | Nome completo do evento |
| subtitle | ❌ | Capa | Tema do evento (quando houver) |
| publisher | ✅ | Ficha catalográfica | Editora dos anais. Se não constar, usar "Núcleo Docomomo {Estado/Região}" |
| isbn | ✅ | Ficha catalográfica | Se disponível. Buscar também via Google `"ISBN" "{título do evento}"` |
| date_published | ✅ | Capa/programa | Data do evento (formato YYYY-MM-DD) |
| location | ✅ | Capa/programa | Cidade do evento |
| description | ✅ | Construir | Referência bibliográfica completa dos anais (ABNT) |
| editors | ❌ | Ficha catalográfica / programa / site | Organizadores. Se não constar na ficha, buscar no programa do evento ou no site |

### H.2 build_description() — código

```python
import json, re

EVENT_NAME = {
    'sdbr': 'Seminário Docomomo Brasil',
    'sdnne': 'Seminário Docomomo Norte/Nordeste',
    'sdmg': 'Seminário Docomomo Minas Gerais',
    'sdrj': 'Encontro Docomomo Rio',
    'sdsp': 'Seminário Docomomo São Paulo',
    'sdsul': 'Seminário Docomomo Sul',
    'sdpr': 'Seminário Docomomo Paraná',
}

def get_event_name(slug):
    for prefix, name in EVENT_NAME.items():
        if slug.startswith(prefix):
            return name
    return 'Seminário Docomomo'

def build_description(sem):
    """Gera a ficha catalográfica a partir dos campos do seminário."""
    slug = sem['slug']
    number = int(re.search(r'(\d+)$', slug).group(1))
    event = get_event_name(slug)
    subtitle = sem['subtitle'] or ''
    publisher = sem['publisher'] or ''
    isbn = sem['isbn'] or ''
    year = sem['year']
    location = sem['location'] or ''

    editors = []
    if sem['editors']:
        try:
            editors = json.loads(sem['editors'])
        except (json.JSONDecodeError, TypeError):
            pass

    # Montar
    desc = f'{number}° {event}: anais'
    if subtitle:
        desc += f': {subtitle}'
    desc += ' [recurso eletrônico]'

    if editors:
        if len(editors) <= 3:
            desc += f' / organização: {", ".join(editors)}'
        else:
            desc += f' / organização: {editors[0]} et al.'

    # Imprenta: Cidade: Editora, Ano
    if location and publisher and year:
        desc += f'. {location}: {publisher}, {year}'
    elif location and year:
        desc += f'. {location}, {year}'
    elif publisher and year:
        desc += f'. {publisher}, {year}'

    if isbn:
        desc += f'. ISBN: {isbn}'

    desc += '.'
    return desc

# Verificar
cur.execute('SELECT * FROM seminars WHERE slug = ?', (slug,))
sem = cur.fetchone()
generated = build_description(sem)
current = sem['description'] or ''

print(f'Atual:  {current}')
print(f'Gerada: {generated}')

if current != generated:
    print('→ DIFERENÇA — atualizar:')
    cur.execute('UPDATE seminars SET description = ? WHERE slug = ?',
                (generated, slug))
    conn.commit()
```

### H.3 Regras da ficha catalográfica

- `N°`: usar número ordinal (1°, 2°, ..., não 1º)
- `[recurso eletrônico]`: sempre presente (todos os anais são digitais)
- Editores: até 3 nomes completos; 4+ usa `et al.`
- Cidade: é a cidade de **publicação** (sede da editora), não necessariamente a do evento
- ISBN: manter formato original (com ou sem hífens)
- Ponto final no fim
- Se a ficha original dos anais tiver informações adicionais (DOI, URL, número de páginas), preservar ao final

Exemplos reais:
```
5° Seminário Docomomo Brasil: anais: Arquitetura e Urbanismo modernos: projeto e preservação [recurso eletrônico] / organização: Hugo Segawa. São Carlos: SAP-EESC-USP, 2003. ISBN: 85-85205-43-1.

1º Seminário Docomomo Norte/Nordeste: anais: Arquitetura e Urbanismo Modernos no Norte e Nordeste do Brasil: universalidade e diversidade [recurso eletrônico] / comissão organizadora: Andréa Câmara... [et al.]. Recife: DEA-UNICAP; MDU-UFPE; CECI, 2006.
```

### H.4 "Disponível originalmente em"

Se os anais foram publicados originalmente em site externo ao docomomobrasil.com (ex: site da universidade organizadora, Even3, plataforma do evento), adicionar ao final da description: `Disponível originalmente em: <URL>.` — NÃO usar links do docomomobrasil.com (é o site que estamos substituindo).

### H.5 Procedimento para campos faltantes

1. **Verificar a ficha catalográfica** no PDF dos anais (geralmente nas primeiras páginas, capa ou contracapa)
2. **Se a ficha não tem o dado**, buscar na internet: `"{título do evento}" "{ano}" site:{domínio do evento}`, buscar no Google Scholar, no Catálogo da Biblioteca Nacional
3. **Se não encontrar**, registrar como "não localizado" no `revisao/{slug}-rev-status.md`
4. **Regra do publisher**: quando não indicado na ficha, usar "Núcleo Docomomo {Estado/Região}" para regionais ou "Docomomo Brasil" para nacionais

---

## I. Verificação de autores

### I.1 Extração e comparação (PDF→DB)

A direção da verificação é **fonte → banco**: extrair os nomes do documento original e verificar se cada um existe no banco. O erro mais provável é um autor que está no PDF mas não foi inserido no banco.

Para cada artigo, extrair os nomes dos autores seguindo a **hierarquia de fontes** (mesma ordem de §A):

1. **doc/docx/odt/fodt/rtf** → ler com python-docx ou equivalente (preserva estilos — autor geralmente em estilo específico)
2. **fontes_plumber/** (.jsonl) → blocos com role near "heading" ou entre título e abstract
3. **fontes/** (.txt do pdftotext) → texto entre título e "Resumo"
4. **PDF** → ler página 1 (pdfplumber ou imagem para escaneados)

Para cada autor encontrado na fonte, verificar se existe no banco (comparar familyname). Atenção aos falsos positivos: sobrenomes que aparecem no cabeçalho mas são de pessoas mencionadas no **título** (objeto de estudo, não autor), siglas de universidades no formato "SIGLA, cidade" que parecem "SOBRENOME, Nome", e palavras em inglês de títulos bilíngues.

Verificar:

1. **Completude**: todos os autores do PDF estão no banco? Nenhum faltando?
2. **Nomes**: `givenname` e `familyname` corretos? Partículas (de, da, do) no `givenname`, último sobrenome no `familyname`. Hispânicos: duplo sobrenome.
3. **Afiliação**: preenchida e no formato correto (sigla: `FAU-USP`, `PROPAR-UFRGS`)? Sem títulos acadêmicos, endereços, emails.
4. **Ordem**: a ordem dos autores no banco corresponde à do PDF (primeiro autor = autor principal)?

### I.2 Código de verificação

```python
# Gerar relatório comparativo: autores do banco vs PDF
import sqlite3, pdfplumber, re, json

conn = sqlite3.connect('anais.db')
cur = conn.cursor()

cur.execute("""
    SELECT a.file, a.title,
           GROUP_CONCAT(au.givenname || ' ' || au.familyname, '; ' ) as db_autores,
           COUNT(aa.author_id) as n_db
    FROM articles a
    LEFT JOIN article_author aa ON a.id = aa.article_id
    LEFT JOIN authors au ON aa.author_id = au.id
    WHERE a.seminar_slug = ?
    GROUP BY a.id ORDER BY a.file
""", (slug,))

discrepancias = []
for file, title, db_autores, n_db in cur.fetchall():
    # Ler PDF e extrair autores do cabeçalho
    pdf = pdfplumber.open(f'nacionais/{slug}/pdfs/{file}')
    text = pdf.pages[0].extract_text() or ''
    pdf.close()

    # Contar autores no PDF (entre título e Resumo)
    m = re.search(r'(?:RESUMO|Resumo)', text)
    if m:
        header = text[:m.start()]
        # Heurística: contar nomes próprios no cabeçalho
        # (implementação depende do formato do seminário)

    # Comparar e reportar discrepâncias
    # ...
```

### I.3 Fluxo pós-correção

Se autores novos foram adicionados ao banco, rodar o mesmo fluxo do pipeline_tratamento.md §7.4–7.6:

```bash
# 1. Alimentar dict.db com nomes novos
python3 dict/seed_authors.py

# 2. Deduplicar autores (merge duplicatas: Pilotis + Jaro-Winkler + coautoria)
python3 scripts/dedup_authors.py --dry-run
python3 scripts/dedup_authors.py

# 3. Expandir iniciais (se houver givennames abreviados)
python3 scripts/expand_initials.py --report
python3 scripts/expand_initials.py --pilotis

# 4. Buscar ORCID para autores sem ORCID
# Lembrar: tentar múltiplas combinações de sobrenome (ver memory/feedback_orcid_search.md)
python3 scripts/fetch_orcid.py --search
python3 scripts/fetch_orcid.py --review
python3 scripts/fetch_orcid.py --apply
```

---

## J. Keywords

### J.1 Operações do --clean-keywords

O `--clean-keywords` executa 4 operações em sequência:

1. **Remover template garbage** — instruções de formulário que ficaram no lugar de keywords reais (regex: `máximo \d`, `separados com`, `espaçamento`, `parágrafo de \d+ pt`)
2. **Separar keywords aglutinadas** — detecta separadores internos:
   - `. ` ou `.` sem espaço (quando seguido de maiúscula e keyword > 30 chars)
   - ` / ` (barra)
   - `, ` (vírgula, só se keyword > 40 chars e cada parte ≥ 3 chars)
3. **Trim de pontuação final** — remove `.`, `;`, `,` do final
4. **Dedup** — remove duplicatas case-insensitive (preserva primeira ocorrência)

### J.2 Capitalização por idioma

- **PT**: usar as mesmas regras dos títulos — expressões consolidadas em maiúscula ("Arquitetura Moderna", "Brutalismo"), termos genéricos em minúscula ("concreto armado", "preservação"). Consultar `dict.db` e `MEMORY.md` para as formas canônicas.
- **EN**: Title Case para movimentos e expressões ("Modern Architecture", "New Brutalism"), lowercase para termos genéricos ("aesthetics", "structure"). Nomes próprios preservados.
- **ES**: mesma lógica que PT — expressões consolidadas maiúscula, genéricos minúscula.

A normalização de capitalização é **manual** (não automatizada), porque depende de contexto semântico.

### J.3 Detecção de inconsistências

```python
# Detectar formas inconsistentes (mesmo keyword com casing diferente)
import json, sqlite3
conn = sqlite3.connect('anais.db')
cur = conn.cursor()
for col in ['keywords', 'keywords_en', 'keywords_es']:
    cur.execute(f"SELECT id, {col} FROM articles WHERE seminar_slug = ? AND {col} IS NOT NULL", (slug,))
    kw_forms = {}
    for art_id, kw_json in cur.fetchall():
        for k in json.loads(kw_json):
            lower = k.strip().lower()
            kw_forms.setdefault(lower, set()).add(k.strip())
    inconsistent = {l: f for l, f in kw_forms.items() if len(f) > 1}
    if inconsistent:
        print(f"\n{col}: {len(inconsistent)} inconsistências")
        for lower, forms in sorted(inconsistent.items()):
            print(f"  {lower}: {forms}")
```

Escolher a forma canônica para cada caso e aplicar com UPDATE direto no banco.

---

## K. Verificação de abstracts

### K.1 Problemas (9 tipos)

1. **Truncamento por quebra de página**: o `pdftotext` insere números de página como linhas isoladas (`\n\n3\n\n`). Quando o abstract cruza a fronteira de uma página, o extrator pode parar no número de página e truncar o texto. **Tratamento**: antes de extrair, limpar o texto com `re.sub(r'\n\s*\n\s*\d{1,3}\s*\n\s*\n', '\n\n', text)` para remover números de página soltos. Após extração, verificar se o abstract termina com pontuação de fim de frase.
2. **Truncamento genérico**: abstract termina no meio de uma frase (sem `.`, `?`, `!`, `"`, `)` no final)
3. **Texto PT colado no abstract_en**: palavras em português após o fim do abstract em inglês (padrão mais comum: abstract_en seguido de "A historiografia...", "O presente trabalho...", "Palavras-chave:...")
4. **Keywords vazadas**: "Palavras-chave:", "Keywords:", "Key words:" no final do abstract
5. **Cabeçalhos e metadados**: títulos de seções, nomes de autores, números de página misturados
6. **Início truncado**: abstract começa no meio de uma frase (faltando o início)
7. **Abstract muito curto**: < 100 caracteres para PT ou < 80 para EN (pode ser genuíno, mas verificar)
8. **abstract_es com lixo de cruzamento de idiomas**: a extração não parou no marcador de keywords e incluiu o conteúdo EN (abstract_en, keywords_en, page breaks) dentro do campo abstract_es. Padrão frequente em artigos ES que usam "Palabras-chave:" (forma híbrida PT/ES) em vez de "Palabras clave:". **Detecção**: abstract_es contém "Abstract", "Keywords:", "⏐" (page break marker), ou é significativamente mais longo que o abstract PT. **Tratamento**: limpar abstract_es truncando no marcador de keywords; se locale=es e o abstract principal já contém o texto correto em espanhol, setar abstract_es = NULL (campo redundante).
9. **abstract_es duplicado do abstract**: em artigos ES (locale=es), o abstract principal já contém o resumo em espanhol. Se abstract_es = abstract (mesma string), é redundância — setar abstract_es = NULL.

### K.2 Código de detecção

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

### K.3 Script de validação

```bash
# Detectar todos os problemas de abstract do seminário
python3 scripts/validar_abstracts.py --slug {slug}

# Corrigir automaticamente swaps abstract PT↔EN
python3 scripts/validar_abstracts.py --slug {slug} --fix-swap
```

O script `validar_abstracts.py` implementa 9 regras de validação aprendidas das revisões humanas anteriores. Rodar **antes** da detecção manual para resolver os problemas mais comuns automaticamente.

---

## L. Ciclo de aprendizado

### L.1 Diagrama

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

### L.2 Fontes

- **`dict.db`** (~5.300 entradas): nomes de autores (`seed_authors.py`), nomes próprios extraídos dos títulos (`seed_titles.py`), expressões consolidadas e topônimos adicionados manualmente durante a revisão
- **`MEMORY.md`**: padrões de capitalização confirmados na revisão humana (ex: "Arquitetura Moderna" sempre maiúscula, "modernismo" isolado em minúscula, "Centro" de cidade em maiúscula)
- **`regras_dados.md`**: regras formalizadas a partir de decisões tomadas durante a revisão

Quanto mais seminários forem revisados, menos correções manuais serão necessárias nos seguintes — a revisão automática (Fase 1) fica progressivamente mais precisa.

---

## M. Classificação por esforço

Diagnóstico gerado em 2026-02-28. Critérios: % de artigos sem abstract, sem referências, sem keywords.

### M.1 Leve — 1.307 artigos (52%)

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

### M.2 Moderada — 589 artigos (24%)

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

### M.3 Pesada — 611 artigos (24%)

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

## N. Notas sobre agentes

### N.1 O que funciona

- **Keywords**: extração por regex simples (buscar "Palavras-chave:" e "Keywords:"), pouca variação → agente funciona bem
- **References**: extração da seção "Bibliografia"/"Referências" no final do texto → agente funciona bem
- **Verificação de truncamento**: detecção por padrão (terminação, comprimento, marcadores PT em EN) → agente funciona bem

### N.2 O que NÃO funciona

- **Abstracts**: extração difícil porque a maioria dos artigos não tem header "Resumo"/"Abstract" em linha separada. O abstract é o bloco de texto entre os dados dos autores e "Palavras-chave:", sem delimitador explícito. Casos especiais frequentes:
  - Abstract EN antes do PT (ordem invertida)
  - "Abstract:" inline na mesma linha do texto (não em linha separada)
  - Artigo em espanhol (com "Resumen") ou francês (com "Résumé")
  - Comunicação curta sem header de abstract
  - Notas de rodapé coladas no final do abstract

### N.3 Estratégia recomendada

1. **Primeiro passo**: rodar script de detecção de marcadores em todos os fontes/ (localizar posições de "Resumo", "Abstract", "Palavras-chave", "Keywords" em cada arquivo)
2. **Segundo passo**: extrair automaticamente os casos simples (marcadores em linha separada, padrão claro)
3. **Terceiro passo**: para os casos que falharam, ler manualmente os primeiros 60-80 linhas do fontes/ e extrair com lógica específica

Esse fluxo em 3 passos é mais rápido que delegar tudo a um agente e esperar ele travar.

---

## O. Estratégia de publicação em ondas

Para não bloquear a publicação pelo esforço de revisão dos seminários mais problemáticos:

1. **Onda 1** — Seminários em bom estado (1.307 artigos, 20 seminários): rodar Fase 1 automática + revisão humana rápida. Publicar.
2. **Onda 2** — Seminários com lacunas pontuais (589 artigos, 11 seminários): extrair campos faltantes dos PDFs + revisão humana. Publicar.
3. **Onda 3** — Seminários problemáticos (611 artigos, 10 seminários): extração extensiva, possivelmente com GROBID ou LLM para referências. Publicar.

Cada onda segue o mesmo fluxo (Fases 0-2 automáticas + Fases 3-5 humanas). Os seminários já revisados (sdbr01-07) e os nacionais já publicados no OJS não entram no pipeline.

---

## P. Exemplos de aprendizado

| Seminário | Correção | Falha identificada | Incorporação |
|-----------|----------|-------------------|-------------|
| sdbr10 | "la" maiúscula em título ES | `dict.db` tinha "la" como `nome` (de `seed_authors.py`) | Removido do dict |
| sdbr10 | NOTAS misturadas com refs | sweep_refs sem passada 0 para lixo grosso | Adicionados padrões body text e figure captions |
| sdbr13 | 11 overflows abstract_en | A20 só rodava na Fase 1.5 | Rodar validate --fix na Fase 0.5 |
| sdbr13 | 31 keywords_en com lixo | clean_keywords sem filtros ALL CAPS/junk | KW_JUNK_RE, ALL CAPS ≥15, >80c |
| sdbr13 | abstract ES no campo PT | Não existia check para idioma errado | A26 novo (auto-fix) |
| sdbr13 | PT colado no abstract_en | A23 só detecta EN→PT, não PT→EN | A27 novo (auto-fix) |
