#!/usr/bin/env python3
"""
Extrai metadados (abstract, keywords, referências) de arquivos editáveis
(.doc, .docx, .odt, .rtf).

Fonte primária quando arquivos editáveis estão disponíveis — preferível ao
pdfplumber. Converte para .docx via LibreOffice e lê com python-docx
(preserva estilos de parágrafo).

Uso:
    python3 scripts/extrair_metadados_doc.py --slug sdpr01                # diagnóstico
    python3 scripts/extrair_metadados_doc.py --slug sdpr01 --apply        # atualiza o banco
    python3 scripts/extrair_metadados_doc.py --slug sdpr01 --verbose      # detalhes
    python3 scripts/extrair_metadados_doc.py --slug sdpr01 --only 001,005 # artigos específicos
"""

import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

try:
    from docx import Document
except ImportError:
    print('ERRO: python-docx não instalado. Rode: pip install python-docx')
    sys.exit(1)

DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(DIR), 'anais.db')

EDITABLE_EXTS = {'.doc', '.docx', '.odt', '.rtf'}

# ---------------------------------------------------------------------------
# Marcadores de seção (case-insensitive, no início do parágrafo)
# ---------------------------------------------------------------------------

ABSTRACT_PT_RE = re.compile(
    r'^(?:RESUMO|Resumo)\s*[:\.\-—]?\s*$', re.IGNORECASE)
ABSTRACT_PT_INLINE_RE = re.compile(
    r'^(?:RESUMO|Resumo)\s*[:\.\-—]\s*(.+)', re.IGNORECASE | re.DOTALL)

ABSTRACT_ES_RE = re.compile(
    r'^(?:RESUMEN|Resumen)\s*[:\.\-—]?\s*$', re.IGNORECASE)
ABSTRACT_ES_INLINE_RE = re.compile(
    r'^(?:RESUMEN|Resumen)\s*[:\.\-—]\s*(.+)', re.IGNORECASE | re.DOTALL)

ABSTRACT_EN_RE = re.compile(
    r'^(?:ABSTRACT|Abstract)\s*[:\.\-—]?\s*$', re.IGNORECASE)
ABSTRACT_EN_INLINE_RE = re.compile(
    r'^(?:ABSTRACT|Abstract)\s*[:\.\-—]\s*(.+)', re.IGNORECASE | re.DOTALL)

# Label bilíngue: "Palavras-chave / key words: kw_pt, ... / kw_en, ..."
KW_BILINGUAL_RE = re.compile(
    r'^(?:Palavras[- ]?[Cc]haves?|PALAVRAS[- ]?CHAVES?)\s*/\s*'
    r'(?:key[\s\-]?words?)\s*[:\.]?\s*(.*)',
    re.IGNORECASE | re.DOTALL)
KW_PT_RE = re.compile(
    r'^(?:Palavras[- ]?[Cc]haves?|PALAVRAS[- ]?CHAVES?)\s*[:\.]?\s*(.*)',
    re.IGNORECASE | re.DOTALL)
KW_EN_RE = re.compile(
    r'^(?:Key[\s\-]?[Ww]ords?|KEY[\s\-]?WORDS?)\s*[:\.]?\s*(.*)',
    re.IGNORECASE | re.DOTALL)
KW_ES_RE = re.compile(
    r'^(?:Palabras[- ]?[Cc]laves?|PALABRAS[- ]?CLAVES?)\s*[:\.]?\s*(.*)',
    re.IGNORECASE | re.DOTALL)

# Padrão para separar keywords PT / EN na mesma linha
# Ex: "Palavras-chave / key words: kw1, kw2 / kw_en1, kw_en2"
KW_PT_EN_SPLIT_RE = re.compile(
    r'\s*/\s*(?:key[\s\-]?words?)\s*[:\.]?\s*', re.IGNORECASE)

