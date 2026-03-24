# Pipeline de Revisão Humana

Pipeline para a revisão humana dos metadados dos artigos no `anais.db`. Executado **após** o [pipeline de revisão automática](pipeline_revisao.md) (Fases 0–2).

## Correspondência entre pipelines

| Etapa | Tratamento | Revisão | Rev. Humana |
|-------|-----------|---------|-------------|
| Aquisição/extração | Fases 1–6 | — | — |
| Banco + enriquecimento | Fase 7 | — | — |
| Revisão automática | Fase 7.3 (→ rev.) | Fases 0–2 | — |
| Revisão humana | — | — | Fases 3–5 |
| Aprendizado | Fase 8 (→ rev.) | Fase 3 | — |

**Pré-requisitos:** Antes de iniciar a revisão humana, o seminário deve ter passado por:
- Fase 0 — Diagnóstico e preenchimento de lacunas
- Fase 1 — Revisão automática (normalização de títulos, limpeza de refs)
- Fase 2 — Geração do HTML de revisão (`revisao/revisao-{slug}.html`)
- Arquivo `revisao/{slug}-rev-status.md` já existente (criado na Fase 0 do pipeline automático)

**IMPORTANTE:** Após a revisão humana, **nunca** re-rodar o pipeline automático no mesmo seminário — scripts como `normalizar_maiusculas.py` sobrescreveriam os ajustes manuais.

---

## Seminários revisados — NÃO ALTERAR

| Seminário | Artigos | Data | Observações |
|-----------|---------|------|-------------|
| sdbr01 | 37 | 2026-02-24 | |
| sdbr02 | 22 | 2026-02-24 | |
| sdbr03 | 56 | 2026-02-26 | 39 títulos, 160+ refs extraídas de notas |
| sdbr04 | 79 | 2026-02-26 | Só resumos, sem refs nem texto completo |
| sdbr05 | 56 | 2026-02-28 | 25 títulos corrigidos, 971 refs limpas |
| sdbr06 | 63 | 2026-03-01 | |
| sdbr07 | 62 | 2026-03-02 | |
| sdbr08 | 188 | 2026-03-09 | 84 itens: 80 títulos, 10 swaps PT/EN, 6 refs re-extraídas, 3 autores identificados |
| sdbr09 | 170 | 2026-03-09 | ~40 itens: 4 keywords_en, 6 abstracts, 11 backfills (fix extract_author), 13 refs re-extraídas de .doc, 5 refs adicionadas |
| sdbr10 | 118 | 2026-03-14 | |
| sdbr11 | 101 | 2026-03-14 | |
| sdbr12 | 82 | 2026-03-14 | |
| sdbr13 | 181 | 2026-03-15 | |
| sdbr14 | 122 | 2026-03-15 | |
| sdbr15 | 101 | 2026-03-15 | |
| sdsul01 | 48 | 2026-03-21 | |
| sdsul02 | 35 | 2026-03-21 | |
| sdsul03 | 39 | 2026-03-21 | |
| sdsul04 | 46 | 2026-03-22 | |
| sdsul05 | 37 | 2026-03-22 | |
| sdsul06 | 24 | 2026-03-22 | 1 correção (021 título→subtítulo) |
| sdsul07 | 46 | 2026-03-23 | 1 correção (033 topônimo + PDF páginas-imagem re-extraído) |
| sdsul08 | 51 | 2026-03-23 | 1 correção (017 subtitle Estadual) |
| sdpr01 | 26 | 2026-03-23 | 2 correções (016 moderna, 022 brutalismo) |
| sdpr02 | 19 | 2026-03-23 | 3 correções (001 split título/subtítulo, 012 urbanismo, 014 arquitetura) |
| sdmg01 | 26 | 2026-03-23 | 1 correção (012 subtitle typo mg1→MG) |
| sdrj02 | 19 | 2026-03-23 | 2 correções (002 arquitetura lowercase, 007 Arquivologia uppercase) |

---

## Visão geral do fluxo

```
   Pipeline de revisão automática (pipeline_revisao.md)
         ↓
┌─────────────────────────────────────────────────────┐
│ Fase 3 — Revisão humana (usuário)                   │
│   3.1 Revisar HTML no navegador                     │
│   3.2 Anotar correções em revisao/{slug}-rev.md     │
├─────────────────────────────────────────────────────┤
│ Fase 4 — Aplicar correções da revisão humana        │
│   4.1 Registrar status da revisão (log)             │
│   4.2 Incorporar aprendizado ao dict e regras       │
├─────────────────────────────────────────────────────┤
│ Fase 5 — Fechar revisão                             │
│   5.0 Verificar log de revisão (zero ⚠️)            │
│   5.1 Pipeline final (clean + check)                │
│   5.2 Regenerar HTML (verificação)                  │
│   5.3 Alimentar dicionário (aprendizado)            │
│   5.4 Incorporar aprendizado da revisão humana      │
│   5.5 Atualizar status (CLAUDE.md, memória)         │
│   5.6 Dump + commit + push                          │
└─────────────────────────────────────────────────────┘
```

