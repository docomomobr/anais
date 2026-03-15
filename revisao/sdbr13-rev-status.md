# Revisão automática — sdbr13 (181 artigos)

Data: 2026-03-15

## Cobertura final
| Campo | Inicial | Final |
|-------|---------|-------|
| abstract | 172 (95%) | **181 (100%)** |
| abstract_en | 170 (93%) | 172 (95%) |
| keywords | 172 (95%) | 174 (96%) |
| keywords_en | 165 (91%) | 171 (94%) |
| references | 172 (95%) | 177 (97%) |
| seções | 0 (0%) | **181 (100%)** |
| total refs | ~4170 | 4179 |

## Validação final: 2 issues genuínos
- A01 sdbr13-040: keywords_en ausente — autor deixou template de instrução no PDF (confirmado visualmente)
- A11 sdbr13-090: ref de 508c — ref legítima única (capítulo em livro, editora Universidad de los Andes longa)

---

## Fase 0 — Diagnóstico e preenchimento

### 0.1 Padrão de metadados ✅
- Locale: 181 pt-BR (100%), 1 corrigido para es (A15)
- Norma de citação: ABNT (80%)
- abstract_es/keywords_es: AUSENTE (<3%) — não buscar

### 0.2 Artigos fora do padrão ✅
- abstract: 9 faltantes
- abstract_en: 11 faltantes
- keywords: 9 faltantes
- keywords_en: 16 faltantes
- references: 9 faltantes

### 0.3 Reinspecionar PDFs ✅
- 3 PDFs escaneados sem OCR (176, 177, 179): 1 página, imagem pura, 0 chars
  - Abstracts lidos visualmente pelo agente LLM (176: AICA/1959, 177: Vitrúvio/Le Corbusier, 179: Esplanada de Santo Antônio)
  - Keywords e refs: genuinamente ilegíveis (texto muito pequeno nos posters)
- 3 resumos expandidos (178, 180, 181): 1 página com texto, sem seção "Resumo" formal
  - Abstracts extraídos do corpo do texto
  - Refs extraídas dos posters: 178 (16 refs), 180 (5 refs), 181 (17 refs)

### 0.3b Extrair fontes pdfplumber ✅
- 178/181 PDFs processados (3 escaneados falharam)
- Profile: corpo 11pt, abstract 9pt, notas ≤7.9pt, headings ≥11.5pt

### 0.4 Preencher lacunas ✅
- Abstracts inseridos: 038, 143 (ES), 156 (ES), 176, 177, 178, 179, 180, 181 → abstract 100%
- Abstract_en inseridos: 038, 143
- Keywords inseridos: 024 (format fix), 143 (ES), 156 (ES)
- Keywords_en inseridos: 023, 035, 048, 120, 134, 164, 167
- Refs inseridos: 024 (29), 038 (22), 143 (11), 156 (39), 178 (16), 180 (5)

### 0.5 Verificar abstracts existentes ✅
- 11 overflows corrigidos:
  - abstract_en: 016 (45107→748c), 017 (35934→1134c), 023 (42057→1486c), 035 (49423→1329c), 156 (37014→911c), 167 (41819→1263c)
  - abstract: 071 (27688→1304c)
  - abstract_es: 123 (33099→NULL), 132 (36333→NULL) — corpo inteiro no campo
- 3 keywords vazadas cortadas: 120, 164, 167 (Key words:/Keywords: no final do abstract_en)
- 1 PT/EN separado: 163 (abstract_en continha PT colado a partir de pos 765)
- 1 abstract_en com ponto adicionado: 080 (texto completo, só faltava ".")
- 2 abstracts re-extraídos por truncamento: 144 (1438→2016c), 151 PT (252→810c) + EN (285→840c)
- 167 abstract_en: re-digitado do PDF (1219c, terminava com "exterior space." não "nature")

### 0.6 Extrair metadados EN ✅
- Coberto pela extração de keywords_en na etapa 0.4

---

## Fase 1 — Revisão automática

