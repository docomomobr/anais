#!/usr/bin/env python3
"""
construir_yaml.py - Constrói YAML de artigos para sdnne05
5º Seminário Docomomo Norte/Nordeste, Fortaleza, 2014

Lê o mapeamento de URLs (sdnne05_urls.json) para obter título e eixo,
extrai metadados dos PDFs via pdftotext, renomeia para sdnne05-NNN.pdf
e gera o YAML consolidado.
"""

import os
import sys
import re
import json
import subprocess
import shutil
import yaml
from collections import OrderedDict

BASE_DIR = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/nne/sdnne05'
PDF_SRC_DIR = os.path.join(BASE_DIR, 'pdfs')
JSON_FILE = os.path.join(BASE_DIR, 'sdnne05_urls.json')
YAML_OUT = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/nne/sdnne05.yaml'

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


def next_placeholder_email():
    """Generate next placeholder email."""
    EMAIL_COUNTER[0] += 1
    return f"sem-email-{EMAIL_COUNTER[0]}@example.com"


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
    """Split full name into givenname/familyname (Brazilian convention)."""
    name = full_name.strip()
    name = re.sub(r'\s+', ' ', name)
    if not name:
        return '', ''
    words = name.split()
    if len(words) == 1:
        return capitalize_name(name), ''
    familyname = words[-1]
    givenname = ' '.join(words[:-1])
    return capitalize_name(givenname), capitalize_name(familyname)


# ── Affiliation extraction ───────────────────────────────────

def extract_affiliation(text):
    """Extract institutional affiliation abbreviation."""
    patterns = [
        (r'Pontif.cia Universidad Cat.lica de Chile|PUC.*Chile', 'PUC-Chile'),
        (r'PPG-FAU-UnB|PPG FAU UnB', 'PPG-FAU-UnB'),
        (r'FAU-?UnB|FAU UnB|FAU/UnB|FAU.UnB', 'FAU-UnB'),
        (r'FAUUSP|FAU-?USP|FAU/USP', 'FAUUSP'),
        (r'PPGAU.*FAUFBA|PPGAU.*UFBA|PPGAU/FAU', 'FAUFBA'),
        (r'FAUFBA|FAU-?UFBA|FAU/UFBA|Faculdade de Arquitetura.*UFBA', 'FAUFBA'),
        (r'IAU-?USP|IAU/USP', 'IAU-USP'),
        (r'FA-?UFRGS|FA UFRGS|FA/UFRGS', 'FA-UFRGS'),
        (r'PROPAR-?UFRGS|PROPAR UFRGS', 'PROPAR-UFRGS'),
        (r'MDU.*UFPE', 'MDU-UFPE'),
        (r'DAU.*UFPE|Departamento de Arquitetura.*UFPE', 'DAU-UFPE'),
        (r'Hochschule Ostwestfalen|Detmolder Schule|hs-owl', 'HS-OWL'),
        (r'Universite? Paris|Sorbonne', 'Univ. Paris 1'),
        (r'UNISINOS|Universidade do Vale do Rio dos Sinos', 'UNISINOS'),
        (r'IFS.*Sergipe|IFS-SE', 'IFS'),
        (r'UFS.*Sergipe|UFS-SE', 'UFS'),
        (r'Unifor\b', 'UNIFOR'),
        (r'UNICAP', 'UNICAP'),
        (r'UFCG', 'UFCG'),
        (r'UFBA', 'UFBA'),
        (r'UFPE', 'UFPE'),
        (r'UFRN', 'UFRN'),
        (r'UFPB', 'UFPB'),
        (r'UFPI', 'UFPI'),
        (r'UFPA', 'UFPA'),
        (r'UNIFAP|Universidade Federal do Amap', 'UNIFAP'),
        (r'UnB\b', 'UnB'),
        (r'UFRGS', 'UFRGS'),
        (r'UFRJ', 'UFRJ'),
        (r'UFMG', 'UFMG'),
        (r'Universidade Federal do Cear|UFC\b', 'UFC'),
        (r'USP\b|Universidade de S.o Paulo', 'USP'),
        (r'UFS\b', 'UFS'),
        (r'UFAL', 'UFAL'),
        (r'Faculdade de Macap|FAMA\b', 'FAMA'),
        (r'Faculdade Seama', 'SEAMA'),
        (r'OAB', 'OAB'),
    ]
    for pattern, abbrev in patterns:
        if re.search(pattern, text, re.I):
            return abbrev
    return None


