# Pipeline de Revisão Automática de Metadados

Pipeline para revisão automática dos metadados dos artigos no `anais.db`. Complementa o [pipeline de tratamento](pipeline_tratamento.md) (fases 1-7) e antecede o [pipeline de revisão humana](pipeline_revisao_humana.md) (Fases 3–5).

A revisão é necessária porque a extração automatizada dos PDFs produz erros sistemáticos: títulos com capitalização errada, resumos truncados, keywords faltantes, referências concatenadas ou ausentes. O pipeline automático corrige os problemas detectáveis por heurísticas; o que escapar vai para a revisão humana.

**IMPORTANTE:** Este pipeline roda **uma única vez** por seminário, **antes** da revisão humana. Após a revisão humana ter corrigido títulos, subtítulos e outros campos, **nunca** re-rodar este pipeline no mesmo seminário — scripts como `normalizar_maiusculas.py` sobrescreveriam os ajustes manuais.

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

## Visão geral do fluxo

```
┌─────────────────────────────────────────────────────┐
│ Fase 0 — Diagnóstico de padrão e preenchimento      │
│   0.1 Levantar padrão de metadados do seminário     │
│   0.2 Identificar artigos fora do padrão            │
│   0.3 Reinspecionar PDFs dos artigos fora do padrão │
│   0.3b Extrair fontes estruturadas (pdfplumber)     │
│   0.4 Preencher lacunas no banco                    │
│   0.5 Verificar abstracts existentes (truncamento   │
│       e lixo de cruzamento de idiomas)              │
│   0.6 Extrair metadados EN (title_en, subtitle_en)  │
├─────────────────────────────────────────────────────┤
│ Fase 1 — Revisão automática (Claude)                │
│   1.1a Títulos e subtítulos PT (LLM + PDF)          │
│   1.1b Normalizar títulos EN (Title Case)           │
│   1.1c Revisão LLM de títulos EN                    │
│   1.2  Referências (limpeza completa)               │
│     1.2a clean_references.py (backfills, split,     │
│          join URLs)                                  │
│     1.2b sweep_refs (8 passadas: lixo grosso,       │
│          headers, page breaks, fragmentos,           │
│          endnotes, split, remoção, body text         │
│          truncado, near-duplicates)                  │
│     1.2c Revisão LLM de TODAS as refs (agente)      │
│          (concatenações, splits, notas, junk —       │
│          tudo que escapou ao sweep heurístico)       │
│   1.3  Keywords (split, garbage, capitalização)     │
│   1.4  Aplicar correções ao banco                   │
│                                                      │
│   ┌─── LOOP até convergir (max 5 iterações) ──────┐ │
│   │ 1.5a validate_metadata.py --fix (auto-fixes)   │ │
│   │ 1.5b fix handlers: A07 abs_en, A08 kw_en,      │ │
│   │      A19 abstract truncado (extração fontes/)   │ │
│   │ 1.5c Se zero issues corrigíveis: sair do loop  │ │
│   └────────────────────────────────────────────────┘ │
│                                                      │
│   1.6  Auditoria final                               │
│     1.6a Cobertura de metadados (artigos)            │
│     1.6b Metadados do seminário (verificar+preencher)│
│     1.6c Seções (eixos) ou sessões (programa)        │
│     1.6d Autores (completude e correção)             │
├─────────────────────────────────────────────────────┤
│ Fase 2 — Gerar HTML de revisão                      │
├─────────────────────────────────────────────────────┤
│ Registro — revisao/{slug}-rev-status.md             │
│   Criar no início da Fase 0, atualizar a cada etapa │
│   Registrar ✅/⚠️ para cada ação concreta realizada  │
└─────────────────────────────────────────────────────┘
         ↓
   Pipeline de revisão humana (pipeline_revisao_humana.md)
```

**Princípio do loop 1.2–1.5:** A revisão automática (1.2–1.4) e a validação (1.5) formam um ciclo. A validação é o checkpoint — se ainda encontra problemas que a revisão automática deveria resolver, volta-se às etapas relevantes. Só se sai do loop quando os issues restantes são **fatos** (dado genuinamente ausente no PDF), não **erros** (dado extraível ou corrigível). A revisão humana (Fases 3–5 do pipeline_revisao_humana.md) recebe apenas o que a automação não consegue resolver.

**Princípio da Fase 3 (aprendizado):** Após a revisão humana, cada correção manual é analisada: por que o pipeline não resolveu isso? A resposta é incorporada aos scripts, ao dict.db ou à documentação, para que o próximo seminário tenha menos correções manuais. O pipeline é **cumulativo** — melhora a cada seminário revisado.

### Registro de status (`revisao/{slug}-rev-status.md`)

**Criar o arquivo no início da Fase 0** e **atualizar a cada etapa concluída** — não no final. Se a sessão crashar ou compactar, o próximo ciclo sabe exatamente onde parou.

**REGRA**: Após concluir cada etapa (0.1, 0.2, ..., 1.1a, 1.2b, etc.), gravar imediatamente no arquivo de status com ✅ e os contadores. Não acumular várias etapas para registrar depois.

O registro deve conter:
- Cada ação concreta realizada, marcada como ✅ (concluída) ou ⚠️ (pendente)
- Contadores atualizados (abstracts, refs, keywords, etc.)
- Etapas restantes antes da próxima fase

**REGRA — Registrar cada correção automática significativa**: Sempre que uma correção manual for feita durante a fase automática (overflows de abstract, keywords com lixo, backfills, abstracts em idioma errado, refs com notas cortadas, etc.), registrar no rev-status:
- **Artigo** afetado
- **Campo** corrigido
- **Antes → depois** (resumo: ex. "45107→748c", "NULL→29 refs", "ES no campo PT → movido para abstract_es")
- **Causa** provável (extração sem delimitação, template do formulário, boundary incorreto, etc.)

Este log é insumo obrigatório da Fase 3 (aprendizado pós-revisão) — sem ele, o diagnóstico fica incompleto e problemas se repetem nos seminários seguintes. As correções automáticas indicam gaps no pipeline tanto quanto as correções humanas.

Este registro evita re-trabalho entre sessões e serve como auditoria do que foi feito.

**REGRA — O rev-status é o fio condutor do processo:** O pipeline tem muitas etapas e é comum surgir um problema inesperado durante a execução (overflow, lixo, dados faltantes). Ao encontrar um problema:
1. **Resolver** o problema
2. **Registrar** a correção no rev-status (artigo, campo, antes/depois, causa)
3. **Reler o rev-status** para identificar a próxima etapa ⏳ pendente
4. **Retomar** o pipeline no ponto exato onde parou

Nunca avançar para uma etapa seguinte sem verificar no rev-status que a etapa atual está ✅. Nunca deixar o pipeline pela metade para resolver um problema secundário sem antes registrar onde parou. O rev-status é a memória de execução — sem ele, o agente perde o fio e pula etapas.

**REGRA — Registrar é parte da execução, não é passo separado:** A etapa só está concluída quando o rev-status foi atualizado. O fluxo de cada etapa é:
1. Executar a etapa
2. **Imediatamente** gravar no rev-status: ✅, contadores, correções feitas (artigo/campo/antes/depois)
3. Só então passar à próxima etapa

Se entre a execução e o registro surgir outro problema, **primeiro registrar a etapa atual**, depois resolver o problema. O rev-status nunca pode ficar mais de uma etapa atrás da execução real.

---

## Fase 0 — Diagnóstico de padrão e preenchimento de lacunas

Antes de qualquer revisão, identificar o **padrão de metadados do seminário** e preencher as lacunas nos artigos que desviam desse padrão. A lógica é simples: se a maioria dos artigos tem um campo (ex: keywords), os poucos que não têm provavelmente tinham o dado no PDF e ele se perdeu na extração. Mas se nenhum artigo tem o campo, é porque o evento não exigia — e não adianta buscar.

### 0.0 Checkpoint inicial + registro de diagnóstico

**ANTES de qualquer ação**, fazer dump e commit para salvar o estado limpo:

```bash
python3 scripts/dump_anais_db.py
python3 dict/dump_db.py
git add anais.sql dict/dict.sql
git commit -m "{slug} pré-revisão: estado inicial"
```

Em seguida, criar um registro de diagnóstico no formato abaixo. Este registro serve como checklist — nenhuma fase pode avançar enquanto houver itens pendentes.

```markdown
## Diagnóstico — {slug} ({N} artigos)

### Padrão de metadados
| Campo | Presença | Classificação | Ação |
|-------|----------|---------------|------|
| abstract | X% | PRESENTE/AUSENTE/INTERMEDIÁRIO | buscar nos PDFs / não buscar |
| abstract_en | X% | ... | ... |
| keywords | X% | ... | ... |
| keywords_en | X% | ... | ... |
| references | X% | ... | ... |

### Artigos fora do padrão — {campo}
| Artigo | Status | Observação |
|--------|--------|------------|
| {file} | ⏳ pendente | |
...

(repetir para cada campo classificado como PRESENTE ou INTERMEDIÁRIO)
```

O registro é preenchido progressivamente:
- **0.1** preenche a tabela de padrão
- **0.2** preenche as listas de artigos fora do padrão (todos com status ⏳)
- **0.3** atualiza cada artigo para ✅ (preenchido) ou ⬜ (genuinamente ausente)
- **0.4** salva no banco apenas os ✅, confirma que não restam ⏳

**Regra de transição**: só avançar para a Fase 1 quando **zero** itens ⏳ restarem no registro.

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

#### Identificar norma de citação

Verificar nos fontes/ qual norma de citação predomina no seminário. Isso afeta a extração e split de referências nas fases seguintes.

```python
# Amostrar 10-20 artigos com referências e classificar
import re, json

ABNT_RE = re.compile(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ]{2,},\s+[A-Z]')          # SOBRENOME, Nome
CHICAGO_RE = re.compile(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóú]+,\s+[A-Z]')  # Sobrenome, Nome
FOOTNOTE_RE = re.compile(r'^\d{1,3}\s+[A-Z]')                       # 1 Autor...

for art_id, refs_text in sample:
    refs = json.loads(refs_text)
    abnt = sum(1 for r in refs if ABNT_RE.match(r.strip()))
    chicago = sum(1 for r in refs if CHICAGO_RE.match(r.strip()) and not ABNT_RE.match(r.strip()))
    footnote = sum(1 for r in refs if FOOTNOTE_RE.match(r.strip()))
    # Classificar: ABNT / Chicago / Misto / Footnotes
```

Registrar no diagnóstico:
- **Norma predominante**: ABNT / Chicago / Misto
- **Artigos com footnotes/endnotes**: lista (esses terão notas no campo refs que devem ser removidas)
- **Idiomas das refs**: pt-BR, en, es (afeta os padrões de split)

### 0.2 Identificar artigos fora do padrão

Para cada campo classificado como "padrão presente", listar os artigos que **não** têm o campo. Esses são os candidatos a reinspecção de PDF.

```sql
-- Exemplo: artigos sem abstract num seminário onde abstract é padrão
SELECT file, title FROM articles
WHERE seminar_slug = '{slug}' AND (abstract IS NULL OR abstract = '');
```

### 0.3 Reinspecionar PDFs

**REGRA: Inspecionar TODOS os artigos fora do padrão, sem exceção.** Não avançar para a Fase 0.4 nem para a Fase 1 enquanto todos os PDFs não tiverem sido inspecionados. Verificar parcialmente e prosseguir é o erro mais comum nesta etapa.

**Extração de texto — hierarquia de fontes:**

A qualidade da extração depende da fonte. Verificar **nesta ordem** antes de qualquer extração:

1. **doc/docx originais** — qualidade máxima. O formato .docx é XML estruturado: preserva estilos de parágrafo (Heading, Title, Normal), negrito, itálico. Com `python-docx` é possível separar título, abstract, keywords e referências **pelo estilo**, sem depender de regex. Os originais podem estar em `fontes/anais/`, organizados por eixo. Arquivos .doc (formato binário antigo) podem ser convertidos para .docx com LibreOffice antes de processar.
2. **pdfplumber** → `fontes_plumber/` — boa qualidade, preserva estrutura tipográfica (separa refs de notas por font_size). Usar quando não há doc/docx.
3. **pdftotext** → `fontes/` — fallback. Não lida com colunas, fragmenta texto.

