# Fluxo de Tratamento e Revisão de Anais para OJS

Fluxo completo validado nos seminários SP (sdsp03, sdsp05-09) e Rio (sdrj02, sdrj03). Aplicável a qualquer série regional.

---

## Fase 1 — Aquisição e organização dos fontes

### 1.1 Identificar tipo de fonte
| Tipo | Ação | Exemplo |
|------|------|---------|
| CD-ROM / mídia física | Copiar conteúdo para `regionais/{região}/{slug}/` | sdsp03 |
| PDF compilado (e-book) | Salvar em `{slug}/` como `{slug}_anais.pdf` | sdsp05-09 |
| PDFs individuais (site/drive) | Baixar para `{slug}/pdfs/` | sdnne07, sdnne09 |
| Even3 / plataforma estruturada | Exportar metadados + PDFs | sdnne10 |

### 1.2 Copiar para o diretório do projeto
```
regionais/{região}/{slug}/
├── pdfs/                  # PDFs individuais (ou serão gerados pelo split)
├── {slug}_anais.pdf       # PDF compilado (se houver)
└── fontes/                # Arquivos originais (PPT, sumários, etc.)
```

### 1.3 Se houver PDF compilado: split em artigos individuais
- Parsear sumário para identificar páginas de início/fim de cada artigo
- Scripts de parsing são específicos por formato — não tentar parser genérico
- Se o parser falhar 2-3 vezes, construir manualmente (hardcode)
- Usar `qpdf --pages` para split
- Verificar split: contagem de páginas via `pdfinfo` vs campo `pages` no YAML

---

## Fase 2 — Extração de metadados

### 2.1 Extrair metadados de cada PDF
Script: `extrair_metadados_pagina1.py` (ou extração via agente para seminários novos)

Campos a extrair:
- **Título** (pode estar em ALL CAPS)
- **Autores** (nomes, muitas vezes com marcadores de nota *)
- **Resumo** em português (COMPLETO, sem truncar)
- **Abstract** em inglês (se existir)
- **Resumen** em espanhol (se existir)
- **Palavras-chave** / Keywords / Palabras clave
- **Referências bibliográficas** (lista ao final do artigo)
- **Contagem de páginas** (`pdfinfo`)

### 2.2 Checklist pós-extração
- [ ] Todos os PDFs foram processados? (contar vs total esperado)
- [ ] Resumos estão COMPLETOS (não truncados em "...")?
- [ ] Keywords foram capturadas? Quantos artigos sem keywords?
- [ ] Autores foram identificados em todos os artigos?
- [ ] Existem PDFs escaneados (sem texto)? Se sim, rodar `ocrmypdf`

### 2.3 Identificar seções/eixos temáticos
- Fontes: sumário do PDF compilado, programa do evento (PPT, site), caderno de resumos
- Mapear cada artigo à sua seção
- Formatos típicos: "Eixo N — Nome", "Mesa N — Nome", "Comunicações Orais — Tema", "Painéis — Tema"

---

## Fase 3 — Construção do YAML

### 3.1 Montar YAML consolidado
Arquivo: `regionais/{região}/{slug}.yaml`

Seção `issue:` obrigatória:
```yaml
issue:
  slug: sdXX99
  title: Nº Seminário Docomomo Região, Cidade, Ano
  subtitle: Tema do seminário
  description: 'Ficha catalográfica completa (ver 3.1b)'
  year: 2024
  volume: 4        # ver mapeamento de volumes abaixo
  number: 2        # número do seminário na série
  date_published: 'YYYY-MM-DD'
  isbn: '978-...'
  publisher: Nome da Editora   # IMPORTANTE: não confundir com organizadores
  editors:                     # organizadores (pessoas)
  - Nome Completo
  source: URL de origem
  sections:                    # seções pré-definidas com abbrev
  - title: Artigos
    abbrev: ART-sdXX99
  - title: Pôsteres
    abbrev: POST-sdXX99
  - title: Geral              # para editoriais, homenagens
    abbrev: GER-sdXX99
    hide_title: true           # não exibe cabeçalho de seção no OJS
```

**Mapeamento de volumes (decidido 2026-02-10):**

