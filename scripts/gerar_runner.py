#!/usr/bin/env python3
"""Gera e consulta runners (checklists executáveis) para seminários.

O runner é o que o Claude segue etapa a etapa. Os pipelines
(pipeline_revisao.md, pipeline_tratamento.md) são a referência
de consulta para detalhes e edge cases.

Uso:
    python3 scripts/gerar_runner.py                         # lista seminários e runners
    python3 scripts/gerar_runner.py SLUG                    # gera runner de revisão
    python3 scripts/gerar_runner.py SLUG --type producao    # gera runner de produção
    python3 scripts/gerar_runner.py SLUG --status           # mostra progresso do runner
    python3 scripts/gerar_runner.py SLUG --force            # sobrescreve runner existente
"""

import argparse
import sqlite3
import os
import re
from datetime import date


def get_stats(slug):
    db = sqlite3.connect('anais.db')
    row = db.execute("""
        SELECT
            COUNT(*),
            SUM(CASE WHEN abstract IS NOT NULL AND abstract != '' THEN 1 ELSE 0 END),
            SUM(CASE WHEN abstract_en IS NOT NULL AND abstract_en != '' THEN 1 ELSE 0 END),
            SUM(CASE WHEN keywords IS NOT NULL AND keywords != '' AND keywords != '[]' THEN 1 ELSE 0 END),
            SUM(CASE WHEN keywords_en IS NOT NULL AND keywords_en != '' AND keywords_en != '[]' THEN 1 ELSE 0 END),
            SUM(CASE WHEN references_ IS NOT NULL AND references_ != '' AND references_ != '[]' THEN 1 ELSE 0 END),
            SUM(CASE WHEN title_en IS NOT NULL AND title_en != '' THEN 1 ELSE 0 END)
        FROM articles WHERE seminar_slug = ?
    """, (slug,)).fetchone()

    if not row or row[0] == 0:
        db.close()
        return None

    n_sections = db.execute(
        "SELECT COUNT(*) FROM sections WHERE seminar_slug = ?", (slug,)
    ).fetchone()[0]

    db.close()
    return {
        'total': row[0],
        'abstract': row[1] or 0,
        'abstract_en': row[2] or 0,
        'keywords': row[3] or 0,
        'keywords_en': row[4] or 0,
        'refs': row[5] or 0,
        'title_en': row[6] or 0,
        'sections': n_sections,
    }


def pct(n, total):
    return round(100 * n / total) if total else 0


def show_status(slug):
    """Mostra progresso de um runner existente."""
    path = f'revisao/{slug}-runner.md'
    if not os.path.exists(path):
        print(f"Runner não existe: {path}")
        print(f"Gerar com: python3 scripts/gerar_runner.py {slug}")
        return

    with open(path) as f:
        content = f.read()

    done = len(re.findall(r'- \[x\]', content))
    skip = len(re.findall(r'- \[skip\]', content, re.IGNORECASE))
    todo = len(re.findall(r'- \[ \]', content))
    total = done + todo

    # Find current phase and next step
    next_step = None
    current_phase = None
    for line in content.split('\n'):
        if line.startswith('## Fase'):
            current_phase = line
        if '- [ ] **' in line and not next_step:
            m = re.search(r'\*\*(.+?)\*\*\s+(.+)', line)
            if m:
                next_step = f"{m.group(1)} {m.group(2)[:60]}"

    print(f"Runner: {path}")
    print(f"Progresso: {done}/{total} ({skip} skip)")
    if next_step:
        print(f"Próxima: {next_step}")
    elif todo == 0:
        print("Concluído!")
    print()

    # Show phases with progress
    phase = None
    phase_done = phase_todo = 0
    for line in content.split('\n'):
        if line.startswith('## Fase'):
            if phase:
                status = '✅' if phase_todo == 0 else f'{phase_done}/{phase_done + phase_todo}'
                print(f"  {status} {phase}")
            phase = line.replace('## ', '').strip()
            phase_done = phase_todo = 0
        elif '- [x]' in line:
            phase_done += 1
        elif '- [ ]' in line:
            phase_todo += 1
    if phase:
        status = '✅' if phase_todo == 0 else f'{phase_done}/{phase_done + phase_todo}'
        print(f"  {status} {phase}")


