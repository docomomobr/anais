# Anais Docomomo Brasil — Documentação do Projeto

Projeto de preservação digital e publicação aberta dos anais dos seminários Docomomo Brasil (nacionais e regionais), abrangendo mais de duas décadas de produção acadêmica sobre documentação e conservação do patrimônio da Arquitetura Moderna brasileira.

---

## 1. O Docomomo e seus seminários

### O que é o Docomomo

O **Docomomo** (International Committee for Documentation and Conservation of Buildings, Sites, and Neighbourhoods of the Modern Movement) é uma organização internacional fundada em 1988 na Holanda, dedicada à documentação e conservação da Arquitetura e do Urbanismo Modernos. O Docomomo Brasil é o representante nacional, ativo desde os anos 1990.

### Os seminários

O Docomomo Brasil promove **seminários acadêmicos periódicos** em que pesquisadores apresentam trabalhos sobre documentação, conservação, intervenção e história da Arquitetura Moderna no Brasil. Existem duas escalas de eventos:

- **Seminários nacionais** (sdbr01–sdbr15): bianuais, itinerantes pelas capitais brasileiras, realizados desde 1995. São os maiores e mais consolidados, com 37 a 79 artigos por edição.
- **Seminários regionais**: organizados por núcleos regionais do Docomomo, com periodicidade e abrangência variáveis:
  - **Norte/Nordeste** (sdnne01–sdnne10): desde 2006, abrangendo estados do Norte e Nordeste.
  - **Sudeste** (sdmg01, sdrj02–04, sdsp03–09): Minas Gerais, Rio de Janeiro e São Paulo. O de São Paulo é o mais ativo.
  - **Sul** (sdsul01–sdsul08, sdpr01–02): estados do Sul do Brasil, incluindo dois seminários paranaenses independentes.

### Os anais

Os **anais** são as publicações que reúnem os artigos apresentados em cada seminário. Historicamente, foram publicados em formatos variados — CDs-ROM, livros impressos, PDFs compilados, plataformas de eventos online — sem padronização de metadados, sem identificadores persistentes (DOIs) e, em muitos casos, sem acesso público. Este projeto reúne, organiza e republica esses anais de forma aberta e padronizada.

### Números atuais

| Âmbito | Seminários | Artigos |
|--------|-----------|---------|
| Nacional | 15 | ~857 |
| Norte/Nordeste | 10 | ~540 |
| Sudeste | 10 | ~397 |
| Sul | 10 | ~406 |
| **Total** | **45** | **~2670** |

O banco de dados reúne **2472 autores** únicos (após deduplicação), dos quais **1206 (49%)** possuem ORCID identificado.

---

## 2. Onde estavam os anais: tipos de fonte

Os anais dos seminários Docomomo nunca tiveram um repositório centralizado. Cada edição foi publicada de forma independente, em formatos e suportes variados. A primeira etapa do projeto é localizar e coletar essas fontes.

### Tipos de fonte encontrados

| Tipo | Descrição | Exemplos |
|------|-----------|----------|
| **CD-ROM** | Mídia física distribuída no evento, com PDFs individuais ou compilados | sdsp03, sdbr01–sdbr04 |
| **PDF compilado (e-book)** | Documento único contendo todos os artigos sequencialmente, com sumário | sdsp05–sdsp09, sdsul01–sdsul08 |
| **PDFs individuais (site/drive)** | Artigos separados hospedados em sites institucionais ou Google Drive | sdnne07, sdnne09 |
| **Plataforma de eventos (Even3)** | Metadados estruturados + PDFs, com exportação disponível | sdnne10 |
| **Documentos Word** | Artigos em .doc/.docx, sem versão PDF | sdpr01, sdpr02 |
| **Site WordPress do Docomomo** | Alguns seminários tinham artigos hospedados no site institucional | sdbr11–sdbr15 |
| **Acervo pessoal dos organizadores** | Material não publicado online, obtido por contato direto | sdnne06, sdnne04 |

### Situação por grupo

**Seminários nacionais (sdbr01–sdbr15):** As fontes mais antigas (sdbr01–sdbr04) estavam em CDs-ROM. Os intermediários (sdbr05–sdbr10) eram PDFs compilados obtidos com organizadores. Os mais recentes (sdbr11–sdbr15) estavam no site WordPress ou em plataformas de eventos.

**Norte/Nordeste (sdnne01–sdnne10):** Grande variação. Alguns tinham PDFs individuais em sites institucionais (sdnne07, sdnne09), outros eram PDFs compilados (sdnne01–sdnne05), e os mais recentes usavam plataformas (sdnne10 no Even3). O sdnne06 foi particularmente difícil: os originais foram obtidos diretamente com os organizadores, e 46 dos 104 artigos existem apenas como resumos.

