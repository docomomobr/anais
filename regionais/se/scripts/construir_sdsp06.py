#!/usr/bin/env python3
"""
Constrói o YAML do 6º Seminário Docomomo São Paulo a partir dos dados
extraídos manualmente do sumário do PDF dos anais.

Gera: sdsp06.yaml
"""

import yaml
from collections import OrderedDict

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

OrderedDumper.add_representer(OrderedDict, dict_representer)


def make_author(full_name, is_primary=False):
    """Separa nome completo em givenname (tudo menos último) e familyname (último)."""
    parts = full_name.strip().split()
    if len(parts) == 1:
        gn = parts[0]
        fn = parts[0]
    else:
        gn = ' '.join(parts[:-1])
        fn = parts[-1]
    return OrderedDict([
        ('givenname', gn),
        ('familyname', fn),
        ('affiliation', ''),
        ('email', f'{fn.lower()}@exemplo.com'),
        ('primary_contact', is_primary),
    ])


def make_article(seq, title, author_names, section):
    """Cria um artigo com a estrutura padrão."""
    authors = []
    for i, name in enumerate(author_names):
        authors.append(make_author(name, is_primary=(i == 0)))
    return OrderedDict([
        ('id', f'sdsp06-{seq:03d}'),
        ('title', title),
        ('authors', authors),
        ('section', section),
        ('locale', 'pt-BR'),
        ('file', f'sdsp06-{seq:03d}.pdf'),
    ])


# ---------------------------------------------------------------------------
# Dados extraídos do sumário (TOC) do PDF
# ---------------------------------------------------------------------------

