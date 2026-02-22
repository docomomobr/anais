#!/usr/bin/env python3
"""
construir_sdnne04.py - Constrói YAML de artigos para sdnne04
4º Seminário Docomomo Norte/Nordeste, Natal, 2012

Lê PDFs de fontes/, extrai metadados via pdftotext, copia/renomeia
para pdfs/ e gera o YAML consolidado.
"""

import os
import sys
import re
import subprocess
import shutil
import yaml
from collections import OrderedDict

BASE_DIR = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/nne/sdnne04'
FONTES_DIR = os.path.join(BASE_DIR, 'fontes')
PDFS_DIR = os.path.join(BASE_DIR, 'pdfs')
YAML_OUT = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/nne/sdnne04.yaml'

HEADER_LINE = 'Arquitetura em cidades'  # Common header prefix

EMAIL_COUNTER = [0]


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


# ── Helpers ──────────────────────────────────────────────────

def extract_text_raw(filepath):
    """Extract text from PDF using pdftotext (no layout)."""
    try:
        result = subprocess.run(
            ['pdftotext', filepath, '-'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.split('\n')
        return None
    except Exception as e:
        print(f"  AVISO: Erro pdftotext {os.path.basename(filepath)}: {e}")
        return None


def get_pdf_page_count(filepath):
    """Get page count from PDF using pdfinfo."""
    try:
        result = subprocess.run(
            ['pdfinfo', filepath],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split('\n'):
            if line.startswith('Pages:'):
                return int(line.split(':')[1].strip())
    except:
        pass
    return None


def next_placeholder_email(familyname):
    """Generate placeholder email based on familyname."""
    EMAIL_COUNTER[0] += 1
    if familyname:
        slug = familyname.lower().replace(' ', '').replace("'", '')
        # Remove accents simplistically
        for src, dst in [('á','a'),('à','a'),('ã','a'),('â','a'),('é','e'),('ê','e'),
                         ('í','i'),('ó','o'),('ô','o'),('õ','o'),('ú','u'),('ç','c')]:
            slug = slug.replace(src, dst)
        return f"{slug}@exemplo.com"
    return f"sem-email-{EMAIL_COUNTER[0]}@exemplo.com"


# ── Name helpers ─────────────────────────────────────────────

PARTICLES = {'de', 'da', 'do', 'dos', 'das', 'e', 'del', 'von', 'di', 'van'}

def capitalize_name(name):
    """Capitalize name, keeping particles lowercase."""
    words = name.split()
    result = []
    for w in words:
        if w.lower() in PARTICLES:
            result.append(w.lower())
        elif w.isupper() and len(w) > 1:
            result.append(w.capitalize())
        else:
            result.append(w)
    return ' '.join(result)


def split_given_family(full_name):
    """Split 'Firstname ... Lastname' into givenname/familyname.

    Brazilian convention: particles (de, da, do) go in givenname,
    familyname = last surname only.
    """
    name = full_name.strip()
    name = re.sub(r'\s+', ' ', name)
    if not name:
        return '', ''
    words = name.split()
    if len(words) == 1:
        return '', capitalize_name(name)
    familyname = words[-1]
    givenname = ' '.join(words[:-1])
    return capitalize_name(givenname), capitalize_name(familyname)


# ── Affiliation extraction ───────────────────────────────────

def extract_affiliation(text):
    """Extract institutional affiliation abbreviation."""
    patterns = [
        (r'PPGAU.*UFPA|PPGAU/UFPA', 'PPGAU-UFPA'),
        (r'PPGAU.*UFRN|PPGAU/UFRN', 'PPGAU-UFRN'),
        (r'PPGAU.*UFPB|PPGAU/UFPB|CAU/PPGAU/UFPB', 'PPGAU-UFPB'),
        (r'PPGAU.*UFAL|PPGAU/UFAL|PPGAU.*FAU.*UFAL', 'PPGAU-UFAL'),
        (r'MDU.*UFPE|MDU/UFPE', 'MDU-UFPE'),
        (r'DAU.*UFPE|Departamento de Arquitetura.*UFPE|DAU/UFPE', 'DAU-UFPE'),
        (r'DAU.*UFC|DAU/UFC|Departamento de Arquitetura.*UFC', 'DAU-UFC'),
        (r'DARQ.*UFRN|DARQ/UFRN|Departamento de Arquitetura.*UFRN', 'DARQ-UFRN'),
        (r'FAUFBA|FAU-?UFBA|FAU/UFBA|Faculdade de Arquitetura.*UFBA', 'FAUFBA'),
        (r'FAU-?UnB|FAU/UnB', 'FAU-UnB'),
        (r'IAU-?USP|IAU/USP|Instituto de Arquitetura.*USP', 'IAU-USP'),
        (r'FAU-?USP|FAUUSP|FAU/USP', 'FAU-USP'),
        (r'FAUUPM|Universidade Presbiteriana Mackenzie|Mackenzie', 'Mackenzie'),
        (r'PROGRAU.*UFPel|DARQ.*UFPel|Universidade Federal de Pelotas', 'UFPel'),
        (r'UniRitter', 'UniRitter'),
        (r'UNIPE|Centro Universitário de João Pessoa', 'UNIPÊ'),
        (r'ESUDA', 'ESUDA'),
        (r'Camillo Filho|Professor Camillo Filho', 'ICF'),
        (r'FAUTL|Universidade T.cnica de Lisboa', 'FAUTL'),
        (r'CGAU.*UFPI|UFPI|Universidade Federal do Piau', 'UFPI'),
        (r'NAU.*UFS|PROARQ.*UFS|Universidade Federal de Sergipe', 'UFS'),
        (r'UFBA', 'UFBA'),
        (r'UFPE', 'UFPE'),
        (r'UFRN', 'UFRN'),
        (r'UFPB', 'UFPB'),
        (r'UFPA', 'UFPA'),
        (r'UFCG', 'UFCG'),
        (r'UFAL', 'UFAL'),
        (r'UnB\b', 'UnB'),
        (r'UFRGS', 'UFRGS'),
        (r'USP\b|Universidade de S.o Paulo', 'USP'),
        (r'UFC\b|Universidade Federal do Cear', 'UFC'),
        (r'Universidade Federal do Rio Grande do Norte', 'UFRN'),
        (r'Universidade Federal da Para.ba', 'UFPB'),
        (r'Universidade Federal da Bahia', 'UFBA'),
        (r'Universidade Federal de Pernambuco', 'UFPE'),
        (r'Universidade Federal do Par.', 'UFPA'),
        (r'Universidade Federal de Alagoas', 'UFAL'),
        (r'Universidade Federal de Campina Grande', 'UFCG'),
        (r'Fundação Joaquim Nabuco|Fundaj', 'Fundaj'),
        (r'Geosistemas', 'Geosistemas'),
    ]
    for pattern, abbrev in patterns:
        if re.search(pattern, text, re.I):
            return abbrev
    return None


# ── Author parsing ───────────────────────────────────────────

def is_bio_line(text):
    """Check if a line looks like a bio/affiliation description."""
    text_lower = text.lower().strip()
    bio_starters = [
        r'^arquitet[ao]\b', r'^engenheiro?a?\b', r'^urbanista\b',
        r'^bacharela?\b', r'^graduand[ao]\b', r'^graduação\b', r'^graduada?\b',
        r'^mestr[ae]\b', r'^mestrand[ao]\b', r'^doutor[ao]?\b', r'^doutoranda?\b',
        r'^profa?\.?\s', r'^professor', r'^pesquisador',
        r'^especialista\b', r'^coordenador',
        r'^docente\b', r'^servidor', r'^membro\b',
        r'^discente\b', r'^concluinte\b', r'^orientador',
        r'^livre.docente\b', r'^biólog[ao]\b',
        r'^advogad[ao]\b', r'^jornalista\b', r'^escritor',
        r'^tecnólog[ao]\b', r'^estudante\b',
        r'^bolsista\b',
        r'^\d+\.\s*(arquitet|graduand|mestr|doutor|prof|estudante|bolsista)',
    ]
    for pat in bio_starters:
        if re.match(pat, text_lower):
            return True
    if any(kw in text_lower for kw in ['universidade', 'programa de pós', 'departamento de',
                                        'faculdade de', 'laboratório', 'instituto',
                                        'escola de', 'grupo de pesquisa', 'centro de tecnologia',
                                        'campus ', 'cidade universitária', 'curso de']):
        return True
    if re.match(r'^(rua|r\.|av\.|avenida|alameda|pra[çc]a|travessa|rod\.)\s', text_lower):
        return True
    if re.match(r'^\d{5}[-.]?\d{3}', text_lower):
        return True
    if re.match(r'^\(\d{2,3}\)', text_lower):
        return True
    if re.match(r'^cep[:\s]', text_lower):
        return True
    if re.match(r'^caixa postal', text_lower):
        return True
    if re.match(r'^br\s+\d', text_lower):
        return True
    if re.match(r'^tel', text_lower):
        return True
    if re.match(r'^\d+[-\s]', text_lower) and 'CEP' in text:
        return True
    return False


def parse_authors_from_header(lines, pdf_name):
    """Parse authors from the header section before RESUMO.

    Handles multiple formats found in sdnne04:
    1. (N) LASTNAME, Firstname  (numbered, UPPERCASE lastname)
    2. LASTNAME, Firstname (N)  (number after name)
    3. LASTNAME, Firstname      (no number, UPPERCASE lastname)
    4. LASTNAME JUNIOR, Firstname (compound family name)
    5. CORDEIRO, Vanessa (1); MOURÃO, Emerson (2)  (semicolon separated, number after)
    6. OLIVEIRA, Patrícia A. S. (1); PERES, Clara T. (2)  (semicolon separated)
    """
    # Find Resumo/RESUMO line index
    resumo_idx = None
    for i, line in enumerate(lines):
        text = line.strip()
        if re.match(r'^(RESUMO|Resumo)\s*$', text):
            resumo_idx = i
            break

    if resumo_idx is None:
        # Try relaxed
        for i, line in enumerate(lines):
            text = line.strip()
            if re.match(r'^resumo\s*$', text, re.I):
                resumo_idx = i
                break
        # Some PDFs may have the resumo embedded differently
        if resumo_idx is None:
            for i, line in enumerate(lines):
                text = line.strip().lower()
                if 'resumo' in text and i > 5 and len(text) < 20:
                    resumo_idx = i
                    break

    if resumo_idx is None:
        print(f"  AVISO: RESUMO não encontrado em {pdf_name}")
        return []

    header = lines[:resumo_idx]

    # Skip the event header line(s)
    start_idx = 0
    for i, line in enumerate(header):
        text = line.strip()
        if HEADER_LINE.lower() in text.lower():
            start_idx = i + 1
            break

    # Skip empty lines after header
    while start_idx < len(header) and not header[start_idx].strip():
        start_idx += 1

    header_text = '\n'.join([l.strip() for l in header[start_idx:]])

    # Strategy 1: Try to find numbered authors with (N) prefix: "(1) LASTNAME, Firstname"
    numbered_prefix = re.findall(r'\(\d+\)\s*([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][A-ZÀÁÂÃÉÊÍÓÔÕÚÇ\s]*?),\s*([^;\n\(]+)', header_text)

    # Strategy 2: "LASTNAME, Firstname (N)." or "LASTNAME, Firstname (N);"
    numbered_suffix = re.findall(r'([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][A-ZÀÁÂÃÉÊÍÓÔÕÚÇ\s]*?),\s*([^;\n\(]+?)\s*\(\d+\)', header_text)

    # Strategy 3: Plain "LASTNAME, Firstname" without numbers
    plain_upper = re.findall(r'^([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][A-ZÀÁÂÃÉÊÍÓÔÕÚÇ\s]*?),\s*([^\n;]+?)$', header_text, re.M)

    # Strategy 4: "LASTNAME¸Firstname" (weird cedilla-comma, seen in DOCONATAL022)
    weird_comma = re.findall(r'([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][A-ZÀÁÂÃÉÊÍÓÔÕÚÇ\s]*?)[¸]\s*([^\n;]+?)$', header_text, re.M)

    raw_authors = []

    if numbered_prefix:
        raw_authors = numbered_prefix
    elif numbered_suffix:
        raw_authors = numbered_suffix
    elif plain_upper:
        # Filter: only take lines where family name is all caps (not title lines)
        for family, given in plain_upper:
            family_clean = family.strip()
            # Must be mostly uppercase (not a title line)
            if family_clean == family_clean.upper() and len(family_clean) > 2:
                # Exclude known false positives
                if not re.match(r'^(RESUMO|ABSTRACT|PALAVRAS|KEY|EIXO|ARQUITETURA|INSERÇ|DE POEMA)', family_clean):
                    raw_authors.append((family_clean, given))
    elif weird_comma:
        raw_authors = weird_comma

    if not raw_authors:
        # Last resort: look for author names in specific lines
        print(f"  AVISO: Autores não encontrados por regex em {pdf_name}")
        return []

    # Now resolve each author with email and affiliation
    authors = []
    used_emails = set()

    for raw_family, raw_given in raw_authors:
        raw_family = raw_family.strip().rstrip('.')
        raw_given = raw_given.strip().rstrip('.')
        # Remove trailing number patterns like "(1)" from givenname
        raw_given = re.sub(r'\s*\(\d+\)\s*$', '', raw_given).strip().rstrip('.')
        # Remove leading/trailing semicolons
        raw_given = raw_given.strip(';').strip()

        # Skip if this looks like a false positive
        if not raw_given or not raw_family:
            continue
        if len(raw_family) < 2 or len(raw_given) < 2:
            continue

        # Handle compound family names like "ANDRADE JUNIOR"
        familyname = capitalize_name(raw_family)
        givenname = capitalize_name(raw_given)

        # For ANDRADE JUNIOR pattern: "Andrade Junior" stays as familyname
        # but per Brazilian convention, "Junior/Neto/Filho" can be part of familyname
        # Check if familyname has multiple words (e.g. "Andrade Junior")
        family_words = familyname.split()
        if len(family_words) > 1:
            # Keep compound family if it contains Junior/Neto/Filho/Sobrinho
            if any(w.lower() in ('junior', 'jr', 'jr.', 'neto', 'filho', 'sobrinho') for w in family_words):
                pass  # Keep as is
            else:
                # Move extra words to givenname (typical split error)
                # Actually for sdnne04, compound families like "SÁ CARNEIRO" should stay
                # Let's keep compound families as-is since the PDF has them as the family name
                pass

        # Find email in the text after this author's name
        # Search for the first unused email in the header
        email = None

        # Find position of this author in header
        # Search for their name pattern
        search_name = raw_family.upper()
        name_pos = header_text.upper().find(search_name)

        if name_pos >= 0:
            # Find next author position (or end of header)
            next_author_pos = len(header_text)
            for other_family, _ in raw_authors:
                other_clean = other_family.strip().upper()
                if other_clean == raw_family.upper():
                    continue
                other_pos = header_text.upper().find(other_clean, name_pos + len(search_name))
                if other_pos > name_pos and other_pos < next_author_pos:
                    next_author_pos = other_pos

            block = header_text[name_pos:next_author_pos]
            email_match = re.search(r'([\w.+-]+@[\w.-]+\.\w{2,})', block)
            if email_match:
                email = email_match.group(1).lower()
                # Fix common OCR issues in emails
                email = email.replace('E-mail:', '').replace('e-mail:', '').strip()

            # Extract affiliation from block
            affiliation = extract_affiliation(block)
        else:
            affiliation = None

        if email and email in used_emails:
            email = None  # Don't reuse
        if email:
            used_emails.add(email)

        # Detect country
        country = 'BR'
        if name_pos >= 0:
            block_lower = header_text[name_pos:name_pos+500].lower()
            if 'lisboa' in block_lower or 'portugal' in block_lower:
                country = 'PT'
            elif 'montevid' in block_lower or 'uruguay' in block_lower:
                country = 'UY'

        authors.append({
            'givenname': givenname,
            'familyname': familyname,
            'email': email,
            'affiliation': affiliation,
            'country': country,
            'primary_contact': len(authors) == 0,
        })

    return authors


# ── Title extraction ─────────────────────────────────────────

def extract_title(lines):
    """Extract title from lines between the header and the author/eixo lines.

    The title is between the event header and the first author line.
    """
    # Find end of event header
    start_idx = 0
    for i, line in enumerate(lines):
        text = line.strip()
        if HEADER_LINE.lower() in text.lower():
            start_idx = i + 1
            break

    # Skip blank lines
    while start_idx < len(lines) and not lines[start_idx].strip():
        start_idx += 1

    # Collect title lines until we hit an author line or eixo temático
    title_lines = []
    for i in range(start_idx, min(start_idx + 15, len(lines))):
        text = lines[i].strip()
        if not text:
            if title_lines:
                break
            continue

        # Stop at author patterns
        if re.match(r'^\(\d+\)\s*[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ]', text):
            break
        if re.match(r'^[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ]{2,}[,¸]\s', text):
            break
        if re.match(r'^[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ]{2,}\s+JUNIOR', text, re.I):
            break
        # Stop at "Eixo temático"
        if re.match(r'^Eixo [Tt]em', text, re.I):
            break

        title_lines.append(text)

    if title_lines:
        full_title = ' '.join(title_lines)
        full_title = re.sub(r'\s+', ' ', full_title).strip()
        return full_title
    return None


def separate_title_subtitle(full_title):
    """Separate title and subtitle.

    Use first ':' as separator unless it's within quotes.
    """
    if not full_title:
        return full_title, None

    # Find first colon not inside quotes
    in_quote = False
    for i, c in enumerate(full_title):
        if c in '""\u201c\u201d':
            in_quote = not in_quote
        if c == ':' and not in_quote:
            title = full_title[:i].strip()
            subtitle = full_title[i+1:].strip()
            if subtitle:
                return title, subtitle
            return title, None

    return full_title, None


# ── Eixo temático extraction ─────────────────────────────────

def extract_eixo(lines):
    """Extract eixo temático from text."""
    for line in lines:
        text = line.strip()
        if re.match(r'^Eixo [Tt]em', text, re.I):
            # Get the eixo value
            eixo_text = re.sub(r'^Eixo [Tt]em.tico\s*:?\s*', '', text, flags=re.I).strip()
            # May continue on next line
            idx = lines.index(line)
            if idx + 1 < len(lines):
                next_line = lines[idx + 1].strip()
                # If next line is not a title/author/resumo, it might be continuation
                if next_line and not re.match(r'^(RESUMO|Resumo|\(\d|[A-Z]{2,},)', next_line):
                    if len(next_line) < 80 and not '@' in next_line:
                        eixo_text += ' ' + next_line
            return eixo_text.strip().rstrip('.')
        # Some PDFs omit "Eixo temático:" but have it inline
    return None


def normalize_eixo(eixo_text):
    """Map eixo temático text to a normalized section name."""
    if not eixo_text:
        return 'Sem eixo', 'SE-sdnne04'

    eixo_lower = eixo_text.lower()

    # Main eixos found in the PDFs:
    # 1. "A arquitetura moderna como projeto" / "A arquitetura modernista como projeto"
    if 'arquitetura modern' in eixo_lower and 'projeto' in eixo_lower:
        return 'A arquitetura moderna como projeto', 'ET1-sdnne04'

    # 2. "narrativas historiográficas" (with various suffixes)
    if 'narrativas historiogr' in eixo_lower:
        return 'Narrativas historiográficas', 'ET2-sdnne04'

    # 3. "experiências de conservação e transformação"
    if 'conservação' in eixo_lower or 'transformação' in eixo_lower:
        return 'Experiências de conservação e transformação', 'ET3-sdnne04'

    return eixo_text, f'ET0-sdnne04'


# ── Metadata extraction ──────────────────────────────────────

def parse_resumo(lines):
    """Extract Portuguese abstract (Resumo)."""
    resumo_lines = []
    in_resumo = False

    for line in lines:
        text = line.strip()
        text_lower = text.lower().strip()

        if re.match(r'^(RESUMO|Resumo)\s*$', text):
            in_resumo = True
            continue

        if in_resumo:
            if re.match(r'^Palavras-?[Cc]have', text, re.I):
                break
            if re.match(r'^PALAVRAS-?CHAVE', text):
                break
            if re.match(r'^PALAVRAS\s+CHAVE', text, re.I):
                break
            if text_lower in ('abstract', 'abstract:'):
                break
            if text_lower in ('resumen', 'resumen:'):
                break
            # Check for keywords inline
            kw_match = re.search(r'Palavras-?[Cc]have\s*:', text, re.I)
            if kw_match:
                before = text[:kw_match.start()].strip()
                if before:
                    resumo_lines.append(before)
                break
            if not text:
                continue
            # Skip page numbers
            if re.match(r'^\d+$', text):
                continue
            # Skip event header repeated
            if HEADER_LINE.lower() in text.lower():
                continue
            resumo_lines.append(text)

    if resumo_lines:
        resumo = ' '.join(resumo_lines)
        resumo = re.sub(r'\s+', ' ', resumo).strip()
        return resumo
    return None


def parse_abstract_en(lines):
    """Extract English abstract."""
    abstract_lines = []
    in_abstract = False

    for line in lines:
        text = line.strip()
        text_lower = text.lower().strip()

        if re.match(r'^ABSTRACT\s*$', text) or text_lower == 'abstract:':
            in_abstract = True
            continue

        if in_abstract:
            if re.match(r'^Key-?[Ww]ords?\s*:', text, re.I):
                break
            if re.match(r'^KEY-?\s*WORDS?\s*:', text):
                break
            kw_match = re.search(r'Key-?[Ww]ords?\s*:', text, re.I)
            if kw_match:
                before = text[:kw_match.start()].strip()
                if before:
                    abstract_lines.append(before)
                break
            if text_lower in ('resumo', 'resumo:'):
                break
            if not text:
                continue
            if re.match(r'^\d+$', text):
                continue
            if HEADER_LINE.lower() in text.lower():
                continue
            # Stop at introduction / body markers
            if re.match(r'^\d+\.?\s*(Introdução|Introduction|Considerações)', text, re.I):
                break
            if re.match(r'^Introdução\s*$', text, re.I):
                break
            abstract_lines.append(text)

    if abstract_lines:
        abstract = ' '.join(abstract_lines)
        abstract = re.sub(r'\s+', ' ', abstract).strip()
        return abstract
    return None


def parse_keywords_pt(lines):
    """Extract Portuguese keywords."""
    for i, line in enumerate(lines):
        text = line.strip()
        if re.match(r'^Palavras-?[Cc]have', text, re.I) or re.match(r'^PALAVRAS-?CHAVE', text) or re.match(r'^PALAVRAS\s+CHAVE', text, re.I):
            kw_text = re.sub(r'^Palavras-?[Cc]have\s*[sS]?\s*:?\s*', '', text, flags=re.I)
            kw_text = re.sub(r'^PALAVRAS-?CHAVE\s*[sS]?\s*:?\s*', '', kw_text, flags=re.I)
            kw_text = re.sub(r'^PALAVRAS\s+CHAVE\s*:?\s*', '', kw_text, flags=re.I)
            kw_text = kw_text.strip().rstrip('.')

            # If keywords are on next line(s) (multiline keywords separated by whitespace)
            if not kw_text and i + 1 < len(lines):
                kw_text = lines[i + 1].strip().rstrip('.')

            # Some PDFs have keywords split across lines with no delimiter
            # e.g. "bioclimática.\n\narquitetura\n\nmoderna..."
            if kw_text and '\n' not in kw_text:
                # Check if next lines also look like keywords (short, no sentences)
                j = i + 1
                extra_kw = []
                while j < len(lines) and j < i + 6:
                    next_text = lines[j].strip()
                    if not next_text:
                        j += 1
                        continue
                    if re.match(r'^(ABSTRACT|Abstract|RESUMO|Resumo|\d+\.)', next_text):
                        break
                    if len(next_text) < 50 and not next_text.endswith('.'):
                        extra_kw.append(next_text)
                    else:
                        break
                    j += 1

            if not kw_text:
                continue

            # Parse keywords by delimiter
            if ';' in kw_text:
                keywords = [k.strip().rstrip('.') for k in kw_text.split(';') if k.strip()]
            elif '. ' in kw_text and ',' not in kw_text:
                keywords = [k.strip().rstrip('.') for k in re.split(r'\.\s+', kw_text) if k.strip()]
            elif ',' in kw_text:
                keywords = [k.strip().rstrip('.') for k in kw_text.split(',') if k.strip()]
            else:
                # Single keyword or space-separated (rare)
                keywords = [kw_text.strip().rstrip('.')]

            keywords = [k for k in keywords if k and len(k) > 1]
            if keywords:
                return keywords
    return []


def parse_keywords_en(lines):
    """Extract English keywords."""
    for line in lines:
        text = line.strip()
        if re.match(r'^Key-?[Ww]ords?\s*:', text, re.I) or re.match(r'^KEY-?\s*WORDS?\s*:', text):
            kw_text = re.sub(r'^Key-?[Ww]ords?\s*:?\s*', '', text, flags=re.I)
            kw_text = re.sub(r'^KEY-?\s*WORDS?\s*:?\s*', '', kw_text, flags=re.I)
            kw_text = kw_text.strip().rstrip('.')
            if not kw_text:
                continue
            if ';' in kw_text:
                keywords = [k.strip().rstrip('.') for k in kw_text.split(';') if k.strip()]
            elif '. ' in kw_text and ',' not in kw_text:
                keywords = [k.strip().rstrip('.') for k in re.split(r'\.\s+', kw_text) if k.strip()]
            elif ',' in kw_text:
                keywords = [k.strip().rstrip('.') for k in kw_text.split(',') if k.strip()]
            else:
                keywords = [kw_text.strip().rstrip('.')]
            keywords = [k for k in keywords if k and len(k) > 1]
            if keywords:
                return keywords
    return []


def parse_references(lines):
    """Extract bibliographic references."""
    refs = []
    in_refs = False
    current_ref = []

    for line in lines:
        text = line.strip()
        text_lower = text.lower()

        if re.match(r'^refer[eê]ncias(\s+bibliogr[aá]ficas)?\.?\s*$', text_lower):
            in_refs = True
            continue
        if text_lower in ('bibliografia', 'bibliografia:', 'referências', 'referências:'):
            in_refs = True
            continue

        if in_refs:
            if not text:
                if current_ref:
                    refs.append(' '.join(current_ref))
                    current_ref = []
                continue

            if re.match(r'^_+$', text):
                break
            if HEADER_LINE.lower() in text.lower():
                if current_ref:
                    refs.append(' '.join(current_ref))
                    current_ref = []
                continue
            if re.match(r'^\d+$', text):
                continue

            # New reference starts with uppercase author name
            if re.match(r'^[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ_]{2,}', text) and current_ref:
                refs.append(' '.join(current_ref))
                current_ref = [text]
            elif re.match(r'^_{3,}', text) and current_ref:
                refs.append(' '.join(current_ref))
                current_ref = [text]
            else:
                current_ref.append(text)

    if current_ref:
        refs.append(' '.join(current_ref))

    cleaned = []
    for ref in refs:
        ref = re.sub(r'\s+', ' ', ref).strip()
        if ref and len(ref) > 10:
            cleaned.append(ref)
    return cleaned


# ── Eixo temático for special PDFs ────────────────────────────

def detect_eixo_from_text(lines):
    """Find eixo temático in lines."""
    for line in lines:
        text = line.strip()
        if re.match(r'^Eixo [Tt]em', text, re.I):
            return extract_eixo(lines)
        # Some PDFs have eixo inline without the "Eixo temático:" prefix
        # e.g. "Experiências de conservação e transformação" standalone
    return None


# ── Main processing ──────────────────────────────────────────

def process_articles():
    print("=" * 70)
    print("Construindo YAML para sdnne04")
    print("4º Seminário Docomomo Norte/Nordeste, Natal, 2012")
    print("=" * 70)

    # 1. List source PDFs
    print("\n1. Listando PDFs fonte...")
    if not os.path.exists(FONTES_DIR):
        print(f"   ERRO: Diretório fontes/ não existe: {FONTES_DIR}")
        return

    src_files = sorted([f for f in os.listdir(FONTES_DIR) if f.startswith('DOCONATAL') and f.endswith('.pdf')])
    print(f"   {len(src_files)} PDFs encontrados em fontes/")

    # 2. Create pdfs/ directory
    os.makedirs(PDFS_DIR, exist_ok=True)

    # 3. Build mapping: sequential numbering (skip gaps in original)
    file_mapping = []
    for seq, src_file in enumerate(src_files, 1):
        new_name = f'sdnne04-{seq:03d}.pdf'
        file_mapping.append({
            'original': src_file,
            'new': new_name,
            'seq': seq,
        })

    print(f"   Mapeamento: {len(file_mapping)} PDFs -> sdnne04-001 a sdnne04-{len(file_mapping):03d}")

    # Print mapping
    print("\n   Mapeamento original -> novo:")
    for m in file_mapping:
        print(f"     {m['original']} -> {m['new']}")

    # 4. Process each PDF
    print("\n2. Processando artigos...")
    articles = []
    all_eixos = {}
    stats = {
        'total': 0, 'with_authors': 0, 'with_resumo': 0,
        'with_abstract_en': 0, 'with_keywords': 0, 'with_keywords_en': 0,
        'with_references': 0, 'total_authors': 0, 'copied': 0,
        'with_eixo': 0,
    }

    for entry in file_mapping:
        src_file = entry['original']
        new_file = entry['new']
        seq = entry['seq']
        article_id = f'sdnne04-{seq:03d}'
        stats['total'] += 1

        src_path = os.path.join(FONTES_DIR, src_file)
        dest_path = os.path.join(PDFS_DIR, new_file)

        print(f"\n--- {article_id} ({src_file})")

        # Copy PDF
        if not os.path.exists(dest_path):
            shutil.copy2(src_path, dest_path)
            stats['copied'] += 1
            print(f"   Copiado: {src_file} -> {new_file}")

        # Extract text
        lines = extract_text_raw(src_path)
        if lines is None:
            print(f"   ERRO: Não foi possível extrair texto")
            articles.append(_empty_article(article_id, new_file, src_file))
            continue

        pages_count = get_pdf_page_count(src_path)

        # Title
        full_title = extract_title(lines)
        if full_title:
            title, subtitle = separate_title_subtitle(full_title)
        else:
            title = f"[Título não extraído - {src_file}]"
            subtitle = None
            print(f"   AVISO: Título não extraído")

        # Apply en-dash rule: " - " -> " — "
        if title:
            title = re.sub(r' - ', ' — ', title)
        if subtitle:
            subtitle = re.sub(r' - ', ' — ', subtitle)

        # Eixo
        eixo_raw = detect_eixo_from_text(lines)
        section_name, section_abbrev = normalize_eixo(eixo_raw)

        if eixo_raw:
            stats['with_eixo'] += 1
            if section_name not in all_eixos:
                all_eixos[section_name] = section_abbrev

        # Authors
        authors = parse_authors_from_header(lines, src_file)

        # Ensure all have emails
        for author in authors:
            if not author.get('email'):
                author['email'] = next_placeholder_email(author.get('familyname', ''))

        # Abstracts and keywords
        resumo = parse_resumo(lines)
        abstract_en = parse_abstract_en(lines)
        keywords_pt = parse_keywords_pt(lines)
        keywords_en = parse_keywords_en(lines)
        references = parse_references(lines)

        # Stats
        if authors:
            stats['with_authors'] += 1
            stats['total_authors'] += len(authors)
        if resumo:
            stats['with_resumo'] += 1
        if abstract_en:
            stats['with_abstract_en'] += 1
        if keywords_pt:
            stats['with_keywords'] += 1
        if keywords_en:
            stats['with_keywords_en'] += 1
        if references:
            stats['with_references'] += 1

        # Build article dict
        article = OrderedDict()
        article['id'] = article_id
        article['title'] = title
        article['subtitle'] = subtitle
        article['authors'] = []
        for a in authors:
            autor = OrderedDict()
            autor['givenname'] = a['givenname']
            autor['familyname'] = a['familyname']
            autor['email'] = a['email']
            autor['affiliation'] = a.get('affiliation')
            autor['orcid'] = None
            autor['bio'] = None
            autor['country'] = a.get('country', 'BR')
            autor['primary_contact'] = a.get('primary_contact', False)
            article['authors'].append(dict(autor))
        article['section'] = section_name
        article['abstract'] = resumo
        article['abstract_en'] = abstract_en
        article['keywords'] = keywords_pt if keywords_pt else []
        article['keywords_en'] = keywords_en if keywords_en else []
        article['references'] = references if references else []
        article['locale'] = 'pt-BR'
        article['file'] = new_file
        article['file_original'] = src_file
        article['pages_count'] = pages_count
        article['pages'] = None

        articles.append(dict(article))

        # Print summary
        n_auth = len(authors)
        has_res = 'sim' if resumo else 'NAO'
        has_abs = 'sim' if abstract_en else 'NAO'
        has_kw = 'sim' if keywords_pt else 'NAO'
        has_ref = len(references)
        print(f"   Título: {title[:70]}")
        if subtitle:
            print(f"   Subtítulo: {subtitle[:70]}")
        print(f"   Eixo: {section_name}")
        print(f"   Autores: {n_auth} | Resumo: {has_res} | Abstract: {has_abs} | KW: {has_kw} | Refs: {has_ref} | Págs: {pages_count}")
        if authors:
            for a in authors:
                aff = a.get('affiliation') or '?'
                print(f"     - {a['givenname']} {a['familyname']} ({aff}) [{a['email']}]")

    # 5. Build sections list
    sections = []
    for name, abbrev in sorted(all_eixos.items(), key=lambda x: x[1]):
        sections.append(OrderedDict([
            ('title', name),
            ('abbrev', abbrev),
        ]))

    # 6. Build YAML
    print("\n" + "=" * 70)
    print("Montando YAML final...")

    yaml_data = OrderedDict()

    # Issue header
    issue = OrderedDict()
    issue['slug'] = 'sdnne04'
    issue['title'] = '4º Seminário Docomomo Norte/Nordeste, Natal, 2012'
    issue['subtitle'] = 'Arquitetura em cidades "sempre novas": modernismo, projeto e patrimônio'
    issue['location'] = 'Natal, RN'
    issue['year'] = 2012
    issue['volume'] = 3
    issue['number'] = 4
    issue['isbn'] = '978-85-425-0625-9'
    issue['publisher'] = 'EDUFRN'
    issue['editors'] = [
        'Rubenilson Brazão Teixeira',
        'George Alexandre Ferreira Dantas',
    ]
    issue['description'] = (
        'TEIXEIRA, Rubenilson Brazão; DANTAS, George Alexandre Ferreira (Org.). '
        'Arquitetura em cidades "sempre novas": modernismo, projeto e patrimônio. '
        'Natal: EDUFRN, 2016. ISBN 978-85-425-0625-9.'
    )
    issue['date_published'] = '2012-05-29'
    issue['sections'] = [dict(s) for s in sections]

    yaml_data['issue'] = dict(issue)
    yaml_data['articles'] = articles

    with open(YAML_OUT, 'w', encoding='utf-8') as f:
        yaml.dump(dict(yaml_data), f, Dumper=OrderedDumper,
                  default_flow_style=False, allow_unicode=True,
                  width=10000, sort_keys=False)

    print(f"   YAML salvo em: {YAML_OUT}")

    # 7. Summary
    print("\n" + "=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    print(f"Total de artigos: {stats['total']}")
    print(f"PDFs copiados: {stats['copied']}")

    print(f"\nPor eixo:")
    eixo_counts = {}
    for a in articles:
        sec = a.get('section', 'Sem eixo')
        eixo_counts[sec] = eixo_counts.get(sec, 0) + 1
    for eixo, n in sorted(eixo_counts.items()):
        print(f"  {eixo}: {n} artigos")

    print(f"\nMetadados extraídos:")
    print(f"  Com título: {len([a for a in articles if a.get('title') and not a['title'].startswith('[')])}/{stats['total']}")
    print(f"  Com autores: {stats['with_authors']}/{stats['total']}")
    print(f"  Com eixo: {stats['with_eixo']}/{stats['total']}")
    print(f"  Com resumo (PT): {stats['with_resumo']}/{stats['total']}")
    print(f"  Com abstract (EN): {stats['with_abstract_en']}/{stats['total']}")
    print(f"  Com keywords (PT): {stats['with_keywords']}/{stats['total']}")
    print(f"  Com keywords (EN): {stats['with_keywords_en']}/{stats['total']}")
    print(f"  Com referências: {stats['with_references']}/{stats['total']}")
    print(f"  Total de autores: {stats['total_authors']}")

    print(f"\nArquivos:")
    print(f"  YAML: {YAML_OUT}")
    print(f"  PDFs: {PDFS_DIR}/")

    # Print file mapping
    print(f"\nMapeamento de arquivos:")
    for m in file_mapping:
        print(f"  {m['original']} -> {m['new']}")


def _empty_article(article_id, new_file, src_file):
    """Create an empty article placeholder."""
    return {
        'id': article_id,
        'title': f'[Erro de extração - {src_file}]',
        'subtitle': None,
        'authors': [],
        'section': 'Sem eixo',
        'abstract': None,
        'abstract_en': None,
        'keywords': [],
        'keywords_en': [],
        'references': [],
        'locale': 'pt-BR',
        'file': new_file,
        'file_original': src_file,
        'pages_count': None,
        'pages': None,
    }


if __name__ == '__main__':
    process_articles()
