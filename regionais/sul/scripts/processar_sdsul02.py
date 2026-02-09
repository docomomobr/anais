#!/usr/bin/env python3
"""
Processa o 2º Seminário Docomomo Sul (Porto Alegre, 2008).
Extrai metadados dos PDFs e gera o YAML consolidado + copia PDFs renomeados.
"""

import yaml
import subprocess
import re
import shutil
import os

# ============================================================
# OrderedDumper (mantém ordem dos campos)
# ============================================================

class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

OrderedDumper.add_representer(dict, dict_representer)

# Representar strings multiline como blocos
def str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

OrderedDumper.add_representer(str, str_representer)

# ============================================================
# Diretórios
# ============================================================

BASE_DIR = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul'
PDF_DIR = os.path.join(BASE_DIR, 'sdsul02', 'pdfs')
YAML_PATH = os.path.join(BASE_DIR, 'sdsul02.yaml')

# ============================================================
# Funções auxiliares
# ============================================================

def pdftotext(filepath, last_page=None):
    """Extrai texto de PDF usando pdftotext."""
    cmd = ['pdftotext']
    if last_page:
        cmd += ['-l', str(last_page)]
    cmd += [filepath, '-']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout
    except Exception:
        return ''

def pdfinfo_pages(filepath):
    """Retorna número de páginas do PDF."""
    try:
        result = subprocess.run(['pdfinfo', filepath], capture_output=True, text=True, timeout=10)
        for line in result.stdout.split('\n'):
            if line.startswith('Pages:'):
                return int(line.split(':')[1].strip())
    except Exception:
        pass
    return 0

def split_name(full_name):
    """Separa nome em givenname/familyname seguindo convenção brasileira.
    Partículas (de, da, do, dos, das, e) ficam no givenname.
    """
    parts = full_name.strip().split()
    if len(parts) <= 1:
        return full_name.strip(), ''

    particles = {'de', 'da', 'do', 'dos', 'das', 'e', 'del', 'di', 'von', 'van', "d'", "d'"}

    # Encontrar o último sobrenome (não-partícula)
    familyname = parts[-1]
    givenname = ' '.join(parts[:-1])

    return givenname, familyname

def extract_keywords(text, label):
    """Extrai palavras-chave de texto usando regex."""
    # Tenta vários padrões
    patterns = [
        rf'{label}\s*[:/]\s*(.+?)(?:\n\n|\n[A-Z]|\nAbstract|\nRESUMO|\nKey)',
        rf'{label}\s*[:/]?\s*(.+?)(?:\.\s*\n|\n\n)',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            raw = m.group(1).strip()
            # Limpar
            raw = re.sub(r'\s+', ' ', raw)
            # Separadores: ; ou , ou –
            if ';' in raw:
                kws = [k.strip().rstrip('.') for k in raw.split(';')]
            elif ',' in raw:
                kws = [k.strip().rstrip('.') for k in raw.split(',')]
            elif ' – ' in raw:
                kws = [k.strip().rstrip('.') for k in raw.split(' – ')]
            elif ' - ' in raw:
                kws = [k.strip().rstrip('.') for k in raw.split(' - ')]
            else:
                kws = [raw.rstrip('.')]
            return [k for k in kws if k and len(k) > 1]
    return []

def extract_references(full_text):
    """Extrai referências bibliográficas do texto completo."""
    # Buscar seção de referências
    patterns = [
        r'(?:REFERÊNCIAS|Referências|REFERENCIAS|Referencias|BIBLIOGRAPHY|Bibliography|REFER[EÊ]NCIAS BIBLIOGR[AÁ]FICAS|Referências bibliográficas|NOTAS E REFER[EÊ]NCIAS|BIBLIOGRAFIA)\s*\n(.*)',
    ]
    refs_text = None
    for pattern in patterns:
        m = re.search(pattern, full_text, re.DOTALL)
        if m:
            refs_text = m.group(1).strip()
            break

    if not refs_text:
        return []

    # Parsear referências individuais
    lines = refs_text.split('\n')
    refs = []
    current = ''
    for line in lines:
        line = line.strip()
        if not line:
            if current:
                refs.append(current.strip())
                current = ''
            continue
        # Nova referência começa com autor em MAIÚSCULAS ou número
        if re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s,]+[.,]', line) or re.match(r'^\d+[.\)]\s', line):
            if current:
                refs.append(current.strip())
            current = line
        else:
            current += ' ' + line

    if current:
        refs.append(current.strip())

    # Limpar
    refs = [r for r in refs if len(r) > 20 and not r.startswith('Imprimir') and not r.startswith('Fechar')]
    return refs[:50]  # Limitar a 50

