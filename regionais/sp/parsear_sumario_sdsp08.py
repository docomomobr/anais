#!/usr/bin/env python3
"""Parseia o sumário do 8º Seminário Docomomo SP (2022).
Formato do TOC:
  TÍTULO EM CAIXA ALTA    PÁG
  SOBRENOME, Nome
  SOBRENOME, Nome
"""
import re
import yaml

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
        sobrenome = parts[0].strip().title()
        nome = parts[1].strip()
        # Corrigir partículas
        for p in ['Da', 'De', 'Do', 'Dos', 'Das', 'E']:
            sobrenome = sobrenome.replace(f' {p} ', f' {p.lower()} ')
            if sobrenome.startswith(f'{p} '):
                sobrenome = f'{p.lower()} ' + sobrenome[len(p)+1:]
        return nome, sobrenome
    parts = nome_str.split()
    if len(parts) >= 2:
        return ' '.join(parts[:-1]), parts[-1]
    return nome_str, ''


def parsear_toc(texto):
    lines = texto.split('\n')
    artigos = []
    homenagens = []
    in_artigos = False
    in_homenagens = False

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detectar seção de homenagens
        if 'SESSÃO DE HOMENAGEADOS' in line:
            in_homenagens = True
            in_artigos = False
            i += 1
            continue

        # Detectar início da seção de artigos
        if 'COMUNICAÇÕES | ARTIGOS COMPLETOS' in line or 'COMUNICAÇÕES' in line and 'ARTIGOS' in line:
            in_artigos = True
            in_homenagens = False
            i += 1
            continue

        if not in_artigos and not in_homenagens:
            i += 1
            continue

        # Detectar fim (números de página de rodapé isolados)
        if re.match(r'^\d{1,2}$', line) and int(line) < 20:
            i += 1
            continue

        # Detectar título de artigo: CAIXA ALTA com número de página
        # Formato: TÍTULO    PÁG
        m = re.match(r'^(.+?)\s{2,}(\d{2,3})\s*$', line)
        if not m:
            # Título pode estar sem página na mesma linha
            # Título em caixa alta seguido de página na próxima linha
            alpha = [c for c in line if c.isalpha()]
            is_upper = alpha and sum(1 for c in alpha if c.isupper()) / len(alpha) > 0.6
            if is_upper and len(line) > 20:
                # Pode ser título — acumular
                titulo_lines = [line]
                i += 1
                pagina = None
                while i < len(lines):
                    l = lines[i].strip()
                    if not l:
                        i += 1
                        continue
                    # Página sozinha?
                    if re.match(r'^\d{2,3}$', l):
                        pagina = int(l)
                        i += 1
                        break
                    # Continuação do título em caixa alta?
                    a2 = [c for c in l if c.isalpha()]
                    if a2 and sum(1 for c in a2 if c.isupper()) / len(a2) > 0.6:
                        titulo_lines.append(l)
                        i += 1
                        continue
                    # Autores (não caixa alta)
                    break

                titulo = ' '.join(titulo_lines).strip()

                # Agora ler autores
                autores = []
                while i < len(lines):
                    l = lines[i].strip()
                    if not l:
                        i += 1
                        continue
                    # Número de rodapé?
                    if re.match(r'^\d{1,2}$', l) and int(l) < 20:
                        i += 1
                        continue
                    # Novo título em caixa alta?
                    a3 = [c for c in l if c.isalpha()]
                    if a3 and sum(1 for c in a3 if c.isupper()) / len(a3) > 0.6 and len(l) > 20:
                        break
                    # Seção especial?
                    if 'COMUNICAÇÕES' in l or 'SESSÃO' in l or 'OFICINAS' in l or 'MOMOTOUR' in l or 'EIXOS' in l:
                        break
                    # Parece autor (SOBRENOME, Nome)
                    if re.match(r'^[A-ZÁÀÂÃÉÈÊÍÓÔÕÚÇ]', l) and ',' in l:
                        nome, sobrenome = parsear_nome(l)
                        autores.append({
                            'givenname': nome,
                            'familyname': sobrenome,
                            'affiliation': '',
                            'email': f'{sobrenome.lower().replace(" ", "")}@exemplo.com',
                            'primary_contact': len(autores) == 0,
                        })
                    i += 1

                if not autores:
                    autores = [{'givenname': '?', 'familyname': '?', 'affiliation': '',
                               'email': 'a@exemplo.com', 'primary_contact': True}]

                entry = {
                    'title': titulo,
                    'authors': autores,
                    'section': 'Homenageados' if in_homenagens else 'Artigos Completos',
                    'page_start': pagina,
                    'locale': 'pt-BR',
                }
                if in_homenagens:
                    homenagens.append(entry)
                else:
                    artigos.append(entry)
                continue

            i += 1
            continue

        # Temos título com página na mesma linha
        titulo = m.group(1).strip()
        pagina = int(m.group(2))
        i += 1

        # Ler autores nas linhas seguintes
        autores = []
        while i < len(lines):
            l = lines[i].strip()
            if not l:
                i += 1
                continue
            if re.match(r'^\d{1,2}$', l) and int(l) < 20:
                i += 1
                continue
            # Novo título?
            a4 = [c for c in l if c.isalpha()]
            if a4 and sum(1 for c in a4 if c.isupper()) / len(a4) > 0.6 and len(l) > 20:
                break
            if 'COMUNICAÇÕES' in l or 'SESSÃO' in l:
                break
            # Autor
            if ',' in l:
                nome, sobrenome = parsear_nome(l)
                autores.append({
                    'givenname': nome,
                    'familyname': sobrenome,
                    'affiliation': '',
                    'email': f'{sobrenome.lower().replace(" ", "")}@exemplo.com',
                    'primary_contact': len(autores) == 0,
                })
            i += 1

        if not autores:
            autores = [{'givenname': '?', 'familyname': '?', 'affiliation': '',
                       'email': 'a@exemplo.com', 'primary_contact': True}]

        entry = {
            'title': titulo,
            'authors': autores,
            'section': 'Homenageados' if in_homenagens else 'Artigos Completos',
            'page_start': pagina,
            'locale': 'pt-BR',
        }
        if in_homenagens:
            homenagens.append(entry)
        else:
            artigos.append(entry)

    return homenagens, artigos


