#!/usr/bin/env python3
"""
Limpa keywords malformados nos YAMLs dos seminários SP.

Problemas tratados:
1. Keywords concatenadas com ponto (.) como separador — split em itens separados
2. Números de página soltos no final (ex: "Curitiba. 32")
3. Títulos de artigos em CAIXA ALTA embutidos (ex: "MODERN ARCHITECTURE IN BRAZIL")
4. Headers de seção/seminário (ex: "A ARQUITETURA MODERNA PAULISTA E A QUESTÃO SOCIAL")
5. Fragmentos em espanhol/inglês no campo PT e vice-versa
6. Lixo de extração (prefixos `: `, `s: `, date ranges soltos)
"""

import yaml
import re
import sys
from pathlib import Path

BASE_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp")

class OrderedDumper(yaml.SafeDumper):
    pass
def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())
OrderedDumper.add_representer(dict, dict_representer)

# Padrões de lixo explícitos (case-insensitive)
GARBAGE_PATTERNS = [
    r'^\d{1,4}$',                    # número de página sozinho
    r'^\d{4}-\d{4}$',               # date range sozinho (1945-1953)
    r'SEMINÁRIO',                    # header de seminário
    r'DOCOMOMO',                     # nome do evento
    r'^Key-?words?\s*:',            # rótulo de keywords embutido
    r'^Palabras\s*clave',           # rótulo em espanhol
]


def eh_lixo(kw):
    """Verifica se uma keyword é lixo (título de artigo, cabeçalho, número de página)."""
    kw_stripped = kw.strip()
    if not kw_stripped:
        return True

    # Número de página sozinho
    if re.match(r'^\d{1,4}\s*$', kw_stripped):
        return True

    # Padrões de lixo explícitos
    for pat in GARBAGE_PATTERNS:
        if re.search(pat, kw_stripped, re.IGNORECASE):
            return True

    # Heurística: se >55% letras são maiúsculas e tem mais de 12 chars alpha,
    # provavelmente é título de artigo (ALL CAPS), não keyword
    alpha = [c for c in kw_stripped if c.isalpha()]
    if len(alpha) > 12:
        upper_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha)
        if upper_ratio > 0.55:
            return True

    # Começa com número de página seguido de texto (ex: "309 UNICAMP: CONCEPT")
    if re.match(r'^\d{2,4}\s+[A-Z]', kw_stripped):
        return True

    # String muito longa provavelmente é abstract ou corpo de texto
    if len(kw_stripped) > 100:
        return True

    return False


def limpar_keyword(kw):
    """Limpa uma keyword individual."""
    kw = kw.strip()
    # Remover prefixos de lixo de extração (": ", "s: ")
    kw = re.sub(r'^[s:]+\s+', '', kw)
    # Remover ponto final, ponto e vírgula final, espaços
    kw = re.sub(r'[\s.;!,]+$', '', kw)
    kw = kw.strip()
    return kw


def split_keywords(kw_list):
    """
    Recebe lista de keywords (pode ter itens concatenados com '.')
    e retorna lista limpa com keywords individuais.
    """
    resultado = []

    for item in kw_list:
        if not isinstance(item, str):
            continue

        # Split por '. ' (ponto seguido de espaço) ou '.' colado em maiúscula
        parts = re.split(r'\.\s+|\.(?=[A-Z])', item)

        for part in parts:
            part = limpar_keyword(part)
            if not part:
                continue
            if eh_lixo(part):
                continue

            # Checar se termina com número de página colado
            # Ex: "SOCIAL 21" ou "DOCOMOMO 135"
            m = re.match(r'^(.+?)\s+\d{1,4}\s*$', part)
            if m:
                part_clean = limpar_keyword(m.group(1))
                if part_clean and not eh_lixo(part_clean):
                    resultado.append(part_clean)
                continue

            resultado.append(part)

    return resultado


def processar_yaml(yaml_path, dry_run=False):
    """Processa um YAML, limpando keywords e keywords_en."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    slug = data['issue']['slug']
    alterados = 0
    total_antes = 0
    total_depois = 0

    for art in data['articles']:
        art_id = art.get('id', '?')

        for campo in ['keywords', 'keywords_en']:
            kw_orig = art.get(campo)
            if not kw_orig or not isinstance(kw_orig, list):
                continue

            total_antes += len(kw_orig)
            kw_limpo = split_keywords(kw_orig)
            total_depois += len(kw_limpo)

            if kw_limpo != kw_orig:
                if dry_run:
                    print(f"  {art_id} [{campo}]:")
                    print(f"    ANTES: {kw_orig}")
                    print(f"    DEPOIS: {kw_limpo}")
                    print()
                art[campo] = kw_limpo if kw_limpo else None
                alterados += 1

        # Remover campo se ficou None
        if art.get('keywords') is None and 'keywords' in art:
            del art['keywords']
        if art.get('keywords_en') is None and 'keywords_en' in art:
            del art['keywords_en']

    if not dry_run and alterados > 0:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                      default_flow_style=False, width=10000, sort_keys=False)

    print(f"{slug}: {alterados} campos alterados ({total_antes} kw antes → {total_depois} depois)")
    return alterados


def main():
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("=== DRY RUN (sem alterações) ===\n")

    yamls = sorted(BASE_DIR.glob("sdsp*.yaml"))
    total = 0
    for yp in yamls:
        total += processar_yaml(yp, dry_run=dry_run)

    print(f"\n{'='*60}")
    print(f"Total: {total} campos alterados em {len(yamls)} arquivos")
    if dry_run:
        print("(nenhuma alteração feita — remover --dry-run para aplicar)")


if __name__ == '__main__':
    main()