### 1.1a Títulos e subtítulos PT ✅
- normalizar_maiusculas.py: 40 artigos alterados
- Revisão LLM (agente): 84 artigos corrigidos, 93 correções
  - Genéricos rebaixados (Obra→obra, Mar→mar, etc.): 18
  - Nomes de edifícios/monumentos capitalizados: 16
  - Instituições capitalizadas: 10
  - Lugares capitalizados: 8
  - "Intervenção" rebaixado: 6
  - Travessões corrigidos (` - ` → ` — `): 6
  - Subtítulos com lowercase no início: 5
  - Fixes críticos: sdbr13-051 título truncado ("Século XIX" → "A morfologia urbana e o edifício hospitalar no século XIX"), sdbr13-169 título era nome do eixo → "As 'outras' do 'outro'"
- Aprendizado salvo em: revisao/sdbr13-titulos-aprendizado.json

### 1.1b/c Títulos EN ⏳
- Não executado nesta sessão (pendente)

### 1.2a clean_references.py ✅
- 6 backfills ABNT resolvidos

### 1.2b sweep_refs ✅
- 91 artigos alterados
- 26 lixo grosso removido, 76 fragmentos juntados, 16 endnotes removidas
- 17 refs splitadas, 6 não-refs removidas, 3 body text truncado, 8 duplicatas
- check_references: 0.1% problemas (3/4179)