```bash
# 1. PRIMEIRO: verificar se existem doc/docx/rtf/odt originais
find nacionais/{slug}/fontes/ -name "*.doc" -o -name "*.docx" -o -name "*.rtf" -o -name "*.odt" | wc -l

# Se existem .docx: ler diretamente com python-docx (preserva estilos)
# Se existem .doc: converter para .docx primeiro
#   soffice --headless --convert-to docx --outdir nacionais/{slug}/fontes_doc/ "{arquivo}.doc"
# Mapear nomes dos .docx para IDs dos artigos:
#   - O YAML pode ter campo source_file com o nome do arquivo original
#   - Se não tem, cruzar por autor (familyname no nome do arquivo) ou título
#   - VALIDAR o mapeamento: abrir o docx e confirmar que o título do artigo
#     corresponde ao título no banco. Se dois docx mapeiam para o mesmo autor,
#     usar o título para desambiguar. NUNCA substituir dados sem confirmar.
#   - Registrar o mapeamento no YAML (campo source_file) para reuso futuro
#
# REGRA: Ao substituir refs de um artigo por dados de outra fonte (docx, plumber),
#   SEMPRE comparar o conteúdo antes de sobrescrever. Se a fonte nova tem MENOS
#   refs que o banco, investigar — pode ser extração incompleta. Não sobrescrever
#   cegamente.

# 2. SE NÃO existem doc/docx: extrair com pdfplumber
python3 scripts/extrair_fontes_plumber.py --slug {slug} --profile-only  # calibrar
python3 scripts/extrair_fontes_plumber.py --slug {slug}                 # extrair
```

**REGRA**: **SEMPRE verificar se existem doc/docx originais ANTES de rodar pdfplumber.** Muitos seminários receberam os artigos em Word — essa é a fonte de maior qualidade. Usar `python-docx` para ler os .docx com seus estilos, não converter para .txt (perde-se a estrutura).

**REGRA**: **Completar SEMPRE a extração pdfplumber para 100% dos artigos**, mesmo quando existem docx. O plumber é fallback para artigos sem docx e para verificação cruzada. Extração parcial é inaceitável — causa erros quando se tenta usar plumber parcial como fonte.

Para **cada** artigo fora do padrão, buscar o campo faltante nos blocos do `.jsonl`:
- **Abstract/resumo**: geralmente após o título e autores, antes das keywords
- **Keywords**: geralmente após o abstract, marcadas com "Palavras-chave:" ou "Keywords:"
- **Referências**: ver subetapas abaixo
- **Abstract EN**: após o abstract PT ou no final do artigo

#### Subetapas para referências faltantes

O diagnóstico de referências é mais granular que os demais campos, porque existem três tipos de fonte no PDF:

**Passo 1 — Extrair texto e classificar todos os artigos sem refs:**

| Artigo | Tipo | Status |
|--------|------|--------|
| {file} | 📚 bibliografia explícita / 📝 endnotes / 📄 footnotes / ⬜ sem refs | ⏳ |

Onde:
- **📚 bibliografia explícita**: seção "Referências", "Bibliografia", "Referências Bibliográficas" etc.
- **📝 endnotes (notas de fim)**: seção "Notas", "Notas ao Texto" com citações numeradas
- **📄 footnotes (notas de rodapé)**: citações dispersas no rodapé das páginas, sem seção dedicada
- **⬜ sem refs**: PDF inspecionado, nenhuma referência encontrada

**REGRA**: Ao classificar um artigo como 📄 footnotes ou ⬜ sem refs, verificar **TODAS** as páginas do PDF, não só as últimas 2-3. Alguns artigos têm a seção de referências em páginas intermediárias (ex: sdbr14-122 tinha refs na p.15 de 17). Classificar errado como "footnotes only" causa perda de dados.

**Passo 2 — Extrair na ordem de facilidade:**
1. Primeiro: 📚 bibliografias explícitas (extração direta)
2. Depois: 📝 endnotes (extração + limpeza de numeração)
3. Por último: 📄 footnotes (extração complexa, pode não valer o esforço)

**Passo 3 — Salvar extração em arquivo antes de inserir no banco:**

```bash
# Salvar refs extraídas em JSON para não perder na compactação de sessão
# Arquivo: revisao/{slug}-refs-extraidas.json
{
    "sdbr06-006.pdf": ["ref1", "ref2", ...],
    "sdbr06-012.pdf": ["ref1", "ref2", ...],
    ...
}
```

Só depois de salvo o arquivo, inserir no banco. Isso garante que a extração não se perde se a sessão for compactada.

**Checklist obrigatório** antes de prosseguir: todos os artigos devem estar marcados como:
- ✅ preenchido (dado encontrado no PDF, salvo em arquivo e no banco)
- ⬜ genuinamente ausente (PDF inspecionado, campo não existe no documento)
- 📄 footnotes (flagged para avaliação futura — não bloqueia a transição)

Só avançar quando **zero** itens ⏳ restarem.

### 0.3b Extrair fontes estruturadas — OBRIGATÓRIO

**Esta etapa é obrigatória.** Hierarquia: doc/docx originais > pdfplumber > pdftotext.

**ANTES de rodar pdfplumber**, verificar se existem doc/docx/rtf/odt originais no diretório fontes/ do seminário. Se existirem, converter para .txt em fontes_doc/ e usar como fonte primária. Só rodar pdfplumber se não houver originais.

O pdfplumber preserva metadados tipográficos (tamanho de fonte, bold, posição Y), permitindo distinguir automaticamente:

- **Corpo** (maior tamanho) vs **abstract/refs** (tamanho intermediário) vs **notas de rodapé** (menor tamanho)
- **Headings** (bold, tamanho > corpo) vs **texto normal**
- **Referências bibliográficas** (após heading "Referências") vs **notas** (após heading "NOTAS" ou na parte inferior da página)

```bash
# Profile: analisa amostra do seminário para calibrar tamanhos
python3 scripts/extrair_fontes_plumber.py --slug {slug} --profile-only

# Extração completa: gera .jsonl por artigo com blocos anotados
python3 scripts/extrair_fontes_plumber.py --slug {slug}
```

**Output:** `{slug}/fontes_plumber/{id}.jsonl` — cada linha é um bloco de texto com campos:
- `page`, `font_size`, `font_name`, `role`, `text`, `bold`, `lines`
- `role`: `body`, `abstract`, `reference`, `footnote`, `heading`, `subheading`, `pagenum`, `small`

**Calibração automática:** O script faz profiling do seminário (amostra de 10 PDFs) para detectar os tamanhos de cada role. Depois adapta per-artigo, recalibrando quando o artigo usa template diferente do seminário. Pós-classificação posicional reclassifica blocos com base em headings semânticos ("Resumo", "Referências", "NOTAS").

**Uso nas fases seguintes:**
- **Fase 0.5** (verificar abstracts): usar blocos `abstract` do `.jsonl` para detectar truncamento — o abstract termina quando o role muda de `abstract` para `body`
- **Fase 1.2** (referências): usar blocos `reference` como fonte preferencial — já exclui notas de rodapé (`footnote`) e corpo (`body`)
- **fix_validation_issues.py**: `find_alt_source()` consulta `fontes_plumber/` como fonte intermediária entre `fontes_doc/` e `fontes/`

**IMPORTANTE:** Na fase de revisão, `fontes_plumber/` é a **fonte primária**, não complementar. O pdftotext (`fontes/`) pode existir de fases anteriores e serve como fallback, mas o pdfplumber é sempre preferido — especialmente para delimitação de abstract, separação refs/notas, e PDFs com layout em colunas.

### 0.4 Preencher lacunas no banco

Aplicar os dados extraídos ao banco **a partir do arquivo JSON salvo na etapa anterior**. Reportar:
- Quantos artigos estavam fora do padrão por campo
- Quantos foram preenchidos com sucesso
- Quantos genuinamente não têm o dado (confirmado no PDF)
- **Lista completa** com status de cada artigo (checklist ✅/⬜/📄)

**REGRA — Verificação de idioma ao inserir abstracts:** Antes de inserir um abstract, verificar o idioma do texto. Se o texto é em espanhol (contém "El presente trabajo", "se propone", "arquitectura") e o `locale` do artigo é `pt-BR`, inserir em `abstract_es`, **não** em `abstract`. Um Resumen em espanhol no campo `abstract` (PT) é um erro que o validate não detecta. (Aprendido com sdbr13-143.)

**REGRA — Extrair também metadados ES:** A Fase 0 deve buscar `abstract_es` e `keywords_es` nos PDFs, não apenas EN. Artigos em PT podem ter seção Resumen/Palabras clave (ex: sdbr13-123). O validate A09 detecta marcador "Resumen" nos `fontes/`, mas se `fontes/` não existe, o dado se perde. (Aprendido com sdbr13-123.)

**REGRA — Rodar sweep_refs DEPOIS de inserir refs:** Se a Fase 0.3/0.4 insere novas refs extraídas dos PDFs, o sweep_refs (1.2b) deve rodar sobre TODAS as refs, incluindo as recém-inseridas. Refs extraídas do pdfplumber frequentemente vêm splitadas por `\n` e precisam que a passada 1 (fragmentos) as junte. Não basta rodar o sweep apenas sobre as refs que já estavam no banco. (Aprendido com sdbr13-024.)

### 0.5 Verificar abstracts existentes (truncamento, lixo, contaminação)

**PRIMEIRO**, rodar o validate para detectar e corrigir automaticamente os problemas mais grossos:

```bash
# Rodar auto-fixes do validate ANTES da varredura manual
# Pega: A20 (overflow >5000c), A25 (keywords coladas), A26 (idioma errado), A27 (PT no EN)
python3 scripts/validate_metadata.py --slug {slug} --fix
```

Isso resolve overflows, keywords coladas e idioma errado antes da inspeção manual, evitando que o operador perca tempo com problemas que o script já sabe corrigir. (Aprendido com sdbr13: 11 overflows de abstract_en foram detectados manualmente na Fase 0.5 — A20 já sabia corrigir mas só rodava na Fase 1.5.)

Após preencher as lacunas (0.4) e rodar o validate, varrer **todos** os abstracts do seminário — tanto os já existentes quanto os recém-inseridos — para detectar problemas de extração. A varredura deve cobrir 100% dos artigos, não apenas os que foram preenchidos na Fase 0.

**Problemas a detectar:**

1. **Truncamento por quebra de página**: o `pdftotext` insere números de página como linhas isoladas (`\n\n3\n\n`). Quando o abstract cruza a fronteira de uma página, o extrator pode parar no número de página e truncar o texto. **Tratamento**: antes de extrair, limpar o texto com `re.sub(r'\n\s*\n\s*\d{1,3}\s*\n\s*\n', '\n\n', text)` para remover números de página soltos. Após extração, verificar se o abstract termina com pontuação de fim de frase.
2. **Truncamento genérico**: abstract termina no meio de uma frase (sem `.`, `?`, `!`, `"`, `)` no final)
3. **Texto PT colado no abstract_en**: palavras em português após o fim do abstract em inglês (padrão mais comum: abstract_en seguido de "A historiografia...", "O presente trabalho...", "Palavras-chave:...")
4. **Keywords vazadas**: "Palavras-chave:", "Keywords:", "Key words:" no final do abstract
5. **Cabeçalhos e metadados**: títulos de seções, nomes de autores, números de página misturados
6. **Início truncado**: abstract começa no meio de uma frase (faltando o início)
7. **Abstract muito curto**: < 100 caracteres para PT ou < 80 para EN (pode ser genuíno, mas verificar)
8. **abstract_es com lixo de cruzamento de idiomas**: a extração não parou no marcador de keywords e incluiu o conteúdo EN (abstract_en, keywords_en, page breaks) dentro do campo abstract_es. Padrão frequente em artigos ES que usam "Palabras-chave:" (forma híbrida PT/ES) em vez de "Palabras clave:". **Detecção**: abstract_es contém "Abstract", "Keywords:", "⏐" (page break marker), ou é significativamente mais longo que o abstract PT. **Tratamento**: limpar abstract_es truncando no marcador de keywords; se locale=es e o abstract principal já contém o texto correto em espanhol, setar abstract_es = NULL (campo redundante).
9. **abstract_es duplicado do abstract**: em artigos ES (locale=es), o abstract principal já contém o resumo em espanhol. Se abstract_es = abstract (mesma string), é redundância — setar abstract_es = NULL.

**Procedimento:**