| Volume | Grupo | Slugs |
|--------|-------|-------|
| 1 | Brasil | sdbr01–sdbr15 |
| 2 | Sudeste | sdmg01, sdrj02–04, sdsp03–09 |
| 3 | Norte/Nordeste | sdnne* |
| 4 | Sul | sdsul* |

**Fontes para dados bibliográficos faltantes (ISBN, editora, organizadores):**
- Ficha catalográfica no próprio PDF (geralmente na página 2 ou 4)
- CBL / Agência Brasileira do ISBN: https://www.cblservicos.org.br/isbn/pesquisa/
- ISBN Search internacional: https://isbnsearch.org/
- Catálogo da Biblioteca Nacional: http://acervo.bn.br/

**IMPORTANTE — Formato do título da issue:**
O campo `title` deve seguir o padrão do OJS: `Nº Encontro Docomomo Região, Cidade, Ano` (ex: `2º Encontro Docomomo Rio, Rio de Janeiro, 2012`). O tema do seminário vai no campo `subtitle`.

**IMPORTANTE — Organizadores vs. Editora:**
- `editors` = organizadores (pessoas que organizaram os anais)
- `publisher` = editora (instituição que publicou)

### 3.1b Ficha catalográfica
Adicionar ao arquivo centralizado `revisao/fichas_catalograficas.yaml`:
```yaml
- slug: sdXX99
  ficha: |
    Nº Encontro Docomomo Região: anais: tema [recurso eletrônico] /
    organização: Nomes. Cidade: Editora, Ano. N p. ISBN 978-...
```
O campo `description` do YAML do seminário deve conter a mesma ficha (em 1 linha).
O script `generate_ojs_xml.py` lê as fichas de `revisao/fichas_catalograficas.yaml` para gerar o `<description>` da issue no XML.

### 3.2 Separação e formatação de títulos

Regras completas em `docs/regras_dados.md` §"Regras para títulos e subtítulos". Resumo para o construtor:

1. **Separar título/subtítulo** no construtor (`construir_*.py`), não depois:
   - Dois-pontos: dividir no primeiro `: ` → `title` + `subtitle`
   - Ponto + nova frase: `Hélio Modesto em Fortaleza. Ressonância e resistibilidade` → title + subtitle
   - Travessão como divisor: `Edifício dos arquitetos — uma crítica` → title + subtitle
   - Não separar se `: ` faz parte do sentido (ex: `Brasília: 50 anos de patrimônio`)
2. **Subtítulo começa com minúscula** (exceto nome próprio, sigla, início de frase interrogativa)
3. **Título começa com maiúscula**
4. **Títulos em inglês misturados**: se o subtítulo contém título em inglês, separá-lo em `title_en`/`subtitle_en`
   - Ex: título PT + subtítulo "a critical view of modern heritage" → mover para `subtitle_en`
5. **Travessão**: ` - ` isolado → ` — ` (em-dash). Não tocar em intervalos, compostos, siglas, refs
6. **ALL CAPS**: converter para sentence case. A normalização fina roda na fase 7.2

A normalização automática de maiúsculas (`dict/normalizar.py`) só roda na fase 7.2 — aqui basta separar corretamente e aplicar o sentence case básico.

### 3.3 Estrutura de cada artigo
```yaml
- id: sdXX99-001
  title: Título normalizado
  subtitle: subtítulo (se houver)
  title_en: English title (se existir)
  subtitle_en: english subtitle (se existir)
  tipo: artigo              # artigo | poster | editorial (informativo, não vai pro OJS)
  authors:
  - givenname: Nome
    familyname: Sobrenome
    affiliation: SIGLA-UNIVERSIDADE
    email: sobrenome@exemplo.com    # ver convenção abaixo
    primary_contact: true
  section: Nome da Seção
  locale: pt-BR
  file: sdXX99-001.pdf       # vazio se não houver PDF
  pages: 1-15                # ou pages_count: 15
  abstract: Resumo completo em português
  abstract_en: Full abstract in English (se existir)
  keywords:
  - palavra 1
  - palavra 2
  keywords_en:
  - keyword 1
  - keyword 2
  references:
  - 'AUTOR. Título. Local: Editora, Ano.'
```

