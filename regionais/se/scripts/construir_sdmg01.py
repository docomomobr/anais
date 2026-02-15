#!/usr/bin/env python3
"""Constrói sdmg01.yaml a partir dos metadados extraídos.

Lê metadados_extraidos.json (gerado por extrair_metadados.py),
aplica normalização (FUNAG, travessão, nomes) e gera o YAML
consolidado no formato padrão do projeto.

Uso:
    python3 regionais/mg/scripts/construir_yaml.py
    python3 regionais/mg/scripts/construir_yaml.py --dry-run
"""

import json
import os
import re
import sys

import yaml

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT = os.path.join(BASE, 'metadados_extraidos.json')
OUTPUT = os.path.join(BASE, 'sdmg01.yaml')

SLUG = 'sdmg01'


# ═══════════════════════════════════════════════════════════════
# Dados autoritativos do programa (PPSX) — nomes e emails dos PDFs
# O parser automático de autores erra por excesso/falta;
# esses dados do programa são a fonte confiável.
# ═══════════════════════════════════════════════════════════════

# Correções de títulos (ALL CAPS → title case, truncamentos, junções)
TITLE_OVERRIDES = {
    'sdmg01-001': 'Da capital ao Triângulo: a contribuição de Wagner Schroden para consolidação do Movimento Moderno em Minas Gerais',
    'sdmg01-005': 'Entre o edifício e a cidade: a trajetória revisitada do engenheiro Arthur Arcuri em Juiz de Fora/MG',
    'sdmg01-007': 'Inserção e exclusão: o caso do Grande Hotel de Ouro Preto',
    'sdmg01-009': 'Ideário urbanístico — propostas, realizações e intervenções: o urbanismo moderno presente nas intervenções urbanas em Belo Horizonte',
    'sdmg01-010': 'Pioneiros da Arquitetura Modernista em Passos',
    'sdmg01-013': 'O Grande Hotel de Ouro Preto e a construção da identidade nacional',
    'sdmg01-016': 'Oscar Niemeyer: complexo arquitetônico da Pampulha e sua recepção nas revistas nacionais e internacionais',
    'sdmg01-022': 'Arquitetura Moderna no Triângulo Mineiro e Alto Paranaíba: a atuação dos grandes escritórios',
    'sdmg01-025': 'O desenvolvimento da Indústria Siderúrgica no Brasil no início do século XX: contribuições de Minas Gerais',
}

