#!/usr/bin/env python3
"""Constrói o YAML do sdsp03 a partir dos metadados extraídos + seções do PPT."""

import yaml
import re
import os
import shutil

# --- Mapeamento PDF → Seção (do programa no PPT) ---

SECOES = {
    # Comunicações Orais - Centralidade e verticalização
    '102': 'Comunicações Orais - Centralidade e verticalização',
    '23':  'Comunicações Orais - Centralidade e verticalização',
    '52':  'Comunicações Orais - Centralidade e verticalização',
    '66':  'Comunicações Orais - Centralidade e verticalização',
    '84':  'Comunicações Orais - Centralidade e verticalização',
    '97':  'Comunicações Orais - Centralidade e verticalização',
    '21':  'Comunicações Orais - Centralidade e verticalização',
    '17':  'Comunicações Orais - Centralidade e verticalização',
    '76':  'Comunicações Orais - Centralidade e verticalização',
    '98':  'Comunicações Orais - Centralidade e verticalização',

    # Comunicações Orais - Da habitação mínima aos bairros-jardim
    '22':  'Comunicações Orais - Da habitação mínima aos bairros-jardim',
    '63':  'Comunicações Orais - Da habitação mínima aos bairros-jardim',
    '42':  'Comunicações Orais - Da habitação mínima aos bairros-jardim',
    '18':  'Comunicações Orais - Da habitação mínima aos bairros-jardim',

    # Comunicações Orais - Formação de acervos: documentação e inventários
    '48':  'Comunicações Orais - Formação de acervos',
    '26':  'Comunicações Orais - Formação de acervos',
    '99':  'Comunicações Orais - Formação de acervos',
    '92':  'Comunicações Orais - Formação de acervos',
    '56':  'Comunicações Orais - Formação de acervos',
    '54':  'Comunicações Orais - Formação de acervos',
    '53':  'Comunicações Orais - Formação de acervos',

    # Comunicações Orais - Paisagem e ambiente urbano
    '04':  'Comunicações Orais - Paisagem e ambiente urbano',
    '82':  'Comunicações Orais - Paisagem e ambiente urbano',
    '24':  'Comunicações Orais - Paisagem e ambiente urbano',
    '91':  'Comunicações Orais - Paisagem e ambiente urbano',
    '06':  'Comunicações Orais - Paisagem e ambiente urbano',
    '33':  'Comunicações Orais - Paisagem e ambiente urbano',
    '14':  'Comunicações Orais - Paisagem e ambiente urbano',
    '61':  'Comunicações Orais - Paisagem e ambiente urbano',
    '19':  'Comunicações Orais - Paisagem e ambiente urbano',
    '36':  'Comunicações Orais - Paisagem e ambiente urbano',

    # Comunicações Orais - Projetos de conservação e restauro
    '27':  'Comunicações Orais - Projetos de conservação e restauro',
    '28':  'Comunicações Orais - Projetos de conservação e restauro',
    '45':  'Comunicações Orais - Projetos de conservação e restauro',

    # Painéis - Centralidade e verticalização
    '64':  'Painéis - Centralidade e verticalização',
    '02':  'Painéis - Centralidade e verticalização',
    '13':  'Painéis - Centralidade e verticalização',
    '57':  'Painéis - Centralidade e verticalização',
    '58':  'Painéis - Centralidade e verticalização',
    '15':  'Painéis - Centralidade e verticalização',
    '62':  'Painéis - Centralidade e verticalização',
    '35':  'Painéis - Centralidade e verticalização',
    '93':  'Painéis - Centralidade e verticalização',
    '59':  'Painéis - Centralidade e verticalização',
    '01':  'Painéis - Centralidade e verticalização',

    # Painéis - Da habitação mínima aos bairros-jardim
    '31':  'Painéis - Da habitação mínima aos bairros-jardim',
    '73':  'Painéis - Da habitação mínima aos bairros-jardim',
    '30':  'Painéis - Da habitação mínima aos bairros-jardim',
    '05':  'Painéis - Da habitação mínima aos bairros-jardim',

    # Painéis - Formação de acervos
    '29':  'Painéis - Formação de acervos',
    '41':  'Painéis - Formação de acervos',
    '71':  'Painéis - Formação de acervos',
    '49':  'Painéis - Formação de acervos',
    '39':  'Painéis - Formação de acervos',
    '75':  'Painéis - Formação de acervos',
    '77':  'Painéis - Formação de acervos',
    '03':  'Painéis - Formação de acervos',
    '86':  'Painéis - Formação de acervos',
    '89':  'Painéis - Formação de acervos',
    '69':  'Painéis - Formação de acervos',
    '100': 'Painéis - Formação de acervos',
    '74':  'Painéis - Formação de acervos',

    # Painéis - Paisagem e ambiente urbano
    '34':  'Painéis - Paisagem e ambiente urbano',
    '50':  'Painéis - Paisagem e ambiente urbano',
    '51':  'Painéis - Paisagem e ambiente urbano',
    '10':  'Painéis - Paisagem e ambiente urbano',
    '40':  'Painéis - Paisagem e ambiente urbano',
    '94':  'Painéis - Paisagem e ambiente urbano',
    '38':  'Painéis - Paisagem e ambiente urbano',
    '90':  'Painéis - Paisagem e ambiente urbano',

    # Painéis - Projetos de conservação e restauro
    '16':  'Painéis - Projetos de conservação e restauro',
    '43':  'Painéis - Projetos de conservação e restauro',
    '44':  'Painéis - Projetos de conservação e restauro',
    '32':  'Painéis - Projetos de conservação e restauro',
}


