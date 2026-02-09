#!/usr/bin/env python3
"""
Merge metadados extraídos no YAML principal do sdsul04.
Também extrai referências bibliográficas de cada PDF.
"""

import yaml
import subprocess
import re
import os

class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

OrderedDumper.add_representer(dict, dict_representer)


def get_full_text(filepath):
    """Extract full text from PDF."""
    try:
        result = subprocess.run(
            ['pdftotext', filepath, '-'],
            capture_output=True, text=True, timeout=60
        )
        return result.stdout
    except Exception:
        return ''


def extract_references(text):
    """Extract bibliographic references from full text."""
    refs = []
    # Common section headers for references
    headers = [
        r'REFERÊNCIAS\s*BIBLIOGRÁFICAS',
        r'REFERÊNCIAS',
        r'REFERENCIAS\s*BIBLIOGRÁFICAS',
        r'REFERENCIAS',
        r'BIBLIOGRAPHY',
        r'BIBLIOGRAF[ÍI]A',
        r'NOTAS\s+E\s+REFERÊNCIAS',
    ]

    pattern = '|'.join(headers)
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return refs

    ref_text = text[match.end():]

    # Split into individual references
    # References typically start with AUTHOR. or numbered
    lines = ref_text.strip().split('\n')
    current_ref = ''

    for line in lines:
        line = line.strip()
        if not line:
            if current_ref:
                refs.append(current_ref.strip())
                current_ref = ''
            continue

        # Stop at common end markers
        if re.match(r'^(ANEXO|APÊNDICE|NOTAS$|^\d+\s*$)', line, re.IGNORECASE):
            break

        # New reference starts with uppercase author pattern or number
        if re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]{2,}[,.]', line) or re.match(r'^\d+[\.\)]\s', line):
            if current_ref:
                refs.append(current_ref.strip())
            current_ref = line
        elif re.match(r'^_+', line):
            # _____ line = same author
            if current_ref:
                refs.append(current_ref.strip())
            current_ref = line
        else:
            current_ref += ' ' + line

    if current_ref:
        refs.append(current_ref.strip())

    # Clean up
    cleaned = []
    for r in refs:
        r = re.sub(r'\s+', ' ', r).strip()
        if len(r) > 15 and not r.startswith('http'):  # skip very short or URL-only
            cleaned.append(r)

    return cleaned


def get_page_count(filepath):
    """Get page count via pdfinfo."""
    try:
        result = subprocess.run(
            ['pdfinfo', filepath],
            capture_output=True, text=True, timeout=30
        )
        for line in result.stdout.splitlines():
            if line.startswith('Pages:'):
                return int(line.split(':')[1].strip())
    except Exception:
        pass
    return None


# Load YAML
yaml_path = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul/sdsul04.yaml'
with open(yaml_path, 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# Load extracted metadata
meta_path = '/tmp/sdsul04_metadados.yaml'
with open(meta_path, 'r', encoding='utf-8') as f:
    meta_list = yaml.safe_load(f)

# Build lookup by original filename
meta_by_file = {}
for m in meta_list:
    meta_by_file[m['file']] = m

pdfs_dir = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul/sdsul04/pdfs'

stats = {
    'abstract': 0,
    'abstract_en': 0,
    'keywords': 0,
    'keywords_en': 0,
    'references': 0,
    'pages': 0,
}

for article in data['articles']:
    orig_file = article.get('file_original', '')
    art_id = article['id']
    num = int(art_id.split('-')[1])

    # Find metadata match
    meta = meta_by_file.get(orig_file)
    if not meta:
        print(f'  WARN: No metadata for {art_id} ({orig_file})')
        continue

    # Merge abstract
    if meta.get('abstract'):
        article['abstract'] = meta['abstract']
        stats['abstract'] += 1

    if meta.get('abstract_en'):
        article['abstract_en'] = meta['abstract_en']
        stats['abstract_en'] += 1

    # Merge keywords
    if meta.get('keywords'):
        article['keywords'] = meta['keywords']
        stats['keywords'] += 1

    if meta.get('keywords_en'):
        article['keywords_en'] = meta['keywords_en']
        stats['keywords_en'] += 1

    # Page count
    pdf_path = os.path.join(pdfs_dir, f'sdsul04-{num:03d}.pdf')
    if os.path.exists(pdf_path):
        pc = get_page_count(pdf_path)
        if pc:
            article['pages_count'] = pc
            stats['pages'] += 1

        # Extract references
        full_text = get_full_text(pdf_path)
        refs = extract_references(full_text)
        if refs:
            article['references'] = refs
            stats['references'] += 1
            print(f'  {art_id}: {len(refs)} refs')
        else:
            print(f'  {art_id}: no refs found')
    else:
        print(f'  WARN: PDF not found: {pdf_path}')

# Save updated YAML
with open(yaml_path, 'w', encoding='utf-8') as f:
    yaml.dump(data, f, Dumper=OrderedDumper, width=10000, sort_keys=False,
              allow_unicode=True, default_flow_style=False)

print(f'\nAtualizado {yaml_path}')
print(f'  Resumos: {stats["abstract"]}/46')
print(f'  Abstracts EN: {stats["abstract_en"]}/46')
print(f'  Keywords PT: {stats["keywords"]}/46')
print(f'  Keywords EN: {stats["keywords_en"]}/46')
print(f'  Referências: {stats["references"]}/46')
print(f'  Páginas: {stats["pages"]}/46')