**Sudeste (sdmg01, sdrj02–04, sdsp03–09):** Os de São Paulo eram PDFs compilados (e-books) com sumários bem estruturados. Os do Rio e de Minas vinham de fontes mais dispersas.

**Sul (sdsul01–08, sdpr01–02):** Predominância de PDFs compilados. Os paranaenses (sdpr01–02) vieram como documentos Word.

### Fontes não localizadas

Dois seminários não puderam ser localizados até o momento: **sdsp04** e **sdrj01**. O sdrj03 possui apenas 4 artigos recuperados.

---

## 3. O processo de trabalho

### 3.1 Coleta dos originais

O ponto de partida é obter o material bruto de cada seminário:

1. **Localizar a fonte**: CDs, sites, drives, contato com organizadores.
2. **Copiar para o repositório**: Cada seminário tem um diretório próprio em `regionais/{grupo}/{slug}/` (regionais) ou `nacionais/` (nacionais), com subpastas `fontes/` (material original) e `pdfs/` (artigos individuais).
3. **Converter se necessário**: Documentos Word são convertidos para PDF. PDFs escaneados passam por OCR (`ocrmypdf`).
4. **Separar artigos de PDFs compilados**: Quando o original é um e-book, o sumário é parseado para identificar as páginas de cada artigo, e o PDF é dividido com `qpdf --pages`.

### 3.2 Extração de metadados

De cada artigo individual (PDF), extraem-se os metadados estruturados:

- **Título** e **subtítulo** (separados por `:`)
- **Autores** (nome completo, afiliação institucional, email)
- **Resumo** em português e, quando existente, **abstract** em inglês
- **Palavras-chave** (PT e EN)
- **Referências bibliográficas** (lista ao final do artigo)
- **Número de páginas**

A extração é feita por scripts Python que usam `pdftotext` e heurísticas específicas por formato de seminário. Para artigos sem seção de "Referências" mas com notas de rodapé, há um pipeline específico de extração e filtragem de notas (separar referências bibliográficas de comentários, resolver abreviações como op. cit. e idem, deduplicar).

Os metadados extraídos são consolidados em um **arquivo YAML por seminário** (ex: `sdsp05.yaml`), que serve como representação canônica dos dados antes da importação no banco.

### 3.3 Organização dos artigos

Cada artigo recebe um **identificador único** no formato `{slug}-{NNN}` (ex: `sdbr05-001`, `sdnne07-042`). Os PDFs são renomeados para esse padrão.

Os artigos são organizados por **seções temáticas** (eixos, mesas, sessões) conforme o programa original do evento. A informação sobre seções vem do sumário, do caderno de resumos ou do site do evento.

### 3.4 Crédito aos organizadores

Os **organizadores dos anais originais** são identificados e registrados no campo `editors` de cada seminário. A **editora** (instituição que publicou) é registrada separadamente. Quando disponível, a **ficha catalográfica** completa é preservada no campo `description`.

Essa distinção (organizadores vs. editora) é fundamental: os organizadores recebem crédito nominal como editores da publicação, enquanto a editora é a entidade institucional responsável pela publicação.

Para seminários sem editora formal identificada, usa-se "Núcleo Docomomo {Região}" como publisher.

---

## 4. Limpeza e normalização dos metadados

Os dados extraídos dos PDFs passam por um processo sistemático de limpeza e normalização, em grande parte automatizado, com revisão humana ao final.

### 4.1 Banco de dados SQLite

Os metadados YAML são importados para um **banco SQLite** (`anais.db`) que serve como fonte central para todas as operações. O banco tem tabelas para seminários, seções, artigos, autores, relação artigo-autor, variantes de nomes e ORCIDs. O dump textual (`anais.sql`) é versionado no Git.

### 4.2 Normalização de títulos

Os títulos passam por normalização de capitalização segundo a norma brasileira (sentence case), usando um **dicionário de entidades nomeadas** (`dict/dict.db`) com mais de 5.000 entradas — nomes próprios, siglas, topônimos, expressões consolidadas (ex: "Arquitetura Moderna", "Movimento Moderno", "Educação Patrimonial"). O normalizador opera em 3 passadas: palavra a palavra, expressões multi-palavra e toponímicos contextuais.

