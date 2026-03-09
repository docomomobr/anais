# Pipeline de Revisão Humana

Pipeline para a revisão humana dos metadados dos artigos no `anais.db`. Executado **após** o [pipeline de revisão automática](pipeline_revisao.md) (Fases 0–2).

**Pré-requisitos:** Antes de iniciar a revisão humana, o seminário deve ter passado por:
- Fase 0 — Diagnóstico e preenchimento de lacunas
- Fase 1 — Revisão automática (normalização de títulos, limpeza de refs)
- Fase 2 — Geração do HTML de revisão (`revisao/revisao-{slug}.html`)

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

**e) Dump do dict:**
```bash
python3 dict/dump_db.py
```

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

# Dump do dicionário
python3 dict/dump_db.py
```

Se a revisão humana revelou expressões consolidadas novas (ex: "Vila Operária" como nome próprio) ou exceções de capitalização, adicioná-las manualmente ao `dict.db`. Registrar padrões confirmados na memória do projeto (`MEMORY.md`) para referência futura.

### 5.4 Incorporar aprendizado da revisão humana

A revisão humana identifica erros **sistemáticos** que podem ser detectados e corrigidos automaticamente nos próximos seminários. Esta fase captura esses padrões e os transforma em validações para o [pipeline automático](pipeline_revisao.md).

**Passo 1 — Categorizar erros da revisão:**

Parsear o arquivo de revisão (`revisao/{slug}-rev.md`) e classificar cada correção numa categoria:

| Categoria | Exemplo | Validação automática |
|-----------|---------|---------------------|
| `SWAP_PT_EN` | abstract PT preenchido com texto EN | `langdetect(abstract)` ≠ locale |
| `KW_EN_NO_ABSTRACT` | keywords_en sem abstract_en | campo cruzado |
| `ABSTRACT_GARBAGE` | abstract é trecho do corpo | comparar com fontes/ |
| `ABSTRACT_NOT_EXTRACTED` | abstract existe no PDF mas não foi extraído | padrão ≥70% + campo vazio |
| `TITLE_IN_ABSTRACT` | título repetido no início do abstract | comparação de strings |
| `TRUNCATED` | abstract termina sem pontuação | regex fim de frase |
| `KW_LEAKED` | keywords vazaram para o abstract | regex marcadores |
| `CONTROL_CHARS` | caracteres de controle no texto | regex [\x00-\x1f] |
| `EN_IS_PT` | abstract_en está em português | langdetect |

**Passo 2 — Rodar validação automática:**

```bash
# Verificar problemas residuais no seminário atual
python3 scripts/validar_abstracts.py --slug {slug} --summary

# Verificar todos os seminários (visão geral)
python3 scripts/validar_abstracts.py --summary
```

**Passo 3 — Salvar aprendizado estruturado:**

Arquivo: `revisao/{slug}-aprendizado-revisao.json`

```json
{
  "erros_sistematicos": [
    {
      "categoria": "SWAP_PT_EN",
      "quantidade": 14,
      "causa_raiz": "extrator confundiu idioma quando abstract vem depois de seção EN",
      "validacao_adicionada": "langdetect no abstract vs locale do artigo"
    }
  ],
  "regras_capitalizacao": [
    {
      "expressao": "Praça [nome]",
      "regra": "maiúscula como logradouro",
      "adicionado_ao_dict": true
    }
  ],
  "padroes_confirmados": [
    "'Arquitetura Moderna' sempre maiúscula como conceito",
    "'arquitetura moderna de [cidade]' descritiva → minúscula"
  ]
}
```

**Passo 4 — Atualizar validações para próximos seminários:**

Se uma categoria apareceu em ≥3 artigos e **não** é coberta pelo script `validar_abstracts.py`, adicionar a regra ao script. O objetivo é que cada revisão humana gere pelo menos uma melhoria no pipeline automático.

### 5.5 Atualizar status

- Adicionar seminário à tabela de revisados em `CLAUDE.md`, neste documento e no `pipeline_revisao.md`
- Atualizar memória do projeto (`MEMORY.md`) com padrões confirmados

### 5.6 Dump, commit e push

```bash
python3 scripts/dump_anais_db.py
git add anais.sql CLAUDE.md
git commit -m "Revisão {slug}: N títulos, N refs, N resumos corrigidos"
git push
```
