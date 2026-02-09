#!/usr/bin/env python3
"""Parseia o sumário do 7º Seminário Docomomo SP (2020).
Formato: ● Título | SOBRENOME, Nome; SOBRENOME, Nome | PÁG
"""
import re
import yaml
import sys

class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

OrderedDumper.add_representer(dict, dict_representer)

def parsear_nome(nome_str):
    """Converte 'SOBRENOME, Nome' para givenname/familyname."""
    nome_str = nome_str.strip()
    if ',' in nome_str:
        parts = nome_str.split(',', 1)
        sobrenome = parts[0].strip()
        nome = parts[1].strip()
        # Capitalizar sobrenome corretamente
        sobrenome = sobrenome.title()
        # Corrigir partículas
        for p in ['Da', 'De', 'Do', 'Dos', 'Das', 'E']:
            sobrenome = sobrenome.replace(f' {p} ', f' {p.lower()} ')
        return nome, sobrenome
    else:
        # Nome sem vírgula - tentar separar
        parts = nome_str.split()
        if len(parts) >= 2:
            return ' '.join(parts[:-1]), parts[-1]
        return nome_str, ''

def separar_nome_sobrenome(givenname_full, familyname_full):
    """Aplica regra brasileira: givenname = tudo menos último, familyname = último."""
    # givenname_full já é o nome, familyname_full já é o sobrenome
    # Precisamos verificar se o sobrenome tem partículas finais
    return givenname_full, familyname_full

def parsear_toc(texto):
    """Parseia o TOC do 7º SP."""
    lines = texto.split('\n')
    artigos = []
    eixo_atual = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Detectar eixo
        if re.match(r'^Eixo\s+\d+\s*\|', line):
            m = re.match(r'^Eixo\s+(\d+)\s*\|', line)
            eixo_atual = int(m.group(1))
            i += 1
            continue

        # Detectar fim do TOC
        if line.startswith('Atividades e normas'):
            break

        # Detectar artigo (começa com ●)
        if line == '●' or line.startswith('●'):
            # Acumular linhas até encontrar o próximo ● ou Eixo ou fim
            i += 1
            bloco = []
            while i < len(lines):
                l = lines[i].strip()
                if l == '●' or l.startswith('●') or re.match(r'^Eixo\s+\d+', l) or l.startswith('Atividades e normas'):
                    break
                if l:
                    bloco.append(l)
                i += 1

            # Juntar bloco
            texto_bloco = ' '.join(bloco)

            # Formato: Título | AUTORES | PÁG
            # ou: Título | AUTORES | \n PÁG (página pode estar em linha separada)
            parts = texto_bloco.split('|')
            if len(parts) >= 2:
                titulo = parts[0].strip()
                autores_str = parts[1].strip()
                pagina = parts[2].strip() if len(parts) > 2 else ''

                # Limpar página
                pagina = re.sub(r'[^\d]', '', pagina)

                # Parsear autores (separados por ;)
                autores_raw = [a.strip() for a in autores_str.split(';') if a.strip()]
                autores = []
                for idx, a in enumerate(autores_raw):
                    nome, sobrenome = parsear_nome(a)
                    autor = {
                        'givenname': nome,
                        'familyname': sobrenome,
                        'affiliation': '',
                        'email': f'{sobrenome.lower().replace(" ", "")}@exemplo.com',
                        'primary_contact': idx == 0
                    }
                    autores.append(autor)

                # Ignorar entradas antes do primeiro eixo (comissões etc.)
                if eixo_atual is None:
                    continue

                artigo = {
                    'title': titulo,
                    'authors': autores,
                    'section': f'Eixo {eixo_atual}',
                    'page_start': int(pagina) if pagina else None,
                    'locale': 'pt-BR',
                }
                artigos.append(artigo)
            continue

        i += 1

    return artigos


def gerar_yaml(artigos, output_path):
    """Gera o YAML consolidado do 7º SP."""
    # Calcular página final de cada artigo
    for i in range(len(artigos) - 1):
        if artigos[i]['page_start'] and artigos[i+1]['page_start']:
            artigos[i]['page_end'] = artigos[i+1]['page_start'] - 1
    if artigos:
        artigos[-1]['page_end'] = 553  # Última página antes de "Atividades e normas"

    # Montar dados
    issue = {
        'slug': 'sdsp07',
        'title': '7º Seminário Docomomo São Paulo',
        'subtitle': 'A difusão da Arquitetura Moderna, 1930-1980',
        'description': 'Anais do 7º Seminário Docomomo São Paulo: A difusão da arquitetura moderna, 1930-1980. São Paulo: PGAUR/USJT, 2020. 566 p. ISBN 978-65-00-11912-1. Evento online, 9 a 14 de novembro de 2020.',
        'year': 2020,
        'volume': 1,
        'number': 7,
        'date_published': '2020-11-09',
        'isbn': '978-65-00-11912-1',
        'editors': [
            'Fernando Guillermo Vázquez Ramos',
            'Mirthes Baffi',
            'Andréa de Oliveira Tourinho',
            'Cristiane Kröhling Pinheiro Borges Bernardi',
            'Eneida de Almeida',
            'Lucio Gomes Machado',
            'Maria Isabel Imbronito',
            'Miguel Antonio Buzzar',
        ],
        'source': 'https://www.nucleodocomomosp.com.br/',
    }

    articles = []
    for idx, a in enumerate(artigos):
        num = idx + 1
        art_id = f'sdsp07-{num:03d}'
        pages = ''
        if a.get('page_start') and a.get('page_end'):
            pages = f"{a['page_start']}-{a['page_end']}"

        article = {
            'id': art_id,
            'title': a['title'],
            'authors': a['authors'],
            'section': a['section'],
            'pages': pages,
            'locale': a['locale'],
            'file': f'{art_id}.pdf',
        }
        articles.append(article)

    data = {'issue': issue, 'articles': articles}

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)

    print(f"Gerado {output_path} com {len(articles)} artigos")
    for sec in set(a['section'] for a in articles):
        count = sum(1 for a in articles if a['section'] == sec)
        print(f"  {sec}: {count} artigos")


if __name__ == '__main__':
    toc_file = '/tmp/sdsp07_text.txt'
    output_file = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp/sdsp07.yaml'

    with open(toc_file, 'r', encoding='utf-8') as f:
        texto = f.read()

    artigos = parsear_toc(texto)
    gerar_yaml(artigos, output_file)