---

## Fase 3 — Revisão humana

O usuário revisa o HTML (`revisao/revisao-{slug}.html`) no navegador e anota as correções necessárias.

### O que verificar

| Campo | O que procurar |
|-------|----------------|
| **Título** | Capitalização, separação título/subtítulo, acentuação |
| **Subtítulo** | Começa com minúscula (exceto nome próprio/sigla) |
| **Título EN** | Title Case correto, nomes próprios preservados, sem truncamento |
| **Subtítulo EN** | Title Case, separação correta do título |
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

**Referências com marcador de repetição de autor (backfill):**

Basta indicar os artigos afetados — o Claude localiza as refs, identifica o autor da ref anterior e preenche automaticamente.

Sintaxes de marcador de repetição encontradas nos anais (todas tratadas por `clean_references.py`):

| Sintaxe | Exemplo | Seminários |
|---------|---------|------------|
| `__` a `________________________` | `______. Caminhos...` | sdbr03, sdbr05, sdbr07 |
| `---------` (hífens) | `---------. A cidade...` | sdbr05 |
| `–––––––` (en-dashes) | `–––––––. Espaços...` | vários |
| `———————` (em-dashes) | `———————. Obras...` | vários |
| `..........` (pontos) | `..........Arquitetura...` | vários |

**Causas conhecidas de falha do backfill** (identificadas no sdbr09, 2026-03-09):

O backfill depende de `extract_author()` em `clean_references.py` para extrair o nome do autor da ref anterior. Essa função pode falhar silenciosamente (retorna `None`), deixando o marcador `______` no texto. Causas documentadas:

| Causa | Exemplo | Fix aplicado |
|-------|---------|-------------|
| Ano entre parênteses após autor | `SOBRENOME, Nome (2003) Título...` | Padrão 1 adicionado: `AUTHOR (YYYY) Title` |
| Multi-autor com `&` ou `;` | `MARQUES & NASLAVSKY. Título...` | `&` e `;` na classe de caracteres |
| Nomes compostos com hífen | `LINS-CORRÊA, Maria. Título...` | Hífen explícito na classe |
| Nomes com apóstrofo | `D'ASSUNÇÃO, Maria. Título...` | Apóstrofo/aspas na classe |

Se encontrar backfills pendentes após `clean_references.py`, verificar se `extract_author()` falha na ref anterior. Se sim, expandir o regex e documentar aqui.

```
refs com ______: 012, 029, 049
```

**Referências concatenadas — re-extração via .doc:**

Quando refs estão aglutinadas (várias obras numa única entrada) e o pdftotext não consegue separar, usar os arquivos .doc originais:

```bash
# 1. Converter .doc para .txt via LibreOffice
soffice --headless --convert-to txt --outdir /tmp arquivo.doc

# 2. Extrair refs do .txt (seção após "Referências" / "Bibliografia" / "References")
# 3. Salvar os .txt convertidos em nacionais/{slug}/fontes_doc/
#    Convenção de nome: {id}-doc.txt (ex: sdbr09-006-doc.txt)
```

O diretório `fontes_doc/` contém textos extraídos de .doc/.docx via LibreOffice (mais limpos que o pdftotext). Quando disponível, **preferir `fontes_doc/` a `fontes/`** para re-extração de referências. Os .doc originais ficam no acervo do seminário (ex: `~/Dropbox/_docomomo/seminarios/.../`). Mapeamento .doc↔artigo: ver `revisao/{slug}-rev-status.md`.

**Outros problemas em referências:**
```
sdbr05-012:
    refs: concatenadas (verificar)

sdbr05-049:
    refs: lixo misturado (notas de rodapé, legendas)
```

**Campos faltantes:**
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
2. **Listar todos os itens** encontrados (ex: "12 itens: sdbr05-003, 010, 015, ...")
3. **Executar cada item**, na ordem em que aparece no arquivo
4. **Verificar cada item** após execução — consultar o banco para confirmar que a correção foi aplicada
5. **Reportar o resultado** como checklist completa, item a item, com ✅ ou ❌
6. Só depois de todos os itens verificados: regenerar o HTML

**O que NÃO fazer:**
- Não buscar outros problemas enquanto executa a lista — isso é trabalho da Fase 1 (pipeline automático), não da Fase 4
- Não aplicar metade dos itens e perguntar ao usuário se pode continuar
- Não misturar itens da lista com correções que o Claude encontrou por conta própria

### 4.1 Registrar status da revisão (log)

**Imediatamente após aplicar todas as correções**, criar o arquivo `revisao/{slug}-rev-status.md` registrando o resultado de cada item do arquivo de revisão. Isso evita re-revisão e serve como auditoria.