# ============================================================
# Dados dos artigos (extraídos manualmente dos PDFs)
# ============================================================

ARTICLES_DATA = [
    {
        'num': 1,
        'title': 'A ponte',
        'authors': [('Andrey Rosenthal', 'Schlee')],
        'affiliations': ['UnB'],
        'emails': ['andreysc@terra.com.br'],
        'locale': 'pt-BR',
        'keywords': ['Ponte Internacional Mauá', 'Rudolf Ahrons', 'concreto armado'],
        'keywords_en': ['Maua International Bridge', 'Rudolf Ahrons', 'Reinforced Concrete'],
    },
    {
        'num': 2,
        'title': 'A obra do escritório de Jacques Pilon no centro de São Paulo',
        'authors': [('Tiago Seneme', 'Franco')],
        'affiliations': ['UPM'],
        'emails': ['tiagofranco82@gmail.com'],
        'locale': 'pt-BR',
        'keywords': ['Jacques Pilon', 'verticalização', 'centro de São Paulo'],
        'keywords_en': ['Jacques Pilon', 'verticalization', 'São Paulo Downtown'],
    },
    {
        'num': 3,
        'title': 'Alcides Rocha Miranda',
        'subtitle': 'Igreja em Nova Friburgo',
        'authors': [('Liege Alvares', 'Sieben')],
        'affiliations': ['PROPAR-UFRGS'],
        'emails': [''],
        'locale': 'pt-BR',
        'keywords': ['Alcides Rocha Miranda', 'concreto aparente'],
        'keywords_en': ['Alcides Rocha Miranda', 'apparent concrete'],
    },
    {
        'num': 4,
        'title': 'A construção da forma livre',
        'subtitle': 'visões opostas sobre o uso do concreto armado na Arquitetura Contemporânea no Brasil',
        'authors': [('Renato Luiz Sobral', 'Anelli')],
        'affiliations': ['EESC-USP'],
        'emails': ['reanelli@sc.usp.br'],
        'locale': 'pt-BR',
        'keywords': [],
        'keywords_en': [],
    },
    {
        'num': 5,
        'title': 'Reidy',
        'subtitle': 'dois projetos, dois países e um princípio',
        'authors': [('Ana Elisa Moraes', 'Souto'), ('Alex Carvalho', 'Brino')],
        'affiliations': ['PROPAR-UFRGS', 'PROPAR-UFRGS'],
        'emails': ['anesouto@ig.com.br', 'alexbrino@yahoo.com.br'],
        'locale': 'pt-BR',
        'keywords': ['projeto arquitetônico', 'sistematicidade', 'concreto', 'Affonso Reidy'],
        'keywords_en': [],
    },
    {
        'num': 6,
        'title': 'O suporte na arquitetura de Rino Levi',
        'subtitle': 'da grelha tridimensional ao dom-ino',
        'authors': [('Celia Castro', 'Gonsales')],
        'affiliations': ['UFPel'],
        'emails': ['celia.gonsales@gmail.com'],
        'locale': 'pt-BR',
        'keywords': ['Rino Levi', 'estrutura'],
        'keywords_en': ['Rino Levi', 'structure'],
    },
    {
        'num': 7,
        'title': 'Da utopia ao concreto',
        'subtitle': 'os prédios habitacionais lineares e curvilíneos de Affonso Reidy como experiência tipológica e construtiva',
        'authors': [('Gilberto Flores', 'Cabral')],
        'affiliations': ['FA-UFRGS'],
        'emails': ['cabweb@terra.com.br'],
        'locale': 'pt-BR',
        'keywords': [],
        'keywords_en': [],
    },
    {
        'num': 8,
        'title': 'Arquitetura Moderna em Porto Alegre',
        'subtitle': 'considerações sobre a flexibilidade em planta e o uso de grelha de concreto em fachadas de edifícios residenciais da década de 50',
        'authors': [('Cristiane Wainberg', 'Finkelstein')],
        'affiliations': ['PROPAR-UFRGS'],
        'emails': ['cris.finkelstein@terra.com.br'],
        'locale': 'pt-BR',
        'keywords': ['brise-soleils ou grelhas de concreto', 'Arquitetura Moderna', 'flexibilidade'],
        'keywords_en': ['brise-soleils', 'modern architecture', 'flexibility'],
    },
    {
        'num': 9,
        'title': 'Viver nas alturas',
        'authors': [('Clarissa Martins de Lucena Santafé', 'Aguiar')],
        'affiliations': ['PROPAR-UFRGS'],
        'emails': ['claguiar@gmail.com'],
        'locale': 'pt-BR',
        'keywords': ['cobertura', 'Arquitetura Moderna', 'diretrizes urbanísticas'],
        'keywords_en': ['rooftop', 'modern architecture', 'urban guidelines'],
    },
    {
        'num': 10,
        'title': 'Banco de Londres e América do Sul',
        'subtitle': 'detalhes construtivos e solução estrutural',
        'authors': [('Cassandra Salton', 'Coradin')],
        'affiliations': ['UFRGS'],
        'emails': ['cassandracoradin@terra.com.br'],
        'locale': 'pt-BR',
        'keywords': [],
        'keywords_en': [],
    },
    {
        'num': 11,
        'title': 'Emílio Henrique Baumgart',
        'subtitle': 'o pai do concreto armado no Brasil',
        'authors': [('Juliano Caldas de', 'Vasconcellos')],
        'affiliations': ['PROPAR-UFRGS'],
        'emails': ['jcvasc@feevale.br'],
        'locale': 'pt-BR',
        'keywords': ['concreto', 'engenharia', 'Baumgart'],
        'keywords_en': ['concrete', 'engineering', 'Baumgart'],
    },
    {
        'num': 12,
        'title': 'Brutalismo no paralelo 33',
        'subtitle': 'Unidad Diego Portales, Santiago - Chile',
        'authors': [('Maribel Aliaga', 'Fuentes')],
        'affiliations': ['PROPAR-UFRGS'],
        'emails': ['marialiaga@gmail.com'],
        'locale': 'pt-BR',
        'keywords': [],
        'keywords_en': [],
    },
    {
        'num': 13,
        'title': 'Ecletismo, ferro e concreto',
        'subtitle': 'um arquivo-belvedere em Porto Alegre',
        'authors': [('Cláudio Calovi', 'Pereira'), ('Samantha Sonza', 'Diefenbach')],
        'affiliations': ['UFRGS', 'PROPAR-UFRGS'],
        'emails': ['claudio.calovi@ufrgs.br', 'samantha.diefenbach@gmail.com'],
        'locale': 'pt-BR',
        'keywords': ['Arquitetura Eclética', 'Arquitetura de Porto Alegre', 'Affonso Hebert'],
        'keywords_en': [],
    },
    {
        'num': 14,
        'title': 'Matéria bruta',
        'subtitle': 'Clorindo Testa e o Centro Cívico de Santa Rosa, La Pampa, 1955-1963',
        'authors': [('Cláudia Piantá Costa', 'Cabral')],
        'affiliations': ['UFRGS'],
        'emails': ['cabralfendt@terra.com.br'],
        'locale': 'pt-BR',
        'keywords': ['Clorindo Testa', 'Centro Cívico', 'concreto armado'],
        'keywords_en': ['Clorindo Testa', 'Civic Center', 'reinforced concrete'],
    },
    {
        'num': 15,
        'title': 'Experiências em concreto armado na África Portuguesa',
        'subtitle': 'influências do Brasil',
        'authors': [('Ana Cristina Fernandes Vaz', 'Milheiro')],
        'affiliations': ['FAUTL'],
        'emails': ['avmilheiro@gmail.com'],
        'locale': 'pt-BR',
        'keywords': [],
        'keywords_en': [],
    },
    {
        'num': 16,
        'title': 'A miragem da industrialização',
        'subtitle': 'abrindo a mata virgem a facão: alguns casos do brutalismo paulista',
        'authors': [('Ruth Verde', 'Zein')],
        'affiliations': ['UPM'],
        'emails': [''],
        'locale': 'pt-BR',
        'keywords': [],
        'keywords_en': [],
    },
    {
        'num': 17,
        'title': 'O Centro Administrativo do Estado do Rio Grande do Sul',
        'subtitle': 'curva de concreto marcando a paisagem',
        'authors': [('Renato Holmer', 'Fiore')],
        'affiliations': ['UFRGS'],
        'emails': ['rhfiore@terra.com.br'],
        'locale': 'pt-BR',
        'keywords': ['Centro Administrativo do Estado do Rio Grande do Sul', 'concreto armado', 'significado na paisagem'],
        'keywords_en': ['Administrative Centre of the State of Rio Grande do Sul', 'reinforced concrete', 'meaning in the townscape'],
    },
    {
        'num': 18,
        'title': 'Máquinas de Vender Máquinas',
        'subtitle': 'formas aerodinâmicas em revendas de automóveis e oficinas mecânicas em Caxias do Sul',
        'authors': [('Ana Elísia da', 'Costa')],
        'affiliations': ['UCS'],
        'emails': ['ana_elisia_costa@hotmail.com'],
        'locale': 'pt-BR',
        'keywords': ['Arquitetura Moderna', 'concessionárias', 'Caxias do Sul'],
        'keywords_en': ['Modern Architecture', 'car dealerships', 'Caxias do Sul'],
    },
    {
        'num': 19,
        'title': 'A casa unifamiliar em Florianópolis',
        'subtitle': 'um modo de ser moderno',
        'authors': [('Josicler Orbem', 'Alberton')],
        'affiliations': ['UNIVALI'],
        'emails': ['arquiteta.josicler@yahoo.com.br'],
        'locale': 'pt-BR',
        'keywords': ['Arquitetura Moderna', 'inventário', 'projeto arquitetônico residencial'],
        'keywords_en': ['Modern Architecture', 'Inventory', 'Architecture house plan'],
    },
    {
        'num': 20,
        'title': 'Composição de planos no edifício Annes Dias nº 154',
        'authors': [('Felipe de Souza L.', 'Pacheco')],
        'affiliations': ['PROPAR-UFRGS'],
        'emails': ['pacheco.felipe@terra.com.br'],
        'locale': 'pt-BR',
        'keywords': ['Arquitetura', 'Moderna', 'planos'],
        'keywords_en': [],
    },
    {
        'num': 21,
        'title': 'O concreto na pré-fabricação',
        'subtitle': 'a construção da Universidade de Brasília',
        'authors': [('Klaus Chaves', 'Alberto')],
        'affiliations': ['CES-JF'],
        'emails': ['klauschavesalberto@gmail.com'],
        'locale': 'pt-BR',
        'keywords': ['UnB', 'pré-fabricação', 'Oscar Niemeyer'],
        'keywords_en': [],
    },
    {
        'num': 22,
        'title': 'A caixa de concreto para a casa do aço',
        'subtitle': 'Escritório-Parque Usiminas',
        'authors': [('Álvaro Pompeiano de Magalhães', 'Drummond')],
        'affiliations': ['EA-UFMG'],
        'emails': ['alvarodru@hotmail.com'],
        'locale': 'pt-BR',
        'keywords': ['concreto armado', 'expressão plástica'],
        'keywords_en': [],
    },
    {
        'num': 23,
        'title': 'Paisagens Desoladas',
        'subtitle': 'Quatro Máscaras de Concreto em Deriva',
        'authors': [("José Artur D'Aló", 'Frota'), ('Eline Maria Moura Pereira', 'Caixeta'), ('Christine Ramos', 'Mahler')],
        'affiliations': ['FAV-UFG', 'UCG', 'FAV-UFG'],
        'emails': ['arturfav@yahoo.com.br', '', ''],
        'locale': 'pt-BR',
        'keywords': ['cultura arquitetônica', 'espaço urbano', 'imaginário urbano'],
        'keywords_en': ['architectural culture', 'urban space', 'urban imaginary'],
    },
    {
        'num': 24,
        'title': 'O concreto na linguagem de Oscar Niemeyer',
        'authors': [('Rosirene', 'Mayer'), ('Benamy', 'Turkienicz')],
        'affiliations': ['PROPAR-UFRGS', 'PROPAR-UFRGS'],
        'emails': ['mayer@ufrgs.br', 'benamy@portoweb.com.br'],
        'locale': 'pt-BR',
        'keywords': ['concreto', 'linguagem', 'gramática'],
        'keywords_en': ['Niemeyer', 'grammar', 'language'],
    },
    {
        'num': 25,
        'title': 'Estrutura e construção do Ministério da Educação e Saúde Pública',
        'authors': [('Juliano Caldas de', 'Vasconcellos')],
        'affiliations': ['PROPAR-UFRGS'],
        'emails': ['jcvasc@feevale.br'],
        'locale': 'pt-BR',
        'keywords': ['concreto', 'Ministério', 'estrutura'],
        'keywords_en': ['concrete', 'Ministry', 'structure'],
    },
    {
        'num': 26,
        'title': 'Niemeyer e Artigas',
        'subtitle': 'aproximações e divergências na busca da expressão formal da estrutura',
        'authors': [('Carlos Fernando Silva', 'Bahima'), ('Alex Carvalho', 'Brino')],
        'affiliations': ['UNISINOS', 'UNIVATES'],
        'emails': ['cfbahima@unisinos.br', 'alexbrino@yahoo.com.br'],
        'locale': 'pt-BR',
        'keywords': [],
        'keywords_en': [],
    },
    {
        'num': 27,
        'title': 'O Edifício Teruszkin',
        'authors': [('Andréa Soler', 'Machado')],
        'affiliations': ['PROPAR-UFRGS'],
        'emails': ['asolerm@terra.com.br'],
        'locale': 'pt-BR',
        'keywords': ['edifício', 'moderno', 'concreto armado'],
        'keywords_en': ['building', 'modern', 'steel concrete'],
    },
    {
        'num': 28,
        'title': 'Da Refinaria à Secretaria',
        'subtitle': 'racionalismo estrutural, socialismo nacional e modernismo regional em obras públicas de Fayet, Araújo & Moojen - 1962 a 1970',
        'authors': [('Sergio Moacir', 'Marques')],
        'affiliations': ['FA-UFRGS'],
        'emails': ['docomomors@uniritter.edu.br'],
        'locale': 'pt-BR',
        'keywords': ['Arquitetura Moderna', 'Arquitetura no Sul'],
        'keywords_en': ['Modern Architecture', 'South Architecture'],
    },
    {
        'num': 29,
        'title': 'Pilotis, pilar, pilastra',
        'subtitle': 'variações brasileiras',
        'authors': [('Rogério de Castro', 'Oliveira')],
        'affiliations': ['PROPAR-UFRGS'],
        'emails': ['rco@ufrgs.br'],
        'locale': 'pt-BR',
        'keywords': ['pilotis', 'modernismo', 'composição arquitetônica'],
        'keywords_en': ['pilotis', 'modernisme', 'composition architecturale'],
    },
    {
        'num': 30,
        'title': 'Tecnologia das construções em cascas',
        'authors': [('Célia Regina Moretti', 'Meirelles'), ('Ricardo Hernán', 'Medrano'), ('Henrique', 'Dinis')],
        'affiliations': ['UPM', 'UPM', 'UPM'],
        'emails': ['cerellesm@gmail.com', '', ''],
        'locale': 'pt-BR',
        'keywords': ['coberturas em casca', 'estruturas em cascas', 'cascas de concreto armado'],
        'keywords_en': ["shells roofs", 'shell structure', 'reinforced concrete shell'],
    },
    {
        'num': 31,
        'title': 'Arquitetura Moderna, Patrimônio Histórico e concreto armado',
        'authors': [('Marcos José', 'Carrilho')],
        'affiliations': ['FAU-Mackenzie'],
        'emails': ['marcos.carrilho@gmail.com'],
        'locale': 'pt-BR',
        'keywords': ['Arquitetura Moderna', 'patrimônio histórico', 'concreto armado'],
        'keywords_en': [],
    },
    {
        'num': 32,
        'title': 'Opus caementicius',
        'subtitle': 'da insuspeita sutileza das pedras brutas',
        'authors': [('Cecilia Rodrigues dos', 'Santos')],
        'affiliations': ['FAU-Mackenzie'],
        'emails': ['altoalegre@uol.com.br'],
        'locale': 'pt-BR',
        'keywords': ['brutalidade e verdade do concreto', 'estetização do concreto bruto'],
        'keywords_en': [],
    },
    {
        'num': 33,
        'title': 'Belo e suave, bruto e sublime',
        'subtitle': 'notas sobre a plasticidade do concreto armado brasileiro',
        'authors': [('Carlos Eduardo', 'Comas')],
        'affiliations': ['PROPAR-UFRGS'],
        'emails': [''],
        'locale': 'pt-BR',
        'keywords': [],
        'keywords_en': [],
    },
    {
        'num': 34,
        'title': 'Vanguarda com gelo',
        'subtitle': 'concreto aparente e gosto eclético',
        'authors': [('Marta', 'Peixoto')],
        'affiliations': ['UFRGS'],
        'emails': [''],
        'locale': 'pt-BR',
        'keywords': [],
        'keywords_en': [],
    },
    {
        'num': 35,
        'title': 'Hormigón, Industrialización, Vivienda',
        'subtitle': 'Sert y la Ciudad de los Motores',
        'authors': [('Carlos Alberto Ferreira', 'Martins')],
        'affiliations': ['IAU-USP'],
        'emails': [''],
        'locale': 'es',
        'keywords': [],
        'keywords_en': [],
    },
]

