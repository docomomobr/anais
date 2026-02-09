#!/usr/bin/env python3
"""
Extrai referências bibliográficas de PDFs de artigos e atualiza YAMLs.

Processa três seminários:
- sdnne07 (65 artigos, campo 'references', PDF via 'file')
- sdnne09 (50 artigos, campo 'references', PDF via 'file')
- sdsul06 (24 artigos, campo 'referencias', PDF via 'arquivo_pdf')
"""

import yaml
import re
import subprocess
from pathlib import Path

BASE = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais")


# ─── YAML helpers ────────────────────────────────────────────────────────────

class OrderedDumper(yaml.SafeDumper):
    pass


def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


OrderedDumper.add_representer(dict, dict_representer)


def salvar_yaml(caminho, dados):
    """Salva YAML preservando ordem dos campos."""
    with open(caminho, 'w', encoding='utf-8') as f:
        yaml.dump(dados, f, Dumper=OrderedDumper, default_flow_style=False,
                  allow_unicode=True, width=10000, sort_keys=False)


# ─── PDF text extraction ─────────────────────────────────────────────────────

def extrair_texto_pdf(pdf_path):
    """Extrai texto completo de um PDF usando pdftotext."""
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', str(pdf_path), '-'],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout
    except Exception as e:
        print(f"  ERRO ao extrair texto de {pdf_path.name}: {e}")
        return ""


# ─── Reference section detection ─────────────────────────────────────────────

# Whitespace prefix including form feed (\x0c) from pdftotext page breaks
WS = r'^[\s\x0c]*'

# Patterns for reference section headers (ordered by specificity)
# Allow optional trailing colon, period, and numbered prefix (e.g., "6." or "5 ")
# Also allow missing accents (REFERENCIAS vs REFERÊNCIAS)
NUM_PREFIX = r'(?:\d+[\.\)]\s+|\d+\s+)?'
REF_PATTERNS = [
    WS + NUM_PREFIX + r'REFER[EÊ]NCIAS\s+BIBLIOGR[AÁ]FICAS[\.:]?\s*$',
    WS + NUM_PREFIX + r'Refer[eê]ncias\s+[Bb]ibliogr[aá]ficas[\.:]?\s*$',
    WS + NUM_PREFIX + r'REFER[EÊ]NCIAS[\.:]?\s*$',
    WS + NUM_PREFIX + r'Refer[eê]ncias[\.:]?\s*$',
    WS + NUM_PREFIX + r'BIBLIOGRAFIA[\.:]?\s*$',
    WS + NUM_PREFIX + r'Bibliografia[\.:]?\s*$',
    WS + NUM_PREFIX + r'REFERENCES[\.:]?\s*$',
    WS + NUM_PREFIX + r'References[\.:]?\s*$',
    WS + NUM_PREFIX + r'BIBLIOGRAPHIC\s+REFERENCES[\.:]?\s*$',
]

# End markers: stop extracting when we hit these
END_PATTERNS = [
    WS + r'ANEXO',
    WS + r'APÊNDICE',
    WS + r'Anexo',
    WS + r'Apêndice',
    WS + r'NOTAS[:\s]*$',
    WS + r'Notas[:\s]*$',
    WS + r'APENDICE',
    WS + r'NOTAS:',
]

# Seminar footer lines to skip
FOOTER_PATTERNS = [
    r'^\d+[°º]\s*Semin[áa]rio\s+Docomomo',
    r'^7[°º]\s+Semin[áa]rio',
    r'^9[°º]\s+Semin[áa]rio',
    r'^VI\s+Semin[áa]rio',
    r'Semin[áa]rio\s+Docomomo\s+(Norte|Sul|N/NE)',
    r'^Manaus,?\s+20\d{2}',
    r'^São\s+Lu[ií]s,?\s+20\d{2}',
    r'^Porto\s+Alegre,?\s+20\d{2}',
]


def encontrar_secao_referencias(texto):
    """
    Encontra a seção de referências no texto extraído do PDF.
    Retorna o texto da seção de referências, ou string vazia.
    """
    lines = texto.split('\n')

    # Strip form feed characters for matching but preserve original lines
    # pdftotext -layout inserts \x0c at page breaks
    # Find the LAST occurrence of a reference header
    ref_start = -1
    for i, line in enumerate(lines):
        for pat in REF_PATTERNS:
            if re.match(pat, line):
                ref_start = i
                break

    if ref_start == -1:
        return ""

    # Extract everything after the header
    ref_lines = lines[ref_start + 1:]

    # Find end marker
    filtered = []
    for line in ref_lines:
        # Check for end markers
        hit_end = False
        for pat in END_PATTERNS:
            if re.match(pat, line):
                hit_end = True
                break
        if hit_end:
            break

        # Skip footer lines (seminar name, city/year)
        is_footer = False
        for pat in FOOTER_PATTERNS:
            if re.search(pat, line):
                is_footer = True
                break
        if is_footer:
            continue

        filtered.append(line)

    return '\n'.join(filtered)


