#!/usr/bin/env python3
"""
split_pdf.py - Split sdsul08 compiled PDF into individual article PDFs
and generate YAML metadata file.

8º Seminário Docomomo Sul, Porto Alegre, 2025
"Infraestrutura / Superestrutura, Cone Sul Global"

Usage:
    python3 split_pdf.py
"""

import subprocess
import os
import sys
import yaml

# --- Configuration ---
BASE_DIR = "/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul/sdsul08"
PDF_DIR = os.path.join(BASE_DIR, "pdfs")
SOURCE_PDF = os.path.join(PDF_DIR, "sdsul08_anais.pdf")
YAML_PATH = "/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul/sdsul08.yaml"
ARTIGOS_DIR = os.path.join(PDF_DIR)

# --- OrderedDumper ---
class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

OrderedDumper.add_representer(dict, dict_representer)

# --- Article data from TOC ---
# Format: (section, start_page, title, authors_str)
# TOC says p553 for "Zonas de contatos" but that's the section divider;
# actual article starts at p555.
ARTICLES_DATA = [
    # Água & Esgoto (14 articles)
    ("Água & Esgoto", 59, "Museu protegido: a trincheira da Fundação Iberê Camargo", "Stéphanie Cerioli"),
    ("Água & Esgoto", 70, "As Piscinas das Marés", "Patricia Hecktheuer"),
    ("Água & Esgoto", 80, "River Basin Heritage: Modernist Hydropower and Knowledge Transfers in Brazil, China, and the Global South", "Yu Yunlong"),
    ("Água & Esgoto", 84, "Barragem do Salto: paisagem antrópica", "Maria Paula Recena"),
    ("Água & Esgoto", 91, "Relações entre o Plano Piloto do Delta do Jacuí e o Relatório Neyrpic", "Bruno Cesar Euphrasio de Mello, Daniel Pitta Fischmann, Eugenia Aumond Kuhn, Geisa Zanini Rorato"),
    ("Água & Esgoto", 95, "O refúgio das águas: um estudo sobre o projeto de Ruy Viveiros de Leiria para o Bairro Mauá na cidade de Canoas/RS", "Anye Theisen"),
    ("Água & Esgoto", 107, "Ruínas em Reconstrução: a Memória e o Simbolismo nas Pontes Destruídas pelas Enchentes no Rio Grande do Sul", "Laura Klajn Baltar, Ana Carolina Santos Pellegrini"),
    ("Água & Esgoto", 117, "Infraestrutura e Expressão: as torres de água de Leo Linzmeyer pelo Brasil nas décadas de 60 e 70", "Brian P. R. de Almeida"),
    ("Água & Esgoto", 131, "Torres de Água dos Conjuntos do IAPI: os projetos de Carlos Frederico Ferreira", "Tiago de Oliveira Andrade, Francisco Spadoni"),
    ("Água & Esgoto", 144, "Niemeyer: o stand pipe de Ribeirão das Lages", "Marcos Almeida"),
    ("Água & Esgoto", 154, "Porto Alegre e a enchente de 1936: uma proposta técnica de defesa em debate na imprensa", "Fabiana Bernardy, Priscila Vargas, Bruno Cesar Euphrasio de Mello"),
    ("Água & Esgoto", 165, "O Muro da Mauá e as Enchentes de 1941 e 2024: História, Desafios Urbanos e Resiliência Climática em Porto Alegre", "Ana Elisa Souto"),
    ("Água & Esgoto", 183, "Cidade Baixa Debaixo D'água: um panorama das transformações urbanas através do histórico das inundações do bairro", "Juliana Giazzon Cavalli"),
    ("Água & Esgoto", 187, "A Gênese do Sistema de Proteção Contra Cheias de Porto Alegre: Desafios Contemporâneos e o Legado Histórico de Hildebrando de Araújo Góes", "Gustavo de Pires Castro, Humberto Teixeira Damilano, Fernanda Saretta"),
    # Viação & Obras Públicas (16 articles)
    ("Viação & Obras Públicas", 199, "A estrutura urbana no plano de Brasília e no plano de Curitiba", "Salvador Gnoato"),
    ("Viação & Obras Públicas", 213, "Infraestrutura como Arquitetura: o caso Linha Férrea da Brasília Extensiva", "Marcela Peres"),
    ("Viação & Obras Públicas", 220, "Conexão Bahia: reflexões em torno do Plano Rodoviário estadual e da remodelação da cidade de Salvador através da revista Técnica (1940-1950)", "José Carlos Huapaya Espinoza, Mirén Arantza Soares Campos, Hiba Ahmad"),
    ("Viação & Obras Públicas", 231, "Urbanismo e paisagem: reflexões sobre o impacto das grandes obras públicas modernas em Caracas (1952-1958)", "José Carlos Huapaya Espinoza, Ruan Carlos Marques Santos"),
    ("Viação & Obras Públicas", 242, "Infraestrutura moderna a serviço da mobilidade: o posto TEXACO dos Irace e a gasolinera ANCAP de Otaegui", "Daniel Pitta Fischmann"),
    ("Viação & Obras Públicas", 261, "Rio-Brasília: havia um posto de gasolina no meio do caminho", "Eduardo Pierrotti Rossetti"),
    ("Viação & Obras Públicas", 265, "O edifício como infraestrutura urbana: Vilanova Artigas e a Rodoviária de Jaú", "Laura Attuati"),
    ("Viação & Obras Públicas", 280, "O legado arquitetônico do BRT de Curitiba", "Fabiano Borba Vianna"),
    ("Viação & Obras Públicas", 291, "Subordinação, aproveitamento e subversão: Marcello Fragelli e o metrô de São Paulo", "Emiliano Homrich Neves da Fontoura, Marta Silveira Peixoto"),
    ("Viação & Obras Públicas", 304, "Desenho unitário, construção fracionada: evolução dos passeios cobertos dos setores para bancos, escritórios e comércio do Plano Piloto de Brasília", "Helena Bender"),
    ("Viação & Obras Públicas", 316, "Estudos para a criação de um ambiente de mobilidade urbana no Vale do Anhangabaú: um ensaio projetual", "André Biselli Sauaia"),
    ("Viação & Obras Públicas", 336, "Evolução intra-urbana das Necrópoles em Bento Gonçalves, RS", "Pauline Fonini Felin, Cristiane Bertoco, William Gallina Marconi"),
    ("Viação & Obras Públicas", 340, "Christiani & Nielsen e a EFSC: uma ponte sobre o rio Itajaí do Sul", "Eduardo Westphal"),
    ("Viação & Obras Públicas", 345, "Auditório Araújo Vianna: a segunda revitalização (2010-2015)", "Cassandra Salton Coradin, Monica Luce Bohrer"),
    ("Viação & Obras Públicas", 352, "Recordar para elaborar: o apagamento do Carandiru", "Kátia Fernanda Marchetto, Ana Carolina Santos Pellegrini"),
    ("Viação & Obras Públicas", 357, "Estrutura e construção da Plataforma Rodoviária de Brasília", "Elcio Gomes, Juliano Caldas de Vasconcellos"),
    # Artesanato & Indústria (7 articles)
    ("Artesanato & Indústria", 375, "Pré-Moldagem como Sistema: um pavilhão industrial da Tramontina por Carlos M. Fayet e Cláudio L. G. Araújo", "Guilherme Biondo Milani, Sergio M. Marques"),
    ("Artesanato & Indústria", 389, "Tijolo Armado: Sistema Arquitetônico, Infraestruturas Reveladas", "Guilherme Osterkamp, Diego Fonseca Brasil"),
    ("Artesanato & Indústria", 394, "Modernidade inclusiva: tetos planos e curvos nos edifícios do CIENTEC - Campus Cachoeirinha", "Carlos Fernando Silva Bahima"),
    ("Artesanato & Indústria", 406, "Memphis S.A.: arquitetura e infraestrutura industrial modernas", "Cristina Gondim, Sergio M. Marques"),
    ("Artesanato & Indústria", 411, "A Cidade Industrial de Porto Alegre: modernidade sob o novo paradigma urbano da capital gaúcha", "Juliano de Faria Rodrigues"),
    ("Artesanato & Indústria", 426, "Várzea do Gravataí: os planos para uma cidade industrial que foram por água abaixo", "Marina Schuler Bonzanini da Luz"),
    ("Artesanato & Indústria", 434, "Resíduos Sólidos: desafios e oportunidades", "Fernanda Jung Drebes"),
    # Climatização & Sustentabilidade (12 articles)
    ("Climatização & Sustentabilidade", 439, "Sistemas de proteção contra cheias e utopias modernas para um bairro operário: Três projetos para a expansão industrial de Porto Alegre", "Kauã Domingues"),
    ("Climatização & Sustentabilidade", 444, "O Conjunto Habitacional Estrela d'Alva (1977-81)", "Carolina Ritter"),
    ("Climatização & Sustentabilidade", 452, "Paisagem, Técnica e Modernidade: Análise dos Planos Urbanísticos para o Bairro Praia de Belas em Porto Alegre (1936;1951)", "Giovanna Copetti Goi, Alessandra Schunski Gonçalves"),
    ("Climatização & Sustentabilidade", 464, "Montadas e Largadas: casas individuais pré-fabricadas perdidas na Amazônia", "Cícero Veiga Oliveira Porto"),
    ("Climatização & Sustentabilidade", 470, "Produção escrita como registro projetual: os Cadernos do Centro de Desenvolvimento de Equipamentos Urbanos e Comunitários (1990-1992)", "Lígia Gimenes Paschoal, Tatiana Sakurai"),
    ("Climatização & Sustentabilidade", 476, "Desconstruindo Clorindo Testa: brises", "Cassandra Salton Coradin"),
    ("Climatização & Sustentabilidade", 479, "Dispositivos Arquitetônicos de Controle Ambiental: uma Investigação na Obra dos Irmãos Roberto", "Mara Eskinazi"),
    ("Climatização & Sustentabilidade", 484, "Heroicos e pragmáticos: a arquitetura latino-americana frente à escassez de recursos", "Cássio Orlandi Sauer, Elisa Toschi Martins"),
    ("Climatização & Sustentabilidade", 488, "Pertinência da forma moderna para regeneração da natureza em dois projetos urbanos para cidades da América do Sul", "Patrícia de Freitas Nerbas"),
    ("Climatização & Sustentabilidade", 498, "O Espaço Público da Alameda de Talca, encontro de Infraestruturas", "Sílvia Sávio Chataignier, Javiera Susana Azocar Weisser"),
    ("Climatização & Sustentabilidade", 512, "Como Estruturar Paisagens: as Torres del Parque de Rogelio Salmona", "Celma Paese, Gianluca Perseu"),
    ("Climatização & Sustentabilidade", 524, "Marina, a cidade de Niemeyer no sertão mineiro", "Rodrigo C. Queiroz, Nícolas Rezende Teixeira"),
    # Agricultura & Pecuária (1 article)
    ("Agricultura & Pecuária", 541, "Estação Experimental de Encruzilhada do Sul: preservação do patrimônio agroindustrial para o desenvolvimento sustentável", "Themis da Silva, Luisa Gertrudis Durán Rocca"),
    # Força & Luz (1 article)
    ("Força & Luz", 555, "Zonas de contatos arquitetônicas e o projeto de Leo Grossman e Winston Ramalho para a Subestação da Copel em Curitiba (1969)", "Isabella Caroline Januário, Felipe Taroh Inoue Sanquetta"),
]

