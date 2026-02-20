#!/usr/bin/env python3
"""
Detecta erros nas referências bibliográficas do anais.db.

Heurísticas:
  1. Referências concatenadas (múltiplas na mesma linha)
     - Muito longas (> 400 chars)
     - Contêm padrão de separação: autor em CAPS seguido de vírgula no meio do texto
  2. Conteúdo que não é referência
     - Fragmentos de texto corrido (sem autor, sem ano, sem editora)
     - Legendas de figuras, notas de rodapé
     - URLs soltas
     - Bullet points, listas de materiais
  3. Referências incompletas
     - Muito curtas (< 25 chars)
     - Parecem continuação da ref anterior (não começam com maiúscula/dígito)

Uso:
    python3 scripts/check_references.py [--slug SLUG] [--min-len N] [--max-len N]
    python3 scripts/check_references.py --summary
"""

import argparse
import json
import os
import re
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')

# Padrões que indicam texto corrido (não referência)
NOT_REF_PATTERNS = [
    # Fragmentos de texto narrativo (verbos conjugados no meio)
    re.compile(r'^[a-záàãâéêíóôõúüç].*\b(encontram-se|trata-se|merece destaque|em pauta|escusado|independentemente)\b', re.IGNORECASE),
    # Legendas de figuras
    re.compile(r'^\(?\s*(fig\.|figura|foto|imagem|fonte:)\s', re.IGNORECASE),
    # Apenas URL
    re.compile(r'^(https?://|www\.)\S+$', re.IGNORECASE),
    # Bullet points ou listas
    re.compile(r'^[•\-–—]\s'),
    # Apenas pontuação/símbolos
    re.compile(r'^[\s•\-–—·.,;:]+$'),
    # Notas de rodapé numeradas (sem ser referência)
    re.compile(r'^\d+\s+[A-Z][a-z]+\s+(é|foi|são|era|tem|deve|pode|precisa|quer|como|quando|onde|porque)\b'),
]

# Padrões que indicam referência legítima
REF_PATTERNS = [
    # SOBRENOME, Nome. Título...
    re.compile(r'^[A-ZÁÀÃÂÉÊÍÓÔÕÚÜÇ][A-ZÁÀÃÂÉÊÍÓÔÕÚÜÇ\s]+,\s*[A-ZÁÀÃÂÉÊÍÓÔÕÚÜÇ]'),
    # Nome Sobrenome. Título...  ou  SIGLA. Título...
    re.compile(r'^[A-ZÁÀÃÂÉÊÍÓÔÕÚÜÇ][A-Za-záàãâéêíóôõúüç\s]+\.\s'),
    # _____. (mesmo autor)
    re.compile(r'^_{2,}\.'),
    # Número. SOBRENOME (refs numeradas)
    re.compile(r'^\d+[\.\)]\s*[A-ZÁÀÃÂÉÊÍÓÔÕÚÜÇ]'),
    # SIGLA (IBGE, IPHAN, BRASIL, etc.)
    re.compile(r'^[A-Z]{2,}[\s.,]'),
]

# Padrão que sugere refs concatenadas: "ano. SOBRENOME," no meio do texto
CONCAT_PATTERN = re.compile(
    r'[12]\d{3}[a-z]?\.\s+[A-ZÁÀÃÂÉÊÍÓÔÕÚÜÇ][A-ZÁÀÃÂÉÊÍÓÔÕÚÜÇ]+,\s*[A-Z]'
)

# Padrão alternativo: ". In:" ou "ano." seguido de nova ref
CONCAT_PATTERN2 = re.compile(
    r'\.\s{2,}[A-ZÁÀÃÂÉÊÍÓÔÕÚÜÇ][A-ZÁÀÃÂÉÊÍÓÔÕÚÜÇ]+,\s'
)


