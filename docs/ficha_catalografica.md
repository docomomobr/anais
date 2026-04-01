# Ficha Catalográfica — Documento de Referência

Referência técnica sobre normas de elaboração de fichas catalográficas (Catalogação na Publicação — CIP), com foco em anais de eventos acadêmicos.

---

## 0. Decisão do projeto (2026-03-31)

**Seminários anteriores ao sdbr16 (sdbr01-15, regionais, idc06):** Cenário B — o campo `description` do banco contém uma **referência bibliográfica padronizada** (não uma ficha catalográfica formal). O formato segue a função `build_description()` documentada em `modulos_pipeline.md` §H, inspirado na ISBD mas sem notação Cutter, CDD/CDU, assuntos ou crédito de bibliotecário.

**A partir do sdbr16:** Cenário C (híbrido) — manter o campo `description` padronizado (cenário B) para o banco/site/Zenodo, e **produzir ficha catalográfica formal** elaborada por bibliotecário para inclusão no PDF do volume completo.

---

## 1. Base normativa

### 1.1 Legislação

- **Lei 10.753/2003** (Política Nacional do Livro), art. 6°: torna obrigatória a adoção da Catalogação na Publicação e do ISBN para toda publicação de livro no Brasil.

### 1.2 Normas ABNT

| Norma | Título | Escopo |
|-------|--------|--------|
| **NBR 6029:2006** | Informação e documentação — Livros e folhetos — Apresentação | Define que a ficha catalográfica deve ser impressa no verso da folha de rosto |
| **NBR 14724:2011** | Informação e documentação — Trabalhos acadêmicos — Apresentação | Torna a ficha obrigatória para teses, dissertações e TCCs |
| **NBR 12899:1993** | Catalogação na publicação | Norma específica sobre CIP (pouco referenciada na prática, substituída pelos padrões internacionais) |

### 1.3 Padrões internacionais de catalogação

| Padrão | Versão vigente | Escopo |
|--------|----------------|--------|
| **ISBD** (International Standard Bibliographic Description) | Edição Consolidada 2011, atualização 2021 (IFLA) | Define as áreas de descrição bibliográfica e a pontuação prescrita |
| **AACR2** (Anglo-American Cataloguing Rules, 2nd ed.) | 2002 rev. (última atualização 2005) | Código de catalogação — regras de entrada, descrição e pontos de acesso. Mais usado no Brasil |
| **RDA** (Resource Description and Access) | Publicado 2010, atualização contínua | Substituto do AACR2, baseado nos FRBR. Adoção lenta no Brasil; recomendado para recursos digitais |
| **MARC 21** | Atualização contínua (Library of Congress) | Formato de intercâmbio de dados bibliográficos; codifica os campos da ficha em registros legíveis por máquina |
| **CDD** (Classificação Decimal de Dewey) | 23ª ed. | Classificação temática (mais usada em bibliotecas públicas) |
| **CDU** (Classificação Decimal Universal) | Edição-padrão 2005+ | Classificação temática (mais usada em bibliotecas universitárias e de pesquisa) |

### 1.4 Relação entre os padrões

```
ISBD (estrutura e pontuação)
  └── AACR2 / RDA (regras de catalogação — Parte I segue a ISBD)
        └── MARC 21 (codificação em campos numéricos)
              └── Ficha catalográfica (apresentação visual no verso da folha de rosto)
```

A ISBD define a estrutura; o AACR2/RDA define as regras de preenchimento; o MARC 21 codifica para sistemas; a ficha catalográfica é a representação visual impressa.

---

## 2. Áreas de descrição (ISBD)

A descrição bibliográfica é organizada em 9 áreas (0-8). Cada área, exceto a primeira, é precedida de **ponto, espaço, travessão, espaço** (`. — `). Dentro de cada área, subelementos são separados por pontuação prescrita.

| Área | Nome | Pontuação prescrita dos subelementos |
|------|------|--------------------------------------|
| **0** | Forma do conteúdo e tipo de mídia | `: ` (tipo de mídia) |
| **1** | Título e indicação de responsabilidade | `[ ]` natureza do documento; `= ` título paralelo; `: ` complemento do título; `/ ` responsabilidade; `; ` outras menções |
| **2** | Edição | `/ ` responsabilidade relativa à edição |
| **3** | Específica do material | (não usada para monografias) |
| **4** | Publicação, produção, distribuição | `; ` outros lugares; `: ` nome do editor; `, ` data |
| **5** | Descrição física | `: ` ilustrações; `; ` dimensões; `+ ` material acompanhante |
| **6** | Série | `( )` envolvem toda a área; `/ ` responsabilidade; `, ` ISSN; `; ` numeração |
| **7** | Notas | Cada nota em linha separada ou separadas por `. — ` |
| **8** | Identificador do recurso e disponibilidade | `: ` condições de aquisição/preço |

