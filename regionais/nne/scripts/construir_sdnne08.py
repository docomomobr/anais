#!/usr/bin/env python3
"""
construir_yaml.py - Constroi YAML de artigos para sdnne08
8 Seminario Docomomo Norte/Nordeste, Palmas, 2021
"""

import os
import sys
import re
import subprocess
import shutil
import yaml
from collections import OrderedDict

try:
    import docx
except ImportError:
    print("ERRO: python-docx nao instalado. Execute: pip install python-docx")
    sys.exit(1)

BASE_DIR = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/nne/sdnne08'
SRC_DIR = os.path.join(BASE_DIR, 'Artigos Completos')
PDF_DIR = os.path.join(BASE_DIR, 'pdfs')
YAML_OUT = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/nne/sdnne08.yaml'

EXCLUDE_FILES = {
    'Copia de ALTERACOES ABNT.pdf',
    u'C\u00f3pia de ALTERA\u00c7\u00d5ES ABNT.pdf',
}


class OrderedDumper(yaml.SafeDumper):
    pass

def _dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

def _str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

OrderedDumper.add_representer(OrderedDict, _dict_representer)
OrderedDumper.add_representer(dict, _dict_representer)
OrderedDumper.add_representer(str, _str_representer)


def normalize_stem(filename):
    stem = os.path.splitext(filename)[0]
    stem = re.sub(r'\s*\(\d+\)\s*$', '', stem)
    stem = re.sub(r'\s*_artigo\s*$', '', stem, flags=re.I)
    stem = re.sub(r'\s*_ARTIGO COMPLETO com ID\s*$', '', stem, flags=re.I)
    stem = re.sub(r'\s*_ARTIGO COMPLETO\s*$', '', stem, flags=re.I)
    stem = re.sub(r'\s*com ID\s*$', '', stem, flags=re.I)
    stem = re.sub(r'\s*com identifica\S+\s*$', '', stem, flags=re.I)
    stem = re.sub(r'\s*- identificado\s*$', '', stem, flags=re.I)
    stem = re.sub(r'\s*- VIII DOCOMOMO N-NE\s*$', '', stem, flags=re.I)
    stem = re.sub(r'\s*- DOCOMOMO_Jul2021\s*$', '', stem, flags=re.I)
    stem = stem.strip().rstrip('.').rstrip('_')
    return stem


def catalog_files():
    files = os.listdir(SRC_DIR)
    docx_files = [f for f in files if f.lower().endswith('.docx')]
    pdf_files = [f for f in files if f.lower().endswith('.pdf') and f not in EXCLUDE_FILES]
    doc_files = [f for f in files if f.lower().endswith('.doc') and not f.lower().endswith('.docx')]

    articles = {}

    for f in docx_files:
        stem = normalize_stem(f)
        key = stem.lower()
        if key not in articles:
            articles[key] = {'stem': stem, 'docx': [], 'pdf': [], 'doc': []}
        articles[key]['docx'].append(f)

    for f in pdf_files:
        stem = normalize_stem(f)
        key = stem.lower()
        if key not in articles:
            articles[key] = {'stem': stem, 'docx': [], 'pdf': [], 'doc': []}
        articles[key]['pdf'].append(f)

    for f in doc_files:
        stem = normalize_stem(f)
        key = stem.lower()
        if key not in articles:
            articles[key] = {'stem': stem, 'docx': [], 'pdf': [], 'doc': []}
        articles[key]['doc'].append(f)

    # Merge entries that differ only by parens around text
    keys = list(articles.keys())
    merged = set()
    for i, k1 in enumerate(keys):
        if k1 in merged:
            continue
        for j, k2 in enumerate(keys):
            if j <= i or k2 in merged:
                continue
            clean1 = k1.replace('(', '').replace(')', '').replace('  ', ' ').strip()
            clean2 = k2.replace('(', '').replace(')', '').replace('  ', ' ').strip()
            if clean1 == clean2:
                articles[k1]['docx'].extend(articles[k2]['docx'])
                articles[k1]['pdf'].extend(articles[k2]['pdf'])
                articles[k1]['doc'].extend(articles[k2]['doc'])
                merged.add(k2)
    for k in merged:
        del articles[k]

    return articles


