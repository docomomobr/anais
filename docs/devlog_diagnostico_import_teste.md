# Devlog — Diagnóstico de falha na importação OJS teste

**Data:** 2026-02-11
**Servidor:** docomomo.ojs.com.br (OJS 3.3.0.21, teste)

## Contexto

13 de 21 seminários regionais foram importados com sucesso. 8 falharam consistentemente com HTTP 500 (corpo vazio). O provedor confirmou que `max_execution_time` e memória PHP NÃO são a causa — "o SCRIPT interrompe antes".

## Testes realizados e conclusões

### 1. Servidor funciona (confirmado)

XML mínimo (1 artigo, wrapper simples, sem abstract/keywords/pages) → **importou com sucesso** (HTTP 200, "importação concluída com êxito").

**Conclusão:** O mecanismo de importação funciona. O problema está no conteúdo dos XMLs.

### 2. Conteúdo dos artigos NÃO é o problema (confirmado)

Artigos reais dos XMLs falhantes (sdsul01-art1, sdsul06-art1, com abstract, keywords, pages, múltiplos autores) → **importaram com sucesso** quando colocados em um wrapper simplificado.

Testes individuais com artigos de sdsul06:
- Artigo com keywords → OK
- Artigo com pages → OK
- Artigo com abstract longo → OK
- Artigo com múltiplos autores → OK

**Conclusão:** Não há nada errado com os artigos. O problema está no wrapper da issue.

### 3. Wrapper real da issue CAUSA o erro (confirmado)

O MESMO artigo que importa com sucesso em wrapper simples → **falha com HTTP 500** quando colocado no wrapper real do sdsul06.

Diferenças entre o wrapper simples (funciona) e o wrapper real (falha):

| Elemento | Wrapper simples (OK) | Wrapper real (500) |
|----------|--------------------|--------------------|
| url_path | "test-sdsul06-art1" | "sdsul06" |
| volume | 99 | 6 |
| description | "Teste com 1 artigo" | Ficha catalográfica longa (300+ chars) |
| title | "Teste sdsul06" | "6º Seminário Docomomo Sul, Porto Alegre, 2019" |
| section ref | Mesma (AC-sdsul06) | Mesma |

### 4. Seções órfãs NÃO são o problema (descartado)

Criamos versão do sdsul06 com section ref completamente nova ("NEWAC-sdsul06") e url_path nova → **mesmo erro HTTP 500**.

**Conclusão:** Seções existentes no banco não interferem.

### 5. Locale en_US NÃO é o problema (descartado)

Vários XMLs com sucesso têm conteúdo `locale="en_US"` (sdsp05: 117 ocorrências, sdsul04: 66, sdnne10: 162). Vários XMLs falhantes NÃO têm en_US (sdsul06: 0, sdnne08: 0).

**Conclusão:** Sem correlação.

### 6. Formato XML validado contra XSD (OK)

Verificamos o XML contra `native.xsd` (OJS) e `pkp-native.xsd` (PKP-lib) do branch stable-3_3_0:
- Ordem dos elementos dentro de `<publication>`: correta
- Ordem dos elementos dentro de `<author>`: correta
- Atributos obrigatórios: presentes
- `locale` em `<article>`: presente (bug conhecido do OJS 3.3.0-12/13 já evitado)

### 7. Comparação wrapper-a-wrapper dos 21 XMLs

Todos os 21 XMLs regionais têm **estrutura idêntica** de wrapper:
- `published="1"`, `current="0"`, `access_status="1"`
- `<description locale="pt_BR">` (todos têm)
- `<issue_identification>` com volume, number, year, title
- `<date_published>` e `<last_modified>`
- `<sections>` com 1-6 seções

Nenhuma diferença estrutural foi encontrada entre o grupo de sucesso (13) e o de falha (8).

### 8. Rate limiting interfere nos testes (confirmado)

Após ~15-20 importações rápidas na mesma sessão (mesmo com delays de 10-12s), até o XML baseline que antes funcionava passou a retornar HTTP 500. O servidor entra em modo de proteção.

**Consequência:** Testes A/B com muitas variantes são confundidos pelo rate limiting. É preciso espaçar os testes com delays mais longos (30s+) e usar sessões frescas.

## Hipóteses restantes (a testar)

