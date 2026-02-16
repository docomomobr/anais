# Devlog — Normalização de maiúsculas

Data: 2026-02-16

## Contexto

Os títulos e subtítulos dos 2394 artigos no `anais.db` tinham capitalização inconsistente: alguns em ALL CAPS, outros em Title Case (americano), outros misturados. A norma brasileira exige sentence case com exceções para nomes próprios, siglas, áreas do saber, movimentos e expressões consolidadas.

## Pipeline de normalização

O módulo `dict/normalizar.py` faz a normalização em 3 passadas:

1. **Palavra a palavra**: cada word é checada contra 7 categorias no `dict.db` (sigla, nome, lugar, area, movimento, toponímico, expressão). Se encontrada, aplica a forma canônica. Se não, minusculiza (exceto primeira do título).

2. **Expressões consolidadas**: regex `\b`-delimitado substitui expressões multi-palavra pela forma canônica (ex: "movimento moderno" → "Movimento Moderno", "arte moderna" → "Arte Moderna").

3. **Toponímicos contextuais**: adjetivos pátrios são capitalizados quando precedidos por movimento ou área (ex: "Arquitetura moderna brasileira" → "Arquitetura Moderna Brasileira").

## Bugs corrigidos

### 1. Expressões sem word boundary

**Problema**: `re.compile(re.escape(expr), re.IGNORECASE)` casava "porto nacional" dentro de "aeroporto nacional", transformando em "aeroPorto Nacional".

**Fix**: Adicionar `\b` word boundaries: `re.compile(r'\b' + re.escape(expr) + r'\b', re.IGNORECASE)`.

### 2. `?` e `!` não trigavam nova frase

**Problema**: Apenas `.` era detectado como fim de frase. Em títulos como "Estilo ou causa? como, quando e onde?", o "como" ficava minúsculo.

**Fix**: Checar `prev.endswith('?')` e `prev.endswith('!')` além de `.`.

### 3. Abreviações curtas trigavam nova frase

**Problema**: "Jr.", "h.", "m.", "Dr." terminam com ponto e trigavam capitalização da palavra seguinte (ex: "Jr. E" em vez de "Jr. e").

**Fix**: Se o núcleo da palavra antes do ponto tem ≤3 caracteres, não tratar como fim de frase.

### 4. Trailing period removido de abreviações

**Problema**: `texto.rstrip('.')` removia o ponto de "E.U.A.", transformando em "E.U.A".

**Fix**: Só remover trailing period se a última palavra não tem pontos internos.

## Falsos positivos removidos do dicionário

Palavras comuns que estavam incorretamente classificadas como nomes/lugares/siglas:

| Palavra | Categoria | Motivo da remoção |
|---------|-----------|-------------------|
| são | lugar | Verbo "ser" (3ª plural): "não são ilhas" → "não São ilhas" |
| se | sigla (Sergipe) | Pronome reflexivo: "cria-se" → "cria-SE" |
| al | sigla (Alagoas) | Preposição espanhola: "al día" → "AL día" |
| ma | sigla (Maranhão) | Conjunção italiana: "ma non troppo" → "MA non troppo" |
| to | sigla (Tocantins) | Preposição inglesa: muito comum |
| espírito | lugar | Substantivo: "o espírito do Brutalismo" → "o Espírito..." |
| dias | nome | Substantivo: "nos dias atuais" → "nos Dias atuais" |
| leite | nome | Substantivo: "o leite" → "o Leite" |
| fontes | nome | Substantivo: "novas fontes" → "novas Fontes" |
| grande | lugar | Adjetivo: "ser grande" → "ser Grande" |
| fora | lugar | Advérbio: "fora do Brasil" → "Fora do Brasil" |
| jardim | nome | Substantivo: "o jardim" → "o Jardim" |
| núcleo | nome | Substantivo: "o núcleo" → "o Núcleo" |
| paixão | nome | Substantivo: "a paixão" → "a Paixão" |
| campos | nome | Substantivo: "nos campos" → "nos Campos" |
| norte | lugar | Substantivo/direção: "el norte chileno" → "el Norte..." |
| ferro | nome | Substantivo: "o ferro" → "o Ferro" |
| massa | nome | Substantivo: "a massa" → "a Massa" |
| porto | lugar | Substantivo: "o porto" → "o Porto" |
| concepción | lugar | Substantivo espanhol: "concepción" = concepção |
| gerais | nome | Adjetivo: "condições gerais" → "condições Gerais" |
| ares | nome | Substantivo: "os ares" → "os Ares" |
| alvorada | nome | Substantivo: "a alvorada" → "a Alvorada" |
| homem | nome | Substantivo: "o homem" → "o Homem" |
| milagre | nome | Substantivo: "o milagre" → "o Milagre" |
| ciudad | nome | Substantivo espanhol: "la ciudad" → "la Ciudad" |
| cidade moderna | expressão | Genérico demais, causava capitalização indevida |