**Emails:** OJS exige email para cada autor. Quando não temos o email real, usar `sobrenome@exemplo.com` (domínio reservado RFC 2606). Se houver colisão de sobrenome no mesmo artigo, usar `sobrenome.inicial@exemplo.com`.

### 3.4 Renomear PDFs para padrão
`{slug}-{NNN}.pdf` (ex: sdsp03-001.pdf, sdnne07-042.pdf)

### 3.5 Pré-enriquecimento de nomes de autores
Quando os nomes extraídos são abreviados (ex: filenames com "Adriana Almeida" em vez de "Adriana Leal de Almeida"), cruzar com o banco existente **antes** de gravar o YAML para usar a forma completa:

```python
# No script construir_*.py, após parsear autores:
import sqlite3
db = sqlite3.connect('anais.db')
c = db.cursor()
for author in authors:
    c.execute("""SELECT givenname, familyname FROM authors
        WHERE familyname = ? AND givenname LIKE ?
        ORDER BY LENGTH(givenname) DESC LIMIT 1""",
        (author['familyname'], author['givenname'].split()[0] + '%'))
    row = c.fetchone()
    if row and len(row[0]) > len(author['givenname']):
        author['givenname'] = row[0]
```

Isso evita criar duplicatas que depois precisam ser resolvidas pelo dedup (etapa 7.4). Essencial quando a fonte de metadados (filename, HTML) traz nomes incompletos.

---

## Fase 4 — Limpeza e normalização

### 4.1 Limpeza de keywords (`limpar_keywords.py`)
Problemas comuns:
- Keywords concatenadas com ponto como separador
- Números de página colados no final
- Títulos em ALL CAPS embutidos (heurística: >55% maiúsculas, >12 chars alpha)
- Headers de seminário/seção
- Abstracts inteiros vazando para o campo keywords

**Sempre rodar `--dry-run` primeiro.** Verificar falsos positivos (anos, décadas, nomes de arquitetos).

### 4.2 Normalização de travessões
Hífen isolado (` - `) usado como separador → travessão (` — `, em-dash U+2014).
Aplica-se a: títulos, subtítulos, nomes de eventos, eixos/seções.
**NÃO** substituir em: intervalos numéricos (1930-1960), palavras compostas (art-déco), section_refs (E1-sdbr12), referências bibliográficas.

### 4.3 Normalização de títulos e subtítulos

Norma brasileira (sentence case). Pipeline em 3 passadas via `dict/normalizar.py` + `dict/dict.db` (~4270 entidades):
1. **Palavra a palavra**: siglas, nomes, lugares, áreas, movimentos → forma canônica; resto → minúscula
2. **Expressões consolidadas**: regex multi-palavra (ex: "Movimento Moderno", "Patrimônio Cultural")
3. **Toponímicos contextuais**: adjetivos pátrios capitalizados após movimento/área (ex: "Brutalismo Paulista")

**A normalização roda no banco (Fase 7.2).** Aqui ficam apenas as regras. Ver `docs/regras_dados.md` e `docs/devlog_normalizacao_maiusculas.md`.

### 4.4 Verificação de referências

Detecta erros nas referências extraídas automaticamente:
- **Concatenadas**: múltiplas refs na mesma linha (> 400 chars, padrão "ano. SOBRENOME,")
- **Não-referências**: texto corrido, legendas de figuras, URLs soltas
- **Fragmentos**: refs incompletas ou continuações (< 25 chars, início minúsculo)

```bash
python3 scripts/check_references.py --summary           # resumo por seminário
python3 scripts/check_references.py --slug sdsul04       # detalhe
python3 scripts/check_references.py --type concatenada   # filtrar por tipo
```

Ver `docs/devlog_check_references.md`.

### 4.5 Revisão de autores
Verificar automaticamente:
- [ ] Familyname com múltiplas palavras (exceto nomes hispânicos — ver decisão abaixo)
- [ ] Partículas (de, da, do) no familyname (devem estar no givenname)
- [ ] Givenname vazio ou muito curto
- [ ] Dígitos ou asteriscos nos nomes
- [ ] Texto de afiliação misturado no nome
- [ ] Sufixos Junior/Filho/Neto: familyname = sufixo, restante vai para givenname

**Decisão registrada:** Nomes hispânicos com duplo sobrenome (ex: Vázquez Ramos, Maita Zambrano) mantêm ambos no `familyname`, respeitando a convenção do autor.

