#!/usr/bin/env python3
"""
split_pdf.py - Split sdsul07 compiled PDF into individual article PDFs
and generate YAML metadata file.

7º Seminário Docomomo Sul, Porto Alegre, 2022
"O Moderno e Reformado: Debatendo o projeto do B. 1920-2022. Parte II"

Usage:
    python3 split_pdf.py
"""

import subprocess
import os
import re
import sys
import yaml

# --- Configuration ---
BASE_DIR = "/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul/sdsul07"
PDF_DIR = os.path.join(BASE_DIR, "pdfs")
SOURCE_PDF = os.path.join(PDF_DIR, "sdsul07_anais.pdf")
YAML_PATH = "/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul/sdsul07.yaml"
ARTIGOS_DIR = PDF_DIR

# --- OrderedDumper ---
class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

OrderedDumper.add_representer(dict, dict_representer)


# --- Article data from TOC + visual page verification ---
# Format: (section, start_page, title, authors_str)
# Sections from the TOC:
#   - Projetos esquecidos
#   - Especulações preservacionistas e Revisões Cênicas
#   - Revisões mobiliárias
#   - Reformas
#   - Casas Esquecidas
#   - Edifícios esquecidos
#   - Séries esquecidas e Revisões urbanas
#   - Revisões arquitetônicas

