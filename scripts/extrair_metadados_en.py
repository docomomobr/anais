#!/usr/bin/env python3
"""
Extrai metadados em inglês (title_en, subtitle_en, abstract_en, keywords_en)
dos arquivos .txt em fontes/.

O title_en é extraído da região entre as keywords PT e o marcador "Abstract".
Padrão A: linhas entre keywords_PT e "Abstract" que não contêm acentos PT.
Padrão B: linhas ALL CAPS logo após o header "Abstract" (título embutido).
Padrão C: linhas acima do "Abstract" (quando não há keywords_PT).

Uso:
    python3 scripts/extrair_metadados_en.py --slug sdbr08 --dry-run
    python3 scripts/extrair_metadados_en.py --slug sdbr08
    python3 scripts/extrair_metadados_en.py --slug sdbr08 --only-title
    python3 scripts/extrair_metadados_en.py --slug sdbr08 --force
"""

import argparse
import json
import os
import re
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')

# Regex para detectar caracteres acentuados do português
PT_ACCENT_RE = re.compile(r'[àáâãéêíóôõúüçÀÁÂÃÉÊÍÓÔÕÚÜÇ]')

# Palavras funcionais PT comuns sem acentos (para detectar texto PT)
PT_FUNCTION_WORDS = {
    'de', 'em', 'e', 'ou', 'com', 'se', 'que', 'por', 'mais', 'mas',
    'do', 'da', 'dos', 'das', 'no', 'na', 'nos', 'nas', 'ao', 'aos',
    'pelo', 'pela', 'pelos', 'pelas', 'um', 'uma', 'uns', 'umas',
    'como', 'para', 'entre', 'sobre', 'desde', 'quanto', 'quando',
    'onde', 'porque', 'pois', 'embora', 'ainda', 'assim', 'bem',
    'seu', 'sua', 'seus', 'suas', 'este', 'esta', 'esse', 'essa',
    'aquele', 'aquela', 'outro', 'outra', 'outros', 'outras',
    'muito', 'muita', 'muitos', 'muitas', 'todo', 'toda', 'todos',
    'cada', 'neste', 'nesta', 'deste', 'desta', 'mesmo', 'mesma',
    'sendo', 'sido', 'foram', 'seria', 'pode', 'podem',
    'deve', 'devem', 'dessa', 'desse', 'dessas', 'desses',
    'nesse', 'nessa', 'nesses', 'nessas', 'algumas', 'alguns',
}

# Marcadores de abstract EN
ABSTRACT_MARKERS = [
    re.compile(r'^\s*ABSTRACT\s*:?\s*$', re.IGNORECASE),
    re.compile(r'^\s*Abstract\s*:?\s*$'),
    re.compile(r'^\s*ABSTRACT\s*:', re.IGNORECASE),
]

# Marcadores de keywords PT (fim da seção PT) — com e sem colon
KW_PT_MARKERS = [
    re.compile(r'^\s*Palavras[\s-]*[Cc]haves?\s*:', re.IGNORECASE),
    re.compile(r'^\s*PALAVRAS[\s-]*CHAVES?\s*:', re.IGNORECASE),
    re.compile(r'^\s*Palavras[\s-]*[Cc]haves?\s*$', re.IGNORECASE),
    re.compile(r'^\s*PALAVRAS[\s-]*CHAVES?\s*$', re.IGNORECASE),
    # Espanhol
    re.compile(r'^\s*Palabras[\s-]*[Cc]laves?\s*:', re.IGNORECASE),
]

# Marcadores de keywords EN
KW_EN_MARKERS = [
    re.compile(r'^\s*Key[\s-]*[Ww]ords?\s*:', re.IGNORECASE),
    re.compile(r'^\s*KEY[\s-]*WORDS?\s*:', re.IGNORECASE),
]

# Padrões de início de corpo de texto (falsos positivos para título)
BODY_TEXT_PATTERNS = re.compile(
    r'^\s*(This paper|This article|This work|This study|The objective|The aim|'
    r'The present|The purpose|The goal|The text|The work|In this|We analyze|'
    r'We examine|Post-war|When thinking|On the ocasion|Considering|'
    r'There is|It was|It is|One of)', re.IGNORECASE
)


