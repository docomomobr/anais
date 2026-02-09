#!/usr/bin/env python3
"""
Constroi o YAML do sdnne02 (2o Seminario Docomomo Norte/Nordeste, Salvador, 2008)
a partir dos 33 PDFs unicos no diretorio pdfs/.
"""

import os
import re
import subprocess
import shutil
import yaml
import unicodedata
from collections import OrderedDict

BASE_DIR = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/nne/sdnne02'
PDF_DIR = os.path.join(BASE_DIR, 'pdfs')
YAML_PATH = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/nne/sdnne02.yaml'
SEMINARIO = 'sdnne02'
SKIP_FILES = {'AF_Alcília Afonso1.pdf'}


class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

def str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

OrderedDumper.add_representer(OrderedDict, dict_representer)
OrderedDumper.add_representer(dict, dict_representer)
OrderedDumper.add_representer(str, str_representer)


def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout.strip()

def get_page_count(pdf_path):
    try:
        output = run_cmd(['pdfinfo', pdf_path])
        for line in output.split('\n'):
            if line.startswith('Pages:'):
                return int(line.split(':')[1].strip())
    except Exception:
        pass
    return None

def get_text(pdf_path, first_page_only=False):
    try:
        cmd = ['pdftotext']
        if first_page_only:
            cmd.extend(['-l', '1'])
        cmd.extend([pdf_path, '-'])
        return run_cmd(cmd)
    except Exception:
        return ''

def normalize_for_match(s):
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def is_bio_line(line):
    """Check if line is a bio/affiliation line (starts with bio indicator)."""
    stripped = line.strip()
    bio_start_patterns = [
        r'^Arq(?:uiteto|uiteta|uitetos|uitetas)\b',
        r'^Professor(?:a|es|as)?\b',
        r'^Doutor(?:a|ando|anda)?\b',
        r'^Mestr(?:e|ando|anda)\b',
        r'^Graduand[oa]\b',
        r'^Estudante\b',
        r'^T[eé]cnic[oa]\b',
        r'^P[oó]s-[Dd]outor',
        r'^Pesquisador[ae]?\b',
        r'^Bolsista\b',
        r'^Especialista\b',
        r'^Faculdade de\b',
    ]
    for pat in bio_start_patterns:
        if re.match(pat, stripped, re.IGNORECASE):
            return True
    return False


def is_email_line(line):
    return bool(re.search(r'[\w.+-]+@[\w.-]+\.\w+', line.strip()))


def has_inline_affil(line):
    """Check if line has inline affiliation like 'Name (UFRGS)'."""
    return bool(re.match(r'^.+\s*\([A-Z]{2,}\)\s*$', line.strip()))