def list_seminars():
    """Lista seminários no banco e runners existentes."""
    db = sqlite3.connect('anais.db')
    rows = db.execute("""
        SELECT s.slug, s.title, COUNT(a.id) as n
        FROM seminars s
        LEFT JOIN articles a ON a.seminar_slug = s.slug
        GROUP BY s.slug
        ORDER BY s.slug
    """).fetchall()
    db.close()

    # Check existing runners
    runners = set()
    if os.path.exists('revisao'):
        for f in os.listdir('revisao'):
            m = re.match(r'(.+)-runner\.md$', f)
            if m:
                runners.add(m.group(1))

    print("Seminários no banco:\n")
    print(f"{'Slug':<12} {'Arts':>4}  {'Runner':<10}  Título")
    print(f"{'─'*12} {'─'*4}  {'─'*10}  {'─'*40}")
    for slug, title, n in rows:
        runner_status = ''
        if slug in runners:
            path = f'revisao/{slug}-runner.md'
            with open(path) as f:
                content = f.read()
            done = len(re.findall(r'- \[x\]', content))
            todo = len(re.findall(r'- \[ \]', content))
            if todo == 0:
                runner_status = '✅ pronto'
            else:
                runner_status = f'⏳ {done}/{done+todo}'
        title_short = (title or '')[:40]
        print(f"{slug:<12} {n:>4}  {runner_status:<10}  {title_short}")

    print(f"\nUso: python3 scripts/gerar_runner.py SLUG [--status]")


def gen_revisao(slug, s):
    t = s['total']
    has_en = pct(s['abstract_en'], t) >= 30
    has_title_en = pct(s['title_en'], t) >= 30
    skip_en = '' if has_en else ' `[SKIP: abstract_en < 30%]`'
    skip_ten = '' if has_title_en else ' `[SKIP: title_en < 30%]`'

    return f"""# {slug} — Runner de revisão

Pipeline: revisao | Gerado: {date.today()} | Artigos: {t}
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/{t} | % |
|-------|-------|---|
| abstract | {s['abstract']} | {pct(s['abstract'], t)}% |
| abstract_en | {s['abstract_en']} | {pct(s['abstract_en'], t)}% |
| keywords | {s['keywords']} | {pct(s['keywords'], t)}% |
| keywords_en | {s['keywords_en']} | {pct(s['keywords_en'], t)}% |
| references | {s['refs']} | {pct(s['refs'], t)}% |
| title_en | {s['title_en']} | {pct(s['title_en'], t)}% |
| sections | {s['sections']} | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [ ] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit
- [ ] **0.1** Levantar padrão de metadados (query cobertura → classificar campos)
- [ ] **0.2** Listar artigos fora do padrão (campos esperados mas ausentes)
- [ ] **0.3** Reinspecionar PDFs dos artigos fora do padrão (hierarquia: docx → plumber → pdftotext)
- [ ] **0.3b** Extrair fontes plumber
  ```
  python3 scripts/extrair_fontes_plumber.py --slug {slug} --profile-only
  python3 scripts/extrair_fontes_plumber.py --slug {slug}
  ```
- [ ] **0.4** Seções/sessões (fontes: sumário, site do evento, cabeçalhos PDF, programa)
- [ ] **0.5** Preencher lacunas no banco (salvar JSON antes, verificar idioma dos abstracts)
- [ ] **0.6** Extrair metadados EN{skip_en}: `python3 scripts/extrair_metadados_en.py --slug {slug}`
- [ ] **0.7** Extrair metadados ES (artigos com locale=es: abstract, keywords do plumber)
- [ ] **0.8** Verificar abstracts + auto-fix
  ```
  python3 scripts/validate_metadata.py --slug {slug} --fix
  ```
  Depois: varredura manual (truncamento, lixo, cruzamento de idiomas)

## Fase 1 — Revisão automática

- [ ] **1.1a** Títulos PT: seed + normalizar + revisão LLM
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug {slug} --dry-run
  python3 scripts/normalizar_maiusculas.py --slug {slug}
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [ ] **1.1b** Títulos EN/ES: `python3 scripts/normalizar_titulos_en.py --slug {slug}`{skip_ten}
- [ ] **1.1c** Revisão LLM títulos EN/ES (cada título vs PDF){skip_ten}
- [ ] **1.2a** Refs limpeza base
  ```
  python3 scripts/clean_references.py --slug {slug} --dry-run
  python3 scripts/clean_references.py --slug {slug}
  python3 scripts/check_references.py --slug {slug} --summary
  ```
- [ ] **1.2b** Refs sweep (8 passadas)
  ```
  python3 scripts/fix_validation_issues.py --slug {slug} --sweep-refs --dry-run
  python3 scripts/fix_validation_issues.py --slug {slug} --sweep-refs
  ```
- [ ] **1.2b+** Re-backfills: `python3 scripts/clean_references.py --slug {slug}`
- [ ] **1.2c** Refs revisão LLM — TODOS os artigos vs fontes (ver §1.2c)
- [ ] **1.3** Keywords
  ```
  python3 scripts/fix_validation_issues.py --slug {slug} --clean-keywords --dry-run
  python3 scripts/fix_validation_issues.py --slug {slug} --clean-keywords
  ```
- [ ] **1.5** Loop validação: `python3 scripts/fix_validation_issues.py --slug {slug} --loop`
- [ ] **1.6** Cobertura de metadados + metadados do seminário (título, ISBN, editora)
- [ ] **1.7** Autores: verificar completude vs PDF (confrontar cada artigo com o PDF)
- [ ] **1.8** Dedup autores: `python3 dict/seed_authors.py && python3 scripts/dedup_authors.py`
- [ ] **1.9** ORCID: `python3 scripts/fetch_orcid.py --search --slug {slug}` → `--review` → `--apply`

## Fase 2 — HTML de revisão + checkpoint

- [ ] **2.0** Validação final + HTML + commit
  ```
  python3 scripts/validate_metadata.py --slug {slug} --fix
  python3 scripts/gerar_revisao_html.py {slug}
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/{slug}-* && git commit -m "{slug} revisão automática (Fases 0-2)"
  ```

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [ ] **3.1** Diagnóstico unificado (correções automáticas + humanas → causa raiz)
- [ ] **3.2** Atualizar dict.db (remover genéricos, adicionar nomes próprios)
- [ ] **3.3** Atualizar scripts (se >=3 artigos com mesmo erro não coberto)
- [ ] **3.4** Atualizar pipeline (se gaps na ordem de execução)
- [ ] **3.5** Verificar: dry-run sem regressão
- [ ] **3.6** Registrar aprendizado (JSON + MEMORY.md)
- [ ] **3.7** Revisão de engenharia (autoavaliação + lints)
- [ ] **3.8** Checklist de conclusão
- [ ] **3.9** Fechar: dump + commit + push + CLAUDE.md
"""


