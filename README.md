# Anais Docomomo Brasil

Repositório de metadados, scripts e site estático dos anais dos seminários [Docomomo Brasil](https://docomomobrasil.com).

## Acervo

O acervo reúne os anais dos **15 Seminários Nacionais** Docomomo Brasil, realizados entre 1995 e 2023, totalizando cerca de **1.400 artigos** de mais de **1.700 autores**.

Os seminários regionais (Norte/Nordeste, Sudeste e Sul) serão incorporados em etapa seguinte.

## Arquitetura de publicação

Os **artigos em PDF** estão depositados no [Zenodo](https://zenodo.org), repositório acadêmico mantido pelo CERN. Cada artigo recebe um DOI individual.

O **site de consulta** é gerado estaticamente com [Hugo](https://gohugo.io) e hospedado no [GitHub Pages](https://pages.github.com). Não depende de banco de dados em tempo real nem de manutenção contínua.

Essa separação é intencional: o PDF está em infraestrutura científica de longo prazo; o site pode ser reconstruído a qualquer momento a partir dos dados versionados.

## Estrutura do repositório

```
anais/
├── anais.sql              # Dump textual do banco SQLite (metadados de todos os artigos)
├── scripts/               # Scripts de processamento, validação e publicação
├── dict/                  # Módulo de normalização e resolução de entidades (nomes, siglas)
├── docs/                  # Documentação técnica (pipelines, regras de dados)
├── nacionais/             # YAMLs consolidados dos seminários nacionais
├── regionais/             # YAMLs dos seminários regionais (em preparação)
├── site/                  # Site Hugo (templates, CSS, config)
│   ├── config.toml
│   ├── layouts/
│   ├── static/
│   └── content/           # Gerado por db2hugo.py (gitignored)
└── schema/                # Schema YAML de referência
```

## Como gerar o site localmente

### Pré-requisitos

- [Python 3.8+](https://www.python.org/)
- [Hugo extended](https://gohugo.io/installation/) (v0.120+)
- SQLite 3
- Dependências Python: `pip install pyyaml`

### Passos

```bash
# 1. Reconstruir o banco SQLite a partir do dump textual
sqlite3 anais.db < anais.sql

# 2. Gerar o conteúdo Hugo a partir do banco
python3 scripts/db2hugo.py --all --outdir site/content

# 3. Servir o site localmente
cd site && hugo server
```

O site estará disponível em `http://localhost:1313/`.

## Metadados

Cada artigo é descrito com os seguintes campos, quando disponíveis na publicação original:

| Campo | Descrição |
|-------|-----------|
| Título | Em português e, quando disponível, em inglês e espanhol |
| Autores | Nome completo, com identificação de sobrenome e prenomes |
| Afiliação | Sigla da instituição do autor à época da publicação |
| ORCID | Identificador internacional do pesquisador |
| Resumo | Em português e, quando disponível, em inglês e espanhol |
| Palavras-chave | Em português e, quando disponível, em inglês e espanhol |
| Referências | Extraídas do texto do artigo |
| Páginas | Numeração no volume original |
| Eixo temático | Divisão temática do evento, conforme a programação original |
| ISBN | Do volume dos anais |

## Padrões adotados

O site implementa os seguintes padrões de metadados para descoberta e interoperabilidade:

- **Highwire Press** — indexação pelo Google Scholar
- **Dublin Core** (ISO 15836)
- **Schema.org** (JSON-LD, tipo `ScholarlyArticle`)
- **COinS** — captura automática por Zotero, Mendeley e outros gerenciadores
- **Signposting** (FAIR) — navegação por agentes automatizados
- **Open Graph / Twitter Cards** — compartilhamento em redes sociais

Cada artigo oferece citação em BibTeX, RIS, CSL-JSON e YAML, além de referência ABNT (NBR 6023:2018).

## Documentação técnica

- [`docs/pipeline_tratamento.md`](docs/pipeline_tratamento.md) — pipeline de ingestão e tratamento de dados
- [`docs/pipeline_revisao.md`](docs/pipeline_revisao.md) — pipeline de revisão automática (diagnóstico, normalização, extração)
- [`docs/pipeline_producao.md`](docs/pipeline_producao.md) — pipeline de produção (Hugo + Zenodo)
- [`docs/regras_dados.md`](docs/regras_dados.md) — regras de normalização de dados
- [`docs/fontes_secoes.md`](docs/fontes_secoes.md) — fontes das seções/eixos temáticos

## Licença

Os artigos são disponibilizados sob licença [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

O código-fonte deste repositório (scripts, templates, configurações) é disponibilizado sob licença [MIT](https://opensource.org/licenses/MIT).

---

Danilo Matoso Macedo — Docomomo Brasil, gestão 26-27