# ── Author parsing (email-anchor approach) ───────────────────

def is_bio_line(text):
    """Check if a line looks like a bio/affiliation description (not a name)."""
    text_lower = text.lower().strip()
    # Lines starting with academic titles, degrees, etc.
    bio_starters = [
        r'^arquitet[ao]\b', r'^engenheiro?a?\b', r'^urbanista\b',
        r'^bacharela?\b', r'^graduand[ao]\b', r'^graduação\b',
        r'^mestr[ae]\b', r'^mestrand[ao]\b', r'^doutor[ao]?\b', r'^doutoranda?\b',
        r'^profa?\.?\s', r'^professor', r'^pesquisador',
        r'^especialista\b', r'^coordenador',
        r'^docente\b', r'^servidor', r'^membro\b',
        r'^discente\b', r'^concluinte\b', r'^orientador',
        r'^livre.docente\b',
    ]
    for pat in bio_starters:
        if re.match(pat, text_lower):
            return True
    # Lines with institutional keywords
    if any(kw in text_lower for kw in ['universidade', 'programa de pós', 'departamento de',
                                        'faculdade de', 'laboratório', 'instituto',
                                        'escola de', 'grupo de pesquisa']):
        return True
    # Address lines
    if re.match(r'^(rua|r\.|av\.|avenida|alameda|pra[çc]a|travessa|rod\.)\s', text_lower):
        return True
    # CEP / postal code
    if re.match(r'^\d{5}[-.]?\d{3}', text_lower):
        return True
    # Phone numbers
    if re.match(r'^\(\d{2,3}\)', text_lower):
        return True
    # Lines that are just addresses (number + street name)
    if re.match(r'^\d+\s+(rua|r\.|av\.|alameda)', text_lower):
        return True
    return False


def is_name_line(text):
    """Check if a line looks like a person's name.

    Criteria: short-ish line, no @, not a bio line,
    looks like a Brazilian/Hispanic personal name.
    """
    text = text.strip()
    if not text or len(text) > 80:
        return False
    if '@' in text:
        return False
    if is_bio_line(text):
        return False

    words = text.split()
    if len(words) < 2 or len(words) > 8:
        return False

    # Reject common non-name patterns
    if re.match(r'^(Eixo|Hist|An.lise|A Vig|o Norte|5.\s*Semin)', text, re.I):
        return False

    # Reject English title lines (common patterns)
    if re.match(r'^(The |Modern |Diffusion|Beyond |An |Ouro |Two |Strategies|'
                r'Metropolis|Lina |How |Heritage|Interventions|Under |'
                r'Innovation|Crea|Still|THE |UNDER|BEYOND|MODERN|TWO|STRATEGIES)', text):
        return False
    # Reject lines that look like English titles (many English words)
    english_words = {'the', 'of', 'in', 'and', 'for', 'from', 'to', 'on',
                     'about', 'between', 'through', 'with', 'its', 'an',
                     'modern', 'architecture', 'building', 'project', 'design',
                     'case', 'study', 'heritage', 'urban', 'city', 'residential',
                     'university', 'preservation', 'conservation', 'history'}
    lower_words = {w.lower().rstrip('.,;:') for w in words}
    english_count = len(lower_words & english_words)
    if english_count >= 3:
        return False

    # Reject lines ending with common title punctuation patterns
    if text.endswith(',') or text.endswith('...'):
        return False

    # First word should start with uppercase
    if not words[0][0].isupper() and not words[0].startswith('"') and not words[0].startswith('('):
        return False

    # Allow "(Coautor)" or "(N)" in names
    clean = re.sub(r'\s*\((?:Coautor|coautor|\d+)\)\s*', ' ', text).strip()
    # After cleaning, reject if it still has brackets
    if any(c in clean for c in ['[', ']', '{', '}']):
        return False

    # Names should have mostly short words (not long institutional/descriptive words)
    long_words = [w for w in words if len(w) > 12 and w.lower() not in PARTICLES]
    if long_words:
        return False

    # Check: names typically have title-case words (first letter upper, rest lower)
    # except for particles and initials
    name_like_count = 0
    for w in words:
        w_clean = w.rstrip('.,;:')
        if w_clean.lower() in PARTICLES:
            name_like_count += 1
        elif re.match(r'^[A-ZÀ-Ú][a-zà-ú]+$', w_clean):
            name_like_count += 1
        elif re.match(r'^[A-ZÀ-Ú]\.$', w_clean):  # initial
            name_like_count += 1
        elif w_clean in ('Jr', 'Jr.', 'Neto', 'Filho', 'II', 'III'):
            name_like_count += 1

    # At least 60% of words should look name-like
    if len(words) > 0 and name_like_count / len(words) < 0.5:
        return False

    return True