def extract_text_from_docx(filepath):
    try:
        doc = docx.Document(filepath)
        return [p.text for p in doc.paragraphs]
    except Exception as e:
        print(f"  AVISO: Erro ao ler docx {os.path.basename(filepath)}: {e}")
        return None


def extract_text_from_pdf(filepath):
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


def parse_title(lines):
    for line in lines:
        text = line.strip()
        if not text:
            continue
        if ':' in text:
            parts = text.split(':', 1)
            title = parts[0].strip()
            subtitle = parts[1].strip().rstrip('.')
            return title, subtitle
        else:
            return text.strip().rstrip('.'), None
    return None, None


def parse_authors_block(lines):
    authors = []
    author_text_parts = []
    title_lines_seen = 0
    past_titles = False

    for i, line in enumerate(lines):
        text = line.strip()
        if not text:
            if author_text_parts:
                break
            continue

        text_lower = text.lower()

        # Stop at resumo
        if text_lower in ('resumo', 'resumen', 'abstract', 'resumo:', 'resumen:', 'abstract:'):
            break
        if len(text) < 15 and 'resum' in text_lower:
            break

        # Skip first few lines = titles (pt, es, en)
        if not past_titles:
            title_lines_seen += 1
            if title_lines_seen <= 3:
                continue
            past_titles = True

        # Skip detail/address/bio lines
        if '@' in text and '.' in text and len(text) < 150:
            continue
        if 'orcid' in text_lower:
            continue
        if re.match(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$', text):
            continue
        if re.match(r'^(Rua|R\.|Av\.|Avenida|CEP|Campus|Endere)', text, re.I):
            continue
        if re.match(r'^\d{5}[-.]?\d{3}', text):
            continue
        if re.match(r'^\d+\.\s*(Doutora?|Mestra?|Graduand|Prof|P.s|Docente|Arquiteta?|Engenheira?)', text, re.I):
            continue
        if re.match(r'^(Doutora?nd|Mestra?nd|Graduand|Doutora?\s|Mestre\s|Profa?\.\s|P.s[- ])', text, re.I):
            continue
        if re.match(r'^(Concluinte|Orientadora?|Docente)', text, re.I):
            continue
        if re.match(r'^(Departamento|Dep\.|Centro de|Faculdade|Instituto|Programa|Escola)', text, re.I):
            continue
        if re.match(r'^E-mail:', text, re.I):
            continue
        if re.match(r'^http', text, re.I):
            continue
        if re.match(r'^[\d\s.,-]+$', text) and len(text) < 20:
            continue
        # Skip address-like short lines
        if re.match(r'^\d+\s+', text) and len(text) < 80 and (',' in text or '-' in text):
            continue
        # Skip "PALMAS, 2021" type lines
        if re.match(r'^[A-Z]+,\s*\d{4}$', text):
            continue

        # Detect author name patterns
        has_numbering = bool(re.search(r'\(\d+\)', text))
        has_semicolons = ';' in text
        # Check if mostly uppercase letters
        alpha_chars = re.sub(r'[^a-zA-Z\u00C0-\u00FF]', '', text)
        is_mostly_upper = len(alpha_chars) > 3 and sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars) > 0.6

        if has_numbering or (has_semicolons and is_mostly_upper) or (is_mostly_upper and len(text) > 5 and len(text) < 120):
            author_text_parts.append(text)
            continue

        if author_text_parts:
            break

    if not author_text_parts:
        return []

    raw_text = ' '.join(author_text_parts)
    raw_text = re.sub(r'\s*\(\d+\)\s*', ' ', raw_text)
    raw_text = re.sub(r'\s+', ' ', raw_text)

    raw_names = re.split(r'\s*;\s*', raw_text)

    for name in raw_names:
        name = name.strip().strip(';').strip(',').strip('.')
        if not name or len(name) < 3:
            continue
        author = parse_single_author_name(name)
        if author:
            authors.append(author)

    return authors