AUTHORITATIVE_AUTHORS = {
    'sdmg01-001': [
        {'name': 'Adriana Capretz Borges da Silva Manhas', 'email': 'dricapretz@hotmail.com'},
        {'name': 'Ana Teresa Cirigliano Villela', 'email': 'anacirig@hotmail.com'},
        {'name': 'Max Paulo Giacheto Manhas', 'email': 'mmanhas@yahoo.com'},
    ],
    'sdmg01-002': [
        {'name': 'Anita R. Di Marco', 'email': 'ardimarco@uol.com.br'},
        {'name': 'Luciana Claudia de Oliveira Souza', 'email': 'lu.historiadora@yahoo.com.br'},
    ],
    'sdmg01-003': [
        {'name': 'Celina Borges Lemos', 'email': 'celina.lemos@uol.com.br'},
        {'name': 'Denise Marques Bahia', 'email': 'dmbahia@uol.com.br'},
    ],
    'sdmg01-004': [
        {'name': 'Clara Luiza Miranda', 'email': 'claravix@hotmail.com'},
    ],
    'sdmg01-005': [
        {'name': 'Fabio Jose Martins de Lima', 'email': 'fabio.lima@ufjf.edu.br'},
        {'name': 'Raquel Fernandes Rezende', 'email': 'quelgeorezende@yahoo.com.br'},
        {'name': 'Raquel Filippo Fernandes Hellich', 'email': 'rhellich@hotmail.com'},
        {'name': 'Eduardo Bento Vasconcelos', 'email': 'eduardo.qb@hotmail.com'},
    ],
    'sdmg01-006': [
        {'name': 'Klaus Chaves Alberto', 'email': 'klaus.alberto@ufjf.edu.br'},
    ],
    'sdmg01-007': [
        {'name': 'Laura Rennó Tenenwurcel', 'email': 'laurarenno@gmail.com'},
        {'name': 'Ricardo dos Santos Teixeira', 'email': 'tsrico@gmail.com'},
        {'name': 'Bruno Tropia Caldas', 'email': 'tropiacaldas@yahoo.com.br'},
    ],
    'sdmg01-008': [
        {'name': 'Maria Beatriz Camargo Cappello', 'email': 'mbcappello@uol.com.br'},
    ],
    'sdmg01-009': [
        {'name': 'Maria Eliza A. Guerra', 'email': 'andradeguerra@triang.com.br'},
    ],
    'sdmg01-010': [
        {'name': 'Mauro Ferreira', 'email': 'mauroferreira52@yahoo.com.br'},
        {'name': 'Douglas Oliveira Santos', 'email': None},
    ],
    'sdmg01-011': [
        {'name': 'Raquel Fernandes Rezende', 'email': 'quelgeorezende@yahoo.com.br'},
        {'name': 'Vera Lucia Ferreira Motta Rezende', 'email': 'vrezende@openlink.com.br'},
    ],
    'sdmg01-012': [
        {'name': 'Raquel von Randow Portes', 'email': 'raquelportes@hotmail.com'},
        {'name': 'Marlice Nazareth Soares de Azevedo', 'email': 'marliceazevedo@globo.br'},
    ],
    'sdmg01-013': [
        {'name': 'Miguel Antonio Buzzar', 'email': 'mbuzzar@sc.usp.br'},
        {'name': 'Lucia Noemi Simoni', 'email': 'simoni.lucia@gmail.com'},
    ],
    'sdmg01-014': [
        {'name': 'Marcos Vinícius Teles Guimarães', 'email': 'margui22@hotmail.com'},
    ],
    'sdmg01-015': [
        {'name': 'Lisandra Mara', 'email': 'lisandram@gmail.com'},
    ],
    'sdmg01-016': [
        {'name': 'Lucy Ana Lassi Dias da Mota Leite', 'email': 'Lucyanawel@yahoo.com.br'},
        {'name': 'Maria Beatriz Camargo Cappello', 'email': 'mbcappello@uol.com.br'},
    ],
    # Pôsteres
    'sdmg01-017': [
        {'name': 'Max Paulo Giacheto Manhas', 'email': None},
        {'name': 'Adriana Capretz Borges da Silva Manhas', 'email': None},
        {'name': 'Ana Teresa Cirigliano Villela', 'email': None},
    ],
    'sdmg01-018': [
        {'name': 'Agnes Leite Thompson Dantas Ferreira', 'email': 'nisthompson@gmail.com'},
        {'name': 'Clara Luiza Miranda', 'email': 'claravix@hotmail.com'},
    ],
    'sdmg01-019': [
        {'name': 'Tatiana Sell Ferreira', 'email': 'tattysell@gmail.com'},
        {'name': 'Aline Werneck Barbosa de Carvalho', 'email': 'abarbosa@ufv.br'},
    ],
    'sdmg01-020': [
        {'name': 'Ariel Luis Lazzarin', 'email': 'arielluislazzarin@yahoo.com.br'},
        {'name': 'Henrique Vitorino Souza Alves', 'email': 'henriquevsa@hotmail.com'},
        {'name': 'Maria Beatriz Camargo Cappello', 'email': 'mbcappello@uol.com.br'},
    ],
    'sdmg01-021': [
        {'name': 'Juscelino Humberto Cunha Machado Junior', 'email': None},
    ],
    'sdmg01-022': [
        {'name': 'Ana Paula Tavares Miranda', 'email': None},
        {'name': 'Maria Beatriz Camargo Cappello', 'email': None},
    ],
    'sdmg01-023': [
        {'name': 'Larissa Oliveira Gonçalves', 'email': None},
        {'name': 'Maria Eliza A. Guerra', 'email': None},
    ],
    'sdmg01-024': [
        {'name': 'Luis Eduardo Borda', 'email': None},
        {'name': 'Larissa Ribeiro Cunha', 'email': None},
    ],
    'sdmg01-025': [
        {'name': 'Maristela Siolari', 'email': None},
    ],
    'sdmg01-026': [
        {'name': 'Regina Esteves Lustoza', 'email': None},
    ],
}


