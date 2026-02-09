#!/usr/bin/env python3
"""
Gera lotes especiais para artigos com PDFs grandes.
"""

import yaml
import base64
from pathlib import Path

YAML_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/yaml")
PDF_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/pdfs")
OUTPUT_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/xml_lotes")

SECAO_MAP = {
    "Eixo 1 - A recepção e a difusão da arquitetura e urbanismo modernos brasileiros": "E1-sdbr12",
    "Eixo 2 - Práticas de preservação da arquitetura e do urbanismo modernos": "E2-sdbr12",
    "Eixo 3 - Práticas (ações e projetos) de Educação Patrimonial": "E3-sdbr12",
    "Eixo 4 - A formação dos futuros profissionais e a preservação do Movimento Moderno": "E4-sdbr12",
}

# Lotes especiais para substituir os problemáticos
LOTES_ESPECIAIS = {
    "02a": ["sdbr12-006", "sdbr12-007", "sdbr12-009", "sdbr12-010"],  # sem 008
    "02b": ["sdbr12-008"],  # PDF grande sozinho
    "03a": ["sdbr12-011", "sdbr12-012", "sdbr12-015"],  # sem 013, 014
    "03b": ["sdbr12-013"],  # PDF grande sozinho
    "03c": ["sdbr12-014"],  # PDF médio sozinho
    "10a": ["sdbr12-046", "sdbr12-047", "sdbr12-048", "sdbr12-050"],  # sem 049
    "10b": ["sdbr12-049"],  # PDF grande sozinho
}

def escape_xml(text):
    if not text:
        return ""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;"))

def get_locale(dados):
    locale = dados.get('locale', 'pt-BR')
    locale = locale.replace('-', '_')
    if locale == 'en':
        locale = 'en_US'
    return locale

def gerar_cabecalho_xml():
    return '''<?xml version="1.0" encoding="UTF-8"?>
<issue xmlns="http://pkp.sfu.ca" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" published="0" current="0" access_status="1" url_path="sdbr12" xsi:schemaLocation="http://pkp.sfu.ca native.xsd">
  <id type="internal" advice="ignore">sdbr12</id>
  <description locale="pt_BR">12° Seminário Docomomo Brasil: anais</description>
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

def gerar_rodape_xml():
    return '''  </articles>
</issue>
'''

def gerar_autor_xml(autor, seq, autor_id, locale="pt_BR"):
    xml = f'''          <author include_in_browse="true" user_group_ref="Autor" seq="{seq}" id="{autor_id}">
            <givenname locale="{locale}">{escape_xml(autor.get('givenname', ''))}</givenname>
            <familyname locale="{locale}">{escape_xml(autor.get('familyname', ''))}</familyname>'''
    if autor.get('affiliation'):
        xml += f'''
            <affiliation locale="{locale}">{escape_xml(autor['affiliation'])}</affiliation>'''
    xml += '''
            <country>BR</country>'''
    if autor.get('email'):
        xml += f'''
            <email>{escape_xml(autor['email'])}</email>'''
    else:
        xml += '''
            <email>sem.email@sdbr12.docomomo.org.br</email>'''
    xml += '''
          </author>'''
    return xml

def gerar_artigo_xml(dados, pdf_path, art_num, f_out):
    secao = dados.get('secao', '')
    secao_ref = SECAO_MAP.get(secao, "E1-sdbr12")
    locale = get_locale(dados)

    submission_id = 90000 + art_num
    publication_id = submission_id
    file_id = 80000 + art_num
    galley_id = 70000 + art_num

    f_out.write(f'''    <article xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" locale="{locale}" date_submitted="2017-11-24" status="3" submission_progress="0" current_publication_id="{publication_id}" stage="production">
      <id type="internal" advice="ignore">{submission_id}</id>
''')

    if pdf_path and pdf_path.exists():
        pdf_size = pdf_path.stat().st_size
        f_out.write(f'''      <submission_file xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="{file_id}" created_at="2017-11-24" date_created="" file_id="{file_id}" stage="proof" updated_at="2017-11-24" viewable="false" genre="Texto do artigo" xsi:schemaLocation="http://pkp.sfu.ca native.xsd">
        <name locale="{locale}">{escape_xml(pdf_path.name)}</name>
        <file id="{file_id}" filesize="{pdf_size}" extension="pdf">
          <embed encoding="base64">''')

        with open(pdf_path, 'rb') as pdf_file:
            while True:
                chunk = pdf_file.read(57 * 1024)
                if not chunk:
                    break
                f_out.write(base64.b64encode(chunk).decode('ascii'))

        f_out.write('''</embed>
        </file>
      </submission_file>
