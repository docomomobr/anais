# Devlog — Redesenho do HTML de revisão

**Data**: 2026-02-24

## Contexto

O script `scripts/gerar_revisao_html.py` gera uma página HTML self-contained para revisão humana dos metadados de cada seminário. A versão anterior mostrava uma lista plana de artigos com campos de dados, mas sem informações do seminário (capa, ficha catalográfica, organizadores) e sem agrupamento por seção.

## Mudanças

### Cabeçalho do seminário (novo)
- Layout flex: capa à esquerda (embed base64, 220px), metadados à direita
- Mostra: título, subtítulo, local, editora, ISBN, organizadores, contagem de artigos/seções
- Placeholder cinza "sem capa" quando não há imagem
- Badge do PDF da edição quando disponível

### Ficha catalográfica (novo)
- Carregada de `revisao/fichas_catalograficas.yaml` (reutiliza `load_fichas()` do db2hugo.py)
- URLs na ficha são clicáveis (linkify automático)

### Sumário agrupado por seção (novo)
- TOC com headings de seção e contagem de artigos
- Cada item: ID + título + autores compactos + indicador PDF (verde/cinza)

### Artigos por seção (novo)
- Headings de seção com fundo colorido
- Sufixo de slug removido dos nomes de seção (ex: " — sdnne08")

### Campos EN (novo)
- Title EN / Subtitle EN mostrados quando existem
- Abstract EN com borda azul (distinta do resumo PT)
- Keywords EN mostrados quando existem

### Outros
- Locale tag (badge) quando diferente de pt-BR
- PDF badge verde/cinza no divider de cada artigo
- Mapeamento `sdpr` adicionado ao `COVER_DIRS`
- Suporte a print (page-break por artigo)

### Preservados do formato anterior
- Georgia serif, 900px max-width
- Labels small caps, campos faltantes em vermelho itálico
- Author pills com afiliação e ORCID
- Referências em lista numerada

## Arquivos modificados
- `scripts/gerar_revisao_html.py` — reescrito (163 → ~310 linhas)
- `revisao/fichas_catalograficas.yaml` — adicionado link repositório UFBA ao sdbr01
- `CLAUDE.md` — adicionado script à tabela de scripts principais

### Saída para pasta revisao/ (2026-02-25)
- Output padrão alterado de `/tmp/` para `revisao/revisao-{slug}.html`

## Uso
```bash
python3 scripts/gerar_revisao_html.py sdbr03
# → revisao/revisao-sdbr03.html
```