```python
# 1. Detecção automática
import sqlite3, re
conn = sqlite3.connect('anais.db')
cur = conn.cursor()
cur.execute("""SELECT file, abstract, abstract_en FROM articles
               WHERE seminar_slug = ? AND (abstract IS NOT NULL OR abstract_en IS NOT NULL)""", (slug,))

for file, abs_pt, abs_en in cur.fetchall():
    issues = []
    for field, text in [('abstract', abs_pt), ('abstract_en', abs_en)]:
        if not text:
            continue
        text = text.strip()
        # Truncamento: não termina com pontuação de fim de frase
        if text and text[-1] not in '.?!"\')':
            issues.append(f"{field}: possível truncamento (termina com '{text[-20:]}')")
        # Muito curto
        if len(text) < 100:
            issues.append(f"{field}: muito curto ({len(text)} chars)")
        # PT no abstract_en
        if field == 'abstract_en':
            pt_markers = ['Palavras-chave', 'Resumo', 'O presente trabalho',
                         'Este artigo', 'Este trabalho', 'A pesquisa']
            for marker in pt_markers:
                if marker in text:
                    issues.append(f"abstract_en: possível texto PT ('{marker}')")
                    break
    if issues:
        print(f"{file}: {'; '.join(issues)}")
```

```bash
# 2. Para cada caso suspeito, conferir no fontes/ e corrigir
# Ler nacionais/{slug}/fontes/{file%.pdf}.txt
# Localizar o abstract correto e fazer o trim/substituição no banco
```

**Regra**: Corrigir diretamente no banco. Não deixar para a revisão humana — problemas de truncamento e lixo são mecânicos e devem ser resolvidos nesta fase.

**Script de validação automática** (complementa a detecção manual):

```bash
# Detectar todos os problemas de abstract do seminário
python3 scripts/validar_abstracts.py --slug {slug}

# Corrigir automaticamente swaps abstract PT↔EN
python3 scripts/validar_abstracts.py --slug {slug} --fix-swap
```

O script `validar_abstracts.py` implementa 9 regras de validação aprendidas das revisões humanas anteriores. Rodar **antes** da detecção manual para resolver os problemas mais comuns automaticamente.

### 0.6 Extrair metadados EN (title_en, subtitle_en, abstract_en, keywords_en)

Se o diagnóstico (0.1) mostrar presença de `abstract_en` ≥ 30%, extrair metadados em inglês dos textos:

```bash
python3 scripts/extrair_metadados_en.py --slug {slug} --dry-run
python3 scripts/extrair_metadados_en.py --slug {slug}
```

O script busca nos fontes/ a seção EN de cada artigo (delimitada pelo marcador "Abstract") e extrai:
- **title_en**: título em inglês (entre keywords_PT e "Abstract", ou em ALL CAPS após o header)
- **subtitle_en**: subtítulo (separado do title_en por `: `, ` — ` ou ` – `)
- **abstract_en**: texto do abstract (se ainda não preenchido)
- **keywords_en**: palavras-chave EN (se ainda não preenchidas)

Flags: `--force` re-extrai mesmo se o campo já tem valor; `--only-title` extrai apenas title_en/subtitle_en.

**Nota:** A extração automática não captura todos os títulos EN — muitos PDFs têm o título inline com o abstract ou em formato não-padrão. Os títulos não capturados serão revisados na Fase 1.1c (revisão LLM).

---

## Fase 1 — Revisão automática

O Claude executa verificações automatizadas e aplica correções ao banco **antes** de gerar o HTML de revisão, para que o humano revise o estado já corrigido.

### 1.1a Títulos e subtítulos PT

**Objetivo:** Corrigir capitalização conforme norma brasileira (sentence case com dict.db).

```bash
# 1. Alimentar dicionário com nomes novos
python3 dict/seed_authors.py
python3 dict/seed_titles.py --apply

# 2. Normalizar
python3 scripts/normalizar_maiusculas.py --slug {slug} --dry-run
python3 scripts/normalizar_maiusculas.py --slug {slug}
```

**Verificação com LLM — OBRIGATÓRIA:** Após a normalização automática, o Claude **lista todos os títulos e subtítulos** e analisa **cada palavra** de cada um. Procedimento concreto:

1. Rodar `SELECT id, title, subtitle FROM articles WHERE seminar_slug = ? ORDER BY id`
2. Processar **um artigo por vez** — NÃO em lote. Para cada artigo, imprimir título e subtítulo e escrever o julgamento de CADA palavra antes de passar ao próximo. Formato obrigatório:

```
sdbr12-041:
  T: O Habitat moderno em São Luís do Maranhão
  → "Habitat": conceito genérico (moradia), não revista → CORRIGIR para "habitat"
  → "São Luís": cidade → OK
  → "Maranhão": estado → OK
  RESULTADO: O habitat moderno em São Luís do Maranhão
```

Se não escreveu o julgamento de cada palavra, não revisou. Pular direto para a correção sem este registro = revisão não feita.

3. Para **cada palavra com maiúscula** (exceto a primeira do título): perguntar "por que está maiúscula?"
   - Nome próprio de pessoa, edifício, instituição, cidade, país → **manter**
   - Nome de revista, periódico, evento → **manter**
   - Expressão consolidada (Arquitetura Moderna, Movimento Moderno, Educação Patrimonial) → **manter**
   - Sigla (SUDENE, IPHAN, GT) → **manter**
   - **Todo o resto → minúscula** (obra, norte/sul como direção, ensino, conservação, tombamento, apartamento, imaginário, intervenção, escolar, edificado, brutalista como adjetivo isolado, arquiteto/a como profissão genérica...)
3. Para **cada palavra com minúscula** que deveria ser maiúscula: perguntar "deveria ser maiúscula?"
   - Nome de cidade (madri → Madri), edifício (congresso nacional → Congresso Nacional), monumento (cristo redentor → Cristo Redentor), periódico (le carré bleu → Le Carré Bleu), apelido (petit paris → Petit Paris), coletivo/grupo artístico (grupo arquitetura nova → Grupo Arquitetura Nova) → **corrigir**
4. Para **cada subtítulo**: verificar que começa com **minúscula** (exceto nome próprio, sigla). "Elementos iniciais..." → "elementos iniciais..."
5. Verificar **separação título/subtítulo** contra o PDF original. Conferir se o split no `:` ou ` — ` corresponde à intenção do autor. Para PDFs escaneados (sem OCR), ler a IMAGEM do PDF para conferir.
6. Verificar **formatação**: hífens soltos ("1970- as" → split em título+subtítulo), travessões, dois pontos
6. Verificar **typos e acentuação**: São Luis → São Luís, preservaçâo → preservação, madri → Madri
7. Verificar **pontuação anômala** que indica separação título/subtítulo mal feita:
   - `//` → split em título + subtítulo
   - `––` ou `--` → substituir por `—` (em-dash) ou split
   - `- ` (hífen+espaço) no meio do título → split ou `—`
   - `:` no meio → pode indicar subtítulo não separado
   - `.` seguido de frase nova no mesmo campo → split título/subtítulo
5. Para cada correção: aplicar no banco. Se a causa foi o dict.db (forçou maiúscula em palavra comum), remover a entrada do dict.
6. **Aplicar correções escrevendo o título completo**, não por replace parcial de string. Replace parcial causa erros: falha silenciosamente ("a Obra" ≠ "A Obra"), ou rebaixa a primeira palavra do título para minúscula. Escrever o título inteiro garante que o resultado é o correto.
7. **Após aplicar, reler o título corrigido** para confirmar. A primeira palavra do título é SEMPRE maiúscula.
7. Registrar todas as correções e aprendizados no `revisao/{slug}-titulos-aprendizado.json`

**Não usar heurísticas para esta etapa.** Ler cada título com os olhos, não com regex.

**COMPARAR COM O ORIGINAL:** Para cada título, comparar com o docx (python-docx) ou PDF original. O `normalizar_maiusculas.py` rebaixa nomes que não estão no dict — a comparação com o original revela o que foi rebaixado indevidamente. Tipos comuns de erro:
- Nomes de edifícios/equipamentos: Hospital de Clínicas, Centro de Convenções, Estação Rodoviária, Plenário Legislativo
- Nomes de lugares/loteamentos: Jardim do Embaixador, Vila dos Operadores, Campus Central
- Períodos/movimentos históricos: Estado Novo, Novecento
- Nomes de revistas/periódicos: Módulo, A Casa, Le Carré Bleu
- Nomes próprios com grafia incomum: Mallet-Stevens, São Luís (acento)
- Adjetivos gentílicos que não devem ser maiúsculas: capixaba, sul-americano

Detecções adicionais:
- Nomes próprios de edifícios/lugares que ficaram em minúscula
- Termos genéricos que ficaram em maiúscula indevida
- Subtítulos que deveriam começar com minúscula (ou vice-versa)
- Separação incorreta entre título e subtítulo
- **Expressões consolidadas com toponímico:** "Arquitetura Moderna", "Arquitetura Modernista", "Arquitetura Contemporânea", "Arquitetura Vernacular" etc. são expressões consolidadas e ficam com maiúscula quando referem o movimento/conceito. Porém, quando seguidas de toponímico ou locativo, funcionam como descritivas e devem ficar em **minúscula**:
  - ✅ "Os princípios da Arquitetura Moderna no Brasil" (conceito)
  - ✅ "a arquitetura moderna de Recife" (descritiva + toponímico)
  - ✅ "Patrimônio da Arquitetura Modernista" (conceito)
  - ✅ "a arquitetura modernista em Belém do Pará" (descritiva + toponímico)
  - O dict/normalizer força maiúscula em todas as ocorrências — a revisão LLM deve rebaixar para minúscula quando o contexto é descritivo (tipicamente: "a/da/na arquitetura moderna/modernista de/em [cidade/estado/país]").

Os critérios de capitalização estão em [`docs/regras_dados.md`](regras_dados.md) e na memória do projeto.

**Registro granular de aprendizado:** Durante a revisão LLM, **cada correção e cada aprendizado devem ser salvos em arquivo** progressivamente, à medida que são identificados. Isso evita perder o trabalho numa compactação de sessão.

Arquivo: `revisao/{slug}-titulos-aprendizado.json`

```json
{
  "correcoes": [
    {
      "file": "sdbr06-008.pdf",
      "campo": "title",
      "de": "esplanada em Santos",
      "para": "Esplanada em Santos",
      "motivo": "nome próprio de edifício",
      "dict_acao": "add_nome:Esplanada"
    },
    {
      "file": "sdbr06-019.pdf",
      "campo": "title",
      "de": "Arquitetura Brasileira",
      "para": "arquitetura brasileira",
      "motivo": "termo genérico, não é 'Arquitetura Moderna'",
      "dict_acao": null
    }
  ],
  "dict_additions": {
    "nomes": ["Esplanada", "Pedregulho"],
    "expressoes": ["Plano Agache", "Brutalismo Paulista"],
    "remover": []
  },
  "padroes_confirmados": [
    "'Arquitetura Moderna' sempre maiúscula",
    "'arquitetura' isolada sempre minúscula"
  ]
}
```

**Procedimento:**
1. Analisar títulos em lotes (ex: 10 por vez)
2. **Após cada lote**, salvar as correções e aprendizados no arquivo JSON
3. Ao final de todos os lotes, aplicar correções ao banco e dict_additions ao dict.db
4. Se a sessão for compactada no meio, o próximo ciclo lê o arquivo e continua de onde parou

**Retroalimentação do dicionário:** Após aplicar as correções do LLM, incorporar os aprendizados ao `dict.db` **a partir do arquivo JSON** (campo `dict_additions`):

1. **Novos nomes próprios** (`dict_additions.nomes`):
   - Edifícios, lugares, instituições → adicionar à tabela `nomes` ou `expressoes`
   - Ex: "Esplanada" (nome de edifício), "Vila Operária" (nome próprio)
2. **Novas expressões consolidadas** (`dict_additions.expressoes`):
   - Ex: "Brutalismo Paulista", "Plano Agache"
   - Adicionar à tabela `expressoes` do `dict.db`
3. **Falsos positivos** (`dict_additions.remover`):
   - Palavras que estão no `dict.db` como nome próprio mas não deveriam estar
   - Remover a entrada
4. **Padrões confirmados** (`padroes_confirmados`): registrar em `MEMORY.md` para referência futura

```bash
# Aplicar aprendizados do arquivo JSON ao dict.db:
python3 -c "
import json, sqlite3
with open('revisao/{slug}-titulos-aprendizado.json') as f:
    data = json.load(f)
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
```

**Nota:** `dict/dict.sql` será salvo no próximo checkpoint (Fase 2).

### 1.1b Normalizar títulos EN e ES

**Objetivo:** Normalizar capitalização de `title_en`, `subtitle_en`, `title_es`, `subtitle_es`.

**Títulos EN** — Title Case (Chicago/APA):

**Objetivo:** Aplicar Title Case inglês (Chicago/APA) a `title_en` e `subtitle_en`.

