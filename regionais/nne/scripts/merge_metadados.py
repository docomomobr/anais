#!/usr/bin/env python3
"""
Merge de metadados extraídos nos YAMLs principais dos seminários regionais N/NE.

Preenche: abstract, keywords, abstract_en, keywords_en, file, id.
Mapeia por número sequencial (chave do PDF → índice do artigo).
"""

import yaml
import re
from pathlib import Path

BASE = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/nne")


class OrderedDumper(yaml.SafeDumper):
    pass


def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


OrderedDumper.add_representer(dict, dict_representer)


def salvar_yaml(caminho, dados):
    """Salva YAML preservando ordem dos campos."""
    with open(caminho, 'w', encoding='utf-8') as f:
        yaml.dump(dados, f, Dumper=OrderedDumper, default_flow_style=False,
                  allow_unicode=True, width=10000, sort_keys=False)


def extrair_numero(nome_pdf):
    """Extrai o número sequencial do nome do PDF (ex: '001_foo.pdf' → 1)."""
    m = re.match(r'^(\d+)_', nome_pdf)
    return int(m.group(1)) if m else None


def limpar_keywords(kw_list):
    """Remove lixo no final de keywords (ex: 'Modernism. !' ou sufixos de seminário)."""
    if not kw_list:
        return []
    resultado = []
    for kw in kw_list:
        # Remove sufixos tipo "9° Seminário Docomomo Norte e Nordeste..."
        kw = re.sub(r'\s*\d+[°º]\s*Semin[áa]rio\s+Docomomo.*$', '', kw, flags=re.IGNORECASE)
        # Remove pontuação no final (ponto, exclamação, espaços)
        kw = re.sub(r'[\s.!]+$', '', kw)
        kw = kw.strip()
        if kw:
            resultado.append(kw)
    return resultado


def processar_seminario(slug):
    """Processa um seminário: merge metadados + mapeamento PDFs + IDs."""
    yaml_principal = BASE / f"{slug}.yaml"
    metadados_file = BASE / slug / f"metadados_extraidos_{slug}.yaml"
    pdf_dir = BASE / slug / "pdfs"

    print(f"\n{'='*60}")
    print(f"Processando {slug}")
    print(f"{'='*60}")

    # Carregar YAML principal
    with open(yaml_principal, 'r', encoding='utf-8') as f:
        dados = yaml.safe_load(f)

    articles = dados['articles']
    print(f"Artigos no YAML: {len(articles)}")

    # Carregar metadados extraídos
    with open(metadados_file, 'r', encoding='utf-8') as f:
        metadados = yaml.safe_load(f)

    print(f"Entradas nos metadados: {len(metadados)}")

    # Indexar metadados por número sequencial
    meta_por_num = {}
    for nome_pdf, meta in metadados.items():
        num = extrair_numero(nome_pdf)
        if num is not None:
            meta_por_num[num] = meta
            meta_por_num[num]['_pdf_key'] = nome_pdf

    # Listar PDFs disponíveis
    pdfs_disponiveis = sorted(pdf_dir.glob("*.pdf"))
    pdf_por_num = {}
    for pdf_path in pdfs_disponiveis:
        num = extrair_numero(pdf_path.name)
        if num is not None:
            pdf_por_num[num] = pdf_path

    print(f"PDFs no diretório: {len(pdf_por_num)}")

    # Estatísticas
    merge_ok = 0
    merge_fail = 0
    pdf_ok = 0
    pdf_extra = []

    for i, artigo in enumerate(articles):
        num = i + 1  # Artigos começam em 1

        # Adicionar ID
        artigo_id = f"{slug}-{num:03d}"
        artigo['id'] = artigo_id

        # Merge de metadados
        if num in meta_por_num:
            meta = meta_por_num[num]

            # Resumo/abstract (português → campo 'abstract' do OJS)
            if meta.get('resumo'):
                artigo['abstract'] = meta['resumo'].strip()

            # Abstract em inglês
            if meta.get('abstract'):
                artigo['abstract_en'] = meta['abstract'].strip()

            # Palavras-chave (português)
            if meta.get('palavras_chave'):
                artigo['keywords'] = limpar_keywords(meta['palavras_chave'])

            # Keywords em inglês
            if meta.get('keywords'):
                artigo['keywords_en'] = limpar_keywords(meta['keywords'])

            merge_ok += 1
        else:
            merge_fail += 1
            print(f"  AVISO: artigo #{num} ({artigo.get('title', '?')[:50]}) sem metadados")

        # Mapeamento de PDF
        if num in pdf_por_num:
            artigo['file'] = pdf_por_num[num].name
            pdf_ok += 1
        else:
            print(f"  AVISO: artigo #{num} ({artigo.get('title', '?')[:50]}) sem PDF")

    # Identificar PDFs extras (sem artigo correspondente)
    for num in sorted(pdf_por_num.keys()):
        if num > len(articles):
            pdf_extra.append(pdf_por_num[num].name)
            print(f"  PDF EXTRA: {pdf_por_num[num].name} (nº {num}, sem artigo correspondente)")

    # Identificar metadados extras (sem artigo correspondente)
    for num in sorted(meta_por_num.keys()):
        if num > len(articles):
            print(f"  METADADOS EXTRA: {meta_por_num[num]['_pdf_key']} (nº {num}, sem artigo correspondente)")

    # Reordenar campos dos artigos
    ordem_campos = [
        'id', 'title', 'subtitle', 'abstract', 'abstract_en',
        'keywords', 'keywords_en', 'section', 'pages', 'file',
        'locale', 'authors'
    ]

    articles_ordenados = []
    for artigo in articles:
        artigo_ord = {}
        for campo in ordem_campos:
            if campo in artigo:
                artigo_ord[campo] = artigo[campo]
        # Campos extras não listados
        for campo in artigo:
            if campo not in artigo_ord:
                artigo_ord[campo] = artigo[campo]
        articles_ordenados.append(artigo_ord)

    dados['articles'] = articles_ordenados

    # Salvar
    salvar_yaml(yaml_principal, dados)

    print(f"\nResumo {slug}:")
    print(f"  Metadados mesclados: {merge_ok}/{len(articles)}")
    print(f"  Sem metadados:       {merge_fail}")
    print(f"  PDFs mapeados:       {pdf_ok}/{len(articles)}")
    print(f"  PDFs extras:         {len(pdf_extra)}")
    if pdf_extra:
        for p in pdf_extra:
            print(f"    - {p}")


def main():
    processar_seminario("sdnne07")
    processar_seminario("sdnne09")
    print("\nConcluído!")


if __name__ == "__main__":
    main()
