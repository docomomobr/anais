---
title: "Editorial"
slug: editorial
---

<div class="author-list">
<span class="author">Danilo Matoso Macedo
<a href="https://orcid.org/0009-0008-4670-9812" target="_blank" rel="noopener" class="orcid-link" title="ORCID: 0009-0008-4670-9812"><img src="/img/orcid.svg" alt="ORCID" class="orcid-icon"></a>
<span class="affiliation">(Docomomo Brasil)</span></span>
</div>

<section class="pdf-action">
<a href="https://doi.org/10.5281/zenodo.19297561" class="doi-badge" target="_blank" rel="noopener"><span class="doi-label">DOI</span><span class="doi-value">10.5281/zenodo.19297561</span></a>
</section>

A organização dos anais de eventos realizados dentro do âmbito do Docomomo Brasil é parte de uma filosofia de armazenagem, descrição e difusão sistemáticas da produção deste nosso grupo com mais de 30 anos de história.

Muitos seminários já estavam disponibilizados na internet — inclusive na página do Docomomo Brasil, conforme organizada em gestões anteriores. Um excelente trabalho de pesquisa sobre os dois primeiros seminários Docomomo Brasil já foi feito por José Carlos Huapaya Espinoza, Alexandre Pajeú Moura, Rômulo Marques e Thiscianne Pessoa em 2019-20. Certo número estava somente em CDs e DVDs hoje obsoletos, guardados nas estantes dos colegas. Outros estavam em sites temporários que já haviam saído do ar. Alguns compõem livros disponibilizados em PDF que puderam ser desmembrados em artigos. Por fim, havia seminários cujos anais não haviam sido previamente publicados. Ainda há muito mais que reunir, sistematizar e publicar. É tarefa coletiva em permanente progresso.

Até aqui, todos os organizadores consultados foram solícitos em atender prontamente a nossa solicitação, enviando os arquivos originais. Esse esforço de busca foi empreendido juntamente a Juliana Nery (Norte / Nordeste) e a Suely Puppi (Paraná).

Para ler, traduzir e organizar a massa de dados, e para fazer a publicação, trabalhamos com a ferramenta Claude Code. Graças a esse recurso, foi possível pesquisar e organizar a publicação dos anais de acordo com os mais atuais padrões de dados e metadados vigentes. Partimos de uma primeira extração de dados feita pela empresa Acesso Acadêmico, que contratamos em 2025 para disponibilizar os arquivos em OJS — *Open Journal System*. Esse sistema, voltado para o fluxo de periódicos, revelou-se problemático para publicar anais, o que ao fim e ao cabo era um adaptação. Cogitamos então a migração para sistemas como dSpace. Por fim, optamos por uma filosofia de armazenagem e publicação, acreditamos, mais robusta que simplesmente dispor os arquivos num servidor pago que poderia ser desativado por alguma inadimplência acidental. Os dados foram distribuídos em plataformas estáveis e resilientes conforme descrevemos abaixo.

## Arquitetura de publicação