### Sinais de pontuação prescrita — resumo

| Sinal | Significado |
|-------|-------------|
| `. — ` | Separa áreas de descrição |
| `: ` | Complemento, subtítulo, editora |
| `/ ` | Indicação de responsabilidade |
| `; ` | Repetição do elemento anterior (outro lugar, outro autor, outra dimensão) |
| `= ` | Título paralelo |
| `[ ]` | Informação tomada fora da fonte principal |
| `( )` | Série; dados de impressão |
| `, ` | Data (na área 4); ISSN (na área 6) |

---

## 3. Regras de entrada para anais de eventos (AACR2)

### 3.1 Entrada principal por evento (AACR2r 21.1B2d)

Obras que **relatam a atividade coletiva** de uma conferência, congresso, seminário, expedição ou evento recebem entrada principal pelo **nome do evento**, desde que:

1. A obra registre a atividade coletiva (atas, coleções de trabalhos/papers);
2. O evento se enquadre na definição de entidade coletiva (AACR2r 21.1B1);
3. O nome do evento seja mencionado na publicação.

### 3.2 Forma do nome do evento

```
Nome do evento (Número. : Ano : Local)
```

Exemplo:
```
Seminário Docomomo Brasil (16. : 2025 : Porto Alegre)
```

Em MARC 21: campo **111** (Entrada principal — Nome de evento).

### 3.3 Quando NÃO usar entrada por evento

- Se a obra é de um único autor (entrada por autor pessoal)
- Se o evento não é mencionado na publicação
- Se é uma compilação por editor/organizador sem caráter de ata/anais (entrada por título, com organizador como entrada secundária)

---

## 4. Estrutura da ficha catalográfica

### 4.1 Formato e posição

- **Posição:** verso da folha de rosto, parte inferior da página
- **Dimensões:** retângulo de **12,5 cm (largura) x 7,5 cm (altura)**
- **Tipografia:** Arial ou Times New Roman, corpo 10-12pt, espaçamento simples
- **Sem negrito** (exceto eventual destaque do cabeçalho)
- **Numeração:** a página é contada mas não recebe número impresso

### 4.2 Elementos da ficha

```
┌─────────────────────────────────────────────────────────┐
│                 Catalogação na fonte                     │
│                                                         │
│  Notação de autor (Cutter)                              │
│                                                         │
│  Cabeçalho (entrada principal)                          │
│      Título : subtítulo [designação do material] /      │
│  indicação de responsabilidade. — Edição. — Lugar :     │
│  Editora, Ano.                                          │
│      Paginação : ilustrações ; dimensões.               │
│                                                         │
│      Notas.                                             │
│      ISBN xxx-xx-xxxxx-xx-x                             │
│                                                         │
│      1. Assunto. 2. Assunto. I. Entrada secundária.     │
│  II. Título.                                            │
│                                                         │
│                                       CDD xxx.xx        │
│                                       CDU xxx.xx        │
│                                                         │
│  Elaborada por [Nome do bibliotecário] — CRB-X/XXXX     │
│_________________________________________________________│
```

### 4.3 Elementos detalhados

| Elemento | Descrição | Obrigatório |
|----------|-----------|-------------|
| **Notação de autor** | Cutter-Sanborn: inicial do sobrenome + número + inicial do título | Sim |
| **Cabeçalho** | Entrada principal: evento (campo 111) ou autor pessoal (campo 100) | Sim |
| **Título** | Título próprio da publicação | Sim |
| **Subtítulo** | Precedido de `: ` | Se houver |
| **Designação geral do material** | `[recurso eletrônico]`, `[livro eletrônico]` etc. entre colchetes | Se aplicável |
| **Indicação de responsabilidade** | Precedida de `/ `; organizadores, editores, autores | Sim |
| **Edição** | `2. ed.`, `ed. rev.` etc. | Se não for primeira |
| **Lugar de publicação** | Cidade sede da editora | Sim |
| **Editora** | Nome da editora, precedido de `: ` | Sim |
| **Data** | Ano de publicação, precedido de `, ` | Sim |
| **Paginação** | Número de páginas ou volumes | Sim |
| **Ilustrações** | `il.`, `il. color.` etc., precedido de `: ` | Se houver |
| **Dimensões** | Altura em cm, precedida de `; ` | Sim (impresso) |
| **Notas** | Informações complementares (inclui URL de acesso, DOI) | Opcional |
| **ISBN** | Número padrão internacional | Sim (se houver) |
| **Assuntos** | Palavras-chave numeradas; classificação temática | Sim |
| **Entradas secundárias** | Numeradas em romanos (I, II, III...) | Sim |
| **CDD / CDU** | Classificação decimal | Sim |
| **Crédito** | Nome e CRB do bibliotecário responsável | Sim |

