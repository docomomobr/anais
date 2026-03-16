# Auditoria de Cobertura de Metadados — 2026-03-16

Auditoria da completude dos metadados no anais.db para publicacao academica.

---

## Contagem geral

| Metrica | Contagem |
|---------|----------|
| Total de artigos | 2.679 |
| Total de seminarios | 45 |
| Autores unicos | 2.481 |
| Tipo artigo | 2.532 |
| Tipo resumo | 124 |
| Tipo mesa | 23 |
| Autores duplicados | 0 (limpo) |
| Artigos sem autores | 0 (limpo) |

---

## Cobertura por campo — Seminarios Nacionais (sdbr01-sdbr15)

| Slug | Tot | Abstr | Abs EN | Abs ES | Keyw | KW EN | KW ES | Refs | Pages | Secao | Tit EN | Tit ES |
|------|-----|-------|--------|--------|------|-------|-------|------|-------|-------|--------|--------|
| sdbr01 | 6 | 0% | 0% | 0% | 0% | 0% | 0% | 83% | 100% | 100% | 0% | 0% |
| sdbr02 | 22 | 73% | 0% | 0% | 0% | 0% | 0% | 86% | 100% | 0% | 0% | 0% |
| sdbr03 | 56 | 79% | 2% | 0% | 0% | 0% | 0% | 96% | 98% | 0% | 0% | 0% |
| sdbr04 | 79 | 100% | 0% | 0% | 0% | 0% | 0% | 0% | 100% | 100% | 0% | 0% |
| sdbr05 | 56 | 100% | 98% | 0% | 82% | 79% | 0% | 100% | 0% | 100% | 0% | 0% |
| sdbr06 | 64 | 94% | 94% | 2% | 84% | 36% | 0% | 97% | 0% | 0% | 3% | 0% |
| sdbr07 | 62 | 98% | 90% | 2% | 89% | 77% | 2% | 95% | 0% | 0% | 0% | 0% |
| sdbr08 | 188 | 95% | 56% | 1% | 94% | 54% | 1% | 96% | 98% | 100% | 16% | 0% |
| sdbr09 | 170 | 86% | 79% | 2% | 86% | 70% | 1% | 84% | 98% | 100% | 1% | 0% |
| sdbr10 | 118 | 98% | 97% | 3% | 95% | 97% | 11% | 96% | 100% | 85% | 3% | 0% |
| sdbr11 | 101 | 97% | 98% | 1% | 99% | 97% | 1% | 98% | 100% | 100% | 0% | 0% |
| sdbr12 | 82 | 100% | 95% | 5% | 100% | 95% | 5% | 100% | 0% | 100% | 0% | 0% |
| sdbr13 | 181 | 99% | 95% | 3% | 96% | 94% | 2% | 98% | 100% | 100% | 1% | 0% |
| sdbr14 | 122 | 100% | 4% | 0% | 99% | 3% | 0% | 98% | 100% | 100% | 0% | 0% |
| sdbr15 | 101 | 98% | 98% | 98% | 99% | 98% | 96% | 99% | 100% | 100% | 97% | 98% |

### Agregados nacionais (1.408 artigos)

| Campo | Cobertura |
|-------|-----------|
| Abstract PT | 95,0% |
| Abstract EN | 69,7% |
| Keywords PT | 82,8% |
| Keywords EN | 63,8% |
| Referencias | 90,1% |
| Secoes | 84,2% |
| ORCID (media) | ~65% |
| Afiliacao | ~6% |

---

## Cobertura — Seminarios Regionais (30 seminarios, 1.271 artigos)

| Campo | Cobertura |
|-------|-----------|
| Abstract PT | 93,4% |
| Abstract EN | 57,3% |
| Keywords PT | 80,3% |
| Keywords EN | 48,3% |
| Referencias | 88,1% |
| Secoes | 100% |
| ORCID (media) | ~60% |
| Afiliacao | ~38% |