# Words that indicate a line is title text, NOT a person's name.
# Only include words that appear IN TITLES of this specific seminar
# and could NOT be surnames/given names.
TITLE_WORDS = {
    'arquitetura', 'moderna', 'moderno', 'modernismo', 'modernidade',
    'modernistas', 'modernos', 'modernista', 'preservacao', 'patrimonio',
    'edificio', 'estudo', 'analise', 'caso', 'proposta', 'residencia',
    'influencia', 'influencias', 'projeto', 'cidade', 'urbano', 'urbana',
    'producao', 'construcao', 'critica', 'valor', 'valores',
    'consolidacao', 'forum', 'racionalismo', 'estetica', 'maquina',
    'permanencias', 'perspectivas', 'dificuldades', 'reconstrucao',
    'simulacao', 'tombamento', 'experimentacao', 'moradia',
    'caminhos', 'contribuicao', 'tradicao', 'regional', 'regionalismo',
    'paradoxos', 'peculiaridades', 'autoridades', 'emendas',
    'recursos', 'obra', 'obras', 'arquitetos', 'discipulos', 'escola',
    'casa', 'judiciario', 'anexo', 'contemporaneo', 'avenida',
    'base', 'aerea', 'mundial', 'terminal', 'rodoviario',
    'centro', 'historico', 'campos', 'opostos', 'raiz', 'amarga',
    'ingles', 'para', 'sobre', 'entre', 'com', 'sem', 'por', 'uma', 'um',
    'nos', 'nas', 'arte', 'etica', 'materiais', 'validando',
    'fator', 'lugar', 'mosaicos', 'curvas', 'virtual',
    'recife', 'fortaleza', 'teresina', 'belem', 'maceio',
    'alagoas', 'bahia', 'pernambuco', 'ceara', 'maranhao', 'piaui',
    'brasil', 'europeu',
    'vila', 'amazonas', 'serra', 'navio', 'tombar',
    'helio', 'modesto', 'ressonancia', 'resistibilidade',
    'ingresso', 'armazenar', 'praca', 'sinimbu', 'residencial',
    'antibioticos', 'universidade', 'federal', 'instituto',
    'processo', 'realizado', 'wandenkolk', 'tinoco',
    'seminario', 'docomomo', 'vernacular', 'movimento',
    'criterios', 'criterio', 'definicao',
    'paralelo', 'escamoteado',
    'cortelazzi', 'kennedy', 'presidente',
    'universitaria', 'ufc',
}


def is_likely_name(line):
    """Check if a line is likely a person's name."""
    stripped = line.strip().rstrip('.')
    words = stripped.split()
    if not words or len(words) < 2:
        return False
    if line.strip().endswith('.'):
        return False
    particles = {'de', 'da', 'do', 'dos', 'das', 'e', 'di'}
    clean = re.sub(r'\s*\([^)]*\)', '', stripped)
    clean_words = clean.split()
    non_particles = [w for w in clean_words if w.lower() not in particles]
    if not non_particles:
        return False
    if not all(w[0].isupper() for w in non_particles):
        return False
    for w in clean_words:
        if normalize_for_match(w) in TITLE_WORDS:
            return False
    if re.search(r'\b\d{4}\b', stripped):
        return False
    return True


def should_merge_with_title(prev_line, candidate):
    """Returns True if candidate name should be merged into title."""
    prev = prev_line.strip()
    if prev.endswith('.'):
        return False
    last_word = prev.split()[-1] if prev.split() else ''
    # Prepositions
    if last_word.lower() in {'de', 'do', 'da', 'dos', 'das', 'por', 'ao', 'no', 'na',
                               'nos', 'nas', 'em', 'com', 'para'}:
        return True
    # Title nouns that precede proper names
    if last_word.lower() in {'arquiteto', 'arquiteta', 'engenheiro', 'engenheira'}:
        return True
    # "por Name" pattern
    words = prev.split()
    if len(words) >= 2 and words[-2].lower() == 'por' and words[-1][0].isupper():
        return True
    return False


def parse_first_page_content(text):
    """Extract content lines between header and footer on first page."""
    lines = text.split('\n')
    start = 0
    for i, line in enumerate(lines):
        if 'semin' in line.lower() and 'docomomo' in line.lower():
            start = i + 1
            break
    while start < len(lines) and not lines[start].strip():
        start += 1
    end = len(lines)
    for i in range(start, len(lines)):
        lower = lines[i].lower()
        if 'faculdade de arquitetura da universidade federal da bahia' in lower:
            end = i
            break
        if 'salvador, 04 a 07' in lower:
            end = i
            break
    content = []
    for i in range(start, end):
        s = lines[i].strip()
        if s and s != '.':
            content.append(s)
    return content


