#!/usr/bin/env python3
"""Divide um PDF compilado em PDFs individuais por artigo, usando dados do YAML."""
import yaml
import subprocess
import os
import sys
import shutil

def split_pdf(yaml_path, pdf_source, output_dir, keep_compiled=True):
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    slug = data['issue']['slug']
    articles = data['articles']
    os.makedirs(output_dir, exist_ok=True)

    # Copiar PDF compilado para o diretório
    if keep_compiled:
        compiled_dest = os.path.join(output_dir, f'{slug}_anais.pdf')
        if not os.path.exists(compiled_dest):
            shutil.copy2(pdf_source, compiled_dest)
            size_mb = os.path.getsize(compiled_dest) / (1024*1024)
            print(f"PDF compilado copiado: {compiled_dest} ({size_mb:.1f} MB)")

    # Obter número total de páginas do PDF
    result = subprocess.run(['pdfinfo', pdf_source], capture_output=True, text=True)
    total_pages = None
    for line in result.stdout.split('\n'):
        if line.startswith('Pages:'):
            total_pages = int(line.split(':')[1].strip())
            break

    if not total_pages:
        print("ERRO: Não foi possível obter número de páginas")
        return

    print(f"PDF fonte: {pdf_source} ({total_pages} páginas)")
    print(f"Artigos: {len(articles)}")

    sucesso = 0
    erros = 0

    for i, art in enumerate(articles):
        art_id = art['id']
        pages = art.get('pages', '')
        if not pages or '-' not in pages:
            print(f"  SKIP {art_id}: sem páginas definidas")
            erros += 1
            continue

        start, end = pages.split('-')
        start = int(start)
        end = int(end)

        # Garantir que end não exceda total
        if end > total_pages:
            end = total_pages

        output_pdf = os.path.join(output_dir, f'{art_id}.pdf')

        try:
            subprocess.run([
                'qpdf', pdf_source,
                '--pages', '.', f'{start}-{end}', '--',
                output_pdf
            ], check=True, capture_output=True)

            size_kb = os.path.getsize(output_pdf) / 1024
            if size_kb < 5:
                print(f"  WARN {art_id}: muito pequeno ({size_kb:.1f} KB)")
            sucesso += 1
        except subprocess.CalledProcessError as e:
            print(f"  ERRO {art_id}: {e.stderr.decode()[:100]}")
            erros += 1

    print(f"\nResultado: {sucesso} extraídos, {erros} erros")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Uso: python3 split_pdf.py <yaml_path> <pdf_source>")
        sys.exit(1)

    yaml_path = sys.argv[1]
    pdf_source = sys.argv[2]

    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    slug = data['issue']['slug']
    base_dir = os.path.dirname(yaml_path)
    output_dir = os.path.join(base_dir, slug, 'pdfs')

    split_pdf(yaml_path, pdf_source, output_dir)