```bash
python3 scripts/normalizar_titulos_en.py --slug {slug} --dry-run
python3 scripts/normalizar_titulos_en.py --slug {slug}
```

Regras de Title Case:
- Capitalizar todas as palavras **exceto** artigos (a, an, the), preposições curtas (in, of, at, by, to, for, with, on), conjunções coordenativas (and, but, or, nor)
- **Primeira e última palavra**: sempre maiúscula
- **Primeira palavra após `:` ou `—`**: sempre maiúscula
- **Acrônimos**: preservar ALL CAPS (IPHAN, UNESCO, CIAM) — via `dict.db` categoria `sigla`
- **Nomes próprios**: preservar forma canônica (Brasilia, Niemeyer) — via `dict.db` categorias `nome`, `lugar`

Usa a biblioteca Python `titlecase` com callback que consulta `dict.db`.

**Títulos ES** — Sentence case (mesma regra do PT):
- Capitalização sentence case via `dict.db` (mesmas regras dos títulos PT)
- Nomes próprios, expressões consolidadas, siglas preservados
- Se `title_es` ou `subtitle_es` existir (campo AUSENTE no diagnóstico → pular)

```bash
python3 scripts/normalizar_maiusculas.py --slug {slug} --field title_es --dry-run
python3 scripts/normalizar_maiusculas.py --slug {slug} --field title_es
```

**Títulos de artigos em locale=es**: o título principal (`title`) está em espanhol — aplicar as mesmas regras de capitalização sentence case. Verificar se `title` não foi normalizado incorretamente pelo dict.db (que é calibrado para PT).

### 1.1c Revisão LLM de títulos EN e ES

**Objetivo:** O Claude compara cada `title_en`, `title_es`, e títulos de artigos locale=es/en com o PDF/docx original para detectar:
- Títulos truncados (extração cortou no meio)
- Title Case incorreto em nomes próprios (EN) ou sentence case incorreto (ES)
- Separação errada título/subtítulo
- Título que é na verdade a primeira frase do abstract (falso positivo)
- Artigos com seção EN/ES no PDF mas sem `title_en`/`title_es` no banco
- Títulos de artigos locale=es que foram normalizados incorretamente pelo dict.db (calibrado para PT)

Salvar aprendizado em `revisao/{slug}-titulos-en-aprendizado.json`:

```json
{
  "correcoes": [
    {
      "file": "sdbr08-020.pdf",
      "campo": "title_en",
      "de": null,
      "para": "The City of Recife as Artistic Object in the Interventions of Paulo Bruscky",
      "motivo": "título não extraído automaticamente (inline com abstract)"
    }
  ],
  "dict_additions": {
    "nomes": ["Bruscky"],
    "siglas": []
  }
}
```

### 1.2 Referências (limpeza completa)

**Objetivo:** Limpar, verificar e corrigir referências em 4 subetapas. A limpeza deve ser **exaustiva** — a validação (1.5) não deve encontrar problemas que esta etapa poderia ter resolvido.

#### 1.2a Limpeza base (clean_references.py)

```bash
python3 scripts/clean_references.py --slug {slug} --dry-run
python3 scripts/clean_references.py --slug {slug}
python3 scripts/check_references.py --slug {slug} --summary
```

Resolve: backfills (underscores ABNT → autor anterior), split de refs concatenadas por underscores, join de URLs órfãs.

**Artigos com 0 referências:** Verificar nos PDFs se há seção de referências ou notas de rodapé com citações. Se houver, extrair seguindo o procedimento documentado em `pipeline_tratamento.md` §2.1b (referências) ou §2.1c (notas de rodapé).

**Re-extração de refs via .doc:** Se `fontes/` (pdftotext) produz refs concatenadas que `clean_references.py` não consegue separar, converter os .doc originais via LibreOffice (`soffice --headless --convert-to txt`) e re-extrair. Salvar os .txt convertidos em `nacionais/{slug}/fontes_doc/` (nome: `{id}-doc.txt`). Quando disponível, preferir `fontes_doc/` para extração de refs — a formatação é mais limpa que o pdftotext.

#### 1.2b Varredura completa de referências (sweep_refs)

```bash
python3 scripts/fix_validation_issues.py --slug {slug} --sweep-refs --dry-run
python3 scripts/fix_validation_issues.py --slug {slug} --sweep-refs
```

Varredura completa de TODAS as refs do seminário em 8 passadas:

| Passada | Ação | Heurística |
|---------|------|------------|
| 0. Lixo grosso | Remover body text, figure captions, headers standalone, NOTAS | `is_body_text()`, `FIGURE_RE`, `SECTION_HEADER_STANDALONE`, `NON_REF_CONTENT` |
| 0b. Headers prefixo | Strip headers de seção prepostos/apostos | `SECTION_HEADER_PREFIXES`: "Escritos ", "Teses e Dissertações ", etc. |
| 0c. Page breaks | Split em marcadores ⏐ + número de página | `PAGE_BREAK_RE`: `\s*[⏐│\|][\uf000-\uf8ff]*\s*\d+\s+` |
| 1. Fragmentos | Juntar à ref anterior | `is_fragment()`: começa com minúscula, ano isolado (`2003.`), URL isolada (`http://...`), `Disponível em:` isolado, curto (<60) com padrão de cidade/ano/página, começa com "In:", "Editora", "vol.", "n." |
| 2. Endnotes | Se contém ref: extrair; senão: remover | `is_numbered_endnote()`: prefixo `^\d{1,3}\s+` seguido de texto classificado por `is_bibliographic_ref()` |
| 3. Split | Separar concatenadas > 300 chars | `split_concatenated_refs()`: boundaries ABNT (`SOBRENOME, Nome`), Chicago (`Sobrenome, Nome`), ano+ponto, publisher (`Press,` `Editora,`), pipe (`\|`) |
| 4. Remoção | Remover não-referências restantes | `is_bibliographic_ref()`: aceita ABNT/Chicago/APA; rejeita se começa com marcador narrativo, tem `has_narrative_structure()` ≥ 3 (PT/EN/ES), ou é nota numerada |
| 5. Body text | Truncar body text do final de refs mistas | `truncate_body_text()`: detecta início de narrativa após dados bibliográficos |
| 6. Near-dupes | Remover near-duplicates | `normalize_ref_for_dedup()`: normaliza pontuação, URLs, meses PT/EN/ES |

**Passada 0 — padrões de lixo grosso** (problema de boundary na extração):

Esses padrões indicam que a extração errou o início da seção de referências e capturou conteúdo que não é ref:

```python
# Figure captions (legendas de figuras capturadas como refs)
FIGURE_RE = re.compile(r'^(Figura|Fig\.?|Figure|Imagem)\s*\d', re.IGNORECASE)

# Section headers standalone (removidos inteiramente)
SECTION_HEADER_STANDALONE = re.compile(
    r'^(Escritos|Livros|Revistas e Periódicos|...)\.?\s*$')

# Body text (>200 chars + narrativa + sem padrão de autor)
def is_body_text(ref):
    return (len(ref) > 200
            and has_narrative_structure(ref)
            and not ABNT_AUTHOR_RE.match(ref)
            and not re.match(r'^[A-Z][a-z]+,\s+[A-Z]', ref))

# Agradecimentos, créditos, CVs, cabeçalhos de subseção
NON_REF_CONTENT = ['agradec', 'crédito', 'ilustraç', 'currículo',
    'fapesp', 'cnpq', 'capes', 'bolsista',
    'fontes primárias', 'artigos de jornais',
    'engenheiro e proprietário']
```

**Passada 0b — headers de seção** (infiltrados como prefixo/sufixo das refs):

Quando a extração pega um header de subseção bibliográfica ("Escritos", "Teses e Dissertações", "Revistas e Periódicos") junto com a primeira ref daquela subseção, o header fica preposto: `"Escritos Banham, Reyner..."`. A passada 0b detecta e remove o header, preservando a ref. Funciona também para headers no final: `"Rowe, Colin. ... 1999. Revistas e Periódicos"`.

**Passada 0c — page breaks** (artefatos de quebra de página no pdftotext):

Entradas como `"USP. São Carlos, 2003 ⏐ 27 Zein, Ruth Verde..."` contêm marcador de page break (⏐ U+23D0 ou │ U+2502, às vezes com PUA chars) seguido de número de página. A passada 0c divide essas entradas em duas.

**Passada 2 — NOTAS/footnotes** (problema mais frequente em artigos ES):

A extração captura a seção BIBLIOGRAFÍA + a seção NOTAS que vem depois. As NOTAS contêm: texto narrativo, citações abreviadas (Ibid., Op. cit.), comentários. A passada 2 detecta endnotes numeradas e extrai apenas a ref bibliográfica embutida, descartando o número e o texto narrativo.

**Passada 5 — body text truncado** (refs mistas):

Quando body text se juntou ao final de uma referência (ex: `"Tese de doutorado. ETSAB-UPC. Pag. 145. Vilanova Artigas já utilizava..."`), a passada 5 detecta o início da narrativa via regex e trunca a ref no boundary.

**Passada 6 — near-duplicates:**

Normaliza refs removendo URLs, pontuação, e mapeando meses PT/EN/ES para forma canônica antes de comparar. Detecta duplicatas que diferem apenas em: presença/ausência de URL, formato do mês (dez/dec/dic), pontuação.

**Safeguard (passada 1):** fragmentos que `is_bibliographic_ref()` classifica como ref legítima NÃO são juntados — preserva refs curtas independentes (ex: "Banham, Reyner. op. cit. p. 361").

**`has_narrative_structure()`:** conta marcadores de discurso em 3 idiomas (PT, EN, ES). Threshold ≥ 3 marcadores = texto narrativo, não referência.

**Meta:** < 2% de problemas por seminário ao final desta etapa.

#### 1.2b+ Re-rodar backfills após o sweep

O sweep (1.2b) pode criar novos backfills ao splittar refs concatenadas. Re-rodar `clean_references.py` para resolver esses backfills pendentes:

```bash
python3 scripts/clean_references.py --slug {slug} --dry-run
python3 scripts/clean_references.py --slug {slug}
```

Aprendido com sdbr13: `clean_references.py` (1.2a) resolveu 6 backfills, mas após o sweep + inserção de refs da Fase 0, restaram 36 backfills que a 1.2a não tinha visto. Re-rodar resolve sem intervenção manual.

#### 1.2c Revisão LLM de TODAS as referências

Após o sweep determinístico (1.2b) e re-backfill (1.2b+), **todas** as referências do seminário devem ser revisadas por LLM. O sweep resolve ~70% dos problemas, mas os ~30% restantes escapam às heurísticas — especialmente concatenações Chicago, notas sem marcadores numéricos, e boundary ambíguos.

**Por que revisar tudo (não só os flaggados):**
A experiência com sdbr10 (118 artigos, ~2000 refs) mostrou que o sweep + validate deixou passar ~100 problemas em 51 artigos. Muitos não eram flaggados por nenhum check — refs de 200-400 chars com concatenação Chicago, notas narrativas sem número, headers de subseção colados. A revisão LLM encontrou e corrigiu todos.

**Tipos de problema que escapam às heurísticas:**

| Tipo | Exemplo | Por que escapa |
|------|---------|----------------|
| Concatenação Chicago | `"...MIT Press, 2003. Sobrenome, Nome. Title..."` | Boundary mixed-case, ref <500 chars |
| Notas sem número | `"O autor argumenta que a técnica construtiva..."` | Não começa com `\d+`, não flaggado como endnote |
| Notas com ref embutida | `"Depoimento de Bucci em: Cotrim, M. (org.)..."` | Começa com nome próprio, parece ref |
| Concatenação backfill | `"______. Obra 1. 1990. ______. Obra 2. 1995."` | Backfill resolveu só o primeiro `______` |
| Fragmento contextual | `"Tese de doutorado. PROPAR-UFRGS, 2005."` | Parece ref independente mas é continuação |
| Near-dupes com variação | Duas versões da mesma ref, uma com URL | `normalize_ref_for_dedup()` não normaliza tudo |
| Headers infiltrados | `"Livros e revistas"` colado como ref | Não está na lista `SECTION_HEADER_STANDALONE` |

**Procedimento (agente background):**