---

## 5. Exemplo completo — anais de seminário

### 5.1 Ficha de anais impressos

```
                    Catalogação na publicação

    S471    Seminário Docomomo Brasil (5. : 2003 : São Carlos)
                Anais do 5° Seminário Docomomo Brasil :
            Arquitetura e Urbanismo modernos : projeto e
            preservação [recurso eletrônico] / organização:
            Hugo Segawa. — São Carlos : SAP-EESC-USP, 2003.
                1 recurso online.

                ISBN 85-85205-43-1

                1. Arquitetura moderna. 2. Urbanismo.
            3. Preservação do patrimônio. I. Segawa, Hugo.
            II. Título.

                                            CDD 720.904
                                            CDU 72.036
```

### 5.2 Ficha de anais eletrônicos (e-book / PDF)

```
                    Catalogação na publicação

    S471    Seminário Docomomo Brasil (16. : 2025 : Porto Alegre)
                Anais do 16° Seminário Docomomo Brasil : O
            futuro do passado : Arquitetura Moderna viva e
            urbana [recurso eletrônico] / organização: Carlos
            Eduardo Comas, Claudia Piantá Costa Cabral, Sergio
            M. Marques. — Porto Alegre : Marcavisual Editora,
            2025.
                1 recurso online.

                Modo de acesso: Internet.
                ISBN 978-65-993024-6-6

                1. Arquitetura moderna. 2. Urbanismo.
            3. Patrimônio cultural. 4. Arquitetura brasileira.
            I. Comas, Carlos Eduardo. II. Cabral, Claudia
            Piantá Costa. III. Marques, Sergio M. IV. Título.

                                            CDD 720.904
                                            CDU 72.036

    Elaborada por [Nome] — CRB-X/XXXX
```

---

## 6. Regras específicas para anais de eventos

### 6.1 Entrada principal

- **Pelo nome do evento**, na forma: `Nome do Evento (Número. : Ano : Local)`
- Número ordinal seguido de ponto: `16.`
- Ano e local separados por `: `

### 6.2 Título

- O título próprio dos anais pode ser:
  - "Anais do Xo Seminário..." (se é o título da publicação)
  - O tema/subtítulo do evento, se os anais não têm título próprio
- Subtítulo (tema do evento) precedido de `: `

### 6.3 Designação geral do material

- `[recurso eletrônico]` — para publicações digitais (PDF, e-book, online)
- `[livro eletrônico]` — alternativa aceita
- Posição: após o título/subtítulo, entre colchetes

### 6.4 Responsabilidade

- Organizadores (não autores individuais dos artigos)
- Até 3 nomes: listar todos, separados por vírgula
- 4 ou mais: primeiro nome seguido de `... [et al.]`
- Precedido de `/ organização: ` ou `/ org.`

### 6.5 Imprenta (publicação)

- **Lugar**: cidade sede da editora (não necessariamente a do evento)
- **Editora**: nome da editora (não sigla, exceto se é a forma conhecida)
- **Data**: ano de publicação
- Formato: `Lugar : Editora, Ano.`

### 6.6 Descrição física

- Para recurso eletrônico: `1 recurso online` ou número de páginas do PDF (`362 p.`)
- Para impresso: `xxx p. : il. ; 23 cm`

### 6.7 Notas

- `Modo de acesso: Internet.` (para publicações online)
- `Promovido por [instituição].` (se relevante)
- `Disponível em: <URL>.` (se houver URL de acesso)
- `Também publicado em formato impresso.` (se aplicável)
- `ISSN xxxx-xxxx` (se os anais têm ISSN como periódico)