# Section divider pages (section name page + blank page)
SECTION_DIVIDERS = {
    "Água & Esgoto": [57, 58],
    "Viação & Obras Públicas": [197, 198],
    "Artesanato & Indústria": [373, 374],
    "Climatização & Sustentabilidade": [437, 438],
    "Agricultura & Pecuária": [539, 540],
    "Força & Luz": [553, 554],
}

# Last article content page (before PROjeto section at p567)
LAST_CONTENT_PAGE = 566


def parse_author_name(full_name):
    """Split full name into givenname and familyname (Brazilian convention).
    Particles (de, da, do, dos, das, e) stay with givenname."""
    full_name = full_name.strip()
    parts = full_name.split()
    if len(parts) == 1:
        return full_name, ""
    familyname = parts[-1]
    givenname_parts = parts[:-1]
    return " ".join(givenname_parts), familyname


def parse_authors(authors_str):
    """Parse comma-separated authors string into structured list."""
    raw_names = []
    parts = authors_str.split(", ")
    for i, part in enumerate(parts):
        if " e " in part and i == len(parts) - 1:
            subparts = part.rsplit(" e ", 1)
            raw_names.extend(subparts)
        elif " e " in part and i > 0:
            subparts = part.rsplit(" e ", 1)
            raw_names.extend(subparts)
        else:
            raw_names.append(part)

    authors = []
    for idx, name in enumerate(raw_names):
        name = name.strip()
        if not name:
            continue
        givenname, familyname = parse_author_name(name)
        author = {
            'givenname': givenname,
            'familyname': familyname,
            'email': f'sem-email-{idx+1}@example.com',
            'affiliation': '',
            'country': 'BR',
            'primary_contact': idx == 0,
        }
        authors.append(author)
    return authors