1. **PRIMEIRO**: Para cada artigo, ler `fontes_plumber/{id}.jsonl` (se existir) ou `fontes/{id}.txt`. Se fontes/ estiver fragmentado (colunas), rodar pdfplumber antes. **NUNCA tentar reconstruir texto fragmentado do pdftotext.**
2. **SEGUNDO — PASSO CRÍTICO**: No texto fonte, identificar o **ponto de corte** entre BIBLIOGRAFIA e NOTAS. Indicadores:
   - Heading "NOTAS", "Notes", "Notas de fim", "Notas ao texto"
   - Numeração sequencial (1, 2, 3... ou ¹, ², ³...) que inicia após a última ref
   - Quebra na ordem alfabética dos autores
   - Mudança de padrão: refs são "AUTOR. Título. Editora, Ano." / notas são "Ver Fulano (2003)...", "Op. cit.", "Ibid.", narrativa
   - No pdfplumber: mudança de font_size (refs em size maior, notas em size menor)
3. Definir a lista de refs válidas (até o ponto de corte) e descartar notas
4. Dentro das refs válidas, corrigir: concatenações, splits, headers
5. Gravar no banco
6. Ao final, gerar relatório

**Prompt para o agente:**

```
Review ALL references in {slug}.

CRITICAL FIRST STEP: For each article, identify WHERE THE BIBLIOGRAPHY ENDS
and WHERE THE NOTES BEGIN. Many articles have a BIBLIOGRAPHY section followed
by a NOTES section — the notes MUST be removed. Indicators:
- Numbered entries (1., 2., 3. or ¹²³) after the last proper reference
- "Op. cit.", "Ibid.", "Idem", "Cfr.", "Ver" — these are notes, not refs
- Narrative text ("O autor argumenta...", "Segundo Fulano...") — notes
- Break in alphabetical order of authors
- In fontes_plumber/: font_size change (refs larger, notes smaller)

PREFERRED SOURCE: Use fontes_plumber/{id}.jsonl when available — it separates
reference blocks from footnote blocks by font size. Only fall back to
fontes/{id}.txt when plumber data is unavailable.
If fontes/ text is fragmented (each word on a separate line), the PDF has
column layout — extract with pdfplumber, do NOT try to reconstruct manually.

For each article:
1. Read fontes_plumber/ or fontes/ and identify the bibliography boundary
2. Read current refs from DB
3. Set refs = only the bibliography entries (cut notes)
4. Within bibliography: fix concatenated refs, split refs, junk
5. Write corrected refs to DB
6. Track all changes for final report
```

**Critérios de decisão LLM:**
- **Ponto de corte BIBLIOGRAFIA→NOTAS**: o critério mais importante. Identificar ANTES de analisar ref a ref.
- **Concatenação**: duas estruturas bibliográficas na mesma entrada → separar
- **Split**: entrada que começa com minúscula, "In:", URL, ano isolado, cidade/editora → juntar à anterior. Quebra na ordem alfabética indica split.
- **Nota vs ref**: entrada com narrativa, "Op. cit.", "Ibid.", "Ver também", numeração sequencial → remover
- **Header**: entrada que é nome de seção ("Livros", "Revistas e Periódicos") → remover
- **Backfill em-dash**: `—.` ou `–.` entre refs = mesmo autor, obra diferente → separar e prepor o autor

**REGRA — Refs longas (A11) que o sweep não resolveu:** Refs >500 chars que `split_concatenated_refs()` não conseguiu separar (sem boundary ABNT/Chicago claro) devem ser resolvidas na revisão LLM. Para cada uma: ler o PDF/plumber, identificar se é concatenação, lista de fontes/URLs, ou ref legítima longa (capítulo em livro com editora longa). Ações: separar, remover URLs órfãs, remover listas de fontes não-bibliográficas, ou marcar como legítima. Não deixar para revisão humana.

**REGRA ABSOLUTA**: Nunca aceitar campo vazio como "genuinamente ausente" sem abrir o PDF/docx original e confirmar visualmente. Se o docx não tem, abrir o PDF. Se o PDF não tem, aí sim é ausente.

**REGRA ABSOLUTA**: A 1.2c **corrige** — não apenas relata. Se identificou um problema, **corrige na hora** e grava no banco. Relatório sem correção = etapa não executada. Cada problema identificado deve ter uma ação correspondente (cortar, juntar, separar, remover). Se não sabe como corrigir, perguntar ao usuário — não pular.

**REGRA**: Revisar **todos** os artigos, sem exceção. Não pular artigos por parecerem limpos. A revisão é exaustiva.

**REGRA**: A revisão LLM NÃO é só de referências. Verificar TODOS os campos:
- **abstract, abstract_en, abstract_es**: ler cada um e julgar:
  - Está no idioma correto? (abstract=PT, abstract_en=EN, abstract_es=ES)
  - Está completo? (não truncado no meio da frase)
  - Não tem lixo? (formulários, tabelas, legendas, dados de questionário, título colado)
  - Não tem outro idioma misturado? (EN no PT, keywords coladas)
  - Faz sentido como resumo acadêmico?
- **keywords, keywords_en, keywords_es**: ler cada lista e julgar:
  - São palavras-chave reais? (não lixo, não texto corrido, não citação ABNT)
  - Estão no idioma correto?
  - Não estão splitadas demais ou aglutinadas?
- Se qualquer campo parece errado → re-extrair do docx (python-docx) ou da imagem do PDF (pdftoppm)
- Se o abstract parece lixo → extrair da imagem do PDF
- **Cada artigo deve ser verificado, sem exceção.** Heurísticas (A23, A25, A14) pegam padrões comuns; o LLM pega o resto.

**Relatório final**: o agente deve produzir:
1. Lista de **todos** os artigos modificados com contagem antes/depois
2. Estatísticas por tipo de correção (concatenação, split, nota cortada, junk removido, backfill resolvido)
3. **Para cada artigo onde cortou notas**: indicar o ponto de corte (ref N → nota N+1)
4. Lista de artigos revisados **sem problemas** (confirma que foram verificados)
5. Análise de padrões: erros que se repetem → candidatos a nova heurística

**Retroalimentação do pipeline**: após a revisão LLM, analisar os padrões de erro encontrados e implementar novas heurísticas no sweep para evitar os mesmos problemas nos seminários seguintes. Testar as melhorias em outro seminário (não no que acabou de ser revisado).

**NÃO passa para revisão humana** — resolve-se inteiramente na sessão Claude Code.

### 1.3 Keywords (split, garbage, capitalização)

**Objetivo:** Limpar e normalizar keywords em PT, EN e ES. A extração via `pdftotext` frequentemente produz keywords aglutinadas (separadas com `.`, `,` ou `/` dentro de uma única entrada), texto de template de formulário ("máximo 3, separados com ponto"), e capitalização inconsistente.

```bash
# 1. Limpeza automática: split, garbage, trim, dedup
python3 scripts/fix_validation_issues.py --slug {slug} --clean-keywords --dry-run
python3 scripts/fix_validation_issues.py --slug {slug} --clean-keywords
```

O `--clean-keywords` executa 4 operações em sequência:

1. **Remover template garbage** — instruções de formulário que ficaram no lugar de keywords reais (regex: `máximo \d`, `separados com`, `espaçamento`, `parágrafo de \d+ pt`)
2. **Separar keywords aglutinadas** — detecta separadores internos:
   - `. ` ou `.` sem espaço (quando seguido de maiúscula e keyword > 30 chars)
   - ` / ` (barra)
   - `, ` (vírgula, só se keyword > 40 chars e cada parte ≥ 3 chars)
3. **Trim de pontuação final** — remove `.`, `;`, `,` do final
4. **Dedup** — remove duplicatas case-insensitive (preserva primeira ocorrência)

```bash
# 2. Normalizar capitalização (após limpeza)
```

A capitalização das keywords depende do idioma:

- **PT**: usar as mesmas regras dos títulos — expressões consolidadas em maiúscula ("Arquitetura Moderna", "Brutalismo"), termos genéricos em minúscula ("concreto armado", "preservação"). Consultar `dict.db` e `MEMORY.md` para as formas canônicas.
- **EN**: Title Case para movimentos e expressões ("Modern Architecture", "New Brutalism"), lowercase para termos genéricos ("aesthetics", "structure"). Nomes próprios preservados.
- **ES**: mesma lógica que PT — expressões consolidadas maiúscula, genéricos minúscula.

A normalização de capitalização é **manual** (não automatizada), porque depende de contexto semântico. Após a limpeza automática, verificar inconsistências:

```python
# Detectar formas inconsistentes (mesmo keyword com casing diferente)
import json, sqlite3
conn = sqlite3.connect('anais.db')
cur = conn.cursor()
for col in ['keywords', 'keywords_en', 'keywords_es']:
    cur.execute(f"SELECT id, {col} FROM articles WHERE seminar_slug = ? AND {col} IS NOT NULL", (slug,))
    kw_forms = {}
    for art_id, kw_json in cur.fetchall():
        for k in json.loads(kw_json):
            lower = k.strip().lower()
            kw_forms.setdefault(lower, set()).add(k.strip())
    inconsistent = {l: f for l, f in kw_forms.items() if len(f) > 1}
    if inconsistent:
        print(f"\n{col}: {len(inconsistent)} inconsistências")
        for lower, forms in sorted(inconsistent.items()):
            print(f"  {lower}: {forms}")
```

Escolher a forma canônica para cada caso e aplicar com UPDATE direto no banco.

### 1.4 Aplicar correções ao banco

Todas as correções das etapas 1.1–1.3 são aplicadas ao `anais.db`. Reportar contagens (N títulos, N refs corrigidas, N keywords corrigidas).

**Nota:** Resumos, abstracts e keywords faltantes já foram tratados na Fase 0. A Fase 1 foca apenas em **corrigir** dados existentes (capitalização de títulos, limpeza de refs, normalização de keywords), não em preencher lacunas.

### 1.5 Loop de validação e correção

A validação é o **checkpoint** do loop. O `--loop` combina validação + auto-fixes + fix handlers numa única execução iterativa. Só sai do loop quando nenhuma correção é aplicada numa iteração, ou após 5 iterações (cap de segurança).

```bash
# Executar o loop completo (recomendado):
python3 scripts/fix_validation_issues.py --slug {slug} --loop
```

```
         ┌───────────────────────────────────────────┐
         │  validate_metadata.py --fix (auto-fixes)   │
         │  A15 locale mismatch                       │
         │  A16 control chars                         │
         │  A17 refs duplicadas                       │
         │  A20 abstract overflow                     │
         │  A21 abstract_es lixo EN / redundante      │
         │  A22 body text em refs (remove entradas)   │
         └──────────────┬────────────────────────────┘
                        │
                        ▼
         ┌───────────────────────────────────────────┐
         │  fix handlers (extração de fontes/)        │
         │  A07 extrair abstract_en                   │
         │  A08 extrair keywords_en                   │
         │  A19 re-extrair abstracts truncados         │
         └──────────────┬────────────────────────────┘
                        │
                        ▼
              Algo foi corrigido?
              ╱              ╲
            sim               não → sair do loop → 1.6
              ╲              ╱
               ▼
              volta ao topo (max 5×)

**NOTA:** A10 (backfills), A11 (split), A12 (não-refs), A13 (URLs órfãs)
são resolvidos pelo sweep_refs (1.2b) — NÃO fazem parte do loop.
Se restarem após o sweep, são casos ambíguos para revisão LLM (1.2c).
```

**IMPORTANTE:** O `--loop` **NÃO** re-roda `clean_references.py` nem `--sweep-refs`. Esses devem ser executados **antes** do loop (etapas 1.2a e 1.2b). O loop trata apenas extração de fontes/ (A07, A08, A19) — issues de refs (A10-A13) são resolvidos pelo sweep e pela revisão LLM (1.2c).

**Máximo 5 iterações.** Se não convergir, os issues restantes vão para revisão humana.

**Sem risco de loop infinito:** cada fix handler só aplica correções idempotentes (extrair texto mais longo, remover não-ref, substituir backfill). Nenhuma correção pode criar um issue que outra correção desfaz.

#### 1.5a Checks da validação

```bash
# Preview (sem alterar banco)
python3 scripts/validate_metadata.py --slug {slug} --dry-run

# Aplicar auto-fixes e gerar relatório
python3 scripts/validate_metadata.py --slug {slug} --fix
```

O script primeiro constrói um **perfil do seminário** (% de preenchimento de cada campo). Só sinaliza campo faltante se ≥30% dos artigos do seminário têm esse campo (evita ruído em seminários sem seção EN).

**Checks:**