REFS_RE = re.compile(
    r'^(?:REFERÊNCIAS|Referências|REFERENCIAS|Referencias|'
    r'REFERÊNCIAS\s+BIBLIOGRÁFICAS|Referências\s+[Bb]ibliográficas|'
    r'BIBLIOGRAFIA|Bibliografia|BIBLIOGRAFÍA|Bibliografía|'
    r'REFERENCES|References|BIBLIOGRAPHIC\s+REFERENCES)\s*[:\.]?\s*$',
    re.IGNORECASE)

# Marcadores que indicam fim de seção (início de novo conteúdo)
BODY_SECTION_RE = re.compile(
    r'^(?:INTRODUÇÃO|Introdução|INTRODUCTION|Introduction|'
    r'CONSIDERAÇÕES\s+FINAIS|Considerações\s+[Ff]inais|'
    r'CONCLUSÃO|Conclusão|CONCLUSION|Conclusion|'
    r'NOTAS?|Notes?|NOTAS?\s+DE\s+RODAPÉ|'
    r'AGRADECIMENTOS|Agradecimentos|ACKNOWLEDGEMENTS|'
    r'ANEXOS?|Anexos?|APÊNDICE|Apêndice|'
    r'\d+[\.\s]+\w)',  # seções numeradas: "1. Introdução", "1 INTRODUÇÃO"
    re.IGNORECASE)

# Separa keywords
KW_SEP_RE = re.compile(r'\s*[;]\s*')
KW_SEP_COMMA_RE = re.compile(r'\s*[,]\s*')

# Padrão para início de referência ABNT
ABNT_AUTHOR_RE = re.compile(
    r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑÜ][A-ZÁÉÍÓÚÂÊÔÃÕÇÑÜ\s,\.\'-]{2,},\s')
CHICAGO_AUTHOR_RE = re.compile(
    r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóúâêôãõç]+,\s+[A-Z]')


# ---------------------------------------------------------------------------
# Localização de diretórios
# ---------------------------------------------------------------------------

def find_fontes_dir(slug):
    """Encontra o diretório fontes/ do seminário."""
    base = os.path.dirname(DIR)
    # Nacionais
    d = os.path.join(base, 'nacionais', slug, 'fontes')
    if os.path.isdir(d):
        return d
    # Regionais
    for grupo in ('nne', 'se', 'sul'):
        d = os.path.join(base, 'regionais', grupo, slug, 'fontes')
        if os.path.isdir(d):
            return d
    return None


def find_editable_files(fontes_dir):
    """Retorna lista de arquivos editáveis no diretório e subdiretórios conhecidos."""
    files = []
    if not fontes_dir or not os.path.isdir(fontes_dir):
        return files
    # Buscar no diretório raiz e em subdiretórios comuns
    search_dirs = [fontes_dir]
    for subdir in ('anais', 'originais', 'artigos', 'docs', 'textos'):
        d = os.path.join(fontes_dir, subdir)
        if os.path.isdir(d):
            search_dirs.append(d)
    for search_dir in search_dirs:
        for f in os.listdir(search_dir):
            ext = os.path.splitext(f)[1].lower()
            if ext in EDITABLE_EXTS:
                files.append(os.path.join(search_dir, f))
    return sorted(files)


# ---------------------------------------------------------------------------
# Conversão e leitura
# ---------------------------------------------------------------------------

