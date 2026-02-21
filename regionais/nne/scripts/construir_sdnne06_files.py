#!/usr/bin/env python3
"""
construir_sdnne06_files.py — Adiciona campo 'file' ao sdnne06.yaml e
copia/converte arquivos-fonte para sdnne06/pdfs/.

Usa o mapeamento corrigido (mapeamento_artigos.yaml) como referência.
Apenas artigos com matched_file != null e tipo == COMPLETO são processados.

Tarefas:
1. Adicionar 'file: sdnne06-{id:03d}.pdf' após 'section' no sdnne06.yaml
2. Copiar PDFs ou converter .doc/.docx via LibreOffice para sdnne06/pdfs/
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import OrderedDict
from pathlib import Path

import yaml


# --- YAML OrderedDumper (project conventions) ---
class OrderedDumper(yaml.Dumper):
    pass


def _dict_representer(dumper, data):
    return dumper.represent_mapping(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items()
    )


def _str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


OrderedDumper.add_representer(OrderedDict, _dict_representer)
OrderedDumper.add_representer(str, _str_representer)


# --- Ordered YAML Loader ---
class OrderedLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader, node):
    loader.flatten_mapping(node)
    pairs = loader.construct_pairs(node)
    return OrderedDict(pairs)


OrderedLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


# --- Paths ---
BASE = Path(__file__).resolve().parent.parent  # regionais/nne/
YAML_PATH = BASE / 'sdnne06.yaml'
MAPPING_PATH = BASE / 'sdnne06' / 'fontes' / 'mapeamento_artigos.yaml'
SOURCE_DIR = BASE / 'sdnne06' / 'fontes' / 'artigos_completos'
PDF_DIR = BASE / 'sdnne06' / 'pdfs'


def load_mapping():
    """Load mapeamento_artigos.yaml and build id→matched_file dict."""
    with open(MAPPING_PATH, encoding='utf-8') as f:
        entries = yaml.load(f, Loader=OrderedLoader)

    mapping = {}
    for entry in entries:
        aid = entry['article_id']
        matched = entry.get('matched_file')
        tipo = entry.get('tipo')
        if matched and tipo == 'COMPLETO':
            mapping[aid] = matched
    return mapping


def load_yaml():
    """Load sdnne06.yaml preserving order."""
    with open(YAML_PATH, encoding='utf-8') as f:
        raw = f.read()

    # Preserve header comments
    header_lines = []
    content_lines = []
    in_header = True
    for line in raw.split('\n'):
        if in_header and (line.startswith('#') or line.strip() == ''):
            header_lines.append(line)
        else:
            in_header = False
            content_lines.append(line)

    content = '\n'.join(content_lines)
    doc = yaml.load(content, Loader=OrderedLoader)
    header = '\n'.join(header_lines)
    if header and not header.endswith('\n'):
        header += '\n'

    return doc, header


def add_file_fields(doc, mapping):
    """Add 'file' field to articles that have a match in the mapping."""
    count = 0
    for article in doc['articles']:
        aid = article['id']
        if aid in mapping:
            filename = f'sdnne06-{aid:03d}.pdf'
            # Insert 'file' after 'section' and before 'abstract'
            new_article = OrderedDict()
            for key, value in article.items():
                new_article[key] = value
                if key == 'section':
                    new_article['file'] = filename
            # Replace article in-place
            article.clear()
            article.update(new_article)
            count += 1
    return count


def save_yaml(doc, header):
    """Save sdnne06.yaml with project conventions."""
    yaml_str = yaml.dump(
        doc, Dumper=OrderedDumper, default_flow_style=False,
        allow_unicode=True, width=10000, sort_keys=False
    )
    with open(YAML_PATH, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(yaml_str)


def process_files(mapping):
    """Copy PDFs or convert .doc/.docx to PDF."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    stats = {'copied': 0, 'converted': 0, 'errors': 0, 'skipped': 0}
    errors = []

    for aid in sorted(mapping.keys()):
        source_name = mapping[aid]
        target_name = f'sdnne06-{aid:03d}.pdf'
        target_path = PDF_DIR / target_name
        source_path = SOURCE_DIR / source_name

        if target_path.exists():
            print(f'  SKIP {target_name} (already exists)')
            stats['skipped'] += 1
            continue

        if not source_path.exists():
            print(f'  ERROR {target_name}: source not found: {source_name}')
            errors.append((aid, source_name, 'source not found'))
            stats['errors'] += 1
            continue

        ext = source_path.suffix.lower()

        if ext == '.pdf':
            shutil.copy2(source_path, target_path)
            print(f'  COPY  {source_name} -> {target_name}')
            stats['copied'] += 1

        elif ext in ('.doc', '.docx'):
            # Convert via LibreOffice
            # LibreOffice requires output dir, not output file
            # Use a temp dir to avoid name collisions
            with tempfile.TemporaryDirectory() as tmpdir:
                result = subprocess.run(
                    [
                        'libreoffice', '--headless', '--convert-to', 'pdf',
                        '--outdir', tmpdir,
                        str(source_path),
                    ],
                    capture_output=True, text=True, timeout=120,
                )
                if result.returncode != 0:
                    print(f'  ERROR {target_name}: LibreOffice conversion failed')
                    print(f'        stderr: {result.stderr[:200]}')
                    errors.append((aid, source_name, 'conversion failed'))
                    stats['errors'] += 1
                    continue

                # Find the converted PDF in tmpdir
                converted_files = list(Path(tmpdir).glob('*.pdf'))
                if not converted_files:
                    print(f'  ERROR {target_name}: no PDF produced by LibreOffice')
                    errors.append((aid, source_name, 'no PDF produced'))
                    stats['errors'] += 1
                    continue

                shutil.move(str(converted_files[0]), target_path)
                print(f'  CONV  {source_name} -> {target_name}')
                stats['converted'] += 1
        else:
            print(f'  ERROR {target_name}: unsupported format {ext}')
            errors.append((aid, source_name, f'unsupported format {ext}'))
            stats['errors'] += 1

    return stats, errors


def main():
    print('=' * 60)
    print('construir_sdnne06_files.py')
    print('=' * 60)

    # 1. Load mapping
    print('\n1. Carregando mapeamento...')
    mapping = load_mapping()
    print(f'   {len(mapping)} artigos com matched_file (tipo COMPLETO)')

    # 2. Update YAML
    print('\n2. Atualizando sdnne06.yaml (campo file)...')
    doc, header = load_yaml()
    n_updated = add_file_fields(doc, mapping)
    save_yaml(doc, header)
    print(f'   {n_updated} artigos atualizados com campo file')

    # 3. Copy/convert files
    print('\n3. Copiando/convertendo arquivos para pdfs/...')
    stats, errors = process_files(mapping)

    # Summary
    print('\n' + '=' * 60)
    print('RESUMO')
    print('=' * 60)
    print(f'  Artigos mapeados:  {len(mapping)}')
    print(f'  YAML atualizados:  {n_updated}')
    print(f'  PDFs copiados:     {stats["copied"]}')
    print(f'  PDFs convertidos:  {stats["converted"]}')
    print(f'  Já existentes:     {stats["skipped"]}')
    print(f'  Erros:             {stats["errors"]}')

    if errors:
        print('\nERROS:')
        for aid, name, reason in errors:
            print(f'  Art.{aid}: {name} — {reason}')

    total_pdfs = stats['copied'] + stats['converted'] + stats['skipped']
    print(f'\nTotal PDFs em {PDF_DIR}: {total_pdfs}')
    print(f'YAML salvo em: {YAML_PATH}')

    if stats['errors'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