def parse_single_author_name(raw_name):
    name = raw_name.strip()
    name = re.sub(r'\s+', ' ', name)
    if not name or len(name) < 3:
        return None

    if ',' in name and name.index(',') < len(name) * 0.6:
        parts = name.split(',', 1)
        familyname = parts[0].strip()
        givenname = parts[1].strip()
    else:
        words = name.split()
        if len(words) == 1:
            return {'givenname': capitalize_name(name), 'familyname': ''}
        familyname = words[-1]
        givenname = ' '.join(words[:-1])

    givenname = capitalize_name(givenname)
    familyname = capitalize_name(familyname)

    return {'givenname': givenname, 'familyname': familyname}


def capitalize_name(name):
    particles = {'de', 'da', 'do', 'dos', 'das', 'e', 'del', 'von', 'di'}
    words = name.split()
    result = []
    for w in words:
        if w.lower() in particles:
            result.append(w.lower())
        elif w.isupper() and len(w) > 1:
            result.append(w.capitalize())
        else:
            result.append(w)
    return ' '.join(result)


def parse_author_details(lines):
    details = []
    current = {}

    for line in lines:
        text = line.strip()
        text_lower = text.lower()

        if not text:
            continue

        if text_lower in ('resumo', 'resumen', 'abstract', 'resumo:'):
            break
        if len(text) < 15 and 'resum' in text_lower:
            break

        num_match = re.match(r'^(\d+)\.\s*(.*)', text)
        if num_match:
            if current:
                details.append(current)
            current = {}
            remaining = num_match.group(2).strip()
            if remaining:
                current['bio'] = remaining
                aff = extract_affiliation(remaining)
                if aff:
                    current['affiliation'] = aff
            continue

        email_match = re.search(r'([\w.+-]+@[\w.-]+\.\w+)', text)
        if email_match and 'email' not in current:
            current['email'] = email_match.group(1).lower()
            continue

        orcid_match = re.search(r'(\d{4}-\d{4}-\d{4}-\d{3}[\dX])', text)
        if orcid_match:
            current['orcid'] = orcid_match.group(1)
            continue

        if current and not current.get('affiliation'):
            aff = extract_affiliation(text)
            if aff:
                current['affiliation'] = aff

    if current:
        details.append(current)

    return details


def extract_affiliation(text):
    patterns = [
        (r'PPG-FAU-UnB|PPG FAU UnB', 'PPG-FAU-UnB'),
        (r'FAU-?UnB|FAU UnB', 'FAU-UnB'),
        (r'FAUUSP|FAU-?USP|Universidade de S.o Paulo', 'FAUUSP'),
        (r'FAUFBA|FAU-?UFBA', 'FAUFBA'),
        (r'FAET-UFMT|FAET UFMT', 'FAET-UFMT'),
        (r'FA-UFRGS|FA UFRGS', 'FA-UFRGS'),
        (r'PROPAR-UFRGS|PROPAR UFRGS', 'PROPAR-UFRGS'),
        (r'MDU-UFPE|MDU UFPE|MDU,\s*UFPE', 'MDU-UFPE'),
        (r'PPGAU/FAU/UFAL|PPGAU-UFAL', 'PPGAU-UFAL'),
        (r'FAU-?UFAL|FAU/UFAL', 'FAU-UFAL'),
        (r'CCT\s*UNICAP|CCT-UNICAP', 'CCT-UNICAP'),
        (r'CEULP[/-]?ULBRA', 'CEULP-ULBRA'),
        (r'UNICAP', 'UNICAP'),
        (r'ESUDA', 'ESUDA'),
        (r'UFCG', 'UFCG'),
        (r'UFBA', 'UFBA'),
        (r'UFPE', 'UFPE'),
        (r'UFRN', 'UFRN'),
        (r'UFPB', 'UFPB'),
        (r'UFPI', 'UFPI'),
        (r'UFT\b', 'UFT'),
        (r'UFAM', 'UFAM'),
        (r'UFAL', 'UFAL'),
        (r'UNIFAP', 'UNIFAP'),
        (r'UFG\b', 'UFG'),
        (r'UnB\b', 'UnB'),
        (r'USP\b', 'USP'),
        (r'UFS\b', 'UFS'),
        (r'UEMA', 'UEMA'),
        (r'UFC\b', 'UFC'),
        (r'UFMA', 'UFMA'),
        (r'IHAC.*UFBA', 'IHAC-UFBA'),
        (r'EBA-?UFBA|Escola de Belas Artes.*UFBA', 'EBA-UFBA'),
        (r'PUC-?GO|PUC Goi', 'PUC-GO'),
        (r'Universidade S.o Francisco', 'USF'),
    ]
    for pattern, abbrev in patterns:
        if re.search(pattern, text, re.I):
            return abbrev
    return None