ARTICLES_DATA = [
    # --- Projetos esquecidos (3 articles) ---
    ("Projetos esquecidos", 9,
     "O outro lado do modernismo no Brasil: Severiano Porto e Vilanova Artigas em Porto Velho",
     "Giovani Barcelos"),

    ("Projetos esquecidos", 17,
     "Edifício lâmina-plataforma: o lado B no concurso para o Paço Municipal e Parque Público de Campinas em 1957",
     "Karina Mendes, Carlos Fernando Bahima"),

    ("Projetos esquecidos", 29,
     "Lina Bo Bardi e a Itália: as torres de habitação do Taba Guaianases",
     "Suely Puppi"),

    # --- Especulações preservacionistas e Revisões Cênicas (4 articles) ---
    ("Especulações preservacionistas e Revisões Cênicas", 38,
     "O que podemos aprender com projetos premiados? Uma análise do Knoll Modernism Prize",
     "Priscila Fonseca da Silva, Larissa Nogueira Agnelo, Sidnei Junior Guadanhim"),

    ("Especulações preservacionistas e Revisões Cênicas", 49,
     "Onde está a rampa? Elementos de suplementação ou ato fundamental",
     "Maria Paula Recena"),

    ("Especulações preservacionistas e Revisões Cênicas", 58,
     "Arquitetura em cena: o cenário de Oscar Niemeyer para a peça Orfeu da Conceição (1956)",
     "Stephanie Cerioli"),

    ("Especulações preservacionistas e Revisões Cênicas", 65,
     "\"O sol faz a festa\": arte pública e Arquitetura no Teatro Nacional Claudio Santoro",
     "Valentina Marques"),

    # --- Revisões mobiliárias (4 articles) ---
    ("Revisões mobiliárias", 77,
     "Enga, Ole, Eca e o aconchegante construtivo",
     "Diego Henrique Soares"),

    ("Revisões mobiliárias", 84,
     "A evolução da questão do mobiliário no escritório de Le Corbusier através de pavilhões de exposições e mostras",
     "Monica Luce Bohrer"),

    ("Revisões mobiliárias", 94,
     "A Casa Edgar Duvivier e seus interiores: uma síntese alternativa de Lucio Costa",
     "Juliana Lopes de Souza, Angelica Ponzio"),

    ("Revisões mobiliárias", 110,
     "Sistemas de mobiliário para armazenamento 1920-1950",
     "Rodrigo Allgayer"),

    # --- Reformas (10 articles) ---
    ("Reformas", 121,
     "O discreto charme do B: Brasília Palace Hotel",
     "Andrey Rosenthal Schlee, Andrey de Aspiazu Schlee"),

    ("Reformas", 127,
     "Apartamentos contemporâneos do B. moderno",
     "Guilherme Osterkamp"),

    ("Reformas", 137,
     "Reformas modernas: três estratégias de Paulo Mendes da Rocha",
     "Marina Bonzanini Luz"),

    ("Reformas", 143,
     "Oscar Niemeyer e o Edifício Manchete: o arquiteto e o grupo Bloch",
     "Eduardo Rosseti, Bruno Campos"),

    ("Reformas", 150,
     "O que pode(ria) ser: reabilitação arquitetônica e urbana no Cine Marrocos",
     "José Alberto Grechoniak, Marcia Heck"),

    ("Reformas", 159,
     "Documentação, Arquitetura Moderna e reforma: o ocaso da FABICO - UFRGS",
     "Anna Paula Canez, Eduardo Hahn"),

    ("Reformas", 167,
     "Reabilitação de patrimônio industrial gaúcho: Metalúrgica Abramo Eberle S.A. (MAESA)",
     "Taisa Festugato"),

    ("Reformas", 176,
     "De hospital a Cidade Matarazzo: o histórico do complexo de hospitais e maternidade Matarazzo e atuais intervenções",
     "Natalia Barbosa Hetem"),

    ("Reformas", 186,
     "Projeções que fazem refletir sobre o projetar: o restauro da Cinemateca Capitólio",
     "Camila de Oliveira Porto"),

    # --- Casas Esquecidas (7 articles) ---
    ("Casas Esquecidas", 198,
     "As casas de Francisco da Conceição Silva no Brasil: um resgate analítico",
     "Ana Paula Nogueira, Marta Peixoto"),

    ("Casas Esquecidas", 207,
     "Residência César Dorfman",
     "João Paulo Barbiero"),

    ("Casas Esquecidas", 217,
     "Números que contam: história e crítica da casa moderna em Porto Alegre pelo viés da análise quantitativa 1949/1970",
     "Daniel Pitta Fischmann"),

    ("Casas Esquecidas", 229,
     "Arquitetura moderna no interior paulista",
     "Amanda Carolina Vantini"),

    ("Casas Esquecidas", 238,
     "As residências de Leo Linzmeyer em Curitiba: estudo exploratório sobre a produção residencial do arquiteto na Curitiba dos anos 60",
     "Giceli de Oliveira, Brian Almeida"),

    ("Casas Esquecidas", 252,
     "Diálogos entre a Arquitetura paulista e o tradicional paranaense: os telhados em duas residências de Roberto Gandolfi",
     "Giceli de Oliveira, Guilherme Fernando Pinto"),

    # --- Edifícios esquecidos (7 articles) ---
    ("Edifícios esquecidos", 269,
     "Demetrio Ribeiro e o Julinho: um projeto no caminho do ideário",
     "Rodrigo Troyano"),

    ("Edifícios esquecidos", 283,
     "Habitação coletiva no Sul: Edifício Nogarô e Edifício Novo Parque",
     "Angela Fagundes"),

    ("Edifícios esquecidos", 293,
     "Da irregularidade à grelha: o lado B de três edifícios residenciais do escritório MMM Roberto",
     "Luisa Prediger, Carlos Bahima"),

    ("Edifícios esquecidos", 304,
     "Arquitetura cotidiana nos anos 1980: uma proposta de catalogação e análise a partir dos projetos publicados na revista \"Casa & Jardim\"",
     "Dely Bentes"),

    ("Edifícios esquecidos", 313,
     "A Arquitetura e o espaço urbano da Cooperativa Habitacional UCOVI (1972-74), Uruguai",
     "Carolina Ritter"),

    ("Edifícios esquecidos", 329,
     "Janelas para a modernidade nas encostas de Santa Tereza",
     "Patricia Hecktheuer"),

    ("Edifícios esquecidos", 343,
     "Capela de Santana do Pé do Morro: de esquecida a protagonista",
     "Paula Olivo"),

    # --- Séries esquecidas e Revisões urbanas (5 articles) ---
    ("Séries esquecidas e Revisões urbanas", 349,
     "A pré-moldagem na Arquitetura brasileira antes dos anos 1960",
     "Juliano Vasconcellos"),

    ("Séries esquecidas e Revisões urbanas", 358,
     "Brizoletas: o estudo do programa arquitetônico escolar no Rio Grande do Sul nos anos 1960",
     "Mariana de Aguiar"),

    ("Séries esquecidas e Revisões urbanas", 367,
     "O lado B da cidade dos vivos: a formação do Cemitério Sul de Brasília em publicações impressas e desenhos técnicos (1960-1972)",
     "Leonardo Oliveira"),

    ("Séries esquecidas e Revisões urbanas", 377,
     "\"Centro de Brasília\", construção historiográfica",
     "Helena Bender"),

    ("Séries esquecidas e Revisões urbanas", 386,
     "O passo a passo moderno no projeto interpretativo do Centro Histórico de Santa Maria",
     "Anelis Rolao Flores"),

    # --- Revisões arquitetônicas (9 articles) ---
    ("Revisões arquitetônicas", 395,
     "O B de Bucci: casas noventistas em Orlândia",
     "Sara Caon, Carlos Fernando Bahima"),

    ("Revisões arquitetônicas", 409,
     "A fortuna de Radić em Vilches",
     "Carlos Eduardo Binatto de Castro, Suelen Camerin"),

    ("Revisões arquitetônicas", 421,
     "Sombra e vento fresco: a casa de Miguel Eyquem para Luis Peña",
     "Carlos Eduardo Binatto de Castro"),

    ("Revisões arquitetônicas", 433,
     "Pilotis e relações de permeabilidade depois dos anos 2000: duas obras de Andrade Morettin Arquitetos em São Paulo",
     "Nathalia Cantergiani"),

    ("Revisões arquitetônicas", 450,
     "A Arquitetura das casas de Eduardo Longo na Acrópole",
     "Eduardo Rossetti, Thiago Turchi"),

    ("Revisões arquitetônicas", 457,
     "Mayumi Souza de Lima e os projetos das EMEIs",
     "Nicolle Magalhães"),

    ("Revisões arquitetônicas", 469,
     "Vinte anos depois mudaram os arquitetos, a crítica e as diferenças",
     "Mario Guidoux Gonzaga"),

    ("Revisões arquitetônicas", 485,
     "Paralelismos e relações entre teorias revisionistas pós CIAMs e três manifestações da Arquitetura Moderna brasileira: 1960/1970",
     "Cristina Gondim"),
]

