# Regras de processamento de dados

Regras completas de normalização e limpeza de dados para os anais Docomomo Brasil.
Resumo em `CLAUDE.md`; este arquivo é a referência canônica.

---

## Mapeamento de campos YAML → OJS

### Issue (Edição)

| Campo YAML | Campo OJS | Obrigatório | Notas |
|------------|-----------|-------------|-------|
| `title` | title | Sim | Título da edição |
| `subtitle` | subtitle | Não | Subtítulo da edição |
| `description` | description | Não | Descrição completa (pode incluir local, ISBN, fonte) |
| `year` | year | Sim | Ano de publicação |
| `volume` | volume | Sim | Número do volume |
| `number` | number | Sim | Número da edição |
| `date_published` | date_published | Sim | Formato: YYYY-MM-DD |
| `editors` | editors | Não | Lista de **organizadores** (pessoas que organizaram os anais) |
| `publisher` | — | Não | **Editora** (instituição que publicou os anais). Incluir na `description` para OJS. |
| `isbn` | — | Não | ISBN da publicação |
| `location` | — | Não | Cidade e UF do evento (ex: "São Carlos, SP") |

**IMPORTANTE — Organizadores vs. Editora:**
- **`editors`** (organizadores): as pessoas que organizam os anais (em inglês, "editors"). Ex: "Miguel Antonio Buzzar"
- **`publisher`** (editora): a instituição que publica os anais (em inglês, "publisher"). Ex: "IAU/USP", "EDUFU", "Mack Pesquisa/UPM"
- O OJS não tem campo dedicado para `publisher` na importação XML; incluir na `description` da issue.

### Campos internos (não vão para OJS)

| Campo | Uso |
|-------|-----|
| `slug` | Identificador interno do seminário |
| `source` | URL de origem dos dados |

### Article (Artigo)

| Campo YAML | Campo OJS | Obrigatório | Notas |
|------------|-----------|-------------|-------|
| `title` | title | Sim | Título do artigo |
| `subtitle` | subtitle | Não | Manter separado do title |
| `abstract` | abstract | Não | Resumo do artigo |
| `keywords` | keywords | Não | Lista de palavras-chave |
| `section` | section_ref | Sim | Seção (ex: "Artigos Completos - Documentação") |
| `pages` | pages | Não | Páginas (ex: "1-15") |
| `file` | galley | Não | Caminho para o arquivo PDF |
| `locale` | locale | Sim | Formato: pt-BR (não pt_BR) |

### Author (Autor)

| Campo YAML | Campo OJS | Obrigatório | Notas |
|------------|-----------|-------------|-------|
| `givenname` | givenname | Sim | Nome |
| `familyname` | familyname | Sim | Sobrenome |
| `email` | email | Sim | Email do autor |
| `affiliation` | affiliation | Não | **Apenas instituição** (ver regras abaixo) |
| `orcid` | orcid | Não | Formato: 0000-0000-0000-0000 |
| `country` | country | Não | Código do país (BR, PT, etc.) |
| `bio` | biography | Não | Título acadêmico (Doutor, Professor, etc.) |
| `primary_contact` | primary_contact | Sim | true/false - autor de correspondência |

---

## Regras para títulos e subtítulos

### Separação título/subtítulo

- O subtítulo é separado do título por `: ` (dois-pontos seguido de espaço)
- Ao parsear, dividir em `title` e `subtitle` no primeiro `: `
- **Títulos com ponto seguido de nova frase** devem ser separados em título + subtítulo:
  - `Hélio Modesto em Fortaleza. Ressonância e resistibilidade` → title: `Hélio Modesto em Fortaleza` + subtitle: `ressonância e resistibilidade`
  - `Vila Amazonas e Vila Serra do Navio. Por que tombar?` → title: `Vila Amazonas e Vila Serra do Navio` + subtitle: `por que tombar?`
- **Títulos com travessão** como separador de subtítulo: separar em título + subtítulo:
  - `Edifício dos arquitetos da Bahia – uma crítica como obra de arte` → title: `Edifício dos arquitetos da Bahia` + subtitle: `uma crítica como obra de arte`