def parse_resumo(lines):
    resumo_lines = []
    in_resumo = False

    for line in lines:
        text = line.strip()
        text_lower = text.lower().strip()

        if text_lower in ('resumo', 'resumo:') or text_lower == '\nresumo':
            in_resumo = True
            continue

        if in_resumo:
            if text_lower.startswith('palavras-chave') or text_lower.startswith('palavras chave'):
                break
            if text_lower in ('resumen', 'resumen:', 'abstract', 'abstract:'):
                break
            if not text:
                continue
            resumo_lines.append(text)

    if resumo_lines:
        resumo = ' '.join(resumo_lines)
        resumo = re.sub(r'\s+', ' ', resumo).strip()
        return resumo
    return None


def parse_keywords(lines):
    for line in lines:
        text = line.strip()
        text_lower = text.lower()

        if text_lower.startswith('palavras-chave') or text_lower.startswith('palavras chave'):
            kw_text = re.sub(r'^palavras-?chave\s*:\s*', '', text, flags=re.I)
            kw_text = kw_text.strip().rstrip('.')
            if ';' in kw_text:
                keywords = [k.strip().rstrip('.') for k in kw_text.split(';') if k.strip()]
            else:
                keywords = [k.strip().rstrip('.') for k in kw_text.split(',') if k.strip()]
            keywords = [k for k in keywords if k and len(k) > 1]
            return keywords
    return []


def parse_references(lines):
    refs = []
    in_refs = False
    current_ref = []

    for line in lines:
        text = line.strip()
        text_lower = text.lower()

        if text_lower in ('refer\u00eancias', 'referencias', 'refer\u00eancias bibliogr\u00e1ficas',
                          'referencias bibliograficas', 'refer\u00eancias:', 'bibliografia',
                          'refer\u00eancia bibliogr\u00e1fica', 'refer\u00eancias.', 'referencias:'):
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

            if re.match(r'^[A-Z\u00C0-\u00DC]{2,}', text) and current_ref:
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


def parse_article(lines, source_type='docx'):
    title, subtitle = parse_title(lines)
    authors = parse_authors_block(lines)
    author_details = parse_author_details(lines)

    for i, author in enumerate(authors):
        if i < len(author_details):
            detail = author_details[i]
            author['email'] = detail.get('email')
            author['orcid'] = detail.get('orcid')
            if not author.get('affiliation'):
                author['affiliation'] = detail.get('affiliation')
            author['bio'] = detail.get('bio')
        else:
            author.setdefault('email', None)
            author.setdefault('orcid', None)
            author.setdefault('affiliation', None)
            author.setdefault('bio', None)

        author['country'] = 'BR'
        author['primary_contact'] = (i == 0)

    resumo = parse_resumo(lines)
    keywords = parse_keywords(lines)
    references = parse_references(lines)

    return {
        'title': title,
        'subtitle': subtitle,
        'authors': authors,
        'resumo': resumo,
        'keywords': keywords,
        'references': references,
    }


