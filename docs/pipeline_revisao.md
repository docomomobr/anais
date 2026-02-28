# Pipeline de Revisão de Metadados

Pipeline para revisão humana dos metadados dos artigos no `anais.db`. Complementa o [pipeline de tratamento](pipeline_tratamento.md) (fases 1-7) e antecede o [pipeline de produção](pipeline_producao.md) (Zenodo + Hugo).

A revisão é necessária porque a extração automatizada dos PDFs produz erros sistemáticos: títulos com capitalização errada, resumos truncados, keywords faltantes, referências concatenadas ou ausentes. A revisão humana corrige esses problemas seminário a seminário.

### Ciclo de aprendizado

O pipeline é cumulativo: cada seminário revisado melhora a revisão dos seguintes.

```
Seminário N                          Seminário N+1
┌──────────┐                         ┌──────────┐
│ Revisão  │──→ novos nomes próprios  │ Revisão  │
│ automát. │    novos topônimos  ──→  │ automát. │ (mais precisa)
│          │    novas expressões      │          │
│ Revisão  │──→ padrões confirmados   │ Revisão  │
│ humana   │    regras de exceção ──→ │ humana   │ (menos correções)
└──────────┘                         └──────────┘
       │                                    │
       ▼                                    ▼
   dict.db                              dict.db
   (+N entradas)                        (+N entradas)
   MEMORY.md                            MEMORY.md
   (padrões confirmados)                (padrões confirmados)
```

Fontes de aprendizado:
- **`dict.db`** (~5.300 entradas): nomes de autores (`seed_authors.py`), nomes próprios extraídos dos títulos (`seed_titles.py`), expressões consolidadas e topônimos adicionados manualmente durante a revisão
- **`MEMORY.md`**: padrões de capitalização confirmados na revisão humana (ex: "Arquitetura Moderna" sempre maiúscula, "modernismo" isolado em minúscula, "Centro" de cidade em maiúscula)
- **`regras_dados.md`**: regras formalizadas a partir de decisões tomadas durante a revisão

Quanto mais seminários forem revisados, menos correções manuais serão necessárias nos seguintes — a revisão automática (Fase 1) fica progressivamente mais precisa.

---

## Seminários revisados — NÃO ALTERAR

| Seminário | Artigos | Data | Observações |
|-----------|---------|------|-------------|
| sdbr01 | 37 | 2026-02-24 | |
| sdbr02 | 22 | 2026-02-24 | |
| sdbr03 | 56 | 2026-02-26 | 39 títulos, 160+ refs extraídas de notas |
| sdbr04 | 79 | 2026-02-26 | Só resumos, sem refs nem texto completo |
| sdbr05 | 56 | 2026-02-28 | 25 títulos corrigidos, 971 refs limpas, backfills dots/dashes |

---

## Visão geral do fluxo

```
┌─────────────────────────────────────────────────────┐
│ Fase 0 — Diagnóstico de padrão e preenchimento      │
│   0.1 Levantar padrão de metadados do seminário     │
│   0.2 Identificar artigos fora do padrão            │
│   0.3 Reinspecionar PDFs dos artigos fora do padrão │
│   0.4 Preencher lacunas no banco                    │
├─────────────────────────────────────────────────────┤
│ Fase 1 — Revisão automática (Claude)                │
│   1.1 Títulos e subtítulos (LLM + PDF)              │
│   1.2 Referências (clean + check + extração)        │
│   1.3 Aplicar todas as correções ao banco           │
├─────────────────────────────────────────────────────┤
│ Fase 2 — Gerar HTML de revisão                      │
├─────────────────────────────────────────────────────┤
│ Fase 3 — Revisão humana (usuário)                   │
│   3.1 Revisar HTML no navegador                     │
│   3.2 Anotar correções em arquivo .md ou .txt       │
├─────────────────────────────────────────────────────┤
│ Fase 4 — Aplicar correções da revisão humana        │
├─────────────────────────────────────────────────────┤
│ Fase 5 — Fechar revisão                             │
│   5.1 Rodar pipeline final (clean + check)          │
│   5.2 Regenerar HTML (verificação)                  │
│   5.3 Atualizar status (CLAUDE.md, memória)         │
│   5.4 Dump + commit + push                          │
└─────────────────────────────────────────────────────┘
```

---

## Fase 0 — Diagnóstico de padrão e preenchimento de lacunas

Antes de qualquer revisão, identificar o **padrão de metadados do seminário** e preencher as lacunas nos artigos que desviam desse padrão. A lógica é simples: se a maioria dos artigos tem um campo (ex: keywords), os poucos que não têm provavelmente tinham o dado no PDF e ele se perdeu na extração. Mas se nenhum artigo tem o campo, é porque o evento não exigia — e não adianta buscar.

