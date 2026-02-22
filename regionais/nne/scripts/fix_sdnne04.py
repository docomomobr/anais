#!/usr/bin/env python3
"""
fix_sdnne04.py - Fix known issues in sdnne04.yaml after initial extraction.

Fixes:
- Section normalization (OCR variants, missing eixo)
- Author names (parsing artifacts, OCR garbled)
- Email assignment (from PDF text)
- Missing authors (articles 032, 039)
- Missing/garbled abstracts
- Title artifacts
"""

import yaml
import re
from collections import OrderedDict

YAML_PATH = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/nne/sdnne04.yaml'


# ── YAML Dumper ──────────────────────────────────────────────

class OrderedDumper(yaml.SafeDumper):
    pass

def _dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

def _str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def _none_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:null', '~')

OrderedDumper.add_representer(OrderedDict, _dict_representer)
OrderedDumper.add_representer(dict, _dict_representer)
OrderedDumper.add_representer(str, _str_representer)
OrderedDumper.add_representer(type(None), _none_representer)


def make_author(givenname, familyname, email, affiliation=None, country='BR', primary_contact=False):
    return {
        'givenname': givenname,
        'familyname': familyname,
        'email': email,
        'affiliation': affiliation,
        'orcid': None,
        'bio': None,
        'country': country,
        'primary_contact': primary_contact,
    }