def parse_title_and_authors(content_lines):
    """
    Separate title from authors.
    Returns: (title, names_list, bios_list, emails_list)
    """
    if not content_lines:
        return '', [], [], []

    # Find first bio/email index
    first_bio_idx = None
    for i, line in enumerate(content_lines):
        if is_bio_line(line) or is_email_line(line):
            first_bio_idx = i
            break

    if first_bio_idx is None:
        # No bio/email: check for inline affiliations as marker
        first_affil_idx = None
        for i, line in enumerate(content_lines):
            if has_inline_affil(line):
                first_affil_idx = i
                break
        if first_affil_idx is not None:
            title = ' '.join(content_lines[:first_affil_idx]).rstrip('.')
            name_lines = content_lines[first_affil_idx:]
            names = []
            for line in name_lines:
                match = re.match(r'^(.+?)\s*\(([^)]+)\)\s*$', line.strip())
                if match:
                    names.append((match.group(1).strip(), match.group(2).strip()))
            return title, names, [], []
        title = ' '.join(content_lines).rstrip('.')
        return title, [], [], []

    # Walk backwards from first_bio_idx to find where names start
    name_start = first_bio_idx
    for i in range(first_bio_idx - 1, -1, -1):
        line = content_lines[i]
        if is_likely_name(line) or has_inline_affil(line):
            # Check: should this name be merged with title (title continuation)?
            if i > 0 and should_merge_with_title(content_lines[i - 1], line):
                # This "name" is actually part of the title
                break
            name_start = i
        else:
            break

    # Title = everything before name_start
    title = ' '.join(content_lines[:name_start]).rstrip('.')

    # Names = lines from name_start to first_bio_idx
    name_lines = []
    for i in range(name_start, first_bio_idx):
        line = content_lines[i]
        if is_likely_name(line) or has_inline_affil(line):
            name_lines.append(line)

    # Bio and email lines = from first_bio_idx onwards
    bios = []
    emails = []
    for i in range(first_bio_idx, len(content_lines)):
        line = content_lines[i]
        if is_email_line(line):
            found = re.findall(r'[\w.+-]+@[\w.-]+\.\w+', line)
            emails.extend(found)
        elif is_bio_line(line):
            bios.append(line)
        elif line.strip() == 'nd':
            continue
        else:
            # Bio continuation - append to last bio
            if bios:
                bios[-1] = bios[-1] + ' ' + line.strip()

    # Parse names
    names = []
    for line in name_lines:
        match = re.match(r'^(.+?)\s*\(([^)]+)\)\s*$', line.strip())
        if match:
            names.append((match.group(1).strip(), match.group(2).strip()))
        else:
            names.append((line.strip(), None))

    return title, names, bios, emails


def extract_authors(names, bios, emails):
    """Build author dicts from parsed data."""
    authors = []
    for i, (name, inline_affil) in enumerate(names):
        author = OrderedDict()
        gn, fn = split_name(name)
        author['givenname'] = gn
        author['familyname'] = fn
        author['email'] = emails[i] if i < len(emails) else None
        if inline_affil:
            author['affiliation'] = inline_affil
        elif i < len(bios):
            author['affiliation'] = extract_affil_sigla(bios[i])
        else:
            author['affiliation'] = None
        author['bio'] = bios[i] if i < len(bios) else None
        bio_text = bios[i] if i < len(bios) else ''
        author['country'] = detect_country(bio_text)
        author['orcid'] = None
        author['primary_contact'] = (i == 0)
        authors.append(author)
    return authors


def split_name(full_name):
    full_name = re.sub(r'\s*\([^)]*\)', '', full_name).strip()
    words = full_name.split()
    if len(words) <= 1:
        return full_name, ''
    return ' '.join(words[:-1]), words[-1]