---

## ORCID — Nacionais

| Slug | Autores | Com ORCID | % |
|------|---------|-----------|---|
| sdbr01 | 6 | 5 | 83% |
| sdbr02 | 25 | 19 | 76% |
| sdbr03 | 87 | 49 | 56% |
| sdbr04 | 94 | 63 | 67% |
| sdbr05 | 85 | 54 | 64% |
| sdbr06 | 82 | 54 | 66% |
| sdbr07 | 95 | 61 | 64% |
| sdbr08 | 265 | 163 | 62% |
| sdbr09 | 236 | 148 | 63% |
| sdbr10 | 164 | 106 | 65% |
| sdbr11 | 142 | 93 | 65% |
| sdbr12 | 115 | 80 | 70% |
| sdbr13 | 293 | 187 | 64% |
| sdbr14 | 198 | 146 | 74% |
| sdbr15 | 178 | 119 | 67% |

---

## Gaps criticos para descobrimento academico

### Prioridade 1 — Alto impacto, grande volume

1. **sdbr01-04 keywords: 0%** — 163 artigos sem nenhuma keyword. Essenciais para indexacao e busca por assunto.
2. **sdbr14 abstract_en: 4%** — 117 de 122 artigos sem abstract EN. Limita muito a descoberta internacional.
3. **sdbr01 abstract: 0%** — 6 artigos sem nenhum resumo (unico seminario nacional nesta situacao).
4. **Afiliacao nacional: ~6%** — So sdbr02 e sdbr04 tem dados significativos. Importante para bibliometria institucional.

### Prioridade 2 — Impacto moderado

5. **sdbr04 referencias: 0%** — 79 artigos. Sao resumos, entao esperado.
6. **Regionais abstract_en: 8 seminarios a 0%** — ~250 artigos sem abstract EN.
7. **sdbr02/sdbr06 secoes: 0%** — 86 artigos sem eixo tematico.
8. **sdbr05-07, sdbr12 pages: 0%** — Sem numeracao de paginas.

### Prioridade 3 — Desejavel

9. **title_en/title_es** — So sdbr15 tem cobertura (97-98%). Todos os outros a 0-16%.
10. **abstract_es/keywords_es** — Minimo exceto sdbr15 e sdnne10.
11. **volume_pdf** — So 3 de 15 nacionais tem.

---

## Qualidade dos dados

- **0 artigos sem autores** — limpo
- **0 autores duplicados** — deduplicacao completa
- **51 artigos com locale nao-pt-BR** — correto (artigos em ES/EN em edicoes com tematica internacional)
- **6 artigos sdbr08 com abstract vazio** — provavelmente tem abstract em campo ES (locale=es)

---

## Comparacao Nacional vs Regional

| Campo | Nacional | Regional | Observacao |
|-------|----------|----------|------------|
| Abstract PT | 95% | 93% | Similar |
| Abstract EN | 70% | 57% | Nacional melhor |
| Keywords PT | 83% | 80% | Similar |
| Keywords EN | 64% | 48% | Nacional melhor |
| Secoes | 84% | 100% | Regional completo |
| ORCID | 65% | 60% | Similar |
| Afiliacao | 6% | 38% | **Regional muito melhor** |

---

## Recomendacoes (ordem de prioridade)

1. Extrair keywords para sdbr01-04 (163 artigos) — provavelmente existem nos PDFs/DOCX originais
2. Extrair abstract_en para sdbr14 (117 artigos) — maior impacto em cobertura EN
3. Extrair abstracts para sdbr01 (6 artigos) — lote pequeno, 100% de impacto
4. Backfill afiliacoes nos nacionais — gap sistemico, dados existem nos originais
5. Atribuir secoes para sdbr02 e sdbr06 (86 artigos) — dados nos programas dos eventos
6. Sweep regional abstract_en/keywords_en para os 8 seminarios a 0% (~250 artigos)
