#!/usr/bin/env python3
"""
Gera o YAML do 9º Seminário Docomomo São Paulo (sdsp09) com todos os 27 artigos
extraídos manualmente do sumário do PDF dos anais.

A RELATORIA MESA ESPECIAL "POLÍTICAS PÚBLICAS" (p.12) NÃO é incluída:
trata-se de relatoria de mesa especial, não de artigo acadêmico.
A APRESENTAÇÃO (p.10) confirma "27 artigos" apresentados.
"""

import yaml
from collections import OrderedDict


# ── OrderedDumper (preserva ordem dos campos) ──────────────────────────

class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

OrderedDumper.add_representer(OrderedDict, dict_representer)
OrderedDumper.add_representer(dict, dict_representer)

# Representar strings com aspas quando contêm caracteres especiais
def str_representer(dumper, data):
    if any(c in data for c in [':', '"', "'", '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '#']):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

OrderedDumper.add_representer(str, str_representer)


# ── Dados da edição ────────────────────────────────────────────────────

issue = OrderedDict([
    ('slug', 'sdsp09'),
    ('title', '9º Seminário Docomomo São Paulo'),
    ('subtitle', 'Preservar e Valorizar o Patrimônio Arquitetônico Moderno: o papel das instituições públicas e agentes privados'),
    ('description', 'Anais do 9º Seminário DO.CO.MO.MO SP: Preservar e Valorizar o Patrimônio Arquitetônico Moderno: o papel das instituições públicas e agentes privados. Santos: UNISANTA / Núcleo Docomomo SP, 2024. 409 p. 26 a 28 de setembro de 2024.'),
    ('year', 2024),
    ('volume', 1),
    ('number', 9),
    ('date_published', '2024-09-26'),
    ('isbn', ''),
    ('editors', [
        'Jaqueline Fernández Alves',
        'Cristina Ribas',
        'Ivo Renato Giroto',
        'Maisa Fonseca de Almeida',
    ]),
    ('source', 'https://www.nucleodocomomosp.com.br/'),
])


# ── 27 artigos extraídos manualmente do sumário ───────────────────────

# Formato: (título, página_início)
# A página final é calculada como (próxima página_início - 1); último artigo termina em 409.

artigos_raw = [
    ('AS DECISÕES DE PRESERVAÇÃO DO PATRIMÔNIO E SEUS DIFERENTES INTERESSADOS', 20),
    ('UM RETROSPECTO DA PRESERVAÇÃO DO PATRIMÔNIO ARQUITETÔNICO MODERNO EM CURITIBA: DA DOCUMENTAÇÃO PIONEIRA AOS INVENTÁRIOS DIGITAIS (1990- 2020)', 31),
    ('O PATRIMÔNIO ARQUITETÔNICO CONSTRUÍDO PELO PLANO DE AÇÃO DO LITORAL', 44),
    ('FUMEST (1970-1989): ASCENSÃO E QUEDA DE UM PROJETO DE INFRAESTRUTURA TURÍSTICA PARA SÃO PAULO', 60),
    ('O PROCESSO DE REVISÃO DO TOMBAMENTO DE PATRIMÔNIO CULTURAL: COLÉGIO DOZE DE OUTUBRO, SÃO PAULO', 77),
    ('ARQUITETURA ESCOLAR MODERNA NA BAIXADA SANTISTA: GRUPO ESCOLAR DE PAE CARÁ OU EE. PHILOMENA CARDOSO DE OLIVEIRA', 94),
    ('EDIFÍCIO CHRISTIANO STOCKLER DAS NEVES – FAU-MACKENZIE', 108),
    ('ARQUITETURA EDUCADORA: FORMAÇÃO DE PÚBLICO E PRESERVAÇÃO DA SEDE DO MAC USP', 130),
    ('A PRODUÇÃO DO ARQUITETO GERALDO CAIUBY', 140),
    ('MUZI E ARENA NA PRODUÇÃO DA ARQUITETURA MODERNA SANTISTA', 154),
    ('MÁRLIO RAPOSO DANTAS: UM ARQUITETO MODERNO E INOVADOR MUDA O CENÁRIO DA CIDADE DE SANTOS/SP', 171),
    ('DOCUMENTAÇÃO DO PROJETO DE ARQUITETURA, ENSAIO SOBRE A CASA DO ARQUITETO E ARTISTA LINEU BORGES DE MACEDO', 185),
    ('A CASA MODERNISTA DE GREGORI WARCHAVCHIK DA RUA SANTA CRUZ: HISTÓRICO, PRESERVAÇÃO E O ATUAL ABANDONO DE UM RELEVANTE PATRIMÔNIO MODERNO NACIONAL', 200),
    ('AS CASAS CONTAM HISTÓRIAS: A IMPLANTAÇÃO DA CIDADE DE TIMÓTEO EM MEADOS DO SÉCULO XX', 215),
    ('ARQUITETURA MODERNA NA PRAIA – RESIDÊNCIAS NA PRAIA DE PERNAMBUCO – GUARUJÁ', 228),
    ('O PALÁCIO FARROUPILHA: IMPACTO DAS OBRAS DE MIES VAN DER ROHE NO PROJETO DE ZOLKO, ATRAVÉS DAS IMAGENS', 243),
    ('O ARQUITETO ROBERTO CAPELLO E O EDIFÍCIO SULACAP DE SANTOS/SP', 254),
    ('O PURGATÓRIO DE JUSCELINO: NIEMEYER E O LUTO POPULAR NO MEMORIAL JK', 267),
    ('A VERTICALIZAÇÃO NA CIDADE DE SÃO VICENTE-SP NOS ANOS DE 1950 E 1960: O EDIFÍCIO MARAHÚ, 1959, DE LAURO DA COSTA LIMA', 280),
    ('TERMINAL PRINCESA ISABEL: REFLEXÕES ACERCA DE SUA PRESERVAÇÃO', 295),
    ('CASA DE SAÚDE ANCHIETA: PRESERVAÇÃO DO PATRIMÔNIO HISTÓRICO-CULTURAL SANTISTA E RESGATE À MEMÓRIA', 310),
    ('EDIFÍCIO IRAJÁ: PROJETO DE RESTAURAÇÃO DE UMA OBRA MODERNA NÃO TOMBADA', 325),
    ('O TOMBAMENTO DOS IMÓVEIS DO BAIRRO DE HIGIENÓPOLIS, 1992-2014', 340),
    ('"BRASÍLIA REVISITADA": REVISÃO DO MODERNO NA URBANÍSTICA DE LUCIO COSTA', 355),
    ('PRESERVAÇÃO DA ARQUITETURA INDUSTRIAL: TRANSFERÊNCIA DO ARMAZÉM 7, SANTOS, SP', 367),
    ('CULTURA E PATRIMÔNIO NO RIO DE BRIZOLA E DARCY RIBEIRO', 382),
    ('PRESERVAÇÃO DO PATRIMÔNIO MODERNO, OS CONSELHOS MUNICIPAIS E O PAPEL DOS PROFISSIONAIS DE ARQUITETURA E URBANISMO: UM OLHAR SOBRE ARARAQUARA E SÃO CARLOS', 393),
]

LAST_PAGE = 409

# ── Construir lista de artigos ─────────────────────────────────────────

articles = []
for i, (title, page_start) in enumerate(artigos_raw):
    num = i + 1
    if i + 1 < len(artigos_raw):
        page_end = artigos_raw[i + 1][1] - 1
    else:
        page_end = LAST_PAGE

    article = OrderedDict([
        ('id', f'sdsp09-{num:03d}'),
        ('title', title),
        ('authors', [
            OrderedDict([
                ('givenname', '?'),
                ('familyname', '?'),
                ('affiliation', ''),
                ('email', 'a@exemplo.com'),
                ('primary_contact', True),
            ])
        ]),
        ('section', 'Artigos Completos'),
        ('pages', f'{page_start}-{page_end}'),
        ('locale', 'pt-BR'),
        ('file', f'sdsp09-{num:03d}.pdf'),
    ])
    articles.append(article)


# ── Montar documento final ─────────────────────────────────────────────

doc = OrderedDict([
    ('issue', issue),
    ('articles', articles),
])

# ── Escrever YAML ──────────────────────────────────────────────────────

output_path = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp/sdsp09.yaml'

with open(output_path, 'w', encoding='utf-8') as f:
    yaml.dump(doc, f, Dumper=OrderedDumper, default_flow_style=False,
              allow_unicode=True, width=10000, sort_keys=False)

print(f'YAML gerado com {len(articles)} artigos em {output_path}')
