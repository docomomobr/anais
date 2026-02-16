#!/usr/bin/env python3
"""Exporta dados do anais.db de volta para YAMLs.

Sobrescreve os YAMLs existentes com os dados enriquecidos do banco
(títulos normalizados, autores deduplicados, ORCIDs, etc.).

Mantém o formato canônico (issue: + articles:) para todos os seminários.
Preserva a ordem original dos artigos e autores.

Uso:
    python3 scripts/export_db_to_yaml.py                    # exporta todos
    python3 scripts/export_db_to_yaml.py --slug sdnne07     # exporta um
    python3 scripts/export_db_to_yaml.py --dry-run           # mostra o que faria
"""

import argparse
import json
import os
import sqlite3
import sys

import yaml

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE, 'anais.db')

# Mapeamento de slug → caminho do YAML
SLUG_TO_PATH = {}


def _init_slug_paths():
    """Descobre caminhos dos YAMLs existentes."""
    for root, dirs, files in os.walk(BASE):
        if any(skip in root for skip in ['/.git', '/scripts', '/docs', '/revisao', '/dict', '/site', '/xml']):
            continue
        for f in sorted(files):
            if f.endswith('.yaml') and not f.startswith('.'):
                # Extrair slug do nome do arquivo (sem extensão)
                slug = os.path.splitext(f)[0]
                SLUG_TO_PATH[slug] = os.path.join(root, f)


class OrderedDumper(yaml.Dumper):
    """YAML dumper que preserva ordem dos dicts e usa largura grande."""
    pass


def _dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


def _str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    if any(c in data for c in [':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`']):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


OrderedDumper.add_representer(dict, _dict_representer)
OrderedDumper.add_representer(str, _str_representer)


def _none_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:null', 'null')


OrderedDumper.add_representer(type(None), _none_representer)


def export_seminar(conn, slug):
    """Exporta um seminário do banco para dict no formato YAML."""

    # Seminar metadata
    sem = conn.execute('SELECT * FROM seminars WHERE slug = ?', (slug,)).fetchone()
    if not sem:
        print(f'  AVISO: seminário {slug} não encontrado no banco', file=sys.stderr)
        return None

    editors = json.loads(sem['editors']) if sem['editors'] else []
    related_urls = json.loads(sem['related_urls']) if sem['related_urls'] else []

    issue = {
        'slug': slug,
        'title': sem['title'],
    }
    if sem['subtitle']:
        issue['subtitle'] = sem['subtitle']
    if sem['location']:
        issue['location'] = sem['location']
    issue['year'] = sem['year']
    if sem['volume'] is not None:
        issue['volume'] = sem['volume']
    if sem['number'] is not None:
        issue['number'] = sem['number']
    if sem['isbn']:
        issue['isbn'] = sem['isbn']
    if sem['doi']:
        issue['doi'] = sem['doi']
    if sem['publisher']:
        issue['publisher'] = sem['publisher']
    if editors:
        issue['editors'] = editors
    if sem['description']:
        issue['description'] = sem['description']
    if sem['source']:
        issue['source'] = sem['source']
    if sem['date_published']:
        issue['date_published'] = sem['date_published']
    if sem['volume_pdf']:
        issue['volume_pdf'] = sem['volume_pdf']
    if related_urls:
        issue['related_urls'] = related_urls

    # Sections
    sections = conn.execute(
        'SELECT title, abbrev, seq, hide_title FROM sections WHERE seminar_slug = ? ORDER BY seq',
        (slug,)
    ).fetchall()

    if sections:
        issue['sections'] = []
        for sec in sections:
            s = {'title': sec['title']}
            if sec['abbrev']:
                s['abbrev'] = sec['abbrev']
            if sec['hide_title']:
                s['hide_title'] = True
            issue['sections'].append(s)

    # Articles
    articles_raw = conn.execute(
        '''SELECT a.*, s.title as section_title
           FROM articles a
           LEFT JOIN sections s ON s.id = a.section_id
           WHERE a.seminar_slug = ?
           ORDER BY a.id''',
        (slug,)
    ).fetchall()

    articles = []
    for art in articles_raw:
        # Authors
        authors_raw = conn.execute(
            '''SELECT au.givenname, au.familyname, au.email, au.orcid,
                      aa.affiliation, aa.bio, aa.country, aa.seq, aa.primary_contact
               FROM article_author aa
               JOIN authors au ON au.id = aa.author_id
               WHERE aa.article_id = ?
               ORDER BY aa.seq''',
            (art['id'],)
        ).fetchall()

        authors = []
        for au in authors_raw:
            author = {
                'givenname': au['givenname'],
                'familyname': au['familyname'],
            }
            author['email'] = au['email']
            author['affiliation'] = au['affiliation']
            author['orcid'] = au['orcid']
            author['bio'] = au['bio']
            author['country'] = au['country'] or 'BR'
            author['primary_contact'] = bool(au['primary_contact'])
            authors.append(author)

        # Keywords
        def parse_json_or_none(val):
            if not val:
                return None
            try:
                parsed = json.loads(val)
                return parsed if isinstance(parsed, list) and parsed else None
            except (json.JSONDecodeError, TypeError):
                return None

        keywords = parse_json_or_none(art['keywords'])
        keywords_en = parse_json_or_none(art['keywords_en'])
        keywords_es = parse_json_or_none(art['keywords_es'])

        # References
        references = parse_json_or_none(art['references_'])

        # Ordem lógica: id, título, subtítulo, autores, seção, resumo, keywords,
        # abstract_en, keywords_en, abstract_es, keywords_es, referências,
        # metadados técnicos (locale, file, pages, doi, document_type)
        article = {
            'id': art['id'],
            'title': art['title'],
        }
        if art['subtitle']:
            article['subtitle'] = art['subtitle']
        article['authors'] = authors
        article['section'] = art['section_title']
        article['abstract'] = art['abstract']
        if keywords:
            article['keywords'] = keywords
        if art['abstract_en']:
            article['abstract_en'] = art['abstract_en']
        if keywords_en:
            article['keywords_en'] = keywords_en
        if art['abstract_es']:
            article['abstract_es'] = art['abstract_es']
        if keywords_es:
            article['keywords_es'] = keywords_es
        if references:
            article['references'] = references
        article['locale'] = art['locale'] or 'pt-BR'
        article['file'] = art['file']
        if art['pages_count'] is not None:
            article['pages_count'] = art['pages_count']
        article['pages'] = art['pages']
        if art['doi']:
            article['doi'] = art['doi']
        if art['document_type'] and art['document_type'] != 'artigo':
            article['document_type'] = art['document_type']

        articles.append(article)

    return {'issue': issue, 'articles': articles}


