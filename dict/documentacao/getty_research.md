# Pesquisa: Getty AAT, TGN e ArchiText para enriquecimento do dicionário

Data: 2026-02-11

## Contexto

O documento `ner_fontes.md` referencia três fontes externas como potenciais
enriquecedores do dicionário: Getty AAT, Getty TGN e ArchiText Mining.
Esta pesquisa avaliou a aplicabilidade de cada uma ao nosso corpus
(2345 artigos de anais de Arquitetura brasileira, em português).

## 1. Getty AAT (Art & Architecture Thesaurus)

**Cobertura em português:** 3.013 conceitos com labels em português, de ~70.000+
no total (4%). Acesso via SPARQL: `http://vocab.getty.edu/sparql`.

**Nota técnica:** O identificador de língua portuguesa no endpoint SPARQL do Getty
é `aat:300389115` (não `gvp_lang:pt`, que retorna zero resultados).

**Termos relevantes encontrados em português:**

| AAT ID | Português | Inglês | No nosso dict.db? |
|--------|-----------|--------|-------------------|
| 300112048 | brutalismo | Brutalist | Sim |
| 300021474 | Modernismo | Modernist | Sim |
| 300391347 | ecletismo | Historicism | Sim |
| 300021432 | Bauhaus | Bauhaus | Sim |
| 300021374 | Futurismo | Futurist | Sim |
| 300021393 | Construtivismo | Constructivist | Sim |
| 300022208 | Pós-modernismo | Post-Modernist | Sim |
| 300021140 | Renascença | Renaissance | Sim (como Renascimento) |
| 300021430 | art nouveau | Art Nouveau | Sim |
| 300021426 | art deco | Art Deco | Sim |
| 300069303 | arquitetura racionalista | Rationalist | Parcial (Racionalismo) |
| 300112407 | Deconstrutivismo | Deconstructivist | **Não** |
| 300456752 | Neoconcreto | Neo-Concrete | **Não** |
| 300375735 | estilo moderno | Modern Style | **Não** |
| 300264556 | arte afro-brasileira | Afro-Brazilian | **Não** |
| 300259487 | Novo Urbanismo | New Urbanism | **Não** |
| 300065758 | Minimalismo | Minimal | **Não** |

**Avaliação:** Dos 18 movimentos no nosso dict.db, a maioria já está coberta.
O AAT adiciona alguns termos que NÃO aparecem nos nossos títulos (Deconstrutivismo,
Minimalismo, Novo Urbanismo), exceto Concretismo/Neoconcretismo que têm
2-3 ocorrências. Cobertura de 4% em português é baixa demais para integração
automatizada via SPARQL.

**Decisão:** Cherry-pick manual de 2 movimentos (Concretismo, Neoconcretismo)
que efetivamente ocorrem nos títulos. Integração SPARQL descartada.

## 2. Getty TGN (Thesaurus of Geographic Names)

**Cobertura brasileira:** 70.865 lugares sob Brasil (`tgn:1000047`).
Hierarquia: Brasil → Grandes Regiões → Estados → Municípios/Cidades.

**Comparação com dict.db:** Nosso dicionário tem 131 lugares curados manualmente,
escolhidos especificamente por ocorrerem nos títulos do nosso corpus.

**Problemas:**
- Labels preferidos sem acentos ("Brasilia", não "Brasília")
- 70K+ entradas incluem milhares de municípios, rios, montanhas que nunca
  aparecem nos nossos títulos
- Requer mapeamento adicional de formas canônicas com diacríticos

**Decisão:** Descartado. Nossa lista curada de 131 lugares é mais útil para
normalização de títulos do que 70K entradas genéricas do TGN.

## 3. ArchiText Mining

**O que é:** Projeto de pesquisa da UPM (Madri) sobre text mining em periódicos
de arquitetura espanhóis (1939-1975). Grupo THACA.

**Língua:** Apenas espanhol. Sem conteúdo em português.

**Dataset:** Não há dataset público disponível para download. O paper publicado
(2019, Zivot Umjetnosti) descreve metodologia sem liberar dados.

**Decisão:** Descartado. Sem artefato reutilizável.

## 4. Getty ULAN (Union List of Artist Names)

Pesquisado em sessão anterior. Cobertura de apenas 1.3% dos nossos autores
(acadêmicos brasileiros, não arquitetos internacionalmente famosos). Descartado.

## Resumo

| Fonte | Cobertura PT | Relevância | Integração | Decisão |
|-------|-------------|------------|------------|---------|
| **AAT** | 3.013 (4%) | Média | Manual: 2 movimentos | Cherry-pick |
| **TGN** | 70.865 lugares | Muito baixa | — | Descartado |
| **ArchiText** | 0 (espanhol) | Nenhuma | — | Descartado |
| **ULAN** | 1.3% autores | Muito baixa | — | Descartado |

## Termos incorporados ao dict.db

Com base na pesquisa AAT + validação contra o corpus de 2345 títulos:

**Movimentos (AAT-sourced):**
- `concretismo` → `Concretismo` (3 ocorrências nos títulos)
- `neoconcretismo` → `Neoconcretismo` (2 ocorrências nos títulos)

**Expressões (corpus-validated, conceitos estabelecidos):**
- `patrimônio histórico` → `Patrimônio Histórico` (9 oc.) — conceito institucional (IPHAN)
- `patrimônio arquitetônico` → `Patrimônio Arquitetônico` (18 oc.)
- `patrimônio edificado` → `Patrimônio Edificado` (5 oc.)
- `patrimônio industrial` → `Patrimônio Industrial` (2 oc.) — conceito TICCIH
- `paisagem cultural` → `Paisagem Cultural` (3 oc.) — conceito UNESCO
- `paisagem urbana` → `Paisagem Urbana` (2 oc.)
- `plano piloto` → `Plano Piloto` (10 oc.) — nome próprio / conceito urbanístico
- `cidade jardim` → `Cidade Jardim` (2 oc.) — conceito urbanístico
- `cidade moderna` → `Cidade Moderna` (14 oc.) — paralelo a "Arquitetura Moderna"

**Termos descartados (técnicas/tipos, não conceitos FUNAG):**
- concreto armado (12 oc.) — técnica construtiva, não conceito capitalizado
- concreto aparente (5 oc.) — idem
- habitação social (8 oc.) — tipo habitacional, não expressão consolidada
- habitação popular (2 oc.) — idem
- conjunto habitacional (11 oc.) — tipologia edilícia, não conceito
- vila operária (2 oc.) — idem