### 0.1 Levantar padrão de metadados

Consultar o banco para cada campo relevante:

```sql
SELECT
  COUNT(*) as total,
  SUM(CASE WHEN abstract IS NOT NULL AND abstract != '' THEN 1 ELSE 0 END) as tem_abstract,
  SUM(CASE WHEN abstract_en IS NOT NULL AND abstract_en != '' THEN 1 ELSE 0 END) as tem_abstract_en,
  SUM(CASE WHEN keywords IS NOT NULL AND keywords != '' AND keywords != '[]' THEN 1 ELSE 0 END) as tem_kw,
  SUM(CASE WHEN keywords_en IS NOT NULL AND keywords_en != '' AND keywords_en != '[]' THEN 1 ELSE 0 END) as tem_kw_en,
  SUM(CASE WHEN references_ IS NOT NULL AND references_ != '' AND references_ != '[]' THEN 1 ELSE 0 END) as tem_refs
FROM articles WHERE seminar_slug = '{slug}';
```

Classificar cada campo como:
- **Padrão presente** (≥70% dos artigos têm): buscar nos PDFs dos artigos faltantes
- **Padrão ausente** (<30% dos artigos têm): não buscar — é característica do evento
- **Intermediário** (30-70%): avaliar caso a caso, pode ser um subconjunto (ex: pôsteres sem abstract)

### 0.2 Identificar artigos fora do padrão

Para cada campo classificado como "padrão presente", listar os artigos que **não** têm o campo. Esses são os candidatos a reinspecção de PDF.

```sql
-- Exemplo: artigos sem abstract num seminário onde abstract é padrão
SELECT file, title FROM articles
WHERE seminar_slug = '{slug}' AND (abstract IS NULL OR abstract = '');
```

### 0.3 Reinspecionar PDFs

Para cada artigo fora do padrão, extrair texto do PDF e buscar o campo faltante:
- **Abstract/resumo**: geralmente após o título e autores, antes das keywords
- **Keywords**: geralmente após o abstract, marcadas com "Palavras-chave:" ou "Keywords:"
- **Referências**: geralmente no final do artigo, sob "Referências", "Bibliografia", "Notas"
- **Abstract EN**: após o abstract PT ou no final do artigo

Usar `pdftotext` para extração. Para PDFs escaneados, verificar com `pdfinfo` e usar `ocrmypdf` se necessário.

### 0.4 Preencher lacunas no banco

Aplicar os dados extraídos ao banco. Reportar:
- Quantos artigos estavam fora do padrão por campo
- Quantos foram preenchidos com sucesso
- Quantos genuinamente não têm o dado (confirmar no PDF)

---

## Fase 1 — Revisão automática

O Claude executa verificações automatizadas e aplica correções ao banco **antes** de gerar o HTML de revisão, para que o humano revise o estado já corrigido.

### 1.1 Títulos e subtítulos

**Objetivo:** Corrigir capitalização conforme norma brasileira (sentence case com dict.db).

```bash
# 1. Alimentar dicionário com nomes novos
python3 dict/seed_authors.py
python3 dict/seed_titles.py --apply
python3 dict/dump_db.py

# 2. Normalizar
python3 scripts/normalizar_maiusculas.py --slug {slug} --dry-run
python3 scripts/normalizar_maiusculas.py --slug {slug}
```

**Verificação adicional com LLM:** Após a normalização automática, o Claude compara cada título com o PDF original para detectar:
- Nomes próprios de edifícios/lugares que ficaram em minúscula
- Termos genéricos que ficaram em maiúscula indevida
- Subtítulos que deveriam começar com minúscula (ou vice-versa)
- Separação incorreta entre título e subtítulo

Os critérios de capitalização estão em [`docs/regras_dados.md`](regras_dados.md) e na memória do projeto.

**Retroalimentação do dicionário:** Após aplicar as correções do LLM, incorporar os aprendizados ao `dict.db` para que o normalizador automático acerte nos seminários seguintes:

1. **Novos nomes próprios** (LLM capitalizou algo que o normalizador não conhecia):
   - Edifícios, lugares, instituições → adicionar à tabela `nomes` ou `expressoes`
   - Ex: "Esplanada" (nome de edifício), "Vila Operária" (nome próprio)
2. **Novas expressões consolidadas** (LLM manteve maiúscula em expressão multi-palavra):
   - Ex: "Brutalismo Paulista", "Plano Agache"
   - Adicionar à tabela `expressoes` do `dict.db`
