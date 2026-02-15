#!/usr/bin/env python3
"""Importa todos os YAMLs (nacionais + regionais) para anais.db.

Trata três formatos de YAML:
1. {issue: {...}, articles: [...]}  — maioria
2. {slug, evento, publicacao, artigos: [...]}  — sdnne02, sdnne05
3. {slug, title, year, articles: [...]}  — sdsul06-08 (sem wrapper issue)

Fase 1 de deduplicação de autores: match exato por (givenname, familyname).
"""

import sqlite3
import yaml
import json
import os
import sys

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE, 'anais.db')


def find_yaml_files():
    """Encontra todos os YAMLs com artigos no projeto."""
    yamls = []
    for root, dirs, files in os.walk(BASE):
        # Ignorar diretórios de scripts, docs, e o próprio .git
        if any(skip in root for skip in ['/scripts', '/docs', '/.git', '/revisao', '/dict', '/site']):
            continue
        for f in sorted(files):
            if f.endswith('.yaml') and not f.startswith('.'):
                yamls.append(os.path.join(root, f))
    return yamls


def parse_seminar(data):
    """Extrai metadados do seminário, independente do formato."""
    # Formato 1: {issue: {...}, articles: [...]}
    if 'issue' in data:
        iss = data['issue']
        return {
            'slug': iss.get('slug'),
            'title': iss.get('title'),
            'subtitle': iss.get('subtitle'),
            'year': iss.get('year'),
            'volume': iss.get('volume'),
            'number': iss.get('number'),
            'date_published': iss.get('date_published'),
            'isbn': iss.get('isbn'),
            'doi': iss.get('doi'),
            'description': iss.get('description'),
            'location': iss.get('location'),
            'publisher': iss.get('publisher'),
            'source': iss.get('source'),
            'editors': iss.get('editors', []),
            'volume_pdf': iss.get('volume_pdf'),
        }

    # Formato 2: sdnne02/05 com evento/publicacao
    if 'evento' in data:
        ev = data.get('evento', {})
        pub = data.get('publicacao', {})
        return {
            'slug': data.get('slug'),
            'title': ev.get('titulo'),
            'subtitle': ev.get('tema'),
            'year': ev.get('data'),
            'volume': data.get('volume'),
            'number': data.get('number'),
            'date_published': f"{ev.get('data', '')}-01-01" if ev.get('data') else None,
            'isbn': pub.get('isbn'),
            'doi': None,
            'description': pub.get('ficha_catalografica'),
            'location': ev.get('local'),
            'publisher': None,
            'source': (data.get('fontes', {}).get('docomomobrasil', {}) or {}).get('url'),
            'editors': ev.get('organizacao', []),
            'volume_pdf': data.get('volume_pdf'),
        }

    # Formato 3: sdsul06-08 com campos no topo
    return {
        'slug': data.get('slug'),
        'title': data.get('title'),
        'subtitle': data.get('subtitle'),
        'year': data.get('year'),
        'volume': data.get('volume'),
        'number': data.get('number'),
        'date_published': data.get('date_published'),
        'isbn': data.get('isbn'),
        'doi': data.get('doi'),
        'description': data.get('description'),
        'location': data.get('location'),
        'publisher': data.get('publisher'),
        'source': data.get('source'),
        'editors': data.get('editors', []),
        'volume_pdf': data.get('volume_pdf'),
    }


def parse_articles(data):
    """Retorna lista de artigos, independente do formato."""
    return data.get('articles', data.get('artigos', []))


def parse_sections_from_data(data):
    """Extrai seções pré-definidas (sdsul06-08)."""
    return data.get('sections', [])


def get_field(art, *names, default=None):
    """Retorna o primeiro campo encontrado dentre os nomes possíveis."""
    for name in names:
        val = art.get(name)
        if val is not None:
            return val
    return default


def normalize_article(art, seminar_slug):
    """Normaliza campos de um artigo para o formato canônico."""
    title = get_field(art, 'title', 'titulo')
    subtitle = get_field(art, 'subtitle', 'subtitulo')
    section = get_field(art, 'section', 'secao')
    abstract = get_field(art, 'abstract', 'resumo')
    abstract_en = get_field(art, 'abstract_en', 'resumo_en')
    abstract_es = get_field(art, 'abstract_es', 'resumo_es')
    keywords = get_field(art, 'keywords', 'palavras_chave')
    keywords_en = get_field(art, 'keywords_en', 'palavras_chave_en')
    keywords_es = get_field(art, 'keywords_es', 'palavras_chave_es')
    references = get_field(art, 'references', 'referencias')
    file_ = get_field(art, 'file', 'arquivo_pdf')
    pages = get_field(art, 'pages', 'paginas')
    pages_count = get_field(art, 'pages_count', 'paginas_total')
    authors = get_field(art, 'authors', 'autores', default=[])

    # Gerar ID se ausente
    art_id = art.get('id')

    return {
        'id': art_id,
        'title': title,
        'subtitle': subtitle,
        'section': section,
        'locale': art.get('locale', 'pt-BR'),
        'pages': str(pages) if pages else None,
        'pages_count': pages_count,
        'file': file_,
        'abstract': abstract,
        'abstract_en': abstract_en,
        'abstract_es': abstract_es,
        'keywords': json.dumps(keywords, ensure_ascii=False) if isinstance(keywords, list) else keywords,
        'keywords_en': json.dumps(keywords_en, ensure_ascii=False) if isinstance(keywords_en, list) else keywords_en,
        'keywords_es': json.dumps(keywords_es, ensure_ascii=False) if isinstance(keywords_es, list) else keywords_es,
        'references_': json.dumps(references, ensure_ascii=False) if isinstance(references, list) else references,
        'ojs_id': art.get('ojs_id'),
        'doi': art.get('doi'),
        'authors': authors,
    }