def fix_yaml():
    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    articles = data['articles']
    fixes = 0

    for a in articles:
        aid = a['id']

        # ── Fix sections ────────────────────────────────────────
        section = a.get('section', '')

        # Normalize all section variants
        section_lower = section.lower().strip()
        if 'narrativa' in section_lower and 'historiogr' in section_lower:
            a['section'] = 'Narrativas historiográficas'
            fixes += 1
        elif 'narrativas hist' in section_lower:
            a['section'] = 'Narrativas historiográficas'
            fixes += 1
        elif 'narrrativas' in section_lower or 'arrativas' in section_lower:
            a['section'] = 'Narrativas historiográficas'
            fixes += 1
        elif 'mático' in section_lower and 'narr' in section_lower:
            a['section'] = 'Narrativas historiográficas'
            fixes += 1

        # ── Article-specific fixes ──────────────────────────────

        if aid == 'sdnne04-001':
            # Keywords PT: only got "bioclimática" but should be full list
            # From PDF: "arquitetura moderna nordestina, projetos arquitetônicos, arquitetura bioclimática."
            # pdftotext split them across lines
            a['keywords'] = ['arquitetura moderna nordestina', 'projetos arquitetônicos', 'arquitetura bioclimática']

        elif aid == 'sdnne04-006':
            # Emails misassigned. Fix from PDF:
            a['authors'] = [
                make_author('Patrícia', 'Barbosa', 'patricia_b_francisco@hotmail.com', 'DARQ-UFRN', primary_contact=True),
                make_author('Felipe', 'Lopes', 'felipearaujo0@hotmail.com', 'DARQ-UFRN'),
                make_author('Giulia', 'Macêdo', 'giulia_macedo@hotmail.com', 'DARQ-UFRN'),
                make_author('Isadora', 'Paiva', 'isa_ndbp@hotmail.com', 'DARQ-UFRN'),
            ]
            fixes += 1

        elif aid == 'sdnne04-007':
            # Missing eixo ("Experiências de conservação e transformação" from PDF text)
            a['section'] = 'Experiências de conservação e transformação'
            # Fix emails from PDF
            a['authors'] = [
                make_author('Jeová de', 'Barros', 'jeovadebarros@ig.com.br', 'PPGAU-UFPA', primary_contact=True),
                make_author('Celma', 'Chaves', 'celma@ufpa.br', 'PPGAU-UFPA'),
            ]
            fixes += 1

        elif aid == 'sdnne04-008':
            # Title has linebreak issue: "Quando o Moderno era um Estorvo ao Tombamento do IPHAN. O Hotel São Fr"
            a['title'] = 'Quando o Moderno era um Estorvo ao Tombamento do IPHAN'
            a['subtitle'] = 'o Hotel São Francisco em Penedo, Alagoas'
            # Fix author: BRENDLE, Betânia (1). -> number after name
            a['authors'] = [
                make_author('Betânia', 'Brendle', 'maria_cavalcanti@baunetz.de', 'UFS', primary_contact=True),
            ]
            fixes += 1

        elif aid == 'sdnne04-009':
            # Fix author names and emails from PDF
            a['authors'] = [
                make_author('Renata M. V.', 'Caldas', 'renatavcaldas@terra.com.br', 'UFPE', primary_contact=True),
                make_author('Fernando Diniz', 'Moreira', 'fmoreira@hotlink.com.br', 'UFPE'),
            ]
            fixes += 1

        elif aid == 'sdnne04-010':
            # Fix emails from PDF
            a['authors'] = [
                make_author('Nathalia Bocayuva', 'Carvalho', 'natybocayuva@hotmail.com', 'DARQ-UFRN', primary_contact=True),
                make_author('Anna Paula Santos', 'Emerenciano', 'annapaulaemerenciano@hotmail.com', 'DARQ-UFRN'),
                make_author('Priscila Ferreira de', 'Macedo', 'lilamacedo@hotmail.com', 'DARQ-UFRN'),
            ]
            fixes += 1

        elif aid == 'sdnne04-012':
            # Fix eixo and emails
            a['section'] = 'A arquitetura moderna como projeto'
            a['authors'] = [
                make_author('Vanessa', 'Cordeiro', 'vanessaacordeiro@hotmail.com', 'UFPI', primary_contact=True),
                make_author('Emerson', 'Mourão', 'emersonlgm@hotmail.com', 'UFPI'),
            ]
            fixes += 1

        elif aid == 'sdnne04-013':
            # Fix emails from PDF (DOCONATAL016 - Cotrim, Tinem, Vidal)
            a['authors'] = [
                make_author('Marcio', 'Cotrim', 'marcio@vitruvius.es', 'UFPB', primary_contact=True),
                make_author('Nelci', 'Tinem', 'ntinem@uol.com.br', 'UFPB'),
                make_author('Wylnna C. L.', 'Vidal', 'wylnna@yahoo.com.br', 'UFPB'),
            ]
            fixes += 1

        elif aid == 'sdnne04-014':
            # Fix author names: "Josemary Omena. P Ferrare" -> "Josemary Omena Passos Ferrare"
            # From PDF: FERRARE, Josemary Omena. P. / ARAÚJO, Méllia Nichole D. / CAVALCANTE, Regina Barbosa. L.
            a['authors'] = [
                make_author('Josemary Omena Passos', 'Ferrare', 'jferrare@uol.com.br', 'PPGAU-UFAL', primary_contact=True),
                make_author('Méllia Nichole Della Bianca', 'Araújo', 'nichole_dellabianca@hotmail.com', 'PPGAU-UFAL'),
                make_author('Regina Barbosa Lopes', 'Cavalcante', 'cavalcante.regina@gmail.com', 'PPGAU-UFAL'),
            ]
            fixes += 1

        elif aid == 'sdnne04-015':
            # OCR garbled PDF (DOCONATAL018 - Ferrare/Medeiros)
            a['title'] = 'Representações de modernidade na "Praia da Avenida" — Maceió'
            a['subtitle'] = 'pontuando o passado, o presente (e o futuro?).'
            a['section'] = 'Narrativas historiográficas'
            a['authors'] = [
                make_author('Josemary Omena Passos', 'Ferrare', 'jferrare@uol.com.br', 'UFAL', primary_contact=True),
                make_author('Elaine Albuquerque', 'Medeiros', 'medeiros@exemplo.com', 'UFAL'),
            ]
            fixes += 1

        elif aid == 'sdnne04-016':
            # Fix section (OCR artifact "Narrativas arrativas...")
            a['section'] = 'Narrativas historiográficas'
            fixes += 1

        elif aid == 'sdnne04-017':
            # Fix author name: "M. Betânia Furtado" -> proper split
            a['authors'] = [
                make_author('M. Betânia', 'Furtado', 'betaniaguerra@uol.com.br', 'UFPI', primary_contact=True),
            ]
            fixes += 1

        elif aid == 'sdnne04-018':
            # Fix author names and emails from PDF (DOCONATAL021 - Galdino/Medeiros/Tinem)
            a['authors'] = [
                make_author('Jaime Ferreira', 'Galdino', 'jaimegferreira@hotmail.com', 'UFPB', primary_contact=True),
                make_author('Elis Dantas', 'Medeiros', 'elisdantasmedeiros@bol.com.br', 'UFPB'),
                make_author('Nelci', 'Tinem', 'ntinem@uol.com.br', 'UFPB'),
            ]
            fixes += 1

        elif aid == 'sdnne04-019':
            # Fix title: includes author bio text in subtitle
            a['title'] = 'Urbanismo moderno no Brasil'
            a['subtitle'] = 'três projetos, três momentos.'
            # Author name: "GONSALES¸Célia" (weird cedilla)
            a['authors'] = [
                make_author('Célia', 'Gonsales', 'celia.gonsales@gmail.com', 'UFPel', primary_contact=True),
            ]
            fixes += 1

        elif aid == 'sdnne04-020':
            # Fix emails from PDF (DOCONATAL023 - Gribel/Sanjad)
            a['authors'] = [
                make_author('Renata L.', 'Gribel', 'renatalgribel@gmail.com', 'PPGAU-UFPA', primary_contact=True),
                make_author('Thais A. B. Caminha', 'Sanjad', 'thais@ufpa.br', 'PPGAU-UFPA'),
            ]
            fixes += 1

        elif aid == 'sdnne04-021':
            # Fix section and emails from PDF (DOCONATAL024 - Jucá Neto/Andrade)
            a['section'] = 'Narrativas historiográficas'
            # Fix title truncation
            a['title'] = 'Construção, tradição e modernismo na obra do arquiteto José Liberal de Castro'
            a['subtitle'] = None
            a['authors'] = [
                make_author('Clovis Ramiro', 'Jucá Neto', 'clovisj@uol.com.br', 'DAU-UFC', primary_contact=True),
                make_author('Margarida Julia Farias de Salles', 'Andrade', 'andrade@exemplo.com', 'DAU-UFC'),
            ]
            fixes += 1

        elif aid == 'sdnne04-023':
            # Fix emails from PDF (DOCONATAL026 - Leite/Ramos)
            a['authors'] = [
                make_author('Carolina', 'Leite', 'carolina@carolinamartins.com', 'FAUTL', 'PT', primary_contact=True),
                make_author('Tânia Beisl', 'Ramos', 'taniaramos@fa.utl.pt', 'FAUTL', 'PT'),
            ]
            fixes += 1

        elif aid == 'sdnne04-024':
            # Fix emails from PDF (DOCONATAL027 - Lins/Brito + coauthors a-e)
            # PDF has complex author list with (a)(b)(c)(d)(e) coauthors
            # Main authors: (1) LINS, Ana Paula; (2) BRITO, Marília
            # Co-authors: (a) CARVALHO, Luiz; (b) BONATES, Mariana; (c) FERRAZ, Rosali
            a['authors'] = [
                make_author('Ana Paula Mota de Bitencourt da Costa', 'Lins', 'anapaulabitencourt@hotmail.com', 'MDU-UFPE', primary_contact=True),
                make_author('Marília', 'Brito', 'brito@exemplo.com', 'UFPE'),
                make_author('Luiz', 'Carvalho', 'carvalho@exemplo.com', None),
                make_author('Mariana', 'Bonates', 'bonates@exemplo.com', None),
                make_author('Rosali', 'Ferraz', 'ferraz@exemplo.com', None),
            ]
            fixes += 1

        elif aid == 'sdnne04-025':
            # Fix title (all caps)
            a['title'] = 'Inserções modernistas na moradia financiada pelos IAPs em Natal (décadas de 1950 e 1960)'
            a['subtitle'] = None
            # Fix emails from PDF (DOCONATAL029 - Lima/Ferreira)
            a['authors'] = [
                make_author('Luiza Maria Medeiros', 'Lima', 'luizamlima@hotmail.com', 'UFRN', primary_contact=True),
                make_author('Angela Lúcia', 'Ferreira', 'alaferreira@hotmail.com', 'PPGAU-UFRN'),
            ]
            fixes += 1

        elif aid == 'sdnne04-026':
            # Fix subtitle (truncated) and emails
            a['subtitle'] = 'um caso de apartamentos paulistanos de interesse social da década de 1950 remanescentes em 2010 — o Conjunto Residencial Santo Antônio'
            a['authors'] = [
                make_author('Aline T.', 'Machado', 'alinetrim@hotmail.com', 'Mackenzie', primary_contact=True),
                make_author('Eunice H. S.', 'Abascal', 'eunice.abascal@mackenzie.com.br', 'Mackenzie'),
            ]
            fixes += 1

        elif aid == 'sdnne04-027':
            # Fix emails from PDF (DOCONATAL031 - Meneses et al.)
            a['authors'] = [
                make_author('Priscila de Oliveira', 'Meneses', 'priscila_meneses@hotmail.com', 'UFPI', primary_contact=True),
                make_author('Rayla Fernanda de Meneses', 'Marques', 'raylafernanda4@hotmail.com', 'UFPI'),
                make_author('Thabata Micaela Matos Frota Lemos', 'Duarte', 'duarte@exemplo.com', 'UFPI'),
                make_author('Willane Soares', 'Oliveira', 'oliveira@exemplo.com', 'UFPI'),
            ]
            fixes += 1

        elif aid == 'sdnne04-028':
            # Fix title (all caps, truncated)
            a['title'] = 'Arquitetura reativa'
            a['subtitle'] = 'energia propulsora de lugares na cidade contemporânea. O caso do Punta Carretas Shopping Center, Montevidéu — UY.'
            fixes += 1

        elif aid == 'sdnne04-030':
            # Fix author names from PDF (DOCONATAL034 - Moreira/Carvalho/Brito)
            a['authors'] = [
                make_author('Amanda Cavalcante', 'Moreira', 'amandacmoreira@hotmail.com', 'UFPI', primary_contact=True),
                make_author('Kelly Felix de', 'Carvalho', 'carvalho@exemplo.com', 'ICF'),
                make_author('Pedro Henrique Tajra Hidd Pearce', 'Brito', 'brito@exemplo.com', 'UFPI'),
            ]
            fixes += 1

        elif aid == 'sdnne04-032':
            # Missing authors and abstract (DOCONATAL036 - Moreira et al.)
            # This PDF has no "RESUMO" marker, uses inline abstract
            a['authors'] = [
                make_author('Fernando Diniz', 'Moreira', 'fmoreira@hotlink.com.br', 'UFPE', primary_contact=True),
                make_author('Mônica', 'Harchambois', 'monicaharchambois@gmail.com', 'Geosistemas'),
                make_author('Ana Maria', 'Bezerra', 'producao.arquitetura@gmail.com', 'UFRN'),
                make_author('Rucélia Cavalcanti da', 'Mata', 'ruana.arq@gmail.com', 'UFRN'),
                make_author('Fernanda Herbster', 'Pinto', 'fernanda.hpinto@gmail.com', 'MDU-UFPE'),
            ]
            a['abstract'] = 'Este artigo procura contribuir para o debate sobre a conservação e a requalificação de grandes edifícios esportivos ao apresentar uma experiência de requalificação de um grande ginásio desportivo com lugar para 15.000 expectadores, o Ginásio de Esportes Geraldo Magalhães (Geraldão) no Recife, projeto de Ícaro de Castro Mello, inaugurado em 1970. O problema residiu na adaptação de um edifício com problemas de conservação, sem tombamento e sem reconhecimento de seus valores pela sociedade, visando adaptá-lo às novas exigências das federações esportivas e dos orgãos públicos e às demandas da municipalidade para modernizar o ginásio a fim de recolocá-lo no circuito de grandes eventos esportivos. O projeto propôs um rearranjo de funções e fluxos no interior do conjunto, privilegiando intervenções mínimas na estrutura física do complexo, e um novo edifício anexo, que contém estacionamento, quadras auxiliares e de aquecimento, bem como espaços para a administração. Na primeira parte, situamos o Geraldão e a obra de Castro Mello em um contexto mais amplo, que inclui a relação entre arquitetura moderna e a prática dos esportes, a utilização do concreto como elemento plástico na arquitetura moderna brasileira, e apresentamos o edifício e a declaração de significância. Na segunda parte, será apresentada uma síntese da pormenorizada análise dos principais problemas de conservação. Por fim, as concepções preliminares e a proposta de intervenção arquitetônica, que deverão ser colocadas em prática a partir da segunda metade de 2012.'
            fixes += 1

        elif aid == 'sdnne04-033':
            # Fix affiliation: Fundaj, not UFPE
            a['authors'][0]['affiliation'] = 'Fundaj'
            fixes += 1

        elif aid == 'sdnne04-034':
            # Fix emails from PDF (DOCONATAL038 - Oliveira/Peres/Gomes/Naslavsky)
            a['title'] = 'Digitalização e Preservação do Patrimônio Iconográfico de Arquitetura'
            a['subtitle'] = 'o caso de Recife'
            a['authors'] = [
                make_author('Patrícia A. S.', 'Oliveira', 'ataidepatricia@gmail.com', 'DAU-UFPE', primary_contact=True),
                make_author('Clara T.', 'Peres', 'clara.ctp@gmail.com', 'DAU-UFPE'),
                make_author('Camilla', 'Gomes', 'gomes@exemplo.com', 'DAU-UFPE'),
                make_author('Guilah', 'Naslavsky', 'naslavsky@exemplo.com', 'DAU-UFPE'),
            ]
            fixes += 1

        elif aid == 'sdnne04-035':
            # Fix emails from PDF (DOCONATAL039 - Pachalski/Gonsales)
            a['authors'] = [
                make_author('Glauco Assumpção', 'Pachalski', 'gpachalski@yahoo.com.br', 'UFPel', primary_contact=True),
                make_author('Célia', 'Gonsales', 'celia.gonsales@gmail.com', 'UFPel'),
            ]
            fixes += 1

        elif aid == 'sdnne04-036':
            # Fix title and emails (DOCONATAL040 - Paiva/Diógenes)
            a['title'] = 'Caminhos da Arquitetura Moderna em Fortaleza'
            a['subtitle'] = 'a contribuição do professor arquiteto José Neudson Braga.'
            a['authors'] = [
                make_author('Ricardo Alexandre', 'Paiva', 'paiva_ricardo@yahoo.com.br', 'DAU-UFC', primary_contact=True),
                make_author('Beatriz Helena N.', 'Diógenes', 'bhdiogenes@yahoo.com.br', 'DAU-UFC'),
            ]
            fixes += 1

        elif aid == 'sdnne04-038':
            # Fix emails from PDF (DOCONATAL042 - Sá Carneiro/Silva/Silva)
            a['authors'] = [
                make_author('Ana Rita', 'Sá Carneiro', 'anaritacarneiro@hotmail.com', 'DAU-UFPE', primary_contact=True),
                make_author('Aline de Figueirôa', 'Silva', 'alinefigueiroa@yahoo.com.br', 'UFPE'),
                make_author('Joelmir Marques', 'Silva', 'joelmir_marques@hotmail.com', 'MDU-UFPE'),
            ]
            fixes += 1

        elif aid == 'sdnne04-039':
            # Missing authors and abstract (DOCONATAL043 - Silva/Silva)
            # This PDF has RESUMO: (with colon) which wasn't matched
            a['authors'] = [
                make_author('Andreza Cruz Alves da', 'Silva', 'andrezacruz_123@hotmail.com', 'UFRN', primary_contact=True),
                make_author('Taís Alvino da', 'Silva', 'taisalvino@gmail.com', 'UFRN'),
            ]
            a['abstract'] = 'Com o tema das expressões da arquitetura modernista, privilegiando edifícios religiosos potiguares, este trabalho propõe uma análise comparativa entre a Catedral Metropolitana de Natal, de autoria do Arquiteto Marconi Grevi, e a Capela Ecumênica da UFRN, do Arquiteto João Maurício Fernandes de Miranda. A escolha dessas duas edificações se deu por um recorte temporal, especificamente a década de 1970. E também pela dissonância visual existente entre as duas edificações, o que geraria uma discussão interessante, tendo foco direcionador o Movimento Moderno. Apesar de possuírem a mesma função, detém porte e focos diferentes, o que torna o estudo ainda mais interessante. Sendo assim, para a leitura morfológica da arquitetura das edificações foram eleitos critérios, os quais são: impacto da obra arquitetônica, forma, organização do espaço, sistema estrutural, transparência x opacidade e materiais de revestimento. Esses critérios estão associados à influência que o Movimento Moderno exerceu sobre os edifícios religiosos.'
            a['section'] = 'A arquitetura moderna como projeto'
            fixes += 1

        elif aid == 'sdnne04-041':
            # Fix title: "E o moderno ficou chato, mas não se tornou eterno1" -> remove footnote marker
            a['title'] = 'E o moderno ficou chato, mas não se tornou eterno'
            fixes += 1

        elif aid == 'sdnne04-042':
            # Fix author 3: ", Terezinha Monteiro Oliveira" -> proper parsing
            # PDF has: OLIVEIRA,, Terezinha Monteiro (double comma)
            a['authors'] = [
                make_author('Natália Miranda', 'Vieira', 'natvieira01@hotmail.com', 'PPGAU-UFRN', primary_contact=True),
                make_author('Sonia', 'Marques', 'marquessonia@hotmail.com', 'UFPB'),
                make_author('Terezinha Monteiro', 'Oliveira', 'terezinha_mo@yahoo.com.br', 'UNIPÊ'),
            ]
            fixes += 1

        elif aid == 'sdnne04-043':
            # Missing eixo. PDF has no explicit eixo marker, but implied from content
            a['section'] = 'Narrativas historiográficas'
            # Fix author: add second author (SILVA, Paulo Raniery Costa da)
            a['authors'] = [
                make_author('José Clewton do', 'Nascimento', 'jclewton@hotmail.com', 'DARQ-UFRN', primary_contact=True),
                make_author('Paulo Raniery Costa da', 'Silva', 'paulorani@hotmail.com', 'DARQ-UFRN'),
            ]
            # RESUMO has colon: "RESUMO:" - extract from text
            a['abstract'] = 'O artigo discorre sobre o processo de transformação do estádio João Cláudio de Vasconcelos Machado — o Machadão — marco da arquitetura modernista natalense, em elemento de obsolescência, tendo em vista a sua não adequação aos padrões atuais exigidos pela FIFA, como uma das arenas de esporte que receberão o evento Copa do Mundo de Futebol de 2014. Nossa análise é realizada em duas etapas, que se complementam: primeiramente, buscamos relacionar a idealização e construção do edifício ao contexto político e social da época, em que o Estado passa a financiar a construção de vários estádios, na perspectiva de utilização do esporte como canal de aproximação com o povo, em busca da legitimação de suas ações. Analisamos o edifício enquanto objeto arquitetônico — revelador de uma linguagem modernista comum aos estádios à época, e cuja forma é resultante de uma relação entre público e prática futebolística bastante particular, bem como sob o ponto de vista urbano, através do qual constatamos que o edifício torna-se uma referência na paisagem natalense. Em seguida, analisamos o processo que desencadeará na opção pela demolição do edifício, tendo em vista a preparação da cidade para sediar o evento Copa do Mundo de Futebol 2014.'
            # Fix title
            a['title'] = 'De poema a "poeira"'
            a['subtitle'] = 'Estádio Machadão, Natal/RN — a decretação da obsolescência de uma referência modernista.'
            fixes += 1

        elif aid == 'sdnne04-044':
            # Missing eixo
            a['section'] = 'Narrativas historiográficas'
            fixes += 1

    # ── Fix sections list ──────────────────────────────────────

    data['issue']['sections'] = [
        {'title': 'A arquitetura moderna como projeto', 'abbrev': 'ET1-sdnne04'},
        {'title': 'Narrativas historiográficas', 'abbrev': 'ET2-sdnne04'},
        {'title': 'Experiências de conservação e transformação', 'abbrev': 'ET3-sdnne04'},
    ]

    # ── Save ────────────────────────────────────────────────────

    with open(YAML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper,
                  default_flow_style=False, allow_unicode=True,
                  width=10000, sort_keys=False)

    print(f"Correções aplicadas: {fixes}")
    print(f"YAML salvo em: {YAML_PATH}")

    # Verify
    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        data2 = yaml.safe_load(f)

    articles2 = data2['articles']
    issues_remaining = 0
    for a in articles2:
        section = a.get('section', '')
        if section in ('Sem eixo', '') or 'Narrrativas' in section or 'arrativas' in section or 'mático' in section:
            print(f"  STILL BAD SECTION: {a['id']}: {section}")
            issues_remaining += 1
        for au in a.get('authors', []):
            gn = au.get('givenname', '')
            if gn.startswith(',') or gn.startswith('.'):
                print(f"  STILL BAD GIVENNAME: {a['id']}: {gn} {au.get('familyname', '')}")
                issues_remaining += 1
        if not a.get('authors'):
            print(f"  STILL NO AUTHORS: {a['id']}")
            issues_remaining += 1

    print(f"\nIssues remaining: {issues_remaining}")


if __name__ == '__main__':
    fix_yaml()