def parse_authors(author_str):
    """Parseia string de autores para lista de dicts givenname/familyname."""
    # Limpar marcadores de nota de rodapé
    author_str = re.sub(r'[*]+\d*|\d+[*]+', '', author_str)
    author_str = author_str.strip()

    # Separar por ;
    names = [n.strip() for n in author_str.split(';') if n.strip()]

    authors = []
    for i, name in enumerate(names):
        # Limpar trailing artifacts
        name = re.sub(r'\s*T$', '', name)  # e.g. "RegoT"
        name = name.strip(' ,.')
        if not name:
            continue

        parts = name.split()
        if len(parts) == 1:
            authors.append({
                'givenname': parts[0],
                'familyname': parts[0],
                'affiliation': '',
                'email': f'{parts[0].lower()}@exemplo.com',
                'primary_contact': i == 0,
            })
        else:
            familyname = parts[-1]
            givenname = ' '.join(parts[:-1])
            # Partículas ficam no givenname
            email_base = familyname.lower()
            email_base = re.sub(r'[^a-z]', '', email_base)
            authors.append({
                'givenname': givenname,
                'familyname': familyname,
                'affiliation': '',
                'email': f'{email_base}@exemplo.com',
                'primary_contact': i == 0,
            })
    return authors


def parse_metadata_file(filepath):
    """Lê o arquivo de metadados extraídos."""
    with open(filepath) as f:
        text = f.read()

    articles = []
    blocks = re.split(r'---\n', text)

    for block in blocks:
        m = re.search(r'=== (\d+)\.pdf \((\d+) pages?\) ===', block)
        if not m:
            continue
        pdf_num = m.group(1)
        pages = int(m.group(2))

        title_m = re.search(r'TITLE: (.+)', block)
        authors_m = re.search(r'AUTHORS: (.+)', block)
        resumo_m = re.search(r'RESUMO: (.+)', block)
        kw_m = re.search(r'KEYWORDS: (.+)', block)

        title = title_m.group(1).strip() if title_m else ''
        authors_raw = authors_m.group(1).strip() if authors_m else ''
        resumo = resumo_m.group(1).strip() if resumo_m else ''
        keywords_raw = kw_m.group(1).strip() if kw_m else ''

        # Keywords
        keywords = []
        if keywords_raw and keywords_raw != '[NOT FOUND]':
            # Separar por ; ou ,
            if ';' in keywords_raw:
                keywords = [k.strip().rstrip('.,;') for k in keywords_raw.split(';') if k.strip()]
            else:
                keywords = [k.strip().rstrip('.,;') for k in keywords_raw.split(',') if k.strip()]
            # Limpar keywords com :: como separador
            cleaned = []
            for kw in keywords:
                if '::' in kw:
                    cleaned.extend([k.strip() for k in kw.split('::') if k.strip()])
                else:
                    cleaned.append(kw)
            keywords = [k for k in cleaned if k]

        articles.append({
            'pdf_num': pdf_num,
            'pages_count': pages,
            'title': title,
            'authors_raw': authors_raw,
            'resumo': resumo,
            'keywords': keywords,
        })

    return articles


