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


def read_plumber_blocks(fontes_dir, file_name):
    """Lê os blocos do plumber JSONL. Retorna lista de dicts ou None."""
    art_id = file_name.replace('.pdf', '')
    jsonl_path = os.path.join(fontes_dir, art_id + '.jsonl')
    if not os.path.exists(jsonl_path):
        return None
    blocks = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            blocks.append(json.loads(line))
    return blocks


def extract_en_from_plumber(blocks):
    """Extrai abstract_en, keywords_en, title_en, subtitle_en dos blocos plumber.

    Usa a estrutura dos blocos (role, page, font_size) em vez de busca por linhas.
    Retorna dict com campos extraídos (chaves só presentes se encontrados).
    """
    result = {}

    # --- Localizar blocos com marcadores EN ---
    abstract_en_parts = []
    keywords_en_raw = None
    title_en_candidates = []

    # Índices de marcadores PT para delimitar a zona EN
    kw_pt_block_idx = None
    abstract_marker_idx = None

    for i, b in enumerate(blocks):
        text = b['text']
        # Keywords PT marker
        if kw_pt_block_idx is None:
            if re.search(r'Palavras[\s-]*[Cc]haves?\s*:', text, re.IGNORECASE):
                kw_pt_block_idx = i

        # Abstract EN marker — heading block or inline
        if abstract_marker_idx is None:
            if b['role'] == 'heading' and re.match(r'\s*Abstract\s*:?\s*$', text, re.IGNORECASE):
                abstract_marker_idx = i
            elif re.search(r'(?:^|\n)\s*Abstract\s*:', text, re.IGNORECASE):
                abstract_marker_idx = i

    # --- abstract_en ---
    if abstract_marker_idx is not None:
        b = blocks[abstract_marker_idx]
        text = b['text']

        # Caso 1: heading "Abstract" — conteúdo nos blocos seguintes
        if b['role'] == 'heading' and re.match(r'\s*Abstract\s*:?\s*$', text, re.IGNORECASE):
            for j in range(abstract_marker_idx + 1, min(len(blocks), abstract_marker_idx + 5)):
                nb = blocks[j]
                if nb['role'] in ('abstract', 'small', 'body', 'footnote'):
                    nt = nb['text'].strip()
                    # Parar se atingir keywords_en
                    if re.match(r'\s*Key[\s-]*[Ww]ords?\s*:', nt, re.IGNORECASE):
                        break
                    # Parar se atingir heading de seção (Introdução, etc.)
                    if nb['role'] == 'heading' and nb['page'] > b['page']:
                        break
                    abstract_en_parts.append(nt)
                    # Verificar se tem keywords embutidas no final
                    m_kw = re.search(r'\n\s*Key[\s-]*[Ww]ords?\s*:', nt)
                    if m_kw:
                        abstract_en_parts[-1] = nt[:m_kw.start()].strip()
                        keywords_en_raw = nt[m_kw.end():].strip()
                        break
                elif nb['role'] == 'heading':
                    break

        # Caso 2: "Abstract:" inline no bloco
        else:
            m = re.search(r'Abstract\s*:\s*(.+)', text, re.DOTALL)
            if m:
                content = m.group(1).strip()
                # Pode ter keywords_en embutidas
                m_kw = re.search(r'\n\s*Key[\s-]*[Ww]ords?\s*:', content)
                if m_kw:
                    abstract_en_parts.append(content[:m_kw.start()].strip())
                    keywords_en_raw = content[m_kw.end():].strip()
                else:
                    abstract_en_parts.append(content)

            # Verificar blocos adjacentes (continuation em role=footnote/small)
            for j in range(abstract_marker_idx + 1, min(len(blocks), abstract_marker_idx + 4)):
                nb = blocks[j]
                if nb['page'] != b['page'] and nb['page'] > b['page'] + 1:
                    break
                if nb['role'] in ('footnote', 'small', 'abstract'):
                    nt = nb['text'].strip()
                    # Rejeitar se parece PT
                    if looks_like_pt(nt[:100]):
                        break
                    if re.match(r'\s*Key[\s-]*[Ww]ords?\s*:', nt, re.IGNORECASE):
                        keywords_en_raw = re.sub(r'^\s*Key[\s-]*[Ww]ords?\s*:\s*', '', nt,
                                                 flags=re.IGNORECASE).strip()
                        break
                    # Se parece continuação EN
                    if not has_pt_accents(nt[:100], 2):
                        abstract_en_parts.append(nt)
                elif nb['role'] in ('heading', 'body'):
                    break

    if abstract_en_parts:
        ae = ' '.join(abstract_en_parts)
        ae = re.sub(r'\n', ' ', ae).strip()
        ae = re.sub(r'  +', ' ', ae)
        # Strip label residual
        ae = re.sub(r'^Abstract\s*:?\s*', '', ae, flags=re.IGNORECASE).strip()
        # Strip keywords no final
        m_kw = re.search(r'\s*Key[\s-]*[Ww]ords?\s*:.*$', ae, re.IGNORECASE)
        if m_kw:
            if keywords_en_raw is None:
                keywords_en_raw = ae[m_kw.start():].strip()
                keywords_en_raw = re.sub(r'^\s*Key[\s-]*[Ww]ords?\s*:\s*', '', keywords_en_raw,
                                         flags=re.IGNORECASE).strip()
            ae = ae[:m_kw.start()].strip()
        if len(ae) > 50:
            result['abstract_en'] = ae

    # --- keywords_en ---
    if keywords_en_raw is None:
        # Buscar em todos os blocos
        for b in blocks:
            m = re.search(r'Key[\s-]*[Ww]ords?\s*:\s*(.+?)(?:\n|$)', b['text'])
            if m:
                keywords_en_raw = m.group(1).strip()
                break

    if keywords_en_raw:
        keywords_en_raw = keywords_en_raw.rstrip('.')
        if ';' in keywords_en_raw:
            kw_list = [k.strip().rstrip('.') for k in keywords_en_raw.split(';') if k.strip()]
        else:
            kw_list = [k.strip().rstrip('.') for k in keywords_en_raw.split(',') if k.strip()]
        kw_list = [k for k in kw_list if len(k) > 1]
        if kw_list:
            result['keywords_en'] = json.dumps(kw_list, ensure_ascii=False)

    # --- title_en ---
    # Procurar entre keywords_PT e Abstract: linhas EN (não-PT) em blocos heading/small
    if kw_pt_block_idx is not None and abstract_marker_idx is not None:
        for i in range(kw_pt_block_idx + 1, abstract_marker_idx):
            b = blocks[i]
            text = b['text'].strip()
            if not text or len(text) < 3:
                continue
            # Pular números de página
            if re.match(r'^\d{1,3}$', text):
                continue
            # Pular continuação de keywords PT (texto curto com vírgulas)
            if len(text) < 40 and ',' in text and not is_all_caps(text):
                continue
            # Verificar se não é PT
            if looks_like_pt(text):
                continue
            if is_likely_title_line(text):
                title_en_candidates.append(text)

    # Padrão B: título ALL CAPS logo após heading "Abstract"
    if not title_en_candidates and abstract_marker_idx is not None:
        b = blocks[abstract_marker_idx]
        if b['role'] == 'heading' and re.match(r'\s*Abstract\s*:?\s*$', b['text'], re.IGNORECASE):
            for j in range(abstract_marker_idx + 1, min(len(blocks), abstract_marker_idx + 5)):
                nb = blocks[j]
                text = nb['text'].strip()
                if not text:
                    continue
                if re.match(r'^\d{1,3}$', text):
                    continue
                if is_all_caps(text) and not has_pt_accents(text, 2):
                    title_en_candidates.append(text)
                else:
                    break

    if title_en_candidates:
        title_raw = ' '.join(title_en_candidates)
        title_raw = re.sub(r'\s+', ' ', title_raw).strip()
        title_en, subtitle_en = split_title_subtitle(title_raw)
        if title_en:
            result['title_en'] = title_en
            if subtitle_en:
                result['subtitle_en'] = subtitle_en

    return result