| Check | Descrição | Modo |
|-------|-----------|------|
| A01 | abstract_en existe mas keywords_en falta | REPORT |
| A02 | keywords_en existe mas abstract_en falta | REPORT |
| A03 | abstract_es existe mas keywords_es falta | REPORT |
| A04 | keywords_es existe mas abstract_es falta | REPORT |
| A05 | ~~REMOVIDO~~ — em locale=es, `abstract` já contém o resumo em espanhol; copiar para abstract_es criava ciclo com A21 | — |
| A06 | ~~REMOVIDO~~ — mesma lógica: `keywords` já está em espanhol para locale=es | — |
| A07 | Marcador "Abstract" no fontes/ mas abstract_en vazio | REPORT |
| A08 | Marcador "Keywords" no fontes/ mas keywords_en vazio | REPORT |
| A09 | Marcador "Resumen" no fontes/ mas abstract_es vazio | REPORT |
| A10 | Backfill pendente (refs com `__`, `---`, etc.) | REPORT |
| A11 | Ref > 500 chars (provavelmente concatenada) | REPORT |
| A12 | Não-referência nas refs (créditos, CVs, agradecimentos) | REPORT |
| A13 | URLs órfãs (ref é só URL) | REPORT |
| A14 | Abstract contém email, afiliação ou CV | REPORT |
| A15 | Locale mismatch (abstract em ES mas locale=pt-BR) | AUTO-FIX |
| A16 | Control characters em campos de texto | AUTO-FIX |
| A17 | Referências duplicadas no mesmo artigo | AUTO-FIX |
| A18 | Artigo sem autores vinculados | REPORT |
| A19 | Abstract possivelmente truncado (sem pontuação final) | REPORT |
| A20 | Abstract overflow (>5000 chars — corpo do texto vazado) | AUTO-FIX |
| A21 | abstract_es com lixo EN (marcadores Abstract/Keywords/⏐) ou redundante (== abstract em locale=es) | AUTO-FIX |
| A22 | Refs com body text (>200 chars narrativo) ou figure captions | AUTO-FIX (remove entradas) + LLM (ambíguos) |
| A23 | abstract_en colado no abstract PT (extração capturou PT+EN como bloco único) | AUTO-FIX (separa PT e EN no boundary "Abstract:"/"The present paper"/etc.) |
| A24 | Encoding ruim (caracteres substitutos ĕ/ė, espaços entre letras) — fonte do PDF com encoding não-padrão | REPORT (requer extração via imagem: `pdftoppm` + leitura visual) |
| A25 | Keywords coladas no final de abstract/abstract_en/abstract_es ("Palavras-chave:", "Keywords:", "Palabras clave:") | AUTO-FIX (corta no marcador). **Guard**: se o marcador aparece no meio de uma frase narrativa (precedido por palavra em minúscula), NÃO corta — é parte do texto, não label de seção. |
| A26 | Abstract em idioma diferente do locale: campo `abstract` (PT) contém texto em espanhol (Resumen inserido no campo errado) | AUTO-FIX (move abstract → abstract_es, seta abstract = NULL) |
| A27 | Texto PT colado no abstract_en: extração capturou EN + notas/texto em PT no mesmo campo | AUTO-FIX (corta no boundary EN→PT, detectado por marcadores PT como "Este artigo", "Palavras-chave:") |

**Relatório:** Salva `revisao/{slug}-validation.json` com a lista de issues e `category_b_candidates` (issues que precisam de julgamento LLM).

#### 1.5b Issues e responsabilidades

| Check | Descrição | Quem resolve | Método |
|-------|-----------|-------------|--------|
| A01-A04 | Mismatches EN/ES | revisão humana | conferência no PDF |
| A05, A06 | ~~REMOVIDOS~~ — ciclo com A21 | — | — |
| A07 | abstract_en faltante (marcador no fontes/) | fix handler | `extract_abstract_en()` |
| A08 | keywords_en faltante (marcador no fontes/) | fix handler | `extract_keywords_en()` |
| A09 | abstract_es faltante (marcador no fontes/) | revisão humana | extração manual |
| A10 | Backfill pendente (___) | sweep_refs (1.2b) | `clean_references.py` + sweep passada 1 |
| A11 | Ref > 500 chars (concatenada) | sweep_refs (1.2b, threshold 300) + validate (report >500) | `split_concatenated_refs()` passada 3 |
| A12 | Não-referência nas refs | sweep_refs (1.2b) | `is_bibliographic_ref()` passada 4 |
| A13 | URLs órfãs | sweep_refs (1.2b) | passada 1 (fragmentos) |
| A14 | Abstract contaminado | revisão humana | falsos positivos frequentes |
| A15 | Locale mismatch | auto-fix (validate) | detecção de idioma |
| A16 | Control characters | auto-fix (validate) | remoção automática |
| A17 | Refs duplicadas | auto-fix (validate) | dedup automático |
| A18 | Sem autores | revisão humana | investigação manual |
| A19 | Abstract truncado | fix handler | `re_extract_abstract()` (prioriza fontes_doc/) |
| A20 | Abstract overflow (>5000 chars) | auto-fix (validate) | trunca no marcador de keywords |
| A21 | abstract_es com lixo EN | auto-fix (validate) | truncar no marcador de keywords ES, ou NULL se redundante |
| A22 | Refs com body text/figure captions | sweep_refs passada 0 | `is_body_text()`, `FIGURE_RE` |

**REGRA CRÍTICA sobre refs:** Lugar de footnote e endnote **NÃO** é no campo `references_`. Se o artigo usa citação em nota de rodapé ao invés de bibliografia, o campo `references_` fica vazio (ou com as poucas refs bibliográficas que houver).

#### 1.5c Critério de saída do loop

**Critério de conclusão**: os issues restantes são **fatos** (dado não existe no documento original), não **erros** (dado errado ou extraível). Se um issue é corrigível, o script deve corrigi-lo — não deixar para revisão humana.

Após convergir, atualizar `revisao/{slug}-rev-status.md` com:
- Resultados da validação final (issues restantes por categoria)
- Estatísticas de preenchimento atualizadas
- Issues residuais devem ser **dados ausentes no PDF** (verificados), não erros

### 1.6 Auditoria final

#### 1.6a Cobertura de metadados (artigos)

Verificar a cobertura de **todos** os campos dos artigos. Funciona como checklist final — nenhum campo deve passar despercebido.

```python
import json, sqlite3
conn = sqlite3.connect('anais.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

fields = ['title', 'subtitle', 'abstract', 'abstract_en', 'abstract_es',
          'keywords', 'keywords_en', 'keywords_es', 'references_', 'locale',
          'title_en', 'subtitle_en']

cur.execute('SELECT * FROM articles WHERE seminar_slug = ? ORDER BY id', (slug,))
rows = cur.fetchall()

print(f'=== Cobertura — {slug} ({len(rows)} artigos) ===')
for col in fields:
    filled = sum(1 for r in rows if r[col] and r[col] not in ('[]', ''))
    pct = filled * 100 // len(rows)
    print(f'  {col:15s}: {filled:3d}/{len(rows)} ({pct:3d}%)')

# Autores
cur.execute("""SELECT a.id, COUNT(aa.author_id) as n
    FROM articles a LEFT JOIN article_author aa ON a.id = aa.article_id
    WHERE a.seminar_slug = ? GROUP BY a.id""", (slug,))
no_auth = [r['id'] for r in cur.fetchall() if r['n'] == 0]
print(f'  {"autores":15s}: {len(rows)-len(no_auth):3d}/{len(rows)}')
if no_auth:
    print(f'    SEM AUTORES: {no_auth}')

# Seções
cur.execute('SELECT COUNT(*) FROM sections WHERE seminar_slug = ?', (slug,))
n_sections = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM articles WHERE seminar_slug = ? AND section_id IS NOT NULL', (slug,))
with_section = cur.fetchone()[0]
print(f'  {"seções":15s}: {n_sections} seções, {with_section}/{len(rows)} artigos com seção')
```

| Campo | Obrigatório | Observação |
|-------|-------------|------------|
| title | ✅ sim | Deve ter 100% |
| subtitle | ❌ não | Nem todo artigo tem subtítulo |
| abstract | ✅ sim | Exceções: artigos só resumo sem abstract no PDF |
| abstract_en | condicional | Se ≥30% do seminário tem, buscar nos faltantes |
| abstract_es | condicional | Só artigos em espanhol |
| keywords | ✅ sim | Exceções: template vazio no PDF |
| keywords_en | condicional | Se ≥30% do seminário tem |
| keywords_es | condicional | Só artigos em espanhol |
| references_ | ✅ sim | Exceções: artigos com footnotes (sem lista de refs) |
| locale | ✅ sim | Deve ter 100% |
| title_en | ❌ não | Só se o artigo tem seção EN no PDF |
| subtitle_en | ❌ não | Raro |
| autores | ✅ sim | Deve ter 100% |

#### 1.6b Metadados do seminário (verificar + preencher)

**Objetivo:** Garantir que os metadados do seminário estejam completos e corretos. Diferente da cobertura de artigos (que é estatística), aqui cada campo deve ser **verificado e preenchido** — não basta listar o que falta.

**REGRA — Verificar contra a ficha catalográfica original:** Abrir o PDF dos anais (geralmente primeiras páginas) e comparar CADA campo com a ficha CIP/catalográfica. Verificar:
- **title/subtitle**: corresponde ao que consta na capa e na ficha? Ortografia, pontuação, capitalização.
- **publisher**: é o que consta na ficha (nome completo ou sigla)? Não inventar — usar exatamente o que a publicação indica.
- **editors**: "organização" ou "coordenação"? Usar o termo da ficha. Nomes completos conforme a ficha.
- **description**: transcrever a ficha catalográfica do PDF (ver procedimento abaixo). Se o campo foi gerado automaticamente por `build_description`, comparar com a ficha original e corrigir divergências.
- **isbn**: confere com a ficha?
- **location/date_published**: confere com a capa?

**"Disponível originalmente em:"**: se os anais foram publicados originalmente em site externo ao docomomobrasil.com (ex: site da universidade organizadora, Even3, plataforma do evento), adicionar ao final da description: `Disponível originalmente em: <URL>.` — NÃO usar links do docomomobrasil.com (é o site que estamos substituindo).

```python
cur.execute('SELECT * FROM seminars WHERE slug = ?', (slug,))
sem = cur.fetchone()
sem_fields = ['title', 'subtitle', 'publisher', 'isbn', 'date_published',
              'location', 'description', 'editors']
print(f'\n=== Metadados do seminário ===')
for col in sem_fields:
    val = sem[col] if sem[col] else '— FALTANDO'
    print(f'  {col:15s}: {str(val)[:80]}')
```

| Campo | Obrigatório | Fonte | Como preencher |
|-------|-------------|-------|----------------|
| title | ✅ | Capa/ficha catalográfica | Nome completo do evento |
| subtitle | ❌ | Capa | Tema do evento (quando houver) |
| publisher | ✅ | Ficha catalográfica | Editora dos anais. Se não constar, usar "Núcleo Docomomo {Estado/Região}" |
| isbn | ✅ | Ficha catalográfica | Se disponível. Buscar também via Google `"ISBN" "{título do evento}"` |
| date_published | ✅ | Capa/programa | Data do evento (formato YYYY-MM-DD) |
| location | ✅ | Capa/programa | Cidade do evento |
| description | ✅ | Construir | Referência bibliográfica completa dos anais (ABNT) |
| editors | ❌ | Ficha catalográfica / programa / site | Organizadores. Se não constar na ficha, buscar no programa do evento ou no site |

**Procedimento para campos faltantes:**

1. **Verificar a ficha catalográfica** no PDF dos anais (geralmente nas primeiras páginas, capa ou contracapa)
2. **Se a ficha não tem o dado**, buscar na internet: `"{título do evento}" "{ano}" site:{domínio do evento}`, buscar no Google Scholar, no Catálogo da Biblioteca Nacional
3. **Se não encontrar**, registrar como "não localizado" no `revisao/{slug}-rev-status.md`
4. **Regra do publisher**: quando não indicado na ficha, usar "Núcleo Docomomo {Estado/Região}" para regionais ou "Docomomo Brasil" para nacionais

**Após preencher todos os campos, gerar/atualizar a `description` (ficha catalográfica ABNT):**

O campo `description` é a referência bibliográfica completa dos anais. **Prioridade**: usar a ficha catalográfica do próprio PDF dos anais (quando existir). Se o PDF tem ficha CIP, transcrever fielmente — usar os mesmos termos (coordenação/organização, editora completa vs sigla, modo de acesso se constar). Se o PDF não tem ficha, construir a partir dos campos do seminário usando o formato padrão abaixo.

Formato padrão (quando não há ficha no PDF):

```
N° Nome do Evento: anais: Subtítulo [recurso eletrônico] / organização: Editor1, Editor2. Cidade: Editora, Ano. ISBN: XXX.
```