### 1.2c Revisão LLM refs ✅
- 36 backfills resolvidos (15 artigos): `______` → autor da ref anterior
- 5 refs longas corrigidas:
  - 014: removido "ACERVOS CONSULTADOS" (header de seção)
  - 039: notas numeradas cortadas do final (1309→152c)
  - 066: URLs órfãs removidas do final
  - 067: lista de URLs "Reportagens" removida (não é ref bibliográfica)
  - 087: ref de 3040c splitada em 13 partes
  - 090: 2 refs concatenadas separadas (O'Byrne Orozco)
  - 111: URL longa trimada
  - 150: path local `file:///C:/` removido
  - 174: 7 processos IPHAN concatenados separados
- 1 nota removida, 1 duplicata removida

### 1.3 Keywords ✅
- Limpeza automática (clean-keywords):
  - sdbr13-024: formato texto→JSON
  - sdbr13-040: keywords_en inteiramente template → NULL
  - sdbr13-036, 050, 075: lixo de título/body removido
  - sdbr13-057: keyword "Passo Fundo / RS-Brasil" preservada (não splitar em /)
  - sdbr13-128: keywords_en splitadas por vírgula
- **Re-extração de 31 keywords_en sujas** (títulos infiltrados, template text, body text, ALL CAPS):
  - Todas re-extraídas dos PDFs com pdfplumber
  - Zero-width spaces removidos (003, 103)
  - Template "(título em negrito e itálico):" limpo (169)
  - Path local file:/// limpo (150)
  - Keyword truncada completada (147: 3 keywords longas legítimas)
- 5 keywords PT com template "(título em negrito):" limpas (027, 060, 091, 146, 160)

### 1.5 Loop validate ✅
- Auto-fixes aplicados: locale mismatch (A15), control chars (A16), refs duplicadas (A17), keywords coladas (A25)
- Convergiu para 2 issues genuínos (A01, A11)

### 1.6 Auditoria final ✅
- **1.6a Cobertura**: abstract 100%, seções 100%, demais >94%
- **1.6b Metadados seminário**:
  - publisher: PPGAU/FAUFBA
  - location: Salvador
  - date_published: 2019-10-07
  - ISBN: 978-85-66843-06-4
  - editors: José Carlos Huapaya Espinoza
  - description: ficha catalográfica ABNT gerada
- **1.6c Seções**: 5 eixos criados, 181/181 artigos mapeados
  - Mesa Redonda: 28
  - Eixo 1 — História e Historiografia: 51
  - Eixo 2 — Inventário e Documentação: 26
  - Eixo 3 — O Modernismo como Cultura: 44
  - Eixo 4 — Teorias e Práticas de Intervenção: 32
  - Fonte: HTML do site inscricoes13docomomobrasil.ufba.br + cabeçalhos dos PDFs

---

## Fase 2 — HTML de revisão ✅
- revisao/revisao-sdbr13.html (181 artigos, 5 seções)

---

## Correções nos scripts (retroalimentação)

### fix_validation_issues.py — clean_keywords
- TEMPLATE_GARBAGE_RE expandido: `título em negrito`, `alinhamento`, `entre linhas`
- KW_JUNK_RE novo: detecta body text (Introdução, Figure, Fonte:, http, citações)
- Newlines: keyword com `\n` → mantém só texto antes da primeira quebra
- ALL CAPS: blocos ≥15 chars em ALL CAPS removidos (preserva siglas curtas)
- Keywords >80 chars: removidas como body text
- Zero-width spaces: limpeza automática (`\u200b`, `\ufeff`)
- Template prefix: extrai keyword válida após `):` em vez de remover tudo

### validate_metadata.py — A25 (keywords no abstract)
- Guard contra falso positivo: se "palavras-chave" ou "key words" aparece no meio de frase narrativa (precedido por palavra em minúscula), não corta
- Contexto expandido para 40+5 chars para capturar mais variações
- Evita truncar abstracts onde o autor menciona "palavras-chave" no corpo do texto

### validate_metadata.py — A26 (abstract em idioma errado)
- Novo check: detecta quando `abstract` (PT) contém texto em espanhol
- Heurística: conta marcadores ES vs PT; se ES > 2×PT e ES ≥ 5, é falso positivo
- Auto-fix: move abstract → abstract_es, seta abstract = NULL
- Detectou sdbr13-153 (além do 143 já corrigido manualmente)

### fix_validation_issues.py — is_fragment()
- Nota sobre padrão "SIGLA, Cidade, Ano": ambíguo (pode ser fragmento ou autor institucional). Deixar para revisão LLM.

### pipeline_revisao.md — Regras novas na Fase 0.4
- Verificar idioma antes de inserir abstract (ES no campo PT = erro)
- Extrair também abstract_es/keywords_es, não só EN
- Rodar sweep_refs DEPOIS de inserir refs extraídas na Fase 0

### pipeline_revisao.md — §1.1a prompt LLM títulos
- "Arquiteto/a" como genérico → minúscula (sdbr13-098)
- Nomes de coletivos/grupos artísticos são nomes próprios (sdbr13-081)
- Verificar split título/subtítulo contra PDF original; para escaneados, ler imagem (sdbr13-176, 038)

---

## Revisão humana — log de correções

| # | Artigo | Campo | Problema | Causa raiz | Fix no pipeline |
|---|--------|-------|----------|-----------|----------------|
| 1 | sdbr13-024 | references | 29 fragmentos, deviam ser 15 refs | Extração splitou no \n sem juntar continuações | Rodar sweep_refs após inserir refs na Fase 0.4 |
| 2 | sdbr13-098 | title | "Arquiteto" maiúscula indevida | LLM não rebaixou | Prompt LLM: "arquiteto/a" genérico |
| 3 | sdbr13-176 | title/subtitle | Split errado | PDF escaneado, LLM não leu imagem | Ler IMAGEM do PDF para escaneados |
| 4 | sdbr13-123 | abstract_es/keywords_es | Faltantes | Fase 0 só buscou EN, não ES | Buscar ES na Fase 0.3/0.4 |
| 5 | sdbr13-038 | title/subtitle | Split no ":" errado | LLM não comparou com PDF | Reforçar verificação de split no prompt |
| 6 | sdbr13-045/073 | keywords_en | Título infiltrado | clean_keywords não detectava ALL CAPS | Script corrigido (KW_JUNK_RE, ALL CAPS ≥15) |
| 7 | sdbr13-081 | subtitle | "grupo" deveria ser "Grupo" (nome próprio) | dict.db não tem "Grupo" contextual | Prompt LLM: coletivos artísticos = nome próprio |
| 8 | sdbr13-143 | abstract | Resumen (ES) no campo abstract (PT) | Extração inseriu sem verificar idioma | A26 novo + regra na Fase 0.4 |
| 9 | sdbr13-010 | references | GAMELEIRA splitada (ref+fragmento) | is_fragment() não pegou "UFRN, Natal, Fev 2019" | Caso ambíguo, documentado como nota |
| 10 | sdbr13-153 | abstract | Abstract em ES no campo PT | Mesmo que #8 | A26 auto-fix detectou e corrigiu |

---

## Dados genuinamente ausentes
- **abstract_en** (9): 071, 123, 132, 176, 177, 178, 179, 180, 181 — PDFs sem seção EN
- **keywords** (7): 071, 176, 177, 178, 179, 180, 181 — PDFs sem palavras-chave
- **keywords_en** (10): 040 (template), 048, 071, 123, 132, 176, 177, 178, 179, 180, 181
- **references** (4): 166 (sem refs no PDF), 176, 177, 179 (posters escaneados ilegíveis)
