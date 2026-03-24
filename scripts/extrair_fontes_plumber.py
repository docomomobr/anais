#!/usr/bin/env python3
"""Extrai texto estruturado dos PDFs usando pdfplumber.

Gera um .jsonl por artigo com blocos de texto anotados por:
- página, tamanho de fonte, nome da fonte, role semântico
- role: heading, body, abstract, footnote, pagenum, header

A calibração dos tamanhos é automática por seminário (profile de N artigos).

Uso:
    python3 scripts/extrair_fontes_plumber.py --slug sdbr10
    python3 scripts/extrair_fontes_plumber.py --slug sdbr10 --profile-only
    python3 scripts/extrair_fontes_plumber.py --slug sdbr10 --article sdbr10-049
"""

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict

import pdfplumber

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Calibração: detectar papéis semânticos dos tamanhos de fonte
# ---------------------------------------------------------------------------

def profile_seminar(pdf_dir, sample_n=10):
    """Analisa amostra de PDFs e retorna mapa tamanho→role.

    Retorna dict com:
        body_size: tamanho do corpo (mais frequente)
        abstract_size: tamanho do abstract/refs (2º mais freq, < corpo)
        footnote_max: tamanho máximo de notas de rodapé
        heading_min: tamanho mínimo de headings (> corpo)
        pagenum_sizes: set de tamanhos usados em números de página
        size_role: dict {tamanho: role}
    """
    pdfs = sorted(glob.glob(os.path.join(pdf_dir, '*.pdf')))
    if not pdfs:
        print(f"ERRO: nenhum PDF em {pdf_dir}", file=sys.stderr)
        sys.exit(1)

    # Amostrar N artigos distribuídos uniformemente
    step = max(1, len(pdfs) // sample_n)
    sample = pdfs[::step][:sample_n]

    # Coletar frequências de tamanho (excluindo primeiras 2 páginas que têm
    # cabeçalhos do seminário, e última página que pode ser só refs/notas)
    size_freq = defaultdict(int)
    size_freq_all = defaultdict(int)
    bold_sizes = defaultdict(int)

    for pdf_path in sample:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    for c in page.chars:
                        s = round(c['size'], 1)
                        size_freq_all[s] += 1
                        if 2 <= i < len(pdf.pages) - 2:
                            size_freq[s] += 1
                        fn = c.get('fontname', '')
                        if 'Bold' in fn:
                            bold_sizes[s] += 1
        except Exception as e:
            print(f"  AVISO: não abriu {pdf_path}: {e}", file=sys.stderr)
            continue

    # Usar frequências das páginas internas para determinar corpo
    freq = size_freq if size_freq else size_freq_all
    sorted_sizes = sorted(freq.items(), key=lambda x: -x[1])

    if len(sorted_sizes) < 2:
        print("ERRO: poucos tamanhos de fonte detectados", file=sys.stderr)
        sys.exit(1)

    body_size = sorted_sizes[0][0]

    # Abstract/refs: maior tamanho < corpo com >5% de frequência
    # OU segundo mais frequente se < corpo
    abstract_size = None
    for s, cnt in sorted_sizes[1:]:
        if s < body_size and cnt > freq[body_size] * 0.03:
            abstract_size = s
            break

    # Se não achou (abstract == corpo em alguns templates), usar corpo
    if abstract_size is None:
        abstract_size = body_size

    # Notas: qualquer tamanho < abstract_size * 0.9
    footnote_max = round(abstract_size * 0.88, 1)

    # Headings: tamanhos > corpo que aparecem em bold
    heading_min = body_size + 0.5

    # Pagenum: tamanhos pequenos com poucos chars (números de página)
    # Geralmente 8-9pt
    pagenum_sizes = set()
    for s, cnt in size_freq_all.items():
        if cnt < 200 and abstract_size > s > footnote_max:
            pagenum_sizes.add(s)

    # Montar mapa tamanho → role
    size_role = {}
    for s in size_freq_all:
        if s >= heading_min and bold_sizes.get(s, 0) > 0:
            size_role[s] = 'heading'
        elif abs(s - body_size) < 0.3:
            size_role[s] = 'body'
        elif abs(s - abstract_size) < 0.3:
            size_role[s] = 'abstract'
        elif s <= footnote_max:
            size_role[s] = 'footnote'
        elif s in pagenum_sizes:
            size_role[s] = 'pagenum'
        elif s > body_size:
            size_role[s] = 'heading'
        else:
            # Entre footnote e abstract — provavelmente legenda ou afiliação
            size_role[s] = 'small'

    profile = {
        'body_size': body_size,
        'abstract_size': abstract_size,
        'footnote_max': footnote_max,
        'heading_min': heading_min,
        'pagenum_sizes': sorted(pagenum_sizes),
        'size_role': {str(k): v for k, v in sorted(size_role.items())},
        'sample_count': len(sample),
        'total_pdfs': len(pdfs),
    }
    return profile


def print_profile(profile):
    """Exibe o profile de forma legível."""
    print(f"\nPerfil tipográfico ({profile['sample_count']} PDFs amostrados de {profile['total_pdfs']}):")
    print(f"  Corpo:       {profile['body_size']}pt")
    print(f"  Abstract:    {profile['abstract_size']}pt")
    print(f"  Notas ≤:     {profile['footnote_max']}pt")
    print(f"  Headings ≥:  {profile['heading_min']}pt")
    print(f"\n  Mapa tamanho → role:")
    for size, role in sorted(profile['size_role'].items(), key=lambda x: float(x[0])):
        print(f"    {size}pt → {role}")


# ---------------------------------------------------------------------------
# Extração: gerar blocos anotados
# ---------------------------------------------------------------------------

def classify_char(char, profile):
    """Retorna o role semântico de um caractere baseado no profile."""
    s = round(char['size'], 1)
    role = profile['size_role'].get(str(s))
    if role:
        return role

    # Fallback: classificar por proximidade
    body = profile['body_size']
    abstract = profile['abstract_size']
    fn_max = profile['footnote_max']

    if s >= profile['heading_min']:
        return 'heading'
    if abs(s - body) < 0.5:
        return 'body'
    if abs(s - abstract) < 0.5:
        return 'abstract'
    if s <= fn_max:
        return 'footnote'
    return 'other'


def adapt_profile(pdf_path, profile):
    """Adapta o profile do seminário ao artigo individual.

    Se o tamanho mais frequente do artigo difere do body_size do seminário,
    recalibra os roles para esse artigo.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            size_freq = defaultdict(int)
            for page in pdf.pages:
                for c in page.chars:
                    size_freq[round(c['size'], 1)] += 1
    except Exception:
        return profile

    if not size_freq:
        return profile

    sorted_sizes = sorted(size_freq.items(), key=lambda x: -x[1])
    art_body = sorted_sizes[0][0]

    # Se o corpo do artigo é o mesmo do seminário (±0.5pt), usar profile original
    if abs(art_body - profile['body_size']) < 0.5:
        return profile

    # Recalibrar: o tamanho mais frequente é o corpo real deste artigo
    adapted = dict(profile)
    adapted['body_size'] = art_body

    # Recalcular abstract: segundo mais frequente abaixo do corpo
    adapted['abstract_size'] = art_body  # default: mesmo que corpo
    for s, cnt in sorted_sizes[1:]:
        if s < art_body and cnt > size_freq[art_body] * 0.03:
            adapted['abstract_size'] = s
            break

    adapted['footnote_max'] = round(adapted['abstract_size'] * 0.88, 1)
    adapted['heading_min'] = art_body + 0.5

    # Reconstruir size_role com todos os tamanhos (seminário + artigo)
    all_sizes = set(float(s) for s in profile['size_role'])
    all_sizes.update(size_freq.keys())
    new_roles = {}
    for s in all_sizes:
        s_str = str(round(s, 1))
        if s >= adapted['heading_min']:
            new_roles[s_str] = 'heading'
        elif abs(s - art_body) < 0.3:
            new_roles[s_str] = 'body'
        elif abs(s - adapted['abstract_size']) < 0.3 and adapted['abstract_size'] != art_body:
            new_roles[s_str] = 'abstract'
        elif s <= adapted['footnote_max']:
            new_roles[s_str] = 'footnote'
        elif s > art_body:
            new_roles[s_str] = 'heading'
        else:
            new_roles[s_str] = 'small'
    adapted['size_role'] = new_roles

    return adapted


def extract_blocks(pdf_path, profile):
    """Extrai blocos de texto anotados de um PDF.

    Retorna lista de dicts com: page, font_size, font_name, role, text, y_top, y_bottom
    Blocos são agrupados por linhas consecutivas com mesmo role.
    """
    # Adaptar profile ao artigo individual
    profile = adapt_profile(pdf_path, profile)

    try:
        pdf = pdfplumber.open(pdf_path)
    except Exception as e:
        print(f"  ERRO: {pdf_path}: {e}", file=sys.stderr)
        return []

    blocks = []

    with pdf:
        for page_idx, page in enumerate(pdf.pages):
            chars = page.chars
            if not chars:
                continue

            # Agrupar caracteres em linhas por posição Y
            lines_by_y = defaultdict(list)
            for c in chars:
                y = round(c['top'], 0)
                lines_by_y[y].append(c)

            # Processar linhas em ordem
            current_block = None

            for y in sorted(lines_by_y.keys()):
                line_chars = lines_by_y[y]
                text = ''.join(c['text'] for c in line_chars).strip()
                if not text:
                    continue

                # Tamanho dominante na linha
                size_counts = defaultdict(int)
                for c in line_chars:
                    size_counts[round(c['size'], 1)] += 1
                dominant_size = max(size_counts, key=size_counts.get)

                # Role da linha
                # Verificar se é bold (para headings)
                bold_chars = sum(1 for c in line_chars if 'Bold' in c.get('fontname', ''))
                is_bold = bold_chars > len(line_chars) * 0.5

                role = classify_char({'size': dominant_size}, profile)

                # Refinar: notas de rodapé ficam na parte inferior da página
                # Se o texto é pequeno (≤ abstract_size) e está abaixo de 70%
                # da página, é provavelmente nota de rodapé
                page_height = page.height or 842
                y_pct = y / page_height
                if (role in ('abstract', 'small') and y_pct > 0.70 and
                        dominant_size <= profile['abstract_size']):
                    role = 'footnote'

                # Refinar: texto bold do tamanho do corpo pode ser sub-heading
                if role == 'body' and is_bold and len(text) < 100:
                    role = 'subheading'

                # Detectar número de página (linha curta, só dígitos)
                clean = text.replace('⏐', '').strip()
                if clean.isdigit() and len(clean) <= 4:
                    role = 'pagenum'

                # Font name dominante
                font_counts = defaultdict(int)
                for c in line_chars:
                    fn = c.get('fontname', '').split('+')[-1]
                    font_counts[fn] += 1
                dominant_font = max(font_counts, key=font_counts.get)

                line_data = {
                    'page': page_idx + 1,
                    'font_size': dominant_size,
                    'font_name': dominant_font,
                    'role': role,
                    'text': text,
                    'y': y,
                    'bold': is_bold,
                }

                # Agrupar linhas consecutivas com mesmo role na mesma página
                if (current_block and
                        current_block['role'] == role and
                        current_block['page'] == page_idx + 1 and
                        y - current_block['_last_y'] < 25):  # gap < 25pt
                    current_block['text'] += '\n' + text
                    current_block['_last_y'] = y
                    current_block['lines'] += 1
                else:
                    if current_block:
                        del current_block['_last_y']
                        blocks.append(current_block)
                    current_block = {
                        'page': page_idx + 1,
                        'font_size': dominant_size,
                        'font_name': dominant_font,
                        'role': role,
                        'text': text,
                        'y': y,
                        'bold': is_bold,
                        'lines': 1,
                        '_last_y': y,
                    }

            if current_block:
                del current_block['_last_y']
                blocks.append(current_block)

    # Pós-classificação posicional
    blocks = post_classify(blocks)
    return blocks


def post_classify(blocks):
    """Reclassifica blocos com base em posição relativa a headings semânticos.

    Regras:
    1. Blocos entre heading "Referências/BIBLIOGRAFÍA/Bibliografia/References"
       e heading "NOTAS"/fim → role 'reference'
    2. Blocos entre heading "RESUMO/RESUMEN/ABSTRACT" e próximo heading
       de corpo (tamanho > heading de seção) → role 'abstract'
    3. Blocos entre heading "NOTAS" e fim → mantém role (footnote)
    """
    import re

    # Padrão: aceita número prefixado ("9.Referências", "7. NOTAS", etc.)
    _NUM_PREFIX = r'(?:\d+[\.\s\-–—]*\s*)?'

    REF_HEADINGS = re.compile(
        _NUM_PREFIX + r'(referências|referencias|bibliograf[íi]a|references|refer[êe]ncias\s+bibliográficas)$',
        re.IGNORECASE
    )
    NOTE_HEADINGS = re.compile(
        _NUM_PREFIX + r'(notas?|notes?|notas?\s+de\s+rodapé|notas?\s+finais|footnotes?)$',
        re.IGNORECASE
    )
    ABSTRACT_HEADINGS = re.compile(
        _NUM_PREFIX + r'(resumo|resumen|abstract)$',
        re.IGNORECASE
    )

    KEYWORDS_RE = re.compile(
        r'^(palavras[- ]?chave|keywords?|key[- ]?words?)\s*:', re.IGNORECASE
    )

    zone = 'pre'  # pre | abstract | body | reference | notes
    abstract_start_page = None  # página onde o primeiro abstract começou
    abstract_heading_count = 0  # quantos headings abstract já viu (Resumo + Abstract = 2)
    saw_keywords_en = False  # já viu keywords EN (sinal de fim de abstract)

    for i, b in enumerate(blocks):
        text_clean = b['text'].strip().rstrip('.:')
        # Também testar a primeira linha (pode ter "RESUMO:\nO texto...")
        first_line = text_clean.split('\n')[0].strip().rstrip('.:')

        is_heading_role = b['role'] in ('heading', 'subheading')
        # Blocos com label inline ("RESUMO: texto...", "ABSTRACT: texto...")
        is_inline_label = (not is_heading_role and
                           ABSTRACT_HEADINGS.match(first_line))
        is_inline_ref = (not is_heading_role and
                         REF_HEADINGS.match(first_line))
        is_inline_note = (not is_heading_role and
                          NOTE_HEADINGS.match(first_line))

        # Detectar keywords EN como sinal de fim de abstract
        if zone == 'abstract' and KEYWORDS_RE.match(first_line):
            # Marcar: keywords vistas. O bloco atual ainda é abstract.
            if re.match(r'^keywords?', first_line, re.IGNORECASE):
                saw_keywords_en = True

        # Se já viu keywords EN e o próximo bloco não-pagenum aparece,
        # o abstract acabou
        if (zone == 'abstract' and saw_keywords_en and
                b['role'] not in ('pagenum',) and
                not KEYWORDS_RE.match(first_line)):
            zone = 'body'

        # Heurística de fim de abstract por distância de páginas:
        # - Se viu 2+ headings (Resumo + Abstract): max 2 páginas após início
        # - Se viu 1 heading: max 3 páginas após início
        # Isso evita que corpo do artigo seja classificado como abstract.
        if zone == 'abstract' and abstract_start_page:
            max_pages = 2 if abstract_heading_count >= 2 else 3
            if (b['page'] > abstract_start_page + max_pages and
                    b['role'] not in ('pagenum', 'heading')):
                zone = 'body'

        if is_heading_role or is_inline_label or is_inline_ref or is_inline_note:
            if ABSTRACT_HEADINGS.match(first_line) or (is_heading_role and ABSTRACT_HEADINGS.match(text_clean)):
                zone = 'abstract'
                abstract_heading_count += 1
                if abstract_start_page is None:
                    abstract_start_page = b['page']
                if is_inline_label:
                    b['role'] = 'abstract'
                continue
            elif REF_HEADINGS.match(first_line) or (is_heading_role and REF_HEADINGS.match(text_clean)):
                zone = 'reference'
                if is_inline_ref:
                    b['role'] = 'reference'
                continue
            elif NOTE_HEADINGS.match(first_line) or (is_heading_role and NOTE_HEADINGS.match(text_clean)):
                zone = 'notes'
                continue
            elif zone == 'abstract' and is_heading_role:
                # Próximo heading após abstract = início do corpo
                zone = 'body'

        # Transição abstract→body: quando corpo e abstract têm o mesmo tamanho,
        # a pós-classificação usa a contagem de blocos e headings como sinal.
        # O título repetido na segunda página (heading com tamanho > corpo) marca
        # o fim do abstract. Também: heading não-abstract/ref/notes marca transição.
        # (Essa transição já é coberta pelo elif acima para headings.)

        # Reclassificar baseado na zona
        if b['role'] in ('pagenum',):
            continue  # não reclassificar números de página

        if zone == 'abstract' and b['role'] not in ('heading', 'footnote', 'pagenum'):
            b['role'] = 'abstract'
        elif zone == 'reference' and b['role'] not in ('heading', 'footnote', 'pagenum'):
            b['role'] = 'reference'
        elif zone == 'notes' and b['role'] not in ('heading', 'pagenum'):
            b['role'] = 'footnote'

    return blocks


# ---------------------------------------------------------------------------
# Pós-processamento: limpeza de abstract e referências extraídos
# ---------------------------------------------------------------------------

KW_LABEL_RE = re.compile(
    r'(Palavras[- ]?[Cc]have|[Kk]eywords?|[Kk]ey[- ]?[Ww]ords?|Palabras[- ]?[Cc]lave)\s*[:\.]?\s*',
)


def post_process_abstract(text):
    """Limpa abstract extraído: remove keywords coladas, hifenização, quebras espúrias.

    Retorna (abstract_limpo, keywords_extraidas_ou_None).
    """
    if not text:
        return text, None

    # 1. Separar keywords coladas no final do abstract
    keywords = None
    m = KW_LABEL_RE.search(text)
    if m:
        # Tudo antes do label é abstract, tudo depois é keywords
        kw_text = text[m.end():].strip()
        text = text[:m.start()].strip()
        # Limpar keywords: separar por ;, /, –, ou .
        if kw_text:
            # Tentar split por ; primeiro, depois por , se pouca segmentação
            if ';' in kw_text:
                kw_list = [k.strip().rstrip('.') for k in kw_text.split(';') if k.strip()]
            elif '/' in kw_text:
                kw_list = [k.strip().rstrip('.') for k in kw_text.split('/') if k.strip()]
            else:
                kw_list = [k.strip().rstrip('.') for k in kw_text.split(',') if k.strip()]
            keywords = ';'.join(kw_list)

    # 2. Corrigir hifenização de quebra de sílaba do PDF ("movi- mento" → "movimento")
    text = re.sub(r'(\w)- (\w)', r'\1\2', text)

    # 3. Remover quebras de linha espúrias (preservar \n\n como parágrafo)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'  +', ' ', text)

    return text.strip(), keywords


def post_process_refs(refs_list):
    """Limpa lista de referências: split de concatenadas, remoção de curtas.

    Retorna lista limpa.
    """
    if not refs_list:
        return refs_list

    ABNT_START = re.compile(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ]{2,},')
    result = []

    for ref in refs_list:
        ref = ref.strip()
        if not ref:
            continue

        # 1. Corrigir hifenização
        ref = re.sub(r'(\w)- (\w)', r'\1\2', ref)

        # 2. Detectar refs concatenadas (>300 chars com padrão ABNT duplo)
        if len(ref) > 300:
            # Tentar split onde um novo padrão SOBRENOME, aparece
            parts = re.split(r'(?<=\.)\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ]{2,},)', ref)
            if len(parts) > 1:
                result.extend(p.strip() for p in parts if len(p.strip()) > 20)
                continue

        # 3. Detectar underscores ABNT (________) como continuação do mesmo autor
        if ref.startswith('____'):
            ref = re.sub(r'^_+\s*', '', ref)
            if result:
                # Usar autor da ref anterior
                prev = result[-1]
                m = ABNT_START.match(prev)
                if m:
                    author_end = prev.find('.')
                    if author_end > 0:
                        ref = prev[:author_end + 1] + ' ' + ref

        # 4. Remover refs muito curtas (<25 chars, provavelmente lixo)
        if len(ref) < 25:
            continue

        result.append(ref)

    return result


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_jsonl(blocks, output_path):
    """Escreve blocos como JSONL."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for block in blocks:
            # Remover campos internos
            out = {k: v for k, v in block.items() if not k.startswith('_')}
            f.write(json.dumps(out, ensure_ascii=False) + '\n')


def find_pdf_dir(slug):
    """Localiza o diretório de PDFs para um slug."""
    # Nacionais
    d = os.path.join(BASE_DIR, 'nacionais', slug, 'pdfs')
    if os.path.isdir(d):
        return d

    # Regionais
    for grupo in ['nne', 'se', 'sul']:
        d = os.path.join(BASE_DIR, 'regionais', grupo, slug, 'pdfs')
        if os.path.isdir(d):
            return d

    return None


def find_output_dir(slug):
    """Localiza/cria o diretório de output para fontes_plumber."""
    # Mesmo nível do fontes/
    for base in [os.path.join(BASE_DIR, 'nacionais', slug),
                 *[os.path.join(BASE_DIR, 'regionais', g, slug) for g in ['nne', 'se', 'sul']]]:
        if os.path.isdir(base):
            out = os.path.join(base, 'fontes_plumber')
            os.makedirs(out, exist_ok=True)
            return out
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Extrai texto estruturado dos PDFs via pdfplumber')
    parser.add_argument('--slug', required=True, help='Slug do seminário (ex: sdbr10)')
    parser.add_argument('--profile-only', action='store_true',
                        help='Apenas exibir o perfil tipográfico, sem extrair')
    parser.add_argument('--article', help='Extrair apenas um artigo (ex: sdbr10-049)')
    parser.add_argument('--sample', type=int, default=10,
                        help='Número de PDFs para amostra do profile (default: 10)')
    args = parser.parse_args()

    pdf_dir = find_pdf_dir(args.slug)
    if not pdf_dir:
        print(f"ERRO: diretório de PDFs não encontrado para {args.slug}", file=sys.stderr)
        sys.exit(1)

    # Fase 1: Profile
    print(f"Analisando perfil tipográfico de {args.slug}...")
    profile = profile_seminar(pdf_dir, sample_n=args.sample)
    print_profile(profile)

    if args.profile_only:
        return

    # Fase 2: Extração
    output_dir = find_output_dir(args.slug)
    if not output_dir:
        print(f"ERRO: não encontrou diretório base para {args.slug}", file=sys.stderr)
        sys.exit(1)

    # Salvar profile
    profile_path = os.path.join(output_dir, '_profile.json')
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    print(f"\nProfile salvo em {profile_path}")

    # Listar PDFs a processar
    if args.article:
        pdfs = [os.path.join(pdf_dir, f'{args.article}.pdf')]
        if not os.path.exists(pdfs[0]):
            print(f"ERRO: {pdfs[0]} não encontrado", file=sys.stderr)
            sys.exit(1)
    else:
        pdfs = sorted(glob.glob(os.path.join(pdf_dir, '*.pdf')))

    print(f"\nExtraindo {len(pdfs)} artigos para {output_dir}/...")

    stats = {'ok': 0, 'blocks': 0, 'error': 0}
    for pdf_path in pdfs:
        art_id = os.path.basename(pdf_path).replace('.pdf', '')
        out_path = os.path.join(output_dir, f'{art_id}.jsonl')

        blocks = extract_blocks(pdf_path, profile)
        if blocks:
            write_jsonl(blocks, out_path)
            role_counts = defaultdict(int)
            for b in blocks:
                role_counts[b['role']] += 1
            roles_str = ', '.join(f'{r}:{n}' for r, n in sorted(role_counts.items()))
            print(f"  {art_id}: {len(blocks)} blocos ({roles_str})")
            stats['ok'] += 1
            stats['blocks'] += len(blocks)
        else:
            print(f"  {art_id}: ERRO (sem blocos)")
            stats['error'] += 1

    print(f"\nResumo: {stats['ok']} ok, {stats['error']} erros, {stats['blocks']} blocos total")


if __name__ == '__main__':
    main()
