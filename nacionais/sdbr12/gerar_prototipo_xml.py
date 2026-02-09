#!/usr/bin/env python3
"""
Gera Native XML protótipo com 3 artigos para teste.
Formato OJS 3.3 baseado no export real.
"""

import yaml
import base64
from pathlib import Path
from datetime import datetime

YAML_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/yaml")
PDF_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/pdfs")
OUTPUT = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/sdbr12_prototipo.xml")

# 3 artigos de teste
ARTIGOS_TESTE = ["sdbr12-001", "sdbr12-062", "sdbr12-082"]

# Mapeamento de seções (usando abbrev como ref)
SECAO_MAP = {
    "Eixo 1 - A recepção e a difusão da arquitetura e urbanismo modernos brasileiros": "E1-sdbr12",
    "Eixo 2 - Práticas de preservação da arquitetura e do urbanismo modernos": "E2-sdbr12",
    "Eixo 3 - Práticas (ações e projetos) de Educação Patrimonial": "E3-sdbr12",
    "Eixo 4 - A formação dos futuros profissionais e a preservação do Movimento Moderno": "E4-sdbr12",
}

def escape_xml(text):
    """Escapa caracteres especiais para XML."""
    if not text:
        return ""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;"))

def gerar_submission_file(dados, pdf_path, file_id):
    """Gera XML do submission_file com PDF embutido."""
    if not pdf_path or not pdf_path.exists():
        return ""

    pdf_size = pdf_path.stat().st_size
    with open(pdf_path, 'rb') as f:
        pdf_base64 = base64.b64encode(f.read()).decode('ascii')

    return f'''      <submission_file xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="{file_id}" created_at="2017-11-24" date_created="" file_id="{file_id}" stage="proof" updated_at="2017-11-24" viewable="false" genre="Texto do artigo" xsi:schemaLocation="http://pkp.sfu.ca native.xsd">
        <name locale="pt_BR">{escape_xml(pdf_path.name)}</name>
        <file id="{file_id}" filesize="{pdf_size}" extension="pdf">
          <embed encoding="base64">{pdf_base64}</embed>
        </file>
      </submission_file>
'''

def gerar_autor_xml(autor, seq, autor_id):
    """Gera XML de um autor."""
    xml = f'''          <author include_in_browse="true" user_group_ref="Autor" seq="{seq}" id="{autor_id}">
            <givenname locale="pt_BR">{escape_xml(autor.get('givenname', ''))}</givenname>
            <familyname locale="pt_BR">{escape_xml(autor.get('familyname', ''))}</familyname>'''

    if autor.get('affiliation'):
        xml += f'''
            <affiliation locale="pt_BR">{escape_xml(autor['affiliation'])}</affiliation>'''

    xml += '''
            <country>BR</country>'''

    if autor.get('email'):
        xml += f'''
            <email>{escape_xml(autor['email'])}</email>'''
    else:
        xml += '''
            <email>autor@exemplo.com</email>'''

    xml += '''
          </author>'''

    return xml

def gerar_artigo_xml(dados, pdf_path, art_num):
    """Gera XML de um artigo no formato OJS 3.3."""
    secao = dados.get('secao', '')
    secao_ref = SECAO_MAP.get(secao, "E1-sdbr12")

    # IDs únicos
    submission_id = 90000 + art_num
    publication_id = submission_id
    file_id = 80000 + art_num
    galley_id = 70000 + art_num

    # Submission file
    submission_file_xml = gerar_submission_file(dados, pdf_path, file_id)

    xml = f'''    <article xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" locale="pt_BR" date_submitted="2017-11-24" status="3" submission_progress="0" current_publication_id="{publication_id}" stage="production">
      <id type="internal" advice="ignore">{submission_id}</id>
{submission_file_xml}      <publication xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" locale="pt_BR" version="1" status="3" url_path="" seq="{art_num}" date_published="2017-11-24" section_ref="{secao_ref}" access_status="0" xsi:schemaLocation="http://pkp.sfu.ca native.xsd">
        <id type="internal" advice="ignore">{publication_id}</id>
        <title locale="pt_BR">{escape_xml(dados.get('titulo', ''))}</title>'''

    if dados.get('subtitulo'):
        xml += f'''
        <subtitle locale="pt_BR">{escape_xml(dados['subtitulo'])}</subtitle>'''

    if dados.get('resumo'):
        xml += f'''
        <abstract locale="pt_BR">{escape_xml(dados['resumo'])}</abstract>'''

    # Palavras-chave
    if dados.get('palavras_chave'):
        xml += '''
        <keywords locale="pt_BR">'''
        for kw in dados['palavras_chave']:
            xml += f'''
          <keyword>{escape_xml(kw)}</keyword>'''
        xml += '''
        </keywords>'''

    # Autores
    xml += '''
        <authors>'''
    autores = dados.get('autores', [])
    if not autores:
        # Autor placeholder se não houver
        xml += f'''
          <author include_in_browse="true" user_group_ref="Autor" seq="0" id="{60000 + art_num}">
            <givenname locale="pt_BR">Autor</givenname>
            <familyname locale="pt_BR">Desconhecido</familyname>
            <country>BR</country>
            <email>autor@exemplo.com</email>
          </author>'''
    else:
        for i, autor in enumerate(autores):
            autor_id = 60000 + art_num * 10 + i
            xml += '\n' + gerar_autor_xml(autor, i, autor_id)
    xml += '''
        </authors>'''

    # Galley (referência ao arquivo)
    if pdf_path and pdf_path.exists():
        xml += f'''
        <article_galley xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" locale="pt_BR" url_path="" approved="false" xsi:schemaLocation="http://pkp.sfu.ca native.xsd">
          <id type="internal" advice="ignore">{galley_id}</id>
          <name locale="pt_BR">PDF</name>
          <seq>0</seq>
          <submission_file_ref id="{file_id}"/>
        </article_galley>'''

    xml += '''
      </publication>
    </article>
'''

    return xml