def parse_authors_from_header(lines):
    """Parse authors from the header section before Resumo.

    Strategy: find all email addresses in the header. For each email,
    the author name is the first name-like line in the block above it.
    Bio/affiliation lines sit between the name and the email.
    """
    # Find Resumo line
    resumo_idx = None
    for i, line in enumerate(lines):
        text = line.strip().lower()
        if text in ('resumo', 'resumo:', 'resumen', 'resumen:'):
            resumo_idx = i
            break

    if resumo_idx is None:
        # Try to find it with less strict matching
        for i, line in enumerate(lines):
            if re.match(r'^\s*Resumo\s*$', line, re.I):
                resumo_idx = i
                break

    if resumo_idx is None:
        return []

    header = lines[:resumo_idx]

    # Find all lines with email addresses
    email_line_indices = []
    for i, line in enumerate(header):
        if re.search(r'[\w.+-]+@[\w.-]+\.\w{2,}', line):
            email_line_indices.append(i)

    # Check for numbered format: (1) LASTNAME, Firstname.
    has_numbered = any(re.match(r'^\s*\(\d+\)\s*[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ]', header[i].strip()) for i in range(len(header)))
    if has_numbered:
        numbered_authors = parse_numbered_authors(header)
        if numbered_authors:
            return numbered_authors

    if not email_line_indices:
        return []

    authors = []

    # For each email line, find the author block
    for ei, email_idx in enumerate(email_line_indices):
        email_line = header[email_idx].strip()
        email_match = re.search(r'([\w.+-]+@[\w.-]+\.\w{2,})', email_line)
        email = email_match.group(1).lower() if email_match else None

        # Determine the start of this author's block
        block_start = email_line_indices[ei - 1] + 1 if ei > 0 else 0
        block_end = email_idx + 1

        block = [(i, header[i].strip()) for i in range(block_start, block_end)]

        author_name = None
        bio_lines = []

        # Scan BACKWARDS from the email line to find the name
        # The name is the closest name-like line above the bio/email
        # Strategy: go backwards, skip empty/bio lines, find name
        candidate_name = None
        for bi in range(len(block) - 1, -1, -1):
            line_idx, text = block[bi]
            if not text:
                continue

            # Skip the email line itself
            if '@' in text:
                # But extract bio text before the email on this line
                bio_part = re.sub(r'[,;\s]*e?-?mail\s*:?\s*[\w.+-]+@[\w.-]+\.\w+', '', text, flags=re.I)
                bio_part = re.sub(r'[\w.+-]+@[\w.-]+\.\w+', '', bio_part)
                bio_part = bio_part.strip().rstrip(',').rstrip(';').strip()
                if bio_part:
                    bio_lines.append(bio_part)
                continue

            # Skip Eixo headers
            if re.match(r'^Eixo Tem', text, re.I):
                continue
            if re.match(r'^(Hist.ria e Historiografia|An.lise cr.tica|A Vig.ncia|o Norte e o Nordeste)', text, re.I):
                continue

            # If this is a bio line, collect it
            if is_bio_line(text):
                bio_lines.append(text)
                continue

            # If this is a name line, take it as the candidate
            if is_name_line(text):
                candidate_name = text
                break
            else:
                # Not a name and not a bio - probably title or other non-author text
                # Stop searching backwards
                break

        if candidate_name:
            # Clean up the name
            cleaned = re.sub(r'\s*\(Coautor\)\s*', '', candidate_name, flags=re.I).strip()
            cleaned = re.sub(r'\s*\(\d+\)\s*', '', cleaned).strip()
            # Handle "LASTNAME, Firstname." format
            if re.match(r'^[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][A-ZÀÁÂÃÉÊÍÓÔÕÚÇa-zàáâãéêíóôõúç\s]+,', cleaned):
                parts = cleaned.split(',', 1)
                last = parts[0].strip().rstrip('.')
                first = parts[1].strip().rstrip('.')
                author_name = f"{first} {last}"
            else:
                author_name = cleaned.rstrip('.')
        else:
            # Last resort: check if there's a line right above the bio that looks name-ish
            # even if is_name_line rejected it
            for bi in range(len(block) - 1, -1, -1):
                line_idx, text = block[bi]
                if not text or '@' in text:
                    continue
                if is_bio_line(text):
                    continue
                # Try it as a name anyway if it's short and title-case
                if len(text) < 60 and len(text.split()) >= 2:
                    author_name = text.rstrip('.')
                break

        # Extract affiliation from bio lines + email line
        all_bio_text = ' '.join(bio_lines) + ' ' + email_line
        affiliation = extract_affiliation(all_bio_text)

        # Detect country
        country = 'BR'
        if re.search(r'Chile', all_bio_text, re.I):
            country = 'CL'
        elif re.search(r'Alemania|Deutschland|Germany|hs-owl', all_bio_text, re.I):
            country = 'DE'

        if author_name:
            givenname, familyname = split_given_family(author_name)
            authors.append({
                'givenname': givenname,
                'familyname': familyname,
                'email': email,
                'affiliation': affiliation,
                'country': country,
                'primary_contact': len(authors) == 0,
            })

    return authors