''')

    f_out.write(f'''      <publication xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" locale="{locale}" version="1" status="3" url_path="" seq="{art_num}" date_published="2017-11-24" section_ref="{secao_ref}" access_status="0" xsi:schemaLocation="http://pkp.sfu.ca native.xsd">
        <id type="internal" advice="ignore">{publication_id}</id>
        <title locale="{locale}">{escape_xml(dados.get('titulo', ''))}</title>''')

    if dados.get('subtitulo'):
        f_out.write(f'''
        <subtitle locale="{locale}">{escape_xml(dados['subtitulo'])}</subtitle>''')

    if dados.get('resumo'):
        f_out.write(f'''
        <abstract locale="{locale}">{escape_xml(dados['resumo'])}</abstract>''')

    if dados.get('resumo_en') and locale != 'en_US':
        f_out.write(f'''
        <abstract locale="en_US">{escape_xml(dados['resumo_en'])}</abstract>''')

    if dados.get('palavras_chave'):
        f_out.write(f'''
        <keywords locale="{locale}">''')
        for kw in dados['palavras_chave']:
            f_out.write(f'''
          <keyword>{escape_xml(kw)}</keyword>''')
        f_out.write('''
        </keywords>''')

    if dados.get('palavras_chave_en') and locale != 'en_US':
        f_out.write('''
        <keywords locale="en_US">''')
        for kw in dados['palavras_chave_en']:
            f_out.write(f'''
          <keyword>{escape_xml(kw)}</keyword>''')
        f_out.write('''
        </keywords>''')

    f_out.write('''
        <authors>''')
    autores = dados.get('autores', [])
    if not autores:
        f_out.write(f'''
          <author include_in_browse="true" user_group_ref="Autor" seq="0" id="{60000 + art_num}">
            <givenname locale="{locale}">Autor</givenname>
            <familyname locale="{locale}">Desconhecido</familyname>
            <country>BR</country>
            <email>sem.email@sdbr12.docomomo.org.br</email>
          </author>''')
    else:
        for i, autor in enumerate(autores):
            autor_id = 60000 + art_num * 10 + i
            f_out.write('\n' + gerar_autor_xml(autor, i, autor_id, locale))
    f_out.write('''
        </authors>''')

    # article_galley antes de citations
    if pdf_path and pdf_path.exists():
        f_out.write(f'''
        <article_galley xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" locale="{locale}" url_path="" approved="false" xsi:schemaLocation="http://pkp.sfu.ca native.xsd">
          <id type="internal" advice="ignore">{galley_id}</id>
          <name locale="{locale}">PDF</name>
          <seq>0</seq>
          <submission_file_ref id="{file_id}"/>
        </article_galley>''')

    if dados.get('referencias'):
        f_out.write('''
        <citations>''')
        for ref in dados['referencias']:
            f_out.write(f'''
          <citation>{escape_xml(ref)}</citation>''')
        f_out.write('''
        </citations>''')

    f_out.write('''
      </publication>
    </article>
''')

def main():
    print("Gerando lotes especiais para PDFs grandes...")

    for lote_id, artigos in LOTES_ESPECIAIS.items():
        output_file = OUTPUT_DIR / f"sdbr12_lote_{lote_id}.xml"
        print(f"\nLote {lote_id}: {artigos}")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(gerar_cabecalho_xml())

            for artigo_id in artigos:
                art_num = int(artigo_id.split('-')[1])
                yaml_file = YAML_DIR / f"{artigo_id}.yaml"

                with open(yaml_file, 'r', encoding='utf-8') as yf:
                    dados = yaml.safe_load(yf)

                pdf_name = dados.get('arquivo_pdf')
                pdf_path = PDF_DIR / pdf_name if pdf_name else None

                print(f"  + {artigo_id}")
                gerar_artigo_xml(dados, pdf_path, art_num, f)

            f.write(gerar_rodape_xml())

        size_mb = output_file.stat().st_size / 1024 / 1024
        print(f"  ✓ {output_file.name} ({size_mb:.1f} MB)")

    print("\n✓ Lotes especiais gerados!")
    print("Agora apague os lotes 02, 03 e 10 antigos e use os novos (02a, 02b, 03a, 03b, 03c, 10a, 10b)")

if __name__ == "__main__":
    main()
