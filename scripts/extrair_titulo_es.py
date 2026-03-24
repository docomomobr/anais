#!/usr/bin/env python3
"""Extrai title_es e subtitle_es (e title_en/subtitle_en) dos PDFs usando pdfplumber.

Usa metadados de fonte (tamanho, bold, italic) para identificar blocos de título
em cada idioma. Funciona para sdnne10 e sdbr15 (padrões de fonte diferentes).

Uso:
    python3 scripts/extrair_titulo_es.py --slug sdnne10 --dry-run
    python3 scripts/extrair_titulo_es.py --slug sdnne10
    python3 scripts/extrair_titulo_es.py --slug sdbr15 --dry-run
"""

import argparse
import os
import re
import sqlite3
import sys

import pdfplumber


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')


# ── Detecção de idioma EN vs ES ──────────────────────────────────────────────

# Palavras exclusivas do espanhol (não existem em inglês)
ES_MARKERS = {
    'del', 'los', 'las', 'una', 'uno', 'unos', 'unas', 'como', 'desde',
    'entre', 'hacia', 'para', 'según', 'sobre', 'tras', 'mediante',
    'arquitectura', 'arquitectónica', 'arquitectónico', 'arquitectónicos',
    'ciudad', 'ciudades', 'moderno', 'moderna', 'modernos', 'modernas',
    'patrimonio', 'documentación', 'conservación', 'habitacional',
    'análisis', 'estudio', 'perspectiva', 'urbana', 'urbano',
    'movimiento', 'diseño', 'histórico', 'histórica', 'públicas',
    'vivienda', 'edificio', 'edificios', 'barrio', 'calle',
    'construcción', 'destrucción', 'reflexiones', 'reflejos',
    'antiguo', 'antigua', 'joven', 'aplicadas', 'piezas',
    'azulejo', 'azulejos', 'superficial',
    # artigos/preposições ES que diferem de EN
    'el', 'la', 'en', 'de', 'y', 'un',
}

# Palavras exclusivas do inglês (não existem em espanhol)
EN_MARKERS = {
    'the', 'of', 'in', 'and', 'for', 'with', 'from', 'between',
    'through', 'towards', 'beyond', 'within', 'into', 'upon',
    'architecture', 'architectural', 'building', 'buildings',
    'city', 'cities', 'modern', 'heritage', 'documentation',
    'conservation', 'housing', 'analysis', 'study', 'perspective',
    'urban', 'movement', 'design', 'historic', 'historical',
    'public', 'memory', 'records', 'reflections',
    'old', 'young', 'applied', 'tile', 'tiles', 'surface',
    # artigos/preposições EN
    'a', 'an',
}


def detect_language_boundary(text):
    """Encontra o ponto onde o texto muda de inglês para espanhol.

    Retorna (en_text, es_text) ou (text, '') se não encontrar ES.
    """
    # Tentar split por padrões comuns de início ES
    # Padrão: nome próprio repetido (ex: "GERALDINO DUDA: ... GERALDINO DUDA: ...")
    # Ou artigo espanhol após pontuação/espaço

    words = text.split()
    if len(words) < 3:
        return text, ''

    # Estratégia: janela deslizante, contar markers EN vs ES
    best_split = -1
    best_score = 0

    for i in range(2, len(words) - 1):
        word_lower = words[i].lower().rstrip('.:,;')

        # Checar se esta palavra inicia uma sequência ES
        if word_lower in ('la', 'el', 'los', 'las', 'un', 'una'):
            # Verificar contexto: as próximas palavras são ES?
            window = words[i:min(i+8, len(words))]
            es_count = sum(1 for w in window if w.lower().rstrip('.:,;') in ES_MARKERS)
            en_count = sum(1 for w in window if w.lower().rstrip('.:,;') in EN_MARKERS)

            # Também verificar que as palavras ANTES são EN
            prev_window = words[max(0, i-5):i]
            prev_en = sum(1 for w in prev_window if w.lower().rstrip('.:,;') in EN_MARKERS)
            prev_es = sum(1 for w in prev_window if w.lower().rstrip('.:,;') in ES_MARKERS)

            score = (es_count - en_count) + (prev_en - prev_es)
            if score > best_score:
                best_score = score
                best_split = i

        # Padrões específicos de início ES
        elif word_lower in ('arquitectura', 'documentación', 'patrimonio',
                           'conservación', 'análisis', 'reflejos', 'reflexiones',
                           'modernidades', 'diálogos', 'registro', 'artes',
                           'poética'):
            # Verificar se antes tinha EN
            prev_window = words[max(0, i-5):i]
            prev_en = sum(1 for w in prev_window if w.lower().rstrip('.:,;') in EN_MARKERS)
            if prev_en >= 1:
                window = words[i:min(i+6, len(words))]
                es_count = sum(1 for w in window if w.lower().rstrip('.:,;') in ES_MARKERS)
                score = es_count + prev_en
                if score > best_score:
                    best_score = score
                    best_split = i

    if best_split > 0 and best_score >= 2:
        en_text = ' '.join(words[:best_split])
        es_text = ' '.join(words[best_split:])
        return en_text, es_text

    return text, ''