def gerar_yaml(homenagens, artigos, output_path):
    # Combinar homenagens + artigos
    todos = homenagens + artigos
    for entry in homenagens:
        entry['section'] = 'Homenageados'
    for entry in artigos:
        entry['section'] = 'Artigos Completos'

    # Calcular página final
    for i in range(len(todos) - 1):
        if todos[i].get('page_start') and todos[i+1].get('page_start'):
            todos[i]['page_end'] = todos[i+1]['page_start'] - 1
    if todos:
        todos[-1]['page_end'] = 610

    issue = {
        'slug': 'sdsp08',
        'title': '8º Seminário Docomomo São Paulo',
        'subtitle': 'A Arquitetura e Urbanismo Modernos e os Acervos',
        'description': 'Anais do Seminário DOCOMOMO São Paulo: a arquitetura e urbanismo modernos e os acervos, 23 a 25 de agosto de 2022. São Carlos: IAU/USP, 2022. 610 p. ISBN 978-65-86810-58-5. CDD 724.98161. Catalogação: Brianda de Oliveira Ordonho Sígolo, CRB-8/8229.',
        'year': 2022,
        'volume': 1,
        'number': 8,
        'date_published': '2022-08-23',
        'isbn': '978-65-86810-58-5',
        'editors': [
            'Miguel Antonio Buzzar',
            'Mônica Junqueira de Camargo',
            'Maisa Fonseca de Almeida',
            'Fernando Atique',
            'Jasmine Luiza Souza Silva',
        ],
        'source': 'https://www.nucleodocomomosp.com.br/',
    }

    articles = []
    for idx, a in enumerate(todos):
        num = idx + 1
        art_id = f'sdsp08-{num:03d}'
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
    for sec in sorted(set(a['section'] for a in articles)):
        count = sum(1 for a in articles if a['section'] == sec)
        print(f"  {sec}: {count} artigos")


if __name__ == '__main__':
    toc_file = '/tmp/sdsp08_toc.txt'
    output_file = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp/sdsp08.yaml'

    with open(toc_file, 'r', encoding='utf-8') as f:
        texto = f.read()

    homenagens, artigos = parsear_toc(texto)
    gerar_yaml(homenagens, artigos, output_file)