def calculate_end_pages(articles):
    """Calculate end page for each article based on next article's start page."""
    result = []
    for i, (section, start, title, authors_str) in enumerate(articles):
        if i + 1 < len(articles):
            next_section, next_start, _, _ = articles[i + 1]
            if next_section != section:
                divider_pages = SECTION_DIVIDERS.get(next_section, [])
                if divider_pages:
                    end_page = divider_pages[0] - 1
                else:
                    end_page = next_start - 1
            else:
                end_page = next_start - 1
        else:
            end_page = LAST_CONTENT_PAGE
        result.append((section, start, end_page, title, authors_str))
    return result


def build_yaml_data(articles_with_pages):
    """Build the YAML data structure."""
    issue = {
        'title': '8º Seminário Docomomo Sul, Porto Alegre, 2025',
        'subtitle': 'Infraestrutura / Superestrutura, Cone Sul Global',
        'slug': 'sdsul08',
        'description': '8º Seminário Docomomo Sul - Infraestrutura / Superestrutura, Cone Sul Global e I Seminário Docomomo Sul PROjeto. Porto Alegre, 24 a 27 de março de 2025. Organização: Sergio M. Marques, Carlos Eduardo Comas, Silvia Leão, Daniel Pitta, Monica L. Bohrer. Editora: Marcavisual. ISBN 978-85-61965-82-2.',
        'year': 2025,
        'volume': 8,
        'number': 1,
        'date_published': '2025-03-24',
        'editors': [
            'Sergio M. Marques',
            'Carlos Eduardo Comas',
            'Silvia Leão',
            'Daniel Pitta',
            'Monica L. Bohrer',
        ],
        'publisher': 'Marcavisual',
        'isbn': '978-85-61965-82-2',
        'location': 'Porto Alegre, RS',
        'source': 'https://www.ufrgs.br/propar/',
    }

    section_map = {
        'Água & Esgoto': 'Artigos - Água & Esgoto',
        'Viação & Obras Públicas': 'Artigos - Viação & Obras Públicas',
        'Artesanato & Indústria': 'Artigos - Artesanato & Indústria',
        'Climatização & Sustentabilidade': 'Artigos - Climatização & Sustentabilidade',
        'Agricultura & Pecuária': 'Artigos - Agricultura & Pecuária',
        'Força & Luz': 'Artigos - Força & Luz',
    }

    articles_list = []
    for i, (section, start, end, title, authors_str) in enumerate(articles_with_pages):
        art_id = f"sdsul08-{i+1:03d}"
        locale = 'en' if title.startswith('River Basin Heritage') else 'pt-BR'
        authors = parse_authors(authors_str)

        article = {
            'id': art_id,
            'seminario': 'sdsul08',
            'titulo': title,
            'locale': locale,
            'secao': section_map.get(section, section),
            'paginas': f"{start}-{end}",
            'autores': authors,
            'arquivo_pdf': f"{art_id}.pdf",
            'status': 'pendente_revisao',
        }
        articles_list.append(article)

    data = {**issue, 'articles': articles_list}
    return data