def split_title_subtitle(text):
    """Separa título e subtítulo por ': ' ou ' — ' ou ' – '."""
    # Tentar ': '
    for sep in [': ', ' — ', ' – ']:
        if sep in text:
            idx = text.index(sep)
            title = text[:idx]
            subtitle = text[idx + len(sep):]
            return title, subtitle
    return text, ''


def extract_titles_sdnne10(pdf_path):
    """Extrai títulos PT, EN, ES do PDF sdnne10 usando font metadata.

    Padrão sdnne10:
    - 14pt Bold = título PT principal
    - 14pt Regular = subtítulo PT
    - 10pt Italic = título EN + título ES (concatenados)
    """
    try:
        pdf = pdfplumber.open(pdf_path)
    except Exception:
        return None

    try:
        page = pdf.pages[0]
        words = page.extract_words(extra_attrs=['fontname', 'size', 'top'])

        # Coletar palavras 10pt Italic com posição vertical
        italic_words = []
        for w in words:
            size = round(w['size'], 1)
            is_italic = 'Italic' in w.get('fontname', '')
            if abs(size - 10) < 0.5 and is_italic:
                italic_words.append((w['top'], w['text']))

        if not italic_words:
            return None

        # Agrupar por linhas (y-position) e detectar gap > 30pt
        # para separar bloco de títulos do bloco de afiliações/corpo
        title_words = []
        prev_top = italic_words[0][0]
        for top, text in italic_words:
            if top - prev_top > 30:
                break  # gap grande = fim do bloco de títulos
            title_words.append(text)
            prev_top = top

        if not title_words:
            return None

        full_text = ' '.join(title_words)

        # Separar EN e ES
        en_text, es_text = detect_language_boundary(full_text)

        # Separar título/subtítulo
        title_en, subtitle_en = split_title_subtitle(en_text)
        title_es, subtitle_es = split_title_subtitle(es_text)

        return {
            'title_en': title_en.strip().rstrip('.'),
            'subtitle_en': subtitle_en.strip().rstrip('.'),
            'title_es': title_es.strip().rstrip('.'),
            'subtitle_es': subtitle_es.strip().rstrip('.'),
        }
    finally:
        pdf.close()


def extract_titles_sdbr15(pdf_path):
    """Extrai títulos EN, ES do PDF sdbr15 usando font metadata.

    Padrão sdbr15:
    - 18pt = título PT
    - 12pt = título EN + título ES (em bloco, mesmo tamanho)
    - 11pt = autores
    """
    try:
        pdf = pdfplumber.open(pdf_path)
    except Exception:
        return None

    try:
        page = pdf.pages[0]
        words = page.extract_words(extra_attrs=['fontname', 'size', 'top'])

        # Coletar palavras de 12pt com posição vertical
        title_words_pos = []
        for w in words:
            size = round(w['size'], 1)
            if abs(size - 12) < 0.5:
                title_words_pos.append((w['top'], w['text']))

        if not title_words_pos:
            return None

        # Detectar gap > 30pt para separar títulos de afiliações
        title_12_words = []
        prev_top = title_words_pos[0][0]
        for top, text in title_words_pos:
            if top - prev_top > 30:
                break
            title_12_words.append(text)
            prev_top = top

        if not title_12_words:
            return None

        full_text = ' '.join(title_12_words)

        # Separar EN e ES
        en_text, es_text = detect_language_boundary(full_text)

        title_en, subtitle_en = split_title_subtitle(en_text)
        title_es, subtitle_es = split_title_subtitle(es_text)

        return {
            'title_en': title_en.strip().rstrip('.'),
            'subtitle_en': subtitle_en.strip().rstrip('.'),
            'title_es': title_es.strip().rstrip('.'),
            'subtitle_es': subtitle_es.strip().rstrip('.'),
        }
    finally:
        pdf.close()


