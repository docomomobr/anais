# Desambiguação de Nomes de Autor (AND) nos Anais Docomomo Brasil

## 1. O que é AND

**AND** (*Author Name Disambiguation*) ou **Desambiguação de Nomes de Autor** é o processo de identificar quando registros de nomes diferentes na verdade se referem à mesma pessoa, e quando nomes idênticos se referem a pessoas distintas.

São dois problemas complementares:

- **Sinonímia**: a mesma pessoa aparece com nomes diferentes ("M.B. Cappello" e "Maria Beatriz Cappello")
- **Polissemia**: o mesmo nome pertence a pessoas diferentes (dois "Carlos Silva" distintos)

Na prática, é um problema de *Entity Resolution* (Resolução de Entidades): dado um conjunto de registros com nomes de pessoas, agrupar os que pertencem ao mesmo indivíduo.

---

## 2. O problema no nosso projeto

O banco de dados dos Anais Docomomo Brasil (`anais.db`) contém:

| Dado | Quantidade |
|------|-----------|
| Seminários | 36 |
| Artigos | 2.345 |
| Autores (após dedup) | 2.113 |
| Variantes registradas | 542 |
| Autores com ORCID | 752 |

Os dados foram coletados de 36 seminários diferentes (15 nacionais + 21 regionais), cada um com formatos, fontes e níveis de qualidade distintos. Um mesmo pesquisador pode ter publicado em vários seminários ao longo de 30 anos (1995-2024), aparecendo com variações do nome:

- **Abreviações**: "M.B. Cappello" vs. "Maria Beatriz Cappello"
- **Partículas diferentes**: "Ana Elísia da Costa" vs. "Ana Elísia Costa"
- **Familyname mal separado**: "Ana | Carolina Bierrenbach" vs. "Ana Carolina de Souza | Bierrenbach"
- **Iniciais**: "J.C. Neto" vs. "João Carlos da Silva Neto"
- **Acentuação inconsistente**: "Elísia" vs. "Elisia"

Sem deduplicação, o mesmo pesquisador aparecia como 2 ou 3 autores distintos, comprometendo a navegação por autor no OJS e qualquer análise bibliométrica.

---

## 3. Pipelines implementadas

O módulo `dict/` contém **duas pipelines independentes** que compartilham o mesmo banco de dados (`dict.db`):

### Pipeline 1: NER (Named Entity Recognition) — normalização de textos

**Arquivo principal:** `dict/normalizar.py`

Normaliza títulos e subtítulos de artigos conforme a norma brasileira de capitalização. Usa um banco de dicionário (`dict.db`, 3.443 entradas) para reconhecer entidades nomeadas e aplicar a capitalização correta.

**Categorias no dicionário:**

| Categoria | Entradas | Regra | Exemplo |
|-----------|---------|-------|---------|
| sigla | 165 | MAIÚSCULA | iphan → IPHAN |
| nome | 3.077 | Capitalizado | niemeyer → Niemeyer |
| lugar | 133 | Capitalizado | brasília → Brasília |
| area | 6 | Capitalizado | arquitetura → Arquitetura |
| movimento | 10 | Capitalizado | modernismo → Modernismo |
| expressao | 52 | Forma canônica | joão pessoa → João Pessoa |

**Fluxo:**

```
Título original    "ARQUITETURA MODERNA EM BRASÍLIA"
         ↓
normalizar_texto() consulta dict.db por cada palavra
         ↓
Resultado          "Arquitetura moderna em Brasília"
```

**Uso como módulo:**

```python
from dict.normalizar import normalizar_texto

titulo = normalizar_texto("ARQUITETURA MODERNA EM BRASÍLIA")
# → "Arquitetura moderna em Brasília"

subtitulo = normalizar_texto("O CASO DE SÃO PAULO", eh_subtitulo=True)
# → "o caso de São Paulo"
```

**Uso na linha de comando:**

```bash
python3 dict/normalizar.py "ARQUITETURA MODERNA EM BRASÍLIA"
python3 dict/normalizar.py --subtitulo "O CASO DE SÃO PAULO"
python3 dict/normalizar.py --stats
```