Outras normalizações:
- **Travessões**: hífen isolado (` - `) substituído por em-dash (` — `) em títulos e nomes de seções (não em intervalos numéricos, compostos ou referências).
- **Separação título/subtítulo**: títulos compostos são divididos no primeiro `:`, com subtítulo iniciando em minúscula.

### 4.3 Normalização de autores

- **Partição de nomes**: familyname = último sobrenome; givenname = todo o resto, incluindo partículas (de, da, do). Nomes hispânicos mantêm duplo sobrenome.
- **Afiliação**: normalizada para sigla institucional (ex: `FAU-USP`, `PROPAR-UFRGS`), removendo títulos acadêmicos, endereços e emails.
- **ORCID**: buscado via APIs (OpenAlex, Crossref, ORCID) e atribuído aos autores. 49% dos autores foram identificados.

### 4.4 Deduplicação de autores

O mesmo pesquisador pode aparecer com grafias diferentes entre seminários (iniciais, ordem de sobrenomes, acentuação). Um pipeline de 11 etapas progressivas deduplica os autores:

1. Enriquecimento via base local (Pilotis — cruzamento por email)
2. Normalização e merge exato
3. Cross-familyname (subconjunto de palavras no givenname)
4. Revisão por LLM (análise de temas, coautores, afiliações)
5. Revisão manual de casos ambíguos

O resultado é registrado em `author_variants`: cada variante mantém o nome original e aponta para o autor canônico. Isso permite rastreabilidade e reversão.

### 4.5 Limpeza de referências

- **Split de underscores ABNT**: a convenção `______.` (repetição de autor) é separada em entradas individuais.
- **Backfill de autores**: `______.` é substituído pelo nome completo do autor da referência anterior.
- **Join de URLs**: URLs órfãs em linha separada são juntadas à referência anterior.
- **Detecção de problemas**: referências concatenadas, conteúdo não-referência (CVs, endereços), fragmentos truncados.

### 4.6 Revisão humana

Após toda a normalização automática, cada seminário passa por **revisão humana** via uma **página HTML de revisão** (`revisao/revisao-{slug}.html`) que exibe capa, ficha catalográfica, seções e todos os artigos com seus campos. O revisor verifica títulos, subtítulos, autores, resumos, keywords e referências, registrando correções que são então aplicadas ao banco.

Os seminários revisados são marcados como tal no registro do projeto, e seus dados não são mais alterados sem solicitação explícita.

---

## 5. Publicação no Zenodo

O **Zenodo** (infraestrutura do CERN, integrada ao InvenioRDM) é usado como repositório canônico dos PDFs, provendo:

- **DOI individual** por artigo (formato `10.5281/zenodo.{id}`)
- **Preservação de longo prazo** (infraestrutura CERN)
- **Estatísticas de acesso** (downloads, visualizações)
- **Licença clara** por artigo (`zenodo-freetoread-1.0` para textos com copyright)

### Metadados no Zenodo

Cada artigo é publicado como um registro individual, com:
- Tipo: conference paper (ou book section, conforme o caso)
- Criadores: autores com ORCIDs
- Contribuidores: organizadores do seminário (role: editor)
- Imprint: título do livro de anais, ISBN, editora, local, páginas
- Conferência: nome, local, data do seminário
- Comunidade: `docomomobr`

### Seminários só-resumo

Alguns seminários (como o sdbr04, com 79 artigos) contêm apenas resumos expandidos, sem texto completo. Nesses casos, o conteúdo já está integralmente nos metadados (título, autores, resumo, keywords), e **não há PDF para subir ao Zenodo**.

### Status

O upload para o Zenodo está em fase de prototipagem. O script `scripts/upload_zenodo.py` implementa o fluxo completo (criação de depósito, upload de PDF, preenchimento de metadados, publicação), com suporte a sandbox e produção. A API InvenioRDM (nova) é usada para campos de imprint (ISBN, editora), pois a API legacy apresenta falhas silenciosas com ISBNs inválidos.

---

## 6. Site Hugo no GitHub Pages

O site público dos anais é um **site estático gerado com Hugo**, hospedado no **GitHub Pages** em `anais.docomomobrasil.com`.

### Arquitetura

```
anais.docomomobrasil.com (GitHub Pages)
  ├── Página inicial
  ├── Por região (Nacional, N/NE, Sudeste, Sul)
  │   └── Seminário (capa, ficha, organizadores)
  │       └── Artigo (título, autores, resumo, keywords, referências)
  │           ├── Botão "Baixar PDF" → link direto Zenodo
  │           └── DOI para citação
  └── Busca (Pagefind)
```

### Princípios

