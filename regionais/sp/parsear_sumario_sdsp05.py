#!/usr/bin/env python3
"""Parseia o sumário do 5º Seminário Docomomo SP (2017).
Formato: linhas contínuas com "Autor(es). Título. PÁGINA" (multiline)
Seções: RECONHECIMENTO, INTERVENÇÃO, GESTÃO (sozinhas na linha)
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
    artigos = []
    secao_atual = None
    secao_map = {'RECONHECIMENTO': 'Reconhecimento', 'INTERVENÇÃO': 'Intervenção', 'GESTÃO': 'Gestão'}

    # Juntar texto contínuo em blocos separados por linhas vazias ou seções
    # Primeiro, encontrar as seções e acumular blocos entre elas
    blocos = []
    bloco_atual = []

    for line in lines:
        stripped = line.strip()

        # Detectar seção
        if stripped in secao_map:
            if bloco_atual:
                blocos.append(('', ' '.join(bloco_atual)))
                bloco_atual = []
            blocos.append(('SECAO', stripped))
            continue

        # Detectar fim do sumário
        if stripped.startswith('V SEMINÁRIO DOCOMOMO SP 2017') and secao_atual:
            break
        if stripped.startswith('DOCOMOMO é o acrônimo'):
            break

        if not stripped:
            if bloco_atual:
                blocos.append(('BLOCO', ' '.join(bloco_atual)))
                bloco_atual = []
            continue

        bloco_atual.append(stripped)

    if bloco_atual:
        blocos.append(('BLOCO', ' '.join(bloco_atual)))

    # Agora processar os blocos
    for tipo, conteudo in blocos:
        if tipo == 'SECAO':
            secao_atual = secao_map.get(conteudo)
            continue

        if secao_atual is None:
            continue

        # O bloco pode conter múltiplos artigos
        # Cada artigo termina com um número de página (2-4 dígitos)
        # Dividir o bloco por números de página
        # Pattern: texto seguido de número 2-4 dígitos
        partes = re.split(r'(?<=\d)\s+(?=[A-ZÁÀÂÃÉÈÊÍÓÔÕÚÇ])', conteudo)

        # Melhor abordagem: encontrar todos os segmentos terminados em número
        segmentos = re.findall(r'(.+?\.\s+\d{2,4})(?=\s+[A-Z]|$)', conteudo)
        if not segmentos:
            # Tentar como bloco único
            segmentos = [conteudo]

        for seg in segmentos:
            seg = seg.strip()
            if not seg:
                continue

            # Extrair página do final
            m_pag = re.search(r'\s+(\d{2,4})\s*$', seg)
            if not m_pag:
                continue
            pagina = int(m_pag.group(1))
            texto_sem_pag = seg[:m_pag.start()].strip()

            # Separar autores do título
            # Formato: "Nome Sobrenome e Nome Sobrenome. Título do artigo"
            # O primeiro ". " após nomes humanos separa autor de título
            # Nomes geralmente têm 2-5 palavras mixed case
            # Títulos podem começar com maiúscula

            # Estratégia: encontrar o primeiro ponto que NÃO está dentro de abreviação
            # e que é seguido de espaço + maiúscula
            m_sep = re.search(r'^(.+?)\.\s+((?:[A-ZÁÀÂÃÉÈÊÍÓÔÕÚÇ"\']).+)$', texto_sem_pag)
            if m_sep:
                autores_str = m_sep.group(1).strip()
                titulo = m_sep.group(2).strip().rstrip('.')
            else:
                autores_str = ''
                titulo = texto_sem_pag.rstrip('.')

            # Parsear autores
            autores = []
            if autores_str:
                # Separar por " e " (mas não "e " dentro de nomes como "de")
                # e por ", " seguido de maiúscula
                autor_parts = re.split(r'\s+e\s+|,\s+(?=[A-ZÁÀÂÃÉÈÊÍÓÔÕÚÇ])', autores_str)
                for idx, ap in enumerate(autor_parts):
                    ap = ap.strip().rstrip('.')
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
                'section': secao_atual,
                'page_start': pagina,
                'locale': 'pt-BR',
            })

    return artigos


def gerar_yaml(artigos, output_path):
    for i in range(len(artigos) - 1):
        if artigos[i]['page_start'] and artigos[i+1]['page_start']:
            artigos[i]['page_end'] = artigos[i+1]['page_start'] - 1
    if artigos:
        artigos[-1]['page_end'] = 1170

    issue = {
        'slug': 'sdsp05',
        'title': '5º Seminário Docomomo São Paulo',
        'subtitle': 'Arquiteturas do Patrimônio Moderno Paulista: reconhecimento, intervenção, gestão',
        'description': 'Arquiteturas do Patrimônio Moderno Paulista: reconhecimento, intervenção, gestão. V Seminário Docomomo SP 2017. São Paulo: Mack Pesquisa/UPM, 2017. 1170 p. ISBN 978-85-88157-16-3. 16-17 outubro 2017.',
        'year': 2017,
        'volume': 1,
        'number': 5,
        'date_published': '2017-10-16',
        'isbn': '978-85-88157-16-3',
        'editors': ['Audrey Migliani Anticoli', 'Fernanda Critelli', 'Silvia Raquel Chiarelli', 'Tais Ossani'],
        'source': 'https://www.nucleodocomomosp.com.br/',
    }

    articles = []
    for idx, a in enumerate(artigos):
        num = idx + 1
        art_id = f'sdsp05-{num:03d}'
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
    for sec in sorted(set(a['section'] for a in articles)):
        count = sum(1 for a in articles if a['section'] == sec)
        print(f"  {sec}: {count} artigos")

if __name__ == '__main__':
    with open('/tmp/sdsp05_toc.txt', 'r', encoding='utf-8') as f:
        texto = f.read()
    artigos = parsear_toc(texto)
    gerar_yaml(artigos, '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp/sdsp05.yaml')
