#!/usr/bin/env python3
"""
Split the compiled PDF of sdsul06 (6º Seminário Docomomo Sul, Porto Alegre, 2019)
into individual article PDFs and generate YAML metadata.

Source: sdsul06_anais.pdf (352 pages, 24 articles)
Output: sdsul06-001.pdf to sdsul06-024.pdf + sdsul06.yaml

Usage:
    python3 split_pdf.py

Requirements:
    - pdftotext (from poppler-utils)
    - qpdf
    - PyYAML
"""

import json, yaml, re, subprocess, os, sys

# ===== Configuration =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "pdfs")
SOURCE_PDF = os.path.join(PDF_DIR, "sdsul06_anais.pdf")
YAML_FILE = os.path.join(os.path.dirname(BASE_DIR), "sdsul06.yaml")
TOTAL_PAGES = 352


# ===== OrderedDumper =====
class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

def str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

OrderedDumper.add_representer(dict, dict_representer)
OrderedDumper.add_representer(str, str_representer)


# ===== Article definitions (from TOC analysis) =====
# key: case-insensitive substring to search in first 600 chars of each page
ARTICLES_DEF = [
    {"title": "Edifício Guaspari: uma intervenção recente no Centro Histórico de Porto Alegre",
     "key": "guaspari", "authors_raw": ["Alexandre Bataioli da Silva", "João Paulo Silveira Barbiero"]},
    {"title": "O interior da Residência de Antônio Barbosa: uma breve análise da atmosfera projetada por Vilanova Artigas",
     "key": "antônio barbosa", "authors_raw": ["Amanda Evellyn Zys"]},
    {"title": "A inclusão do Patrimônio Moderno na inventariação de bens edificados com interesse patrimonial",
     "key": "anelis", "authors_raw": ["Anelis Rolão Flôres", "Francisco Queruz", "Adriano da Silva Falcão", "Gabriela Martins Flores"]},
    {"title": "Transparência e permeabilidade na Arquitetura Moderna gaúcha: a reforma da fachada do Edifício Christofell",
     "key": "christofell", "authors_raw": ["Silvio Belmonte de Abreu", "Angela Cristiane Fagundes"]},
    {"title": "Cláudio Araújo e a livre expressão do trabalho de interiores",
     "key": "livre expressão", "authors_raw": ["Arthur Lauxen Luiz"]},
    {"title": "Sem placa, ainda com grelha: entre o pragmatismo da estrutura independente e o potencial de renovação dos edifícios residenciais em Porto Alegre 1950/68",
     "key": "sem placa", "authors_raw": ["Carlos Fernando Silva Bahima", "João Ricardo Masuero"]},
    {"title": "A Arquitetura da Biblioteca Nacional de Buenos Aires: do concurso à construção (1961-1996)",
     "key": "buenos aires", "authors_raw": ["Cassandra Salton Coradin"]},
    {"title": "O Edifício Formac pelas lentes de João Alberto Fonseca da Silva",
     "key": "formac", "authors_raw": ["Manuela Catafesta", "Fábio Bortoli"]},
    {"title": "As intervenções recentes de Scheps na Facultad de Ingeniería de Vilamajó",
     "key": "scheps", "authors_raw": ["Cristiane dos Santos Bitencourt Schwingel", "Luis Henrique Haas Luccas"]},
    {"title": "Arquitetura da demolição, a nova memória do Moderno",
     "key": "oppermann", "authors_raw": ["Cristiane Leticia Oppermann Thies", "Fernanda Peron Gaspary"]},
    {"title": "Guillermo Jullian de la Fuente: a trajetória do arquiteto chileno entre dois projetos herdados de Le Corbusier",
     "key": "jullian", "authors_raw": ["Cristina Gondim"]},
    {"title": "Cápsula do tempo: Residência Germano Vollmer Filho, 1967-69, Porto Alegre, Arquiteto João Carlos Paiva da Silva",
     "key": "germano vollmer", "authors_raw": ["Daniel Pitta Fischmann"]},
    {"title": "Horacio Baliero e a construção da paisagem: o caso do Cemitério Parque de Mar del Plata",
     "key": "horacio baliero", "authors_raw": ["Diego Fonseca Brasil Vianna"]},
    {"title": "O Hospital Lagoa: conciliando preservação patrimonial e atualização funcional no caso hospitalar",
     "key": "hospital lagoa", "authors_raw": ["Gustavo Fluckseder Cemin"]},
    {"title": "Duas residências unifamiliares gaúchas e as ações sofridas ao longo de 50 anos de existência",
     "key": "unifamilar", "authors_raw": ["João Paulo Silveira Barbiero", "Alexandre Bataioli da Silva"]},
    {"title": "A pré-moldagem brasileira e o lado B das obras de Oscar Niemeyer em Brasília",
     "key": "pré-moldagem", "authors_raw": ["Juliano Caldas de Vasconcellos"]},
    {"title": "Fortuna. O lado B da virtuosa Estação de Hidroaviões",
     "key": "hidroaviões", "authors_raw": ["Leonora Romano", "Claudio Calovi Pereira"]},
    {"title": "Museu de Arte do Rio: sobre dimensão patrimonial e projeto",
     "key": "museu de arte do rio", "authors_raw": ["Luís Henrique Haas Luccas"]},
    {"title": "Pavilhão Aviação S.T.A.R.: uma estrela pouco conhecida na constelação de obras sobre Le Corbusier",
     "key": "s.t.a.r", "authors_raw": ["Mônica Luce Bohrer"]},
    {"title": "Arquitetura industrial na obra de Gregório Zolko: cinco casos de estudo",
     "key": "zolko", "authors_raw": ["Nicolás Sica Palermo", "Ricardo José Rossin de Oliveira", "Fernando Guillermo Vázquez Ramos"]},
    {"title": "Niemeyer reconsiderado. O terreno como artefato",
     "key": "niemeyer reconsiderado", "authors_raw": ["Carlos Eduardo Dias Comas", "Marcos Leite Almeida"]},
    {"title": "Sede Administrativa da Sanepar: projeto, restauro e retrofit",
     "key": "sanepar", "authors_raw": ["Salvador Gnoato"]},
    {"title": "Llao Llao: luxuoso, pampeiro, moderno, tudo junto e misturado",
     "key": "llao llao", "authors_raw": ["Marta Silveira Peixoto"]},
    {"title": "Alejandro Bustillo e Victoria Ocampo: a casa de Palermo Chico",
     "key": "victoria ocampo", "authors_raw": ["Cláudia Costa Cabral"]},
]