def classify_ref(ref, index, total):
    """Classifica uma referência e retorna lista de problemas encontrados."""
    problems = []
    ref = ref.strip()

    if not ref:
        problems.append(('vazia', 'Referência vazia'))
        return problems

    length = len(ref)

    # 1. Muito curta
    if length < 25:
        problems.append(('curta', f'Muito curta ({length} chars)'))

    # 2. Muito longa (possível concatenação)
    if length > 400:
        severity = 'concatenada_provavel' if length > 800 else 'concatenada_possivel'
        problems.append((severity, f'Muito longa ({length} chars)'))

    # 3. Padrão de concatenação no meio do texto
    if CONCAT_PATTERN.search(ref[50:] if len(ref) > 50 else ''):
        problems.append(('concatenada_padrao', 'Padrão "ano. SOBRENOME," detectado no meio'))

    if CONCAT_PATTERN2.search(ref[50:] if len(ref) > 50 else ''):
        problems.append(('concatenada_padrao2', 'Espaço duplo + novo autor detectado no meio'))

    # 4. Não começa com maiúscula nem dígito (possível continuação ou texto)
    if ref and not ref[0].isupper() and not ref[0].isdigit() and not ref.startswith('_') and not ref.startswith('http') and not ref.startswith('('):
        # Verificar se parece texto corrido
        problems.append(('inicio_minuscula', 'Não começa com maiúscula/dígito'))

    # 5. Parece texto corrido (não referência)
    is_ref = any(p.match(ref) for p in REF_PATTERNS)
    if not is_ref and length > 50:
        # Heurística: referências geralmente têm ano (4 dígitos) e ponto
        has_year = bool(re.search(r'\b[12]\d{3}\b', ref))
        has_period = '.' in ref
        if not has_year and not has_period:
            problems.append(('sem_ano_ponto', 'Sem ano e sem ponto (provavelmente não é referência)'))
        elif not has_year:
            # Pode ser texto corrido longo sem ano
            words = ref.split()
            # Texto corrido tende a ter muitas palavras comuns em sequência
            common_words = {'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas',
                           'um', 'uma', 'o', 'a', 'os', 'as', 'que', 'se', 'com', 'por',
                           'para', 'como', 'mais', 'não', 'ou', 'é', 'foi', 'são', 'ser'}
            common_count = sum(1 for w in words if w.lower() in common_words)
            ratio = common_count / len(words) if words else 0
            if ratio > 0.35 and length > 100:
                problems.append(('texto_corrido', f'Alta proporção de palavras comuns ({ratio:.0%})'))

    # 6. Padrões específicos de não-referência
    for pattern in NOT_REF_PATTERNS:
        if pattern.search(ref):
            problems.append(('nao_referencia', f'Padrão de não-referência detectado'))
            break

    return problems


def check_article(article_id, refs_json):
    """Verifica referências de um artigo. Retorna lista de (ref_index, ref_text, problems)."""
    try:
        refs = json.loads(refs_json)
    except (json.JSONDecodeError, TypeError):
        return [(0, refs_json[:100] if refs_json else '', [('json_invalido', 'JSON inválido')])]

    if not isinstance(refs, list):
        return [(0, str(refs)[:100], [('formato_invalido', 'Não é lista')])]

    issues = []
    for i, ref in enumerate(refs):
        if not isinstance(ref, str):
            issues.append((i, str(ref)[:100], [('tipo_invalido', f'Tipo: {type(ref).__name__}')]))
            continue
        problems = classify_ref(ref, i, len(refs))
        if problems:
            issues.append((i, ref, problems))

    return issues