# ─── Reference splitting ─────────────────────────────────────────────────────

def is_new_reference_start(line):
    """
    Determines if a line starts a new reference entry.

    Patterns detected:
    - UPPERCASE AUTHOR: "SILVA, J. A." / "BRUAND, Y."
    - Underscore continuation: "______." or "_____."
    - Numbered: "1." "2)" "[1]"
    - Institutional author in caps: "BRASIL." "IPHAN."
    - URL-only line starting with http
    """
    stripped = line.strip()
    if not stripped:
        return False

    # Numbered references
    if re.match(r'^\d+[\.\)]\s+', stripped):
        return True
    if re.match(r'^\[\d+\]\s+', stripped):
        return True

    # Underscore continuation (same author)
    if re.match(r'^_{3,}\.?\s', stripped):
        return True

    # UPPERCASE author pattern: at least 2 uppercase letters followed by comma or period
    # e.g., "SILVA, J." or "BRUAND, Y." or "CASTOR, Ricardo"
    if re.match(r'^[A-ZÁÉÍÓÚÀÂÃÊÔÇÜ]{2,}[\s,.]', stripped):
        return True

    # Institutional author or title starting with uppercase word
    # e.g., "BRASIL.", "IBGE.", "INSTITUTO BRASILEIRO..."
    if re.match(r'^[A-ZÁÉÍÓÚÀÂÃÊÔÇÜ]{2,}\.\s', stripped):
        return True

    return False


def split_references(ref_text):
    """
    Splits the reference section text into individual reference entries.
    Merges continuation lines into single entries.
    """
    lines = ref_text.split('\n')

    references = []
    current_ref = []

    for line in lines:
        stripped = line.strip()

        # Skip empty lines between references
        if not stripped:
            if current_ref:
                # Empty line can signal end of current ref
                # But only if next non-empty line starts a new ref
                # For now, just keep collecting
                pass
            continue

        # Skip page numbers (standalone numbers)
        if re.match(r'^\d{1,3}$', stripped):
            continue

        # Check if this starts a new reference
        if is_new_reference_start(stripped):
            if current_ref:
                references.append(' '.join(current_ref))
            current_ref = [stripped]
        else:
            # Continuation of previous reference
            if current_ref:
                current_ref.append(stripped)
            else:
                # Orphan continuation line before first ref, start a new one
                current_ref = [stripped]

    # Don't forget the last reference
    if current_ref:
        references.append(' '.join(current_ref))

    return references


def limpar_referencias(refs):
    """
    Cleans up the list of extracted references.
    - Removes entries shorter than 15 chars
    - Removes entries that are just page numbers or noise
    - Merges multi-space runs
    - Strips trailing/leading whitespace
    """
    cleaned = []
    for ref in refs:
        # Normalize whitespace
        ref = re.sub(r'\s+', ' ', ref).strip()

        # Remove trailing page number artifacts
        ref = re.sub(r'\s+\d{1,3}\s*$', '', ref)

        # Skip too short
        if len(ref) < 15:
            continue

        # Skip if it's just a URL with no context
        if ref.startswith('http') and ' ' not in ref and len(ref) < 50:
            continue

        # Skip if it's only numbers/symbols
        if re.match(r'^[\d\s\.\-/]+$', ref):
            continue

        cleaned.append(ref)

    return cleaned


# ─── Main processing ─────────────────────────────────────────────────────────

