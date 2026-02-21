#!/usr/bin/env python3
"""
Constrói o sdnne06.yaml a partir de:
1. caderno_parsed.json — 105 artigos parseados do caderno de resumos
2. email_listing_detailed.json — emails de aceite com categorias
3. Arquivos baixados em fontes/attachments/ — artigos completos

O 6º Seminário Docomomo N/NE (Teresina, 2016) publicou apenas o caderno
de resumos. Os textos completos são escassos (~14 arquivos de ~100 artigos).
"""

import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

import yaml


# --- YAML OrderedDumper ---
class OrderedDumper(yaml.Dumper):
    pass

def _dict_representer(dumper, data):
    return dumper.represent_mapping(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, data.items())

def _str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

OrderedDumper.add_representer(OrderedDict, _dict_representer)
OrderedDumper.add_representer(str, _str_representer)


BASE = Path(__file__).resolve().parent.parent  # regionais/nne/
EMAILS_DIR = BASE / 'sdnne06' / 'fontes' / 'emails'
ATTACH_DIR = BASE / 'sdnne06' / 'fontes' / 'attachments'
OUT_YAML = BASE / 'sdnne06.yaml'


def parse_author(raw):
    """Parse 'SURNAME, X. Y.' or 'SURNAME, Full Name' into givenname/familyname."""
    # Clean up spaces before periods: "D ." → "D."
    raw = re.sub(r'\s+\.', '.', raw.strip())
    # Only strip trailing dot if it's NOT an initial (single letter before dot)
    if raw.endswith('.') and not re.search(r'\b[A-Z]\.$', raw):
        raw = raw.rstrip('.')

    if ',' not in raw:
        # No comma — likely a parsing artifact, skip
        return None

    parts = raw.split(',', 1)
    family_raw = parts[0].strip()
    given_raw = parts[1].strip() if len(parts) > 1 else ''

    if not given_raw:
        return None

    # familyname: title-case the surname
    # Handle multi-word: "ALBUQUERQUE JÚNIOR" → "Albuquerque Júnior"
    family = title_case_name(family_raw)

    # givenname: preserve as-is if initials, title-case if full name
    given = normalize_given(given_raw.strip())

    if not family or not given:
        return None

    return OrderedDict([
        ('givenname', given),
        ('familyname', family),
    ])


def title_case_name(s):
    """Title-case a surname, handling particles and accents."""
    words = s.split()
    result = []
    particles = {'de', 'da', 'do', 'dos', 'das', 'e'}
    for w in words:
        lower = w.lower()
        if lower in particles and result:
            result.append(lower)
        else:
            # Title-case preserving accents
            result.append(w.capitalize() if w.isupper() or w.islower() else w)
    return ' '.join(result)


def normalize_given(s):
    """Normalize givenname: title-case full names, preserve initials."""
    # First, handle multi-initial abbreviations without spaces: "C.M.S." → "C. M. S."
    s = re.sub(r'([A-Za-z])\.([A-Za-z])', r'\1. \2', s)
    s = re.sub(r'([A-Za-z])\.([A-Za-z])', r'\1. \2', s)  # Second pass for 3+ initials

    # Split into tokens
    tokens = s.split()
    result = []
    particles = {'de', 'da', 'do', 'dos', 'das'}
    for t in tokens:
        bare = t.rstrip('.')
        lower = bare.lower()
        has_dot = t.endswith('.')
        is_single_letter = len(bare) == 1

        if lower in particles:
            # Particle: always lowercase (DE → de, DA → da)
            result.append(lower)
        elif lower == 'e' and not has_dot:
            # "e" connector (but "E." is an initial)
            result.append('e')
        elif is_single_letter and bare[0].isupper():
            # Single letter initial: "D" or "D." → "D."
            result.append(bare.upper() + '.')
        elif bare.isupper() and len(bare) == 2 and has_dot:
            # Two-letter initial with dot: "DE." → could be particle "de" with erroneous dot
            if lower in particles:
                result.append(lower)
            else:
                result.append(bare.upper() + '.')
        elif bare.isupper() and len(bare) > 2:
            # Full name in caps: "ALCÍLIA" → "Alcília"
            result.append(bare.capitalize())
        else:
            result.append(t)
    return ' '.join(result)


def normalize_title(title):
    """Clean up title: fix spaces, travessão."""
    title = re.sub(r'\s+', ' ', title).strip()
    # Travessão: " - " isolado → " — "
    title = re.sub(r'(?<=[a-zA-ZÀ-ú]) - (?=[a-zA-ZÀ-ú])', ' — ', title)
    return title