def main():
    basedir = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp'
    metadados = parse_metadata_file('/tmp/sdsp03_metadados_extraidos.txt')

    # Ordenar por número do PDF
    metadados.sort(key=lambda a: int(a['pdf_num']))

    # Renomear PDFs: 01.pdf → sdsp03-001.pdf
    pdfs_dir = os.path.join(basedir, 'sdsp03', 'pdfs')
    rename_map = {}
    for i, art in enumerate(metadados):
        old_name = f"{art['pdf_num']}.pdf"
        new_name = f"sdsp03-{i+1:03d}.pdf"
        old_path = os.path.join(pdfs_dir, old_name)
        new_path = os.path.join(pdfs_dir, new_name)
        if os.path.exists(old_path) and old_path != new_path:
            # Rename via temp to avoid conflicts
            rename_map[old_path] = new_path

    # Two-pass rename to avoid conflicts
    temp_dir = os.path.join(pdfs_dir, '_temp_rename')
    os.makedirs(temp_dir, exist_ok=True)
    for old_path, new_path in rename_map.items():
        temp_path = os.path.join(temp_dir, os.path.basename(new_path))
        shutil.copy2(old_path, temp_path)
    for old_path in rename_map:
        os.remove(old_path)
    for fname in os.listdir(temp_dir):
        shutil.move(os.path.join(temp_dir, fname), os.path.join(pdfs_dir, fname))
    os.rmdir(temp_dir)

    # Construir YAML
    articles = []
    for i, art in enumerate(metadados):
        idx = i + 1
        art_id = f'sdsp03-{idx:03d}'
        new_pdf = f'sdsp03-{idx:03d}.pdf'

        # Título: separar subtitle no primeiro `: `
        title = art['title']
        subtitle = ''
        # Remover ponto final do título
        title = title.rstrip('.')
        # Limpar asterisco artifact
        title = title.replace('ARQUITETURA*', 'ARQUITETURA')

        if ': ' in title:
            parts = title.split(': ', 1)
            title = parts[0]
            subtitle = parts[1]

        # Seção
        section = SECOES.get(art['pdf_num'], '(sem seção)')

        # Autores
        authors = parse_authors(art['authors_raw'])

        article = {
            'id': art_id,
            'title': title,
        }
        if subtitle:
            article['subtitle'] = subtitle
        article['authors'] = authors
        article['section'] = section
        article['locale'] = 'pt-BR'
        article['file'] = new_pdf
        article['pages_count'] = art['pages_count']
        article['pdf_original'] = f"{art['pdf_num']}.pdf"
        if art['resumo']:
            article['abstract'] = art['resumo']
        if art['keywords']:
            article['keywords'] = art['keywords']

        articles.append(article)

    # Issue metadata
    issue = {
        'slug': 'sdsp03',
        'title': '3º Seminário Docomomo São Paulo',
        'subtitle': 'Permanência e Transitoriedade do Movimento Modernista Paulista',
        'description': '3° Seminário Docomomo São Paulo: Permanência e Transitoriedade do Movimento Modernista Paulista. São Paulo: Universidade Presbiteriana Mackenzie, 2005.',
        'year': 2005,
        'volume': 1,
        'number': 3,
        'date_published': '2005-08-17',
        'isbn': '',
        'publisher': 'Universidade Presbiteriana Mackenzie',
        'editors': [],
        'source': 'CD-ROM dos anais',
    }

    data = {'issue': issue, 'articles': articles}

    # Dumper ordenado
    class OrderedDumper(yaml.SafeDumper):
        pass

    def dict_representer(dumper, data):
        return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

    OrderedDumper.add_representer(dict, dict_representer)

    yaml_path = os.path.join(basedir, 'sdsp03.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, default_flow_style=False,
                  allow_unicode=True, width=10000, sort_keys=False)

    print(f'YAML gerado: {yaml_path}')
    print(f'Artigos: {len(articles)}')
    print(f'PDFs renomeados: {len(rename_map)}')

    # Contagem por seção
    sec_counts = {}
    for a in articles:
        s = a['section']
        sec_counts[s] = sec_counts.get(s, 0) + 1
    for s, c in sorted(sec_counts.items()):
        print(f'  [{c:2d}] {s}')


if __name__ == '__main__':
    main()