O script `scripts/normalizar_maiusculas.py` aplica esta pipeline a todos os títulos e subtítulos no `anais.db`.

---

### Pipeline 2: AND (Desambiguação de Nomes de Autor)

**Arquivos principais:** `dict/entity_resolution.py` + `scripts/dedup_authors.py`

Identifica variantes de nome e faz merge dos registros duplicados no `anais.db`. Mantém uma tabela `author_variants` com o histórico de todos os merges.

**Funcionamento em 4 fases:**

| Fase | Nome | Ação | Automatização |
|------|------|------|---------------|
| 0 | Enriquecimento (Pilotis) | Expande nomes abreviados usando base externa de emails | Automático |
| 1 | Merge por último sobrenome | Corrige partição errada givenname/familyname | Automático (alta confiança) |
| 2 | Merge por variantes | Detecta abreviações dentro do mesmo familyname | Automático (alta confiança) |
| 3 | Relatório de ambíguos | Lista casos de baixa confiança | Revisão humana |

**Exemplo da Fase 2:**

```
Autor A: "Maria Beatriz" | "Cappello"  (3 artigos)
Autor B: "M.B."          | "Cappello"  (1 artigo)
         ↓
is_variant() → True (familyname idêntico + givenname é abreviação)
confidence() → 'alta' (2 tokens reais no nome curto)
         ↓
MERGE: mantém "Maria Beatriz Cappello", registra "M.B. Cappello" como variante
```

**Uso:**

```bash
# Executar dedup completa (fases 0-3)
python3 scripts/dedup_authors.py

# Apenas mostrar o que faria (sem alterar o banco)
python3 scripts/dedup_authors.py --dry-run

# Apenas relatório de ambíguos
python3 scripts/dedup_authors.py --report
```

---

## 4. Abordagem prática vs. acadêmica

A pesquisa acadêmica sobre AND (documentada em `and_fontes.md`, com 41 referências) descreve abordagens complexas:

- Redes neurais profundas (GCN, DHGN)
- Aprendizado ativo com a biblioteca `dedupe`
- Grafos de conhecimento acadêmico
- Integração com Getty ULAN via SPARQL
- Métricas sofisticadas (Jaro-Winkler, TF-IDF)

**A nossa abordagem é mais simples, mas funciona para a escala do projeto.** Com 2.113 autores (não 2 milhões), não precisamos de machine learning. O algoritmo implementado é determinístico, auditável e reversível.

### O que usamos

| Técnica | Implementação | Referência |
|---------|---------------|------------|
| **Blocking por familyname** | Agrupa autores pelo último sobrenome normalizado (sem acentos). Só compara pares dentro do mesmo grupo. | `dedup_authors.py`, fases 1 e 2 |
| **Detecção de abreviações** | "M.B." casa com "Maria Beatriz" (cada inicial é prefixo do token correspondente) | `entity_resolution.py`, `is_abbreviation_of()` |
| **Tratamento de partículas** | "de", "da", "do" ficam no givenname, nunca no familyname. Removidas para comparação. | Constante `PARTICLES` |
| **Nível de confiança** | Nome curto com 2+ palavras reais = alta confiança (merge automático). Com 1 palavra = baixa (revisão humana). | `confidence()` |
| **Pilotis** | Base externa de membros do Docomomo com emails. Match por email expande nomes abreviados. | `dedup_authors.py`, fase 0 |
| **ORCID como âncora** | 752 dos 2.113 autores têm ORCID. Identificador único e inequívoco. | Campo `orcid` na tabela `authors` |
| **Revisão humana** | Fase 3 gera relatório de ambíguos. Fichas em `revisao/` para edição manual. | `dedup_authors.py`, fase 3 |

### O que **nao** usamos (e por que)

