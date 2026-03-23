# Fluxo de Tratamento e Revisão de Anais para OJS

Fluxo completo validado nos seminários SP (sdsp03, sdsp05-09) e Rio (sdrj02, sdrj03). Aplicável a qualquer série regional.

Para procedimentos detalhados de revisão automática (normalização, extração, validação), ver [pipeline_revisao.md](pipeline_revisao.md). Para revisão humana, ver [pipeline_revisao_humana.md](pipeline_revisao_humana.md).

---

## Regras de execução

As mesmas regras do [pipeline de revisão](pipeline_revisao.md#regras-de-execução) aplicam-se aqui:

1. **R1 — Execução literal.** Cada etapa é obrigatória. Não pular.
2. **R2 — Registro imediato.** Após cada etapa, gravar no `revisao/{slug}-rev-status.md`.
3. **R3 — Gates de transição.** Não avançar sem verificar etapa anterior.
4. **R4 — Hierarquia de fontes.** (1) doc/docx, (2) fontes_plumber/, (3) fontes/ (pdftotext).
5. **R5 — Salvar antes de inserir.** JSON intermediário antes de gravar no banco.
6. **R6 — Registrar correções.** Artigo, campo, antes/depois, causa.
7. **R7 — Retomada.** Ler rev-status — última ✅ — retomar próxima.
8. **R8 — Corrigir, não relatar.** Problema identificado → corrigir na hora.
9. **R9 — Campo vazio ≠ genuinamente ausente.** Confirmar no PDF/docx.
10. **R10 — Nenhum "OK" genérico.** Registrar o que foi feito e o resultado concreto.

---

## Runner

O **runner** (`revisao/{slug}-runner.md`) é o checklist executável do seminário. Para gerar:

```bash
python3 scripts/gerar_runner.py {slug}           # gerar runner de revisão
python3 scripts/gerar_runner.py {slug} --status   # ver progresso
python3 scripts/gerar_runner.py                    # listar seminários
```

Quando existir um runner, **seguir o runner** — os pipelines (este documento e pipeline_revisao.md) são referência de consulta para edge cases.

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

**Hierarquia de fontes (R4):** Verificar nesta ordem. A fonte determina a ferramenta de extração:

| Prioridade | Fonte | Ferramenta | Qualidade |
|------------|-------|-----------|-----------|
| 1 | doc/docx/odt/rtf | `extrair_metadados_doc.py` | Melhor (estilos preservados) |
| 2 | PDF texto | `extrair_fontes_plumber.py` | Boa (roles por font_size) |
| 3 | PDF imagem | `ocrmypdf` → plumber | Razoável |
| 4 | pdftotext | `extrair_metadados_textos.py` | Fallback |

Ver [`modulos_pipeline.md` §A](modulos_pipeline.md#a-hierarquia-de-fontes-para-extração) para o procedimento completo.

**Etapa 1 — Verificar se existem editáveis:**

```bash
find regionais/{região}/{slug}/fontes/ -name "*.doc" -o -name "*.docx" -o -name "*.odt" -o -name "*.rtf" | wc -l
```

**Se existem editáveis** → usar `extrair_metadados_doc.py` (fonte primária):

```bash
python3 scripts/extrair_metadados_doc.py --slug {slug}             # diagnóstico
python3 scripts/extrair_metadados_doc.py --slug {slug} --apply     # extrair e gravar no banco
```

Converte para .docx via LibreOffice, lê com python-docx (preserva estilos de parágrafo), extrai abstract, keywords, refs. Substitui o plumber quando disponível — **NÃO converter docx para .txt** (perde-se a estrutura).

**Se não existem editáveis** (ou para artigos sem docx) → extrair via pdfplumber:

```bash
python3 scripts/extrair_fontes_plumber.py --slug {slug} --profile-only
python3 scripts/extrair_fontes_plumber.py --slug {slug}
```

Gera `fontes_plumber/{slug}-NNN.jsonl` com blocos estruturados (role: heading/body/abstract/reference/footnote).

**NOTA:** Mesmo quando existem editáveis, rodar o plumber para 100% dos artigos — serve como fallback e verificação cruzada.

**OCR para PDFs imagem:** Pôsteres e PDFs escaneados (0 caracteres de texto) precisam de OCR antes do pdfplumber:

```bash
ocrmypdf -l por --force-ocr input.pdf output-ocr.pdf
```

Requer `tesseract-ocr` + `tesseract-ocr-por`. Após OCR, re-rodar pdfplumber no PDF OCR'ado.

Campos a extrair:
- **Título** (pode estar em ALL CAPS)
- **Autores** (nomes, muitas vezes com marcadores de nota *)
- **Resumo** em português (COMPLETO, sem truncar)
- **Abstract** em inglês (se existir)
- **Resumen** em espanhol (se existir)
- **Palavras-chave** / Keywords / Palabras clave
- **Referências bibliográficas** (lista ao final do artigo) — ver §2.1b
- **Contagem de páginas** (`pdfinfo`)

### 2.1b Extrair referências bibliográficas dos PDFs

Cada artigo completo contém uma seção de referências ao final. A extração usa `pdftotext -layout` e parsing da seção "Referências" / "REFERÊNCIAS" / "Bibliografia" / variantes (com e sem acento).

**Não há um script único genérico.** Cada seminário pode exigir adaptações (variantes do heading, formatação do PDF, artefatos). Consultar os scripts existentes como referência e adaptar ao caso:

| Script | Região | Notas |
|--------|--------|-------|
| `regionais/se/scripts/extrair_refs_sp.py` | SP | Aceita slug como argumento. Lógica mais completa (backfill `______`, join URLs, filtro de não-refs). Boa base para novos seminários. |
| `regionais/se/scripts/extrair_referencias_sp.py` | SP | Versão anterior / alternativa |
| `regionais/se/scripts/extrair_metadados_pagina1.py` | SE | Extrai refs junto com outros metadados |
| `nacionais/scripts/extrair_metadados_textos.py` | Nacionais | Extrai de textos brutos (pdftotext pré-gerado) |

**Procedimento:**
1. Verificar se já existe script de extração para o grupo regional
2. Se não, usar `extrair_refs_sp.py` como base e adaptar paths e patterns
3. Variantes comuns do heading: `REFERENCIAS` (sem acento), `Referências Bibliográficas`, `Bibliography`, `References`
4. Após extração, sempre rodar `clean_references.py` (§4.4a) e `check_references.py` (§4.4b)
5. Meta: < 2% de problemas por seminário

### 2.1c Extrair referências de notas de rodapé/endnotes

Quando o artigo não possui seção de "Referências" mas tem notas numeradas (endnotes) ao final, as referências bibliográficas estão misturadas com comentários. Este pipeline extrai, filtra, resolve abreviações e formata as referências.

**Quando usar:** Artigos com 0 refs após a extração padrão (§2.1b) que possuem seção "NOTAS" ao final.

**Classificação prévia dos artigos sem refs:**

| Situação | Ação |
|----------|------|
| Tem seção "NOTAS" com endnotes numeradas | Usar este pipeline |
| Tem seção "Referências Bibliográficas" numerada | Extração direta (§2.1b) |
| Notas inline dispersas no texto (sem seção agrupada) | Geralmente impraticável — pular |
| Relatório institucional / sem notas | Sem refs — pular |

#### Etapa 1 — Localizar e extrair notas

```bash
# Extrair texto do PDF
pdftotext artigo.pdf /tmp/artigo.txt

# Encontrar início das notas
grep -n "^NOTAS\|^Notas\|^NOTES" /tmp/artigo.txt

# Ler do ponto encontrado em diante
# Se layout em duas colunas, pdftotext embaralha a ordem
# Nesse caso, extrair imagens das páginas de notas:
pdftoppm -png -r 200 -f {pag_inicio_notas} -l {ultima_pag} artigo.pdf /tmp/artigo-notas
```

**Dica:** Para artigos com muitas notas (>20), combinar pdftotext (texto legível) + imagens (ordem correta das colunas). Para poucos notes (<10), ler direto das imagens.

#### Etapa 2 — Transcrever e classificar cada nota

Para cada nota numerada, classificar em uma das categorias:

| Categoria | Exemplo | Ação |
|-----------|---------|------|
| **Referência bibliográfica** | `BRUAND, Yves. Arquitetura Contemporânea no Brasil. São Paulo: Perspectiva, 1981.` | **Manter** |
| **Comentário/contexto** | `O Rio de Janeiro é a cidade com maior número de bens tombados...` | **Excluir** |
| **Op. cit.** | `BRUAND, op. cit., p. 24.` | **Excluir** (ref já capturada) |
| **Idem / Ibidem** | `Idem, p. 167.` | **Excluir** (ref já capturada) |
| **Apud** (citação indireta) | `BELLORI, 1672, apud PANOFSKY, 1989.` | **Manter** a obra citante (Panofsky); opcionalmente manter a original (Bellori) |
| **Misto** (comentário + ref) | `A historiadora Mariza Veloso publicou a tese "O tecido do tempo" (PPGAS-UnB, 1992).` | **Extrair** a parte bibliográfica |
| **Nota composta** | `BARTHES, Mitologias, 1982. DELEUZE, Proust e os signos, 1987. TAFURI, Projeto e utopia, 1985.` | **Desmembrar** em refs individuais |

#### Etapa 3 — Resolver op.cit. / idem / ibidem

Manter um registro de qual obra cada nota referencia para garantir que todas sejam capturadas:

```
Nota 7 → DUARTE, Hélio. "O problema escolar..."  ← REF (capturada)
Nota 8 → Idem, p. 5                               ← aponta para nota 7 → já capturada
Nota 9 → Ibidem                                    ← aponta para nota 7 → já capturada
Nota 12 → Duarte, op. cit., p. 6                   ← aponta para nota 7 → já capturada
```

Se a primeira ocorrência de uma obra é via op.cit. (a nota original está fora do trecho extraído), reconstruir a referência a partir do contexto.

#### Etapa 4 — Formatar em ABNT e ordenar

Para cada referência extraída:

1. **Padronizar formato**: `SOBRENOME, Nome. Título. Local: Editora, Ano.`
2. **Completar dados quando possível** (editora, local) sem inventar
3. **Preservar texto original** quando a referência no artigo difere do padrão ABNT — não corrigir erros factuais do autor (ex: atribuição errada), apenas formatar
4. **Ordenar alfabeticamente** por sobrenome do primeiro autor
5. **Deduplicar** dentro do mesmo artigo (mesma obra citada em notas diferentes)

#### Etapa 5 — Aplicar ao banco

```python
import sqlite3, json
conn = sqlite3.connect('anais.db')
c = conn.cursor()
refs_json = json.dumps(ref_list, ensure_ascii=False)
c.execute('UPDATE articles SET references_ = ? WHERE id = ?', (refs_json, art_id))
conn.commit()
```

#### Etapa 6 — Verificar

```bash
python3 scripts/check_references.py --slug {slug} --summary
python3 scripts/clean_references.py --slug {slug} --dry-run
```

#### Volume de trabalho típico

| Artigos com notas | Esforço | Estratégia |
|-------------------|---------|------------|
| ≤10 notas | Leve (minutos) | Ler imagens, transcrever direto |
| 10-20 notas | Médio | pdftotext + imagens, filtragem manual |
| 20-50 notas | Pesado | pdftotext + imagens + rastreamento op.cit. |
| >50 notas | Muito pesado | Dividir em lotes, processar com LLM |

**Caso real — sdbr02:** 22 artigos, dos quais 7 com notas pesadas (8 a 50 notas cada). Pipeline produziu 105 refs dos artigos com notas + 110 refs dos com bibliografia direta = 215 refs totais. Artigos sem refs (3/22) eram relatório institucional ou textos sem notas.

### 2.1d Extrair metadados EN

```bash
python3 scripts/extrair_metadados_en.py --slug {slug} --dry-run
python3 scripts/extrair_metadados_en.py --slug {slug}
```

Extrai `title_en`, `subtitle_en`, `abstract_en`, `keywords_en` dos PDFs. Suporta `fontes/` (.txt) e `fontes_plumber/` (.jsonl). Para plumber, usa extração estruturada com verificação de blocos adjacentes (role=footnote/small) para continuação de abstract_en.

Rodar se ≥30% dos artigos têm abstract_en ou se os PDFs têm seções em inglês.

### 2.2 Checklist pós-extração
- [ ] Todos os PDFs foram processados? (contar vs total esperado)
- [ ] `fontes_plumber/` gerado para 100% dos artigos?
- [ ] PDFs escaneados passaram por OCR (`ocrmypdf`)?
- [ ] Resumos estão COMPLETOS (não truncados em "...")?
- [ ] Keywords foram capturadas? Quantos artigos sem keywords?
- [ ] Autores foram identificados em todos os artigos?
- [ ] Metadados EN extraídos quando existentes?

### 2.3 Identificar seções/eixos temáticos

Verificar nesta ordem (hierarquia de fontes para seções):
1. `fontes/` do seminário (HTML/XML de DVDs, sumários, programas)
2. Folha de rosto dos artigos (cabeçalho do PDF indica eixo/sessão)
3. Site original do evento (campo `source` na tabela `seminars`)
4. Busca na internet / Wayback Machine
5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
6. Caderno de resumos

Formatos típicos: "Eixo N — Nome", "Mesa N — Nome", "Sessão N — Nome", "Comunicações Orais — Tema", "Painéis — Tema"

Fontes das seções documentadas em [`docs/fontes_secoes.md`](fontes_secoes.md).

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

Para verificação e geração automática da ficha catalográfica, ver [`modulos_pipeline.md` §H](modulos_pipeline.md#h-metadados-do-seminário).

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

### 4.4 Limpeza e verificação de referências

Sub-pipeline em 3 etapas: limpeza automática → detecção → correção manual/LLM.

#### 4.4a — Limpeza automática (`clean_references.py`)

Script reutilizável que corrige padrões sistemáticos. **Rodar logo após a extração (Fase 2) ou após importação no banco (Fase 7.1).**

```bash
python3 scripts/clean_references.py --slug sdnne01 --dry-run   # preview
python3 scripts/clean_references.py --slug sdnne01              # aplicar
python3 scripts/clean_references.py                              # banco inteiro
```

Operações automáticas:

1. **Split de underscores ABNT**: Na convenção ABNT, `______` (6+ underscores) substitui o nome do autor quando há obras consecutivas do mesmo autor. O pdftotext extrai tudo em uma linha só. O script separa em referências individuais.
   - Exemplo: `SEGAWA, Hugo. Arquiteturas... ______. A pesada herança...` → 2 refs
2. **Backfill de autores**: Refs que começam com `______` recebem o nome extraído da ref anterior.
   - Exemplo: `______. A república ensina a morar...` → `CORREIA, Telma de Barros. A república ensina a morar...`
3. **Join de URLs órfãs**: URLs em linha separada são juntadas à ref anterior (`Disponível em` + URL).

O script é **idempotente** (seguro rodar múltiplas vezes) e **não altera refs que já estão corretas**.

#### 4.4b — Detecção de problemas (`check_references.py`)

Detecta erros restantes após a limpeza automática:
- **Concatenadas**: múltiplas refs na mesma linha (> 400 chars, padrão "ano. SOBRENOME,")
- **Não-referências**: texto corrido, legendas de figuras, URLs soltas
- **Fragmentos**: refs incompletas ou continuações (< 25 chars, início minúsculo)

```bash
python3 scripts/check_references.py --summary           # resumo por seminário
python3 scripts/check_references.py --slug sdsul04       # detalhe
python3 scripts/check_references.py --type concatenada   # filtrar por tipo
```

Meta: **< 2% de problemas** por seminário. Ver detalhes das heurísticas em `docs/devlog_check_references.md`.

#### 4.4c — Sweep completo de referências

Após limpeza base e detecção, rodar varredura em 8 passadas. Ver [`modulos_pipeline.md` §C](modulos_pipeline.md#c-sweep_refs--passadas-e-heurísticas) para heurísticas detalhadas.

```bash
python3 scripts/fix_validation_issues.py --slug {slug} --sweep-refs --dry-run
python3 scripts/fix_validation_issues.py --slug {slug} --sweep-refs
```

#### 4.4d — Revisão LLM de referências

**Para artigos com notas de rodapé em vez de bibliografia:** ver §2.1c (pipeline de extração de referências de notas).

**Revisão LLM sistemática — OBRIGATÓRIA.** Após a limpeza automática (4.4a-c), fazer revisão LLM de TODAS as referências de TODOS os artigos, confrontando com o plumber:

1. Para CADA artigo: ler o plumber inteiro
2. Identificar a boundary BIBLIOGRAFIA → NOTAS (passo crítico)
3. Confrontar refs no banco com refs no PDF
4. Corrigir na hora (R8): splits, joins, refs faltantes, lixo

Ver [`modulos_pipeline.md` §F](modulos_pipeline.md#f-revisão-llm-de-referências) para o procedimento LLM completo, prompt e critérios de decisão.

Padrões comuns de correção:
- **Refs de jornal/revista sem autor pessoal** concatenadas — split manual
- **Texto corrido** (corpo do artigo, notas de rodapé, biografias) — remove/truncate
- **Refs garbled** (texto de outra seção) — replace com texto correto
- **Fragmentos pós-split** (editora/ano quebrados) — join à ref anterior

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

Ver [`modulos_pipeline.md` §K](modulos_pipeline.md#k-verificação-de-abstracts) para os 9 tipos de problema de abstracts e código de detecção automática.

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

### 7.0 Git checkpoint + rev-status

```bash
python3 scripts/dump_anais_db.py
git add anais.sql && git commit -m "Checkpoint antes de importar {slug}"
```

Criar `revisao/{slug}-rev-status.md` com o template do [pipeline de revisão](pipeline_revisao.md#template-do-rev-status). Atualizar progressivamente a cada etapa (R2).

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

Para revisão LLM de títulos (PT, EN, ES), ver [`modulos_pipeline.md` §D](modulos_pipeline.md#d-revisão-llm-de-títulos-pt) e [§E](modulos_pipeline.md#e-revisão-llm-de-títulos-en-e-es).

### 7.2b Retroalimentar dicionário após revisão LLM

Quando um LLM (ou revisão humana) corrige títulos que o normalizador automático não acertou, as correções devem ser incorporadas ao `dict.db` para beneficiar os seminários seguintes:

1. **Novos nomes próprios** (capitalizados pelo LLM): adicionar à tabela `nomes` ou `expressoes`
2. **Novas expressões consolidadas**: adicionar à tabela `expressoes`
3. **Falsos positivos** (o normalizador capitalizou algo indevidamente): remover ou ajustar no `dict.db`

```bash
# Após aplicar correções do LLM:
python3 dict/dump_db.py
```

Este ciclo de retroalimentação é cumulativo: cada seminário processado melhora o normalizador para os seguintes. Ver ciclo de aprendizado em [`modulos_pipeline.md` §L](modulos_pipeline.md#l-ciclo-de-aprendizado).

### 7.3 Limpar e verificar referências
```bash
# Limpeza automática (underscores ABNT, URLs órfãs)
python3 scripts/clean_references.py --slug {slug} --dry-run
python3 scripts/clean_references.py --slug {slug}

# Verificação de problemas restantes
python3 scripts/check_references.py --slug {slug} --summary
python3 scripts/check_references.py --slug {slug}
```
Ver § 4.4 para o sub-pipeline completo de limpeza de referências.

### 7.3b Sweep completo de referências
Após a limpeza base (7.3), rodar a varredura completa em 8 passadas:

```bash
python3 scripts/fix_validation_issues.py --slug {slug} --sweep-refs --dry-run
python3 scripts/fix_validation_issues.py --slug {slug} --sweep-refs
```

Resolve: lixo grosso, headers infiltrados, page breaks, fragmentos, endnotes, concatenadas, body text, near-dupes. Ver [`modulos_pipeline.md` §C](modulos_pipeline.md#c-sweep_refs--passadas-e-heurísticas) para detalhes das passadas e heurísticas.

Após o sweep, re-rodar backfills (o sweep pode criar novos ao splittar refs):

```bash
python3 scripts/clean_references.py --slug {slug}
```

### 7.3c Verificar abstracts
Rodar auto-fixes e verificar truncamento, lixo e contaminação de idiomas:

```bash
python3 scripts/validate_metadata.py --slug {slug} --fix
```

Detecta e corrige: overflows (A20), keywords coladas (A25), idioma errado (A26), PT no EN (A27). Ver [`modulos_pipeline.md` §K](modulos_pipeline.md#k-verificação-de-abstracts) para os 9 tipos de problema e código de detecção.

**Regra — Verificar idioma ao inserir abstracts:** texto em espanhol → `abstract_es`, não `abstract`.

### 7.3d Limpar keywords

```bash
python3 scripts/fix_validation_issues.py --slug {slug} --clean-keywords --dry-run
python3 scripts/fix_validation_issues.py --slug {slug} --clean-keywords
```

Resolve: template garbage, split de keywords aglutinadas, trim de pontuação, dedup. Ver [`modulos_pipeline.md` §J](modulos_pipeline.md#j-keywords) para detalhes.

### 7.3e Validação de metadados (loop)

```bash
python3 scripts/fix_validation_issues.py --slug {slug} --loop
```

Loop: validate_metadata --fix (auto-fixes A15–A27) → fix handlers (A07 abstract_en, A08 keywords_en, A19 abstract truncado) → repete até convergir (max 5 iterações). Ver [`modulos_pipeline.md` §G](modulos_pipeline.md#g-checks-de-validação-a01a27) para a lista completa de checks.

### 7.3f Revisão LLM final — TODOS os artigos × TODOS os campos

**OBRIGATÓRIA.** Para CADA artigo, ler o plumber inteiro e confrontar CADA campo (título, subtítulo, abstract, abstract_en, keywords, keywords_en, title_en, refs) com o texto do PDF. Corrigir na hora (R8). Registrar resultado de cada artigo no runner.

Esta etapa é o gate final antes de gerar o HTML de revisão. Pega problemas que as heurísticas não detectam: truncamentos sutis, refs faltantes, subtítulos não separados, keywords ausentes mas presentes no PDF.

Ver [pipeline_revisao.md §1.10](pipeline_revisao.md) para procedimento detalhado.

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

### 7.8 Gerar conteúdo Hugo
```bash
python3 scripts/db2hugo.py --seminar {slug}
```
Gera as páginas do seminário em `site/content/{ambito}/{slug}/`. Para revisar localmente: `cd site && hugo server`.

### 7.9 Git commit e push
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

**Após a Fase 7, gerar o HTML de revisão e submeter à revisão humana:**

```bash
python3 scripts/validate_metadata.py --slug {slug} --fix
python3 scripts/gerar_revisao_html.py {slug}
sqlite3 anais.db .dump > anais.sql
git add anais.sql revisao/{slug}-* && git commit -m "{slug} revisão automática"
```

→ Próximo: [pipeline de revisão humana](pipeline_revisao_humana.md)

---

## Fase 8 — Aprendizado pós-revisão

Após a revisão humana, cada correção manual é analisada para melhorar o pipeline cumulativamente. Ver [pipeline_revisao.md Fase 3](pipeline_revisao.md) para procedimento detalhado.

### 8.1 Diagnóstico unificado
Agregar TODAS as correções (automáticas + humanas) e identificar causa raiz de cada uma. Por que o pipeline não resolveu?

### 8.2 Atualizar dict.db
- **Remover** palavras genéricas que o dict força maiúscula (ex: `modernista`, `jardim`)
- **Adicionar** nomes próprios novos encontrados durante a revisão
- **Adicionar** expressões consolidadas confirmadas (ex: `Assembleia Legislativa`)

### 8.3 Atualizar scripts
Se ≥3 artigos têm o mesmo erro não coberto pelas heurísticas → corrigir o script.

### 8.4 Atualizar pipeline
Se a revisão revelou gaps na ordem de execução → ajustar a documentação.

### 8.5 Verificar
Dry-run normalizar (verificar que as correções da revisão humana não regridem), validate 0 issues, dedup 0 merges.

### 8.6 Registrar aprendizado
Criar `revisao/{slug}-aprendizado-revisao.json` com correções automáticas e humanas, causas raiz, bugs corrigidos.

### 8.7 Revisão de engenharia
Auditar TODOS os scripts usados no pipeline (usar Opus). Verificar: json.loads sem guard, SQL sem parâmetros, edge cases com valores nulos.

### 8.8 Fechar

```bash
python3 scripts/dump_anais_db.py
python3 dict/dump_db.py
git add anais.sql dict/dict.sql revisao/{slug}-*
git commit -m "{slug} revisão completa (Fases 0-8)"
```

Atualizar CLAUDE.md (tabela de seminários revisados) e `docs/pipeline_revisao_humana.md` (tabela de seminários).

**Após a Fase 8, o seminário está pronto para publicação** (site Hugo + Zenodo). O pipeline de produção via OJS foi arquivado em `docs/archive/pipeline_producao_ojs.md`.

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
| `clean_references.py` | 7.3 | Limpeza automática de refs: split underscores ABNT, backfill autores, join URLs |
| `check_references.py` | 7.3 | Detecta erros restantes em referências (`--summary`, `--slug`, `--type`) |
| `dedup_authors.py` | 7.4 | Dedup autores (Pilotis + Jaro-Winkler + coautoria) |
| `expand_initials.py` | 7.5 | Expande iniciais de givennames |
| `fetch_orcid.py` | 7.6 | Busca ORCIDs via OpenAlex/Crossref/ORCID (`--search --review --apply`) |
| `dump_anais_db.py` | 7.7 | Gera anais.sql (dump versionável) |
| `extrair_metadados_doc.py` | 2.1 | Extrai metadados de editáveis (doc/docx/odt/rtf) via python-docx (`--apply`, `--slug`) |
| `extrair_fontes_plumber.py` | 2.1 | Extrai texto estruturado dos PDFs via pdfplumber (`--profile-only`, `--slug`) |
| `extrair_metadados_en.py` | 2.1d | Extrai title_en, abstract_en, keywords_en dos PDFs |
| `validate_metadata.py` | 7.3c | Validação abrangente: cruzamentos idioma, backfills, refs longas (`--fix`, `--slug`) |
| `fix_validation_issues.py` | 7.3 | Sweep refs, clean keywords, loop validação (`--sweep-refs`, `--clean-keywords`, `--loop`) |
| `gerar_revisao_html.py` | 7 | HTML de revisão por seminário (capa, ficha, artigos por seção) |
| `gerar_runner.py` | — | Gera/consulta runners (checklists executáveis). `--status`, `--type producao` |
| `init_anais_db.py` | — | Cria schema do anais.db |

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
18. **Artigos com notas de rodapé em vez de bibliografia** exigem pipeline específico (§2.1c) — filtrar comentários, resolver op.cit./idem, desmembrar notas compostas, formatar e deduplicar. Para volumes antigos (sdbr01-02), esse é o padrão dominante
19. **pdftotext em layout de duas colunas** embaralha a ordem das notas — sempre conferir com imagens (`pdftoppm`) quando a numeração parece fora de sequência
