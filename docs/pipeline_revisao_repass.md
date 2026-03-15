# Pipeline de Repassagem — Seminários já revisados

Pipeline filho do [`pipeline_revisao.md`](pipeline_revisao.md) para re-rodar a revisão automática em seminários que foram revisados com versão anterior do pipeline (sdbr01–sdbr09).

**Objetivo:** aplicar os checks e melhorias que não existiam quando esses seminários foram revisados, sem exigir nova revisão humana.

**REGRA #0 do pipeline pai se aplica integralmente.**

---

## Diferenças em relação ao pipeline completo

1. **Títulos e subtítulos (PT, EN, ES):** NÃO aplicar normalização automática (`normalizar_maiusculas.py`, `normalizar_titulos_en.py`) — esses seminários já foram revisados manualmente. Apenas **listar** alterações propostas e pedir **confirmação humana** antes de aplicar cada uma.
2. **Sem parada para revisão humana:** não gerar HTML nem esperar `rev.md`. Corrigir automaticamente o que for seguro (refs, keywords, validate auto-fixes). Listar o que precisaria de decisão humana num relatório final.
3. **Fase 3 (aprendizado + engenharia):** rodar uma única vez ao final de todos os seminários, não a cada um.

---

## Etapas por seminário

Para cada seminário (sdbr01, sdbr02, ..., sdbr09):

### R.1 Diagnóstico rápido

```bash
python3 scripts/validate_metadata.py --slug {slug} --dry-run
```

Registrar contagem de issues. Se zero → seminário limpo, pular para o próximo.

### R.2 Auto-fixes seguros

Rodar validate com --fix para aplicar auto-fixes que não tocam em títulos:

```bash
python3 scripts/validate_metadata.py --slug {slug} --fix
```

Auto-fixes seguros: A15 (locale), A16 (control chars), A17 (refs duplicadas), A20 (overflow), A21 (abstract_es lixo), A23 (EN colado no PT), A25 (keywords coladas), A26 (abstract idioma errado), A27 (PT no EN).

### R.3 Referências

```bash
python3 scripts/clean_references.py --slug {slug}
python3 scripts/fix_validation_issues.py --slug {slug} --sweep-refs
python3 scripts/clean_references.py --slug {slug}   # re-backfill
```

### R.4 Keywords

```bash
python3 scripts/fix_validation_issues.py --slug {slug} --clean-keywords
```

### R.5 Títulos — LISTAR, NÃO APLICAR

Rodar em dry-run e listar propostas de alteração. **Pedir confirmação humana** antes de aplicar.

```bash
# PT
python3 scripts/normalizar_maiusculas.py --slug {slug} --dry-run

# EN (se houver)
python3 scripts/normalizar_titulos_en.py --slug {slug} --dry-run

# ES (se houver)
python3 scripts/normalizar_maiusculas.py --slug {slug} --field title_es --dry-run
```

Salvar a lista de propostas em `revisao/{slug}-repass-titulos.txt`. O humano decide quais aplicar.

### R.6 Verificação de autores (1.6d)

```bash
# Verificação exaustiva PDF→DB
```

Reportar discrepâncias. Corrigir sem confirmação (autores faltantes são erro claro).

### R.7 Seções

Se `section_id` está NULL para todos os artigos e existe fonte de eixos (PDF dos anais, site do evento), criar seções e mapear. Se já mapeados, pular.

### R.8 Ficha catalográfica (1.6b)

Verificar `description` contra ficha CIP do PDF dos anais (se disponível). Corrigir se necessário.

### R.9 Registrar

Salvar resumo em `revisao/{slug}-repass-status.md`:
- Issues encontrados e resolvidos
- Issues que precisam de decisão humana
- Propostas de título não aplicadas (aguardando confirmação)

---

## Ao final de todos os seminários

### R.10 Relatório consolidado

Agregar todos os `{slug}-repass-status.md` num relatório único com:
- Total de auto-fixes por tipo
- Propostas de título pendentes (para confirmação humana em lote)
- Issues não resolvidos

### R.11 Fase 3 (aprendizado + engenharia)

Rodar uma única vez, cobrindo todos os seminários repassados:
- 3.1 Diagnóstico unificado
- 3.3 Scripts (se aplicável)
- 3.5 Verificação (dry-run)
- 3.7 Engenharia (7 itens)
- 3.8 Commit + push

---

## Seminários a repassar

| Slug | Artigos | Revisado em | Observação |
|------|---------|-------------|------------|
| sdbr01 | 37 | 2026-02-24 | |
| sdbr02 | 22 | 2026-02-24 | |
| sdbr03 | 56 | 2026-02-26 | |
| sdbr04 | 79 | 2026-02-26 | Só resumos |
| sdbr05 | 56 | 2026-02-28 | |
| sdbr06 | 63 | 2026-03-01 | |
| sdbr07 | 62 | 2026-03-02 | |
| sdbr08 | 188 | 2026-03-09 | |
| sdbr09 | 170 | 2026-03-09 | |
