#!/usr/bin/env python3
"""
Generate HTML for OJS static pages (Custom Pages).

Creates:
  - Landing page (home) with 5 regional groups
  - One index page per group (Brasil, N/NE, RJ, SP, Sul)

The HTML uses only inline styles compatible with OJS's TinyMCE editor.
Cover images use actual OJS URLs from a cover map (JSON: {slug: url}).

Usage:
    # Fetch cover URLs from OJS API and generate pages:
    python3 scripts/generate_static_pages.py --base-url /index.php/ojs \\
        --ojs-url https://docomomo.ojs.com.br/index.php/ojs \\
        --ojs-user editor --ojs-pass ***

    # Or use a pre-built cover map:
    python3 scripts/generate_static_pages.py --cover-map covers.json

    # Generate without covers (images hidden via onerror):
    python3 scripts/generate_static_pages.py
"""

import argparse
import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')

# Group definitions
GROUPS = [
    {
        'volume': 1,
        'name': 'Brasil',
        'slug': 'brasil',
        'description': 'Seminários nacionais do Docomomo Brasil, realizados desde 1995.',
        'prefix': 'sdbr',
        'bg': '#B3CCA3',
        'border': '#5a8a42',
    },
    {
        'volume': 3,
        'name': 'Norte/Nordeste',
        'slug': 'norte-nordeste',
        'description': 'Seminários regionais do Docomomo Norte/Nordeste.',
        'prefix': 'sdnne',
        'bg': '#f0d060',
        'border': '#b08a10',
    },
    {
        'volume': 4,
        'name': 'Rio de Janeiro',
        'slug': 'rio-de-janeiro',
        'description': 'Seminários regionais do Docomomo Rio.',
        'prefix': 'sdrj',
        'bg': '#88bce4',
        'border': '#2a70a8',
    },
    {
        'volume': 5,
        'name': 'São Paulo',
        'slug': 'sao-paulo',
        'description': 'Seminários regionais do Docomomo São Paulo.',
        'prefix': 'sdsp',
        'bg': '#e07080',
        'border': '#a03040',
    },
    {
        'volume': 6,
        'name': 'Sul',
        'slug': 'sul',
        'description': 'Seminários regionais do Docomomo Sul.',
        'prefix': 'sdsul',
        'bg': '#c4a882',
        'border': '#7a5a30',
    },
]


def fetch_cover_map(ojs_url, ojs_user, ojs_pass):
    """Query OJS API to build {slug: cover_image_url} mapping."""
    import requests

    VOL_PREFIX = {1: 'sdbr', 3: 'sdnne', 4: 'sdrj', 5: 'sdsp', 6: 'sdsul'}

    s = requests.Session()
    s.post(f'{ojs_url}/login/signIn',
           data={'username': ojs_user, 'password': ojs_pass})

    cover_map = {}
    offset = 0
    while True:
        r = s.get(f'{ojs_url}/api/v1/issues',
                  params={'count': 50, 'offset': offset},
                  headers={'Accept': 'application/json'})
        data = r.json()
        items = data.get('items', [])
        if not items:
            break
        for issue in items:
            vol = issue.get('volume')
            num = int(issue.get('number', 0))
            prefix = VOL_PREFIX.get(vol)
            if prefix:
                slug = f'{prefix}{num:02d}'
                cover_url = issue.get('coverImageUrl', {}).get('pt_BR', '')
                if cover_url:
                    cover_map[slug] = cover_url
        offset += len(items)
        if offset >= data.get('itemsMax', 0):
            break

    return cover_map


def get_seminars(conn, volume):
    """Get all seminars for a volume/group."""
    rows = conn.execute('''
        SELECT s.slug, s.title, s.year, s.number,
               (SELECT COUNT(*) FROM articles a WHERE a.seminar_slug = s.slug) as n_arts
        FROM seminars s
        WHERE s.volume = ?
        ORDER BY s.number
    ''', (volume,)).fetchall()
    return rows


def get_sections(conn, slug):
    """Get sections for a seminar."""
    rows = conn.execute('''
        SELECT sec.title,
               (SELECT COUNT(*) FROM articles a WHERE a.section_id = sec.id) as n_arts
        FROM sections sec
        WHERE sec.seminar_slug = ?
        ORDER BY sec.seq, sec.id
    ''', (slug,)).fetchall()
    return rows