def split_pdf(articles_with_pages):
    """Split the compiled PDF into individual article PDFs using qpdf."""
    errors = []
    success = 0
    for i, (section, start, end, title, authors_str) in enumerate(articles_with_pages):
        art_id = f"sdsul08-{i+1:03d}"
        output_pdf = os.path.join(ARTIGOS_DIR, f"{art_id}.pdf")

        cmd = [
            'qpdf', '--pages', SOURCE_PDF, f'{start}-{end}', '--',
            '--empty', output_pdf
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            errors.append((art_id, result.stderr))
            print(f"  ERROR {art_id}: {result.stderr.strip()}")
        else:
            n_pages = end - start + 1
            size_kb = os.path.getsize(output_pdf) / 1024
            print(f"  {art_id}.pdf  p.{start}-{end} ({n_pages}p, {size_kb:.0f}KB)")
            success += 1

    return success, errors


def main():
    print(f"8º Seminário Docomomo Sul - Split PDF")
    print(f"Source: {SOURCE_PDF}")
    print(f"Output: {ARTIGOS_DIR}")
    print()

    articles_with_pages = calculate_end_pages(ARTICLES_DATA)

    print(f"Building YAML metadata for {len(articles_with_pages)} articles...")
    yaml_data = build_yaml_data(articles_with_pages)

    with open(YAML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)
    print(f"  YAML written to {YAML_PATH}")
    print()

    print(f"Splitting PDF into {len(articles_with_pages)} individual files...")
    success, errors = split_pdf(articles_with_pages)

    print()
    print("=" * 60)
    print(f"SUMMARY")
    print(f"  Total articles: {len(articles_with_pages)}")
    print(f"  Successfully split: {success}")
    print(f"  Errors: {len(errors)}")

    sections = {}
    for section, start, end, title, authors in articles_with_pages:
        sections[section] = sections.get(section, 0) + 1
    print(f"\n  Articles by section:")
    for section, count in sections.items():
        print(f"    {section}: {count}")

    if errors:
        print(f"\n  Errors:")
        for art_id, err in errors:
            print(f"    {art_id}: {err}")

    print(f"\n  YAML: {YAML_PATH}")
    print(f"  PDFs: {ARTIGOS_DIR}/sdsul08-*.pdf")


if __name__ == '__main__':
    main()