def main():
    print("Gerando XML protótipo com 3 artigos (formato OJS 3.3)...")

    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<issue xmlns="http://pkp.sfu.ca" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" published="0" current="0" access_status="1" url_path="sdbr12" xsi:schemaLocation="http://pkp.sfu.ca native.xsd">
  <id type="internal" advice="ignore">sdbr12</id>
  <description locale="pt_BR">12° Seminário Docomomo Brasil: anais: arquitetura e urbanismo do movimento moderno: patrimônio cultural brasileiro: difusão, preservação e sociedade [recurso eletrônico] / organização: Maria Beatriz Camargo Cappello e Maria Marta Camisassa. Uberlândia: EDUFU, 2017. ISBN 978-85-64554-03-0</description>
  <issue_identification>
    <volume>12</volume>
    <year>2017</year>
    <title locale="pt_BR">12º Seminário Docomomo Brasil, Uberlândia, 2017</title>
  </issue_identification>
  <date_published>2017-11-24</date_published>
  <last_modified>2017-11-24</last_modified>
  <sections>
    <section ref="E1-sdbr12" seq="0" editor_restricted="0" meta_indexed="1" meta_reviewed="1" abstracts_not_required="0" hide_title="0" hide_author="0" abstract_word_count="0">
      <id type="internal" advice="ignore">20</id>
      <abbrev locale="pt_BR">E1-sdbr12</abbrev>
      <title locale="pt_BR">Eixo 1 - A recepção e a difusão da arquitetura e urbanismo modernos brasileiros</title>
    </section>
    <section ref="E2-sdbr12" seq="1" editor_restricted="0" meta_indexed="1" meta_reviewed="1" abstracts_not_required="0" hide_title="0" hide_author="0" abstract_word_count="0">
      <id type="internal" advice="ignore">21</id>
      <abbrev locale="pt_BR">E2-sdbr12</abbrev>
      <title locale="pt_BR">Eixo 2 - Práticas de preservação da arquitetura e do urbanismo modernos</title>
    </section>
    <section ref="E3-sdbr12" seq="2" editor_restricted="0" meta_indexed="1" meta_reviewed="1" abstracts_not_required="0" hide_title="0" hide_author="0" abstract_word_count="0">
      <id type="internal" advice="ignore">22</id>
      <abbrev locale="pt_BR">E3-sdbr12</abbrev>
      <title locale="pt_BR">Eixo 3 - Práticas (ações e projetos) de Educação Patrimonial</title>
    </section>
    <section ref="E4-sdbr12" seq="3" editor_restricted="0" meta_indexed="1" meta_reviewed="1" abstracts_not_required="0" hide_title="0" hide_author="0" abstract_word_count="0">
      <id type="internal" advice="ignore">23</id>
      <abbrev locale="pt_BR">E4-sdbr12</abbrev>
      <title locale="pt_BR">Eixo 4 - A formação dos futuros profissionais e a preservação do Movimento Moderno</title>
    </section>
  </sections>
  <articles>
'''

    for art_num, artigo_id in enumerate(ARTIGOS_TESTE, 1):
        yaml_file = YAML_DIR / f"{artigo_id}.yaml"

        with open(yaml_file, 'r', encoding='utf-8') as f:
            dados = yaml.safe_load(f)

        pdf_name = dados.get('arquivo_pdf')
        pdf_path = PDF_DIR / pdf_name if pdf_name else None

        print(f"  + {artigo_id}: {dados.get('titulo', '')[:50]}...")
        xml += gerar_artigo_xml(dados, pdf_path, art_num)

    xml += '''  </articles>
</issue>
'''

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(xml)

    size_mb = OUTPUT.stat().st_size / 1024 / 1024
    print(f"\n✓ Protótipo gerado: {OUTPUT}")
    print(f"  3 artigos, {size_mb:.1f} MB")

if __name__ == "__main__":
    main()
