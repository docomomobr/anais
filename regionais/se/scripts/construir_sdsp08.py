#!/usr/bin/env python3
"""
Gera o YAML do 8º Seminário Docomomo São Paulo (sdsp08) a partir dos dados
extraídos manualmente do SUMÁRIO do PDF dos anais.

Saída: sdsp08.yaml
"""

import yaml
import os

# --- OrderedDumper para manter ordem dos campos ---

class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

OrderedDumper.add_representer(dict, dict_representer)


def make_email(familyname):
    """Gera email placeholder a partir do sobrenome."""
    name = familyname.lower()
    # Remove acentos simples para email
    replacements = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ü': 'u',
        'ç': 'c',
        "\u2019": '', "'": '', " ": "_",
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    # Remove caracteres não alfanuméricos exceto _
    name = ''.join(c for c in name if c.isalnum() or c == '_')
    return f"{name}@exemplo.com"


def make_author(givenname, familyname, primary=False):
    return {
        'givenname': givenname,
        'familyname': familyname,
        'affiliation': '',
        'email': make_email(familyname),
        'primary_contact': primary,
    }


# =====================================================================
# DADOS EXTRAÍDOS DO SUMÁRIO
# =====================================================================

# Página inicial de cada artigo (homenagens + artigos), em ordem.
# Última página do livro: 610.

articles_raw = []

# --- SESSÃO DE HOMENAGEADOS (4 artigos) ---

articles_raw.append({
    'id': 'sdsp08-001',
    'title': 'HOMENAGEM À ODILÉA TOSCANO (1934-2015)',
    'authors': [
        make_author('Sara', 'Goldchmit', primary=True),
    ],
    'section': 'Homenageados',
    'start_page': 19,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-002',
    'title': 'JOÃO WALTER TOSCANO A PARTIR DE SEU ACERVO',
    'authors': [
        make_author('Vitor', 'Lima', primary=True),
        make_author('João', 'Fiammenghi'),
    ],
    'section': 'Homenageados',
    'start_page': 22,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-003',
    'title': 'O ARQUITETO UBYRAJARA GILIOLI',
    'authors': [
        make_author('Jasmine Luiza Souza', 'Silva', primary=True),
    ],
    'section': 'Homenageados',
    'start_page': 31,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-004',
    'title': 'FRANCISCO JOSÉ SANTORO',
    'authors': [
        make_author('Cristiane Kröhling Pinheiro Borges', 'Bernardi', primary=True),
        make_author('Maisa Fonseca de', 'Almeida'),
    ],
    'section': 'Homenageados',
    'start_page': 43,
    'locale': 'pt-BR',
})

# --- COMUNICAÇÕES | ARTIGOS COMPLETOS (36 artigos) ---