def parse_numbered_authors(header_lines):
    """Parse authors in numbered format: (1) LASTNAME, Firstname.

    Handles formats like:
      (1) NASCIMENTO, José Clewton do.
      Bio...; email@example.com
    """
    authors = []
    text = '\n'.join([l.strip() for l in header_lines])

    # More flexible pattern: (N) LASTNAME, Firstname [do/da/de/etc].
    pattern = r'\(\d+\)\s*([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][A-ZÀÁÂÃÉÊÍÓÔÕÚÇ\s]*?),\s*([^.\n]+(?:\.\s*)?)'
    for match in re.finditer(pattern, text):
        raw_family = match.group(1).strip()
        raw_given = match.group(2).strip().rstrip('.')

        familyname = capitalize_name(raw_family)
        givenname = capitalize_name(raw_given)

        # Look for email after this match
        after = text[match.end():match.end() + 500]
        # Stop at next numbered author
        next_num = re.search(r'\(\d+\)\s*[A-Z]', after)
        if next_num:
            after = after[:next_num.start()]

        email_match = re.search(r'([\w.+-]+@[\w.-]+\.\w{2,})', after)
        email = email_match.group(1).lower() if email_match else None
        affiliation = extract_affiliation(after[:300])

        country = 'BR'
        if re.search(r'Chile', after[:300], re.I):
            country = 'CL'

        authors.append({
            'givenname': givenname,
            'familyname': familyname,
            'email': email,
            'affiliation': affiliation,
            'country': country,
            'primary_contact': len(authors) == 0,
        })

    return authors


# ── Metadata extraction ──────────────────────────────────────

def parse_resumo(lines):
    """Extract Portuguese abstract (Resumo)."""
    resumo_lines = []
    in_resumo = False

    for line in lines:
        text = line.strip()
        text_lower = text.lower().strip()

        if text_lower in ('resumo', 'resumo:'):
            in_resumo = True
            continue

        if in_resumo:
            if text_lower.startswith('palavras-chave') or text_lower.startswith('palavras chave'):
                break
            if text_lower in ('resumen', 'resumen:', 'abstract', 'abstract:'):
                break
            kw_match = re.search(r'Palavras-?chave\s*:', text, re.I)
            if kw_match:
                before = text[:kw_match.start()].strip()
                if before:
                    resumo_lines.append(before)
                break
            if not text:
                continue
            if re.match(r'^5.\s*Semin.rio\s+DOCOMOMO', text, re.I):
                break
            if re.match(r'^\d+$', text):
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

        if text_lower in ('abstract', 'abstract:'):
            in_abstract = True
            continue

        if in_abstract:
            if text_lower.startswith('keywords') or text_lower.startswith('key words') or text_lower.startswith('key-words'):
                break
            kw_match = re.search(r'Keywords?\s*:', text, re.I)
            if kw_match:
                before = text[:kw_match.start()].strip()
                if before:
                    abstract_lines.append(before)
                break
            if text_lower in ('resumo', 'resumo:'):
                break
            if not text:
                continue
            if re.match(r'^5.\s*Semin.rio\s+DOCOMOMO', text, re.I):
                break
            if re.match(r'^\d+$', text):
                continue
            abstract_lines.append(text)

    if abstract_lines:
        abstract = ' '.join(abstract_lines)
        abstract = re.sub(r'\s+', ' ', abstract).strip()
        return abstract
    return None


