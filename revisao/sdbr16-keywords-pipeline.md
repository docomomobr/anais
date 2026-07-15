# Pipeline temporário — Revisão de keywords sdbr16

Baseado nas etapas 1.3, 1.5, 1.6a e 1.10 do `pipeline_revisao.md`.

Estado atual: 323 artigos (288 artigos + 35 mesas).
- 266 com 3+ keywords
- 2 com 2 keywords (sdbr16-008, sdbr16-209)
- 0 com 1 keyword
- 55 sem keywords (35 mesas + 20 artigos)
- 0 com keywords_en (campo não preenchido no seminário)
- 12 com keywords_es
- 32 inconsistências de casing

Nenhum artigo tem docx disponível entre os 20 sem keywords — todos são excursistas ou conferências sem arquivo original.

---

## Etapa 1 — Limpeza automática (1.3)

```bash
python3 scripts/fix_validation_issues.py --slug sdbr16 --clean-keywords --dry-run
python3 scripts/fix_validation_issues.py --slug sdbr16 --clean-keywords
```

Pendente: 1 junk em sdbr16-202 (`"segunda-Geração" Moderna` — aspas curvas internas).

**DONE**: □

---

## Etapa 2 — Extração de keywords faltantes dos PDFs

Para os 20 artigos sem keywords (não-mesa) e os 2 com apenas 2:

| id | pdf | abs | ação |
|----|-----|-----|------|
| sdbr16-008 | — | sim | docx não existe; verificar no PDF (PRONTOS/) |
| sdbr16-019 | sim | não | sem abstract nem keywords — resumo expandido? verificar PDF |
| sdbr16-037 | sim | sim | verificar PDF |
| sdbr16-042 | — | sim | sem PDF; keywords no abstract? |
| sdbr16-054 | — | não | sem PDF, sem abstract — pendente organização |
| sdbr16-082 | — | sim | sem PDF; keywords no abstract? |
| sdbr16-103 | sim | sim | verificar PDF |
| sdbr16-117 | — | sim | sem PDF |
| sdbr16-126 | sim | sim | verificar PDF |
| sdbr16-172 | — | sim | sem PDF |
| sdbr16-173 | — | sim | sem PDF |
| sdbr16-174 | sim | sim | verificar PDF |
| sdbr16-179 | — | sim | sem PDF |
| sdbr16-193 | — | sim | sem PDF |
| sdbr16-196 | sim | sim | verificar PDF |
| sdbr16-201 | sim | não | sem abstract — pendente organização |
| sdbr16-209 | — | sim | docx não existe; somente 2 kw |
| sdbr16-220 | sim | sim | verificar PDF |
| sdbr16-229 | — | sim | sem PDF |
| sdbr16-245 | sim | sim | verificar PDF |
| sdbr16-256 | sim | sim | verificar PDF |
| sdbr16-272 | — | sim | sem PDF |

**Procedimento**: Para os que têm PDF, buscar "Palavras-chave" / "Keywords" / "Palabras clave" no plumber ou no PDF direto. Para os sem PDF, verificar se o abstract contém keywords embutidas.

**Regra R12**: NUNCA gerar ou inventar keywords. Se não há no documento, campo fica vazio.

**DONE**: □

---

## Etapa 3 — Mesas redondas (sdbr16-m01 a m35)

As 35 mesas redondas não têm docx/PDF com keywords. Verificar se alguma possui keywords embutidas no abstract. Se não, aceitar como genuinamente sem keywords (não é erro).

**DONE**: □

---

## Etapa 4 — Corrigir inconsistências de casing (J.2 + J.3)

32 inconsistências detectadas. Resolver cada uma escolhendo a forma canônica:

### Regras de capitalização (referência: `regras_dados.md`):