Exemplos reais:
```
5° Seminário Docomomo Brasil: anais: Arquitetura e Urbanismo modernos: projeto e preservação [recurso eletrônico] / organização: Hugo Segawa. São Carlos: SAP-EESC-USP, 2003. ISBN: 85-85205-43-1.

1º Seminário Docomomo Norte/Nordeste: anais: Arquitetura e Urbanismo Modernos no Norte e Nordeste do Brasil: universalidade e diversidade [recurso eletrônico] / comissão organizadora: Andréa Câmara... [et al.]. Recife: DEA-UNICAP; MDU-UFPE; CECI, 2006.
```

Código para gerar e verificar:

```python
import json, re

EVENT_NAME = {
    'sdbr': 'Seminário Docomomo Brasil',
    'sdnne': 'Seminário Docomomo Norte/Nordeste',
    'sdmg': 'Seminário Docomomo Minas Gerais',
    'sdrj': 'Encontro Docomomo Rio',
    'sdsp': 'Seminário Docomomo São Paulo',
    'sdsul': 'Seminário Docomomo Sul',
    'sdpr': 'Seminário Docomomo Paraná',
}

def get_event_name(slug):
    for prefix, name in EVENT_NAME.items():
        if slug.startswith(prefix):
            return name
    return 'Seminário Docomomo'

def build_description(sem):
    """Gera a ficha catalográfica a partir dos campos do seminário."""
    slug = sem['slug']
    number = int(re.search(r'(\d+)$', slug).group(1))
    event = get_event_name(slug)
    subtitle = sem['subtitle'] or ''
    publisher = sem['publisher'] or ''
    isbn = sem['isbn'] or ''
    year = sem['year']
    location = sem['location'] or ''

    editors = []
    if sem['editors']:
        try:
            editors = json.loads(sem['editors'])
        except (json.JSONDecodeError, TypeError):
            pass

    # Montar
    desc = f'{number}° {event}: anais'
    if subtitle:
        desc += f': {subtitle}'
    desc += ' [recurso eletrônico]'

    if editors:
        if len(editors) <= 3:
            desc += f' / organização: {", ".join(editors)}'
        else:
            desc += f' / organização: {editors[0]} et al.'

    # Imprenta: Cidade: Editora, Ano
    if location and publisher and year:
        desc += f'. {location}: {publisher}, {year}'
    elif location and year:
        desc += f'. {location}, {year}'
    elif publisher and year:
        desc += f'. {publisher}, {year}'

    if isbn:
        desc += f'. ISBN: {isbn}'

    desc += '.'
    return desc

# Verificar
cur.execute('SELECT * FROM seminars WHERE slug = ?', (slug,))
sem = cur.fetchone()
generated = build_description(sem)
current = sem['description'] or ''

print(f'Atual:  {current}')
print(f'Gerada: {generated}')

if current != generated:
    print('→ DIFERENÇA — atualizar:')
    cur.execute('UPDATE seminars SET description = ? WHERE slug = ?',
                (generated, slug))
    conn.commit()
```

**Regras da ficha catalográfica:**
- `N°`: usar número ordinal (1°, 2°, ..., não 1º)
- `[recurso eletrônico]`: sempre presente (todos os anais são digitais)
- Editores: até 3 nomes completos; 4+ usa `et al.`
- Cidade: é a cidade de **publicação** (sede da editora), não necessariamente a do evento
- ISBN: manter formato original (com ou sem hífens)
- Ponto final no fim
- Se a ficha original dos anais tiver informações adicionais (DOI, URL, número de páginas), preservar ao final

#### 1.6c Seções / sessões (estrutura temática do evento)

**Objetivo:** Mapear os artigos à estrutura temática do evento — eixos temáticos, mesas temáticas, ou sessões.

**Hierarquia de preferência:** Primeiro buscar **seções (eixos temáticos)** — são a divisão editorial dos anais, mais estável e significativa. Só recorrer a **sessões** (divisão logística do programa) se os eixos não forem encontrados. Eixos temáticos geralmente aparecem na **chamada de trabalhos**, na **capa dos anais**, no **sumário**, ou no **cabeçalho dos artigos**. Sessões aparecem no **programa do evento**.

**Fontes (em ordem de preferência):**
1. Sumário ou índice dos anais (PDF do volume)
2. Cabeçalho dos PDFs dos artigos (eixo/mesa indicado na primeira página)
3. Chamada de trabalhos (site do evento, e-mail de divulgação)
4. Caderno de programação / programa das sessões
5. Caderno de resumos (quando publicado em separado)

**Procedimento:**

1. **Verificar os PDFs dos artigos** — o cabeçalho da primeira página indica o eixo temático? Se sim, extrair os eixos daí (mais confiável que o programa)
2. **Verificar o sumário dos anais** — se o PDF do volume tem sumário organizado por seções/eixos, usar essa estrutura
3. **Se não houver eixos**, localizar o programa do evento — buscar na internet `"{título do evento}" programa sessões`, verificar o site do evento
4. **Extrair as seções** — listar seção/eixo + título + artigos/autores. Se o PDF do programa tiver layout de 2 colunas, converter para imagem (`pdftoppm`) e ler visualmente em vez de confiar no pdftotext
5. **Criar as seções no banco** — `INSERT INTO sections (seminar_slug, title, seq)`
   - **Capitalização**: aplicar as mesmas regras dos títulos de artigos (sentence case, expressões consolidadas maiúsculas, genéricos minúsculas). Títulos de eixos no PDF geralmente estão em ALL CAPS — converter para sentence case.
6. **Mapear artigos → seções** — cruzar autores e títulos com o banco. Usar fuzzy matching + verificação manual dos autores para desambiguar títulos que mudaram entre programa e publicação
7. **Artigos sem seção** — artigos nos anais que não aparecem no programa (pôsteres, adições tardias) ficam com `section_id = NULL`
8. **Seções sem artigos** — sessões cujos papers não foram publicados nos anais (ex: conferências de convidados, mesas-redondas). Criar a seção mesmo assim para documentar a estrutura do evento

**Quando não encontrar nem eixos nem programa:** Registrar no status que a estrutura temática não foi localizada.

#### 1.6d Autores (verificação exaustiva)

**Objetivo:** Garantir que **todos** os autores de **todos** os artigos estão no banco, com nomes corretos. Não podemos deixar de citar um autor.

**REGRA**: Esta verificação é **exaustiva** — comparar CADA artigo com o PDF. Não amostrar.

**Passo 1 — Extrair autores da fonte e comparar com o banco (PDF→DB):**

A direção da verificação é **fonte → banco**: extrair os nomes do documento original e verificar se cada um existe no banco. O erro mais provável é um autor que está no PDF mas não foi inserido no banco.

Para cada artigo, extrair os nomes dos autores seguindo a **hierarquia de fontes** (mesma ordem de §0.3):