def parse_keywords_pt(lines):
    """Extract Portuguese keywords."""
    for line in lines:
        text = line.strip()
        if re.match(r'^Palavras-?chave', text, re.I):
            kw_text = re.sub(r'^Palavras-?chave\s*:\s*', '', text, flags=re.I)
            kw_text = kw_text.strip().rstrip('.')
            if not kw_text:
                continue
            if ';' in kw_text:
                keywords = [k.strip().rstrip('.') for k in kw_text.split(';') if k.strip()]
            elif '. ' in kw_text:
                keywords = [k.strip().rstrip('.') for k in re.split(r'\.\s+', kw_text) if k.strip()]
            else:
                keywords = [k.strip().rstrip('.') for k in kw_text.split(',') if k.strip()]
            keywords = [k for k in keywords if k and len(k) > 1]
            if keywords:
                return keywords
    return []


def parse_keywords_en(lines):
    """Extract English keywords."""
    for line in lines:
        text = line.strip()
        if re.match(r'^Key-?words?', text, re.I):
            kw_text = re.sub(r'^Key-?words?\s*:\s*', '', text, flags=re.I)
            kw_text = kw_text.strip().rstrip('.')
            if not kw_text:
                continue
            if ';' in kw_text:
                keywords = [k.strip().rstrip('.') for k in kw_text.split(';') if k.strip()]
            elif '. ' in kw_text:
                keywords = [k.strip().rstrip('.') for k in re.split(r'\.\s+', kw_text) if k.strip()]
            else:
                keywords = [k.strip().rstrip('.') for k in kw_text.split(',') if k.strip()]
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
        if text_lower in ('bibliografia', 'bibliografia:'):
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
            if re.match(r'^5.\s*Semin.rio\s+DOCOMOMO', text, re.I):
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


# ── Title extraction ─────────────────────────────────────────

def extract_full_title_from_pdf(lines, json_title):
    """Extract the full title from the PDF text.

    The PDF title may be more complete than the (possibly truncated) JSON title.
    """
    json_prefix = json_title.strip()[:20].upper()

    title_lines = []
    in_title = False

    for i, line in enumerate(lines):
        text = line.strip()
        if not text:
            if in_title and title_lines:
                break
            continue

        # Skip Eixo header lines
        if re.match(r'^Eixo Tem.tico', text, re.I):
            continue
        if re.match(r'^(Hist.ria e Historiografia|An.lise cr.tica|A Vig.ncia)', text, re.I):
            continue
        if re.match(r'^(o Norte e o Nordeste)', text, re.I):
            continue

        if not in_title:
            text_upper = text.upper()
            if json_prefix and text_upper.startswith(json_prefix[:15]):
                in_title = True
                title_lines.append(text)
                continue
        else:
            # Check if still part of title
            alpha = re.sub(r'[^a-zA-ZÀ-ÿ]', '', text)
            if alpha:
                upper_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha)
                if upper_ratio > 0.5 and len(text) > 5:
                    title_lines.append(text)
                    continue
            break

    if title_lines:
        full_title = ' '.join(title_lines)
        full_title = re.sub(r'\s+', ' ', full_title).strip()
        return full_title
    return None


def separate_title_subtitle(full_title):
    """Separate title and subtitle at first ':'."""
    if ':' in full_title:
        idx = full_title.index(':')
        title = full_title[:idx].strip()
        subtitle = full_title[idx+1:].strip()
        if subtitle:
            return title, subtitle
    return full_title, None


def detect_locale(title, lines):
    """Detect article locale."""
    title_lower = title.lower() if title else ''
    if any(w in title_lower for w in ['arquitectura', 'patrimonio urbano', 'proyecto', 'ciudad']):
        return 'es'
    for line in lines[:50]:
        text = line.strip().lower()
        if text in ('resumen', 'resumen:'):
            return 'es'
        if text in ('resumo', 'resumo:'):
            return 'pt-BR'
    return 'pt-BR'


# ── URL mapping ──────────────────────────────────────────────