### Travessão vs. hífen

- **Hífen isolado** (` - `) usado como separador **não é hífen, é travessão** (` — `, em-dash U+2014)
- Aplicar em todos os campos textuais: títulos, subtítulos, nomes de eventos, eixos temáticos, seções
- Exemplos:
  - `Rino Levi - Hespéria nos trópicos` → `Rino Levi — Hespéria nos trópicos`
  - `Mesa 1 - Modos de usar a cidade` → `Mesa 1 — Modos de usar a cidade`
  - `Artigos Completos - Documentação` → `Artigos Completos — Documentação`
  - `Teresina - PI` → `Teresina — PI`
- **Não substituir** hífens que são parte de:
  - Intervalos numéricos: `1930-1960`, `pp. 89-94`
  - Palavras compostas: `art-déco`, `pré-fabricado`
  - Siglas com hífen: `E1-sdbr12`, `AC-CONS-sdnne09`
  - Referências bibliográficas (campo `references`)

### Capitalização (norma brasileira)

Referência: https://funag.gov.br/manual/index.php?title=Mai%C3%BAsculas_e_min%C3%BAsculas

- **Título**: Primeira letra maiúscula
- **Subtítulo**: Começa com minúscula (exceto se iniciar com nome próprio, sigla, etc.)

**Regras específicas:**

| Categoria | Regra | Exemplos |
|-----------|-------|----------|
| Nomes próprios | MAIÚSCULA | Maria, Brasília, UFMT, Docomomo |
| Adjetivos pátrios (isolados) | minúscula | brasileiro, francês, português |
| Adjetivos pátrios em expressão consolidada | Maiúscula | Arquitetura Moderna **Brasileira**, Escola **Paulista** |
| Disciplinas/áreas do saber | Maiúscula | Arquitetura, Urbanismo, História |
| Movimentos/períodos históricos | Maiúscula | Modernismo, Renascimento, Art Déco |
| Conceitos substantivados (período/ideia) | Maiúscula | Modernidade, Brutalismo |
| Expressões consolidadas | Maiúscula | Educação Patrimonial, Patrimônio Cultural, Movimento Moderno, Arquitetura Moderna |
| Regiões geográficas | Maiúscula | Nordeste, Norte, Sudeste |
| Artigos/preposições/conjunções | minúscula | o, a, de, da, e, ou, para |
| Logradouros (nome próprio) | Maiúscula | Praça Sinimbú, Avenida Affonso Penna, Terminal Rodoviário Presidente Kennedy |
| Logradouros (genérico) | minúscula | as praças da cidade, uma avenida arborizada |
| Palavras comuns | minúscula | edifício, casa, projeto, estudo |
| Siglas | MAIÚSCULA | BNB, SESI, SENAI, IPHAN, VANT |
| Séculos (algarismos romanos) | MAIÚSCULA | XX, XXI, XIX, XVIII |

**Consistência em expressões consolidadas:**
- Quando um adjetivo pátrio ou toponímico faz parte de uma expressão consolidada capitalizada, ele também deve ser capitalizado para manter a consistência. Ex: "Arquitetura Moderna Brasileira" (não "Arquitetura Moderna brasileira"), "Urbanismo Moderno Paulista" (não "Urbanismo Moderno paulista").
- Da mesma forma, "Moderna/Moderno" deve acompanhar a capitalização de "Arquitetura/Urbanismo": "Arquitetura Moderna" (não "Arquitetura moderna"), "Urbanismo Moderno" (não "Urbanismo moderno").
- "Modernidade" substantivado (como período ou conceito histórico) leva maiúscula: "a Modernidade brasileira", "imagens da Modernidade paulistana". Quando usado como qualidade abstrata genérica, minúscula: "a modernidade do projeto".

---

## Regras de limpeza de dados

### Affiliation (Afiliação)

O campo `affiliation` deve conter **apenas** a sigla da instituição, no formato `UNIDADE-UNIVERSIDADE`.

**Formato padrão:**