def generate_group_page(conn, group, base_url, cover_map=None):
    """Generate HTML for a group index page."""
    if cover_map is None:
        cover_map = {}
    seminars = get_seminars(conn, group['volume'])

    html = f'''<div style="max-width: 900px; margin: 0 auto;">
<p style="font-size: 1.1em; color: #555; margin-bottom: 2em;">{group['description']}</p>

<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 2em;">
'''

    for sem in seminars:
        slug = sem['slug']
        title = sem['title']
        n_arts = sem['n_arts']

        # Get sections
        sections = get_sections(conn, slug)

        issue_url = f'{base_url}/issue/view/{slug}'
        cover_url = cover_map.get(slug, '')

        # Section list
        sections_html = ''
        if sections and len(sections) > 1:
            items = []
            for sec in sections:
                items.append(f'<li style="margin: 2px 0; font-size: 0.85em; color: #666;">{sec["title"]} ({sec["n_arts"]})</li>')
            sections_html = f'<ul style="list-style: none; padding: 0; margin: 5px 0 0 0;">{"".join(items)}</ul>'

        # Cover image (only if URL known)
        cover_html = ''
        if cover_url:
            cover_html = f'''<a href="{issue_url}" style="display: block;">
      <img src="{cover_url}" alt="{title}" style="width: 100%; height: auto; display: block;" onerror="this.style.display='none'">
    </a>'''

        html += f'''  <div style="border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: #fff;">
    {cover_html}
    <div style="padding: 12px;">
      <h3 style="margin: 0 0 5px 0; font-size: 1em;"><a href="{issue_url}" style="text-decoration: none; color: #333;">{title}</a></h3>
      <p style="margin: 0; font-size: 0.9em; color: #888;">{n_arts} artigos</p>
      {sections_html}
    </div>
  </div>
'''

    html += '''</div>
</div>'''

    return html


def generate_landing_page(conn, base_url, cover_map=None):
    """Generate HTML for the main landing page with all groups."""
    if cover_map is None:
        cover_map = {}

    html = '''<div style="max-width: 900px; margin: 0 auto;">
<p style="font-size: 1.1em; color: #555; margin-bottom: 2em;">Acervo digital dos anais dos seminários do Docomomo Brasil — nacionais e regionais.</p>

'''

    for group in GROUPS:
        seminars = get_seminars(conn, group['volume'])
        total_arts = sum(s['n_arts'] for s in seminars)
        n_sems = len(seminars)
        page_url = f'{base_url}/{group["slug"]}'

        # Show all cover thumbnails (wrap to multiple lines)
        thumbs_html = ''
        for sem in seminars:
            slug = sem['slug']
            issue_url = f'{base_url}/issue/view/{slug}'
            cover_url = cover_map.get(slug, '')
            if cover_url:
                thumbs_html += f'<a href="{issue_url}" title="{sem["title"]}" style="display: inline-block; margin: 4px;"><img src="{cover_url}" alt="{sem["title"]}" style="width: 80px; height: auto; border-radius: 4px; border: 1px solid #eee;" onerror="this.style.display=\'none\'"></a>'

        html += f'''<div style="margin-bottom: 2.5em; padding: 1.5em; border: 1px solid #ddd; border-radius: 10px;">
  <h2 style="margin: 0 0 0.3em 0;"><a href="{page_url}" style="text-decoration: none; color: #222;">{group['name']}</a></h2>
  <p style="margin: 0 0 0.8em 0; font-size: 0.95em; color: #666;">{n_sems} {'seminário' if n_sems == 1 else 'seminários'} &middot; {total_arts} {'artigo' if total_arts == 1 else 'artigos'}</p>
  <div style="display: flex; flex-wrap: wrap; padding: 4px 0;">
    {thumbs_html}
  </div>
</div>

'''

    html += '''</div>'''
    return html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='/anais',
                       help='Base URL for the journal (default: /anais)')
    parser.add_argument('--outdir', default=os.path.join(BASE_DIR, 'paginas_estaticas'),
                       help='Output directory')
    parser.add_argument('--cover-map',
                       help='JSON file mapping slug → cover image URL')
    parser.add_argument('--ojs-url',
                       help='OJS base URL to fetch cover URLs (e.g. https://docomomo.ojs.com.br/index.php/ojs)')
    parser.add_argument('--ojs-user', help='OJS username')
    parser.add_argument('--ojs-pass', help='OJS password')
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Build cover map
    cover_map = {}
    if args.cover_map:
        with open(args.cover_map, encoding='utf-8') as f:
            cover_map = json.load(f)
        print(f'Loaded {len(cover_map)} cover URLs from {args.cover_map}')
    elif args.ojs_url and args.ojs_user and args.ojs_pass:
        cover_map = fetch_cover_map(args.ojs_url, args.ojs_user, args.ojs_pass)
        print(f'Fetched {len(cover_map)} cover URLs from OJS API')
    else:
        print('No cover map provided (use --cover-map or --ojs-url/user/pass). Pages will have no cover images.')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Generate landing page
    landing = generate_landing_page(conn, args.base_url, cover_map)
    with open(os.path.join(args.outdir, 'landing.html'), 'w', encoding='utf-8') as f:
        f.write(landing)
    print(f'Generated: landing.html')

    # Generate group pages
    for group in GROUPS:
        page = generate_group_page(conn, group, args.base_url, cover_map)
        filename = f'{group["slug"]}.html'
        with open(os.path.join(args.outdir, filename), 'w', encoding='utf-8') as f:
            f.write(page)
        n_sems = len(get_seminars(conn, group['volume']))
        print(f'Generated: {filename} ({n_sems} seminários)')

    conn.close()
    print(f'\nAll pages in {args.outdir}/')


if __name__ == '__main__':
    main()
