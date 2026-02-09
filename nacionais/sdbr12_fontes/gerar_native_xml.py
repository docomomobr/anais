#!/usr/bin/env python3
"""
Gera Native XML do OJS para importação do sdbr12.
"""

import yaml
import base64
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

YAML_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/yaml")
PDF_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/pdfs")
OUTPUT = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/sdbr12_native.xml")

# Mapeamento de seções
SECAO_MAP = {
    "Eixo 1 - A recepção e a difusão da arquitetura e urbanismo modernos brasileiros": "E1-sdbr12",
    "Eixo 2 - Práticas de preservação da arquitetura e do urbanismo modernos": "E2-sdbr12",
    "Eixo 3 - Práticas (ações e projetos) de Educação Patrimonial": "E3-sdbr12",
    "Eixo 4 - A formação dos futuros profissionais e a preservação do Movimento Moderno": "E4-sdbr12",
}

def criar_issue():
    """Cria elemento da issue."""
    issue = Element("issue")
    issue.set("xmlns", "http://pkp.sfu.ca")
    issue.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    issue.set("xsi:schemaLocation", "http://pkp.sfu.ca native.xsd")
    issue.set("published", "0")  # Não publicar automaticamente
    issue.set("current", "0")
    issue.set("access_status", "1")

    # Identificação
    issue_id = SubElement(issue, "id", type="internal", advice="ignore")
    issue_id.text = "sdbr12"

    # Volume e ano
    volume = SubElement(issue, "volume")
    volume.text = "12"

    year = SubElement(issue, "year")
    year.text = "2017"

    # Título
    title = SubElement(issue, "title", locale="pt_BR")
    title.text = "12º Seminário Docomomo Brasil, Uberlândia, 2017"

    # Descrição
    desc = SubElement(issue, "description", locale="pt_BR")
    desc.text = """12° Seminário Docomomo Brasil: anais: arquitetura e urbanismo do movimento moderno: patrimônio cultural brasileiro: difusão, preservação e sociedade [recurso eletrônico] / organização: Maria Beatriz Camargo Cappello e Maria Marta Camisassa. Uberlândia: EDUFU, 2017.

ISBN 978-85-64554-03-0"""

    # Data de publicação
    date_pub = SubElement(issue, "date_published")
    date_pub.text = "2017-11-24"

    # Seções
    sections = SubElement(issue, "sections")
    for secao_nome, secao_abbrev in SECAO_MAP.items():
        section = SubElement(sections, "section")
        section.set("ref", secao_abbrev)
        sec_title = SubElement(section, "title", locale="pt_BR")
        sec_title.text = secao_nome
        sec_abbrev = SubElement(section, "abbrev", locale="pt_BR")
        sec_abbrev.text = secao_abbrev

    return issue


def criar_artigo(dados, pdf_path):
    """Cria elemento de artigo."""
    article = Element("article")
    article.set("xmlns", "http://pkp.sfu.ca")
    article.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    article.set("locale", "pt_BR")
    article.set("date_submitted", "2017-11-24")
    article.set("stage", "production")
    article.set("date_published", "2017-11-24")
    article.set("status", "3")  # STATUS_PUBLISHED

    # Seção
    secao = dados.get('secao', '')
    secao_ref = SECAO_MAP.get(secao, "E1-sdbr12")
    article.set("section_ref", secao_ref)

    # ID
    art_id = SubElement(article, "id", type="internal", advice="ignore")
    art_id.text = dados.get('id', '')

    # Título
    title = SubElement(article, "title", locale="pt_BR")
    title.text = dados.get('titulo', '')

    # Subtítulo
    if dados.get('subtitulo'):
        subtitle = SubElement(article, "subtitle", locale="pt_BR")
        subtitle.text = dados['subtitulo']

    # Resumo
    if dados.get('resumo'):
        abstract = SubElement(article, "abstract", locale="pt_BR")
        abstract.text = dados['resumo']

    # Palavras-chave
    if dados.get('palavras_chave'):
        keywords = SubElement(article, "keywords", locale="pt_BR")
        for kw in dados['palavras_chave']:
            keyword = SubElement(keywords, "keyword")
            keyword.text = kw

    # Autores
    if dados.get('autores'):
        authors = SubElement(article, "authors")
        for i, autor in enumerate(dados['autores']):
            author = SubElement(authors, "author")
            author.set("primary_contact", "true" if autor.get('primary_contact') else "false")
            author.set("include_in_browse", "true")
            author.set("user_group_ref", "Autor")

            gn = SubElement(author, "givenname", locale="pt_BR")
            gn.text = autor.get('givenname', '')

            fn = SubElement(author, "familyname", locale="pt_BR")
            fn.text = autor.get('familyname', '')

            if autor.get('affiliation'):
                aff = SubElement(author, "affiliation", locale="pt_BR")
                aff.text = autor['affiliation']

            if autor.get('email'):
                email = SubElement(author, "email")
                email.text = autor['email']

    # Galley (PDF)
    if pdf_path and pdf_path.exists():
        galley = SubElement(article, "article_galley")
        galley.set("locale", "pt_BR")
        galley.set("approved", "false")

        galley_id = SubElement(galley, "id", type="internal", advice="ignore")
        galley_id.text = dados.get('id', '') + "-pdf"

        galley_name = SubElement(galley, "name", locale="pt_BR")
        galley_name.text = "PDF"

        galley_seq = SubElement(galley, "seq")
        galley_seq.text = "0"

        # Arquivo embutido
        submission_file = SubElement(galley, "submission_file")
        submission_file.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        submission_file.set("stage", "proof")
        submission_file.set("id", dados.get('id', '') + "-file")
        submission_file.set("xsi:schemaLocation", "http://pkp.sfu.ca native.xsd")

        file_name = SubElement(submission_file, "name", locale="pt_BR")
        file_name.text = pdf_path.name

        file_el = SubElement(submission_file, "file")
        file_el.set("id", dados.get('id', '') + "-file-rev")
        file_el.set("filesize", str(pdf_path.stat().st_size))
        file_el.set("extension", "pdf")

        # Embed base64
        embed = SubElement(file_el, "embed", encoding="base64")
        with open(pdf_path, 'rb') as f:
            embed.text = base64.b64encode(f.read()).decode('ascii')

    return article


def main():
    print("Gerando Native XML para sdbr12...")

    # Criar issue
    issue = criar_issue()

    # Container de artigos
    articles = SubElement(issue, "articles")

    # Processar cada YAML
    count = 0
    for yaml_file in sorted(YAML_DIR.glob("sdbr12-*.yaml")):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            dados = yaml.safe_load(f)

        pdf_name = dados.get('arquivo_pdf')
        pdf_path = PDF_DIR / pdf_name if pdf_name else None

        if pdf_path and not pdf_path.exists():
            print(f"  AVISO: PDF não encontrado: {pdf_name}")
            pdf_path = None

        article = criar_artigo(dados, pdf_path)
        articles.append(article)
        count += 1
        print(f"  [{count}/82] {dados.get('id')}: {dados.get('titulo', '')[:50]}...")

    # Formatar e salvar
    xml_str = tostring(issue, encoding='unicode')
    xml_pretty = minidom.parseString(xml_str).toprettyxml(indent="  ")

    # Remover linha de declaração duplicada
    lines = xml_pretty.split('\n')
    if lines[0].startswith('<?xml'):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"\n✓ XML gerado: {OUTPUT}")
    print(f"  {count} artigos incluídos")
    print(f"  Tamanho: {OUTPUT.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