def convert_to_docx(file_path, output_dir):
    """Converte arquivo editável para .docx via LibreOffice.
    Retorna caminho do .docx ou None se falhar."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.docx':
        # Já é docx — copiar para output_dir
        dest = os.path.join(output_dir, os.path.basename(file_path))
        shutil.copy2(file_path, dest)
        return dest

    try:
        result = subprocess.run(
            ['soffice', '--headless', '--convert-to', 'docx',
             '--outdir', output_dir, file_path],
            capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return None
        # soffice gera arquivo com mesmo nome mas extensão .docx
        base = os.path.splitext(os.path.basename(file_path))[0]
        docx_path = os.path.join(output_dir, base + '.docx')
        if os.path.exists(docx_path):
            return docx_path
        # Tentar com extensão original em maiúscula
        for f in os.listdir(output_dir):
            if f.lower() == base.lower() + '.docx':
                return os.path.join(output_dir, f)
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def read_paragraphs(docx_path):
    """Lê todos os parágrafos de um .docx, retorna lista de strings."""
    try:
        doc = Document(docx_path)
        return [p.text for p in doc.paragraphs]
    except Exception as e:
        print(f'  ERRO lendo {docx_path}: {e}', file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Extração de metadados
# ---------------------------------------------------------------------------

def parse_keywords(text):
    """Extrai lista de keywords de uma string.
    Retorna (kw_pt, kw_en) se há separador PT/EN, senão (kw, None)."""
    if not text or not text.strip():
        return [], None
    text = text.strip().rstrip('.')

    # Verificar se tem separador PT / EN (ex: "kw1, kw2 / key words: kw_en1")
    kw_en = None
    m = KW_PT_EN_SPLIT_RE.search(text)
    if m:
        pt_part = text[:m.start()].strip().rstrip('.')
        en_part = text[m.end():].strip().rstrip('.')
        kw_en = _split_kw_list(en_part)
        text = pt_part

    return _split_kw_list(text), kw_en


def parse_bilingual_keywords(text):
    """Parse keywords do formato bilíngue:
    'kw_pt1, kw_pt2, kw_pt3 / kw_en1, kw_en2, kw_en3'

    Separa pelo '/' que divide dois grupos com mesmo número de keywords.
    Retorna (kw_pt, kw_en).
    """
    if not text or not text.strip():
        return [], []
    text = text.strip().rstrip('.')

    # Encontrar todas as posições de ' / '
    sep = ' / '
    positions = []
    start = 0
    while True:
        pos = text.find(sep, start)
        if pos < 0:
            break
        positions.append(pos)
        start = pos + len(sep)

    if not positions:
        # Sem separador — tudo PT
        return _split_kw_list(text), []

    # Tentar cada posição: a correta divide em dois lados com
    # o mesmo número de keywords (ou mais próximo)
    best_pos = positions[-1]  # default: último separador
    if len(positions) == 1:
        pass  # só 1 posição — usar essa
    else:
        # Verificar a que produz lados mais equilibrados
        sep_char = ';' if ';' in text else ','
        best_diff = float('inf')
        for pos in positions:
            left = text[:pos]
            right = text[pos + len(sep):]
            n_left = left.count(sep_char) + 1
            n_right = right.count(sep_char) + 1
            diff = abs(n_left - n_right)
            if diff < best_diff:
                best_diff = diff
                best_pos = pos

    pt_part = text[:best_pos].strip().rstrip('.')
    en_part = text[best_pos + len(sep):].strip().rstrip('.')

    return _split_kw_list(pt_part), _split_kw_list(en_part)


def _split_kw_list(text):
    """Separa uma string de keywords em lista."""
    if not text:
        return []
    text = text.strip().rstrip('.')
    if ';' in text:
        kws = KW_SEP_RE.split(text)
    elif ',' in text:
        kws = KW_SEP_COMMA_RE.split(text)
    else:
        kws = [text]
    result = []
    for kw in kws:
        kw = kw.strip().rstrip('.')
        if kw and len(kw) > 1:
            result.append(kw)
    return result


# Limite de tamanho para abstract (chars). Se exceder, provavelmente
# capturou corpo do texto além do resumo.
ABSTRACT_MAX_CHARS = 3500


def extract_metadata(paragraphs, verbose=False):
    """Extrai abstract, keywords, refs de uma lista de parágrafos.

    State machine:
        SCAN → detecta marcador → entra no estado correspondente
        ABSTRACT_PT / ABSTRACT_EN / ABSTRACT_ES / KEYWORDS_PT / KEYWORDS_EN / REFS / BODY

    Retorna dict com campos extraídos (None se não encontrado).
    """
    state = 'SCAN'
    abstract_pt = []
    abstract_en = []
    abstract_es = []
    keywords_pt = []
    keywords_en = []
    keywords_es = []
    references = []
    current_ref_lines = []  # acumula linhas de uma referência

    def flush_ref():
        """Junta linhas acumuladas numa referência."""
        if current_ref_lines:
            ref = ' '.join(current_ref_lines).strip()
            if ref and len(ref) > 5:
                references.append(ref)
            current_ref_lines.clear()

    for i, text in enumerate(paragraphs):
        text_stripped = text.strip()
        if not text_stripped:
            # Parágrafo vazio — pode indicar fim de seção
            if state in ('ABSTRACT_PT', 'ABSTRACT_EN', 'ABSTRACT_ES'):
                # Parágrafo vazio no abstract: pode ser quebra legítima
                # Mas se já temos conteúdo, pode indicar fim
                pass
            if state == 'REFS':
                flush_ref()
            continue

        # Tentar detectar marcador de seção
        # Ordem importa: verificar marcadores antes de acumular conteúdo

        # --- Resumo PT ---
        m = ABSTRACT_PT_INLINE_RE.match(text_stripped)
        if m:
            if state == 'REFS':
                flush_ref()
            state = 'ABSTRACT_PT'
            content = m.group(1).strip()
            if content:
                abstract_pt.append(content)
            if verbose:
                print(f'    §{i}: → ABSTRACT_PT (inline)')
            continue

        if ABSTRACT_PT_RE.match(text_stripped):
            if state == 'REFS':
                flush_ref()
            state = 'ABSTRACT_PT'
            if verbose:
                print(f'    §{i}: → ABSTRACT_PT')
            continue

        # --- Abstract EN ---
        m = ABSTRACT_EN_INLINE_RE.match(text_stripped)
        if m:
            if state == 'REFS':
                flush_ref()
            state = 'ABSTRACT_EN'
            content = m.group(1).strip()
            if content:
                abstract_en.append(content)
            if verbose:
                print(f'    §{i}: → ABSTRACT_EN (inline)')
            continue

        if ABSTRACT_EN_RE.match(text_stripped):
            if state == 'REFS':
                flush_ref()
            state = 'ABSTRACT_EN'
            if verbose:
                print(f'    §{i}: → ABSTRACT_EN')
            continue

        # --- Resumen ES ---
        m = ABSTRACT_ES_INLINE_RE.match(text_stripped)
        if m:
            if state == 'REFS':
                flush_ref()
            state = 'ABSTRACT_ES'
            content = m.group(1).strip()
            if content:
                abstract_es.append(content)
            if verbose:
                print(f'    §{i}: → ABSTRACT_ES (inline)')
            continue

        if ABSTRACT_ES_RE.match(text_stripped):
            if state == 'REFS':
                flush_ref()
            state = 'ABSTRACT_ES'
            if verbose:
                print(f'    §{i}: → ABSTRACT_ES')
            continue

        # --- Keywords bilíngue (Palavras-chave / key words: ...) ---
        m = KW_BILINGUAL_RE.match(text_stripped)
        if m:
            if state == 'REFS':
                flush_ref()
            state = 'SCAN'
            kw_text = m.group(1)
            kw_pt, kw_en_bi = parse_bilingual_keywords(kw_text)
            keywords_pt = kw_pt
            if kw_en_bi and not keywords_en:
                keywords_en = kw_en_bi
            if verbose:
                print(f'    §{i}: → KW_BILINGUAL PT: {keywords_pt}')
                if kw_en_bi:
                    print(f'    §{i}:   KW_BILINGUAL EN: {kw_en_bi}')
            continue

        # --- Keywords PT ---
        m = KW_PT_RE.match(text_stripped)
        if m:
            if state == 'REFS':
                flush_ref()
            state = 'SCAN'  # keywords são linha única
            kw_text = m.group(1)
            kw_pt, kw_en_from_pt = parse_keywords(kw_text)
            keywords_pt = kw_pt
            if kw_en_from_pt and not keywords_en:
                keywords_en = kw_en_from_pt
            if verbose:
                print(f'    §{i}: → KW_PT: {keywords_pt}')
                if kw_en_from_pt:
                    print(f'    §{i}:   KW_EN (inline): {kw_en_from_pt}')
            continue

        # --- Keywords EN ---
        m = KW_EN_RE.match(text_stripped)
        if m:
            if state == 'REFS':
                flush_ref()
            state = 'SCAN'
            kw_text = m.group(1)
            kw_list, _ = parse_keywords(kw_text)
            keywords_en = kw_list
            if verbose:
                print(f'    §{i}: → KW_EN: {keywords_en}')
            continue

        # --- Keywords ES ---
        m = KW_ES_RE.match(text_stripped)
        if m:
            if state == 'REFS':
                flush_ref()
            state = 'SCAN'
            kw_text = m.group(1)
            kw_list, _ = parse_keywords(kw_text)
            keywords_es = kw_list
            if verbose:
                print(f'    §{i}: → KW_ES: {keywords_es}')
            continue

        # --- Referências ---
        if REFS_RE.match(text_stripped):
            if state == 'REFS':
                flush_ref()
            state = 'REFS'
            if verbose:
                print(f'    §{i}: → REFS')
            continue

        # --- Seção do corpo (interrompe abstract) ---
        if state in ('ABSTRACT_PT', 'ABSTRACT_EN', 'ABSTRACT_ES', 'SCAN'):
            if BODY_SECTION_RE.match(text_stripped):
                state = 'BODY'
                if verbose:
                    print(f'    §{i}: → BODY ({text_stripped[:40]})')
                continue

        # --- Acumular conteúdo conforme o estado ---
        if state == 'ABSTRACT_PT':
            # Verificar se entrou em keywords (bilíngue ou PT)
            m = KW_BILINGUAL_RE.match(text_stripped)
            if m:
                kw_pt, kw_en_bi = parse_bilingual_keywords(m.group(1))
                keywords_pt = kw_pt
                if kw_en_bi and not keywords_en:
                    keywords_en = kw_en_bi
                state = 'SCAN'
                continue
            m = KW_PT_RE.match(text_stripped)
            if m:
                kw_pt, kw_en_from_pt = parse_keywords(m.group(1))
                keywords_pt = kw_pt
                if kw_en_from_pt and not keywords_en:
                    keywords_en = kw_en_from_pt
                state = 'SCAN'
                continue
            # Proteção contra overflow: se abstract já é grande demais,
            # provavelmente capturou corpo do texto
            current_len = sum(len(p) for p in abstract_pt)
            if current_len + len(text_stripped) > ABSTRACT_MAX_CHARS:
                if verbose:
                    print(f'    §{i}: ABSTRACT_PT overflow ({current_len}c), parando')
                state = 'BODY'
                continue
            abstract_pt.append(text_stripped)

        elif state == 'ABSTRACT_EN':
            m = KW_EN_RE.match(text_stripped)
            if m:
                kw_list, _ = parse_keywords(m.group(1))
                keywords_en = kw_list
                state = 'SCAN'
                continue
            current_len = sum(len(p) for p in abstract_en)
            if current_len + len(text_stripped) > ABSTRACT_MAX_CHARS:
                if verbose:
                    print(f'    §{i}: ABSTRACT_EN overflow ({current_len}c), parando')
                state = 'BODY'
                continue
            abstract_en.append(text_stripped)

        elif state == 'ABSTRACT_ES':
            m = KW_ES_RE.match(text_stripped)
            if m:
                kw_list, _ = parse_keywords(m.group(1))
                keywords_es = kw_list
                state = 'SCAN'
                continue
            current_len = sum(len(p) for p in abstract_es)
            if current_len + len(text_stripped) > ABSTRACT_MAX_CHARS:
                if verbose:
                    print(f'    §{i}: ABSTRACT_ES overflow ({current_len}c), parando')
                state = 'BODY'
                continue
            abstract_es.append(text_stripped)

        elif state == 'REFS':
            # Cada parágrafo pode ser uma referência completa
            # ou continuação da anterior
            is_new_ref = (
                ABNT_AUTHOR_RE.match(text_stripped) or
                CHICAGO_AUTHOR_RE.match(text_stripped) or
                text_stripped.startswith('[') or
                (len(text_stripped) > 20 and text_stripped[0].isupper()
                 and not current_ref_lines)
            )
            if is_new_ref and current_ref_lines:
                flush_ref()
            current_ref_lines.append(text_stripped)

    # Flush última referência
    if state == 'REFS':
        flush_ref()

    # Montar resultado
    # keywords_pt/en/es já são listas (do parse_keywords)
    result = {
        'abstract': '\n\n'.join(abstract_pt) if abstract_pt else None,
        'abstract_en': '\n\n'.join(abstract_en) if abstract_en else None,
        'abstract_es': '\n\n'.join(abstract_es) if abstract_es else None,
        'keywords': keywords_pt if keywords_pt else None,
        'keywords_en': keywords_en if keywords_en else None,
        'keywords_es': keywords_es if keywords_es else None,
        'references': references if references else None,
    }

    return result


# ---------------------------------------------------------------------------
# Mapeamento filename → artigo
# ---------------------------------------------------------------------------

def normalize_for_match(text):
    """Normaliza texto para fuzzy matching."""
    text = text.lower()
    text = re.sub(r'[áàâã]', 'a', text)
    text = re.sub(r'[éêë]', 'e', text)
    text = re.sub(r'[íî]', 'i', text)
    text = re.sub(r'[óôõ]', 'o', text)
    text = re.sub(r'[úü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_title_from_filename(filename):
    """Extrai a parte do título do nome do arquivo.
    Remove extensão, autor entre parênteses, etc."""
    name = os.path.splitext(os.path.basename(filename))[0]
    # Remover conteúdo entre parênteses no final (geralmente autor+instituição)
    name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
    # Remover hífens e traços duplos
    name = re.sub(r'\s*[-–—]\s*$', '', name)
    return name.strip()


def match_files_to_articles(files, articles, verbose=False):
    """Faz fuzzy matching de filenames para artigos.

    articles: list of (id, title, subtitle)
    Retorna dict: file_path → article_id (ou None se sem match).
    """
    mapping = {}
    used_ids = set()

    for fpath in files:
        fname = os.path.basename(fpath)

        # Pular arquivos que não são artigos
        fname_lower = fname.lower()
        if any(skip in fname_lower for skip in
               ['programa', 'capa', 'sumario', 'sumário', '.jpg', '.png',
                '.gif', '.bmp', '.tiff', 'palestra']):
            if verbose:
                print(f'  SKIP: {fname} (não é artigo)')
            mapping[fpath] = None
            continue

        file_title = extract_title_from_filename(fname)
        file_norm = normalize_for_match(file_title)

        best_id = None
        best_score = 0

        for art_id, title, subtitle in articles:
            if art_id in used_ids:
                continue
            # Combinar título + subtítulo
            full_title = title or ''
            if subtitle:
                full_title += ' ' + subtitle
            art_norm = normalize_for_match(full_title)

            score = SequenceMatcher(None, file_norm, art_norm).ratio()

            # Tentar só o título (sem subtítulo)
            if title:
                score2 = SequenceMatcher(
                    None, file_norm, normalize_for_match(title)).ratio()
                score = max(score, score2)

            if score > best_score:
                best_score = score
                best_id = art_id

        if best_score >= 0.5:
            mapping[fpath] = best_id
            used_ids.add(best_id)
            if verbose:
                print(f'  MATCH ({best_score:.2f}): {fname[:60]} → {best_id}')
        else:
            mapping[fpath] = None
            if verbose:
                print(f'  NO MATCH ({best_score:.2f}): {fname[:60]}')

    return mapping


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Extrair metadados de arquivos editáveis (.doc/.docx/.odt/.rtf)')
    parser.add_argument('--slug', required=True,
                        help='Slug do seminário (ex: sdpr01)')
    parser.add_argument('--apply', action='store_true',
                        help='Atualizar o banco de dados')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Mostrar detalhes da extração')
    parser.add_argument('--only', type=str, default=None,
                        help='Artigos específicos (ex: 001,005,010)')
    parser.add_argument('--force', action='store_true',
                        help='Sobrescrever campos já preenchidos no banco')
    parser.add_argument('--db', default=DB_PATH,
                        help=f'Caminho do banco (default: {DB_PATH})')
    args = parser.parse_args()

    # Encontrar diretório fontes/
    fontes_dir = find_fontes_dir(args.slug)
    if not fontes_dir:
        print(f'ERRO: diretório fontes/ não encontrado para {args.slug}')
        sys.exit(1)

    # Encontrar arquivos editáveis
    editable_files = find_editable_files(fontes_dir)
    if not editable_files:
        print(f'Nenhum arquivo editável encontrado em {fontes_dir}')
        sys.exit(0)

    print(f'Seminário: {args.slug}')
    print(f'Fontes: {fontes_dir}')
    print(f'Arquivos editáveis: {len(editable_files)}')
    print()

    # Carregar artigos do banco
    conn = sqlite3.connect(args.db)
    try:
        _run_extraction(conn, args, editable_files)
    finally:
        conn.close()


def _run_extraction(conn, args, editable_files):
    """Lógica principal de extração (separada para garantir conn.close())."""
    articles = conn.execute(
        'SELECT id, title, subtitle FROM articles WHERE seminar_slug = ? ORDER BY id',
        (args.slug,)).fetchall()

    # Dados atuais do banco
    current_data = {}
    for row in conn.execute(
            'SELECT id, abstract, abstract_en, abstract_es, keywords, keywords_en, '
            'keywords_es, references_ FROM articles WHERE seminar_slug = ?',
            (args.slug,)):
        current_data[row[0]] = {
            'abstract': row[1], 'abstract_en': row[2],
            'abstract_es': row[3],
            'keywords': row[4], 'keywords_en': row[5],
            'keywords_es': row[6], 'references': row[7],
        }

    # Filtro --only
    only_ids = None
    if args.only:
        only_ids = set()
        for x in args.only.split(','):
            x = x.strip()
            if x.isdigit():
                only_ids.add(f'{args.slug}-{x.zfill(3)}')
            else:
                only_ids.add(x)

    # Mapear arquivos → artigos
    print('=== Mapeamento arquivo → artigo ===\n')
    mapping = match_files_to_articles(editable_files, articles, verbose=True)
    print()

    unmatched = [f for f, aid in mapping.items()
                 if aid is None and not any(
                     skip in os.path.basename(f).lower()
                     for skip in ['programa', 'capa', 'sumario', 'sumário',
                                  '.jpg', '.png', 'palestra'])]
    if unmatched:
        print(f'AVISO: {len(unmatched)} arquivo(s) sem match:')
        for f in unmatched:
            print(f'  - {os.path.basename(f)}')
        print()

    matched_ids = set(v for v in mapping.values() if v)
    unmatched_arts = [a for a in articles if a[0] not in matched_ids]
    if unmatched_arts:
        print(f'Artigos sem arquivo editável ({len(unmatched_arts)}):')
        for art_id, title, _ in unmatched_arts:
            print(f'  - {art_id}: {title[:60]}')
        print()

    # Converter e extrair
    print('=== Extração de metadados ===\n')

    with tempfile.TemporaryDirectory() as tmpdir:
        results = {}  # art_id → extracted metadata
        errors = []

        for fpath, art_id in sorted(mapping.items(),
                                     key=lambda x: x[1] or ''):
            if art_id is None:
                continue
            if only_ids and art_id not in only_ids:
                continue

            fname = os.path.basename(fpath)
            print(f'{art_id}: {fname[:70]}')

            # Converter para .docx
            docx_path = convert_to_docx(fpath, tmpdir)
            if not docx_path:
                print(f'  ERRO: conversão falhou')
                errors.append((art_id, 'conversão falhou'))
                continue

            # Ler parágrafos
            paragraphs = read_paragraphs(docx_path)
            if not paragraphs:
                print(f'  ERRO: nenhum parágrafo lido')
                errors.append((art_id, 'nenhum parágrafo'))
                continue

            if args.verbose:
                print(f'  {len(paragraphs)} parágrafos')

            # Extrair metadados
            meta = extract_metadata(paragraphs, verbose=args.verbose)
            results[art_id] = meta

            # Reportar
            cur = current_data.get(art_id, {})
            fields_found = []
            fields_new = []  # campos que seriam novos no banco

            for field, key in [
                ('abstract', 'abstract'),
                ('abstract_en', 'abstract_en'),
                ('abstract_es', 'abstract_es'),
                ('keywords', 'keywords'),
                ('keywords_en', 'keywords_en'),
                ('keywords_es', 'keywords_es'),
                ('references', 'references'),
            ]:
                val = meta.get(field)
                if val:
                    if isinstance(val, list):
                        desc = f'{len(val)} itens'
                    else:
                        desc = f'{len(val)}c'
                    cur_val = cur.get(key)
                    if cur_val:
                        fields_found.append(f'{field}={desc} (DB: {len(cur_val) if isinstance(cur_val, str) else "tem"})')
                    else:
                        fields_found.append(f'{field}={desc} [NOVO]')
                        fields_new.append(field)

            if fields_found:
                print(f'  Encontrado: {", ".join(fields_found)}')
            else:
                print(f'  Nada extraído')

            print()

    # Resumo
    print('=== Resumo ===\n')
    total_new = {f: 0 for f in
                 ['abstract', 'abstract_en', 'abstract_es', 'keywords',
                  'keywords_en', 'keywords_es', 'references']}
    total_update = {f: 0 for f in total_new}

    for art_id, meta in results.items():
        cur = current_data.get(art_id, {})
        for field in total_new:
            val = meta.get(field)
            db_key = 'references' if field == 'references' else field
            if val:
                if cur.get(db_key):
                    total_update[field] += 1
                else:
                    total_new[field] += 1

    print(f'Artigos processados: {len(results)}/{len(articles)}')
    print()
    print(f'{"Campo":<15} {"Novos":<8} {"Atualizações":<15}')
    print(f'{"-"*15} {"-"*8} {"-"*15}')
    for field in total_new:
        n = total_new[field]
        u = total_update[field]
        marker = ' ← ' if n > 0 else ''
        print(f'{field:<15} {n:<8} {u:<15}{marker}')
    print()

    if errors:
        print(f'Erros: {len(errors)}')
        for art_id, err in errors:
            print(f'  {art_id}: {err}')
        print()

    # Aplicar ao banco
    if args.apply:
        print('=== Aplicando ao banco ===\n')
        changes = 0
        for art_id, meta in sorted(results.items()):
            cur = current_data.get(art_id, {})
            updates = []

            for field, db_col in [
                ('abstract', 'abstract'),
                ('abstract_en', 'abstract_en'),
                ('abstract_es', 'abstract_es'),
                ('keywords', 'keywords'),
                ('keywords_en', 'keywords_en'),
                ('keywords_es', 'keywords_es'),
                ('references', 'references_'),
            ]:
                val = meta.get(field)
                if not val:
                    continue

                cur_key = 'references' if db_col == 'references_' else db_col
                has_current = bool(cur.get(cur_key))

                if has_current and not args.force:
                    continue  # Não sobrescrever sem --force

                # Serializar
                if isinstance(val, list):
                    db_val = json.dumps(val, ensure_ascii=False)
                else:
                    db_val = val

                updates.append((db_col, db_val))

            if updates:
                for db_col, db_val in updates:
                    conn.execute(
                        f'UPDATE articles SET {db_col} = ? WHERE id = ?',
                        (db_val, art_id))
                    changes += 1
                    print(f'  {art_id}.{db_col} ← atualizado')

        conn.commit()
        print(f'\n{changes} campo(s) atualizados.')
    else:
        # Contar o que seria atualizado
        would_update = sum(total_new.values())
        if would_update > 0:
            print(f'Use --apply para gravar {would_update} campo(s) novos no banco.')
        if sum(total_update.values()) > 0:
            print(f'Use --apply --force para sobrescrever '
                  f'{sum(total_update.values())} campo(s) existentes.')


if __name__ == '__main__':
    main()