# Page counts (from pdfinfo)
PAGE_COUNTS = {
    1: 14, 2: 18, 3: 11, 4: 24, 5: 19, 6: 19, 7: 22, 8: 17, 9: 19, 10: 18,
    11: 12, 12: 22, 13: 18, 14: 22, 15: 31, 16: 28, 17: 16, 18: 18, 19: 18, 20: 12,
    21: 28, 22: 14, 23: 18, 24: 22, 25: 19, 26: 17, 27: 19, 28: 30, 29: 9, 30: 9,
    31: 17, 32: 12, 33: 4, 34: 1, 35: 12,
}

# ============================================================
# Extrair resumos dos PDFs
# ============================================================

def extract_abstract(text, label='Resumo'):
    """Extrai resumo do texto extraído do PDF."""
    # Padrões para encontrar o resumo
    patterns = [
        rf'{label}\s*:?\s*\n(.*?)(?:\n\s*(?:Abstract|ABSTRACT|Palavras|Key|RESUMEE|Resumen|Résumé|THE CONCRETE))',
        rf'{label}\s*:\s*(.*?)(?:\n\s*(?:Abstract|ABSTRACT|Palavras|Key|THE CONCRETE))',
        rf'{label}\s*:?\s*\n(.*?)(?:\n\n\n)',
        rf'{label}\s*\n(.*?)(?:\n\s*(?:Abstract|ABSTRACT|Palavras|Key))',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if m:
            abstract = m.group(1).strip()
            # Limpar
            abstract = re.sub(r'\s+', ' ', abstract)
            abstract = abstract.replace('Imprimir', '').replace('Fechar', '').strip()
            if len(abstract) > 50:
                return abstract
    return None

def extract_abstract_en(text):
    """Extrai abstract em inglês."""
    patterns = [
        r'Abstract\s*:?\s*\n(.*?)(?:\n\s*(?:Palavras|Key|Mots|Imprimir|$))',
        r'ABSTRACT\s*:?\s*\n(.*?)(?:\n\s*(?:Palavras|Key|Keywords|Mots|Imprimir|$))',
        r'Abstract\s*\n(.*?)(?:\n\n\n)',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if m:
            abstract = m.group(1).strip()
            abstract = re.sub(r'\s+', ' ', abstract)
            abstract = abstract.replace('Imprimir', '').replace('Fechar', '').strip()
            if len(abstract) > 50:
                return abstract
    return None

# ============================================================
# Processar
# ============================================================

def process():
    articles = []

    for art_data in ARTICLES_DATA:
        num = art_data['num']
        pdf_name = f'{num:03d}.pdf'
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        new_pdf_name = f'sdsul02-{num:03d}.pdf'

        print(f'Processando {pdf_name} -> {new_pdf_name}...')

        # Extrair texto das primeiras 3 páginas para metadados
        text_first = pdftotext(pdf_path, last_page=3)

        # Extrair texto completo para referências
        text_full = pdftotext(pdf_path)

        # Extrair resumo
        abstract = extract_abstract(text_first) or extract_abstract(text_first, 'RESUMO')
        abstract_en = extract_abstract_en(text_first)

        # Extrair referências
        refs = extract_references(text_full)

        # Montar autores
        authors = []
        for i, (gn, fn) in enumerate(art_data['authors']):
            author = {
                'givenname': gn,
                'familyname': fn,
                'affiliation': art_data['affiliations'][i] if i < len(art_data['affiliations']) else '',
                'email': art_data['emails'][i] if i < len(art_data['emails']) and art_data['emails'][i] else f'{fn.lower().replace(" ", "")}@exemplo.com',
                'primary_contact': i == 0,
            }
            authors.append(author)

        # Montar artigo
        article = {
            'id': f'sdsul02-{num:03d}',
            'title': art_data['title'],
        }

        if art_data.get('subtitle'):
            article['subtitle'] = art_data['subtitle']

        article['authors'] = authors
        article['section'] = 'Artigos'
        article['locale'] = art_data['locale']
        article['file'] = new_pdf_name
        article['file_original'] = pdf_name
        article['pages_count'] = PAGE_COUNTS.get(num, 0)

        if abstract:
            article['abstract'] = abstract
        else:
            article['abstract'] = None

        if abstract_en:
            article['abstract_en'] = abstract_en
        else:
            article['abstract_en'] = None

        article['keywords'] = art_data.get('keywords', [])
        article['keywords_en'] = art_data.get('keywords_en', [])

        if refs:
            article['references'] = refs

        articles.append(article)

        # Copiar PDF renomeado
        dest_pdf = os.path.join(PDF_DIR, new_pdf_name)
        if not os.path.exists(dest_pdf):
            shutil.copy2(pdf_path, dest_pdf)
            print(f'  Copiado -> {new_pdf_name}')
        else:
            print(f'  {new_pdf_name} já existe')

    # ============================================================
    # Montar YAML
    # ============================================================

    data = {
        'issue': {
            'slug': 'sdsul02',
            'title': '2º Seminário Docomomo Sul, Porto Alegre, 2008',
            'subtitle': 'Plasticidade e industrialização na arquitetura do cone sul americano, 1930/70',
            'description': 'COMAS, Carlos Eduardo; MAHFUZ, Edson; CATTANI, Airton (org.). Anais do II Seminário do.co.mo.mo_sul, Plasticidade e industrialização na arquitetura do cone sul americano 1930/70, Porto Alegre, 25-27 ago. 2008 [recurso eletrônico]. Porto Alegre: PROPAR/UFRGS, 2008. 1 CD-ROM. ISBN 978-85-60188-09-3.',
            'year': 2008,
            'volume': 1,
            'number': 2,
            'date_published': '2008-08-25',
            'isbn': '978-85-60188-09-3',
            'publisher': 'PROPAR/UFRGS',
            'editors': [
                'Carlos Eduardo Comas',
                'Edson Mahfuz',
                'Airton Cattani',
            ],
            'source': 'https://www.ufrgs.br/propar/anais-do-2o-seminario-docomomo-sul/',
        },
        'articles': articles,
    }

    with open(YAML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, Dumper=OrderedDumper, width=10000, sort_keys=False, allow_unicode=True, default_flow_style=False)

    print(f'\n=== YAML salvo em {YAML_PATH} ===')
    print(f'Total de artigos: {len(articles)}')

    # Estatísticas
    with_abstract = sum(1 for a in articles if a.get('abstract'))
    with_abstract_en = sum(1 for a in articles if a.get('abstract_en'))
    with_keywords = sum(1 for a in articles if a.get('keywords'))
    with_refs = sum(1 for a in articles if a.get('references'))

    print(f'Com resumo: {with_abstract}/{len(articles)}')
    print(f'Com abstract_en: {with_abstract_en}/{len(articles)}')
    print(f'Com keywords: {with_keywords}/{len(articles)}')
    print(f'Com referências: {with_refs}/{len(articles)}')

if __name__ == '__main__':
    process()