def dump_yaml(data):
    """Serializa para YAML no formato canônico do projeto.

    Adiciona linha em branco entre artigos para legibilidade.
    """
    raw = yaml.dump(
        data,
        Dumper=OrderedDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=10000,
    )
    # Adicionar linha em branco entre artigos (antes de cada "- id:")
    lines = raw.split('\n')
    result = []
    for i, line in enumerate(lines):
        if line.startswith('- id:') and i > 0 and result and result[-1] != '':
            result.append('')
        result.append(line)
    return '\n'.join(result)


def main():
    parser = argparse.ArgumentParser(description='Exportar anais.db para YAMLs')
    parser.add_argument('--slug', help='Exportar apenas este seminário')
    parser.add_argument('--dry-run', action='store_true', help='Apenas mostrar, não escrever')
    parser.add_argument('--outdir', help='Diretório de saída (default: sobrescreve YAMLs existentes)')
    args = parser.parse_args()

    _init_slug_paths()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.slug:
        slugs = [args.slug]
    else:
        rows = conn.execute('SELECT slug FROM seminars ORDER BY volume, number').fetchall()
        slugs = [r['slug'] for r in rows]

    exported = 0
    for slug in slugs:
        data = export_seminar(conn, slug)
        if not data:
            continue

        n_articles = len(data['articles'])

        if args.outdir:
            outpath = os.path.join(args.outdir, f'{slug}.yaml')
        elif slug in SLUG_TO_PATH:
            outpath = SLUG_TO_PATH[slug]
        else:
            print(f'  {slug}: sem YAML existente, pulando (use --outdir)', file=sys.stderr)
            continue

        if args.dry_run:
            print(f'  {slug}: {n_articles} artigos → {outpath}')
        else:
            os.makedirs(os.path.dirname(outpath), exist_ok=True)
            with open(outpath, 'w', encoding='utf-8') as f:
                f.write(dump_yaml(data))
            print(f'  {slug}: {n_articles} artigos → {outpath}')

        exported += 1

    conn.close()
    print(f'\nTotal: {exported} seminários exportados')


if __name__ == '__main__':
    main()