# ═══════════════════════════════════════════════════════════════
# OrderedDumper (padrão do projeto)
# ═══════════════════════════════════════════════════════════════

class OrderedDumper(yaml.SafeDumper):
    pass


def _dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


def _str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


OrderedDumper.add_representer(dict, _dict_representer)
OrderedDumper.add_representer(str, _str_representer)


# ═══════════════════════════════════════════════════════════════
# Normalização de nomes
# ═══════════════════════════════════════════════════════════════

PARTICULAS = {'de', 'da', 'do', 'dos', 'das', 'e'}


def split_name(full_name):
    """Separa givenname/familyname seguindo regra brasileira.

    Regra: familyname = último sobrenome; givenname = todo o resto.
    Partículas (de, da, do) ficam no givenname.
    """
    full_name = full_name.strip()
    # Remover números superscript
    full_name = re.sub(r'\d+$', '', full_name).strip()

    parts = full_name.split()
    if len(parts) <= 1:
        return full_name, ''

    # Encontrar o último sobrenome (não-partícula)
    familyname = parts[-1]
    givenname = ' '.join(parts[:-1])

    return givenname, familyname


def normalize_affiliation(aff):
    """Normaliza afiliação para formato SIGLA-UNIVERSIDADE."""
    if not aff:
        return None

    # Limpar
    aff = aff.strip()
    aff = re.sub(r'^\d+\s*', '', aff)  # Remover número de footnote

    # Se já é uma sigla curta, manter
    if len(aff) < 30 and re.match(r'^[A-Z]', aff):
        return aff

    # Tentar extrair sigla de universidade
    siglas = re.findall(r'\b(UF[A-Z]{1,4}|PUC|UNIUBE|UNICEP|MACKENZIE|UFMG|USP|UFJF|UFV|UFES|UFSCar|UFAL|UFF)\b', aff, re.IGNORECASE)
    if siglas:
        return siglas[0].upper()

    # Se é uma descrição longa, manter (será revisada manualmente)
    if len(aff) > 200:
        return None

    return aff


def fix_travessao(text):
    """Substitui hífen isolado por travessão (em-dash)."""
    if not text:
        return text
    # ` - ` isolado → ` — ` (não em intervalos, palavras compostas)
    return re.sub(r'(?<=[a-zA-ZÀ-ú]) - (?=[a-zA-ZÀ-ú])', ' — ', text)


def split_title_subtitle(full_title):
    """Separa título e subtítulo no primeiro `: `."""
    if not full_title:
        return full_title, None

    # Procurar `: ` como separador
    if ': ' in full_title:
        parts = full_title.split(': ', 1)
        title = parts[0].strip()
        subtitle = parts[1].strip()
        # Subtítulo começa com minúscula (exceto nome próprio/sigla)
        if subtitle and subtitle[0].isupper():
            first_word = subtitle.split()[0] if subtitle.split() else ''
            # Manter maiúscula se nome próprio ou sigla
            if not (first_word.isupper() or first_word in ['Oscar', 'Niemeyer', 'Arthur', 'Sylvio']):
                subtitle = subtitle[0].lower() + subtitle[1:]
        return title, subtitle

    return full_title, None


# ═══════════════════════════════════════════════════════════════
# Construção do YAML
# ═══════════════════════════════════════════════════════════════

def build_issue():
    """Monta metadados da issue (seminário)."""
    return {
        'slug': SLUG,
        'title': '1º Seminário Docomomo Minas Gerais',
        'location': 'Belo Horizonte, MG',
        'year': 2010,
        'volume': 1,
        'number': 1,
        'isbn': None,
        'publisher': None,
        'description': '1° Seminário Docomomo Minas Gerais: anais [recurso eletrônico]. Belo Horizonte: [Editora], 2010.',
        'source': None,
        'date_published': '2010-04-20',
    }