# Hispanic authors: keep double surname in familyname
HISPANIC_AUTHORS = {
    "Fernando Guillermo Vázquez Ramos": ("Fernando Guillermo", "Vázquez Ramos"),
}


def split_author_name(full_name):
    """Split full name into givenname and familyname following Brazilian convention."""
    if full_name in HISPANIC_AUTHORS:
        return HISPANIC_AUTHORS[full_name]
    parts = full_name.strip().split()
    if len(parts) == 1:
        return full_name, ""
    return ' '.join(parts[:-1]), parts[-1]


def extract_text(pdf_path):
    """Extract full text from PDF using pdftotext."""
    result = subprocess.run(
        ['pdftotext', pdf_path, '-'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR: pdftotext failed: {result.stderr}")
        sys.exit(1)
    return result.stdout


def find_article_pages(pages, articles_def):
    """Find start page of each article by searching for key in page text."""
    for art in articles_def:
        key = art["key"].lower()
        for i in range(4, len(pages)):  # Skip preamble (pages 1-4)
            if key in pages[i][:600].lower():
                art["start_page"] = i + 1  # 1-indexed
                break
        else:
            print(f"ERROR: Article not found: {art['key']} ({art['title'][:50]})")
            art["start_page"] = None

    # Sort by start page
    articles_def.sort(key=lambda a: a.get("start_page") or 999)

    # Check for missing
    missing = [a for a in articles_def if a["start_page"] is None]
    if missing:
        print(f"FATAL: {len(missing)} articles not found!")
        for a in missing:
            print(f"  - {a['title']}")
        sys.exit(1)

    # Calculate end pages
    for i, art in enumerate(articles_def):
        if i < len(articles_def) - 1:
            art["end_page"] = articles_def[i + 1]["start_page"] - 1
        else:
            art["end_page"] = TOTAL_PAGES

    return articles_def


def extract_metadata(pages, articles):
    """Extract resumo, keywords, and emails from article text."""
    for art in articles:
        sp = art["start_page"] - 1  # 0-indexed
        article_text = '\n'.join(pages[sp:sp + 3])

        # Emails
        emails_raw = re.findall(
            r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})',
            article_text
        )
        art["emails"] = list(dict.fromkeys(emails_raw))

        # Resumo
        resumo_match = re.search(
            r'(?:Resumo|RESUMO)[:\s]*\n?(.*?)(?=\n\s*(?:Palavras|Abstract|ABSTRACT|Keywords|KEYWORDS|Introdução|INTRODUÇÃO))',
            article_text, re.DOTALL | re.IGNORECASE
        )
        if resumo_match:
            resumo = resumo_match.group(1).strip()
            resumo = re.sub(r'\n', ' ', resumo)
            resumo = re.sub(r'\s+', ' ', resumo)
            art["resumo"] = resumo
        else:
            art["resumo"] = None

        # Keywords
        kw_match = re.search(
            r'(?:Palavras[\s-]*chave[s]?)[:\s]*\n?(.*?)(?=\n\s*(?:Abstract|ABSTRACT|Keywords|KEYWORDS|\n\n|Introdução|INTRODUÇÃO))',
            article_text, re.DOTALL | re.IGNORECASE
        )
        if kw_match:
            kw_text = kw_match.group(1).strip()
            kw_text = re.sub(r'\n', ' ', kw_text)
            keywords = [k.strip().rstrip('.').strip() for k in re.split(r'[;,]', kw_text)
                       if k.strip() and len(k.strip()) > 1]
            keywords = [k.replace("(título em negrito):", "").strip() for k in keywords]
            keywords = [k for k in keywords if k]
            art["keywords"] = keywords if keywords else None
        else:
            art["keywords"] = None

    return articles