3. **Falsos positivos** (LLM corrigiu algo que o normalizador ou o PDF deixou em maiúscula indevida):
   - Verificar se a palavra está no `dict.db` como nome próprio e não deveria estar
   - Se estiver, remover a entrada
4. **Padrões confirmados**: registrar em `MEMORY.md` para referência futura

```bash
# Verificar se as correções implicam mudanças no dict.db:
python3 -c "
import sqlite3
conn = sqlite3.connect('dict/dict.db')
cur = conn.cursor()
# Adicionar expressões novas
for expr in ['Nova Expressão', ...]:
    cur.execute('INSERT OR IGNORE INTO expressoes (expressao) VALUES (?)', (expr,))
# Adicionar nomes novos
for nome in ['NovoNome', ...]:
    cur.execute('INSERT OR IGNORE INTO nomes (nome) VALUES (?)', (nome,))
conn.commit()
"
python3 dict/dump_db.py
```

### 1.2 Referências

**Objetivo:** Limpar, verificar e extrair referências faltantes.

```bash
# Limpeza automática
python3 scripts/clean_references.py --slug {slug} --dry-run
python3 scripts/clean_references.py --slug {slug}

# Verificação
python3 scripts/check_references.py --slug {slug} --summary
```

**Artigos com 0 referências:** Verificar nos PDFs se há seção de referências ou notas de rodapé com citações. Se houver, extrair seguindo o procedimento documentado em `pipeline_tratamento.md` §2.1b (referências) ou §2.1c (notas de rodapé).

**Varredura completa de TODAS as referências:** O `check_references.py` detecta apenas padrões específicos (concatenadas, fragmentos curtos). Ele **não detecta**: notas de rodapé misturadas, agradecimentos, cabeçalhos de seção ("FONTES PRIMÁRIAS:", "Artigos de jornais:"), créditos de ilustração, refs quebradas em múltiplas linhas, nem backfills pendentes com padrões incomuns (`---------`, `––––––`). É obrigatório varrer as referências de **todos os artigos** do seminário, não apenas os sinalizados pelos scripts. Fazer isso programaticamente:

```python
# Verificação completa: backfills, não-refs, fragmentos, quebras de linha
for art in articles:
    for ref in art.references:
        # Backfill pendente (qualquer variante de underscores/traços)
        if re.match(r'^[-–—_]{3,}', ref.strip()):
            flag("backfill pendente")
        # Não-referência (agradecimentos, créditos, cabeçalhos)
        if any(x in ref.lower() for x in ['crédito', 'ilustraç', 'agradec',
               'fapesp', 'cnpq', 'capes', 'fontes primárias', 'artigos de jornais']):
            flag("possível não-referência")
        # Ref quebrada em linha (começa com minúscula, ou < 30 chars sem ser URL)
        if ref[0].islower() or (len(ref) < 30 and not ref.startswith('http')):
            flag("possível fragmento / quebra de linha")
```

**Meta:** < 2% de problemas por seminário.

### 1.3 Aplicar correções ao banco

Todas as correções das etapas 1.1–1.2 são aplicadas ao `anais.db`. Reportar contagens (N títulos, N refs corrigidas).

**Nota:** Resumos, abstracts e keywords faltantes já foram tratados na Fase 0. A Fase 1 foca apenas em **corrigir** dados existentes (capitalização de títulos, limpeza de refs), não em preencher lacunas.

---

## Fase 2 — Gerar HTML de revisão

```bash
python3 scripts/gerar_revisao_html.py {slug}
```

Gera `revisao/revisao-{slug}.html` com:
- Capa do seminário (se houver)
- Ficha catalográfica
- Artigos agrupados por seção
- Para cada artigo: título, subtítulo, autores (com afiliação), resumo PT, abstract EN, keywords PT/EN, referências

Abrir no navegador para revisão humana.

---

## Fase 3 — Revisão humana

O usuário revisa o HTML no navegador e anota as correções necessárias.

### O que verificar

| Campo | O que procurar |
|-------|----------------|
| **Título** | Capitalização, separação título/subtítulo, acentuação |
| **Subtítulo** | Começa com minúscula (exceto nome próprio/sigla) |
| **Autores** | Nomes corretos, ordem, partículas no givenname |
| **Resumo PT** | Completo, não truncado |
| **Abstract EN** | Presente quando o PDF tem, não truncado |
| **Keywords PT** | Presentes, corretas |
| **Keywords EN** | Presentes, corretas |
| **Referências** | Presentes, sem concatenações, sem lixo |
| **Ficha catalográfica** | ISBN, editora, organizadores, ano |
| **Seções** | Artigos na seção correta |