| Abordagem acadêmica | Por que nao |
|---------------------|-------------|
| Biblioteca `dedupe` (ML) | Requer rotulagem manual de centenas de pares para treinar. Para 2k autores, regras determinísticas resolvem. |
| Getty ULAN | Cobre arquitetos famosos, nao pesquisadores acadêmicos brasileiros contemporâneos. |
| Graph Neural Networks | Complexidade desproporcional para o volume de dados. |
| Jaro-Winkler / fuzzy matching | Nomes brasileiros sao longos e estruturados (givenname + familyname). Comparação exata de familyname + prefixo de givenname é suficiente. |
| PostgreSQL + schema dedicado | O SQLite com tabelas `authors` + `author_variants` é adequado para o volume. |

### Resultados

O pipeline de dedup reduziu o número de autores e registrou 542 variantes. Os 15 autores mais produtivos (com mais artigos publicados) sao identificados corretamente mesmo quando publicaram com nomes diferentes ao longo de 30 anos de seminários.

---

## 5. Módulos do dict/

### Estrutura de arquivos

```
dict/
├── __init__.py              # Exports dos dois pipelines
├── normalizar.py            # Pipeline 1: NER + normalização de maiúsculas
├── entity_resolution.py     # Pipeline 2: detecção de variantes de nome
├── init_db.py               # Cria dict.db com schema + entradas manuais
├── seed_authors.py          # Importa nomes de autores de banco externo
├── seed_titles.py           # Extrai nomes próprios de títulos de artigos
├── dump_db.py               # Gera dict.sql (dump textual versionável)
├── dict.db                  # Banco SQLite (gitignored)
├── dict.sql                 # Dump SQL (versionado no git)
├── .gitignore               # Ignora dict.db
├── README.md                # Documentação técnica do módulo
└── documentacao/
    ├── and_fontes.md         # Pesquisa acadêmica (41 referências)
    └── and_pesquisa.md       # Este arquivo
```

### Descrição de cada módulo

**`__init__.py`** — Marcador de pacote Python. Exporta as funções públicas de ambos os pipelines (`normalizar_texto`, `is_variant`, `is_abbreviation_of`, `confidence`, etc.).

**`init_db.py`** — Cria o banco `dict.db` com a tabela `dict_names` e popula com entradas manuais: 165 siglas (instituições, UFs, romanos), 133 lugares (cidades, estados, países), 6 áreas do saber, 10 movimentos artísticos e 52 expressões consolidadas. Aceita `--reset` para recriar do zero.

**`seed_authors.py`** — Lê a tabela `authors` de qualquer banco SQLite e insere cada parte dos nomes (givenname, familyname) como entradas `nome` no dicionário. Filtra partículas e iniciais. Nao sobrescreve entradas existentes. Adicionou 3.077 nomes de autores ao dicionário.

**`seed_titles.py`** — Extrai candidatos a nomes próprios dos títulos de artigos. Usa heurística: palavras capitalizadas que nao sao início de frase, nao sao siglas conhecidas e nao estao no dicionário. Gera lista para revisão humana antes de inserir (flag `--apply`).

**`normalizar.py`** — Pipeline 1. Carrega o dicionário em memória e normaliza textos palavra por palavra. Prioridade: sigla > nome > lugar > área > movimento > início de frase > minúscula. Segunda passada aplica expressões consolidadas via regex. Trata hífens, barras e apóstrofos (`d'Alva`). Funciona como módulo importável ou CLI.

**`entity_resolution.py`** — Pipeline 2. Funções puras (sem acesso a banco) para comparação de nomes:

| Função | O que faz |
|--------|-----------|
| `normalize_name(name)` | Minúscula, sem acentos, pontos viram espaços |
| `is_abbreviation_of(short, long)` | "M.B." é abreviação de "Maria Beatriz"? |
| `is_variant(gn1, gn2, fn1, fn2)` | Dois nomes sao variantes da mesma pessoa? |
| `longer_name(n1, n2)` | Qual dos dois nomes é mais completo? |
| `confidence(gn_short, gn_long)` | "alta" (2+ tokens reais) ou "baixa" (1 token) |
| `full_name_tokens(gn, fn)` | Tokens normalizados sem partículas |
| `full_name_compatible(short, long)` | Nomes completos compatíveis (primeiro, meio, último)? |
| `split_name_canonical(parts)` | Separa tokens em (givenname, familyname) |