articles_raw.append({
    'id': 'sdsp08-005',
    'title': 'O PATRIMÔNIO ARQUITETÔNICO DA UNIVERSIDADE DE SÃO PAULO: O CASO DO CAMPUS DE SÃO CARLOS',
    'authors': [
        make_author('Julia', 'Simabukuro', primary=True),
        make_author('Miguel Antonio', 'Buzzar'),
    ],
    'section': 'Artigos Completos',
    'start_page': 57,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-006',
    'title': 'ACERVO DO INSTITUTO DE ARQUITETOS DO BRASIL – DEPARTAMENTO SÃO PAULO (IAB-SP): ESTRATÉGIAS E DESAFIOS DE GESTÃO E DIFUSÃO DOCUMENTAL',
    'authors': [
        make_author('Sabrina Studart Fontenele', 'Costa', primary=True),
        make_author('Allan Pedro dos Santos', 'Silva'),
        make_author('Emerson', 'Fioravante'),
    ],
    'section': 'Artigos Completos',
    'start_page': 71,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-007',
    'title': 'A ESCRITA DA HISTORIOGRAFIA DA ARQUITETURA MODERNA ATRAVÉS DA PESQUISA DOCUMENTAL EM ACERVO DE PROJETOS: UM ESTUDO SOBRE A CIDADE DE RIBEIRÃO PRETO, E AS POSSIBILIDADES DE CONTRIBUIÇÃO',
    'authors': [
        make_author('Ana Carolina Gleria', 'Lima', primary=True),
    ],
    'section': 'Artigos Completos',
    'start_page': 86,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-008',
    'title': 'A VERTICALIZAÇÃO PAULISTANA PELO ACERVO DA FAUUSP: UMA EXPERIÊNCIA DE PESQUISA INTEGRADA',
    'authors': [
        make_author('Rebeca Guglielmo', 'Santana', primary=True),
        make_author('André Góes Monteiro', 'Antonio'),
        make_author('Ivo Renato', 'Giroto'),
        make_author('Helena Aparecida Ayoub', 'Silva'),
    ],
    'section': 'Artigos Completos',
    'start_page': 104,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-009',
    'title': 'PORTAL DIGITAL PARA DIFUSÃO DOS ACERVOS DA FAUUSP',
    'authors': [
        make_author('Gisele Ferreira de', 'Brito', primary=True),
        make_author('Eduardo Augusto', 'Costa'),
        make_author('Leandro Manuel Reis', 'Velloso'),
    ],
    'section': 'Artigos Completos',
    'start_page': 121,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-010',
    'title': 'JORGE CARON: UMA ANÁLISE DO ACERVO PESSOAL DO ARQUITETO',
    'authors': [
        make_author('Amanda Saba', 'Ruggiero', primary=True),
        make_author('Yasmin Natália', 'Migliati'),
    ],
    'section': 'Artigos Completos',
    'start_page': 136,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-011',
    'title': 'A IMPORTÂNCIA DOS ACERVOS DE ARQUITETURA PARA A HISTORIOGRAFIA: A PESQUISA SOBRE EDUARDO KNEESE DE MELLO',
    'authors': [
        make_author('Aline Nassaralla', 'Regino', primary=True),
    ],
    'section': 'Artigos Completos',
    'start_page': 152,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-012',
    'title': 'JACQUES PILON E GIANCARLO PALANTI: PESQUISA E OS DESAFIOS DA EXTROVERSÃO DAS COLEÇÕES DA SEÇÃO TÉCNICA DE MATERIAIS ICONOGRÁFICOS DA BIBLIOTECA DA FAUUSP',
    'authors': [
        make_author('Joana Mello de Carvalho e', 'Silva', primary=True),
        make_author('Daniel Alves da', 'Silva'),
        make_author('Fernando Prudente', 'Comparini'),
    ],
    'section': 'Artigos Completos',
    'start_page': 167,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-013',
    'title': 'HERNANI DO VAL PENTEADO E A VARIAÇÃO ESTILÍSTICA',
    'authors': [
        make_author('Silvia Ferreira Santos', 'Wolff', primary=True),
    ],
    'section': 'Artigos Completos',
    'start_page': 181,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-014',
    'title': 'O ACERVO DA FAUUSP E A FORMAÇÃO ESTUDANTIL. O TRABALHO COM AS COLEÇÕES DE OSWALDO ARTHUR BRATKE E RINO LEVI',
    'authors': [
        make_author('Mônica Junqueira de', 'Camargo', primary=True),
        make_author('Thais Ribeiro da', 'Cruz'),
    ],
    'section': 'Artigos Completos',
    'start_page': 195,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-015',
    'title': 'O EDIFÍCIO DO SENAI DE SOROCABA: DO PROJETO AO ESTADO DE CONSERVAÇÃO ATUAL',
    'authors': [
        make_author('Taiana Car', 'Vidotto', primary=True),
        make_author('Rodrigo Henrique', 'Geraldo'),
    ],
    'section': 'Artigos Completos',
    'start_page': 211,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-016',
    'title': 'EDIFÍCIO NOVA CENTRAL',
    'authors': [
        make_author('Maria Luiza', 'Dutra', primary=True),
        make_author('Daniel Luiz Vieira', 'Carcavalli'),
        make_author('Diego Petrini', 'Pinheiro'),
    ],
    'section': 'Artigos Completos',
    'start_page': 225,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-017',
    'title': 'DO PÓ VIEMOS E PARA O PÓ NÃO VOLTAREMOS – O QUE NINGUÉM SABE SOBRE O EDIFÍCIO PIRAPAMA (RECIFE-PE)',
    'authors': [
        make_author('Fernanda Lúcia', 'Herbster', primary=True),
        make_author('Liliana de Souza', 'Adrião'),
    ],
    'section': 'Artigos Completos',
    'start_page': 239,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-018',
    'title': 'A MODERNIDADE EM DOIS ATOS: O TEATRO MUNICIPAL DE ARARAQUARA',
    'authors': [
        make_author('Cristiane Kröhling Pinheiro Borges', 'Bernardi', primary=True),
    ],
    'section': 'Artigos Completos',
    'start_page': 250,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-019',
    'title': 'A CASA DE UMA ARQUITETA MODERNA, ESTUDO DA RESIDÊNCIA NADIR DE CARVALHO (1975)',
    'authors': [
        make_author('Felipe Taroh Inoue', 'Sanquetta', primary=True),
    ],
    'section': 'Artigos Completos',
    'start_page': 267,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-020',
    'title': 'A IMPORTÂNCIA DOS ACERVOS ICONOGRÁFICOS PARA A COMPREENSÃO DO PROCESSO PROJETUAL NA ARQUITETURA: O EXEMPLO DO EDIFÍCIO SÃO LUIZ, DE MARCELLO FRAGELLI',
    'authors': [
        make_author('Mario Tavares Moura', 'Moura Filho', primary=True),
        make_author('Tatiana', 'Sakurai'),
    ],
    'section': 'Artigos Completos',
    'start_page': 282,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-021',
    'title': 'REFLEXÕES SOBRE A CASA BROOS: O PROCESSO PROJETUAL ATRAVÉS DOS DESENHOS DO ACERVO',
    'authors': [
        make_author('Fernando Guillermo', 'Vázquez Ramos', primary=True),
        make_author('Ana Carolina Buim Azevedo', 'Marques'),
    ],
    'section': 'Artigos Completos',
    'start_page': 298,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-022',
    'title': 'A PRESERVAÇÃO E DESTRUIÇÃO DAS OBRAS DO ARQUITETO AYRTON LOLÔ CORNELSEN',
    'authors': [
        make_author('Marcia', 'Cavalieri', primary=True),
    ],
    'section': 'Artigos Completos',
    'start_page': 316,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-023',
    'title': 'MASP: DESAFIOS DA PRESERVAÇÃO E SALVAGUARDA. ADEQUAÇÃO ÀS NORMAS DE SEGURANÇA CONTRA INCÊNDIO E RESTAURO DAS FACHADAS DO MUSEU DE ARTE DE SÃO PAULO',
    'authors': [
        make_author('Miriam', 'Elwing', primary=True),
        make_author('Ana Marta', 'Ditolvo'),
        make_author('Maria Aparecida', 'Soukef'),
    ],
    'section': 'Artigos Completos',
    'start_page': 331,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-024',
    'title': 'ESPAÇO COMO OBJETO DE CONSERVAÇÃO: UM ESTUDO DIACRÔNICO DO PAVILHÃO CICCILLO MATARAZZO (1954-2021)',
    'authors': [
        make_author('Lívia Morais', 'Nóbrega', primary=True),
        make_author('Luiz Manuel do Eirado', 'Amorim'),
    ],
    'section': 'Artigos Completos',
    'start_page': 351,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-025',
    'title': 'O USO DA GRELHA NOS EDIFÍCIOS RESIDENCIAIS DE MMM ROBERTO: DA REGULARIDADE À DISTORÇÃO',
    'authors': [
        make_author('Luísa Dresch', 'Prediger', primary=True),
        make_author('Carlos Fernando Silva', 'Bahima'),
    ],
    'section': 'Artigos Completos',
    'start_page': 369,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-026',
    'title': 'ARQUITETURA E CIDADE NO PROCESSO DE MODERNIZAÇÃO: LONDRINA E SUA PRODUÇÃO MODERNA NA DÉCADA DE 1950',
    'authors': [
        make_author('Fernanda Millan', 'Fachi', primary=True),
        make_author('Miguel Antonio', 'Buzzar'),
    ],
    'section': 'Artigos Completos',
    'start_page': 385,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-027',
    'title': 'CIA. CITY: ACERVO E PESQUISAS',
    'authors': [
        make_author('Silvia Ferreira Santos', 'Wolff', primary=True),
        make_author('Aline Nassaralla', 'Regino'),
        make_author("Roseli Maria Martin", "D'Elboux"),
    ],
    'section': 'Artigos Completos',
    'start_page': 400,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-028',
    'title': 'INTERVENÇÕES ARQUITETÔNICAS EM RESIDÊNCIAS MODERNAS NO NORDESTE BRASILEIRO: ESTUDOS DE CASOS EM CAMPINA GRANDE, PB',
    'authors': [
        make_author('Alcilia', 'Afonso', primary=True),
    ],
    'section': 'Artigos Completos',
    'start_page': 414,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-029',
    'title': 'LEVANTAMENTOS DIGITAIS COMO METODOLOGIA DE IDENTIFICAÇÃO DA ARQUITETURA MODERNA NO CENTRO DE RIBEIRÃO PRETO',
    'authors': [
        make_author('Laura Marques', 'dos Santos', primary=True),
        make_author('Tatiana de Souza', 'Gaspar'),
    ],
    'section': 'Artigos Completos',
    'start_page': 428,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-030',
    'title': 'DEAMBULAR PELO MODERNO: O CAMINHAR COMO PRESERVAÇÃO DA ARQUITETURA MODERNA DE CURITIBA',
    'authors': [
        make_author('Isabela Ignacio de', 'Moura', primary=True),
        make_author('Karina Scussiato', 'Pimentel'),
    ],
    'section': 'Artigos Completos',
    'start_page': 443,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-031',
    'title': 'CENTRO HISTÓRICO DE SÃO PAULO: DOCUMENTAÇÃO E ESTUDOS DE REABILITAÇÃO',
    'authors': [
        make_author('Marcos J.', 'Carrilho', primary=True),
        make_author('Alessandro J C.', 'Ribeiro'),
        make_author('Cecilia H G R dos', 'Santos'),
        make_author('Silvia F S.', 'Wolff'),
    ],
    'section': 'Artigos Completos',
    'start_page': 458,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-032',
    'title': 'PATRIMÔNIO FERROVIÁRIO DE BIRIGUI: POTENCIALIDADES CONTEMPORÂNEAS DE CONSERVAÇÃO E PRESERVAÇÃO',
    'authors': [
        make_author('Evelyn Caroline da Silva', 'Camara', primary=True),
        make_author('Hélio', 'Hirao'),
    ],
    'section': 'Artigos Completos',
    'start_page': 472,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-033',
    'title': 'O PAPEL DA GALERIA DE DESIGN NA PRESERVAÇÃO DO MÓVEL MODERNO BRASILEIRO: A EXPERIÊNCIA DA BOSSA FURNITURE',
    'authors': [
        make_author('Ariel Brasileiro', 'Lins', primary=True),
        make_author('Isabela Ferreira', 'Milagre'),
    ],
    'section': 'Artigos Completos',
    'start_page': 485,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-034',
    'title': 'GARE DO ORIENTE: ÂNCORA ARQUITETÔNICA, DINÂMICA NA EXPO98',
    'authors': [
        make_author('Oreste', 'Bortolli Junior', primary=True),
        make_author('Gerson Fernandes', 'Brancaliao'),
    ],
    'section': 'Artigos Completos',
    'start_page': 500,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-035',
    'title': 'ARQUITETURA E AS BIENAIS: O ACERVO DO ARQUIVO HISTÓRICO WANDA SVEVO',
    'authors': [
        make_author('Raíssa', 'Armelin Lopes', primary=True),
        make_author('Ana Maria Reis de Goes', 'Monteiro'),
    ],
    'section': 'Artigos Completos',
    'start_page': 518,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-036',
    'title': 'CERTIDÕES VINTENÁRIAS COMO FONTES DOCUMENTAIS: ALTERNATIVAS PARA A COMPREENSÃO HISTÓRICA DE UM PATRIMÔNIO ARQUITETÔNICO DE NIEMEYER NO INTERIOR DO RIO DE JANEIRO',
    'authors': [
        make_author('Julia', 'Andrade', primary=True),
    ],
    'section': 'Artigos Completos',
    'start_page': 534,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-037',
    'title': 'CONCURSO COMO PRÁTICA: O PROCESSO DE PESQUISA',
    'authors': [
        make_author('Beatriz Agostini', 'Teixeira', primary=True),
        make_author('Marina', 'Oba'),
        make_author('Daniela', 'Moro'),
    ],
    'section': 'Artigos Completos',
    'start_page': 549,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-038',
    'title': 'A PESQUISA HISTORIOGRÁFICA COMO PROPULSORA DA DISCUSSÃO SOBRE A IMPORTÂNCIA DOS ACERVOS DE CONCURSOS PÚBLICOS DE ANTEPROJETOS',
    'authors': [
        make_author('Cassandra Salton', 'Coradin', primary=True),
    ],
    'section': 'Artigos Completos',
    'start_page': 562,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-039',
    'title': 'NARRATIVAS DA MODERNIDADE: O PROBLEMA DAS "ESCOLAS" E OS ACERVOS NA HISTORIOGRAFIA DA ARQUITETURA',
    'authors': [
        make_author('Luz de', 'Lucca Neto', primary=True),
    ],
    'section': 'Artigos Completos',
    'start_page': 578,
    'locale': 'pt-BR',
})