**Padrão**: palavras ambíguas (substantivo comum E nome próprio/lugar) devem ser tratadas via **expressões** (multi-palavra), nunca como entradas standalone. Ex: "Porto" standalone → remove; "Porto Alegre", "Porto Nacional" → mantém como expressão.

## Siglas de 2 letras — lição aprendida

Siglas de estados brasileiros com 2 letras conflitam com palavras comuns em português, espanhol e italiano. Removidas: SE, AL, MA, TO. Mantidas (menos ambíguas): SP, RJ, MG, BA, PE, etc.

Numerais romanos (I, II, III, IV, V, VII, VIII, X, XI, XII, XIII, XIV, XV, XX) adicionados como siglas para manter uppercasing.

## Mixed-case: MoMA e UnB

Siglas com case misto não funcionam com a categoria `sigla` (que sempre uppercaseia). Solução: registrar como `nome` com canonical em mixed case.

## Entradas adicionadas

O dicionário cresceu de ~3687 para 4270 entradas (+580):

| Categoria | Antes | Depois | Novas |
|-----------|-------|--------|-------|
| siglas | ~260 | 275 | ~15 (ABCP, CBI, CECAP, TPA, FIFA + numerais romanos) |
| nomes | ~2700 | 3042 | ~340 (nomes de arquitetos, artistas, pesquisadores) |
| lugares | ~260 | 292 | ~32 (butantã, chandigarh, havana, mantiqueira, etc.) |
| áreas | 6 | 7 | 1 (arquitectura → area) |
| movimentos | ~20 | 31 | ~11 (tropicália, concretismo, purismo, brutalista, etc.) |
| toponímicos | ~170 | 171 | ~1 |
| expressões | ~390 | 449 | ~59 (Arte Moderna, Centro Histórico, Carta de Atenas, etc.) |

## Resultado

- **469 artigos regionais** (de 987) tiveram títulos/subtítulos normalizados
- **664 artigos nacionais** teriam mudanças mas não foram alterados (já publicados no OJS)
- Dump atualizado: `anais.sql` e `dict/dict.sql`

## Limitações conhecidas

1. **Ambiguidade inerente**: "Modernidade" pode ser período histórico (maiúscula) ou qualidade abstrata (minúscula). O normalizador sempre capitaliza — revisão manual necessária para os poucos casos de uso genérico.

2. **Nomes de instituições**: "Universidade Federal de...", "Instituto de...", "Escola de..." são lowercased pela norma (termos genéricos), o que pode parecer errado. Instituições específicas devem ser adicionadas como expressões.

3. **Títulos em idiomas estrangeiros**: Títulos em espanhol e inglês seguem as mesmas regras de capitalização (sentence case). Isso pode parecer estranho para títulos em inglês (que normalmente usam title case), mas é consistente com a norma.

4. **init_db.py desatualizado**: As entradas foram adicionadas diretamente no `dict.db`. O `init_db.py` não foi atualizado com todas as novas entradas. Para reproduzir o dicionário do zero, usar `dict.sql`.
