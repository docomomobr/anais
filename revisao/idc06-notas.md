# idc06 — Notas de revisão

## OCR e spillover em proceedings escaneados

Em proceedings escaneados (OCR, layout 2 colunas), o plumber produz artefatos:

1. **Spillover de keywords**: KEYWORDS na página 1 de artigos multi-página pertencem ao artigo ANTERIOR (texto do final que sangrou no scan). Detectar via y < 200 na p1.

2. **Interleaving de refs**: Texto de 2 colunas fica intercalado, gerando refs garbled (corpo do texto + legendas + referências misturados).

3. **Refs de artigo errado**: Bibliografia de um artigo pode ser atribuída ao seguinte/anterior.

### Procedimento para OCR ruins

- Mapear marcadores (BIBLIOGRAPHY, KEYWORDS, NOTES) via plumber ANTES de abrir imagens
- Usar `page` e `y` do plumber para identificar spillovers (p1, y<200)
- Gerar imagens apenas das páginas mapeadas (`pdftoppm -png -r 200 -f P -l P`)
- Confrontar refs no banco com imagem — plumber insuficiente para refs

## Particularidades de conferências internacionais

- **locale=en**: campos primários em inglês. Scripts PT (normalizar_maiusculas.py) não se aplicam.
- **Países**: default country='BR' incorreto para maioria. Corrigir via bios dos autores.
- **~40% sem refs/kw formais**: artigos curtos, session reports, citações inline.
- **Session pages**: fotos de participantes, sem conteúdo acadêmico → sem kw/refs esperados.

## Correções aplicadas (resumo)

| Artigo | Problema | Correção |
|--------|----------|----------|
| 005 | 5 refs garbled | 3 refs limpas |
| 006/007 | Títulos trocados | Corrigidos |
| 011 | Hanna → Hannah Lewi | Nome corrigido |
| 014 | 23 refs = duplicata do 013 | 1 ref real |
| 016 | 13 refs garbled | 21 refs limpas da imagem p.82 |
| 017 | 61 refs do artigo errado (016) | 3 notas reais |
| 021 | 21 refs garbled | 32 refs limpas |
| 023 | 18 refs | 19 (1 faltante + correções OCR) |
| 035 | Mazza-Dourado | Mazza Dourado (sem hífen) |
| 039 | Brändle | Brendle |
| 045 | Mariëka | Marieke Kuipers |
| 048 | sem refs | 10 refs da imagem |
| 050 | Reconsidering | Revisiting Chandigarh |
| 42 autores | country=BR | 19 países corrigidos |

## Cobertura final

- 54 artigos, 13 seções, 24 subtítulos
- 35/54 keywords (65%), 26/54 refs (48%)
- 58 autores, 18 ORCIDs, 19 países
- 8 A11 (refs longas) restantes para revisão humana