def _has_relevant_files(path, ext):
    """Verifica se o diretório tem arquivos com a extensão relevante."""
    try:
        return any(f.endswith(ext) for f in os.listdir(path))
    except OSError:
        return False


def find_fontes_dir(slug):
    """Localiza o diretório fontes/ para um seminário.

    Retorna (path, tipo) onde tipo é 'txt' (pdftotext) ou 'plumber' (jsonl).
    Hierarquia: fontes/ com .txt > fontes_plumber/ com .jsonl.
    """
    search_dirs = [os.path.join(BASE_DIR, 'nacionais', slug)]
    for grupo in ['nne', 'se', 'sul']:
        search_dirs.append(os.path.join(BASE_DIR, 'regionais', grupo, slug))

    for base in search_dirs:
        # Preferir fontes/ .txt (mais completo)
        fontes_path = os.path.join(base, 'fontes')
        if os.path.isdir(fontes_path) and _has_relevant_files(fontes_path, '.txt'):
            return fontes_path, 'txt'
        # Fallback: fontes_plumber/ .jsonl
        plumber_path = os.path.join(base, 'fontes_plumber')
        if os.path.isdir(plumber_path) and _has_relevant_files(plumber_path, '.jsonl'):
            return plumber_path, 'plumber'

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
        fname = file_name or f'{art_id}.pdf'
        updates = {}

        if fontes_tipo == 'plumber':
            # Extração estruturada do plumber
            plumber_blocks = read_plumber_blocks(fontes_dir, fname)
            if not plumber_blocks:
                print(f'{art_id:<15} {"—":<60} {"—":<5} sem fonte')
                stats['title_failed'] += 1
                continue

            extracted = extract_en_from_plumber(plumber_blocks)
            if not extracted:
                print(f'{art_id:<15} {"—":<60} {"—":<5} sem seção EN')
                stats['no_en_section'] += 1
                continue

            # title_en
            if old_title_en and not force:
                stats['title_existing'] += 1
                status_title = 'existente'
            elif 'title_en' in extracted:
                updates['title_en'] = extracted['title_en']
                if 'subtitle_en' in extracted:
                    updates['subtitle_en'] = extracted['subtitle_en']
                    stats['subtitle_extracted'] += 1
                stats['title_extracted'] += 1
                status_title = 'NOVO'
            else:
                stats['title_failed'] += 1
                status_title = 'falhou'

            # abstract_en
            if not only_title:
                if old_abstract_en and not force:
                    stats['abstract_existing'] += 1
                elif 'abstract_en' in extracted:
                    updates['abstract_en'] = extracted['abstract_en']
                    stats['abstract_extracted'] += 1

            # keywords_en
            if not only_title:
                if old_kw_en and old_kw_en != '[]' and not force:
                    stats['keywords_existing'] += 1
                elif 'keywords_en' in extracted:
                    updates['keywords_en'] = extracted['keywords_en']
                    stats['keywords_extracted'] += 1
        else:
            # Extração por linhas (fontes/ .txt)
            text = read_fontes_text(fontes_dir, fontes_tipo, fname)
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

            # title_en
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

            # abstract_en
            if not only_title:
                if old_abstract_en and not force:
                    stats['abstract_existing'] += 1
                else:
                    abstract_en = extract_abstract_en(lines)
                    if abstract_en:
                        updates['abstract_en'] = abstract_en
                        stats['abstract_extracted'] += 1

            # keywords_en
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
