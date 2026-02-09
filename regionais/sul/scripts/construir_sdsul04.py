#!/usr/bin/env python3
"""Constrói YAML do sdsul04 a partir do índice e programa."""

import yaml

class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

OrderedDumper.add_representer(dict, dict_representer)

issue = {
    'slug': 'sdsul04',
    'title': '4º Seminário Docomomo Sul, Porto Alegre, 2013',
    'subtitle': 'Pedra, barro e metal: norma e licença na arquitetura moderna do cone sul americano, 1930-1970',
    'description': 'COMAS, Carlos Eduardo; CABRAL, Claudia Costa; CATTANI, Airton (org.). Anais do IV Seminário do.co.mo.mo_sul, Porto Alegre, 25-27 mar. 2013 [recurso eletrônico]. Porto Alegre: PROPAR/UFRGS, 2013. 1 CD-ROM. ISBN 978-85-60188-13-4.',
    'year': 2013,
    'volume': 1,
    'number': 4,
    'date_published': '2013-03-25',
    'isbn': '978-85-60188-13-4',
    'publisher': 'PROPAR/UFRGS',
    'editors': [
        'Carlos Eduardo Comas',
        'Claudia Costa Cabral',
        'Airton Cattani',
    ],
    'source': 'https://www.ufrgs.br/propar/anais-do-4o-seminario-docomomo-sul/',
}