- **Expressões consolidadas** → Maiúscula: Arquitetura Moderna, Arquitetura Moderna Brasileira, Brutalismo, Modernismo, Modernidade, Patrimônio Cultural, Patrimônio Moderno, Patrimônio Industrial
- **"Arquitetura" como disciplina** → Maiúscula: Arquitetura, Urbanismo
- **"arquitetura" adjetivada** → minúscula: arquitetura escolar, arquitetura hospitalar, arquitetura contemporânea, arquitetura paulista, arquitetura moderna residencial
- **Nomes próprios** → Maiúscula: Le Corbusier, Lina Bo Bardi, Roberto Burle Marx, Lelé, São Paulo, Museu de Arte Moderna
- **Termos genéricos** → minúscula: conservação, preservação, fotografia, natureza, representação, urbanismo (quando genérico), modernidade (quando genérico)
- **Pré-fabricação** → minúscula (termo técnico genérico): pré-fabricação

### Formas canônicas a aplicar:

| keyword (lower) | forma canônica | justificativa |
|------------------|----------------|---------------|
| arquitetura | Arquitetura | disciplina |
| arquitetura contemporânea | arquitetura contemporânea | adjetivada |
| arquitetura escolar | arquitetura escolar | adjetivada |
| arquitetura hospitalar | arquitetura hospitalar | adjetivada |
| arquitetura moderna | Arquitetura Moderna | expressão consolidada |
| arquitetura moderna brasileira | Arquitetura Moderna Brasileira | expressão consolidada |
| arquitetura moderna residencial | Arquitetura moderna residencial | "Moderna" consolidada, "residencial" adjetivo |
| arquitetura paulista | arquitetura paulista | adjetivada + gentílico |
| brutalismo | Brutalismo | movimento |
| cidade universitária | cidade universitária | genérico |
| conservação | conservação | genérico |
| especulação imobiliária | especulação imobiliária | genérico |
| fotografia | fotografia | genérico |
| habitação moderna | habitação moderna | genérico |
| identidade nacional | identidade nacional | genérico |
| le corbusier | Le Corbusier | nome próprio |
| lelé | Lelé | nome próprio |
| lina bo bardi | Lina Bo Bardi | nome próprio |
| modernidade | Modernidade | conceito substantivado |
| modernismo | Modernismo | movimento |
| museu de arte moderna | Museu de Arte Moderna | nome próprio (instituição) |
| natureza | natureza | genérico |
| patrimônio industrial | patrimônio industrial | genérico (não consolidada) |
| patrimônio moderno | Patrimônio Moderno | expressão consolidada |
| pedagogia projetual | pedagogia projetual | genérico |
| preservação | preservação | genérico |
| pré-fabricação | pré-fabricação | genérico |
| representação | representação | genérico |
| reuso adaptativo | reuso adaptativo | genérico |
| roberto burle marx | Roberto Burle Marx | nome próprio |
| são paulo | São Paulo | nome próprio |
| urbanismo | Urbanismo | disciplina |

### Caso especial: sdbr16-202

Keyword `"segunda-Geração" Moderna` — limpar aspas curvas, corrigir casing: `segunda geração moderna` ou `"segunda geração" moderna`.

### Caso especial: sdbr16-287 REFAP

`REFAP` — sigla legítima (Refinaria Alberto Pasqualini). Manter ALL CAPS.

### Caso especial: Pós-II Guerra

`Arquitetura Americana Pós-Ii Guerra` → `Arquitetura americana pós-II Guerra` (gentílico minúscula, numeral romano maiúscula).

**DONE**: □

---

## Etapa 5 — Varredura geral de qualidade

Verificar todos os 268 artigos com keywords:

1. Keywords que são fragmentos de texto (não keywords reais)
2. Keywords com pontuação residual (`.`, `;`, `,` no final)
3. Keywords com números de página ou lixo de extração
4. Keywords duplicadas
5. Keywords muito longas (>80 caracteres — provavelmente frase, não keyword)
6. Keywords com "(N)" — numeração residual de template

```python
# Queries de verificação
import sqlite3, json
conn = sqlite3.connect("anais.db")
cur = conn.cursor()

# Muito longas
cur.execute("SELECT id, keywords FROM articles WHERE seminar_slug='sdbr16' AND keywords IS NOT NULL AND keywords != '' AND keywords != '[]'")
for aid, kw_json in cur.fetchall():
    for k in json.loads(kw_json):
        if len(k) > 60:
            print(f"LONGA {aid}: {k}")
        if k[-1] in '.;,':
            print(f"PUNCT {aid}: {k}")
        if '(' in k and ')' in k and any(c.isdigit() for c in k):
            print(f"NUM? {aid}: {k}")
```