def find_fontes_dir(slug):
    """Localiza o diretório fontes/ para um seminário.

    Retorna (path, tipo) onde tipo é 'txt' (pdftotext) ou 'plumber' (jsonl).
    Hierarquia: fontes/ > fontes_plumber/.
    """
    # Nacionais
    for subdir, tipo in [('fontes', 'txt'), ('fontes_plumber', 'plumber')]:
        path = os.path.join(BASE_DIR, 'nacionais', slug, subdir)
        if os.path.isdir(path):
            return path, tipo
    # Regionais
    for grupo in ['nne', 'se', 'sul']:
        for subdir, tipo in [('fontes', 'txt'), ('fontes_plumber', 'plumber')]:
            path = os.path.join(BASE_DIR, 'regionais', grupo, slug, subdir)
            if os.path.isdir(path):
                return path, tipo
    return None, None


def read_fontes_text(fontes_dir, fontes_tipo, file_name):
    """Lê o texto de um artigo a partir de fontes/ (txt) ou fontes_plumber/ (jsonl).

    Retorna o texto como string, ou None se o arquivo não existe.
    """
    art_id = file_name.replace('.pdf', '')

    if fontes_tipo == 'txt':
        txt_name = file_name.replace('.pdf', '.txt')
        txt_path = os.path.join(fontes_dir, txt_name)
        if not os.path.exists(txt_path):
            return None
        with open(txt_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    elif fontes_tipo == 'plumber':
        jsonl_path = os.path.join(fontes_dir, art_id + '.jsonl')
        if not os.path.exists(jsonl_path):
            return None
        # Converter blocos do plumber em texto contínuo (preservando quebras de linha)
        lines = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                block = json.loads(line)
                text = block.get('text', '').strip()
                if text:
                    lines.append(text)
        return '\n'.join(lines)

    return None


def has_pt_accents(text, threshold=2):
    """Retorna True se o texto tem >= threshold caracteres acentuados PT."""
    return len(PT_ACCENT_RE.findall(text)) >= threshold


def looks_like_pt(text):
    """Heurística para detectar texto em português, mesmo sem acentos."""
    if has_pt_accents(text, 2):
        return True
    # Contar palavras funcionais PT
    words = text.lower().split()
    if not words:
        return False
    pt_count = sum(1 for w in words if w.strip('.,;:()[]') in PT_FUNCTION_WORDS)
    # Se >= 25% das palavras são funcionais PT, provavelmente é PT
    return pt_count >= max(2, len(words) * 0.25)


def is_likely_title_line(line):
    """Verifica se uma linha parece ser parte de um título EN (não corpo de texto)."""
    line = line.strip()
    if not line:
        return False
    if BODY_TEXT_PATTERNS.match(line):
        return False
    if len(line) > 200:
        return False
    # Rejeitar linhas que são claramente continuação de keywords
    if re.match(r'^[a-záéíóúàâêôãõüç,;.\s-]+$', line, re.IGNORECASE) and len(line) < 40:
        return False
    return True


def is_abstract_marker(line):
    """Verifica se a linha é um marcador de Abstract."""
    for pat in ABSTRACT_MARKERS:
        if pat.search(line):
            return True
    return False


def is_kw_pt_marker(line):
    """Verifica se a linha é um marcador de keywords PT."""
    for pat in KW_PT_MARKERS:
        if pat.search(line):
            return True
    return False


def is_kw_en_marker(line):
    """Verifica se a linha é um marcador de keywords EN."""
    for pat in KW_EN_MARKERS:
        if pat.search(line):
            return True
    return False


def is_all_caps(line):
    """Verifica se uma linha é ALL CAPS (letras > 3 e todas maiúsculas)."""
    alpha = re.sub(r'[^a-zA-Z]', '', line)
    return len(alpha) > 3 and alpha == alpha.upper()


def extract_title_en(lines):
    """Extrai título EN de uma lista de linhas do texto.

    Padrão A: linhas entre keywords_PT e Abstract que não são PT.
    Padrão B: linhas ALL CAPS após header "ABSTRACT" (quando está sozinho na linha).
    Padrão C: linhas acima do Abstract (quando não há keywords_PT).

    Retorna (title_en, subtitle_en) ou (None, None).
    """
    kw_pt_pos = None
    abstract_pos = None
    abstract_inline = False

    for i, line in enumerate(lines):
        if kw_pt_pos is None and is_kw_pt_marker(line):
            kw_pt_pos = i
        if abstract_pos is None and is_abstract_marker(line):
            abstract_pos = i
            cleaned = re.sub(r'^\s*abstract\s*:?\s*', '', line, flags=re.IGNORECASE).strip()
            if len(cleaned) > 30:
                abstract_inline = True

    if abstract_pos is None:
        return None, None

    # Padrão A: coletar linhas entre keywords_PT e Abstract
    if kw_pt_pos is not None and abstract_pos > kw_pt_pos:
        candidate_lines = []
        # Pular linhas que são continuação das keywords PT
        # (a keywords PT pode ter wrapping, pular até a próxima linha vazia)
        start = kw_pt_pos + 1
        in_kw_continuation = True
        for i in range(start, abstract_pos):
            line = lines[i].strip()
            if not line:
                in_kw_continuation = False
                continue
            if in_kw_continuation:
                # Linhas curtas logo após keywords_PT são continuação
                if len(line) < 80 and not is_all_caps(line):
                    continue
                in_kw_continuation = False
            # Pular números de página isolados e marcadores tipo "-1-"
            if re.match(r'^[\s\-]*\d{1,3}[\s\-]*$', line):
                continue
            # Pular se parece texto PT
            if looks_like_pt(line):
                continue
            # Pular marcadores de keywords EN
            if is_kw_en_marker(lines[i]):
                continue
            if is_likely_title_line(line):
                candidate_lines.append(line)

        if candidate_lines:
            title_raw = ' '.join(candidate_lines)
            title_raw = re.sub(r'\s+', ' ', title_raw).strip()
            return split_title_subtitle(title_raw)

    # Padrão B: título ALL CAPS após header "ABSTRACT" em linha separada
    # Só aceitar linhas ALL CAPS — mixed case após Abstract é corpo de texto
    if abstract_pos is not None and not abstract_inline:
        candidate_lines = []
        for i in range(abstract_pos + 1, min(len(lines), abstract_pos + 8)):
            line = lines[i].strip()
            if not line:
                if candidate_lines:
                    break
                continue
            if re.match(r'^\d{1,3}$', line):
                continue
            if is_all_caps(line) and not has_pt_accents(line, 2):
                candidate_lines.append(line)
            else:
                break  # primeira linha não-CAPS = fim do título

        if candidate_lines:
            title_raw = ' '.join(candidate_lines)
            title_raw = re.sub(r'\s+', ' ', title_raw).strip()
            return split_title_subtitle(title_raw)

    # Padrão C: linhas acima do Abstract (quando não há keywords_PT)
    if abstract_pos is not None and kw_pt_pos is None:
        candidate_lines = []
        for i in range(abstract_pos - 1, max(abstract_pos - 6, -1), -1):
            if i < 0:
                break
            line = lines[i].strip()
            if not line:
                if candidate_lines:
                    break
                continue
            if looks_like_pt(line):
                break
            if re.match(r'^\d{1,3}$', line):
                continue
            if is_likely_title_line(line):
                candidate_lines.insert(0, line)
            else:
                break

        if candidate_lines:
            title_raw = ' '.join(candidate_lines)
            title_raw = re.sub(r'\s+', ' ', title_raw).strip()
            return split_title_subtitle(title_raw)

    return None, None


def split_title_subtitle(title_raw):
    """Separa título e subtítulo EN por ': ' ou ' — ' ou ' – '.

    Retorna (title, subtitle) ou (title, None).
    """
    for sep in [': ', ' — ', ' – ']:
        if sep in title_raw:
            parts = title_raw.split(sep, 1)
            title = parts[0].strip()
            subtitle = parts[1].strip()
            if title and subtitle:
                return title, subtitle

    return title_raw, None


def extract_abstract_en(lines):
    """Extrai abstract EN do texto.

    Procura entre o marcador Abstract e o marcador Keywords EN ou fim da seção.
    Retorna o texto do abstract ou None.
    """
    abstract_pos = None
    abstract_text_start = None

    for i, line in enumerate(lines):
        if abstract_pos is None and is_abstract_marker(line):
            abstract_pos = i
            cleaned = re.sub(r'^\s*abstract\s*:?\s*', '', line, flags=re.IGNORECASE).strip()
            if cleaned:
                abstract_text_start = i
            else:
                abstract_text_start = i + 1
            break

    if abstract_pos is None:
        return None

    # Se Pattern B encontrou título ALL CAPS após Abstract, pular essas linhas
    skip_until_body = abstract_text_start
    for i in range(abstract_text_start, min(len(lines), abstract_pos + 8)):
        line = lines[i].strip()
        if not line:
            continue
        if re.match(r'^\d{1,3}$', line):
            continue
        if is_all_caps(line) and not has_pt_accents(line, 2):
            skip_until_body = i + 1
        else:
            break

    # Coletar linhas do abstract
    abstract_lines = []
    empty_count = 0
    start = max(abstract_text_start, skip_until_body)
    for i in range(start, min(len(lines), abstract_pos + 50)):
        line = lines[i]
        stripped = line.strip()

        if is_kw_en_marker(line):
            break

        if not stripped:
            empty_count += 1
            if empty_count >= 2 and abstract_lines:
                break
            continue
        else:
            empty_count = 0

        if re.match(r'^\d{1,3}$', stripped):
            continue

        if i == abstract_text_start and abstract_text_start == abstract_pos:
            text = re.sub(r'^\s*abstract\s*:?\s*', '', line, flags=re.IGNORECASE)
            abstract_lines.append(text.strip())
        else:
            abstract_lines.append(stripped)

    if abstract_lines:
        text = ' '.join(abstract_lines)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    return None


def extract_keywords_en(lines):
    """Extrai keywords EN do texto.

    Retorna lista de keywords ou None.
    """
    for i, line in enumerate(lines):
        if is_kw_en_marker(line):
            text = re.sub(r'^\s*key[\s-]*words?\s*:?\s*', '', line, flags=re.IGNORECASE).strip()
            for j in range(i + 1, min(len(lines), i + 5)):
                next_line = lines[j].strip()
                if not next_line:
                    break
                if re.match(r'^\d{1,3}$', next_line):
                    break
                if len(next_line) > 100:
                    break
                text += ' ' + next_line

            # Separar por ; ou , ou –
            if ';' in text:
                keywords = [k.strip().rstrip('.') for k in text.split(';') if k.strip()]
            elif ' – ' in text:
                keywords = [k.strip().rstrip('.') for k in text.split(' – ') if k.strip()]
            else:
                keywords = [k.strip().rstrip('.') for k in text.split(',') if k.strip()]

            keywords = [k for k in keywords if len(k) > 1]
            return keywords if keywords else None

    return None


def process_seminar(conn, slug, dry_run=False, force=False, only_title=False):
    """Processa todos os artigos de um seminário."""
    fontes_dir, fontes_tipo = find_fontes_dir(slug)
    if not fontes_dir:
        print(f'ERRO: diretório fontes/ e fontes_plumber/ não encontrados para {slug}')
        return
    print(f'Fonte: {fontes_dir} ({fontes_tipo})')

    rows = conn.execute(
        '''SELECT id, file, title_en, subtitle_en, abstract_en, keywords_en
           FROM articles WHERE seminar_slug = ? ORDER BY id''',
        (slug,)
    ).fetchall()

    stats = {
        'total': len(rows),
        'title_extracted': 0,
        'title_existing': 0,
        'title_failed': 0,
        'subtitle_extracted': 0,
        'abstract_extracted': 0,
        'abstract_existing': 0,
        'keywords_extracted': 0,
        'keywords_existing': 0,
        'no_en_section': 0,
    }

    print(f'\n=== {slug}: {len(rows)} artigos ===\n')
    print(f'{"ID":<15} {"title_en":<60} {"sub":<5} {"status"}')
    print('-' * 100)

    for art_id, file_name, old_title_en, old_subtitle_en, old_abstract_en, old_kw_en in rows:
        text = read_fontes_text(fontes_dir, fontes_tipo, file_name or f'{art_id}.pdf')

        if not text:
            print(f'{art_id:<15} {"—":<60} {"—":<5} sem fonte')
            stats['title_failed'] += 1
            continue

        lines = text.split('\n')

        has_abstract = any(is_abstract_marker(l) for l in lines)
        if not has_abstract:
            print(f'{art_id:<15} {"—":<60} {"—":<5} sem seção EN')
            stats['no_en_section'] += 1
            continue

        updates = {}

        # --- title_en ---
        if old_title_en and not force:
            stats['title_existing'] += 1
            status_title = 'existente'
        else:
            title_en, subtitle_en = extract_title_en(lines)
            if title_en:
                updates['title_en'] = title_en
                if subtitle_en:
                    updates['subtitle_en'] = subtitle_en
                    stats['subtitle_extracted'] += 1
                stats['title_extracted'] += 1
                status_title = 'NOVO'
            else:
                stats['title_failed'] += 1
                status_title = 'falhou'

        # --- abstract_en ---
        if not only_title:
            if old_abstract_en and not force:
                stats['abstract_existing'] += 1
            else:
                abstract_en = extract_abstract_en(lines)
                if abstract_en:
                    updates['abstract_en'] = abstract_en
                    stats['abstract_extracted'] += 1

        # --- keywords_en ---
        if not only_title:
            if old_kw_en and old_kw_en != '[]' and not force:
                stats['keywords_existing'] += 1
            else:
                kw_en = extract_keywords_en(lines)
                if kw_en:
                    updates['keywords_en'] = json.dumps(kw_en, ensure_ascii=False)
                    stats['keywords_extracted'] += 1

        # Mostrar resultado
        title_display = updates.get('title_en', old_title_en or '—')
        if len(title_display) > 57:
            title_display = title_display[:57] + '...'
        sub_flag = 'sub' if updates.get('subtitle_en') or old_subtitle_en else '—'
        print(f'{art_id:<15} {title_display:<60} {sub_flag:<5} {status_title}')

        # Aplicar ao banco
        if updates and not dry_run:
            set_clauses = ', '.join(f'{k} = ?' for k in updates)
            values = list(updates.values()) + [art_id]
            conn.execute(f'UPDATE articles SET {set_clauses} WHERE id = ?', values)

    if not dry_run:
        conn.commit()

    # Resumo
    print()
    print(f'--- Resumo {slug} {"(dry-run)" if dry_run else ""} ---')
    print(f'Total artigos:    {stats["total"]}')
    print(f'Sem seção EN:     {stats["no_en_section"]}')
    print(f'title_en:         {stats["title_extracted"]} extraídos, '
          f'{stats["title_existing"]} já existentes, {stats["title_failed"]} falharam')
    print(f'subtitle_en:      {stats["subtitle_extracted"]} extraídos')
    if not only_title:
        print(f'abstract_en:      {stats["abstract_extracted"]} extraídos, '
              f'{stats["abstract_existing"]} já existentes')
        print(f'keywords_en:      {stats["keywords_extracted"]} extraídos, '
              f'{stats["keywords_existing"]} já existentes')
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Extrair metadados EN (title_en, subtitle_en, abstract_en, keywords_en)')
    parser.add_argument('--slug', required=True, help='Seminário a processar')
    parser.add_argument('--dry-run', action='store_true', help='Apenas mostrar, não alterar o banco')
    parser.add_argument('--force', action='store_true',
                        help='Re-extrair mesmo se o campo já tem valor')
    parser.add_argument('--only-title', action='store_true',
                        help='Extrair apenas title_en/subtitle_en (skip abstract/keywords)')
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    process_seminar(conn, args.slug, dry_run=args.dry_run, force=args.force,
                    only_title=args.only_title)
    conn.close()


if __name__ == '__main__':
    main()