def main():
    parser = argparse.ArgumentParser(description='Detectar erros em referências bibliográficas')
    parser.add_argument('--slug', help='Verificar apenas este seminário')
    parser.add_argument('--summary', action='store_true', help='Mostrar apenas resumo por seminário')
    parser.add_argument('--type', choices=['concatenada', 'nao_ref', 'curta', 'todas'],
                        default='todas', help='Filtrar por tipo de problema')
    parser.add_argument('--max-show', type=int, default=200,
                        help='Máximo de problemas a mostrar no detalhe (default: 200)')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    where = "WHERE references_ IS NOT NULL AND references_ != ''"
    params = []
    if args.slug:
        where += " AND seminar_slug = ?"
        params.append(args.slug)

    rows = conn.execute(
        f"SELECT id, seminar_slug, references_ FROM articles {where} ORDER BY id",
        params
    ).fetchall()

    # Classificar problemas em categorias
    TYPE_MAP = {
        'concatenada': {'concatenada_provavel', 'concatenada_possivel', 'concatenada_padrao', 'concatenada_padrao2'},
        'nao_ref': {'nao_referencia', 'texto_corrido', 'sem_ano_ponto', 'inicio_minuscula'},
        'curta': {'curta', 'vazia'},
    }

    # Acumular estatísticas
    stats_by_slug = {}  # slug → {type → count}
    all_issues = []  # (article_id, ref_index, ref_text, problems)

    for row in rows:
        article_id = row['id']
        slug = row['seminar_slug']
        issues = check_article(article_id, row['references_'])

        if slug not in stats_by_slug:
            stats_by_slug[slug] = {
                'total_refs': len(json.loads(row['references_'])),
                'concatenada': 0, 'nao_ref': 0, 'curta': 0, 'outras': 0,
                'artigos_com_problema': 0,
            }
        else:
            stats_by_slug[slug]['total_refs'] += len(json.loads(row['references_']))

        if issues:
            stats_by_slug[slug]['artigos_com_problema'] += 1

        for ref_idx, ref_text, problems in issues:
            for prob_type, prob_desc in problems:
                categorized = False
                for cat, types in TYPE_MAP.items():
                    if prob_type in types:
                        stats_by_slug[slug][cat] += 1
                        categorized = True
                        break
                if not categorized:
                    stats_by_slug[slug]['outras'] += 1

                # Filtro por tipo
                if args.type != 'todas':
                    if prob_type not in TYPE_MAP.get(args.type, set()):
                        continue

                all_issues.append((article_id, ref_idx, ref_text, prob_type, prob_desc))

    conn.close()

    # Mostrar resultado
    if args.summary:
        print(f"{'Slug':<12} {'Refs':>5} {'Concat':>7} {'Não-ref':>8} {'Curta':>6} {'Arts c/ prob':>12}")
        print('-' * 55)
        totals = {'refs': 0, 'concat': 0, 'nao_ref': 0, 'curta': 0, 'arts': 0}
        for slug in sorted(stats_by_slug):
            s = stats_by_slug[slug]
            print(f"{slug:<12} {s['total_refs']:>5} {s['concatenada']:>7} {s['nao_ref']:>8} {s['curta']:>6} {s['artigos_com_problema']:>12}")
            totals['refs'] += s['total_refs']
            totals['concat'] += s['concatenada']
            totals['nao_ref'] += s['nao_ref']
            totals['curta'] += s['curta']
            totals['arts'] += s['artigos_com_problema']
        print('-' * 55)
        print(f"{'TOTAL':<12} {totals['refs']:>5} {totals['concat']:>7} {totals['nao_ref']:>8} {totals['curta']:>6} {totals['arts']:>12}")
    else:
        shown = 0
        current_article = None
        for article_id, ref_idx, ref_text, prob_type, prob_desc in all_issues:
            if shown >= args.max_show:
                remaining = len(all_issues) - shown
                print(f"\n... e mais {remaining} problemas. Use --max-show para ver mais.")
                break

            if article_id != current_article:
                current_article = article_id
                print(f"\n{'='*70}")
                print(f"  {article_id}")
                print(f"{'='*70}")

            # Cor do tipo
            label = prob_type.upper().replace('_', ' ')
            ref_preview = ref_text[:300]
            if len(ref_text) > 300:
                ref_preview += '...'

            print(f"\n  [{label}] ref #{ref_idx + 1}: {prob_desc}")
            print(f"  > {ref_preview}")
            shown += 1

        print(f"\n--- Total: {len(all_issues)} problemas em {len(stats_by_slug)} seminários ---")

    # Resumo final
    total_probs = sum(s['concatenada'] + s['nao_ref'] + s['curta'] for s in stats_by_slug.values())
    total_refs = sum(s['total_refs'] for s in stats_by_slug.values())
    if total_refs > 0:
        print(f"\nResumo: {total_probs} problemas / {total_refs} referências ({total_probs/total_refs*100:.1f}%)")
    else:
        print(f"\nResumo: {total_probs} problemas / 0 referências")


if __name__ == '__main__':
    main()