def build_article(meta):
    """Constrói entrada de artigo a partir dos metadados extraídos."""
    article_id_for_title = meta['id']
    title_raw = TITLE_OVERRIDES.get(article_id_for_title, meta.get('title', ''))
    title_raw = fix_travessao(title_raw)
    title, subtitle = split_title_subtitle(title_raw)

    # Autores: usar dados autoritativos do PPSX (mais confiável que o parser)
    article_id = meta['id']
    auth_source = AUTHORITATIVE_AUTHORS.get(article_id, meta.get('authors', []))

    authors = []
    for au in auth_source:
        givenname, familyname = split_name(au['name'])
        author = {
            'givenname': givenname,
            'familyname': familyname,
        }
        if au.get('email'):
            author['email'] = au['email']
        aff = normalize_affiliation(au.get('affiliation'))
        if aff:
            author['affiliation'] = aff
        authors.append(author)

    # Palavras-chave
    keywords = meta.get('keywords_pt')
    keywords_en = meta.get('keywords_en')
    # Limpar keywords com lixo colado (ex: "campus universitário. Bibliografia")
    if keywords:
        clean_kw = []
        for kw in keywords:
            # Se termina com ponto + palavra solta, é artefato
            if '. ' in kw:
                kw = kw.split('. ')[0]
            clean_kw.append(kw.strip())
        keywords = [k for k in clean_kw if k]
    if keywords_en:
        clean_kw = []
        for kw in keywords_en:
            if '. ' in kw:
                kw = kw.split('. ')[0]
            clean_kw.append(kw.strip())
        keywords_en = [k for k in clean_kw if k]

    # Referências
    references = meta.get('references')

    article = {
        'id': meta['id'],
        'titulo': title,
    }
    if subtitle:
        article['subtitulo'] = subtitle

    article['autores'] = authors
    article['secao'] = f"{meta['section']} — {SLUG}"

    if keywords:
        article['palavras_chave'] = keywords
    if keywords_en:
        article['palavras_chave_en'] = keywords_en

    if meta.get('abstract_pt'):
        article['resumo'] = meta['abstract_pt']
    if meta.get('abstract_en'):
        article['resumo_en'] = meta['abstract_en']

    article['locale'] = 'pt-BR'
    article['arquivo_pdf'] = f"{meta['id']}.pdf"
    if meta.get('pages_count'):
        article['paginas_total'] = meta['pages_count']

    if references:
        article['referencias'] = references

    return article


def main():
    dry_run = '--dry-run' in sys.argv

    if not os.path.isfile(INPUT):
        print(f"Erro: {INPUT} não encontrado. Rode extrair_metadados.py primeiro.")
        sys.exit(1)

    with open(INPUT, 'r', encoding='utf-8') as f:
        all_meta = json.load(f)

    print(f"Lidos {len(all_meta)} artigos de {INPUT}")

    issue = build_issue()
    articles = []

    for meta in all_meta:
        article = build_article(meta)
        articles.append(article)

    data = {
        'issue': issue,
        'articles': articles,
    }

    if dry_run:
        print(yaml.dump(data, Dumper=OrderedDumper, width=10000, sort_keys=False, allow_unicode=True))
        return

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, width=10000, sort_keys=False, allow_unicode=True)

    # Adicionar linha em branco entre artigos para legibilidade
    with open(OUTPUT, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'\n(- id: )', r'\n\n\1', content)
    # Remover a linha extra antes do primeiro artigo
    content = content.replace('articles:\n\n- id:', 'articles:\n- id:', 1)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Gerado: {OUTPUT}")
    print(f"  Issue: {issue['title']}")
    print(f"  Artigos: {len(articles)}")

    # Resumo de qualidade
    with_abstract = sum(1 for a in articles if a.get('resumo'))
    with_keywords = sum(1 for a in articles if a.get('palavras_chave'))
    with_refs = sum(1 for a in articles if a.get('referencias'))
    with_en = sum(1 for a in articles if a.get('resumo_en'))

    print(f"  Com resumo PT: {with_abstract}/{len(articles)}")
    print(f"  Com abstract EN: {with_en}/{len(articles)}")
    print(f"  Com palavras-chave: {with_keywords}/{len(articles)}")
    print(f"  Com referências: {with_refs}/{len(articles)}")


if __name__ == '__main__':
    main()