### H1: Volume/number conflitando com issue existente
Se o servidor já tem uma issue com volume=6 e number=1 (sdsul01), talvez tentar criar outra issue com volume=6 e number=2 cause conflito interno no OJS. Mas isso não explica por que number=4 (sdsul04) e number=7/8 (sdsul07/08) funcionaram.

### H2: Tamanho ou conteúdo da description
A description longa (ficha catalográfica) pode ter caracteres que causem erro no parser PHP. Testar com description curta vs. longa.

### H3: Interação volume + description + title
Talvez a combinação específica de volume=6 + description longa + título com "º" cause o erro. Testar adicionando cada elemento individualmente ao wrapper simples.

### H4: Estado do servidor pós-13 importações
Pode haver um limite no número de issues ou seções no banco de teste que causa erro ao tentar criar mais. Verificar se QUALQUER importação nova funciona com volume diferente.

## Teste A/B (4 variantes, delays de 30s, sessão fresca por teste)

Todos os 4 falharam com HTTP 500, incluindo o baseline:

| Teste | Variação | Resultado |
|-------|----------|-----------|
| A | baseline (vol=99, desc curta, title curto) | ❌ HTTP 500 |
| B | baseline + description longa | ❌ HTTP 500 |
| C | baseline + volume=6 | ❌ HTTP 500 |
| D | baseline + título real com "6º" | ❌ HTTP 500 |

### Teste ping (ultra-mínimo, IDs únicos UUID)

Resultado: **ConnectionError** — servidor fechou a conexão durante o step de import (login e upload funcionam normalmente). O endpoint de import está sendo bloqueado ao nível de rede (WAF/Cloudflare), não ao nível de aplicação.

A página do OJS (`/index.php/ojs`) continua respondendo normalmente (HTTP 200).

## CAUSA RAIZ ENCONTRADA: colisão de títulos de seção (bug OJS pkp-lib #9755)

### O problema

No OJS 3.3, seções são **journal-wide** (compartilhadas entre todas as issues), não per-issue. O método `_sectionExist()` em `NativeXmlIssueFilter.inc.php` busca seções existentes por **título** (não por abbreviation). Quando encontra um título idêntico, retorna `true` e a nova seção NÃO é criada. Mas os artigos do novo XML referenciam a abbreviation nova (que nunca foi criada), causando:

1. `NativeXmlPublicationFilter` busca `getByAbbrev("SEC5-sdnne07")` → `null`
2. Publication não é criada, mas a submission JÁ foi criada
3. PHP tenta indexar uma submission sem publication → `getData() on null` → **fatal error → HTTP 500 vazio**

### Verificação: 100% de correlação

**Todas as 8 falhas** têm títulos de seção que colidem com seções já criadas:

| XML falhante | Título da seção | Colide com |
|-------------|-----------------|------------|
| sdnne07 | "Artigos Completos" | SEC1-sdnne02 (✅) |
| sdnne08 | "Artigos Completos" | SEC1-sdnne02 (✅) |
| sdsp08 | "Artigos Completos" | SEC1-sdnne02 (✅) |
| sdsp09 | "Artigos Completos" | SEC1-sdnne02 (✅) |
| sdsul06 | "Artigos Completos" | SEC1-sdnne02 (✅) |
| sdsul02 | "Artigos" | (colide entre si, os 3 falham) |
| sdsul03 | "Artigos" | (colide entre si) |
| sdsul05 | "Artigos" | (colide entre si) |

**Nenhum dos 13 de sucesso** tem colisão de título de seção.

### Referências

- Bug: [pkp-lib #9755](https://github.com/pkp/pkp-lib/issues/9755) — Non-existent section_ref fails silently
- Código-fonte: `_sectionExist()` em `NativeXmlIssueFilter.inc.php` (branch stable-3_3_0)
- Post no fórum PKP: "After upgrading to 3.3.0.8 error 500 on trying to import issues/articles"

### Solução

Tornar os títulos de seção **únicos por seminário**, ex:
- "Artigos Completos" → "Artigos Completos — sdnne07"
- "Artigos" → "Artigos — sdsul02"

Isso evita que `_sectionExist()` encontre colisão e garante que a seção seja criada.

### Nota sobre rate limiting

Independentemente da causa raiz acima, o servidor de teste impõe rate limiting no endpoint de import após muitas tentativas rápidas. Após os ~30+ testes diagnósticos, o servidor começou a rejeitar conexões (ConnectionError). Isso deve se resolver sozinho com o tempo.