# Last content page (page 499 has references; page 500 is back cover)
LAST_CONTENT_PAGE = 499


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
        # Handle "X e Y" at the end
        if " e " in part and i == len(parts) - 1:
            subparts = part.rsplit(" e ", 1)
            raw_names.extend(subparts)
        elif " e " in part and i > 0:
            subparts = part.rsplit(" e ", 1)
            raw_names.extend(subparts)
        else:
            raw_names.append(part)

    email_counter = [0]  # mutable to track across calls

    authors = []
    for idx, name in enumerate(raw_names):
        name = name.strip()
        if not name:
            continue
        givenname, familyname = parse_author_name(name)
        email_counter[0] += 1
        author = {
            'givenname': givenname,
            'familyname': familyname,
            'email': f'sem-email-{email_counter[0]}@example.com',
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
            next_start = articles[i + 1][1]
            end_page = next_start - 1
        else:
            end_page = LAST_CONTENT_PAGE
        result.append((section, start, end_page, title, authors_str))
    return result


def get_page_count(pdf_path):
    """Get page count of a PDF using pdfinfo."""
    try:
        result = subprocess.run(['pdfinfo', pdf_path], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if line.startswith('Pages:'):
                return int(line.split(':')[1].strip())
    except:
        pass
    return 0


def extract_metadata(pdf_path):
    """Extract resumo, abstract, keywords from an individual article PDF."""
    try:
        result = subprocess.run(['pdftotext', pdf_path, '-'], capture_output=True, text=True)
        text = result.stdout
    except:
        return {}

    metadata = {}

    # Common section headings that signal end of resumo/abstract
    # These are uppercase headings typically found after the resumo block
    END_MARKERS = (
        r'Abstract[\.:]\s'
        r'|Palavras[- ]?chave'
        r'|Keywords[\.:]\s'
        r'|INTRODUÇÃO'
        r'|APRESENTAÇÃO'
        r'|CONSIDERAÇÕES'
        r'|UMA CASA'
        r'|O CONCURSO'
        r'|PORTO VELHO'
        r'|SOMBRA\n'
        r'|O VAZIO'
        r'|A ARQUITETA'
        r'|O LADO B'
        r'|LUCIO COSTA'
        r'|CONTEXTO'
        r'|JOCKEY CLUB'
        r'|A PRODUÇÃO'
        r'|O CENÁRIO'
        r'|AS ORIGENS'
        r'|O TEATRO'
        r'|A POLTRONA'
        r'|OS PAVILHÕES'
        r'|LE CORBUSIER'
        r'|BRASÍLIA'
        r'|O PROJETO'
        r'|O EDIFÍCIO'
        r'|REFORMAS'
        r'|ANTECEDENTES'
        r'|DOCUMENTAÇÃO'
        r'|PATRIMÔNIO'
        r'|MATARAZZO'
        r'|CINEMATECA'
        r'|FRANCISCO'
        r'|RESIDÊNCIA'
        r'|HISTÓRICO'
        r'|NÚMEROS'
        r'|DEMETRIO'
        r'|HABITAÇÃO'
        r'|IRREGULARIDADE'
        r'|GRELHA'
        r'|COOPERATIVA'
        r'|JANELAS'
        r'|CAPELA'
        r'|MOLDAGEM'
        r'|PRÉ-MOLDAGEM'
        r'|BRIZOLETAS'
        r'|CEMITÉRIO'
        r'|CENTRO DE BRASÍLIA'
        r'|PASSO A PASSO'
        r'|BUCCI'
        r'|FORTUNA'
        r'|PILOTIS'
        r'|CASAS DE EDUARDO'
        r'|MAYUMI'
        r'|VINTE ANOS'
        r'|PARALELISMOS'
        r'|CEDEC'
        r'|A CONFIGURAÇÃO'
        r'|DIVERSAS'
        r'|ABORDAGENS'
        r'|A CIDADE'
        r'|AS CASAS'
        r'|SOBRE O ARCO'
        r'|PRODUÇÃO ESCRITA'
        r'|UM NOVO'
        r'|UM PROJETO'
        r'|ARQUITETURA COTIDIANA'
        r'|A IMPLANTAÇÃO'
        r'|A PRÉ-MOLDAGEM'
        r'|\n\n[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ\s]{10,}\n'
    )

    # Extract Resumo - use a more flexible end pattern
    resumo_match = re.search(
        r'Resumo\.?\s*(.+?)(?=' + END_MARKERS + r')',
        text, re.DOTALL
    )
    if resumo_match:
        resumo = resumo_match.group(1).strip()
        resumo = re.sub(r'\s+', ' ', resumo)
        if len(resumo) > 50:
            metadata['resumo'] = resumo

    # Extract Abstract
    abstract_match = re.search(
        r'Abstract\.?\s*(.+?)(?=Keywords|Palavras|INTRODUÇÃO|APRESENTAÇÃO|\n\n[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{5,})',
        text, re.DOTALL | re.IGNORECASE
    )
    if abstract_match:
        abstract = abstract_match.group(1).strip()
        abstract = re.sub(r'\s+', ' ', abstract)
        if len(abstract) > 50:
            metadata['resumo_en'] = abstract

    # Extract Palavras-chave (rarely present in extractable text for this proceedings)
    kw_match = re.search(
        r'Palavras[- ]?chave[s]?\.?\s*[:\.]?\s*(.+?)(?=\n\s*(?:Abstract|Keywords|INTRODUÇÃO|APRESENTAÇÃO|\n\n[A-Z]))',
        text, re.DOTALL | re.IGNORECASE
    )
    if kw_match:
        kw_text = kw_match.group(1).strip()
        kw_text = re.sub(r'\s+', ' ', kw_text)
        if ';' in kw_text:
            keywords = [k.strip().rstrip('.') for k in kw_text.split(';') if k.strip()]
        elif '.' in kw_text and kw_text.count('.') > 1:
            keywords = [k.strip().rstrip('.') for k in kw_text.split('.') if k.strip()]
        else:
            keywords = [k.strip().rstrip('.') for k in kw_text.split(',') if k.strip()]
        keywords = [k for k in keywords if k and len(k) > 1]
        if keywords:
            metadata['palavras_chave'] = keywords

    # Extract Keywords (English)
    kw_en_match = re.search(
        r'Keywords\.?\s*:?\s*(.+?)(?=\n\s*(?:INTRODUÇÃO|APRESENTAÇÃO|\n\n[A-Z]))',
        text, re.DOTALL | re.IGNORECASE
    )
    if kw_en_match:
        kw_text = kw_en_match.group(1).strip()
        kw_text = re.sub(r'\s+', ' ', kw_text)
        if ';' in kw_text:
            keywords_en = [k.strip().rstrip('.') for k in kw_text.split(';') if k.strip()]
        else:
            keywords_en = [k.strip().rstrip('.') for k in kw_text.split(',') if k.strip()]
        keywords_en = [k for k in keywords_en if k and len(k) > 1]
        if keywords_en:
            metadata['palavras_chave_en'] = keywords_en

    # Extract Referências
    ref_match = re.search(
        r'(?:REFERÊNCIAS|REFERENCIAS|REFERÊNCIAS BIBLIOGRÁFICAS)\s*\n(.+)',
        text, re.DOTALL | re.IGNORECASE
    )
    if ref_match:
        ref_text = ref_match.group(1).strip()
        # Split references by lines starting with uppercase or by double newlines
        refs = []
        current_ref = []
        for line in ref_text.split('\n'):
            line = line.strip()
            if not line:
                if current_ref:
                    refs.append(' '.join(current_ref))
                    current_ref = []
                continue
            # New reference starts with uppercase letter or underscore
            if current_ref and (line[0].isupper() or line.startswith('_')):
                refs.append(' '.join(current_ref))
                current_ref = [line]
            else:
                current_ref.append(line)
        if current_ref:
            refs.append(' '.join(current_ref))
        # Clean up
        refs = [re.sub(r'\s+', ' ', r).strip() for r in refs if len(r.strip()) > 10]
        if refs:
            metadata['referencias'] = refs

    return metadata


def build_yaml_data(articles_with_pages):
    """Build the YAML data structure."""
    issue = {
        'title': '7º Seminário Docomomo Sul, Porto Alegre, 2022',
        'subtitle': 'O Moderno e Reformado: Debatendo o projeto do B. 1920-2022. Parte II',
        'slug': 'sdsul07',
        'description': 'Anais do VII Seminário Docomomo Sul. O Moderno e Reformado: Debatendo o projeto do B. 1920-2022. Parte II. Promovido pelo PROPAR-UFRGS e Docomomo Núcleo RS. Porto Alegre, 17 a 19 de novembro de 2022. Organizadora: Marta Peixoto. Porto Alegre: Marcavisual, 2022. 500p. ISBN 978-65-89263-60-9.',
        'year': 2022,
        'volume': 7,
        'number': 1,
        'date_published': '2022-11-17',
        'editors': [
            'Marta Peixoto',
        ],
        'publisher': 'Marcavisual',
        'isbn': '978-65-89263-60-9',
        'location': 'Porto Alegre, RS',
        'source': 'https://www.ufrgs.br/propar/publicacoes.htm',
    }

    # Build unique sections list
    seen_sections = []
    sections = []
    for section, _, _, _, _ in articles_with_pages:
        if section not in seen_sections:
            seen_sections.append(section)
            sections.append({
                'title': section,
                'abbrev': f'{section[:3].upper()}-sdsul07'.replace(' ', ''),
            })

    email_counter = 0
    articles_list = []
    for i, (section, start, end, title, authors_str) in enumerate(articles_with_pages):
        art_id = f"sdsul07-{i+1:03d}"

        # Parse authors with globally incrementing email counter
        raw_names = []
        parts = authors_str.split(", ")
        for j, part in enumerate(parts):
            if " e " in part and j == len(parts) - 1:
                subparts = part.rsplit(" e ", 1)
                raw_names.extend(subparts)
            elif " e " in part and j > 0:
                subparts = part.rsplit(" e ", 1)
                raw_names.extend(subparts)
            else:
                raw_names.append(part)

        authors = []
        for idx, name in enumerate(raw_names):
            name = name.strip()
            if not name:
                continue
            email_counter += 1
            givenname, familyname = parse_author_name(name)
            author = {
                'givenname': givenname,
                'familyname': familyname,
                'email': f'sem-email-{email_counter}@example.com',
                'affiliation': '',
                'country': 'BR',
                'primary_contact': idx == 0,
            }
            authors.append(author)

        article = {
            'id': art_id,
            'seminario': 'sdsul07',
            'titulo': title,
            'locale': 'pt-BR',
            'secao': section,
            'paginas': f"{start}-{end}",
            'autores': authors,
            'arquivo_pdf': f"{art_id}.pdf",
            'pages_count': end - start + 1,
            'status': 'pendente_revisao',
        }
        articles_list.append(article)

    data = {**issue, 'sections': sections, 'articles': articles_list}
    return data


def split_pdf(articles_with_pages):
    """Split the compiled PDF into individual article PDFs using qpdf."""
    errors = []
    success = 0
    for i, (section, start, end, title, authors_str) in enumerate(articles_with_pages):
        art_id = f"sdsul07-{i+1:03d}"
        output_pdf = os.path.join(ARTIGOS_DIR, f"{art_id}.pdf")

        cmd = [
            'qpdf', '--pages', SOURCE_PDF, f'{start}-{end}', '--',
            '--empty', output_pdf
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode not in (0, 3):  # 3 = warnings but success
            errors.append((art_id, result.stderr))
            print(f"  ERROR {art_id}: {result.stderr.strip()}")
        else:
            n_pages = end - start + 1
            size_kb = os.path.getsize(output_pdf) / 1024
            print(f"  {art_id}.pdf  p.{start}-{end} ({n_pages}p, {size_kb:.0f}KB)")
            success += 1

    return success, errors


def enrich_with_metadata(yaml_data):
    """Extract metadata from individual PDFs and add to YAML data."""
    enriched = 0
    for article in yaml_data['articles']:
        pdf_path = os.path.join(ARTIGOS_DIR, article['arquivo_pdf'])
        if not os.path.exists(pdf_path):
            continue

        metadata = extract_metadata(pdf_path)

        if 'resumo' in metadata:
            article['resumo'] = metadata['resumo']
            enriched += 1
        if 'resumo_en' in metadata:
            article['resumo_en'] = metadata['resumo_en']
        if 'palavras_chave' in metadata:
            article['palavras_chave'] = metadata['palavras_chave']
        if 'palavras_chave_en' in metadata:
            article['palavras_chave_en'] = metadata['palavras_chave_en']
        if 'referencias' in metadata:
            article['referencias'] = metadata['referencias']

        # Update page count from actual PDF
        pages = get_page_count(pdf_path)
        if pages:
            article['pages_count'] = pages

    return enriched


def main():
    print(f"7º Seminário Docomomo Sul - Split PDF")
    print(f"Source: {SOURCE_PDF}")
    print(f"Output: {ARTIGOS_DIR}")
    print()

    if not os.path.exists(SOURCE_PDF):
        print(f"ERROR: Source PDF not found: {SOURCE_PDF}")
        sys.exit(1)

    articles_with_pages = calculate_end_pages(ARTICLES_DATA)

    print(f"Splitting PDF into {len(articles_with_pages)} individual files...")
    success, errors = split_pdf(articles_with_pages)
    print()

    print(f"Extracting metadata from individual PDFs...")
    yaml_data = build_yaml_data(articles_with_pages)
    enriched = enrich_with_metadata(yaml_data)
    print(f"  Enriched {enriched}/{len(articles_with_pages)} articles with resumo")
    print()

    print(f"Writing YAML to {YAML_PATH}...")
    with open(YAML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)
    print(f"  Done.")
    print()

    # --- Summary ---
    print("=" * 60)
    print("SUMMARY")
    print(f"  Total articles: {len(articles_with_pages)}")
    print(f"  Successfully split: {success}")
    print(f"  Errors: {len(errors)}")

    sections = {}
    for section, start, end, title, authors in articles_with_pages:
        sections[section] = sections.get(section, 0) + 1
    print(f"\n  Articles by section:")
    for section, count in sections.items():
        print(f"    {section}: {count}")

    # Count metadata
    resumo_count = sum(1 for a in yaml_data['articles'] if 'resumo' in a)
    kw_count = sum(1 for a in yaml_data['articles'] if 'palavras_chave' in a)
    ref_count = sum(1 for a in yaml_data['articles'] if 'referencias' in a)
    print(f"\n  Metadata extracted:")
    print(f"    With resumo: {resumo_count}/{len(articles_with_pages)}")
    print(f"    With palavras_chave: {kw_count}/{len(articles_with_pages)}")
    print(f"    With referencias: {ref_count}/{len(articles_with_pages)}")

    # Total authors
    total_authors = sum(len(a['autores']) for a in yaml_data['articles'])
    print(f"    Total authors: {total_authors}")

    if errors:
        print(f"\n  Errors:")
        for art_id, err in errors:
            print(f"    {art_id}: {err}")

    print(f"\n  YAML: {YAML_PATH}")
    print(f"  PDFs: {ARTIGOS_DIR}/sdsul07-*.pdf")


if __name__ == '__main__':
    main()