articles_raw.append({
    'id': 'sdsp08-040',
    'title': 'O CONCURSO E O PROJETO PREMIADO PARA A SEDE DA SBPC (1978)',
    'authors': [
        make_author('Isabella Caroline', 'Januário', primary=True),
        make_author('Andryelle de Carvalho', 'Ptaszek'),
        make_author('Renato Leão', 'Rego'),
    ],
    'section': 'Artigos Completos',
    'start_page': 594,
    'locale': 'pt-BR',
})

# =====================================================================
# CALCULAR PÁGINAS (end = next start - 1; último termina em 610)
# =====================================================================

LAST_PAGE = 610

for i, art in enumerate(articles_raw):
    start = art['start_page']
    if i + 1 < len(articles_raw):
        end = articles_raw[i + 1]['start_page'] - 1
    else:
        end = LAST_PAGE
    art['pages'] = f"{start}-{end}"


# =====================================================================
# MONTAR ESTRUTURA YAML
# =====================================================================

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
for art in articles_raw:
    article = {
        'id': art['id'],
        'title': art['title'],
        'authors': art['authors'],
        'section': art['section'],
        'pages': art['pages'],
        'locale': art['locale'],
        'file': f"{art['id']}.pdf",
    }
    articles.append(article)

data = {
    'issue': issue,
    'articles': articles,
}

# =====================================================================
# ESCREVER YAML
# =====================================================================

output_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(output_dir, 'sdsp08.yaml')

with open(output_path, 'w', encoding='utf-8') as f:
    yaml.dump(data, f, Dumper=OrderedDumper, default_flow_style=False,
              allow_unicode=True, width=10000, sort_keys=False)

print(f"Arquivo gerado: {output_path}")
print(f"Total de artigos: {len(articles)}")
print(f"  Homenageados: {sum(1 for a in articles if a['section'] == 'Homenageados')}")
print(f"  Artigos Completos: {sum(1 for a in articles if a['section'] == 'Artigos Completos')}")