### 4.6 Verificação de resumos e abstracts
- [ ] Todos os resumos estão completos (não truncados)?
- [ ] Abstracts em inglês foram extraídos quando existem?
- [ ] Artigos sem resumo: são exceções legítimas (homenagens, editoriais)?

---

## Fase 5 — Revisão humana

### 5.1 Sistema de 3 levas (`revisao/`)

Arquivos em texto puro editáveis com neovim. Cada leva tem `.txt` (editável) + `.orig.txt` (baseline para diff).

**Leva 1 — Fichas catalográficas** (`01_fichas.txt`):
- Dados da issue: title, subtitle, description, year, isbn, editors, publisher
- Apenas seminários regionais (nacionais já publicados e validados no OJS)

**Leva 2 — Seções** (`02_secoes.txt`):
- Seções/eixos com contagem de artigos: `  [ 26] Artigos Completos — Documentação`
- Apenas regionais

**Leva 3 — Títulos e autores** (`03_{slug}.txt`):
```
sdbr13-001
T: Darcy Ribeiro e a Arquitetura
S: o Modernismo como cultura
A: Fabrício Ribeiro dos Santos Godoi

sdbr13-002
T: Periodização na historiografia da Arquitetura no Brasil
S: Bruand, Segawa e Bastos; Zein
A: Taís de Carvalho Ossani
```
- Um arquivo por seminário (nacionais mantidos para revisão por alto)
- Campos: T (título), S (subtítulo), X (seção, se variável), A (autores)

### 5.2 Fluxo de revisão
1. Editar `.txt` com neovim
2. Diff contra `.orig.txt` para identificar mudanças
3. Aplicar mudanças ao YAML (script ou manual)

### 5.3 Itens a conferir
- [ ] Títulos: capitalização correta, separação título/subtítulo, travessão vs. hífen
- [ ] Autores: nomes corretos, ordem correta, partículas no givenname
- [ ] Seções: artigos atribuídos à seção correta
- [ ] Editora vs. organizadores (campos distintos)
- [ ] ISBN correto

---

## Fase 6 — Verificação de PDFs

### 6.1 Checklist de PDFs
- [ ] Cada artigo tem um PDF correspondente
- [ ] Nenhum PDF órfão (sem artigo correspondente)
- [ ] Tamanho > 10KB (não vazio)
- [ ] Contagem de páginas confere com campo `pages`
- [ ] PDF compilado existe (se aplicável)

---

## Fase 7 — Banco de dados e enriquecimento

**IMPORTANTE:** O script padrão `import_yaml_to_db.py` é **destrutivo** (apaga tudo). Para adicionar seminários novos sem perder ORCIDs, variantes e dedup, usar modo incremental.

### 7.0 Git checkpoint ANTES de mexer no banco
```bash
python3 scripts/dump_anais_db.py
git add anais.sql && git commit -m "Checkpoint antes de importar {slug}"
```

### 7.1 Importar YAML para o banco SQLite (incremental)
```bash
# Incremental: só importa os slugs indicados, preserva todo o resto
python3 scripts/import_yaml_to_db.py --incremental --only sdrj02 sdrj03

# NUNCA rodar sem flags para adicionar seminários novos!
# O modo padrão (sem flags) apaga TUDO: ORCIDs, variantes, dedup
```
Flags disponíveis:
- `--incremental`: não apaga dados existentes
- `--only SLUG [SLUG ...]`: importa apenas os slugs indicados (limpa e reimporta só eles)
- Sem flags: reimportação destrutiva completa (só para reconstruir do zero)

### 7.1b Alimentar dicionário com novos nomes (AND)
```bash
# Importar nomes de autores recém-adicionados ao banco
python3 dict/seed_authors.py

# Extrair nomes próprios dos títulos dos artigos
python3 dict/seed_titles.py --apply

# Dump do dicionário atualizado
python3 dict/dump_db.py
```
**OBRIGATÓRIO antes de normalizar.** Sem este passo, o normalizador não reconhece os nomes próprios novos (autores e lugares mencionados nos títulos) e os transforma em minúscula. Os scripts são idempotentes — entradas já existentes no dict.db são ignoradas.