def clean_keywords(keywords):
    """Clean keywords list: remove duplicates, empty, trailing dots."""
    seen = set()
    result = []
    for kw in keywords:
        kw = kw.strip().rstrip('.')
        if not kw:
            continue
        key = kw.lower()
        if key not in seen:
            seen.add(key)
            result.append(kw)
    return result


def extract_acceptances(email_listing):
    """Extract accepted article titles and categories from acceptance emails."""
    acceptances = {}
    for email in email_listing:
        folder = email.get('folder', '')
        if folder in ('artigos completos', 'inbox', 'rascunhos', 'lixo'):
            continue
        body = email.get('detail', {}).get('body', '')
        if 'aceito' not in body.lower() and 'aceite' not in body.lower():
            continue
        # Extract title from quoted text
        match = re.search(r'"([^"]+)"', body)
        if not match:
            match = re.search(r'\"([^\"]+)\"', body)
        if not match:
            continue
        title = match.group(1).strip()
        # Extract category
        category = 'unknown'
        body_upper = body.upper()
        if 'APRESENTAÇÃO ORAL' in body_upper:
            category = 'ORAL'
        elif 'PAINEL DIGITAL' in body_upper or 'POSTER' in body_upper or 'PÔSTER' in body_upper:
            category = 'POSTER'
        elif 'DOCOJOVEM' in body_upper or 'DOCO JOVEM' in body_upper:
            category = 'DOCOJOVEM'

        # Normalize title for matching
        key = re.sub(r'\s+', ' ', title.lower().strip())
        acceptances[key] = {
            'title': title,
            'category': category,
            'folder': folder,
        }
    return acceptances


