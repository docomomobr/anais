#!/usr/bin/env python3
"""
Extrai referências bibliográficas dos PDFs dos seminários SP e atualiza os YAMLs.

Uso:
    python3 extrair_refs_sp.py sdsp03
    python3 extrair_refs_sp.py sdsp05
    python3 extrair_refs_sp.py sdsp06
    python3 extrair_refs_sp.py sdsp03 sdsp05 sdsp06   # todos de uma vez
"""

import yaml
import re
import sys
import subprocess
from pathlib import Path
from collections import OrderedDict

BASE_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp")

# --- OrderedDumper para preservar ordem dos campos ---

class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

OrderedDumper.add_representer(dict, dict_representer)
OrderedDumper.add_representer(OrderedDict, dict_representer)


# --- Ordem canônica dos campos de artigo ---

FIELD_ORDER = [
    'id', 'title', 'subtitle', 'authors', 'section', 'locale', 'file',
    'pages_count', 'pages', 'pdf_original', 'abstract', 'abstract_en',
    'keywords', 'keywords_en', 'references', 'revisado',
]

def reorder_article(art):
    """Reordena campos do artigo conforme FIELD_ORDER, preservando campos extras."""
    ordered = OrderedDict()
    for key in FIELD_ORDER:
        if key in art:
            ordered[key] = art[key]
    # Campos não previstos ficam antes de 'revisado'
    for key in art:
        if key not in ordered:
            ordered[key] = art[key]
    return dict(ordered)


# --- Extração de referências ---

def extract_text_from_pdf(pdf_path):
    """Extrai texto do PDF usando pdftotext -layout."""
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', str(pdf_path), '-'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def extract_refs(text):
    """Busca seção de referências no texto extraído."""
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
    """Parseia bloco de texto em referências individuais."""
    # Remove números de página soltos
    block = re.sub(r"\n\s*\d{1,3}\s*$", "\n", block, flags=re.MULTILINE)

    # Corta antes de seções não-referência
    for marker in [
        "Créditos das imagens", "Créditos", "CRÉDITOS",
        "Legendas", "LEGENDAS", "Notas", "NOTAS",
    ]:
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

        # Detecta início de nova referência
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

    # Limpa e filtra
    cleaned = []
    for r in refs:
        r = re.sub(r"\s+", " ", r).strip()
        if len(r) < 15:
            continue
        if r.startswith("Imprimir") or r.startswith("Fechar"):
            continue
        # Remove marcadores de página tipo "·15·" no final
        r = re.sub(r"\s*·\d+·\s*$", "", r)
        cleaned.append(r)

    return cleaned or None


# --- Processamento principal ---

def process_seminar(slug):
    """Processa um seminário: lê YAML, extrai refs dos PDFs, atualiza YAML."""
    yaml_path = BASE_DIR / f"{slug}.yaml"
    pdf_dir = BASE_DIR / slug / "pdfs"

    if not yaml_path.exists():
        print(f"ERRO: {yaml_path} não encontrado")
        return
    if not pdf_dir.exists():
        print(f"ERRO: {pdf_dir} não encontrado")
        return

    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    articles = data.get('articles', [])
    total = len(articles)
    before = sum(1 for a in articles if a.get('references'))
    extracted = 0
    failed = 0

    for art in articles:
        art_id = art.get('id', '?')

        # Pula se já tem referências
        if art.get('references'):
            continue

        pdf_file = art.get('file')
        if not pdf_file:
            print(f"  {art_id}: sem campo 'file'")
            failed += 1
            continue

        pdf_path = pdf_dir / pdf_file
        if not pdf_path.exists():
            print(f"  {art_id}: PDF não encontrado: {pdf_path}")
            failed += 1
            continue

        text = extract_text_from_pdf(pdf_path)
        if not text:
            print(f"  {art_id}: falha ao extrair texto do PDF")
            failed += 1
            continue

        refs = extract_refs(text)
        if refs:
            art['references'] = refs
            extracted += 1
        else:
            failed += 1

    after = sum(1 for a in articles if a.get('references'))

    # Reordena campos de cada artigo
    data['articles'] = [reorder_article(a) for a in articles]

    # Salva YAML
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)

    print(f"\n{'='*60}")
    print(f"{slug}: {total} artigos total")
    print(f"  Referências ANTES:  {before}")
    print(f"  Referências DEPOIS: {after}")
    print(f"  Extraídas agora:    {extracted}")
    print(f"  Sem referências:    {failed}")
    print(f"{'='*60}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python3 extrair_refs_sp.py <slug> [slug2] [slug3]")
        print("Exemplo: python3 extrair_refs_sp.py sdsp03 sdsp05 sdsp06")
        sys.exit(1)

    for slug in sys.argv[1:]:
        print(f"\nProcessando {slug}...")
        process_seminar(slug)