### 7.2 Normalizar títulos no banco
```bash
# Verificar mudanças (sem alterar)
python3 scripts/normalizar_maiusculas.py --dry-run

# Verificar um seminário específico
python3 scripts/normalizar_maiusculas.py --slug sdnne07 --dry-run

# Aplicar
python3 scripts/normalizar_maiusculas.py
```
Usa `dict/normalizar.py` + `dict.db` para capitalização conforme norma brasileira. Se aparecerem falsos positivos, corrigir no `dict/dict.db` — remover a entrada standalone e, se necessário, adicionar como expressão multi-palavra. Ver `docs/devlog_normalizacao_maiusculas.md`.

### 7.3 Verificar referências
```bash
python3 scripts/check_references.py --summary
python3 scripts/check_references.py --slug {slug}
```
Correção requer revisão manual ou re-extração dos PDFs. Ver `docs/devlog_check_references.md`.

### 7.4 Deduplicação de autores (AND)

Pipeline completo documentado em [`docs/dedup_autores.md`](dedup_autores.md): 11 etapas progressivas, da mais segura à mais agressiva. Resultado típico: ~22% de redução.

```bash
# Etapas automáticas (1-9): Pilotis, normalização, auto-merge, partículas, cross-familyname, coautores, afiliação
python3 scripts/dedup_authors.py

# Apenas relatório (sem alterar DB)
python3 scripts/dedup_authors.py --report

# Dry-run
python3 scripts/dedup_authors.py --dry-run
```

Após as etapas automáticas, o script lista os **casos ambíguos** (fase 3). Resolvê-los em duas sub-etapas:

**Etapa 9 — Afiliação em comum:** Compara `article_author.affiliation` dos pares ambíguos. Mesma afiliação + nomes compatíveis = forte indicativo de mesma pessoa. Dados de afiliação nem sempre estão disponíveis.

**Etapa 10 — Revisão por LLM:** O LLM analisa temas dos artigos, coautores, afiliações e período temporal para decidir merge/skip. Pode consultar ORCID/Lattes para desambiguar.

**Etapa 11 — Resolução manual:** Casos que nem o LLM resolve (pai/filho, homônimos, nomes genéricos). Pesquisa Lattes ou consulta direta ao autor.

Resolver ambíguos com SQL (ou script):
```sql
-- Merge: mover artigos do duplicado para o canônico
UPDATE article_author SET author_id = {CANONICAL} WHERE author_id = {DUPE}
  AND article_id NOT IN (SELECT article_id FROM article_author WHERE author_id = {CANONICAL});
INSERT OR IGNORE INTO author_variants (author_id, givenname, familyname, source)
  VALUES ({CANONICAL}, '{gn_dupe}', '{fn_dupe}', 'manual-merge');
DELETE FROM article_author WHERE author_id = {DUPE};
DELETE FROM authors WHERE id = {DUPE};
```

**Regras importantes:**
- Sempre registrar variantes em `author_variants` antes de mergear
- Enriquecer email/orcid do canônico se a variante tem dado que o canônico não tem
- Falsos positivos conhecidos (NÃO mergear): pai/filho, irmãs, homônimos com iniciais diferentes. Ver lista completa em `dedup_autores.md`.

### 7.5 Expansão de iniciais
```bash
python3 scripts/expand_initials.py --report    # relatório
python3 scripts/expand_initials.py --pilotis   # match local (Pilotis)
python3 scripts/expand_initials.py --web       # busca web
python3 scripts/expand_initials.py --apply /tmp/initials_report.json  # aplicar
```

### 7.6 Buscar ORCIDs
```bash
# Pipeline v2.0: OpenAlex → Crossref → ORCID API
python3 scripts/fetch_orcid.py --search              # busca nas APIs
python3 scripts/fetch_orcid.py --search --resume      # retomar interrompida
python3 scripts/fetch_orcid.py --search --recheck-days 180  # re-check antigos
python3 scripts/fetch_orcid.py --scrape-faculty       # raspar corpo docente
python3 scripts/fetch_orcid.py --scrape-faculty --apply
python3 scripts/fetch_orcid.py --review               # revisar candidatos
python3 scripts/fetch_orcid.py --apply                # aplicar ao banco
python3 scripts/fetch_orcid.py --stats                # estatísticas
```
Critérios de aceitação automática: resultado único + afiliação BR. Exclusões em `orcid_exclusions`. URLs de corpo docente em `dict/faculty_pages.yaml`.