**DONE**: □

---

## Etapa 6 — keywords_es: verificar artigos em espanhol

12 artigos com keywords_es. Aplicar mesma lógica de inconsistências e casing (regras ES = regras PT, com exceção pragmática para "Arquitectura Moderna" e "Movimiento Moderno").

**DONE**: □

---

## Etapa 7 — Revisão manual dos faltantes (1.10 parcial — só keywords)

Nenhum dos 20 artigos sem keywords tem docx. A fonte possível é o PDF (via plumber ou imagem).

### 7a — 10 artigos COM PDF (buscar keywords no documento)

| id | fonte |
|----|-------|
| sdbr16-008 | PRONTOS/ (2 kw, verificar se há mais) |
| sdbr16-019 | pdfs/ |
| sdbr16-037 | pdfs/ |
| sdbr16-103 | pdfs/ |
| sdbr16-126 | pdfs/ |
| sdbr16-174 | pdfs/ |
| sdbr16-196 | pdfs/ |
| sdbr16-201 | pdfs/ |
| sdbr16-220 | pdfs/ |
| sdbr16-245 | pdfs/ |
| sdbr16-256 | pdfs/ |
| sdbr16-209 | PRONTOS/ (2 kw, verificar se há mais) |

**Procedimento por artigo:**
1. Ler o plumber `.jsonl` (se existir) OU converter PDF para imagem
2. Localizar "Palavras-chave" / "Keywords" / "Palabras clave"
3. Se encontrar: extrair e inserir no banco
4. Se não encontrar: registrar "sem keywords no documento"
5. Registrar resultado: `{id}: {N} keywords extraídas` ou `{id}: sem keywords (verificado)`

**DONE**: □

### 7b — 10 artigos SEM PDF nem docx (aceitar como sem keywords)

| id | situação |
|----|----------|
| sdbr16-042 | sem PDF, sem docx |
| sdbr16-054 | sem PDF, sem docx, sem abstract — pendente organização |
| sdbr16-082 | sem PDF, sem docx |
| sdbr16-117 | sem PDF, sem docx |
| sdbr16-172 | sem PDF, sem docx |
| sdbr16-173 | sem PDF, sem docx |
| sdbr16-179 | sem PDF, sem docx |
| sdbr16-193 | sem PDF, sem docx |
| sdbr16-229 | sem PDF, sem docx |
| sdbr16-272 | sem PDF, sem docx |

Sem fonte disponível para extração. Registrar como "genuinamente sem keywords (sem fonte)".

**DONE**: □

---

## Etapa 8 — Aplicar correções e verificar

```bash
# Rodar clean-keywords novamente (pega aglutinadas, dedup, etc.)
python3 scripts/fix_validation_issues.py --slug sdbr16 --clean-keywords --dry-run
python3 scripts/fix_validation_issues.py --slug sdbr16 --clean-keywords

# Validate
python3 scripts/validate_metadata.py --slug sdbr16

# Regenerar HTML
python3 scripts/gerar_revisao_html.py sdbr16

# Dump
python3 scripts/dump_anais_db.py
```

**DONE**: □

---

## Checklist final

- [x] Etapa 1: clean-keywords automático — 1 junk removido (sdbr16-202)
- [x] Etapa 2: extração de PDFs — nenhum dos 10 com PDF tem label de keywords no plumber
- [x] Etapa 3: mesas redondas — 35 genuinamente sem keywords (1 tem fragmento truncado no abstract)
- [x] Etapa 4: 32+36 inconsistências de casing resolvidas (60 artigos canonical + 36 ALL CAPS parcial)
- [x] Etapa 5: varredura de qualidade — limpa (REFAP é sigla legítima)
- [x] Etapa 6: keywords_es — 7 artigos corrigidos (ALL CAPS, numeração (N), nomes)
- [x] Etapa 7a: 12 artigos com PDF verificados no plumber — nenhum tem keywords além do que já estava no banco
- [x] Etapa 7b: 10 artigos sem PDF nem docx — aceitos como sem keywords (sem fonte)
- [x] Etapa 8: clean + validate (1 A19 restante) + HTML + dump