def processar_seminario(yaml_path, pdf_dir, ref_field, pdf_field, seminar_name):
    """
    Processes a seminar: extracts references from PDFs and updates YAML.

    Args:
        yaml_path: Path to the YAML file
        pdf_dir: Path to the PDF directory
        ref_field: Field name for references ('references' or 'referencias')
        pdf_field: Field name for PDF filename ('file' or 'arquivo_pdf')
        seminar_name: Name for logging
    """
    print(f"\n{'='*60}")
    print(f"Processando: {seminar_name}")
    print(f"{'='*60}")

    # Load YAML
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # Determine structure (sdnne has issue/articles, sdsul is flat)
    if 'articles' in data:
        articles = data['articles']
    elif 'issue' in data and 'articles' not in data:
        # sdsul06 is flat (articles at top level key 'articles')
        articles = data.get('articles', [])
    else:
        articles = data.get('articles', [])

    total = len(articles)
    extracted = 0
    skipped = 0
    failed = 0
    ref_counts = []

    for i, art in enumerate(articles):
        art_id = art.get('id', f'#{i+1}')
        pdf_name = art.get(pdf_field)

        if not pdf_name:
            print(f"  [{art_id}] SEM PDF definido - pulando")
            skipped += 1
            continue

        pdf_path = pdf_dir / pdf_name
        if not pdf_path.exists():
            print(f"  [{art_id}] PDF não encontrado: {pdf_name}")
            failed += 1
            continue

        # Skip if references already exist
        if art.get(ref_field):
            print(f"  [{art_id}] já tem {ref_field} - pulando")
            skipped += 1
            continue

        # Extract text
        texto = extrair_texto_pdf(pdf_path)
        if not texto:
            print(f"  [{art_id}] texto vazio - pulando")
            failed += 1
            continue

        # Find references section
        ref_text = encontrar_secao_referencias(texto)
        if not ref_text:
            print(f"  [{art_id}] seção de referências não encontrada")
            failed += 1
            continue

        # Split into individual references
        refs = split_references(ref_text)
        refs = limpar_referencias(refs)

        if not refs:
            print(f"  [{art_id}] nenhuma referência extraída após limpeza")
            failed += 1
            continue

        # Add to article
        art[ref_field] = refs
        extracted += 1
        ref_counts.append(len(refs))

        if len(refs) <= 5:
            status = "poucas"
        elif len(refs) <= 20:
            status = "ok"
        else:
            status = "muitas"

        print(f"  [{art_id}] {len(refs)} referências ({status})")

    # Save updated YAML
    salvar_yaml(yaml_path, data)

    # Print summary
    avg_refs = sum(ref_counts) / len(ref_counts) if ref_counts else 0
    print(f"\n--- Resumo {seminar_name} ---")
    print(f"  Total de artigos: {total}")
    print(f"  Referências extraídas: {extracted}/{total}")
    print(f"  Pulados (já existentes/sem PDF): {skipped}")
    print(f"  Falhas (sem seção/sem texto): {failed}")
    if ref_counts:
        print(f"  Refs por artigo: min={min(ref_counts)}, max={max(ref_counts)}, média={avg_refs:.1f}")
        print(f"  Total de referências: {sum(ref_counts)}")

    return {
        'name': seminar_name,
        'total': total,
        'extracted': extracted,
        'skipped': skipped,
        'failed': failed,
        'ref_counts': ref_counts,
    }


def main():
    seminarios = [
        {
            'yaml_path': BASE / 'regionais/nne/sdnne07.yaml',
            'pdf_dir': BASE / 'regionais/nne/sdnne07/pdfs',
            'ref_field': 'references',
            'pdf_field': 'file',
            'name': 'sdnne07 (7º Seminário Docomomo N/NE, Manaus 2018)',
        },
        {
            'yaml_path': BASE / 'regionais/nne/sdnne09.yaml',
            'pdf_dir': BASE / 'regionais/nne/sdnne09/pdfs',
            'ref_field': 'references',
            'pdf_field': 'file',
            'name': 'sdnne09 (9º Seminário Docomomo N/NE, São Luís 2022)',
        },
        {
            'yaml_path': BASE / 'regionais/sul/sdsul06.yaml',
            'pdf_dir': BASE / 'regionais/sul/sdsul06/pdfs',
            'ref_field': 'referencias',
            'pdf_field': 'arquivo_pdf',
            'name': 'sdsul06 (6º Seminário Docomomo Sul, Porto Alegre 2019)',
        },
    ]

    results = []
    for sem in seminarios:
        r = processar_seminario(
            yaml_path=sem['yaml_path'],
            pdf_dir=sem['pdf_dir'],
            ref_field=sem['ref_field'],
            pdf_field=sem['pdf_field'],
            seminar_name=sem['name'],
        )
        results.append(r)

    # Final summary
    print(f"\n{'='*60}")
    print("RESUMO GERAL")
    print(f"{'='*60}")
    total_refs = 0
    total_arts = 0
    total_extracted = 0
    for r in results:
        n_refs = sum(r['ref_counts'])
        total_refs += n_refs
        total_arts += r['total']
        total_extracted += r['extracted']
        print(f"  {r['name']}:")
        print(f"    {r['extracted']}/{r['total']} artigos com referências ({n_refs} refs total)")
    print(f"\n  TOTAL: {total_extracted}/{total_arts} artigos, {total_refs} referências extraídas")


if __name__ == '__main__':
    main()