# Dados extraídos do índice (DOCOMOMO_2013.pdf) e programa (Programa_DOCOMOMO_2013.pdf)
# Formato: (num, file, title, authors_list, session)
# Sessões de comunicação (1-6) do programa
articles_data = [
    (1, '01-Adalbelto-Vilela_Sylvia-Ficher.pdf',
     'João Filgueiras Lima e a alegoria da construção',
     [('Adalberto', 'Vilela', ''), ('Sylvia', 'Ficher', 'UnB')],
     'Sessão de comunicação 3'),

    (2, '02-Alex-Brino_-Anna-Cannes.pdf',
     'Lucio Costa: lugar e recorrência da materialidade colonial',
     [('Alex Carvalho', 'Brino', ''), ('Anna Paula', 'Canez', '')],
     'Sessão de comunicação 4'),

    (3, '03-Alfredo-Pelaez.pdf',
     'El bosque y la espiral',
     [('Alfredo', 'Peláez', '')],
     'Sessão de comunicação 2'),

    (4, '04-Ana-Carolina-Pellegrini.pdf',
     'Pedra, papel: tesouro',
     [('Ana Carolina', 'Pellegrini', '')],
     'Sessão de comunicação 1'),

    (5, '05-Ana-Cristina-Fernandes-Vaz-Milheiro.pdf',
     'Arquitectura colonial portuguesa e sistemas construtivos tradicionais africanos: abordagens modernas',
     [('Ana Cristina Fernandez Vaz', 'Milheiro', '')],
     'Sessão de comunicação 6'),  # not in programa, inferring from index position

    (6, '06-Ana-Elisia-Costa.pdf',
     'A poética dos tijolos aparentes e o caráter industrial: MAESA (1948)',
     [('Ana Elísia da', 'Costa', '')],
     'Sessão de comunicação 5'),

    (7, '07-Ana-Gabriela-Lima_Andraci-Atique.pdf',
     'Casas casadas: o emprego dos tijolos e a ideia de moderno nas casas de Joaquim e Liliana Guedes',
     [('Ana Gabriela Godinho', 'Lima', ''), ('Andraci Maria', 'Atique', '')],
     'Sessão de comunicação 2'),

    (8, '08-Ana-Elisa-Souto.pdf',
     'A técnica e o material como instrumentos para a geração formal na obra de Paulo Mendes da Rocha',
     [('Ana Elisa', 'Souto', '')],
     'Sessão de comunicação 6'),

    (9, '09-Andrea-Soler-Machado.pdf',
     'A pedra na arquitetura moderna de Porto Alegre, 1950-70',
     [('Andréa Soler', 'Machado', '')],
     'Sessão de comunicação 5'),

    (10, '10-Carla-Caires.pdf',
     'A cidade aberta de Ritoque: campo de experimentação',
     [('Carla', 'Caires', '')],
     'Sessão de comunicação 4'),

    (11, '11-Carlos-Bahima.pdf',
     'Colunas metálicas sob cobertura plana: exceção e regra na casa Helio Dourado',
     [('Carlos Fernando Silva', 'Bahima', '')],
     'Sessão de comunicação 2'),

    (12, '12-Carlos-Henrique-Magalhaes-de-Lima.pdf',
     'Produção em massa e índice espacial: a pré-fabricação na arquitetura de Milton Ramos',
     [('Carlos Henrique Magalhães de', 'Lima', '')],
     'Sessão de comunicação 3'),

    (13, '13-Celia-Castro-Gonsales.pdf',
     'Ofício e arte na arquitetura moderna: Ari Marangon, arquiteto artesão',
     [('Célia', 'Gonsales', '')],
     'Sessão de comunicação 5'),

    (14, '14-claudia_cabral_Helena-bender.pdf',
     'Usos do primitivismo: pedra, barro e arquitetura moderna',
     [('Cláudia Piantá Costa', 'Cabral', ''), ('Helena', 'Bender', '')],
     'Sessão de comunicação 4'),

    (15, '15-Danilo-Matoso-Bruna-Lima-Elcio-da-Silva.pdf',
     'Aço e alumínio nas fachadas da Câmara dos Deputados',
     [('Danilo Matoso', 'Macedo', ''), ('Bruna', 'Lima', ''), ('Elcio Gomes da', 'Silva', '')],
     'Sessão de comunicação 3'),

    (16, '16-Eduardo-Pierrotti-Rossetti.pdf',
     'Brasília-patrimônio: desdobrar desafios e encarar o presente',
     [('Eduardo Pierrotti', 'Rossetti', '')],
     'Sessão de comunicação 3'),

    (17, '17-Elane-Peixoto.pdf',
     'Lelé, um arquiteto para sempre moderno',
     [('Elane Ribeiro', 'Peixoto', '')],
     'Sessão de comunicação 3'),

    (18, '18-Elcio-da-Silva_Danilo-Matoso.pdf',
     'Estruturas metálicas no concreto de Brasília',
     [('Elcio Gomes da', 'Silva', ''), ('Danilo Matoso', 'Macedo', '')],
     'Sessão de comunicação 3'),

    (19, '19-Gonzalo-Gambaro.pdf',
     'El conjunto habitacional CAP: exploraciones de nueva materialidad',
     [('Gonzalo', 'Abarca', '')],
     'Sessão de comunicação 6'),  # index says Gonzalo Abarca, file says Gambaro

    (20, '20-Horacio-Torrent.pdf',
     'Ciudades de barro: experiencia urbana y cultura material en la arquitectura chilena del siglo XX',
     [('Horacio', 'Torrent', '')],
     'Sessão de comunicação 4'),

    (21, '21-Igor-Fracalossi.pdf',
     'Uma realidade ausente: casa em Jean Mermoz',
     [('Igor', 'Fracalossi', '')],
     'Sessão de comunicação 2'),

    (22, '22-Jose-Artur-Frota_Eline-Caixeta.pdf',
     "É pau, é pedra, é o fim do caminho / É um resto de toco, é um pouco sozinho: quatro projetos, uma paisagem",
     [("José Artur D'Aló", 'Frota', ''), ('Eline', 'Caixeta', '')],
     'Sessão de comunicação 4'),

    (23, '23-Juan-Pablo-Tuja.pdf',
     'De naturaleza moderna',
     [('Juan Pablo', 'Tuja', '')],
     'Sessão de comunicação 6'),

    (24, '24-Leonardo-Fitz.pdf',
     'Os casos das igrejas de Eladio Dieste em Atlântida e Durazno',
     [('Leonardo', 'Fitz', '')],
     'Sessão de comunicação 4'),

    (25, '25-liege-puhl.pdf',
     'O uso do metal nas rearquiteturas brasileiras',
     [('Liege Sieben', 'Puhl', '')],
     'Sessão de comunicação 1'),

    (26, '26-Luis-Henrique-Haas-Luccas.pdf',
     'Blocks modernos para o ócio: o edifício Vanguardia em Punta del Este, 1956',
     [('Luis Henrique Haas', 'Luccas', '')],
     'Sessão de comunicação 6'),

    (27, '27-Luis-Muller.pdf',
     'Lo suave y lo áspero: texturas y contrastes en las casas de Wladimiro Acosta',
     [('Luis', 'Muller', '')],
     'Sessão de comunicação 1'),

    (28, '28-Macarena-Cortes-D.pdf',
     "Arquitectura moderna y turismo en Chile: madera y piedra en el Hotel Termas de Puyehue y el Hotel Portillo",
     [('Macarena', 'Cortés', ''), ("Luz María Vergara", "D'Alençon", ''), ('Anita Puig', 'Gomes', '')],
     'Sessão de comunicação 6'),

    (29, '29-Marcelo-Dela-Giustina.pdf',
     'Identidade material: legibilidade de usos e materialidade no Edifício Floragê, David Libeskind, Porto Alegre, 1963',
     [('Marcelo Della', 'Giustina', '')],
     'Sessão de comunicação 6'),

    (30, '30-Marcos-Petroli-Luis-Henrique-Luccas.pdf',
     'Vedações de tijolos aparentes, estrutura de concreto: uma análise da prática através do Centro Municipal de Cultura de Porto Alegre',
     [('Marcos', 'Petroli', ''), ('Luis Henrique Haas', 'Luccas', '')],
     'Sessão de comunicação 5'),

    (31, '31-Maria-Ana-Ferre.pdf',
     'A casa, a pedra, e os três projetos de Eduardo Sacriste',
     [('Maria Ana', 'Ferré', '')],
     'Sessão de comunicação 2'),

    (32, '32-Maria-Luiza-Adams-Sanvitto.pdf',
     'A tenda moderna: o uso da pedra e do metal numa obra de exceção',
     [('Maria Luiza Adams', 'Sanvitto', '')],
     'Sessão de comunicação 2'),

    (33, '33-Marta-Silveira-Peixoto.pdf',
     'Vidro feito de metal',
     [('Marta Silveira', 'Peixoto', '')],
     'Sessão de comunicação 1'),

    (34, '34-Martin-Gonzalez-Luz.pdf',
     'El ladrillo y la estructura en la arquitectura de Payssé y Lorente',
     [('Martin Gonzalez', 'Luz', '')],
     'Sessão de comunicação 6'),

    (35, '35-Michelle-Schneider-Santos.pdf',
     'Arte e arquitetura moderna no Paraná: o uso do painel cerâmico na obra de Forte e Gandolfi',
     [('Michelle Schneider', 'Santos', '')],
     'Sessão de comunicação 5'),

    (36, '36-Monika-Stumpp_Ana-Elisia-Costa.pdf',
     'Janelas "modernas": materialidade das aberturas na arquitetura moderna de Caxias do Sul',
     [('Monika Maria', 'Stumpp', ''), ('Ana Elísia da', 'Costa', '')],
     'Sessão de comunicação 5'),

    (37, '37-nathalia-cantergiani.pdf',
     'Superfícies abstratas: o elemento cerâmico como textura na arquitetura moderna brasileira',
     [('Nathalia Cantergiani Fagundes de', 'Oliveira', '')],
     'Sessão de comunicação 5'),

    (38, '38-Pamela-Dominguez-Bastidas.pdf',
     'Vinculaciones técnicas, históricas y arquitectónicas sobre el origen del asentamiento moderno de Cerro Sombrero en Tierra del Fuego, con la producción acerera en el sur de Chile',
     [('Pamela', 'Dominguez', '')],
     'Sessão de comunicação 4'),

    (39, '39-Pedro-Morais.pdf',
     'Decifrando a esfinge: uma tentativa de análise do Conjunto JK',
     [('Pedro', 'Morais', '')],
     'Sessão de comunicação 3'),

    (40, '40-Renata-Santiago-Ramos.pdf',
     'Casa Dico, casa do automóvel: programa moderno e suas explorações técnicas e formais, Porto Alegre, 1952',
     [('Renata Santiago', 'Ramos', '')],
     'Sessão de comunicação 5'),

    (41, '41-Ruth-Zein_Silvia-Raquel-Chiarelli.pdf',
     'Tijolo por tijolo num desenho mágico: a "casinha" de Vilanova Artigas',
     [('Ruth Verde', 'Zein', ''), ('Silvia Raquel', 'Chiarelli', '')],
     'Sessão de comunicação 1'),

    (42, '42-Silvia-Leao.pdf',
     'Lota de Macedo Soares: casa moderna, materialidade híbrida',
     [('Silvia', 'Leão', '')],
     'Sessão de comunicação 2'),

    (43, '43-Silvia-Raquel-Chiarelli.pdf',
     'A presença do concreto, da madeira e do metal no restaurante vertical Fasano',
     [('Silvia Raquel', 'Chiarelli', '')],
     'Sessão de comunicação 6'),

    (44, '44-Suely-de-Oliveira-Figueiredo-Puppi.pdf',
     'Lina Bo Bardi: metal e pedra na casa de vidro',
     [('Suely de Oliveira Figueiredo', 'Puppi', '')],
     'Sessão de comunicação 1'),

    (45, '45-Veronica-Saavedra.pdf',
     'Casa Labbé de Emilio Duhart H. y Héctor Valdés P., Santiago de Chile, 1941: materialidad vernácula para una concepción moderna',
     [('Verónica Esparza', 'Saavedra', '')],
     'Sessão de comunicação 1'),

    (46, '46-paulo-bruna_camila-schimidt.pdf',
     'Abóbadas inéditas: o SESI de Osasco/SP',
     [('Paulo Julio Valentino', 'Bruna', ''), ('Camila', 'Schmidt', '')],
     'Sessão de comunicação 4'),
]