def extract_affil_sigla(bio):
    if not bio:
        return None
    sigla_map = [
        ('ETSAB/UPC', 'ETSAB-UPC'), ('ETSAB', 'ETSAB-UPC'),
        ('FAUUSP', 'FAU-USP'),
        ('PPGAU-UFBA', 'PPGAU-UFBA'), ('PPGAU/UFRN', 'PPGAU-UFRN'),
        ('PPGAU/UFBA', 'PPGAU-UFBA'),
        ('PROPAR', 'PROPAR-UFRGS'), ('PROURB', 'PROURB-UFRJ'),
        ('University of Michigan', 'Univ. Michigan'),
        ('Sorbonne', 'Univ. Paris 1'), ('Paris 1', 'Univ. Paris 1'),
        ('UTL', 'FA-UTL'),
    ]
    for key, val in sigla_map:
        if key in bio:
            return val
    siglas = re.findall(r'\b(UF[A-Z]{1,4}|UEMA|UEPA|UNICAP|FAUPE|UPM|USP|IPHAN|UnB)\b', bio)
    if siglas:
        return siglas[-1]
    uni_patterns = [
        (r'Universidade Federal de Pelotas', 'UFPel'),
        (r'Universidade Federal de Pernambuco', 'UFPE'),
        (r'Universidade Federal da Bahia', 'UFBA'),
        (r'Universidade Federal do Cear', 'UFC'),
        (r'Universidade Federal de Alagoas', 'UFAL'),
        (r'Universidade Federal do Piau', 'UFPI'),
        (r'Universidade Federal do Rio Grande do Norte', 'UFRN'),
        (r'Universidade Federal do Rio Grande do Sul', 'UFRGS'),
        (r'Universidade Federal do Par', 'UFPA'),
        (r'Universidade Federal do Rio de Janeiro', 'UFRJ'),
        (r'Universidade de Bras', 'UnB'),
        (r'Universidade de S.o Paulo', 'USP'),
        (r'Universidade Presbiteriana Mackenzie', 'UPM'),
        (r'Universidade Estadual do Maranh', 'UEMA'),
        (r'Universidade Estadual do Par', 'UEPA'),
        (r'Universidade Tiradentes', 'UNIT'),
        (r'Faculdade de Arquitetura e Urbanismo de S.o Paulo', 'FAU-USP'),
        (r'Faculdade de Arquitetura e Urbanismo da Universidade de S.o Paulo', 'FAU-USP'),
        (r'Faculdade de Arquitetura e Urbanismo da Universidade Presbiteriana', 'FAU-UPM'),
        (r'Faculdades Unidas de Pernambuco', 'FAUPE'),
    ]
    for pattern, sigla in uni_patterns:
        if re.search(pattern, bio, re.IGNORECASE):
            return sigla
    parens = re.findall(r'\(([A-Z]{2,}[^)]*)\)', bio)
    if parens:
        return parens[-1]
    return None


def detect_country(bio):
    if not bio:
        return 'BR'
    foreign = {
        'Portugal': 'PT', 'UTL': 'PT',
        'EUA': 'US', 'USA': 'US', 'Michigan': 'US',
        'University of Michigan': 'US',
        'Sorbonne': 'FR', 'Paris 1': 'FR',
        'UPC': 'ES', 'ETSAB': 'ES',
    }
    for key, country in foreign.items():
        if key in bio:
            return country
    return 'BR'


def parse_resumo_keywords(full_text):
    resumo = None
    palavras_chave = []
    lines = full_text.split('\n')

    resumo_lines = []
    in_resumo = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^Resumo\s*:?\s*$', stripped, re.IGNORECASE):
            in_resumo = True
            continue
        if in_resumo:
            if re.match(r'^(?:Palavr|Palabr|Abstract|Key\s*word)', stripped, re.IGNORECASE):
                break
            if 'Faculdade de Arquitetura da Universidade' in stripped:
                break
            if re.match(r'^2.\s*Semin.rio DOCOMOMO', stripped):
                break
            if stripped:
                resumo_lines.append(stripped)

    if resumo_lines:
        resumo = ' '.join(resumo_lines).strip()
        resumo = re.sub(r'\s+', ' ', resumo)

    kw_text = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        kw_match = re.match(
            r'^(?:Palavras[\s-]*[Cc]have[s]?|Palabras[\s-]*[Cc]lave)\s*[:\s]*(.*)$',
            stripped, re.IGNORECASE
        )
        if kw_match:
            kw_rest = kw_match.group(1).strip()
            kw_parts = [kw_rest] if kw_rest else []
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j].strip()
                if not next_line:
                    break
                if re.match(r'^(?:Abstract|Key\s*word|Faculdade|2.\s*Semin)', next_line, re.IGNORECASE):
                    break
                kw_parts.append(next_line)
            kw_text = ' '.join(kw_parts).strip()
            break

    if kw_text:
        raw_kws = re.split(r'[;,]', kw_text)
        palavras_chave = [kw.strip().rstrip('.') for kw in raw_kws if kw.strip()]

    return resumo, palavras_chave