**`dump_db.py`** — Gera o dump textual `dict.sql` a partir de `dict.db`, para versionamento no git. O `.db` binário é gitignored.

**`dict.db`** — Banco SQLite com 3.443 entradas. Schema:

```sql
CREATE TABLE dict_names (
    word TEXT PRIMARY KEY,
    category TEXT NOT NULL,    -- sigla, nome, lugar, area, movimento, expressao
    canonical TEXT NOT NULL,   -- forma canônica (ex: 'Brasília', 'IPHAN')
    source TEXT DEFAULT 'manual'  -- origem: manual, autores, titulos
);
```

**`dict.sql`** — Dump textual do banco, versionado no git. Permite reconstruir o `.db` e rastrear mudanças no dicionário via `git diff`.

---

## 6. Pesquisa aplicada (2026-02-11)

Três frentes de pesquisa foram conduzidas em paralelo para avaliar técnicas complementares à dedup existente.

### 6.1 Getty ULAN — DESCARTADO

O **Union List of Artist Names** (ULAN) do Getty Research Institute é o vocabulário controlado de referência para artistas e arquitetos. Testamos sua aplicabilidade via endpoint SPARQL (`http://vocab.getty.edu/sparql`).

**Arquitetos brasileiros famosos encontrados no ULAN:**
- Oscar Niemeyer — sim (ID: 500028798)
- Lúcio Costa — sim
- Lina Bo Bardi — sim
- Paulo Mendes da Rocha — sim
- Roberto Burle Marx — sim
- Affonso Eduardo Reidy — sim
- Vilanova Artigas — sim

**Pesquisadores acadêmicos contemporâneos encontrados:** NENHUM.
Testamos: Ruth Verde Zein, Hugo Segawa, Carlos Eduardo Comas, Abilio Guerra, Fernando Lara, Roberto Montezuma — nenhum tem registro no ULAN.

**Cobertura estimada:** ~1,3% dos nossos 2.113 autores (apenas os arquitetos históricos que aparecem como autores de textos sobre suas próprias obras).

**Conclusão:** O ULAN cobre artistas e arquitetos consagrados, não pesquisadores acadêmicos. Para uma coleção de anais de seminários (onde 95%+ dos autores são professores, doutorandos, mestrandos), o ULAN é irrelevante. O ORCID (752 autores, 35,6%) é ordens de grandeza mais útil.

### 6.2 Bibliotecas Python: dedupe vs. recordlinkage

| Aspecto | dedupe | recordlinkage |
|---------|--------|---------------|
| Classificador | Supervisionado (logístico) | ECM não-supervisionado |
| Treinamento | Requer rotulação manual (~200 pares) | Sem treinamento |
| Dependências | fastcluster, simplecosine, zope.index | Apenas pandas, numpy, scipy, sklearn |
| Escala ideal | Milhares a milhões | Centenas a dezenas de milhares |
| Blocking | Obrigatório (faz parte do pipeline) | Opcional (Index classes) |
| Saída | Clusters com probabilidade | Pares com score de similaridade |
| Manutenção | Modelo salvo em arquivo | Sem estado (re-executa) |

**Conclusão:** Para 2.100 autores sem dados rotulados, **recordlinkage** é mais adequado. Não requer treinamento supervisionado, usa classificador ECM (Expectation-Conditional Maximization) que funciona sem exemplos rotulados, e tem dependências padrão.

### 6.3 Jaro-Winkler distance — VALE IMPLEMENTAR

Testamos **Jaro-Winkler similarity** em todos os pares de familynames diferentes no banco. Threshold >= 0.90 produziu 357 pares candidatos, dos quais filtramos os que têm o **mesmo givenname** (ou compatível):

**Duplicatas reais encontradas (mesma pessoa, familyname grafado diferente):**

