# Plano de Tratamento — Seminários Docomomo São Paulo (5º ao 9º)

## Visão geral

Cinco seminários, ~215 artigos no total, todos em formato de PDF compilado (e-book).
A extração requer: (1) split do PDF compilado em PDFs individuais por artigo,
(2) extração de metadados do sumário, (3) criação dos YAMLs.

## Fonte dos dados

| Sem. | PDF | Páginas | Artigos | Seções | ISBN |
|------|-----|---------|---------|--------|------|
| 5º (2017) | pdf1.pdf (6.6 MB) | 1170 | 68 | 3 eixos | 978-85-88157-16-3 |
| 6º (2018) | pdf2.pdf (4.7 MB) | 609 | 37 | 9 mesas | 978-85-66624-25-0 |
| 7º (2020) | sdsp07_anais.pdf (121 MB) | 566 | 43 | 3 eixos | 978-65-00-11912-1 |
| 8º (2022) | pdf_8.pdf (26 MB) | 610 | 36+4h | 3 eixos | 978-65-86810-58-5 |
| 9º (2024) | pdf5.pdf (30 MB) | 409 | 27 | 1 | — |

Publicação adicional: Caderno de Resumos do 6º (pdf3_resumos.pdf, 16 MB, 179 p, ISBN 978-85-66624-22-9)

## Fichas catalográficas

| Sem. | Ficha | Classificação |
|------|-------|---------------|
| 5º | Ausente no PDF. Dados: ISBN 978-85-88157-16-3; Mack Pesquisa/UPM; Org: Anticoli, Critelli, Chiarelli, Ossani | — |
| 6º | S471. CDD 724.98161. Catalogação: Brianda de Oliveira Ordonho Sígolo, CRB-8/8229. IAU/USP | Completa |
| 7º | Ausente. ISBN 978-65-00-11912-1; Livro Digital; PGAUR/USJT | — |
| 8º | S471. CDD 724.98161. Catalogação: Brianda de O. Ordonho Sígolo, CRB-8/8229. IAU/USP | Completa |
| 9º | Ausente. Sem ISBN. UNISANTA/Núcleo Docomomo SP | — |

## Etapas do tratamento

### Etapa 1: Criação dos YAMLs base (metadados da issue + artigos do sumário)

**Para cada seminário:**

1. Parsear o sumário (TOC) do PDF extraído em texto
2. Extrair para cada artigo: título, autores, página inicial
3. Calcular página final de cada artigo (= página inicial do próximo - 1)
4. Mapear artigos às seções/eixos
5. Gerar YAML no formato consolidado (1 arquivo por seminário)

**Formato do sumário por seminário (complexidade de parsing):**

| Sem. | Formato do TOC | Complexidade |
|------|----------------|--------------|
| 5º | `Nome Sobrenome e Nome Sobrenome. Título do artigo. PÁG` | Média — autores inline com título |
| 6º | `TÍTULO EM CAIXA ALTA (Nome Sobrenome \| Nome Sobrenome)` | Baixa — título e autores bem separados |
| 7º | `● Título \| SOBRENOME, Nome; SOBRENOME, Nome \| PÁG` | Baixa — campos separados por pipe |
| 8º | `TÍTULO EM CAIXA ALTA    PÁG` + `SOBRENOME, Nome` na linha seguinte | Média — título e autores em linhas separadas |
| 9º | `TÍTULO EM CAIXA ALTA ..... PÁG` | Média — sem autores no sumário |

**Observações:**
- O 5º é o mais complexo: autores e título na mesma linha, separados por ponto
- O 9º não tem autores no sumário — precisará extrair da primeira página de cada artigo
- O 7º é o mais limpo: campos bem delimitados por `|`

### Etapa 2: Split dos PDFs em artigos individuais

**Para cada seminário:**

1. Usar página inicial/final de cada artigo (da etapa 1)
2. Extrair com `qpdf` ou `pdftk`: `qpdf input.pdf --pages . start-end -- output.pdf`
3. Renomear para padrão `sdsp{NN}-{NNN}.pdf`
4. Verificar tamanhos (>10KB = válido)
5. Descontar páginas preliminares (capa, sumário, comissões, apresentação)

**Páginas preliminares estimadas (antes do 1º artigo):**

| Sem. | 1ª página de artigo | Páginas prelim. |
|------|---------------------|-----------------|
| 5º | p. 13 | 12 |
| 6º | p. 16 (do sumário) | ~15 |
| 7º | p. 21 | 20 |
| 8º | p. 57 (artigos); p. 19 (homenagens) | 18/56 |
| 9º | p. 20 | 19 |

### Etapa 3: Extração de metadados adicionais (resumos, palavras-chave)

**Abordagem:** Extrair texto da primeira página de cada artigo individual (pós-split).
Tipicamente, artigos acadêmicos têm: título, autores, resumo, palavras-chave na 1ª página.

**Por seminário:**

| Sem. | Resumo esperado | Keywords esperadas | Idiomas |
|------|-----------------|-------------------|---------|
| 5º | Sim (padrão acadêmico) | Provável | pt-BR, alguns en/es |
| 6º | Sim | Provável | pt-BR, alguns en/es/it |
| 7º | Sim | Provável | pt-BR, alguns es |
| 8º | Sim | Provável | pt-BR |
| 9º | Sim | Provável | pt-BR |

**Método de extração:**
- Script Python que extrai texto das primeiras 2 páginas de cada PDF individual
- Regex para identificar blocos de Resumo/Abstract e Palavras-chave/Keywords
- Fallback: extração manual ou via LLM para casos ambíguos