| Original | Normalizado |
|----------|-------------|
| Faculdade de Arquitetura e Urbanismo da USP | FAU-USP |
| Instituto de Arquitetura e Urbanismo da USP | IAU-USP |
| PROPAR UFRGS | PROPAR-UFRGS |
| Faculdade de Arquitetura da UFBA | FAUFBA |
| Faculdade de Arquitetura da UFRGS | FA-UFRGS |
| PROARQ UFRJ | PROARQ-UFRJ |
| MDU - UFPE | MDU-UFPE |
| UNICEP São Carlos | UNICEP |
| AA School of Architecture | AA School |

Se não houver unidade específica, usar apenas a sigla: `USP`, `UFRJ`, `UFBA`, `UFU`, etc.

Para instituições estrangeiras, usar nome abreviado reconhecido internacionalmente.

**Remover:**
- Títulos acadêmicos (Doutor, Mestre, Professor, Graduando)
- Endereços postais (Rua, Av., CEP, etc.)
- ORCID (extrair para campo próprio)
- Emails (já existe campo próprio)
- Nomes completos de faculdades/departamentos (substituir por sigla)

### ORCID

- Extrair do campo afiliação se presente
- Formato padrão: `0000-0000-0000-0000` (sem URL)
- Aceita formatos de entrada: `orcid.org/...`, `https://orcid.org/...`, número direto

### Bio (Biografia)

O campo `bio` deve conter informação acadêmica completa e válida:
- Grau acadêmico + área + instituição (ex: "Doutora em Arquitetura pela FAUUSP")
- Cargo + instituição (ex: "Professora Adjunta da UFCG")

**Remover:**
- Endereços postais (Rua, Av., CEP)
- Informações incompletas (ex: apenas "Arquitetura e Urbanismo" sem contexto)

**Se não houver informação válida:** usar `null`

---

## Processamento de autores

### Separação de nome brasileiro

| Nome completo | givenname | familyname |
|---------------|-----------|------------|
| Maria Beatriz Camargo Cappello | Maria Beatriz Camargo | Cappello |
| Fernando Antonio Oliveira Mello | Fernando Antonio Oliveira | Mello |
| João Carlos da Silva Neto | João Carlos da Silva | Neto |
| Ana Elísia da Costa | Ana Elísia da | Costa |
| Claudia dos Reis e Cunha | Claudia dos Reis e | Cunha |
| Patricia Ataíde Solon de Oliveira | Patricia Ataíde Solon de | Oliveira |

**Regra:** givenname = todos menos o último; familyname = último sobrenome apenas.

**Partículas (de, da, do, dos, das, e):** ficam no `givenname`, não no `familyname`. Isso mantém consistência e evita ambiguidade na ordenação alfabética por sobrenome.

**Nomes hispânicos (duplo sobrenome):** Respeitar a convenção hispânica, mantendo os dois sobrenomes no `familyname`. Ex: `Fernando Guillermo | Vázquez Ramos`, `Pablo Andrés | Maita Zambrano`. Não reduzir a um sobrenome só.

### Normalização de maiúsculas

Listas de referência em `scripts/normalizar_maiusculas.py` e `dict/normalizar.py`:

```python
SIGLAS = {'bnh', 'iphan', 'ufmg', 'usp', ...}  # sempre MAIÚSCULAS
NOMES_PROPRIOS = {'niemeyer', 'brasília', 'pedregulho', ...}  # Capitalizar
```

**Subtítulo:** primeira letra minúscula, exceto se for sigla/nome próprio.

---

## Convenções de IDs

| Tipo | Formato | Exemplo |
|------|---------|---------|
| Artigo nacional | `sdbr{NN}-{NNN}` | sdbr12-001 |
| Artigo N/NE | `sdnne{NN}-{NNN}` | sdnne07-001 |
| Artigo SP | `sdsp{NN}-{NNN}` | sdsp03-001 |
| Artigo Sul | `sdsul{NN}-{NNN}` | sdsul03-001 |
| Artigo Rio | `sdrj{NN}-{NNN}` | sdrj04-001 |
| Seminário | `sdbr{NN}` / `sdnne{NN}` / etc. | sdbr12, sdnne07 |