def main():
    # Load data
    with open(EMAILS_DIR / 'caderno_parsed.json') as f:
        caderno = json.load(f)

    with open(EMAILS_DIR / 'email_listing_detailed.json') as f:
        email_listing = json.load(f)

    print(f"Caderno: {len(caderno)} entries")

    # Extract acceptance records
    acceptances = extract_acceptances(email_listing)
    print(f"Acceptance emails: {len(acceptances)} records")

    # Manual fix for parsing artifact: Glauco Campello article
    # The PDF column layout mixed title, authors and abstract
    glauco_fix = {
        'title': 'A permanência dos critérios modernos na obra de Glauco Campello — Estação Rodoviária Argemiro de Figueiredo. Campina Grande. PB',
        'authors': ['AFONSO, A.', 'ARAÚJO, C. K. S. de'],
        'abstract': (
            'Este artigo possui como objeto de estudo, o Terminal Rodoviário Argemiro '
            'Figueiredo, inaugurado em 25 de maio de 1985, localizado no bairro Sandra '
            'Cavalcante, Campina Grande, zona agreste da Paraíba. O projeto é de autoria '
            'do arquiteto Glauco Campello, nascido em 1934, em Mamanguape, Paraíba. '
            'O objetivo desse artigo é o de analisar arquitetonicamente essa obra, '
            'observando-se a permanência dos critérios modernos na mesma, que apesar '
            'de ter sido concluída em 1985, manteve todos os princípios projetuais da '
            'linguagem moderna, tais como uso de modulação, racionalidade projetual e '
            'construtiva, transparências espaciais, e atenção especial ao detalhe dos '
            'elementos compositivos.'
        ),
        'keywords': ['arquitetura moderna', 'Glauco Campello', 'Campina Grande'],
        'section': 'DOCOJOVEM',
    }

    # Deduplicate caderno entries (same title in different sections)
    seen_titles = {}
    unique_articles = []
    duplicates = []
    for art in caderno:
        title = art['title'].strip()
        # Normalize for comparison
        key = re.sub(r'\s+', ' ', title.lower().strip())
        key = key.rstrip('.')

        # Skip non-article entries (editorial credits, etc.)
        if any(skip in title.lower() for skip in ('coordenação editorial', 'comissão organizadora', 'comitê científico')):
            print(f"  SKIP editorial: {title[:60]}")
            continue

        # Replace parsing artifact with manual fix
        if len(title) > 300:
            print(f"  FIX artifact → '{glauco_fix['title'][:60]}...'")
            art = glauco_fix
            title = art['title']
            key = re.sub(r'\s+', ' ', title.lower().strip()).rstrip('.')

        if key in seen_titles:
            duplicates.append((title, art['section'], seen_titles[key]))
        else:
            seen_titles[key] = art['section']
            unique_articles.append(art)

    print(f"Unique articles: {len(unique_articles)} (removed {len(duplicates)} duplicates)")
    for title, sec, orig_sec in duplicates:
        print(f"  Duplicate: '{title[:60]}' ({sec} vs {orig_sec})")

    # Section mapping
    section_map = {
        'ORAL': 'Apresentação Oral',
        'POSTER': 'Poster Digital',
        'DOCOJOVEM': 'Doco Jovem',
    }

    # Build articles
    articles = []
    for i, art in enumerate(unique_articles, 1):
        title = normalize_title(art['title'])
        section = section_map.get(art['section'], art['section'])

        # Parse authors
        authors = []
        for raw_author in art.get('authors', []):
            # Skip parsing artifacts (abstract text captured as author)
            if len(raw_author) > 60:
                continue
            # Skip if it looks like abstract text (lowercase words, no comma pattern)
            if ',' not in raw_author:
                continue
            # Skip if contains common abstract starter words
            raw_lower = raw_author.lower()
            if any(w in raw_lower for w in ('durante', 'presente', 'artigo', 'estudo', 'objetivo')):
                continue
            parsed = parse_author(raw_author)
            if parsed:
                authors.append(parsed)

        if not authors:
            print(f"  WARNING: no authors for '{title[:60]}'")
            continue

        # Clean keywords
        keywords = clean_keywords(art.get('keywords', []))

        # Abstract
        abstract = art.get('abstract', '').strip()
        # Remove author initials that leaked into abstract start
        # Pattern: "COTRIM. M." or "SANTOS,R. S." or "ALVES,A. A. A."
        # Repeat to handle multiple leaked authors
        for _ in range(3):
            abstract = re.sub(
                r'^[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ]{2,}[\.,]\s*(?:[A-Z]\.\s*)+',
                '', abstract
            ).strip()

        entry = OrderedDict()
        entry['id'] = i
        entry['title'] = title
        entry['authors'] = authors
        entry['section'] = section
        entry['abstract'] = abstract
        if keywords:
            entry['keywords'] = keywords
        entry['pages'] = ''

        articles.append(entry)

    # Count by section
    by_section = {}
    for a in articles:
        sec = a['section']
        by_section[sec] = by_section.get(sec, 0) + 1

    print(f"\nArticles by section:")
    for sec, count in by_section.items():
        print(f"  {sec}: {count}")
    print(f"  Total: {len(articles)}")

    # Build YAML
    issue = OrderedDict([
        ('slug', 'sdnne06'),
        ('title', '6º Seminário Docomomo Norte/Nordeste, Teresina, 2016'),
        ('subtitle', 'Arquitetura — tectônica e lugar'),
        ('year', 2016),
        ('volume', 3),
        ('number', 6),
        ('date_published', '2016-08-10'),
        ('isbn', '978-85-7463-919-2'),
        ('publisher', 'UFPI'),
        ('description', (
            'DOCOMOMO Norte/Nordeste (6.:2016:.Teresina, PI)\n'
            'Arquitetura: tectônica e lugar / VI DOCOMOMO Norte/Nordeste. — Teresina, 2016.\n'
            '200p. il.\n'
            'ISBN 978-85-7463-919-2\n'
            'Seminário realizado em Teresina de 10 a 13 de agosto de 2016.\n'
            '1. Patrimônio e cidade. 2. História e cidade. I. Título. II. Afonso, Alcília.\n'
            'CDD 725.948 122'
        )),
        ('editors', [
            OrderedDict([('givenname', 'Alcília'), ('familyname', 'Afonso')]),
        ]),
        ('sections', [
            OrderedDict([('title', 'Apresentação Oral'), ('abbrev', 'AO-sdnne06')]),
            OrderedDict([('title', 'Poster Digital'), ('abbrev', 'PD-sdnne06')]),
            OrderedDict([('title', 'Doco Jovem'), ('abbrev', 'DJ-sdnne06')]),
        ]),
    ])

    doc = OrderedDict([
        ('issue', issue),
        ('articles', articles),
    ])

    # Write YAML
    yaml_str = yaml.dump(doc, Dumper=OrderedDumper, default_flow_style=False,
                         allow_unicode=True, width=10000, sort_keys=False)

    # Add header comment
    header = '# 6º Seminário Docomomo Norte/Nordeste — Teresina (2016)\n'
    header += '# Fonte: caderno de resumos (apenas resumos, sem textos completos)\n'
    header += '# Autores listados com iniciais — expandir quando possível\n\n'
    yaml_str = header + yaml_str

    OUT_YAML.write_text(yaml_str, encoding='utf-8')
    print(f"\nYAML written to {OUT_YAML}")
    print(f"Total: {len(articles)} articles")


if __name__ == '__main__':
    main()
