#!/usr/bin/env python3
"""Parseia o sumário do 6º Seminário Docomomo SP (2018).
Abordagem: texto bruto → regex para extrair TÍTULO (Autores) agrupados por Mesa.
"""
import re
import yaml

class OrderedDumper(yaml.SafeDumper):
    pass
def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())
OrderedDumper.add_representer(dict, dict_representer)

def parsear_nome_inline(nome_str):
    nome_str = nome_str.strip()
    parts = nome_str.split()
    if len(parts) <= 1:
        return nome_str, ''
    return ' '.join(parts[:-1]), parts[-1]


def parsear_toc(texto):
    lines = texto.split('\n')

    # Encontrar região do sumário: de "4 | Artigos" até "Comissão Organizadora"
    start = None
    end = None
    for i, line in enumerate(lines):
        if '4 | Artigos' in line and start is None:
            start = i + 1
        if start and ('Comissão Organizadora' in line or 'Comissão Científica' in line):
            end = i
            break

    if start is None:
        print("ERRO: não encontrou '4 | Artigos'")
        return []

    if end is None:
        end = len(lines)

    # Limpar: remover headers/footers de página
    clean_lines = []
    for line in lines[start:end]:
        stripped = line.strip()
        # Ignorar linhas de cabeçalho/rodapé
        if stripped in ('', 'Sumário'):
            continue
        if '6º SEMINÁRIO SP DOCOMOMO' in stripped:
            continue
        if 'A ARQUITETURA MODERNA PAULISTA E A QUESTÃO SOCIAL' in stripped:
            continue
        if re.match(r'^\d{1,2}$', stripped):
            continue
        clean_lines.append(stripped)

    # Juntar tudo em texto contínuo
    full_text = '\n'.join(clean_lines)

    # Dividir por mesas
    # Pattern: Mesa de debate N: "Tema"
    mesa_pattern = re.compile(
        r'Mesas?\s+de\s+debates?\s+(\d+)\s*:\s*"([^"]+)"',
        re.IGNORECASE
    )

    # Encontrar posições das mesas
    mesa_positions = []
    for m in mesa_pattern.finditer(full_text):
        mesa_positions.append((m.start(), m.end(), int(m.group(1)), m.group(2).strip()))

    artigos = []

    for mi, (mstart, mend, mesa_num, mesa_titulo) in enumerate(mesa_positions):
        # Texto desta mesa: do fim do header até o início da próxima mesa
        if mi + 1 < len(mesa_positions):
            texto_mesa = full_text[mend:mesa_positions[mi+1][0]]
        else:
            texto_mesa = full_text[mend:]

        # Extrair artigos: TÍTULO EM CAIXA ALTA seguido de (Autores)
        # Pattern: texto em caixa alta (possivelmente multiline) seguido de (nomes | nomes)
        # Juntar linhas para facilitar
        texto_mesa = ' '.join(texto_mesa.split())

        # Encontrar padrões: UPPER_TEXT (Authors)
        # O título é caixa alta, autores entre parênteses
        art_pattern = re.compile(
            r'([A-ZÁÀÂÃÉÈÊÍÓÔÕÚÇ][A-ZÁÀÂÃÉÈÊÍÓÔÕÚÇ\s,:\-–—\.\'"\(\)0-9/]+?)\s*'
            r'\(([A-Za-záàâãéèêíóôõúçÁÀÂÃÉÈÊÍÓÔÕÚÇ\s\|,\.]+?)\)'
        )

        for am in art_pattern.finditer(texto_mesa):
            titulo = am.group(1).strip()
            autores_str = am.group(2).strip()

            # Limpar título
            titulo = titulo.strip().rstrip('.').strip()

            # Ignorar títulos muito curtos (provavelmente lixo)
            if len(titulo) < 10:
                continue

            # Verificar que é realmente caixa alta (>60% maiúsculas)
            alpha = [c for c in titulo if c.isalpha()]
            if alpha and sum(1 for c in alpha if c.isupper()) / len(alpha) < 0.6:
                continue

            # Parsear autores (separados por |)
            autores = []
            autor_parts = re.split(r'\s*\|\s*', autores_str)
            for idx, ap in enumerate(autor_parts):
                ap = ap.strip()
                # Verificar se é instituição (sigla)
                if re.match(r'^[A-Z]{2,}$', ap.replace('-', '').replace(' ', '')):
                    continue
                if not ap or len(ap) < 3:
                    continue
                nome, sobrenome = parsear_nome_inline(ap)
                autores.append({
                    'givenname': nome,
                    'familyname': sobrenome,
                    'affiliation': '',
                    'email': f'{sobrenome.lower().replace(" ", "")}@exemplo.com',
                    'primary_contact': idx == 0,
                })

            if not autores:
                autores = [{'givenname': '?', 'familyname': '?', 'affiliation': '',
                           'email': 'a@exemplo.com', 'primary_contact': True}]

            artigos.append({
                'title': titulo,
                'authors': autores,
                'section': f'Mesa {mesa_num} - {mesa_titulo}',
                'locale': 'pt-BR',
            })

    return artigos


def gerar_yaml(artigos, output_path):
    issue = {
        'slug': 'sdsp06',
        'title': '6º Seminário Docomomo São Paulo',
        'subtitle': 'A Arquitetura Moderna paulista e a questão social',
        'description': 'Anais do 6º Seminário Docomomo São Paulo: a arquitetura moderna paulista e a questão social. São Carlos: IAU/USP, 2018. 609 p. ISBN 978-85-66624-25-0. CDD 724.98161. Catalogação: Brianda de Oliveira Ordonho Sígolo, CRB-8/8229. 24 a 26 de setembro de 2018.',
        'year': 2018,
        'volume': 1,
        'number': 6,
        'date_published': '2018-09-24',
        'isbn': '978-85-66624-25-0',
        'editors': ['Miguel Antonio Buzzar', 'Fernando Guillermo Vázquez Ramos', 'Paulo Yasuhide Fujioka'],
        'source': 'https://www.nucleodocomomosp.com.br/',
    }

    articles = []
    for idx, a in enumerate(artigos):
        num = idx + 1
        art_id = f'sdsp06-{num:03d}'
        articles.append({
            'id': art_id, 'title': a['title'], 'authors': a['authors'],
            'section': a['section'], 'pages': '', 'locale': a['locale'],
            'file': f'{art_id}.pdf',
        })

    data = {'issue': issue, 'articles': articles}
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)
    print(f"Gerado {output_path} com {len(articles)} artigos")
    for sec in sorted(set(a['section'] for a in articles)):
        count = sum(1 for a in articles if a['section'] == sec)
        print(f"  {sec}: {count} artigos")

if __name__ == '__main__':
    with open('/tmp/sdsp06_toc.txt', 'r', encoding='utf-8') as f:
        texto = f.read()
    artigos = parsear_toc(texto)
    gerar_yaml(artigos, '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp/sdsp06.yaml')
