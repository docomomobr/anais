#!/usr/bin/env python3
"""
Clean up header artifacts from references in sdsp08.yaml.
The PDF header "A ARQUITETURA E URBANISMO MODERNOS E OS ACERVOS" was captured
as part of some references. This script:
1. Removes entries that are ONLY the header text (with optional "MESA N")
2. Removes entries that are ONLY the header + "ORGANIZAÇÃO DO EVENTO"
3. Strips the header prefix from entries where real reference text follows
"""

import os
import re
import yaml
from collections import OrderedDict

BASE = "/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp"
HEADER = "A ARQUITETURA E URBANISMO MODERNOS E OS ACERVOS"

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


def clean_refs(refs):
    """Clean header artifacts from a list of references."""
    if not refs:
        return refs
    cleaned = []
    removed = 0
    stripped = 0
    for ref in refs:
        s = ref.strip()
        # Case 1: exactly the header (with optional MESA N suffix)
        if re.match(r'^A ARQUITETURA E URBANISMO MODERNOS E OS ACERVOS(\s+MESA\s+\d+)?$', s):
            removed += 1
            continue
        # Case 2: header + ORGANIZAÇÃO DO EVENTO
        if s.startswith(HEADER) and 'ORGANIZAÇÃO DO EVENTO' in s:
            removed += 1
            continue
        # Case 3: header prepended to real reference text
        if s.startswith(HEADER):
            rest = s[len(HEADER):].strip()
            if rest and len(rest) >= 15:
                cleaned.append(rest)
                stripped += 1
                continue
            else:
                removed += 1
                continue
        cleaned.append(ref)
    return cleaned if cleaned else None, removed, stripped


def process(slug):
    yaml_path = os.path.join(BASE, f"{slug}.yaml")
    print(f"\nProcessing {slug}...")

    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.load(f, Loader=OrderedLoader)

    total_removed = 0
    total_stripped = 0
    articles_affected = 0

    for art in data['articles']:
        refs = art.get('references')
        if not refs:
            continue
        cleaned, removed, stripped = clean_refs(refs)
        if removed > 0 or stripped > 0:
            articles_affected += 1
            total_removed += removed
            total_stripped += stripped
            if cleaned:
                art['references'] = cleaned
            else:
                del art['references']
            print(f"  {art['id']}: removed {removed}, stripped prefix from {stripped}")

    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)

    print(f"  Total: {articles_affected} articles affected, {total_removed} entries removed, {total_stripped} prefixes stripped")


if __name__ == '__main__':
    process('sdsp08')