def parse_references(full_text):
    lines = full_text.split('\n')
    ref_start = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^(?:REFER.NCIAS\s*(?:BIBLIOGR.FICAS)?|Bibliografia|Refer.ncias\s*(?:Bibliogr.ficas)?)\s*:?\s*$',
                     stripped, re.IGNORECASE):
            ref_start = i + 1
            break

    if ref_start is None:
        return None

    ref_lines = []
    for i in range(ref_start, len(lines)):
        stripped = lines[i].strip()
        if re.match(r'^\d{1,3}$', stripped):
            continue
        if 'Faculdade de Arquitetura da Universidade Federal da Bahia' in stripped:
            continue
        if 'Salvador, 04 a 07 de junho' in stripped:
            continue
        if re.match(r'^2.\s*Semin.rio DOCOMOMO', stripped):
            continue
        ref_lines.append(stripped)

    refs = []
    current_ref = []
    for line in ref_lines:
        if not line:
            if current_ref:
                refs.append(' '.join(current_ref))
                current_ref = []
            continue
        if re.match(r'^[A-Z\u00C0-\u00DC][A-Z\u00C0-\u00DC\s,\.]+[,.]', line) or re.match(r'^_{3,}', line):
            if current_ref:
                refs.append(' '.join(current_ref))
            current_ref = [line]
        else:
            current_ref.append(line)

    if current_ref:
        refs.append(' '.join(current_ref))

    cleaned = []
    for ref in refs:
        ref = re.sub(r'\s+', ' ', ref).strip()
        if len(ref) > 15:
            cleaned.append(ref)
    return cleaned if cleaned else None


def process_pdf(pdf_path, filename):
    first_page = get_text(pdf_path, first_page_only=True)
    full_text = get_text(pdf_path)
    page_count = get_page_count(pdf_path)

    content_lines = parse_first_page_content(first_page)
    title, names, bios, emails = parse_title_and_authors(content_lines)

    titulo = title
    subtitulo = None
    if ': ' in title:
        parts = title.split(': ', 1)
        titulo = parts[0].strip()
        subtitulo = parts[1].strip()

    authors = extract_authors(names, bios, emails)
    resumo, palavras_chave = parse_resumo_keywords(full_text)
    referencias = parse_references(full_text)

    return {
        'titulo': titulo,
        'subtitulo': subtitulo,
        'autores': authors,
        'resumo': resumo,
        'palavras_chave': palavras_chave if palavras_chave else None,
        'paginas_total': page_count,
        'referencias': referencias,
        'arquivo_original': filename,
    }