### 7.7 Dump do banco
```bash
python3 scripts/dump_anais_db.py     # gera anais.sql (versionado no git)
```

### 7.8 Git commit e push
```bash
git add anais.sql {yamls} {scripts modificados}
git commit -m "Importar {slug}: N artigos, NER, dedup, ORCIDs"
git push
```

### Checklist pós-banco
- [ ] Novos seminários: `SELECT slug, COUNT(*) FROM articles WHERE seminar_slug IN (...) GROUP BY seminar_slug`
- [ ] ORCIDs preservados: `SELECT COUNT(*) FROM authors WHERE orcid IS NOT NULL` (≥ valor anterior)
- [ ] Variantes preservadas: `SELECT COUNT(*) FROM author_variants` (≥ valor anterior)
- [ ] Títulos normalizados (spot check nos novos)
- [ ] Referências verificadas (spot check nos novos)
- [ ] Ambíguos de dedup resolvidos
- [ ] `anais.sql` atualizado e commitado

---

## Fase 8 — Preparação para OJS

**IMPORTANTE:** Gerar XMLs somente APÓS completar toda a Fase 7 (NER, dedup, ORCID). XMLs gerados antes do enriquecimento ficam desatualizados.

### 8.1 Gerar XMLs de importação
Script centralizado: `scripts/generate_ojs_xml.py`

```bash
# Teste (só metadados, 1 XML por seminário):
python3 scripts/generate_ojs_xml.py --slug sdrj02 --outdir xml_test

# Produção (com PDFs em base64, 1 XML por artigo):
python3 scripts/generate_ojs_xml.py --slug sdrj02 --with-pdf --outdir xml_prod
```

O script:
- Lê do `anais.db` (artigos, autores, seções) — por isso precisa rodar APÓS enriquecimento
- Lê fichas de `revisao/fichas_catalograficas.yaml` para `<description>` (NÃO usa o campo `description` do banco)
- Gera títulos de seção únicos por issue (sufixo ` — {slug}`) para evitar colisão OJS
- Respeita `hide_title` das seções
- Mapeia volumes para nomes (1→Brasil, 2→Sudeste, etc.)
- Inclui ORCIDs dos autores quando disponíveis

**Fonte de verdade para `description`:** `revisao/fichas_catalograficas.yaml`. O campo `description` do YAML/banco é redundante — manter sincronizado mas o XML usa as fichas.

### 8.2 Issues e seções são criadas pelo XML
O XML com `published="1"` cria a issue e suas seções automaticamente.
Não é necessário criar manualmente antes da importação.

### 8.3 Upload de capa da edição
Capas em PNG: `regionais/{região}/capas/{slug}.png` ou `nacionais/capas/{slug}.png`.
OJS não aceita SVG como capa — usar PNG.

### 8.4 Galley de edição completa (PDF compilado)

Quando existir um PDF compilado dos anais completos (e-book), anexar à **issue** como galley com label "EDIÇÃO COMPLETA".

**Seminários com PDF compilado:** sdsp05, sdsp06, sdsp07, sdsp08, sdsp09, sdnne07, sdnne09 (e possivelmente outros).

### 8.5 Upload e importação dos artigos
1. Login e obter cookies de sessão
2. Obter CSRF token
3. Para cada XML: upload → importBounce → confirmar resultado
4. Sleep 0.5s entre uploads

---

## Fase 9 — Verificação pós-importação

- [ ] Contagem de artigos por seção confere
- [ ] PDFs acessíveis (baixar e abrir 2-3 amostras)
- [ ] Metadados corretos (títulos, autores, resumos)
- [ ] urlPath da issue funcionando
- [ ] Data de publicação correta
- [ ] Capa da edição (se houver)

---

## Referência rápida de scripts

### Scripts centralizados (`scripts/`)