articles = []
for num, filename, title, authors, session in articles_data:
    art_id = f'sdsul04-{num:03d}'

    # Separate title/subtitle at first colon
    if ': ' in title:
        parts = title.split(': ', 1)
        art_title = parts[0]
        art_subtitle = parts[1]
    elif ' / ' in title:
        parts = title.split(' / ', 1)
        art_title = parts[0]
        art_subtitle = parts[1]
    else:
        art_title = title
        art_subtitle = None

    # Detect locale from title
    spanish_indicators = ['el ', 'la ', 'las ', 'los ', 'del ', 'en ', 'una ', 'con ', 'sur ', 'de naturaleza']
    title_lower = title.lower()
    if any(title_lower.startswith(ind) or f' {ind}' in title_lower for ind in spanish_indicators):
        # Check more carefully
        es_words = sum(1 for w in ['el', 'la', 'las', 'los', 'del', 'en', 'una', 'con', 'sur', 'arquitectura', 'moderna', 'materialidad', 'experiencia'] if w in title_lower.split())
        pt_words = sum(1 for w in ['de', 'na', 'no', 'da', 'do', 'em', 'uma', 'para', 'arquitetura'] if w in title_lower.split())
        if es_words > pt_words:
            locale = 'es'
        else:
            locale = 'pt-BR'
    else:
        locale = 'pt-BR'

    authors_list = []
    for i, (given, family, affil) in enumerate(authors):
        authors_list.append({
            'givenname': given,
            'familyname': family,
            'affiliation': affil,
            'email': f'{family.lower().replace(" ", "").replace("'", "")}@exemplo.com',
            'primary_contact': i == 0,
        })

    article = {
        'id': art_id,
        'title': art_title,
    }
    if art_subtitle:
        article['subtitle'] = art_subtitle
    article['authors'] = authors_list
    article['section'] = session
    article['locale'] = locale
    article['file'] = f'{art_id}.pdf'
    article['file_original'] = filename
    article['abstract'] = None
    article['abstract_en'] = None
    article['keywords'] = []
    article['keywords_en'] = []

    articles.append(article)

output = {'issue': issue, 'articles': articles}

outpath = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul/sdsul04.yaml'
with open(outpath, 'w', encoding='utf-8') as f:
    yaml.dump(output, f, Dumper=OrderedDumper, width=10000, sort_keys=False,
              allow_unicode=True, default_flow_style=False)

print(f'Escrito {outpath} com {len(articles)} artigos')

# Stats
sessions = {}
for a in articles:
    s = a['section']
    sessions[s] = sessions.get(s, 0) + 1
for s, c in sorted(sessions.items()):
    print(f'  {s}: {c} artigos')

locales = {}
for a in articles:
    l = a['locale']
    locales[l] = locales.get(l, 0) + 1
for l, c in sorted(locales.items()):
    print(f'  Locale {l}: {c}')
