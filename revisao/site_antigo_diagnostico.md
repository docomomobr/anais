# Diagnóstico — Site antigo vs banco

Fonte: https://docomomobrasil.com/old/ (antigo docomomo.org.br)
HTMLs salvos em: revisao/site_antigo/
Data: 2026-03-19

## Resumo comparativo

| Seminário | Site antigo | DB | Faltam reais | Notas |
|-----------|-------------|-----|-------------|-------|
| sdbr03 | 60 | 58 | **3** | PDFs 404 na Wayback |
| sdbr04 | (não digital.) | 79 | — | Sessoes.htm tem 195KB, verificar |
| sdbr05 | 56 | 61 | **0** | Todos casam (títulos abreviados no DB). 5 extras = mesas |
| sdbr06 | 79 | 64 | **13** | 2 eram falsos positivos (027 El-Jaick, 007 Guarino Lopes). PDFs 404 na Wayback |
| sdbr07 | 74 (PROPAR) | 74 | **0** | Renumerado, 5 inseridos, 10 mesas atribuídas |
| sdbr08 | 189 | 188 | **7** | Temos DVD. Não buscar online |
| sdbr09 | 172 | 170 | **4** | Temos DVD. Não buscar online |
| sdbr10 | (sem página) | 118 | — | — |

Nota: matching refinado em 2 passadas. sdbr05 confirmado: 0 faltantes reais (títulos abreviados no DB casam com completos no site). sdbr08/09 têm DVD como fonte — não buscar online.

## sdbr07 — Concluído

Renumerado conforme PROPAR (ver revisao/sdbr07-rev.md).
5 artigos faltantes: PDFs baixados, fontes_plumber extraídos. Inserção pendente.

## sdbr03 — Sessões e programação completa!

A página sessoes.htm tem o programa completo do seminário (8-11/dez/1999):
- Tema A: Os Conceitos do Movimento Moderno (subtemas A1, A2, A3)
- Tema B: Práticas da Preservação e Intervenção (subtemas B1-B5)
- Sessão Especial (bens em risco)
- Sessão Memória (Lucio Costa, Abrahão Sanovicz, Álvaro Vital Brazil, Bratke)
- Conferências: Maristella Casciato, Jean-Paul Midant, Wessel de Jonge, Hélio Piñon

Programação dia a dia com sessões A/B/C paralelas, coordenadores, autores e afiliações.
Isso permite atribuir cada artigo à sua sessão temática (A, B ou C) e ao subtema.

A página trabalhos.htm lista artigos em ordem ALFABÉTICA (não por sessão).
Os artigos no site antigo têm códigos de subtema nas URLs (subtema_A1F, etc.).

3 artigos faltam no DB:
- A paixão do início na Arquitetura de Paulo Mendes da Rocha
- Porque Lúcio Costa usa a Pequena Casa do Colono na sua Construção Teórica
- Rumo ao Moderno: Uma Historiografia da Arquitetura Moderna em São Paulo até 1945

## sdbr04 — Site antigo não tinha artigos

Mensagem: "Ainda não foram digitalizados os trabalhos do 4º seminário."
Porém a página sessoes.htm tem 195KB — pode conter a programação com os títulos.

## sdbr05 — Divergência grande (9 faltam, 14 sobram)

Provavelmente muitos falsos negativos no matching (títulos abreviados no site vs completos no DB).
14 "sobrando" no DB inclui as 5 mesas temáticas inseridas recentemente.

## sdbr06 — 17 artigos faltam no DB!

Maior lacuna. 79 no site antigo vs 64 no DB = 15 artigos a mais no site.
2 "sobrando" no DB são provavelmente matches ruins (títulos levemente diferentes).

## sdbr08 — 7 faltam, 6 sobram

Diferença pequena. Pode ser problema de matching (títulos em CAPS no site vs normalizados no DB).

## sdbr09 — 4 faltam, 2 sobram

Diferença pequena. Inclui mesas e artigos de apresentação que podem não estar no DB.

## HTMLs salvos

revisao/site_antigo/{slug}_{pagina}.htm para sdbr03-sdbr09:
- trabalhos.htm — lista de artigos (alfabética)
- sessoes.htm — sessões/eixos temáticos e programação
- apresentacao.htm — apresentação do seminário
- autores.htm — lista de autores

## Concluídos (2026-03-19)

- sdbr03: 6 sessões criadas e atribuídas (58/58 artigos). 3 artigos faltantes sem PDF
- sdbr06: 4 sessões criadas e atribuídas (64/64 artigos). 13 artigos faltantes sem PDF
- sdbr07: renumerado (PROPAR), 5 artigos inseridos, 10 mesas atribuídas (74/74 artigos)

## Pendências

### sdbr02 — sessões (contatar Huapaya/UFBA)

24 artigos sem sessão. Os 3 eixos são conhecidos:
1. Arquitetura, espaço público e projeto social
2. Arte e técnica: possibilidades de novas formulações no campo da arquitetura e do urbanismo
3. Intervenções contemporâneas na arquitetura e no urbanismo modernos

Mesas: I-A(3), I-B(4), I-C(4), II-A(4), II-B(3), III-A(4), III-B(5), Grupos de Pesquisa(4), Painéis(6), Conferências(3).
O mapeamento artigo→mesa está no arquivo físico do Lab20/UFBA.
Contatar Prof. José Carlos Huapaya Espinoza (coordenador Lab20) para obter a planilha Excel
que a equipe de digitalização (Caio Anderson, Gabriela Otremba) criou a partir da programação original.
Pista parcial: sdbr02-005 (Sílvia Wolff) menciona no abstract "grupo 3 relativo à preservação" → eixo III.

### sdbr10 — 18 artigos sem sessão

Verificar fonte para os 18 artigos sem section_id.

### sdbr04 — sessoes.htm (195KB)

Verificar se contém a lista de trabalhos (a página trabalhos.htm diz "não digitalizados").

### sdbr08/sdbr09 — artigos faltantes (DVD)

7 e 4 artigos faltantes respectivamente. Verificar nos DVDs disponíveis.