def build_yaml(articles):
    """Build YAML structure and write to file."""
    issue = {
        "slug": "sdsul06",
        "title": "6º Seminário Docomomo Sul",
        "subtitle": "O moderno e reformado",
        "description": "Anais do VI Seminário Docomomo Sul: o moderno e reformado. Debatendo o projeto do B. 1920-2019. Parte I. Promovido pelo PROPAR-UFRGS, curso de Arquitetura e Urbanismo da Unisinos e DOCOMOMO Núcleo RS. Porto Alegre: Marcavisual, 2019. ISBN 978-85-61965-77-8.",
        "year": 2019,
        "volume": 6,
        "number": 6,
        "date_published": "2019-11-07",
        "editors": ["Carlos Eduardo Comas", "Marta Peixoto"],
        "publisher": "Marcavisual",
        "isbn": "978-85-61965-77-8",
        "location": "Porto Alegre, RS",
        "source": "https://www.ufrgs.br/propar/publicacoes.htm",
        "sections": [
            {"title": "Artigos Completos", "abbrev": "AC-sdsul06"}
        ],
        "articles": []
    }

    for i, art in enumerate(articles):
        article_id = f"sdsul06-{i + 1:03d}"

        # Split title/subtitle on first ": "
        full_title = art["title"]
        if ": " in full_title:
            title_part, subtitle_part = full_title.split(": ", 1)
        else:
            title_part = full_title
            subtitle_part = None

        # Build authors
        authors = []
        emails = art.get("emails", [])
        for j, author_name in enumerate(art["authors_raw"]):
            gn, fn = split_author_name(author_name)
            author = {
                "givenname": gn,
                "familyname": fn,
                "email": emails[j] if j < len(emails) else f"nao.informado{j + 1}@sdsul06.temp",
                "affiliation": None,
                "country": "BR",
                "primary_contact": j == 0
            }
            authors.append(author)

        article = {"id": article_id, "seminario": "sdsul06", "titulo": title_part}
        if subtitle_part:
            article["subtitulo"] = subtitle_part
        article["locale"] = "pt-BR"
        article["secao"] = "Artigos Completos"
        article["paginas"] = f"{art['start_page']}-{art['end_page']}"
        article["autores"] = authors
        if art.get("resumo"):
            article["resumo"] = art["resumo"]
        if art.get("keywords"):
            article["palavras_chave"] = art["keywords"]
        article["arquivo_pdf"] = f"{article_id}.pdf"
        article["status"] = "pendente_revisao"

        issue["articles"].append(article)

    with open(YAML_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(issue, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)

    print(f"YAML written to {YAML_FILE}")
    return issue


def split_pdf(articles):
    """Split source PDF into individual article PDFs using qpdf."""
    errors = []
    for i, art in enumerate(articles):
        article_id = f"sdsul06-{i + 1:03d}"
        output_pdf = os.path.join(PDF_DIR, f"{article_id}.pdf")
        sp = art["start_page"]
        ep = art["end_page"]

        cmd = [
            "qpdf", SOURCE_PDF,
            "--pages", SOURCE_PDF, f"{sp}-{ep}", "--",
            output_pdf
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            errors.append(f"  {article_id}: {result.stderr.strip()}")
            print(f"  ERROR: {article_id} (p.{sp}-{ep})")
        else:
            size = os.path.getsize(output_pdf)
            print(f"  OK: {article_id}.pdf (p.{sp}-{ep}, {size / 1024:.0f}KB)")

    return errors


def main():
    if not os.path.exists(SOURCE_PDF):
        print(f"ERROR: Source PDF not found: {SOURCE_PDF}")
        sys.exit(1)

    print(f"Extracting text from {SOURCE_PDF}...")
    full_text = extract_text(SOURCE_PDF)
    pages = full_text.split('\x0c')
    print(f"  {len(pages)} pages extracted")

    print(f"\nFinding article boundaries...")
    articles = find_article_pages(pages, ARTICLES_DEF)
    print(f"  {len(articles)} articles found")

    print(f"\nExtracting metadata...")
    articles = extract_metadata(pages, articles)
    resumos = sum(1 for a in articles if a.get("resumo"))
    keywords = sum(1 for a in articles if a.get("keywords"))
    print(f"  Resumos: {resumos}/{len(articles)}")
    print(f"  Keywords: {keywords}/{len(articles)}")

    print(f"\nBuilding YAML...")
    build_yaml(articles)

    print(f"\nSplitting PDF...")
    errors = split_pdf(articles)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"SUMMARY - sdsul06 (6o Seminario Docomomo Sul)")
    print(f"{'=' * 60}")
    print(f"Source: {SOURCE_PDF} ({TOTAL_PAGES} pages)")
    print(f"Articles: {len(articles)}")
    print(f"Preamble: pages 1-4 (cover, cataloging, TOC)")
    print(f"YAML: {YAML_FILE}")
    print(f"PDFs: {PDF_DIR}/sdsul06-001.pdf to sdsul06-{len(articles):03d}.pdf")
    print(f"Resumos: {resumos}/{len(articles)}")
    print(f"Keywords: {keywords}/{len(articles)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors:
            print(e)
    else:
        print(f"All {len(articles)} PDFs split successfully!")


if __name__ == "__main__":
    main()