articles_data = [
    # =========================================================================
    # Mesa 1: Modos de usar a cidade: espaços educacionais
    # =========================================================================
    {
        'title': 'ARQUITETURA MODERNA E SEU OLHAR SOBRE OS AMBIENTES DE ENSINO',
        'authors': ['Jasmine Luiza Souza Silva'],
        'section': 'Mesa 1 - Modos de usar a cidade: espaços educacionais',
    },
    {
        'title': 'AS ESCOLAS DO CONVÊNIO ESCOLAR E AS TRANSFORMAÇÕES URBANAS EM SÃO PAULO, 1949-1954',
        'authors': ['Juliane Bellot Rolemberg Lessa'],
        'section': 'Mesa 1 - Modos de usar a cidade: espaços educacionais',
    },
    {
        'title': 'CONCEPÇÃO DE UM ACAMPAMENTO ESCOLAR: A PRÁXIS POPULAR MATERIALIZADA',
        'authors': ['Maria Helena Paiva da Costa', 'Ana Paula Koury'],
        'section': 'Mesa 1 - Modos de usar a cidade: espaços educacionais',
    },
    {
        'title': 'A ESCOLA MODERNA ENQUANTO POTÊNCIA DO DIREITO À CIDADE: ESTUDO DE CASO DA EE CONSELHEIRO CRISPINIANO',
        'authors': ['Miranda Zamberlan Nedel', 'Miguel Antonio Buzzar'],
        'section': 'Mesa 1 - Modos de usar a cidade: espaços educacionais',
    },
    {
        'title': 'DIFUSÃO DA ARQUITETURA MODERNA NO INTERIOR PAULISTA. CASO DE ESTUDO: ESCOLA ANTONIO ADOLFO LOBBE EM SÃO CARLOS (1961)',
        'authors': ['Rachel Bergantin', 'Miguel Antonio Buzzar', 'Paulo Yassuhide Fujioka'],
        'section': 'Mesa 1 - Modos de usar a cidade: espaços educacionais',
    },

    # =========================================================================
    # Mesa 2: Modos de analisar a cidade: Registro e análise projetual e patrimonial
    # =========================================================================
    {
        'title': 'ARQUITETURA MODERNA E FOTOGRAFIA: VELANDO E REVELANDO A FAU-USP DE VILANOVA ARTIGAS',
        'authors': ['Arthur Simon Zanella', 'Eduardo Luisi Paixão Silva Campolon'],
        'section': 'Mesa 2 - Modos de analisar a cidade: registro e análise projetual e patrimonial',
    },
    {
        'title': 'EDUARDO KNEESE DE MELLO: GESTÃO E ORGANIZAÇÃO DA COLEÇÃO ICONOGRÁFICA',
        'authors': ['Elisa Horta', 'Ademir Pereira dos Santos'],
        'section': 'Mesa 2 - Modos de analisar a cidade: registro e análise projetual e patrimonial',
    },
    {
        'title': 'UM PANORAMA DA ARQUITETURA MODERNA NATALENSE: O CASO DOS EDIFÍCIOS VERTICAIS (ANOS 1960 E 1970)',
        'authors': ['Maria Heloísa Alves de Oliveira', 'Edja Trigueiro'],
        'section': 'Mesa 2 - Modos de analisar a cidade: registro e análise projetual e patrimonial',
    },
    {
        'title': 'A PARTE E O TODO NA ARQUITETURA MODERNA NO BRASIL',
        'authors': ['Rodrigo Queiroz'],
        'section': 'Mesa 2 - Modos de analisar a cidade: registro e análise projetual e patrimonial',
    },

    # =========================================================================
    # Mesa 3: Modos de morar: habitações coletivas
    # =========================================================================
    {
        'title': 'EDIFÍCIO GERMAINE: MORAR MODERNO EM TRÊS TEMPOS',
        'authors': ['Alessandro José Castroviejo Ribeiro', 'Marcos José Carrilho'],
        'section': 'Mesa 3 - Modos de morar: habitações coletivas',
    },
    {
        'title': 'ENTRE A TEORIA E A PRÁTICA: EDUARDO KNEESE DE MELLO E AS DIFERENTES FORMAS DE MORAR',
        'authors': ['Aline Nassaralla Regino', 'Rafael Antonio Cunha Perrone'],
        'section': 'Mesa 3 - Modos de morar: habitações coletivas',
    },
    {
        'title': 'O PARQUE NOVO SANTO AMARO V, UMA INTERVENÇÃO MODERNA NA PERIFERIA DE SÃO PAULO',
        'authors': ['Catharina Christina Teixeira'],
        'section': 'Mesa 3 - Modos de morar: habitações coletivas',
    },
    {
        'title': 'IAPC CIDADE JARDIM E AS MODERNAS FORMAS DE MORAR',
        'authors': ['Aline Nassaralla Regino', 'Rafael Antonio Cunha Perrone'],
        'section': 'Mesa 3 - Modos de morar: habitações coletivas',
    },
    {
        'title': 'CASAS NO SERTÃO: ARQUITETURA RESIDENCIAL DE JOAQUIM GUEDES EM CARAÍBA-BA',
        'authors': ['Rogério Penna Quintanilha'],
        'section': 'Mesa 3 - Modos de morar: habitações coletivas',
    },

    # =========================================================================
    # Mesa 4: Modos de morar: habitações unifamiliares
    # =========================================================================
    {
        'title': 'LINA E BRATKE: MODOS DE MORAR DOS ARQUITETOS MODERNOS EM SÃO PAULO',
        'authors': ['Daniele Aparecida Alves', 'Aline Nassaralla Regino'],
        'section': 'Mesa 4 - Modos de morar: habitações unifamiliares',
    },
    {
        'title': 'COMO VAI ANTÔNIO!',
        'authors': ['Fernando Guillermo Vázquez Ramos', 'Andréa de Oliveira Tourinho'],
        'section': 'Mesa 4 - Modos de morar: habitações unifamiliares',
    },
    {
        'title': 'ESPORÁDICAS INTUIÇÕES. A ARQUITETURA RESIDENCIAL PAULISTA NAS REVISTAS ITALIANAS (1930-1960) - CONSIDERAÇÕES À MARGEM',
        'authors': ['Francesca Sarno'],
        'section': 'Mesa 4 - Modos de morar: habitações unifamiliares',
    },
    {
        'title': 'AS RESIDÊNCIAS PARA CLASSE MÉDIA PAULISTANA DOS ANOS 1960: UMA OBRA DO ARQUITETO MARIO MAURO GRAZIOSI',
        'authors': ['Luciana Monzillo de Oliveira', 'João Carlos Graziosi'],
        'section': 'Mesa 4 - Modos de morar: habitações unifamiliares',
    },
    {
        'title': 'POPCONCRETO E A CASA BERQUÓ: A INFLUÊNCIA DAS PROPOSTAS DE WALDEMAR CORDEIRO NA OBRA DE VILANOVA ARTIGAS',
        'authors': ['Rogério Marcondes Machado'],
        'section': 'Mesa 4 - Modos de morar: habitações unifamiliares',
    },

    # =========================================================================
    # Mesa 5: Modos de morar: entre modos de habitar e modos de construir
    # =========================================================================
    {
        'title': 'CASA NINCA BORDANO, UMA ABÓBADA NA RUA DAS JABUTICABEIRAS',
        'authors': ['Bárbara Cardoso Garcia', 'Brunna Heine'],
        'section': 'Mesa 5 - Modos de morar: entre modos de habitar e modos de construir',
    },
    {
        'title': 'EDIFÍCIO GEMINI: CONSTRUÇÃO FORMAL E TECTONICIDADE DE UM PROTÓTIPO DE HABITAÇÃO COLETIVA',
        'authors': ['Cristiane Lavall'],
        'section': 'Mesa 5 - Modos de morar: entre modos de habitar e modos de construir',
    },
    {
        'title': 'VERTICALIZAÇÃO EM SÃO PAULO: NOVOS MODOS DE MORAR NO CENTRO',
        'authors': ['Marcella França Fernandes', 'Aline Nassaralla Regino'],
        'section': 'Mesa 5 - Modos de morar: entre modos de habitar e modos de construir',
    },
    {
        'title': 'O USO DA ABÓBADA NA TIPOLOGIA RESIDENCIAL: OBRAS DE RODRIGO LEFRÈVE E SÉRGIO FERRO',
        'authors': ['Matheus Gomes Chemello', 'Pauline Fonini Felin'],
        'section': 'Mesa 5 - Modos de morar: entre modos de habitar e modos de construir',
    },

    # =========================================================================
    # Mesa 6: Modos de usar a cidade: espaços educacionais universitários
    # =========================================================================
    {
        'title': 'ARQUITETURA MODERNA EM DIÁLOGO: JORGE CARON E LUIZ GASTÃO DE CASTRO LIMA',
        'authors': ['Amanda Saba Ruggiero', 'Cristiane Kröhling Pinheiro Borges Bernardi'],
        'section': 'Mesa 6 - Modos de usar a cidade: espaços educacionais universitários',
    },
    {
        'title': 'O EDIFÍCIO DA FAU-USP – PROJETO E DISCURSO DOS VAZIOS',
        'authors': ['Bárbara Cardoso Garcia', 'Lucas Barros', 'Maíra Baltrush'],
        'section': 'Mesa 6 - Modos de usar a cidade: espaços educacionais universitários',
    },
    {
        'title': 'O EDIFÍCIO DA UNIVERSIDADE SÃO JUDAS TADEU',
        'authors': ['Eneida de Almeida', 'Maria Isabel Imbronito', 'Paula de Vicenzo Fidelis Belfort Mattos'],
        'section': 'Mesa 6 - Modos de usar a cidade: espaços educacionais universitários',
    },
    {
        'title': 'O EDIFÍCIO DA FAU SANTOS (1973 – 1976)',
        'authors': ['Taiana Car Vidotto', 'Ana Maria Reis de Goes Monteiro', 'Fernando Shigueo Nakandakare'],
        'section': 'Mesa 6 - Modos de usar a cidade: espaços educacionais universitários',
    },

    # =========================================================================
    # Mesa 7: Modos de usar a cidade: espaços da coletividade
    # =========================================================================
    {
        'title': 'A QUALIDADE ESPACIAL NAS ÁREAS COMUNITÁRIAS DE DOIS CONJUNTOS HABITACIONAIS',
        'authors': ['Isadora Finoketti Malicheski'],
        'section': 'Mesa 7 - Modos de usar a cidade: espaços da coletividade',
    },
    {
        'title': 'O PARQUE IBIRAPUERA: MONUMENTALIDADE E MODERNISMO',
        'authors': ['Ivan Souza Vieira'],
        'section': 'Mesa 7 - Modos de usar a cidade: espaços da coletividade',
    },
    {
        'title': 'CLUBES PRIVADOS, DESENHO E CIDADE DOS ANOS 1960: O CASO DA SOCIEDADE HARMONIA DE TÊNIS EM SÃO PAULO',
        'authors': ['Victor Próspero'],
        'section': 'Mesa 7 - Modos de usar a cidade: espaços da coletividade',
    },
    {
        'title': 'A CASA DO POVO BRASILEIRO: O PAVILHÃO DO BRASIL EM OSAKA, 1970',
        'authors': ['Maria Isabel Villac'],
        'section': 'Mesa 7 - Modos de usar a cidade: espaços da coletividade',
    },

    # =========================================================================
    # Mesa 8: Modos de usar a cidade: espaços culturais
    # =========================================================================
    {
        'title': 'ARQUITETURA, CINEMA E SOCIEDADE: O CINEMA DE RUA',
        'authors': ['Isabella Novais Faria'],
        'section': 'Mesa 8 - Modos de usar a cidade: espaços culturais',
    },
    {
        'title': 'A INTRODUÇÃO DA ARQUITETURA MODERNA NOS TEATROS DE SÃO PAULO: O PROJETO DE ROBERTO TIBAU PARA O TEATRO PAULO EIRÓ',
        'authors': ['Luciana Monzillo de Oliveira', 'Maria Augusta Justi Pisani'],
        'section': 'Mesa 8 - Modos de usar a cidade: espaços culturais',
    },
    {
        'title': 'DUAS OBRAS CONTEMPORÂNEAS DE DOIS ARQUITETOS MODERNOS. OSCAR NIEMEYER E PAULO MENDES DA ROCHA NO SÉCULO XXI',
        'authors': ['Ivo Renato Giroto'],
        'section': 'Mesa 8 - Modos de usar a cidade: espaços culturais',
    },
    {
        'title': 'DOS PRECEITOS ÀS PRÁTICAS DE PRESERVAÇÃO NO PATRIMÔNIO ARQUITETÔNICO MODERNO: O CASO DA BIBLIOTECA MÁRIO DE ANDRADE',
        'authors': ['Thais da Silva Santos', 'André Augusto de Almeida Alves'],
        'section': 'Mesa 8 - Modos de usar a cidade: espaços culturais',
    },

    # =========================================================================
    # Mesa 9: Modos de trabalhar: entre edifícios e modos de trabalho modernos
    # =========================================================================
    {
        'title': 'CAIXA ECONÔMICA ESTADUAL DE SÃO PAULO EM IBITINGA: 40 ANOS DO EXEMPLAR DE ARQUITETURA BANCÁRIA NA CIDADE',
        'authors': ['Paulo Yassuhide Fujioka', 'Vinicius Galbieri Severino'],
        'section': 'Mesa 9 - Modos de trabalhar: entre edifícios e modos de trabalho modernos',
    },
    {
        'title': 'DOIS EDIFÍCIOS INDUSTRIAIS DE GREGÓRIO ZOLKO. OS PROJETOS DA AMORTEX (1968) E BELZER (1976)',
        'authors': ['Ricardo José Rossin de Oliveira', 'Fernando Guillermo Vázquez Ramos'],
        'section': 'Mesa 9 - Modos de trabalhar: entre edifícios e modos de trabalho modernos',
    },
]


