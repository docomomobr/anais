#!/usr/bin/env python3
"""
Add pages_count to articles in YAML files using pdfinfo.
Only adds pages_count where missing; does not modify other fields.
"""

import yaml
import subprocess
import os
import sys
from collections import OrderedDict

BASE = '/home/danilomacedo/Dropbox/docomomo/26-27/anais'

# --- OrderedDumper (preserves field order) ---

class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

OrderedDumper.add_representer(dict, dict_representer)
OrderedDumper.add_representer(OrderedDict, dict_representer)

# Represent None as 'null' explicitly
def none_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:null', 'null')

OrderedDumper.add_representer(type(None), none_representer)

# --- OrderedLoader (preserves field order on load) ---

class OrderedLoader(yaml.SafeLoader):
    pass

def construct_mapping(loader, node):
    loader.flatten_mapping(node)
    pairs = loader.construct_pairs(node)
    return OrderedDict(pairs)

OrderedLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_mapping)


def get_page_count(pdf_path):
    """Get page count from PDF using pdfinfo."""
    try:
        result = subprocess.run(
            ['pdfinfo', pdf_path],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if line.startswith('Pages:'):
                return int(line.split(':')[1].strip())
    except Exception as e:
        print(f"  ERRO pdfinfo {pdf_path}: {e}", file=sys.stderr)
    return None


# Configuration for each seminar
SEMINARS = [
    {
        'name': 'sdnne02',
        'yaml_path': os.path.join(BASE, 'regionais/nne/sdnne02.yaml'),
        'pdf_dir': os.path.join(BASE, 'regionais/nne/sdnne02/pdfs'),
        'file_field': 'arquivo_pdf',
        'articles_key': 'artigos',
        'has_issue_wrapper': False,
    },
    {
        'name': 'sdnne07',
        'yaml_path': os.path.join(BASE, 'regionais/nne/sdnne07.yaml'),
        'pdf_dir': os.path.join(BASE, 'regionais/nne/sdnne07/pdfs'),
        'file_field': 'file',
        'articles_key': 'articles',
        'has_issue_wrapper': True,
    },
    {
        'name': 'sdnne09',
        'yaml_path': os.path.join(BASE, 'regionais/nne/sdnne09.yaml'),
        'pdf_dir': os.path.join(BASE, 'regionais/nne/sdnne09/pdfs'),
        'file_field': 'file',
        'articles_key': 'articles',
        'has_issue_wrapper': True,
    },
    {
        'name': 'sdsul06',
        'yaml_path': os.path.join(BASE, 'regionais/sul/sdsul06.yaml'),
        'pdf_dir': os.path.join(BASE, 'regionais/sul/sdsul06/pdfs'),
        'file_field': 'arquivo_pdf',
        'articles_key': 'articles',
        'has_issue_wrapper': False,
    },
    {
        'name': 'sdrj04',
        'yaml_path': os.path.join(BASE, 'regionais/rio/sdrj04.yaml'),
        'pdf_dir': os.path.join(BASE, 'regionais/rio/sdrj04/pdfs'),
        'file_field': 'arquivo_pdf',
        'articles_key': 'articles',
        'has_issue_wrapper': True,
    },
    {
        'name': 'sdsp05',
        'yaml_path': os.path.join(BASE, 'regionais/sp/sdsp05.yaml'),
        'pdf_dir': os.path.join(BASE, 'regionais/sp/sdsp05/pdfs'),
        'file_field': 'file',
        'articles_key': 'articles',
        'has_issue_wrapper': True,
    },
    {
        'name': 'sdsp06',
        'yaml_path': os.path.join(BASE, 'regionais/sp/sdsp06.yaml'),
        'pdf_dir': os.path.join(BASE, 'regionais/sp/sdsp06/pdfs'),
        'file_field': 'file',
        'articles_key': 'articles',
        'has_issue_wrapper': True,
    },
    {
        'name': 'sdsp07',
        'yaml_path': os.path.join(BASE, 'regionais/sp/sdsp07.yaml'),
        'pdf_dir': os.path.join(BASE, 'regionais/sp/sdsp07/pdfs'),
        'file_field': 'file',
        'articles_key': 'articles',
        'has_issue_wrapper': True,
    },
    {
        'name': 'sdsp08',
        'yaml_path': os.path.join(BASE, 'regionais/sp/sdsp08.yaml'),
        'pdf_dir': os.path.join(BASE, 'regionais/sp/sdsp08/pdfs'),
        'file_field': 'file',
        'articles_key': 'articles',
        'has_issue_wrapper': True,
    },
    {
        'name': 'sdsp09',
        'yaml_path': os.path.join(BASE, 'regionais/sp/sdsp09.yaml'),
        'pdf_dir': os.path.join(BASE, 'regionais/sp/sdsp09/pdfs'),
        'file_field': 'file',
        'articles_key': 'articles',
        'has_issue_wrapper': True,
    },
]


def process_seminar(config):
    name = config['name']
    yaml_path = config['yaml_path']
    pdf_dir = config['pdf_dir']
    file_field = config['file_field']
    articles_key = config['articles_key']
    has_issue_wrapper = config['has_issue_wrapper']

    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.load(f, Loader=OrderedLoader)

    # Get articles list
    if has_issue_wrapper:
        articles = data.get(articles_key, [])
    else:
        articles = data.get(articles_key, [])

    total = len(articles)
    added = 0
    skipped_existing = 0
    skipped_no_pdf = 0
    errors = 0

    for art in articles:
        # Skip if pages_count already present
        if 'pages_count' in art:
            skipped_existing += 1
            continue

        # Get PDF filename
        pdf_filename = art.get(file_field)
        if not pdf_filename:
            skipped_no_pdf += 1
            continue

        pdf_path = os.path.join(pdf_dir, pdf_filename)
        if not os.path.isfile(pdf_path):
            art_id = art.get('id', art.get('titulo', art.get('title', '?')))
            print(f"  AVISO [{name}]: PDF não encontrado: {pdf_path} (artigo {art_id})")
            errors += 1
            continue

        count = get_page_count(pdf_path)
        if count is not None:
            # Insert pages_count right after file_field
            keys = list(art.keys())
            file_idx = keys.index(file_field) if file_field in keys else len(keys)
            new_art = OrderedDict()
            for i, k in enumerate(keys):
                new_art[k] = art[k]
                if k == file_field:
                    new_art['pages_count'] = count
            # If file_field was not found, just append
            if file_field not in keys:
                new_art['pages_count'] = count
            # Replace article in-place
            art.clear()
            art.update(new_art)
            added += 1
        else:
            art_id = art.get('id', '?')
            print(f"  ERRO [{name}]: pdfinfo falhou para {pdf_path} (artigo {art_id})")
            errors += 1

    # Save
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, default_flow_style=False,
                  allow_unicode=True, width=10000, sort_keys=False)

    print(f"{name}: {total} artigos, {added} pages_count adicionados, "
          f"{skipped_existing} já existentes, {skipped_no_pdf} sem PDF, {errors} erros")
    return added


def main():
    total_added = 0
    for config in SEMINARS:
        name = config['name']
        if not os.path.isfile(config['yaml_path']):
            print(f"ERRO: YAML não encontrado: {config['yaml_path']}")
            continue
        total_added += process_seminar(config)

    print(f"\nTotal: {total_added} pages_count adicionados")


if __name__ == '__main__':
    main()