| Script | Fase | Função |
|--------|------|--------|
| `import_yaml_to_db.py` | 7.1 | Importa YAMLs → SQLite (`--incremental --only SLUG`) |
| `dict/seed_authors.py` | 7.1b | Alimenta dict.db com nomes de autores do anais.db |
| `dict/seed_titles.py` | 7.1b | Extrai nomes próprios dos títulos para dict.db (`--apply`) |
| `dict/dump_db.py` | 7.1b | Gera dict.sql (dump versionável do dicionário) |
| `normalizar_maiusculas.py` | 7.2 | Capitalização conforme norma brasileira via dict/normalizar.py |
| `check_references.py` | 7.3 | Detecta erros em referências (`--summary`, `--slug`, `--type`) |
| `dedup_authors.py` | 7.4 | Dedup autores (Pilotis + Jaro-Winkler + coautoria) |
| `expand_initials.py` | 7.5 | Expande iniciais de givennames |
| `fetch_orcid.py` | 7.6 | Busca ORCIDs via OpenAlex/Crossref/ORCID (`--search --review --apply`) |
| `dump_anais_db.py` | 7.7 | Gera anais.sql (dump versionável) |
| `init_anais_db.py` | — | Cria schema do anais.db |
| `generate_ojs_xml.py` | 8.1 | Gera Native XML para OJS (`--slug --with-pdf --outdir`) |
| `import_ojs.py` | 8.5 | Importa XMLs no OJS (test/prod) |
| `generate_static_pages.py` | — | Gera HTMLs das páginas estáticas |

### Scripts regionais (por diretório)

| Script | Fase | Função | Local |
|--------|------|--------|-------|
| `parsear_sumario_*.py` | 2 | Parseia sumário do PDF compilado | sp/scripts/ |
| `split_pdf.py` | 1 | Divide PDF compilado via qpdf | sp/scripts/ |
| `construir_*.py` | 3 | Constrói YAML quando parser falha | sp/scripts/, sul/scripts/ |
| `extrair_metadados_pagina1.py` | 2 | Extrai resumo/abstract/keywords de PDFs | sp/scripts/ |
| `extrair_metadados_textos.py` | 2 | Extrai de textos brutos (pdftotext) | nacionais/scripts/ |
| `limpar_keywords.py` | 4 | Limpeza de keywords contaminadas | sp/scripts/ |
| `normalizar_afiliacoes.py` | 4 | Normaliza afiliações para siglas | nne/scripts/ |
| `merge_metadados.py` | 3 | Merge metadados extraídos no YAML | nne/scripts/ |

---

## Lições aprendidas

1. **Parsers de sumário são específicos por formato** — não criar parser genérico
2. **Construção manual (hardcode) é legítima** quando parser falha 2-3 vezes
3. **Resumos DEVEM ser extraídos completos** — truncar causa retrabalho
4. **Keywords sempre precisam de limpeza** — a contaminação é regra, não exceção
5. **Normalização de títulos requer iteração** — cada seminário traz nomes próprios novos
6. **Revisão humana ANTES de gerar XML** — corrigir depois do upload é muito mais trabalhoso
7. **Verificar PDFs antes de gerar XML** — confirmar contagem de páginas e existência
8. **Homenageados/editoriais sem resumo são exceção legítima** — documentar no YAML
9. **Distinguir organizadores (editors) de editora (publisher)** — campos diferentes
10. **NUNCA rodar import_yaml_to_db.py sem flags** para adicionar seminários — destrói ORCIDs, variantes e dedup. Sempre `--incremental --only SLUG`
11. **Sempre git checkpoint (dump + commit) antes de mexer no banco** — possibilita restauração via `sqlite3 anais.db < anais.sql`
12. **Seções com hide_title** (ex: "Geral" para editoriais) exigem `hide_title: true` no YAML e coluna no banco
13. **Incluir todos os autores** (professores + bolsistas/colaboradores), não só os principais
14. **Entradas sem PDF** são válidas — usar `arquivo_pdf: ''` e subir só metadados
15. **Palavras ambíguas no dicionário** (nome próprio E substantivo comum) devem ser tratadas como expressões multi-palavra, nunca como entradas standalone
16. **Siglas de 2 letras** (SE, AL, MA, TO) conflitam com palavras comuns — evitar no dict.db
17. **Referências extraídas de PDFs** frequentemente contêm texto corrido, legendas e fragmentos — sempre rodar `check_references.py` após extração