- **PDFs ficam apenas no Zenodo**: o site não hospeda PDFs, apenas linka para o Zenodo. Isso evita duplicação, garante DOI funcional e centraliza as estatísticas de acesso.
- **Metadados acadêmicos no HTML**: tags Highwire Press (para Google Scholar), Dublin Core, Schema.org/JSON-LD e Open Graph. Permite que o Google Scholar e gerenciadores de referência (Zotero) capturem os metadados corretamente.
- **Busca integrada**: Pagefind indexa todos os artigos para busca no lado do cliente, sem servidor.
- **Thumbnails**: a primeira página de cada PDF é convertida em imagem (`pdftoppm`) e usada como capa do artigo no site.

### Geração de conteúdo

O script `scripts/db2hugo.py` lê o `anais.db` e gera as páginas Hugo (Markdown com front matter YAML) para cada seminário e artigo. O conteúdo gerado (`site/content/`) não é versionado no Git — apenas os templates, configurações e imagens estáticas.

### DNS

Os domínios `anais.docomomobrasil.com` e `livros.docomomobrasil.com` são CNAMEs apontando para `docomomobr.github.io`, gerenciados pelo provedor de DNS do domínio `docomomobrasil.com`.

---

## 7. Estrutura do repositório

```
anais/
├── nacionais/              # 15 seminários nacionais (YAMLs + PDFs)
│   ├── sdbr01.yaml         # Metadados consolidados
│   ├── ...
│   ├── sdbr15.yaml
│   ├── capas/              # Capas em PNG
│   └── sdbr{NN}/pdfs/      # PDFs dos artigos (gitignored)
│
├── regionais/
│   ├── nne/                # Norte/Nordeste (10 seminários)
│   ├── se/                 # Sudeste: MG + RJ + SP (10 seminários)
│   └── sul/                # Sul + Paraná (10 seminários)
│
├── scripts/                # Scripts principais de processamento
├── dict/                   # Dicionário NER (dict.db, normalizar.py)
├── docs/                   # Documentação técnica
├── revisao/                # HTMLs de revisão humana
├── site/                   # Site Hugo (config, layouts, static)
│
├── anais.db                # Banco SQLite (gitignored)
├── anais.sql               # Dump textual do banco (versionado)
└── CLAUDE.md               # Diretrizes do projeto
```

Os binários (PDFs, banco SQLite, capas) são gitignored. O repositório versiona apenas os YAMLs, scripts, documentação, dump SQL e arquivos do site Hugo.

---

## 8. Fluxo de trabalho resumido

```
┌─────────────────────────────────────────────────────────┐
│  1. COLETA                                              │
│  Localizar fontes → Copiar → Converter → Separar PDFs  │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│  2. EXTRAÇÃO                                            │
│  pdftotext → Parsear metadados → Montar YAML            │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│  3. LIMPEZA E NORMALIZAÇÃO                              │
│  Importar no SQLite → Normalizar títulos → Limpar refs  │
│  → Deduplicar autores → Buscar ORCIDs                   │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│  4. REVISÃO HUMANA                                      │
│  Gerar HTML de revisão → Revisar → Aplicar correções    │
└──────────────────────────┬──────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           │                               │
┌──────────▼──────────┐        ┌───────────▼──────────┐
│  5. ZENODO           │        │  6. SITE HUGO        │
│  Upload PDFs         │        │  Gerar páginas       │
│  Receber DOIs        │◄──────►│  Linkar PDFs/DOIs    │
│  Preservação         │        │  Busca (Pagefind)    │
│  Estatísticas        │        │  Deploy (GH Pages)   │
└─────────────────────┘        └──────────────────────┘
```

---

## 9. Licenciamento e acesso

- **Textos dos artigos**: direitos reservados aos autores. Licença Zenodo `zenodo-freetoread-1.0` (leitura livre, demais direitos reservados).
- **Metadados**: domínio público (fatos bibliográficos não são protegidos por copyright).
- **Código do projeto**: repositório GitHub público (`github.com/docomomobr/anais`).

---

## 10. Créditos

Projeto realizado por **Danilo Matoso Macedo** (ORCID `0009-0008-4670-9812`), com apoio da Comissão Executiva do Docomomo Brasil, dos núcleos regionais e dos organizadores de cada seminário. Agradecimentos especiais a **Juliana Cardoso Nery** (ORCID `0000-0002-8476-5339`), pela colaboração junto à Comissão Executiva, e a **Suely de Oliveira Figueirêdo Puppi** (ORCID `0009-0001-7224-670X`), pela contribuição com os seminários do Paraná.