Os **artigos em PDF** estão depositados na [comunidade Docomomo Brasil no Zenodo](https://zenodo.org/communities/docomomobr), repositório acadêmico mantido pelo CERN (Organização Europeia para a Pesquisa Nuclear) e financiado pela Comissão Europeia. O Zenodo é uma infraestrutura pública de longo prazo, sem custo para o depositante, que garante a preservação e o acesso permanente aos arquivos. Cada artigo recebe um DOI (Digital Object Identifier) individual, identificador persistente que assegura que o trabalho será sempre localizável, mesmo que endereços de internet mudem.

O **site de consulta** que você está lendo é gerado estaticamente com [Hugo](https://gohugo.io) e hospedado no [GitHub Pages](https://pages.github.com). Não depende de banco de dados em tempo real, de servidor de aplicação nem de manutenção contínua. A íntegra do código-fonte, dos metadados e do histórico de alterações está em repositório público no [GitHub](https://github.com/docomomobr/anais). Qualquer pessoa pode verificar, reproduzir ou continuar este trabalho.

Essa separação é intencional. O PDF — objeto primário da publicação acadêmica — está em infraestrutura científica de longo prazo. O site — interface de consulta, busca e citação — pode ser reconstruído a qualquer momento a partir dos dados versionados. Se um serviço sair do ar, o outro continua funcionando.

## Acervo

O acervo reúne os anais de **45 seminários** Docomomo Brasil — nacionais e regionais — realizados entre 1995 e 2025, totalizando **2.714 artigos** de **2.461 autores**.

| Âmbito | Seminários | Artigos | Período |
|--------|-----------|---------|---------|
| Nacional | 15 | 1.441 | 1995–2023 |
| Norte/Nordeste | 10 | 545 | 2006–2025 |
| Sul | 8 | 326 | 2008–2022 |
| São Paulo | 6 | 289 | 2007–2024 |
| Paraná | 2 | 45 | 2012–2015 |
| Rio de Janeiro | 3 | 42 | 2013–2017 |
| Minas Gerais | 1 | 26 | 2010 |

## Metadados

Cada artigo foi descrito com os seguintes metadados, quando disponíveis na publicação original:

| Campo | Descrição |
|-------|-----------|
| Título | Em português e, quando disponível no original, em inglês e espanhol |
| Autores | Nome completo, com identificação de sobrenome e prenomes |
| Afiliação | Sigla da instituição do autor à época da publicação |
| ORCID | Identificador internacional do pesquisador, buscado junto ao registro ORCID |
| Resumo | Em português e, quando disponível, em inglês e espanhol |
| Palavras-chave | Em português e, quando disponível, em inglês e espanhol |
| Referências bibliográficas | Extraídas do texto do artigo |
| Páginas | Numeração no volume original |
| Eixo temático / Sessão | Divisão temática do evento, conforme a programação original |
| ISBN | Do volume dos anais |

Os ORCIDs foram obtidos por busca automatizada na API pública do ORCID, com verificação manual dos resultados. Cerca de 57% dos autores possuem ORCID identificado.

## Padrões e normas

Os metadados seguem padrões internacionais consolidados para publicações acadêmicas, visando a máxima interoperabilidade e descobribilidade:

### Descoberta e indexação

- **[Highwire Press](https://scholar.google.com/intl/en/scholar/inclusion.html)** — Metatags reconhecidas pelo Google Scholar para indexação de artigos acadêmicos. Incluem título, autores, data, DOI, URL do PDF, resumo, ORCID, afiliação, ISBN e paginação.
- **[Dublin Core](https://www.dublincore.org/specifications/dublin-core/)** — Padrão ISO 15836 para descrição de recursos digitais.
- **[Schema.org](https://schema.org/ScholarlyArticle)** — Vocabulário JSON-LD para dados estruturados, com tipo ScholarlyArticle. Reconhecido pelo Google e outros mecanismos de busca para exibição enriquecida nos resultados.
- **[COinS](https://en.wikipedia.org/wiki/COinS)** (ContextObjects in Spans) — Padrão OpenURL para captura automática de referências. Permite que gerenciadores bibliográficos como Zotero e Mendeley importem os dados do artigo com um clique.
- **[Signposting](https://signposting.org/)** (FAIR) — Links tipados que facilitam a navegação por agentes automatizados, em conformidade com os princípios FAIR (Findable, Accessible, Interoperable, Reusable).
- **[Open Graph](https://ogp.me/) / Twitter Cards** — Metadados para compartilhamento em redes sociais, com título, descrição e imagem.

### Exportação de citações

Cada artigo oferece a referência bibliográfica em quatro formatos, acessíveis por links na página:

| Formato | Uso principal |
|---------|--------------|
| **BibTeX** | LaTeX, JabRef, Overleaf |
| **RIS** | EndNote, Mendeley, Zotero |
| **CSL-JSON** | Zotero, processadores CSL |
| **CSL-YAML** | pandoc-citeproc, processamento automatizado |

### Citação ABNT

A página de cada artigo inclui a referência formatada segundo a **NBR 6023:2018** (Informação e documentação — Referências — Elaboração), pronta para copiar e colar.

## Licença

Os artigos são disponibilizados sob licença [Creative Commons Atribuição 4.0 Internacional (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/), que permite compartilhar e adaptar o material, desde que seja dado crédito ao autor.