### Formato das anotações

O usuário anota correções em arquivo markdown (`revisao/{slug}-rev.md`) ou comunica diretamente ao Claude. Formato sugerido:

**Correções de campos específicos:**
```yaml
sdbr05-034:
    title: 'Museu de Arte de São Paulo'

sdbr05-008:
    title: 'O edifício Esplanada em Santos'
    subtitle: 'uma análise tipológica'
```

**Referências com `______` / `--------` (autor repetido não expandido):**

Basta indicar os artigos afetados — o Claude localiza as refs, identifica o autor da ref anterior e preenche automaticamente. Não é necessário informar qual é o autor.

```
refs com ______: 012, 029, 049
```

**Outros problemas em referências:**
```
sdbr05-012:
    refs: concatenadas (verificar)

sdbr05-049:
    refs: lixo misturado (notas de rodapé, legendas)
```

**Campos faltantes (resumo, keywords, abstract):**
```
sdbr05-045:
    abstract_en: falta (tem no PDF)

sdbr05-010:
    keywords_en: falta
```

---

## Fase 4 — Aplicar correções da revisão humana

**REGRA**: O arquivo de revisão (`revisao/{slug}-rev.md`) é uma lista de instruções. O Claude deve executar **todos** os itens da lista, sem exceção. Não executar metade. Não pular itens. Não misturar com outras tarefas.

**Procedimento obrigatório:**

1. **Ler o arquivo inteiro** antes de começar qualquer correção
2. **Listar todos os itens** encontrados (ex: "12 itens: sdbr05-003, 010, 015, 016, 019, 020, 028, 030, 031, 039, 043, ...")
3. **Executar cada item**, na ordem em que aparece no arquivo
4. **Verificar cada item** após execução — consultar o banco para confirmar que a correção foi aplicada
5. **Reportar o resultado** como checklist completa, item a item, com ✅ ou ❌
6. Só depois de todos os itens verificados: atualizar o YAML e regenerar o HTML

**O que NÃO fazer:**
- Não buscar outros problemas enquanto executa a lista — isso é trabalho da Fase 1, não da Fase 4
- Não aplicar metade dos itens e perguntar ao usuário se pode continuar
- Não misturar itens da lista com correções que o Claude encontrou por conta própria

---

## Fase 5 — Fechar revisão

### 5.1 Pipeline final

```bash
python3 scripts/clean_references.py --slug {slug}
python3 scripts/check_references.py --slug {slug} --summary
```

Resultado esperado: 0 problemas (ou apenas problemas aceitos conscientemente).

### 5.2 Regenerar HTML (verificação opcional)

```bash
python3 scripts/gerar_revisao_html.py {slug}
```

O usuário pode dar uma olhada rápida para confirmar que as correções foram aplicadas.

### 5.3 Alimentar dicionário (aprendizado)

Incorporar ao `dict.db` os nomes próprios e padrões descobertos durante a revisão:

```bash
# Nomes de autores novos
python3 dict/seed_authors.py

# Nomes próprios dos títulos (edifícios, lugares, obras)
python3 dict/seed_titles.py --apply

# Dump do dicionário
python3 dict/dump_db.py
```

Se a revisão humana revelou expressões consolidadas novas (ex: "Vila Operária" como nome próprio) ou exceções de capitalização, adicioná-las manualmente ao `dict.db`. Registrar padrões confirmados na memória do projeto (`MEMORY.md`) para referência futura.

### 5.4 Atualizar status

- Adicionar seminário à tabela de revisados em `CLAUDE.md` e neste documento
- Atualizar memória do projeto com padrões confirmados

### 5.5 Dump, commit e push

```bash
python3 scripts/dump_anais_db.py
git add anais.sql CLAUDE.md
git commit -m "Revisão {slug}: N títulos, N refs, N resumos corrigidos"
git push
```

---

## Classificação dos seminários por esforço

Diagnóstico gerado em 2026-02-28. Critérios: % de artigos sem abstract, sem referências, sem keywords.

### Revisão leve — 1.307 artigos (52%)

Precisam apenas de normalização automática de títulos + revisão rápida no HTML. Poucos campos faltantes.