### Etapa 4: Normalização

Reutilizar scripts existentes de `regionais/nne/`:

1. **Normalização de maiúsculas** (`normalizar_maiusculas.py`): adaptar dicionários para contexto SP
   - Adicionar nomes próprios SP: Bratke, Artigas, Warchavchik, Niemeyer, Kneese de Mello, Rino Levi, etc.
   - Expressões consolidadas: "São Paulo", "São Carlos", "São Caetano do Sul", "São Judas Tadeu", etc.

2. **Afiliações** (`normalizar_afiliacoes.py`): expandir mapa para instituições SP
   - Frequentes: UPM/Mackenzie, FAU-USP, IAU-USP, USJT, UNIP, UNESP, UNICAMP, UNITAU, Belas Artes, Senac, Escola da Cidade, UNISANTA

3. **Keywords**: limpar trailing punctuation, remover sufixos de seminário

### Etapa 5: Mapeamento de seções

| Sem. | Seções | section_ref |
|------|--------|-------------|
| 5º | Reconhecimento, Intervenção, Gestão | `REC-sdsp05`, `INT-sdsp05`, `GES-sdsp05` |
| 6º | 9 mesas de debate (agrupar por tema?) | `MD1-sdsp06` a `MD9-sdsp06` ou por tema |
| 7º | Eixo 1, Eixo 2, Eixo 3 | `E1-sdsp07`, `E2-sdsp07`, `E3-sdsp07` |
| 8º | 3 eixos + Homenageados | `E1-sdsp08`, `E2-sdsp08`, `E3-sdsp08`, `HOM-sdsp08` |
| 9º | Seção única | `AC-sdsp09` |

**Nota sobre o 6º:** As 9 mesas de debate poderiam ser agrupadas tematicamente:
- Espaços educacionais (mesas 1, 6)
- Análise projetual e patrimonial (mesa 2)
- Habitação (mesas 3, 4, 5)
- Espaços coletivos e culturais (mesas 7, 8)
- Trabalho (mesa 9)

Ou manter as 9 mesas como seções. **Decisão necessária.**

### Etapa 6: Geração de XMLs e importação

(Postergar — mesmo tratamento que sdnne07/sdnne09)

---

## Ordem de processamento recomendada

### 1º: 7º SP (2020) — Mais simples
- TOC bem estruturado (campos separados por `|`)
- 43 artigos
- Eixos já definidos
- PDF grande (121 MB) mas formato limpo

### 2º: 9º SP (2024) — Menor volume
- 27 artigos apenas
- Seção única
- **Complicador:** sem autores no sumário → extrair das primeiras páginas
- **Complicador:** sem ISBN

### 3º: 6º SP (2018) — Formato limpo
- TOC com títulos em caixa alta e autores entre parênteses
- 37 artigos
- 9 mesas → decidir agrupamento

### 4º: 8º SP (2022) — Ficha completa
- TOC com título + autores em linhas separadas
- 36 artigos + 4 homenagens
- 3 eixos definidos
- Ficha catalográfica completa

### 5º: 5º SP (2017) — Mais complexo
- TOC com autores e título misturados na mesma linha
- **68 artigos** (maior volume)
- PDF menor (6.6 MB) apesar de 1170 páginas (baixa resolução?)
- 3 eixos definidos
- Parsing mais difícil

---

## Scripts a criar

| Script | Função | Reutilizável |
|--------|--------|--------------|
| `parsear_sumario_sdsp07.py` | Parsear TOC do 7º (formato pipe) | Parcial |
| `parsear_sumario_sdsp06.py` | Parsear TOC do 6º (formato mesa/caixa alta) | Parcial |
| `parsear_sumario_sdsp08.py` | Parsear TOC do 8º (título + autor em linhas separadas) | Parcial |
| `parsear_sumario_sdsp05.py` | Parsear TOC do 5º (autor.título.página) | Específico |
| `parsear_sumario_sdsp09.py` | Parsear TOC do 9º (só títulos) | Parcial |
| `split_pdf.py` | Dividir PDF compilado em artigos individuais | **Sim** |
| `extrair_metadados_pagina1.py` | Extrair resumo/keywords da 1ª página | **Sim** |
| `gerar_yaml_sp.py` | Gerar YAML consolidado a partir do TOC parseado | **Sim** |

**Reutilizáveis de `regionais/nne/`:**
- `normalizar_maiusculas.py` (adaptar dicionários)
- `normalizar_afiliacoes.py` (expandir mapa)
- `merge_metadados.py` (adaptar para formato SP)

---

## Decisões pendentes

1. **Seções do 6º SP:** Manter 9 mesas ou agrupar por tema?
2. **Homenagens do 8º SP:** Incluir como artigos ou separar?
3. **Caderno de Resumos do 6º:** Publicar como edição separada ou ignorar?
4. **9º SP sem ISBN:** Registrar mesmo assim ou buscar com organizadores?
5. **Eixos do 5º e 7º SP:** Usar nomes completos dos eixos como seções?

---

## Estimativa de volume

| Etapa | Itens | Esforço |
|-------|-------|---------|
| Parsing de sumários | 5 scripts distintos | Alto (cada formato é diferente) |
| Split de PDFs | 215 artigos | Automatizável |
| Extração de metadados | 215 artigos | Automatizável (com revisão manual) |
| Normalização | ~215 títulos, ~500 autores | Médio (adaptar dicionários) |
| Revisão manual | ~10-15% dos artigos | Médio |
| Geração de YAMLs | 5 arquivos | Baixo |

---

*Criado em: 2026-02-08*