def load_url_mapping():
    """Load the URL-to-metadata mapping from JSON."""
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    mapping = []
    for entry in entries:
        url = entry['url']
        filename = url.split('/')[-1]
        mapping.append({
            'filename': filename,
            'eixo': entry['eixo'],
            'title_json': entry['title'],
            'url': url,
        })
    return mapping


# ── Main processing ──────────────────────────────────────────

def process_articles():
    print("=" * 70)
    print("Construindo YAML para sdnne05")
    print("5º Seminário Docomomo Norte/Nordeste, Fortaleza, 2014")
    print("=" * 70)

    # 1. Load URL mapping
    print("\n1. Carregando mapeamento de URLs...")
    mapping = load_url_mapping()
    print(f"   {len(mapping)} entradas no JSON")

    # 2. Verify PDFs exist
    print("\n2. Verificando PDFs...")
    pdf_files = set(os.listdir(PDF_SRC_DIR))
    missing = [e['filename'] for e in mapping if e['filename'] not in pdf_files]
    if missing:
        print(f"   AVISO: {len(missing)} PDFs faltando!")
        for m in missing:
            print(f"     - {m}")
    else:
        print(f"   Todos os {len(mapping)} PDFs encontrados")

    # 3. Sort by eixo then original order
    eixo_order = {'Eixo A': 0, 'Eixo B': 1, 'Eixo C': 2}
    for i, entry in enumerate(mapping):
        entry['original_order'] = i
    sorted_entries = sorted(mapping, key=lambda e: (eixo_order.get(e['eixo'], 99), e['original_order']))

    # 4. Process each PDF
    print("\n3. Processando artigos...")
    articles = []
    stats = {
        'total': 0, 'with_authors': 0, 'with_resumo': 0,
        'with_abstract_en': 0, 'with_keywords': 0, 'with_keywords_en': 0,
        'with_references': 0, 'total_authors': 0, 'renamed': 0,
    }

    for seq, entry in enumerate(sorted_entries, 1):
        article_id = f'sdnne05-{seq:03d}'
        filename = entry['filename']
        eixo = entry['eixo']
        json_title = entry['title_json']
        stats['total'] += 1

        src_path = os.path.join(PDF_SRC_DIR, filename)
        new_filename = f'{article_id}.pdf'
        dest_path = os.path.join(PDF_SRC_DIR, new_filename)

        print(f"\n--- {article_id} [{eixo}]: {json_title[:65]}...")

        # Determine which file to read
        read_path = src_path if os.path.exists(src_path) else dest_path
        if not os.path.exists(read_path):
            print(f"   ERRO: PDF não encontrado")
            continue

        # Extract text
        lines = extract_text_raw(read_path)
        if lines is None:
            print(f"   ERRO: Não foi possível extrair texto")
            continue

        pages_count = get_pdf_page_count(read_path)

        # Title
        full_title_pdf = extract_full_title_from_pdf(lines, json_title)
        full_title = full_title_pdf if full_title_pdf else json_title
        title, subtitle = separate_title_subtitle(full_title)

        # Locale
        locale = detect_locale(title, lines)

        # Authors
        authors = parse_authors_from_header(lines)

        # Ensure all have emails
        for author in authors:
            if not author.get('email'):
                author['email'] = next_placeholder_email()

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

        # Copy/rename PDF
        if os.path.exists(src_path) and not os.path.exists(dest_path):
            shutil.copy2(src_path, dest_path)
            stats['renamed'] += 1
            print(f"   PDF copiado: {filename} -> {new_filename}")
        elif os.path.exists(dest_path):
            pass  # already renamed

        # Build article dict
        article = OrderedDict()
        article['id'] = article_id
        article['title'] = title
        article['subtitle'] = subtitle
        article['locale'] = locale
        article['section'] = eixo

        autores_list = []
        for a in authors:
            autor = OrderedDict()
            autor['givenname'] = a['givenname']
            autor['familyname'] = a['familyname']
            autor['email'] = a['email']
            autor['affiliation'] = a.get('affiliation')
            autor['country'] = a.get('country', 'BR')
            autor['primary_contact'] = a.get('primary_contact', False)
            autores_list.append(dict(autor))

        article['authors'] = autores_list
        article['abstract'] = resumo
        article['abstract_en'] = abstract_en
        article['keywords'] = keywords_pt if keywords_pt else []
        article['keywords_en'] = keywords_en if keywords_en else []
        article['file'] = new_filename
        article['file_original'] = filename
        article['pages_count'] = pages_count
        article['references'] = references if references else []

        articles.append(dict(article))

        # Print summary
        n_auth = len(authors)
        has_res = 'sim' if resumo else 'NAO'
        has_abs = 'sim' if abstract_en else 'NAO'
        has_kw = 'sim' if keywords_pt else 'NAO'
        has_ref = len(references)
        print(f"   Título: {title[:65]}")
        if subtitle:
            print(f"   Subtítulo: {subtitle[:65]}")
        print(f"   Autores: {n_auth} | Resumo: {has_res} | Abstract: {has_abs} | KW: {has_kw} | Refs: {has_ref} | Págs: {pages_count}")
        if authors:
            for a in authors:
                aff = a.get('affiliation', '?')
                print(f"     - {a['givenname']} {a['familyname']} ({aff}) [{a['email']}]")

    # 5. Build YAML
    print("\n" + "=" * 70)
    print("Montando YAML final...")

    yaml_data = OrderedDict()
    yaml_data['slug'] = 'sdnne05'
    yaml_data['volume'] = 1
    yaml_data['number'] = 5
    yaml_data['evento'] = OrderedDict([
        ('titulo', '5º Seminário Docomomo Norte/Nordeste'),
        ('tema', None),
        ('local', 'Fortaleza, CE'),
        ('data', 2014),
        ('organizacao', []),
    ])
    yaml_data['publicacao'] = OrderedDict([
        ('ficha_catalografica', '5° Seminário Docomomo Norte/Nordeste: anais [recurso eletrônico].\nFortaleza: [Editora], 2014.\n'),
        ('isbn', None),
        ('editora', None),
        ('ano', 2014),
    ])
    yaml_data['fontes'] = OrderedDict([
        ('docomomobrasil', None),
        ('externa', OrderedDict([
            ('url', 'https://docomomoceara.wixsite.com/docomomoceara/eixo-a'),
            ('descricao', 'Site Docomomo Ceará - anais organizados por eixo temático'),
        ])),
    ])
    yaml_data['status'] = 'disponivel_externo'
    yaml_data['contato'] = OrderedDict([
        ('instituicao', 'Núcleo Docomomo CE'),
        ('notas', 'Buscar dados catalográficos completos'),
    ])
    yaml_data['artigos'] = articles

    with open(YAML_OUT, 'w', encoding='utf-8') as f:
        f.write('# 5º Seminário Docomomo Norte/Nordeste - Fortaleza (2014)\n')
        yaml.dump(dict(yaml_data), f, Dumper=OrderedDumper,
                  default_flow_style=False, allow_unicode=True,
                  width=10000, sort_keys=False)

    print(f"   YAML salvo em: {YAML_OUT}")

    # 6. Summary
    print("\n" + "=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    print(f"Total de artigos: {stats['total']}")
    print(f"PDFs renomeados: {stats['renamed']}")

    print(f"\nPor eixo:")
    for eixo in ['Eixo A', 'Eixo B', 'Eixo C']:
        n = len([a for a in articles if a.get('section') == eixo])
        print(f"  {eixo}: {n} artigos")

    print(f"\nMetadados extraídos:")
    print(f"  Com título: {len([a for a in articles if a.get('title')])}/{stats['total']}")
    print(f"  Com autores: {stats['with_authors']}/{stats['total']}")
    print(f"  Com resumo (PT): {stats['with_resumo']}/{stats['total']}")
    print(f"  Com abstract (EN): {stats['with_abstract_en']}/{stats['total']}")
    print(f"  Com keywords (PT): {stats['with_keywords']}/{stats['total']}")
    print(f"  Com keywords (EN): {stats['with_keywords_en']}/{stats['total']}")
    print(f"  Com referências: {stats['with_references']}/{stats['total']}")
    print(f"  Total de autores: {stats['total_authors']}")

    locales = {}
    for a in articles:
        loc = a.get('locale', 'pt-BR')
        locales[loc] = locales.get(loc, 0) + 1
    print(f"\nIdiomas:")
    for loc, count in sorted(locales.items()):
        print(f"  {loc}: {count}")

    print(f"\nArquivos:")
    print(f"  YAML: {YAML_OUT}")
    print(f"  PDFs: {PDF_SRC_DIR}/")


if __name__ == '__main__':
    process_articles()