def choose_best_docx(docx_list):
    if len(docx_list) == 1:
        return docx_list[0]
    for f in sorted(docx_list, reverse=True):
        if '(2)' in f:
            return f
    for f in docx_list:
        if 'identific' in f.lower():
            return f
    return sorted(docx_list)[0]


def choose_best_pdf(pdf_list):
    if len(pdf_list) == 1:
        return pdf_list[0]
    for f in pdf_list:
        if 'identific' in f.lower() or 'com id' in f.lower().replace('_', ' '):
            return f
    for f in sorted(pdf_list):
        if '(1)' in f:
            return f
    return sorted(pdf_list, key=len)[0]


def process_articles():
    print("=" * 60)
    print("Construindo YAML para sdnne08")
    print("8o Seminario Docomomo Norte/Nordeste, Palmas, 2021")
    print("=" * 60)

    print("\n1. Catalogando arquivos...")
    articles_map = catalog_files()
    print(f"   {len(articles_map)} artigos unicos identificados")

    os.makedirs(PDF_DIR, exist_ok=True)

    articles = []
    no_pdf = []
    errors = []
    seq = 0

    sorted_keys = sorted(articles_map.keys())

    for key in sorted_keys:
        entry = articles_map[key]
        seq += 1
        article_id = f'sdnne08-{seq:03d}'

        stem_short = entry['stem'][:70]
        print(f"\n--- {article_id}: {stem_short}...")

        lines = None
        source_type = None

        if entry['docx']:
            best_docx = choose_best_docx(entry['docx'])
            filepath = os.path.join(SRC_DIR, best_docx)
            print(f"   Fonte: docx ({best_docx})")
            lines = extract_text_from_docx(filepath)
            source_type = 'docx'

        if lines is None and (entry['pdf'] or entry['doc']):
            if entry['pdf']:
                best_pdf = choose_best_pdf(entry['pdf'])
                filepath = os.path.join(SRC_DIR, best_pdf)
                print(f"   Fonte texto: pdf ({best_pdf})")
                lines = extract_text_from_pdf(filepath)
                source_type = 'pdf'
            elif entry['doc']:
                print(f"   .doc nao suportado: {entry['doc'][0]}")
                # Try if there is a corresponding PDF
                pass

        if lines is None:
            print(f"   ERRO: Nenhuma fonte de texto disponivel!")
            errors.append((article_id, entry))
            continue

        metadata = parse_article(lines, source_type)

        if entry['docx']:
            arquivo_original = choose_best_docx(entry['docx'])
        elif entry['doc']:
            arquivo_original = entry['doc'][0]
        elif entry['pdf']:
            arquivo_original = choose_best_pdf(entry['pdf'])
        else:
            arquivo_original = None

        arquivo_pdf = f'{article_id}.pdf'
        pdf_dest = os.path.join(PDF_DIR, arquivo_pdf)
        paginas_total = None

        if entry['pdf']:
            best_pdf = choose_best_pdf(entry['pdf'])
            pdf_src = os.path.join(SRC_DIR, best_pdf)
            if not os.path.exists(pdf_dest):
                shutil.copy2(pdf_src, pdf_dest)
                print(f"   PDF copiado: {best_pdf} -> {arquivo_pdf}")
            else:
                print(f"   PDF ja existe: {arquivo_pdf}")
            paginas_total = get_pdf_page_count(pdf_dest)
        else:
            print(f"   *** SEM PDF - necessita conversao manual ***")
            no_pdf.append((article_id, arquivo_original))
            arquivo_pdf = None

        article = OrderedDict()
        article['id'] = article_id
        article['titulo'] = metadata['title']
        article['subtitulo'] = metadata['subtitle']
        article['locale'] = 'pt-BR'
        article['secao'] = 'Artigos Completos'

        autores = []
        for a in metadata['authors']:
            autor = OrderedDict()
            autor['givenname'] = a.get('givenname', '')
            autor['familyname'] = a.get('familyname', '')
            autor['email'] = a.get('email')
            autor['affiliation'] = a.get('affiliation')
            autor['orcid'] = a.get('orcid')
            autor['bio'] = a.get('bio')
            autor['country'] = a.get('country', 'BR')
            autor['primary_contact'] = a.get('primary_contact', False)
            autores.append(dict(autor))

        article['autores'] = autores
        article['resumo'] = metadata['resumo']
        article['palavras_chave'] = metadata['keywords'] if metadata['keywords'] else []
        article['arquivo_pdf'] = arquivo_pdf
        article['arquivo_original'] = arquivo_original
        article['paginas_total'] = paginas_total
        article['referencias'] = metadata['references'] if metadata['references'] else []

        articles.append(dict(article))

        n_authors = len(metadata['authors'])
        n_refs = len(metadata['references'])
        has_resumo = 'sim' if metadata['resumo'] else 'NAO'
        has_kw = 'sim' if metadata['keywords'] else 'NAO'
        t = metadata['title'][:60] if metadata['title'] else 'NAO EXTRAIDO'
        print(f"   Titulo: {t}")
        if metadata['subtitle']:
            print(f"   Subtitulo: {metadata['subtitle'][:60]}")
        print(f"   Autores: {n_authors} | Resumo: {has_resumo} | Keywords: {has_kw} | Refs: {n_refs}")
        if paginas_total:
            print(f"   Paginas: {paginas_total}")

    print("\n" + "=" * 60)
    print("Montando YAML final...")

    yaml_data = OrderedDict()
    yaml_data['issue'] = OrderedDict([
        ('slug', 'sdnne08'),
        ('title', u'8\u00ba Semin\u00e1rio Docomomo Norte/Nordeste'),
        ('location', 'Palmas, TO'),
        ('year', 2021),
        ('volume', 1),
        ('number', 8),
        ('isbn', None),
        ('publisher', None),
        ('description', u'8\u00b0 Semin\u00e1rio Docomomo Norte/Nordeste: anais [recurso eletr\u00f4nico]. Palmas: [Editora], 2021.'),
        ('source', 'https://8docomomonnepalmas.weebly.com/'),
        ('date_published', '2021-01-01'),
    ])
    yaml_data['articles'] = articles

    with open(YAML_OUT, 'w', encoding='utf-8') as f:
        yaml.dump(dict(yaml_data), f, Dumper=OrderedDumper,
                  default_flow_style=False, allow_unicode=True,
                  width=10000, sort_keys=False)

    print(f"   YAML salvo em: {YAML_OUT}")

    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)
    print(f"Total de artigos: {len(articles)}")
    print(f"Com PDF: {len([a for a in articles if a.get('arquivo_pdf')])}")
    print(f"Sem PDF (necessitam conversao): {len(no_pdf)}")
    if no_pdf:
        for aid, orig in no_pdf:
            print(f"  - {aid}: {orig}")
    print(f"Erros de extracao: {len(errors)}")
    if errors:
        for aid, entry in errors:
            print(f"  - {aid}: {entry['stem']}")

    n_with_resumo = len([a for a in articles if a.get('resumo')])
    n_with_kw = len([a for a in articles if a.get('palavras_chave')])
    n_with_authors = len([a for a in articles if a.get('autores')])
    n_with_refs = len([a for a in articles if a.get('referencias')])

    print(f"\nMetadados extraidos:")
    print(f"  Com titulo: {len([a for a in articles if a.get('titulo')])}/{len(articles)}")
    print(f"  Com autores: {n_with_authors}/{len(articles)}")
    print(f"  Com resumo: {n_with_resumo}/{len(articles)}")
    print(f"  Com palavras-chave: {n_with_kw}/{len(articles)}")
    print(f"  Com referencias: {n_with_refs}/{len(articles)}")

    total_authors = sum(len(a.get('autores', [])) for a in articles)
    print(f"  Total de autores: {total_authors}")

    print(f"\nArquivos:")
    print(f"  YAML: {YAML_OUT}")
    print(f"  PDFs: {PDF_DIR}/")


if __name__ == '__main__':
    process_articles()