1. **doc/docx/odt/fodt/rtf** → ler com python-docx ou equivalente (preserva estilos — autor geralmente em estilo específico)
2. **fontes_plumber/** (.jsonl) → blocos com role near "heading" ou entre título e abstract
3. **fontes/** (.txt do pdftotext) → texto entre título e "Resumo"
4. **PDF** → ler página 1 (pdfplumber ou imagem para escaneados)

Para cada autor encontrado na fonte, verificar se existe no banco (comparar familyname). Atenção aos falsos positivos: sobrenomes que aparecem no cabeçalho mas são de pessoas mencionadas no **título** (objeto de estudo, não autor), siglas de universidades no formato "SIGLA, cidade" que parecem "SOBRENOME, Nome", e palavras em inglês de títulos bilíngues.

Verificar:

1. **Completude**: todos os autores do PDF estão no banco? Nenhum faltando?
2. **Nomes**: `givenname` e `familyname` corretos? Partículas (de, da, do) no `givenname`, último sobrenome no `familyname`. Hispânicos: duplo sobrenome.
3. **Afiliação**: preenchida e no formato correto (sigla: `FAU-USP`, `PROPAR-UFRGS`)? Sem títulos acadêmicos, endereços, emails.
4. **Ordem**: a ordem dos autores no banco corresponde à do PDF (primeiro autor = autor principal)?

```python
# Gerar relatório comparativo: autores do banco vs PDF
import sqlite3, pdfplumber, re, json

conn = sqlite3.connect('anais.db')
cur = conn.cursor()

cur.execute("""
    SELECT a.file, a.title,
           GROUP_CONCAT(au.givenname || ' ' || au.familyname, '; ' ) as db_autores,
           COUNT(aa.author_id) as n_db
    FROM articles a
    LEFT JOIN article_author aa ON a.id = aa.article_id
    LEFT JOIN authors au ON aa.author_id = au.id
    WHERE a.seminar_slug = ?
    GROUP BY a.id ORDER BY a.file
""", (slug,))

discrepancias = []
for file, title, db_autores, n_db in cur.fetchall():
    # Ler PDF e extrair autores do cabeçalho
    pdf = pdfplumber.open(f'nacionais/{slug}/pdfs/{file}')
    text = pdf.pages[0].extract_text() or ''
    pdf.close()

    # Contar autores no PDF (entre título e Resumo)
    m = re.search(r'(?:RESUMO|Resumo)', text)
    if m:
        header = text[:m.start()]
        # Heurística: contar nomes próprios no cabeçalho
        # (implementação depende do formato do seminário)

    # Comparar e reportar discrepâncias
    # ...
```

**Passo 2 — Corrigir discrepâncias:**

Para cada artigo com autor faltante ou nome errado:
- Adicionar o autor ao banco (`INSERT INTO authors` + `INSERT INTO article_author`)
- Corrigir givenname/familyname se necessário
- Registrar cada correção no rev-status

**Passo 3 — Deduplicação, expansão de iniciais e ORCID:**

Se autores novos foram adicionados ao banco, rodar o mesmo fluxo do pipeline_tratamento.md §7.4–7.6:

```bash
# 1. Alimentar dict.db com nomes novos
python3 dict/seed_authors.py

# 2. Deduplicar autores (merge duplicatas: Pilotis + Jaro-Winkler + coautoria)
python3 scripts/dedup_authors.py --dry-run
python3 scripts/dedup_authors.py

# 3. Expandir iniciais (se houver givennames abreviados)
python3 scripts/expand_initials.py --report
python3 scripts/expand_initials.py --pilotis

# 4. Buscar ORCID para autores sem ORCID
# Lembrar: tentar múltiplas combinações de sobrenome (ver memory/feedback_orcid_search.md)
python3 scripts/fetch_orcid.py --search
python3 scripts/fetch_orcid.py --review
python3 scripts/fetch_orcid.py --apply
```

**REGRA**: Se um autor novo foi adicionado ao banco, SEMPRE rodar o fluxo completo (seed → dedup → iniciais → ORCID). Autores podem já existir no banco por outro seminário com grafia ligeiramente diferente.

**Critério de conclusão da 1.6**: todos os campos obrigatórios dos artigos com 100% (ou exceções documentadas); metadados do seminário preenchidos; seções/sessões criadas e artigos mapeados onde possível; autores verificados (completude e nomes). Tudo registrado no `revisao/{slug}-rev-status.md`.

---

## Fase 2 — Gerar HTML de revisão

```bash
python3 scripts/gerar_revisao_html.py {slug}
```

Gera `revisao/revisao-{slug}.html` com:
- Capa do seminário (se houver)
- Ficha catalográfica (campo `description` do DB, com fallback para YAML)
- **Sumário de validação** — se `revisao/{slug}-validation.json` existir, exibe painel com contagem de issues por categoria
- Artigos agrupados por seção
- Para cada artigo: título, subtítulo, autores (com afiliação), resumo PT, abstract EN, keywords PT/EN, referências
- **Alertas inline** — artigos com issues de validação exibem badges coloridos (warning/error/info) com detalhes do problema

O HTML é auto-contido (CSS inline, capa em base64). Abrir no navegador para revisão humana.

**IMPORTANTE:** Rodar `validate_metadata.py --fix` **ANTES** de gerar o HTML, para que os warnings estejam atualizados. Sem o JSON de validação, o HTML não mostra alertas.

**Checkpoint — dump e commit:**

```bash
python3 scripts/dump_anais_db.py
python3 dict/dump_db.py
git add anais.sql dict/dict.sql revisao/{slug}-*
git commit -m "{slug} revisão automática concluída (Fases 0-2)"
```

Este commit marca o estado pós-revisão automática / pré-revisão humana. Permite reverter se a revisão humana introduzir problemas.

**Próximo passo:** Executar o [pipeline de revisão humana](pipeline_revisao_humana.md).

---

## Fase 3 — Aprendizado pós-revisão

Executar **após** a conclusão da revisão humana ([pipeline de revisão humana](pipeline_revisao_humana.md)). Usa como insumo **todas** as correções: tanto as da fase automática (Fases 0–1) quanto as da revisão humana.

**Princípio:** Para cada correção (automática ou humana), perguntar: "por que o pipeline não resolveu isso automaticamente?" O aprendizado só existe se resultar em **alteração concreta**: entrada no dict, regra no script, ou instrução documentada. Documentar sem alterar nada não é aprendizado.

### 3.1 Diagnóstico unificado

Agregar TODAS as correções num log único antes de diagnosticar:

1. **Correções da fase automática** (registradas no `{slug}-rev-status.md`):
   - Overflows de abstract corrigidos manualmente (deveria ter sido A20?)
   - Keywords com lixo limpas manualmente (deveria ter sido clean_keywords?)
   - Backfills resolvidos manualmente (deveria ter sido clean_references?)
   - Abstracts em idioma errado (deveria ter sido A26?)
   - Refs com notas/lixo removidas manualmente (deveria ter sido sweep_refs?)

2. **Correções da revisão humana** (registradas no `{slug}-rev.md`):
   - Títulos/subtítulos corrigidos (deveria ter sido normalizar_maiusculas + LLM?)
   - Refs com splits errados (deveria ter sido sweep_refs passada 1?)
   - Dados faltantes (deveria ter sido extraído na Fase 0?)

3. **Cruzamento com seminários anteriores**: quais problemas se repetiram? Fixes que deveriam ter sido incorporados na revisão do seminário anterior e não foram.

Para cada problema, classificar:
- **Padrão recorrente** → automatizar (novo check, nova heurística, novo filtro)
- **Caso único** → só aplicar a correção
- **Dado faltante no dict.db** → adicionar
- **Gap na ordem de execução** → ajustar pipeline (ex: rodar check X antes da Fase Y)

Registrar o diagnóstico completo no `{slug}-rev-status.md`, seção "Log de correções" com tabela causa raiz.

### 3.2 Atualizar dict.db

Analisar o arquivo `revisao/{slug}-titulos-aprendizado.json` (ou as correções da revisão) e classificar cada correção:

| Tipo | Ação no dict.db | Exemplo |
|------|----------------|---------|
| Palavra genérica forçando maiúscula | **REMOVER** do dict | `obra`, `restauração`, `tradição` |
| Gentílico/adjetivo forçando maiúscula | **REMOVER** do dict | `carioca`, `metropolitana` |
| Nome próprio faltando | **ADICIONAR** ao dict | `Bienal`, `Esplanada`, `Centenário` |
| Expressão consolidada faltando | **ADICIONAR** como expressão | `Centro Administrativo`, `Base Naval` |

```bash
# Verificar contradições: palavras corrigidas p/ minúscula que estão no dict
python3 -c "
import sqlite3
conn = sqlite3.connect('dict/dict.db')
for row in conn.execute(\"\"\"
    SELECT word, category, source FROM dict_names
    WHERE source = 'titulos' ORDER BY word
\"\"\"):
    print(f'{row[0]} ({row[1]}/{row[2]})')
"
```

**Nota:** `dict/dict.sql` será salvo no checkpoint da §3.8.

**Critério de remoção**: se a revisão corrigiu uma palavra para minúscula em ≥2 artigos, e a palavra não é nome próprio, remover do dict.

**Critério de adição**: se a revisão corrigiu uma palavra para maiúscula, e é nome de edifício, instituição, evento ou lugar, adicionar ao dict.

### 3.3 Atualizar scripts de validação

Se um tipo de erro apareceu em ≥3 artigos e **não** é coberto pelos scripts existentes, adicionar a regra.

### 3.4 Atualizar pipeline

Se o diagnóstico identificou gaps na ordem de execução (ex: "A20 deveria rodar na Fase 0.5, não só na 1.5"), atualizar este documento.

### 3.5 Verificar

Re-rodar os scripts alterados em dry-run no mesmo seminário para confirmar que as melhorias não causam regressão. Testar também num seminário não revisado.

### 3.6 Registrar aprendizado

Arquivo: `revisao/{slug}-aprendizado-revisao.json`

```json
{
  "dict_removals": ["obra", "restauração"],
  "dict_additions": ["Bienal", "Esplanada"],
  "scripts_alterados": ["validate_metadata.py", "fix_validation_issues.py"],
  "pipeline_alterado": true,
  "padroes_confirmados": [
    "'Arquitetura Moderna' sempre maiúscula como conceito",
    "'arquitetura moderna de [cidade]' descritiva → minúscula"
  ]
}
```

Atualizar MEMORY.md com padrões confirmados novos.

### 3.7 Revisão de engenharia

**PRIMEIRO — Autoavaliação**: antes de revisar os scripts, responder: "executei **todas** as etapas do pipeline_revisao.md para este seminário?" Reler o pipeline do início (§0.0) ao fim (Fase 2) e verificar que nenhuma etapa foi pulada ou feita pela metade. Se alguma etapa foi pulada, voltar e fazer.

Após confirmar que o pipeline foi executado integralmente e as melhorias (3.2–3.6) foram implementadas, revisar o `pipeline_revisao.md`, o `pipeline_revisao_humana.md` e os scripts alterados com olhar de engenheiro de software:

- **Lints**: inconsistências entre o que o pipeline documenta e o que os scripts fazem
- **Erros de lógica**: checks que se contradizem (ex: A25 cortava abstracts que A19 depois flaggava como truncados), auto-fixes que desfazem correções manuais
- **Redundância**: mesma verificação em dois lugares, checks duplicados, código morto
- **Riscos de loop**: auto-fixes que podem criar problemas que outros auto-fixes tentam resolver (ex: A05/A06 criavam ciclo com A21 — já removidos)
- **Ordem de execução**: checks que dependem de dados que só existem após outra etapa
- **Cobertura**: gaps entre o que o pipeline promete e o que os scripts implementam (ex: pipeline diz "verificar idioma" mas nenhum check faz isso)
- **Robustez**: scripts que crasham com dados inesperados (ex: keywords não-JSON), guards insuficientes

Registrar os achados e correções no `{slug}-rev-status.md`.

### 3.8 Checklist de conclusão

**ANTES de commitar**, verificar que TODAS as etapas da Fase 3 foram executadas:

- [ ] 3.1 Diagnóstico unificado (automático + humano) — tabela de causa raiz no rev-status
- [ ] 3.2 Dict atualizado (remoções + adições)
- [ ] 3.3 Scripts corrigidos (se aplicável)
- [ ] 3.4 Pipeline atualizado (se aplicável)
- [ ] 3.5 Verificação (dry-run no mesmo seminário + teste em outro)
- [ ] 3.6 Aprendizado registrado (JSON + MEMORY.md)
- [ ] 3.7 Revisão de engenharia (lints, lógica, regressão)

Se algum item não foi feito, **parar e fazer antes de commitar**.

### 3.9 Atualizar status e fechar

1. Adicionar seminário à tabela de revisados em `CLAUDE.md` (status ✅, data)
2. Adicionar entrada no devlog do `CLAUDE.md` com resumo do que foi feito
3. Atualizar tabela de revisados neste documento (se houver)
4. Dump, commit e push:

```bash
python3 scripts/dump_anais_db.py
python3 dict/dump_db.py
git add anais.sql dict/dict.sql CLAUDE.md docs/pipeline_revisao.md docs/pipeline_revisao_humana.md \
       scripts/*.py revisao/{slug}-*
git commit -m "{slug} revisado + melhorias pipeline"
git push
```

**Exemplos concretos:**

| Seminário | Correção | Falha identificada | Incorporação |
|-----------|----------|-------------------|-------------|
| sdbr10 | "la" maiúscula em título ES | `dict.db` tinha "la" como `nome` (de `seed_authors.py`) | Removido do dict |
| sdbr10 | NOTAS misturadas com refs | sweep_refs sem passada 0 para lixo grosso | Adicionados padrões body text e figure captions |
| sdbr13 | 11 overflows abstract_en | A20 só rodava na Fase 1.5 | Rodar validate --fix na Fase 0.5 |
| sdbr13 | 31 keywords_en com lixo | clean_keywords sem filtros ALL CAPS/junk | KW_JUNK_RE, ALL CAPS ≥15, >80c |
| sdbr13 | abstract ES no campo PT | Não existia check para idioma errado | A26 novo (auto-fix) |
| sdbr13 | PT colado no abstract_en | A23 só detecta EN→PT, não PT→EN | A27 novo (auto-fix) |

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

Cada onda segue o mesmo fluxo (Fases 0-2 automáticas + Fases 3-5 humanas). Os seminários já revisados (sdbr01-07) e os nacionais já publicados no OJS não entram no pipeline.

---

## Notas sobre uso de agentes em background

A Fase 0 envolve leitura e extração de dezenas de arquivos de texto. É tentador delegar tudo a agentes em background, mas na prática os agentes travam frequentemente ao gerar scripts longos de extração. As regras abaixo evitam desperdício de tempo:

### O que funciona em agentes
- **Keywords**: extração por regex simples (buscar "Palavras-chave:" e "Keywords:"), pouca variação → agente funciona bem
- **References**: extração da seção "Bibliografia"/"Referências" no final do texto → agente funciona bem
- **Verificação de truncamento**: detecção por padrão (terminação, comprimento, marcadores PT em EN) → agente funciona bem

### O que NÃO funciona em agentes
- **Abstracts**: extração difícil porque a maioria dos artigos não tem header "Resumo"/"Abstract" em linha separada. O abstract é o bloco de texto entre os dados dos autores e "Palavras-chave:", sem delimitador explícito. Casos especiais frequentes:
  - Abstract EN antes do PT (ordem invertida)
  - "Abstract:" inline na mesma linha do texto (não em linha separada)
  - Artigo em espanhol (com "Resumen") ou francês (com "Résumé")
  - Comunicação curta sem header de abstract
  - Notas de rodapé coladas no final do abstract

### Estratégia recomendada
1. **Primeiro passo**: rodar script de detecção de marcadores em todos os fontes/ (localizar posições de "Resumo", "Abstract", "Palavras-chave", "Keywords" em cada arquivo)
2. **Segundo passo**: extrair automaticamente os casos simples (marcadores em linha separada, padrão claro)
3. **Terceiro passo**: para os casos que falharam, ler manualmente os primeiros 60-80 linhas do fontes/ e extrair com lógica específica

Esse fluxo em 3 passos é mais rápido que delegar tudo a um agente e esperar ele travar.

---

## Referência rápida

| Comando | Fase | Função |
|---------|------|--------|
| `scripts/extrair_fontes_plumber.py --slug {slug}` | 0.3b | Extrair fontes estruturadas (pdfplumber → .jsonl com roles semânticos) |
| `scripts/extrair_metadados_en.py --slug {slug}` | 0.6 | Extrair title_en, subtitle_en, abstract_en, keywords_en |
| `scripts/validar_abstracts.py --slug {slug}` | 0.5 | Validar abstracts (9 regras + lixo ES) |
| `scripts/validar_abstracts.py --slug {slug} --fix-swap` | 0.5 | Corrigir swaps abstract PT↔EN |
| `dict/seed_authors.py` + `seed_titles.py --apply` | 1.1a | Alimentar dicionário |
| `scripts/normalizar_maiusculas.py --slug {slug}` | 1.1a | Normalizar títulos PT |
| `scripts/normalizar_titulos_en.py --slug {slug}` | 1.1b | Normalizar títulos EN (Title Case) |
| `scripts/clean_references.py --slug {slug}` | 1.2a | Limpar referências (backfills, split ABNT, URLs) |
| `scripts/check_references.py --slug {slug} --summary` | 1.2a | Verificar referências |
| `scripts/fix_validation_issues.py --slug {slug} --sweep-refs` | 1.2b | Varredura completa de refs (fragmentos, endnotes, body text) |
| `scripts/fix_validation_issues.py --slug {slug} --clean-keywords` | 1.3 | Limpeza de keywords (split, garbage, trim, dedup) |
| `scripts/validate_metadata.py --slug {slug} --fix` | 1.5a | Validar + auto-fix (checkpoint do loop) |
| `scripts/fix_validation_issues.py --slug {slug} --loop` | 1.5 | Loop validate→fix→validate até convergir |
| `scripts/gerar_revisao_html.py {slug}` | 2 | Gerar HTML de revisão (com alertas de validação) |