# ---------------------------------------------------------------------------
# Montagem do YAML
# ---------------------------------------------------------------------------

articles = []
for seq, art in enumerate(articles_data, start=1):
    articles.append(make_article(seq, art['title'], art['authors'], art['section']))

data = OrderedDict([
    ('issue', OrderedDict([
        ('slug', 'sdsp06'),
        ('title', '6º Seminário Docomomo São Paulo'),
        ('subtitle', 'A Arquitetura Moderna paulista e a questão social'),
        ('description', 'Anais do 6º Seminário Docomomo São Paulo: a arquitetura moderna paulista e a questão social. São Carlos: IAU/USP, 2018. 609 p. ISBN 978-85-66624-25-0. CDD 724.98161.'),
        ('year', 2018),
        ('volume', 1),
        ('number', 6),
        ('date_published', '2018-09-24'),
        ('isbn', '978-85-66624-25-0'),
        ('editors', [
            'Miguel Antonio Buzzar',
            'Fernando Guillermo Vázquez Ramos',
            'Paulo Yasuhide Fujioka',
        ]),
        ('source', 'https://www.nucleodocomomosp.com.br/'),
    ])),
    ('articles', articles),
])

# ---------------------------------------------------------------------------
# Escrita do YAML
# ---------------------------------------------------------------------------

output_path = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp/sdsp06.yaml'

with open(output_path, 'w', encoding='utf-8') as f:
    yaml.dump(dict(data), f, Dumper=OrderedDumper, default_flow_style=False,
              allow_unicode=True, width=10000, sort_keys=False)

print(f'YAML gerado com {len(articles)} artigos em {output_path}')