def main():
    all_files = sorted(os.listdir(PDF_DIR))
    pdf_files = [f for f in all_files if f.endswith('.pdf')
                 and f not in SKIP_FILES
                 and not f.startswith('sdnne02-')]

    print(f"Total PDFs no diretorio: {len([f for f in all_files if f.endswith('.pdf')])}")
    print(f"Duplicados ignorados: {SKIP_FILES}")
    print(f"PDFs a processar: {len(pdf_files)}")
    print()

    artigos = []
    for i, filename in enumerate(pdf_files):
        seq = i + 1
        article_id = f'{SEMINARIO}-{seq:03d}'
        pdf_path = os.path.join(PDF_DIR, filename)

        print(f"[{seq:02d}/{len(pdf_files)}] {filename}")
        data = process_pdf(pdf_path, filename)

        article = OrderedDict()
        article['id'] = article_id
        article['titulo'] = data['titulo']
        article['subtitulo'] = data['subtitulo']
        article['locale'] = 'pt-BR'
        article['secao'] = 'Artigos Completos'
        article['autores'] = data['autores']
        article['resumo'] = data['resumo']
        article['palavras_chave'] = data['palavras_chave']
        article['arquivo_pdf'] = f'{article_id}.pdf'
        article['arquivo_original'] = data['arquivo_original']
        article['paginas_total'] = data['paginas_total']
        article['referencias'] = data['referencias']
        artigos.append(article)

        dst = os.path.join(PDF_DIR, f'{article_id}.pdf')
        if not os.path.exists(dst):
            shutil.copy2(pdf_path, dst)

        titulo_short = (data['titulo'] or '???')[:55]
        n_aut = len(data['autores'])
        has_r = 'Y' if data.get('resumo') else 'N'
        has_k = 'Y' if data.get('palavras_chave') else 'N'
        has_ref = 'Y' if data.get('referencias') else 'N'
        print(f"       => {titulo_short}")
        print(f"          Aut:{n_aut} Res:{has_r} KW:{has_k} Ref:{has_ref} Pag:{data['paginas_total']}")

    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        existing = yaml.safe_load(f)

    existing['artigos'] = artigos

    with open(YAML_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(existing, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)

    print()
    print('=' * 70)
    print(f'SUMARIO - {SEMINARIO}')
    print('=' * 70)
    print(f'Total de artigos: {len(artigos)}')
    com_resumo = sum(1 for a in artigos if a.get('resumo'))
    com_kw = sum(1 for a in artigos if a.get('palavras_chave'))
    com_ref = sum(1 for a in artigos if a.get('referencias'))
    com_email = sum(1 for a in artigos if any(au.get('email') for au in a.get('autores', [])))
    total_aut = sum(len(a.get('autores', [])) for a in artigos)
    print(f'Com resumo:           {com_resumo}/{len(artigos)}')
    print(f'Com palavras-chave:   {com_kw}/{len(artigos)}')
    print(f'Com referencias:      {com_ref}/{len(artigos)}')
    print(f'Com email (>=1 autor): {com_email}/{len(artigos)}')
    print(f'Total de autores:     {total_aut}')
    print()

    sem_resumo = [a for a in artigos if not a.get('resumo')]
    if sem_resumo:
        print('Artigos SEM resumo:')
        for a in sem_resumo:
            print(f"  - {a['id']}: {a['titulo'][:60]}")
        print()

    sem_kw = [a for a in artigos if not a.get('palavras_chave')]
    if sem_kw:
        print('Artigos SEM palavras-chave:')
        for a in sem_kw:
            print(f"  - {a['id']}: {a['titulo'][:60]}")
        print()

    sem_ref = [a for a in artigos if not a.get('referencias')]
    if sem_ref:
        print('Artigos SEM referencias:')
        for a in sem_ref:
            print(f"  - {a['id']}: {a['titulo'][:60]}")
        print()

    sem_aut = [a for a in artigos if not a.get('autores')]
    if sem_aut:
        print('Artigos SEM autores:')
        for a in sem_aut:
            print(f"  - {a['id']}: {a['titulo'][:60]}")
        print()

    print('LISTA DE ARTIGOS:')
    for a in artigos:
        aut_names = ', '.join(f"{au['givenname']} {au['familyname']}" for au in a['autores'])
        print(f"  {a['id']}: {a['titulo'][:50]} | {aut_names[:50]}")

    print()
    print(f'YAML salvo em: {YAML_PATH}')
    print(f'PDFs padronizados em: {PDF_DIR}/')


if __name__ == '__main__':
    main()
