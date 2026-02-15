#!/usr/bin/env python3
"""Parseia o sumário do 9º Seminário Docomomo SP (2024).
Formato: TÍTULO EM CAIXA ALTA ......... PÁG
Sem autores no sumário.
"""
import re
import yaml

class OrderedDumper(yaml.SafeDumper):
    pass
def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())
OrderedDumper.add_representer(dict, dict_representer)


def parsear_toc(texto):
    lines = texto.split('\n')
    artigos = []
    in_trabalhos = False

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line == 'TRABALHOS':
            in_trabalhos = True
            i += 1
            continue

        # Fim: seção APRESENTAÇÃO após TRABALHOS
        if in_trabalhos and artigos and line.startswith('APRESENTAÇÃO'):
            break

        if not in_trabalhos:
            i += 1
            continue

        if not line:
            i += 1
            continue

        # Tentar extrair: TÍTULO ........ PÁG
        # Página pode estar na mesma linha (após pontos) ou na linha seguinte
        m = re.search(r'\.{2,}\s*(\d{2,3})\s*$', line)
        if m:
            titulo = line[:m.start()].strip()
            pagina = int(m.group(1))

            # Verificar se título é longo o suficiente (não é "APRESENTAÇÃO" etc.)
            if len(titulo) > 15:
                artigos.append({
                    'title': titulo,
                    'authors': [{'givenname': '?', 'familyname': '?', 'affiliation': '',
                                'email': 'a@exemplo.com', 'primary_contact': True}],
                    'section': 'Artigos Completos',
                    'page_start': pagina,
                    'locale': 'pt-BR',
                })
            i += 1
            continue

        # Título sem página na mesma linha — pode estar espalhado em 2-3 linhas
        # Acumular linhas até encontrar uma com pontos+página
        alpha = [c for c in line if c.isalpha()]
        is_upper = alpha and sum(1 for c in alpha if c.isupper()) / len(alpha) > 0.5
        if is_upper and len(line) > 15:
            titulo_lines = [line]
            i += 1
            pagina = None
            while i < len(lines):
                l = lines[i].strip()
                if not l:
                    i += 1
                    continue
                m2 = re.search(r'\.{2,}\s*(\d{2,3})\s*$', l)
                if m2:
                    rest = l[:m2.start()].strip()
                    if rest:
                        titulo_lines.append(rest)
                    pagina = int(m2.group(1))
                    i += 1
                    break
                titulo_lines.append(l)
                i += 1
                if i - len(titulo_lines) > 5:  # safety
                    break

            titulo = ' '.join(titulo_lines).strip()
            titulo = re.sub(r'[\s.]+$', '', titulo)

            if pagina and len(titulo) > 15:
                artigos.append({
                    'title': titulo,
                    'authors': [{'givenname': '?', 'familyname': '?', 'affiliation': '',
                                'email': 'a@exemplo.com', 'primary_contact': True}],
                    'section': 'Artigos Completos',
                    'page_start': pagina,
                    'locale': 'pt-BR',
                })
            continue

        i += 1

    return artigos


def gerar_yaml(artigos, output_path):
    for i in range(len(artigos) - 1):
        if artigos[i]['page_start'] and artigos[i+1]['page_start']:
            artigos[i]['page_end'] = artigos[i+1]['page_start'] - 1
    if artigos:
        artigos[-1]['page_end'] = 409

    issue = {
        'slug': 'sdsp09',
        'title': '9º Seminário Docomomo São Paulo',
        'subtitle': 'Preservar e Valorizar o Patrimônio Arquitetônico Moderno: o papel das instituições públicas e agentes privados',
        'description': 'Anais do 9º Seminário DO.CO.MO.MO SP: Preservar e Valorizar o Patrimônio Arquitetônico Moderno: o papel das instituições públicas e agentes privados. Santos: UNISANTA / Núcleo Docomomo SP, 2024. 409 p. 26 a 28 de setembro de 2024.',
        'year': 2024,
        'volume': 1,
        'number': 9,
        'date_published': '2024-09-26',
        'isbn': '',
        'editors': ['Jaqueline Fernández Alves', 'Cristina Ribas', 'Ivo Renato Giroto', 'Maisa Fonseca de Almeida'],
        'source': 'https://www.nucleodocomomosp.com.br/',
    }

    articles = []
    for idx, a in enumerate(artigos):
        num = idx + 1
        art_id = f'sdsp09-{num:03d}'
        pages = ''
        if a.get('page_start') and a.get('page_end'):
            pages = f"{a['page_start']}-{a['page_end']}"
        articles.append({
            'id': art_id, 'title': a['title'], 'authors': a['authors'],
            'section': a['section'], 'pages': pages, 'locale': a['locale'],
            'file': f'{art_id}.pdf',
        })

    data = {'issue': issue, 'articles': articles}
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)
    print(f"Gerado {output_path} com {len(articles)} artigos")

if __name__ == '__main__':
    with open('/tmp/sdsp09_toc.txt', 'r', encoding='utf-8') as f:
        texto = f.read()
    artigos = parsear_toc(texto)
    gerar_yaml(artigos, '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp/sdsp09.yaml')
