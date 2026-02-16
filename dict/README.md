# dict — NER + Entity Resolution para textos brasileiros

Módulo reutilizável com dois pipelines:

1. **NER** (Named Entity Recognition) — normalização de maiúsculas/minúsculas em títulos e subtítulos, conforme a norma brasileira de capitalização (referência: manual da [FUNAG](https://funag.gov.br/manual/index.php?title=Mai%C3%BAsculas_e_min%C3%BAsculas))
2. **Entity Resolution** — deduplicação de nomes de pessoas, reconhecendo variantes (abreviações, iniciais, partículas) como a mesma entidade

Usado nos Anais Docomomo Brasil e projetado para reuso em outros projetos (Momopedia, etc.).

> **REGRA FUNDAMENTAL**: Todos os dados de dicionário (nomes, siglas, lugares,
> movimentos, toponímicos, expressões) devem residir **exclusivamente no
> `dict.db`**. NUNCA adicionar listas de palavras diretamente nos scripts
> Python. Os scripts leem tudo do banco. Para adicionar entradas: editar
> `init_db.py` e rodar `--reset`, ou inserir diretamente no `dict.db` via
> SQLite.

## Tipologias de erro tratadas

O pipeline aborda 5 tipologias de erro em metadados bibliográficos
(ref: [ner_fontes.md](documentacao/ner_fontes.md)):

| # | Tipologia | Status | Tratamento |
|---|-----------|--------|------------|
| 1 | **OCR / digitação** (substituição de caracteres, fusão de palavras) | Fora de escopo | Dados vêm de Word/Even3, não de OCR. Erros residuais corrigidos na revisão humana (`revisao/`) |
| 2 | **Variância terminológica** ("Concreto Aparente" vs "Béton Brut") | Fora de escopo | Normalizamos capitalização, não vocabulário. Termos preservados como no original |
| 3 | **Ambiguidade de entidades** ("igreja" genérico vs "Igreja da Pampulha") | ✅ Coberto | dict.db distingue por categoria: expressões consolidadas, movimentos, lugares, nomes próprios |
| 4 | **Inconsistência de capitalização** (CAIXA ALTA, Title Case errado) | ✅ Core | `normalizar.py` aplica norma brasileira de capitalização em 3 passadas (palavras → expressões → toponímicos) |
| 5 | **Multilíngue / diacríticos** (acentos, mistura de idiomas) | Parcial | <2% dos títulos são en/es. Acentos preservados. Travessão normalizado (hífen → em-dash) |

A tipologia 4 é o núcleo do módulo. As tipologias 1 e 2 são tratadas pela revisão humana
e estão fora do escopo da normalização automática. A tipologia 3 é resolvida pelo dicionário
de entidades (dict.db). A tipologia 5 é marginal na escala do projeto.

## Regras de capitalização

Tudo minúscula, exceto:

| Categoria | Regra | Exemplos |
|-----------|-------|----------|
| Primeira palavra do título | Maiúscula | `Arquitetura moderna em...` |
| Primeira palavra do subtítulo | minúscula | `...o caso de São Paulo` |
| Siglas | MAIÚSCULA | BNH, USP, IPHAN, CIAM |
| Nomes próprios | Capitalizado | Niemeyer, Reidy, Lucio |
| Lugares | Capitalizado | Brasília, Recife, Nordeste |
| Áreas do saber | Capitalizado | Arquitetura, Urbanismo |
| Movimentos/períodos | Capitalizado | Modernismo, Art Déco |
| Expressões consolidadas | Forma canônica | Patrimônio Cultural, João Pessoa |
| Artigos, preposições, conjunções | minúscula | o, a, de, da, e, ou, para |
| Palavras comuns | minúscula | edifício, casa, projeto |

Casos especiais:
- `d'Alva`, `d'água` — preserva apóstrofo e capitaliza
- Palavras com hífen — cada parte tratada individualmente
- Palavras com barra (`/`) — cada parte tratada individualmente

## Banco de dados

`dict.db` (SQLite, gitignored) contém uma tabela `dict_names`:

```sql
CREATE TABLE dict_names (
    word TEXT PRIMARY KEY,    -- palavra em minúsculas (ou expressão)
    category TEXT NOT NULL,   -- 'sigla', 'nome', 'lugar', 'area', 'movimento', 'expressao'
    canonical TEXT NOT NULL,  -- forma canônica (ex: 'Brasília', 'IPHAN', 'Art Déco')
    source TEXT               -- origem: 'manual', 'autores', etc.
);
```

O dump textual `dict.sql` é versionado no git.

## Pipeline

### 1. Criar o banco

```bash
python3 dict/init_db.py [--reset]
```

Cria `dict.db` com o schema e as entradas manuais iniciais:
- Siglas (UFs, instituições, romanos)
- Áreas do saber
- Movimentos artísticos/históricos
- Lugares (cidades, estados, países, bairros)
- Expressões consolidadas (nomes compostos, topônimos)

### 2. Importar nomes de autores

```bash
python3 dict/seed_authors.py [--source anais.db]
```

Lê a tabela `authors` do banco fonte e extrai cada parte do nome (givenname, familyname) como entrada `nome` no dicionário. Filtra partículas (de, da, do) e iniciais. Não sobrescreve entradas existentes.

Parâmetros para outros projetos:
```bash
python3 dict/seed_authors.py --source momopedia.db --table people --givenname first_name --familyname last_name
```

### 3. Gerar dump

```bash
python3 dict/dump_db.py
```

Gera `dict.sql` para versionamento.

### 4. Normalizar textos

#### Como módulo Python

```python
import sys
sys.path.insert(0, '/caminho/para/anais')
from dict import normalizar_texto

titulo = normalizar_texto("ARQUITETURA MODERNA EM BRASÍLIA")
# → "Arquitetura moderna em Brasília"

subtitulo = normalizar_texto("O CASO DE SÃO PAULO", eh_subtitulo=True)
# → "o caso de São Paulo"
```

#### Na linha de comando

```bash
# Texto único
python3 dict/normalizar.py "ARQUITETURA MODERNA EM BRASÍLIA"

# Subtítulo
python3 dict/normalizar.py --subtitulo "O CASO DE SÃO PAULO"

# Estatísticas do dicionário
python3 dict/normalizar.py --stats

# Pipe (uma linha por entrada)
echo "PATRIMÔNIO CULTURAL NO NORDESTE" | python3 dict/normalizar.py
```

### 5. Aplicar ao banco de artigos

O script `scripts/normalizar_maiusculas.py` usa este módulo para normalizar todos os títulos e subtítulos no `anais.db`:

```bash
# Dry-run (mostra sem alterar)
python3 scripts/normalizar_maiusculas.py --dry-run

# Apenas um seminário
python3 scripts/normalizar_maiusculas.py --slug sdnne05 --dry-run

# Aplicar
python3 scripts/normalizar_maiusculas.py
```

## Manutenção do dicionário

### Adicionar entrada manual

```bash
sqlite3 dict/dict.db "INSERT INTO dict_names VALUES ('petrobras','sigla','PETROBRAS','manual')"
python3 dict/dump_db.py
```

### Categorias

| Categoria | `word` | `canonical` | Aplicação | Exemplo |
|-----------|--------|-------------|-----------|---------|
| **sigla** | minúsculas | MAIÚSCULAS | Sempre | `iphan` → `IPHAN` |
| **nome** | minúsculas | Capitalizado | Sempre | `niemeyer` → `Niemeyer` |
| **lugar** | minúsculas | Capitalizado | Sempre | `brasília` → `Brasília` |
| **area** | minúsculas | Capitalizado | Sempre | `arquitetura` → `Arquitetura` |
| **movimento** | minúsculas | Capitalizado | Sempre | `modernismo` → `Modernismo` |
| **toponimico** | minúsculas | Capitalizado | Contextual | `paulista` → `Paulista` (só após movimento/área) |
| **expressao** | minúsculas (multi-palavra) | Forma canônica | 2a passada (regex) | `joão pessoa` → `João Pessoa` |

**Importante:** Toponímicos NÃO são capitalizados sempre — apenas quando seguem movimento, área ou expressão consolidada (ex: "Brutalismo Paulista", "Arquitetura Moderna Brasileira", "Educação Patrimonial Brasileira"). Quando isolados, ficam em minúscula (ex: "a cultura paulista").

### Prioridade de aplicação

1. Sigla (MAIÚSCULA)
2. Nome próprio (Capitalizado)
3. Lugar (Capitalizado)
4. Área do saber (Capitalizado)
5. Movimento (Capitalizado)
6. Início de frase (Capitalizado) — só para título, não subtítulo
7. Tudo mais → minúscula
8. Expressões consolidadas (segunda passada, regex)
9. Toponímicos contextuais (terceira passada — capitaliza após movimento/área/expressão)

---

## Pipeline 2: Entity Resolution (deduplicação de nomes)

Reconhece que variantes como "M.B. Cappello", "Maria Beatriz Cappello" e "Maria B. C. Cappello" referem-se à mesma pessoa.

### Conceitos

- **Variante**: nome parcial, abreviado ou com partículas diferentes que corresponde ao mesmo indivíduo
- **Confiança alta**: givenname curto tem 2+ palavras reais (menos risco de falso positivo)
- **Confiança baixa**: givenname curto tem ≤1 palavra (ex: "Ana Lima" — pode ser outra Ana)

### Funções disponíveis

```python
from dict.entity_resolution import is_variant, is_abbreviation_of, confidence

# Verificar se dois nomes são a mesma pessoa
is_variant("Maria Beatriz", "Cappello", "M.B.", "Cappello")  # True
is_variant("Ana", "Lima", "Mariana", "Lima")                  # False

# Verificar abreviação
is_abbreviation_of("M.B.", "Maria Beatriz")  # True
is_abbreviation_of("Ana", "Ana Elísia")      # True

# Nível de confiança
confidence("M.B.", "Maria Beatriz")  # 'alta' (2 tokens reais)
confidence("Ana", "Ana Elísia")      # 'baixa' (1 token real)
```

### Algoritmo

1. **Agrupar** por último sobrenome (normalizado, sem acentos)
2. **Comparar** pares dentro de cada grupo:
   - Familyname deve ser idêntico (normalizado)
   - Givenname de um deve ser prefixo/abreviação do outro
   - Primeiro token do curto deve casar com primeiro do longo
   - Tokens do meio devem aparecer em ordem
3. **Classificar** confiança:
   - Alta: givenname curto tem ≥2 palavras reais → merge automático
   - Baixa: givenname curto tem ≤1 palavra → relatório para revisão

### Uso na linha de comando

```bash
# Testar um par
python3 dict/entity_resolution.py "Maria Beatriz" "Cappello" "M.B." "Cappello"

# Rodar suite de testes
python3 dict/entity_resolution.py --test
```

### Integração com deduplicação de autores

O script `scripts/dedup_authors.py` usa estas funções para deduplicar autores no `anais.db`:

```bash
python3 scripts/dedup_authors.py              # Executar dedup (fases 0-3)
python3 scripts/dedup_authors.py --dry-run    # Apenas mostrar o que faria
python3 scripts/dedup_authors.py --report     # Apenas relatório de ambíguos
```

Fases:
1. **Enriquecimento** (Pilotis) — expande nomes via match por email
2. **Merge por último sobrenome** — corrige familyname mal particionado
3. **Merge por variantes** — merge automático de alta confiança
4. **Relatório** — lista casos ambíguos para revisão manual

---

## Arquivos

```
dict/
├── __init__.py              # Exports de ambos os pipelines
├── normalizar.py            # Pipeline 1: NER — normalização de maiúsculas
├── entity_resolution.py     # Pipeline 2: Entity Resolution — dedup de nomes
├── init_db.py               # Cria dict.db com schema + entradas manuais
├── seed_authors.py          # Importa nomes de autores de banco externo
├── seed_titles.py           # Extrai nomes próprios de títulos de artigos
├── dump_db.py               # Gera dict.sql (versionável)
├── dict.sql                 # Dump SQL (versionado)
├── dict.db                  # Banco SQLite (gitignored)
├── .gitignore               # Ignora dict.db
└── README.md                # Este arquivo
```