def gen_producao(slug, s):
    return f"""# {slug} — Runner de produção

Pipeline: producao | Gerado: {date.today()} | Artigos: {s['total']}
Referência: [pipeline_producao.md](../docs/pipeline_producao.md)

## Pré-requisitos

- [ ] Revisão automática concluída (Fases 0-2)
- [ ] Revisão humana concluída

## Produção

- [ ] Exportar YAML: `python3 scripts/export_db_to_yaml.py --slug {slug}`
- [ ] Gerar Hugo: `python3 scripts/db2hugo.py --seminar {slug}`
- [ ] Build local: `cd site && hugo server` (verificar)
- [ ] Upload Zenodo
  ```
  python3 scripts/upload_zenodo.py --slug {slug} --community docomomobr --dry-run
  python3 scripts/upload_zenodo.py --slug {slug} --community docomomobr
  ```
- [ ] Gravar DOIs no banco
- [ ] Dump + commit + push
"""


def main():
    p = argparse.ArgumentParser(
        description='Gera e consulta runners (checklists executáveis) para seminários')
    p.add_argument('slug', nargs='?', default=None,
                   help='Slug do seminário (sem argumento: lista todos)')
    p.add_argument('--type', choices=['revisao', 'producao'], default='revisao',
                   help='Tipo de runner (default: revisao)')
    p.add_argument('--status', action='store_true',
                   help='Mostra progresso do runner existente')
    p.add_argument('--force', action='store_true',
                   help='Sobrescrever runner existente')
    args = p.parse_args()

    if args.slug is None:
        list_seminars()
        return

    if args.status:
        show_status(args.slug)
        return

    out = f'revisao/{args.slug}-runner.md'
    if os.path.exists(out) and not args.force:
        print(f"Já existe: {out}")
        show_status(args.slug)
        print(f"\nUse --force para sobrescrever")
        return

    stats = get_stats(args.slug)
    if not stats:
        print(f"'{args.slug}' não encontrado no banco")
        return

    gen = gen_revisao if args.type == 'revisao' else gen_producao
    content = gen(args.slug, stats)

    os.makedirs('revisao', exist_ok=True)
    with open(out, 'w') as f:
        f.write(content)
    print(f"{out} ({stats['total']} artigos)")


if __name__ == '__main__':
    main()
