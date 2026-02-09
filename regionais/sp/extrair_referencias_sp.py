#!/usr/bin/env python3
"""
Extract references from PDF files for SP seminars (sdsp07, sdsp08, sdsp09)
and update their YAML files.
"""

import sys
import os
import re
import subprocess
import yaml
from collections import OrderedDict

BASE = "/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp"

# --- OrderedDumper ---
class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

def str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

OrderedDumper.add_representer(OrderedDict, dict_representer)
OrderedDumper.add_representer(dict, dict_representer)
OrderedDumper.add_representer(str, str_representer)

# --- OrderedLoader ---
class OrderedLoader(yaml.SafeLoader):
    pass

def construct_mapping(loader, node):
    loader.flatten_mapping(node)
    pairs = loader.construct_pairs(node)
    return OrderedDict(pairs)

OrderedLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)

# --- Field ordering ---
FIELD_ORDER = [
    'id', 'title', 'subtitle', 'authors', 'section', 'pages', 'locale',
    'file', 'pages_count', 'pdf_original',
    'abstract', 'abstract_en', 'keywords', 'keywords_en',
    'references', 'revisado'
]

def order_article(art):
    ordered = OrderedDict()
    for key in FIELD_ORDER:
        if key in art:
            ordered[key] = art[key]
    # Any remaining keys not in FIELD_ORDER
    for key in art:
        if key not in ordered:
            ordered[key] = art[key]
    return ordered


# --- Reference extraction ---
def extract_refs(text):
    pats = [
        r"(?:^|\n)\s*\d*\s*[.\-\u2013\u2014]?\s*(?:Refer[eê]ncias\s*[Bb]ibliogr[aá]ficas?|REFER[EÊ]NCIAS\s*BIBLIOGR[AÁ]FICAS?)\s*:?\s*\n(.*)",
        r"(?:^|\n)\s*\d*\s*[.\-\u2013\u2014]?\s*(?:Referências|REFERÊNCIAS|Bibliografia|BIBLIOGRAFIA)\s*:?\s*\n(.*)",
        r"(?:^|\n)\s*(?:\d+\s*[.\-\u2013\u2014]\s*)?(?:Referências|REFERÊNCIAS|Bibliografia|BIBLIOGRAFIA|References|REFERENCES)\s*:?\s*\n(.*)",
    ]
    for p in pats:
        m = re.search(p, text, re.DOTALL | re.MULTILINE)
        if m:
            return parse_refs_block(m.group(1).strip())
    return None


def parse_refs_block(block):
    # Remove stray page numbers at end of lines
    block = re.sub(r"\n\s*\d{1,3}\s*$", "\n", block, flags=re.MULTILINE)
    # Trim at known non-reference sections
    for marker in ["Créditos das imagens", "Créditos", "CRÉDITOS",
                    "Legendas", "LEGENDAS", "Notas", "NOTAS"]:
        idx = block.find(marker)
        if idx > 0:
            block = block[:idx]
    lines = block.split("\n")
    refs, cur = [], ""
    for l in lines:
        s = l.strip()
        if not s:
            if cur:
                refs.append(cur.strip())
                cur = ""
            continue
        new_ref = (
            bool(re.match(r"^[A-Z\u00C0-\u00DC][A-Z\u00C0-\u00DC\s,\.]+[,\.]", s))
            or s.startswith("__")
            or s.startswith("Cf. ")
        )
        if new_ref and cur:
            refs.append(cur.strip())
            cur = s
        elif cur:
            cur += " " + s
        else:
            cur = s
    if cur:
        refs.append(cur.strip())
    return [
        re.sub(r"\s+", " ", r).strip()
        for r in refs
        if len(r.strip()) >= 15
        and not r.startswith("Imprimir")
        and not r.startswith("Fechar")
    ] or None


def process_seminar(slug):
    yaml_path = os.path.join(BASE, f"{slug}.yaml")
    pdf_dir = os.path.join(BASE, slug, "pdfs")

    print(f"\n{'='*60}")
    print(f"Processing {slug}")
    print(f"{'='*60}")

    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.load(f, Loader=OrderedLoader)

    articles = data['articles']
    total = len(articles)
    had_refs_before = sum(1 for a in articles if a.get('references'))
    extracted_count = 0
    failed = []

    for i, art in enumerate(articles):
        aid = art['id']
        if art.get('references'):
            continue  # already has references

        pdf_file = art.get('file', '')
        if not pdf_file:
            failed.append((aid, 'no file field'))
            continue

        pdf_path = os.path.join(pdf_dir, pdf_file)
        if not os.path.exists(pdf_path):
            failed.append((aid, f'PDF not found: {pdf_path}'))
            continue

        try:
            result = subprocess.run(
                ['pdftotext', '-layout', pdf_path, '-'],
                capture_output=True, text=True, timeout=30
            )
            text = result.stdout
        except Exception as e:
            failed.append((aid, f'pdftotext error: {e}'))
            continue

        if not text or len(text) < 100:
            failed.append((aid, 'empty/short text'))
            continue

        refs = extract_refs(text)
        if refs:
            art['references'] = refs
            extracted_count += 1
            print(f"  {aid}: {len(refs)} references")
        else:
            failed.append((aid, 'no references section found'))

    # Re-order fields in articles
    data['articles'] = [order_article(a) for a in articles]

    # Write back
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)

    has_refs_after = sum(1 for a in data['articles'] if a.get('references'))

    print(f"\n--- {slug} Statistics ---")
    print(f"  Total articles:          {total}")
    print(f"  With references BEFORE:  {had_refs_before}")
    print(f"  Extracted this run:      {extracted_count}")
    print(f"  With references AFTER:   {has_refs_after}")
    print(f"  Failed/skipped:          {len(failed)}")
    if failed:
        for aid, reason in failed:
            print(f"    {aid}: {reason}")


if __name__ == '__main__':
    seminars = sys.argv[1:] if len(sys.argv) > 1 else ['sdsp07', 'sdsp08', 'sdsp09']
    for slug in seminars:
        process_seminar(slug)