### 6.8 Assuntos

- Palavras-chave que representam o conteúdo temático
- Numeradas sequencialmente: `1. Assunto. 2. Assunto.`
- Seguidas das entradas secundárias em numeração romana

### 6.9 Entradas secundárias

- Organizadores: `I. Sobrenome, Nome.`
- Título: última entrada secundária: `IV. Título.`
- Instituição promotora (opcional): `V. Universidade Federal...`

### 6.10 Classificação

- **CDD**: Arquitetura moderna = 720.904; Urbanismo = 711
- **CDU**: Arquitetura moderna = 72.036; Urbanismo = 711

---

## 7. Quem elabora

A ficha catalográfica **deve ser elaborada por bibliotecário** com registro no Conselho Regional de Biblioteconomia (CRB), conforme a Lei 4.084/1962. O crédito ao profissional é obrigatório na ficha.

No Brasil, os principais serviços de CIP são:

| Serviço | Escopo |
|---------|--------|
| **CBL** (Câmara Brasileira do Livro) | Editoras comerciais. Serviço pago (R$30 sócios, R$60 não sócios). Prazo: 24h úteis |
| **Bibliotecas universitárias** | Publicações da instituição (anais, livros, teses). Serviço gratuito |
| **Biblioteca Nacional** | Depósito legal e catalogação nacional. ISSN para periódicos |
| **Bibliotecários autônomos** | Serviço terceirizado |

---

## 8. AACR2 vs. RDA — situação no Brasil

| Aspecto | AACR2 | RDA |
|---------|-------|-----|
| Vigência | Publicado 1978, revisado 2002 | Publicado 2010, atualização contínua |
| Status | Não mais atualizado | Substituto oficial do AACR2 |
| Adoção no Brasil | Predominante (maioria das bibliotecas) | Em implantação gradual (desde ~2015) |
| Base teórica | ISBD | FRBR (Functional Requirements for Bibliographic Records) |
| Recursos digitais | Suporte limitado | Projetado para todos os tipos de recurso |
| Formato de saída | MARC 21 | MARC 21 ou outros (linked data) |

O RDA é o padrão recomendado para novas catalogações, especialmente de recursos digitais. Na prática brasileira (2025-2026), a maioria das bibliotecas universitárias e da CBL ainda opera com AACR2 ou uma transição híbrida.

---

## 9. Referências e fontes

### Normas

- ABNT. **NBR 6029:2006** — Informação e documentação — Livros e folhetos — Apresentação.
- ABNT. **NBR 14724:2011** — Informação e documentação — Trabalhos acadêmicos — Apresentação.
- ABNT. **NBR 12899:1993** — Catalogação-na-publicação.
- IFLA. **ISBD: International Standard Bibliographic Description** — Consolidated Edition, 2011 (Update 2021).
- Joint Steering Committee for Development of RDA. **RDA: Resource Description and Access**, 2010-.
- CÓDIGO de Catalogação Anglo-Americano. 2. ed. rev. Brasília: FEBAB, 2004.

### Legislação

- BRASIL. **Lei 10.753, de 30 de outubro de 2003** — Institui a Política Nacional do Livro.
- BRASIL. **Lei 4.084, de 30 de junho de 1962** — Dispõe sobre a profissão de Bibliotecário.

### Fontes consultadas

- CBL — Elementos da ficha catalográfica: https://www.cblservicos.org.br/catalogacao/elementos-da-ficha-catalografica/
- CBL — Catalogação: https://www.cblservicos.org.br/catalogacao/
- UFSC — Catalogação na fonte: https://portal.bu.ufsc.br/servicos/catalogacao-na-fonte/
- Assumpção, Fabrício — Síntese sobre pontos de acesso (AACR2): https://fabricioassumpcao.com/2016/03/aacr2-escolha-dos-pontos-de-acesso.html
- Assumpção, Fabrício — Bibliografia brasileira sobre RDA: https://fabricioassumpcao.com/bibliografia-rda
- Mettzer — Guia de ficha catalográfica: https://blog.mettzer.com/ficha-catalografica/
- Câmara Municipal de Alpiarça (PT) — Zonas ISBD: https://www.alpiarca.pt/biblioteca/mp/catalogacao_zonas_isbd.html
- IFLA — ISBD Consolidada (repositório): https://repository.ifla.org/items/a696641d-f3c5-4512-bdee-3663b3e7f7ac