| Slug | Arts | s/abs | s/ref | s/kw | Observações |
|------|------|-------|-------|------|-------------|
| sdbr05 | 56 | 0% | 0% | 18% | Correções aplicadas, aguarda revisão humana |
| sdbr11 | 101 | 3% | 3% | 2% | |
| sdbr12 | 82 | 0% | 4% | 0% | |
| sdbr13 | 181 | 5% | 5% | 5% | |
| sdbr14 | 122 | 1% | 3% | 2% | |
| sdbr15 | 101 | 2% | 2% | 1% | |
| sdnne01 | 44 | 0% | 2% | 0% | |
| sdnne02 | 33 | 3% | 9% | 6% | |
| sdnne03 | 41 | 0% | 0% | 7% | |
| sdnne05 | 32 | 0% | 6% | 0% | |
| sdnne07 | 65 | 3% | 8% | 3% | |
| sdnne08 | 41 | 0% | 0% | 2% | |
| sdnne09 | 50 | 0% | 0% | 2% | |
| sdnne10 | 85 | 0% | 4% | 0% | |
| sdsp03 | 74 | 0% | 16% | 1% | |
| sdsp05 | 68 | 0% | 7% | 0% | |
| sdsp06 | 37 | 0% | 3% | 0% | |
| sdsp07 | 43 | 0% | 2% | 0% | |
| sdsp09 | 27 | 0% | 7% | 4% | |
| sdsul06 | 24 | 4% | 0% | 8% | |

### Revisão moderada — 589 artigos (24%)

Lacunas pontuais: keywords faltantes, algumas referências, poucos abstracts ausentes. Requer extração parcial dos PDFs.

| Slug | Arts | s/abs | s/ref | s/kw | Observações |
|------|------|-------|-------|------|-------------|
| sdbr10 | 118 | 22% | 24% | 14% | |
| sdnne04 | 45 | 0% | 27% | 2% | |
| sdnne06 | 104 | 0% | 44% | 1% | 46 artigos só resumo (sem texto completo) |
| sdrj04 | 17 | 6% | 12% | 12% | |
| sdsp08 | 40 | 10% | 8% | 10% | |
| sdsul01 | 48 | 0% | 10% | 98% | Keywords quase totalmente faltantes |
| sdsul02 | 35 | 20% | 3% | 29% | |
| sdsul03 | 39 | 15% | 15% | 23% | |
| sdsul04 | 46 | 7% | 22% | 17% | |
| sdsul07 | 46 | 15% | 2% | 100% | Keywords totalmente faltantes |
| sdsul08 | 51 | 4% | 4% | 100% | Keywords totalmente faltantes |

### Revisão pesada — 611 artigos (24%)

Muitos abstracts e/ou referências faltantes. Requer extração extensiva dos PDFs.

| Slug | Arts | s/abs | s/ref | s/kw | Observações |
|------|------|-------|-------|------|-------------|
| sdbr06 | 64 | 91% | 31% | 22% | Quase todos sem abstract |
| sdbr07 | 62 | 31% | 18% | 34% | |
| sdbr08 | 184 | 49% | 24% | 22% | Maior seminário, muitas lacunas |
| sdbr09 | 170 | 20% | 69% | 20% | 69% sem referências |
| sdmg01 | 26 | 35% | 23% | 31% | |
| sdpr01 | 26 | 31% | 31% | 35% | |
| sdpr02 | 19 | 47% | 0% | 74% | |
| sdrj02 | 19 | 58% | 63% | 100% | |
| sdrj03 | 4 | 0% | 100% | 100% | Apenas 4 artigos |
| sdsul05 | 37 | 30% | 3% | 5% | |

---

## Estratégia de publicação em ondas

Para não bloquear a publicação pelo esforço de revisão dos seminários mais problemáticos:

1. **Onda 1** — Seminários em bom estado (1.307 artigos, 20 seminários): rodar Fase 1 automática + revisão humana rápida. Publicar.
2. **Onda 2** — Seminários com lacunas pontuais (589 artigos, 11 seminários): extrair campos faltantes dos PDFs + revisão humana. Publicar.
3. **Onda 3** — Seminários problemáticos (611 artigos, 10 seminários): extração extensiva, possivelmente com GROBID ou LLM para referências. Publicar.

Cada onda segue o mesmo fluxo (Fases 1-5). Os seminários já revisados (sdbr01-04) e os nacionais já publicados no OJS não entram no pipeline.

---

## Referência rápida

| Comando | Fase | Função |
|---------|------|--------|
| `dict/seed_authors.py` + `seed_titles.py --apply` + `dump_db.py` | 1.1 | Alimentar dicionário |
| `scripts/normalizar_maiusculas.py --slug {slug}` | 1.1 | Normalizar títulos |
| `scripts/clean_references.py --slug {slug}` | 1.2 | Limpar referências |
| `scripts/check_references.py --slug {slug} --summary` | 1.2 | Verificar referências |
| `scripts/gerar_revisao_html.py {slug}` | 2 | Gerar HTML de revisão |
| `scripts/dump_anais_db.py` | 5.4 | Dump do banco |