**Formato:**

```markdown
# {slug} — Status da revisão humana

Data da revisão: YYYY-MM-DD
Fonte: `revisao/{slug}-rev.md`

## Itens concluídos (N/M)

### Títulos corrigidos
- ✅ {slug}-NNN: title → "Novo título"
...

### Subtítulos corrigidos
- ✅ {slug}-NNN: subtitle → "novo subtítulo"
...

### Abstracts corrigidos
- ✅ {slug}-NNN: abstract re-extraído
- ✅ {slug}-NNN: abstract limpo (artigo não tem)
...

### Referências corrigidas
- ✅ {slug}-NNN: N referências substituídas
...

(demais categorias conforme o conteúdo da revisão)

## Itens pendentes (N/M)

### Categoria
- ⚠️ {slug}-NNN: descrição do que falta fazer e por quê
...
```

**Regras:**
- **Todo item** do `{slug}-rev.md` deve aparecer no log, marcado como ✅ (concluído) ou ⚠️ (pendente com justificativa)
- Agrupar por categoria (títulos, subtítulos, abstracts, keywords, referências, seções, autores, etc.)
- Itens pendentes devem ter **motivo** (ex: "refs parseadas de notas, precisa LLM", "verificar autores no XML/DVD")
- O log é atualizado progressivamente — se a revisão for continuada em outra sessão, acrescentar ao log existente

**Exemplo real:** `revisao/sdbr08-rev-status.md` (75/84 concluídos, 9 pendentes)

### 4.2 Incorporar aprendizado ao dict e às regras

**Executar APÓS aplicar todas as correções.** Etapas concretas:

**a) Verificar contradições com dict.db:**
```python
# Palavras corrigidas para minúscula → NÃO devem estar no dict forçando maiúscula
# Expressões corrigidas para maiúscula → DEVEM estar no dict como expressão
import sqlite3
db = sqlite3.connect('dict/dict.db')
db.execute("SELECT * FROM dict_names WHERE word='modernista' COLLATE NOCASE")
# Se retornar resultado com canonical maiúsculo → REMOVER do dict
```

**b) Atualizar dict.db:**
- **Remover** palavras que o dict força maiúscula mas que são genéricas (ex: `modernista`, `obra`, `jardim`)
- **Adicionar expressões** confirmadas como nomes próprios compostos (ex: `Assembleia Legislativa`, `Mercado Central`)
- **Adicionar nomes** próprios novos encontrados nos títulos (ex: `Nordschild`)

**c) Atualizar MEMORY.md** (seção "Padrões de capitalização confirmados"):
- Adicionar novos padrões confirmados pela revisão

**d) Verificar backfills em referências:**
- Se algum backfill manual usou sintaxe que `clean_references.py` não detectou, corrigir o regex e documentar na tabela de sintaxes da Fase 3

**Nota:** `dict/dict.sql` será salvo no checkpoint §5.4 (fim da revisão humana).

---

## Fase 5 — Fechar revisão

### 5.0 Verificar log de revisão

Antes de fechar, confirmar que o log `revisao/{slug}-rev-status.md` está completo:
- **Zero itens ⚠️**: pode fechar
- **Itens ⚠️ restantes**: decidir com o usuário se são bloqueantes ou se podem ficar como pendência documentada para sessão futura

Não fechar revisão com itens ⚠️ sem decisão explícita do usuário.

### 5.1 Pipeline final

```bash
python3 scripts/clean_references.py --slug {slug}
python3 scripts/check_references.py --slug {slug} --summary
```

Resultado esperado: 0 problemas (ou apenas problemas aceitos conscientemente).

**ATENÇÃO:** NÃO rodar `normalizar_maiusculas.py` nem `normalizar_titulos_en.py` aqui — sobrescreveria as correções da revisão humana. Apenas `clean_references.py` e `check_references.py` são seguros nesta fase.

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
```

Se a revisão humana revelou expressões consolidadas novas (ex: "Vila Operária" como nome próprio) ou exceções de capitalização, adicioná-las manualmente ao `dict.db`. Registrar padrões confirmados na memória do projeto (`MEMORY.md`) para referência futura.

### 5.4 Fechar revisão humana

A revisão humana termina quando todas as correções do `revisao/{slug}-rev.md` foram aplicadas e verificadas. Registrar o status final no `{slug}-rev-status.md`.

**Checkpoint — dump e commit:**

```bash
python3 scripts/dump_anais_db.py
python3 dict/dump_db.py
git add anais.sql dict/dict.sql revisao/{slug}-*
git commit -m "{slug} revisão humana concluída"
```

**Próximo passo:** Executar a [Fase 3 — Aprendizado](pipeline_revisao.md#fase-3--aprendizado-pós-revisão) do pipeline de revisão automática.