def get_or_create_author(cur, givenname, familyname):
    """Retorna author_id, criando se necessário. Match exato."""
    cur.execute(
        'SELECT id FROM authors WHERE givenname = ? AND familyname = ?',
        (givenname, familyname)
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        'INSERT INTO authors (givenname, familyname) VALUES (?, ?)',
        (givenname, familyname)
    )
    return cur.lastrowid


def update_author_contact(cur, author_id, email, orcid):
    """Atualiza email/orcid se o novo valor for mais completo."""
    if not email and not orcid:
        return
    cur.execute('SELECT email, orcid FROM authors WHERE id = ?', (author_id,))
    current = cur.fetchone()
    updates = {}
    if email and not current[0]:
        updates['email'] = email
    if orcid and not current[1]:
        updates['orcid'] = orcid
    if updates:
        sets = ', '.join(f'{k} = ?' for k in updates)
        cur.execute(f'UPDATE authors SET {sets} WHERE id = ?',
                    list(updates.values()) + [author_id])


def parse_issue_sections(data):
    """Extrai seções definidas em issue.sections (sdrj02, sdrj03, etc.)."""
    if 'issue' in data:
        return data['issue'].get('sections', [])
    return []


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Importa YAMLs para anais.db')
    parser.add_argument('--incremental', action='store_true',
                        help='Importar sem apagar dados existentes')
    parser.add_argument('--only', nargs='+', metavar='SLUG',
                        help='Importar apenas estes slugs (ex: sdrj02 sdrj03)')
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f'Banco não encontrado: {DB_PATH}')
        print('Execute init_anais_db.py primeiro.')
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    cur = conn.cursor()

    if not args.incremental and not args.only:
        # Limpar dados existentes (para reimportação completa)
        for table in ['article_author', 'author_variants', 'articles', 'authors', 'sections', 'seminars']:
            cur.execute(f'DELETE FROM {table}')
        # Reset autoincrement
        cur.execute("DELETE FROM sqlite_sequence")
        conn.commit()
    elif args.only:
        # Limpar apenas os slugs especificados
        for slug in args.only:
            cur.execute('DELETE FROM article_author WHERE article_id IN (SELECT id FROM articles WHERE seminar_slug = ?)', (slug,))
            cur.execute('DELETE FROM articles WHERE seminar_slug = ?', (slug,))
            cur.execute('DELETE FROM sections WHERE seminar_slug = ?', (slug,))
            cur.execute('DELETE FROM seminars WHERE slug = ?', (slug,))
        conn.commit()
        print(f'Limpou dados de: {", ".join(args.only)}')

    yaml_files = find_yaml_files()
    stats = {
        'seminars': 0, 'sections': 0, 'articles': 0,
        'authors': 0, 'article_author': 0, 'skipped': 0,
    }

    for path in yaml_files:
        with open(path) as f:
            data = yaml.safe_load(f)

        if not data or not isinstance(data, dict):
            continue

        # Verificar se tem artigos
        articles_raw = parse_articles(data)
        if not articles_raw:
            continue

        # Parsear seminário
        sem = parse_seminar(data)
        if not sem.get('slug'):
            print(f'  SKIP (sem slug): {path}')
            continue

        slug = sem['slug']

        # Filtrar por --only se especificado
        if args.only and slug not in args.only:
            continue

        print(f'{slug:12s} — {len(articles_raw)} artigos ... ', end='', flush=True)

        # Inserir seminário
        cur.execute('''
            INSERT OR REPLACE INTO seminars
            (slug, title, subtitle, year, volume, number, date_published,
             isbn, doi, description, location, publisher, source, editors,
             volume_pdf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            slug, sem['title'], sem['subtitle'], sem['year'],
            sem['volume'], sem['number'],
            str(sem['date_published']) if sem['date_published'] else None,
            sem['isbn'], sem['doi'], sem['description'],
            sem['location'], sem['publisher'], sem['source'],
            json.dumps(sem['editors'], ensure_ascii=False) if sem['editors'] else '[]',
            sem['volume_pdf'],
        ))
        stats['seminars'] += 1

        # Seções pré-definidas (sdsul06-08 no topo, sdrj02-03 em issue.sections)
        predefined_sections = parse_sections_from_data(data) or parse_issue_sections(data)
        for i, sec in enumerate(predefined_sections):
            cur.execute('''
                INSERT OR IGNORE INTO sections (seminar_slug, title, abbrev, seq, hide_title)
                VALUES (?, ?, ?, ?, ?)
            ''', (slug, sec['title'], sec.get('abbrev'), i,
                  1 if sec.get('hide_title') else 0))

        # Processar artigos
        art_count = 0
        for idx, art_raw in enumerate(articles_raw):
            art = normalize_article(art_raw, slug)

            # Gerar ID se ausente
            art_id = art['id'] or f'{slug}-{idx+1:03d}'

            # Seção: buscar ou criar
            section_id = None
            if art['section']:
                cur.execute(
                    'SELECT id FROM sections WHERE seminar_slug = ? AND title = ?',
                    (slug, art['section'])
                )
                row = cur.fetchone()
                if row:
                    section_id = row[0]
                else:
                    cur.execute(
                        'INSERT INTO sections (seminar_slug, title, seq) VALUES (?, ?, ?)',
                        (slug, art['section'], stats['sections'])
                    )
                    section_id = cur.lastrowid
                    stats['sections'] += 1

            # Inserir artigo
            try:
                cur.execute('''
                    INSERT INTO articles
                    (id, seminar_slug, section_id, title, subtitle, locale,
                     pages, pages_count, file, abstract, abstract_en, abstract_es,
                     keywords, keywords_en, keywords_es, references_, ojs_id, doi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    art_id, slug, section_id, art['title'], art['subtitle'],
                    art['locale'], art['pages'], art['pages_count'], art['file'],
                    art['abstract'], art['abstract_en'], art['abstract_es'],
                    art['keywords'], art['keywords_en'], art['keywords_es'],
                    art['references_'], art['ojs_id'], art['doi'],
                ))
            except sqlite3.IntegrityError as e:
                print(f'\n  ERRO artigo {art_id}: {e}')
                stats['skipped'] += 1
                continue

            art_count += 1

            # Autores
            for seq, author in enumerate(art['authors']):
                gn = (author.get('givenname') or '').strip()
                fn = (author.get('familyname') or '').strip()
                if not gn or not fn:
                    continue

                author_id = get_or_create_author(cur, gn, fn)
                update_author_contact(
                    cur, author_id,
                    author.get('email'),
                    author.get('orcid')
                )

                try:
                    cur.execute('''
                        INSERT OR IGNORE INTO article_author
                        (article_id, author_id, seq, primary_contact,
                         affiliation, bio, country)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        art_id, author_id, seq,
                        1 if author.get('primary_contact') else 0,
                        author.get('affiliation'),
                        author.get('bio'),
                        author.get('country', 'BR'),
                    ))
                    stats['article_author'] += 1
                except sqlite3.IntegrityError:
                    pass  # mesmo autor duplicado no artigo

        stats['articles'] += art_count
        print(f'{art_count} importados')

    conn.commit()

    # Contar autores
    cur.execute('SELECT COUNT(*) FROM authors')
    stats['authors'] = cur.fetchone()[0]

    # Resumo
    print(f'\n{"="*50}')
    print(f'Seminários:      {stats["seminars"]}')
    print(f'Seções:          {stats["sections"]}')
    print(f'Artigos:         {stats["articles"]}')
    print(f'Autores únicos:  {stats["authors"]}')
    print(f'Vínculos autor:  {stats["article_author"]}')
    if stats['skipped']:
        print(f'Artigos pulados: {stats["skipped"]}')

    # Top autores recorrentes
    print(f'\nTop 10 autores por nº de artigos:')
    cur.execute('''
        SELECT a.givenname, a.familyname, COUNT(*) as n
        FROM article_author aa JOIN authors a ON aa.author_id = a.id
        GROUP BY a.id ORDER BY n DESC LIMIT 10
    ''')
    for gn, fn, n in cur.fetchall():
        print(f'  {n:3d} artigos — {gn} {fn}')

    # Autores com email/orcid
    cur.execute('SELECT COUNT(*) FROM authors WHERE email IS NOT NULL')
    with_email = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM authors WHERE orcid IS NOT NULL')
    with_orcid = cur.fetchone()[0]
    print(f'\nAutores com email: {with_email}/{stats["authors"]}')
    print(f'Autores com ORCID: {with_orcid}/{stats["authors"]}')

    conn.close()
    print(f'\nBanco atualizado: {os.path.abspath(DB_PATH)}')


if __name__ == '__main__':
    main()