def main():
    parser = argparse.ArgumentParser(description='Extrai title_es/subtitle_es dos PDFs')
    parser.add_argument('--slug', required=True, help='Seminário (ex: sdnne10, sdbr15)')
    parser.add_argument('--dry-run', action='store_true', help='Mostrar sem alterar o banco')
    parser.add_argument('--force', action='store_true', help='Re-extrair mesmo se já existe')
    parser.add_argument('--also-en', action='store_true', help='Também extrair/atualizar title_en')
    args = parser.parse_args()

    slug = args.slug

    # Determinar diretório dos PDFs
    if slug.startswith('sdbr'):
        pdf_dir = f"nacionais/{slug}/pdfs"
        extract_fn = extract_titles_sdbr15
    elif slug.startswith('sdnne'):
        pdf_dir = f"regionais/nne/{slug}/pdfs"
        extract_fn = extract_titles_sdnne10
    else:
        print(f"Slug não suportado: {slug}")
        sys.exit(1)

    if not os.path.isdir(pdf_dir):
        print(f"Diretório não encontrado: {pdf_dir}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Buscar artigos do seminário
    articles = cur.execute(
        "SELECT id, title, title_en, subtitle_en, title_es, subtitle_es "
        "FROM articles WHERE seminar_slug = ? ORDER BY id",
        (slug,)
    ).fetchall()

    stats = {'extracted': 0, 'skipped_exists': 0, 'skipped_no_pdf': 0, 'failed': 0}

    for art in articles:
        art_id = art['id']
        pdf_path = os.path.join(pdf_dir, f"{art_id}.pdf")

        if not os.path.exists(pdf_path):
            stats['skipped_no_pdf'] += 1
            continue

        has_es = art['title_es'] and art['title_es'].strip()
        has_en = art['title_en'] and art['title_en'].strip()

        if has_es and not args.force and not (args.also_en and not has_en):
            stats['skipped_exists'] += 1
            continue

        result = extract_fn(pdf_path)

        if not result or (not result['title_es'] and not result['title_en']):
            stats['failed'] += 1
            print(f"  {art_id}: FALHOU (sem títulos EN/ES detectados)")
            continue

        # Montar updates
        updates = {}
        if result['title_es'] and (not has_es or args.force):
            updates['title_es'] = result['title_es']
            updates['subtitle_es'] = result['subtitle_es']

        if args.also_en and result['title_en'] and (not has_en or args.force):
            updates['title_en'] = result['title_en']
            updates['subtitle_en'] = result['subtitle_en']

        if not updates:
            stats['skipped_exists'] += 1
            continue

        stats['extracted'] += 1

        # Print
        if 'title_es' in updates:
            es_display = updates['title_es']
            if updates.get('subtitle_es'):
                es_display += f": {updates['subtitle_es']}"
            print(f"  {art_id} [ES]: {es_display}")

        if 'title_en' in updates:
            en_display = updates['title_en']
            if updates.get('subtitle_en'):
                en_display += f": {updates['subtitle_en']}"
            print(f"  {art_id} [EN]: {en_display}")

        if not args.dry_run:
            set_clause = ', '.join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [art_id]
            cur.execute(f"UPDATE articles SET {set_clause} WHERE id = ?", values)

    try:
        if not args.dry_run:
            conn.commit()
    finally:
        conn.close()

    print(f"\n{'[DRY-RUN] ' if args.dry_run else ''}Resultado:")
    print(f"  Extraídos: {stats['extracted']}")
    print(f"  Já existentes (skip): {stats['skipped_exists']}")
    print(f"  Sem PDF: {stats['skipped_no_pdf']}")
    print(f"  Falhou: {stats['failed']}")


if __name__ == '__main__':
    main()