| JW Score | Autor A | Autor B | Evidência |
|----------|---------|---------|-----------|
| 0.971 | [1504] Maria Beatriz Camargo **Cappello** | [1800] Maria Beatriz Camargo **Capello** | Mesmo nome completo, ll→l |
| 0.967 | [709] Fábio Fernandes **Villela** | [1330] Fabio Fernandes **Vilella** | Mesmo nome, ll/le invertidos |
| 0.971 | [1538] Claudio Andrés **Galeno Ibaceta** | [1838] Claudio **Galeno-Ibaceta** | Nome composto hispânico, espaço→hífen |
| 0.975 | [84] Eduardo Pierrotti **Rossetti** | [609] Eduardo **Rosseti** | Mesmo Eduardo, tt→t |
| 0.975 | [948] Renata **Zampieri** | [1666] Renata Venturini **Zampier** | Mesma Renata, i final |
| 0.960 | [272] Márcia Gadelha **Cavalcante** | [2551] Márcia **Cavalcanti** | Mesmo primeiro nome, e→i |

**Falsos positivos comuns (nomes parecidos, pessoas diferentes):**

| JW Score | Autor A | Autor B | Por que é falso |
|----------|---------|---------|-----------------|
| 0.987 | Eduardo Mendes de **Vasconcellos** | Gustavo Bruski de **Vasconcelos** | Givennames diferentes |
| 0.975 | Magda **Campelo** | Maria de Fátima **Campello** | Givennames diferentes |
| 0.971 | Felipe **Moraes** | Jorge **Morales** | Pessoas diferentes |
| 0.967 | Jacqueline **Romaro** | Danielle **Romão** | Pessoas diferentes |

**O caso do nome composto hispânico** (Galeno Ibaceta / Galeno-Ibaceta) é importante: o matching por familyname exato falha porque um usa espaço e outro hífen. Jaro-Winkler encontra.

**Regra proposta:** Jaro-Winkler >= 0.92 no familyname + givenname compatível (abreviação ou prefixo) = candidato a merge. Revisão automática para alta confiança, humana para baixa.

### 6.4 Coautoria como sinal — VALE IMPLEMENTAR

Analisamos a tabela `article_author` para co-aparição de autores:

- **Co-aparição no mesmo artigo** = definitivamente pessoas diferentes (sinal negativo forte). Impede merge mesmo que nomes sejam muito parecidos.
- **Coautores compartilhados** (sem co-aparição direta) = sinal positivo. Se A publicou com C, e B publicou com C, e A/B nunca co-apareceram, é evidência de que A=B.

**Caso encontrado:** Cantuaria (Eloane vs Eliane) — a análise de coautores resolve a ambiguidade.

**Implementação:** Antes de fazer merge, verificar se os dois candidatos co-aparecem em algum artigo. Se sim, rejeitar merge. Se compartilham coautores, aumentar confiança.

### 6.5 Blocking — DESNECESSÁRIO

Blocking (agrupar por iniciais/fonético antes de comparar) é otimização para datasets grandes. Com 2.100 autores, a comparação all-pairs gera ~2,2 milhões de pares — processável em <1 segundo com Jaro-Winkler puro Python. Não implementar.

---

## 7. Referências

Para a pesquisa acadêmica completa sobre AND, com 41 referências cobrindo deep learning, a biblioteca `dedupe`, Getty ULAN, schema do OJS, Dublin Core e MARC21, ver:

**[`dict/documentacao/and_fontes.md`](and_fontes.md)**

Tópicos cobertos naquele documento:
- Estado da arte em AND (2016-2025)
- Especificidades do domínio da Arquitetura
- Schema do banco de dados OJS 3.3/3.4
- Projeto de um "Disambiguation Workbench" (banco intermediário)
- Algoritmos de blocagem e clustering
- Integração com Getty ULAN via SPARQL
- Biblioteca `dedupe` para aprendizado ativo
- Padronização Dublin Core e MARC21
- Considerações éticas (GDPR)
- Desambiguação incremental (online)
