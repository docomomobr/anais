#!/usr/bin/env python3
"""
Correção sistemática dos issues encontrados por validate_metadata.py.

Lê revisao/{slug}-validation.json e aplica correções determinísticas:
- A07: Extrai abstract_en do fontes/
- A08: Extrai keywords_en do fontes/
- A10: Resolve backfills (substitui ____ pelo autor da ref anterior)
- A11: Split de refs concatenadas + remoção de não-referências
- A12: Remove não-referências
- A13: Junta URLs órfãs à ref anterior

Issues que NÃO são corrigidos (ficam para revisão humana):
- A01-A04: Mismatches EN/ES (reportados para conferência)
- A09: abstract_es faltante (extração de ES é rara)
- A14: Abstract contaminado (precisa julgamento humano)
- A15: Locale mismatch (auto-fix pelo validate_metadata.py --fix)

Uso:
    python3 scripts/fix_validation_issues.py --slug sdbr10 --dry-run
    python3 scripts/fix_validation_issues.py --slug sdbr10
    python3 scripts/fix_validation_issues.py --slug sdbr10 --only A11  # só refs longas

Depende de validate_metadata.py ter sido rodado ANTES (gera o JSON de input).
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')

# Importar funções dos scripts existentes
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))
from clean_references import UNDERSCORE_START, extract_author
from extrair_metadados_en import (
    find_fontes_dir, read_fontes_text, extract_abstract_en, extract_keywords_en
)


# ── Classificação de referências ─────────────────────────────────────────────

# Padrão ABNT: SOBRENOME, Nome ou SIGLA. ou "Título de obra"
ABNT_AUTHOR_RE = re.compile(
    r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][A-ZÁÉÍÓÚÂÊÔÃÕÇÑa-záéíóúâêôãõç\s]+,\s+[A-Z]'
)

# Entrada sem autor: periódico/revista como entrada principal
PERIODICAL_RE = re.compile(
    r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][A-Za-záéíóúâêôãõç]+\.\s+n\.\s*\d'
)

# Entrada que começa com aspas (título como entrada)
QUOTED_ENTRY_RE = re.compile(r'^["\'""]')

# Palavras que iniciam comentário/endnote (NÃO é referência bibliográfica)
NON_REF_STARTERS = [
    'O ', 'A ', 'Os ', 'As ', 'Um ', 'Uma ',
    'Para ', 'Nesta ', 'Neste ', 'Muitos ', 'Segundo ',
    'No ', 'Na ', 'Nos ', 'Nas ',
    'Essa ', 'Esse ', 'Este ', 'Esta ', 'Esses ', 'Estas ',
    'Também ', 'Além ', 'Apesar ', 'Enquanto ', 'Embora ',
    'Ver ', 'Ver: ', 'Veja ', 'Cf. ', 'Cf ', 'Idem', 'Ibidem', 'Ibíd.', 'Ibid.',
    'Op. cit.', 'Op.cit.', 'Cfr. ', 'Cfr ',
    'This ', 'These ', 'That ',
    'Conforme ', 'Sobre ', 'Entre ', 'Dentre ',
    'Foi ', 'Foram ', 'Sendo ', 'São ', 'É ',
    'Como ', 'Quando ', 'Onde ',
    'Tal ', 'Tais ', 'Outro ', 'Outros ', 'Outra ',
    'Tombado ', 'Projeto de ', 'Criou ',  # descrições de obras/edifícios
    'Caderno Especial',  # fragmento de ref sem autor
    # Legendas de imagem / créditos de foto
    'Courtesy of ', 'Photograph by ', 'Photo by ', 'Photo: ',
    'Foto de ', 'Foto: ', 'Source: ', 'Fonte: ',
]

# Número de nota no início (¹, ², 1., 2., 1), i., ii. etc.)
NOTE_NUMBER_RE = re.compile(r'^[\d¹²³⁴⁵⁶⁷⁸⁹⁰\u00B9\u00B2\u00B3]+[.\s)]\s*[A-Z]')

# Figure captions (legendas de figuras capturadas como refs)
FIGURE_RE = re.compile(r'^(Figura|Fig\.?|Figure|Imagem)\s*\d', re.IGNORECASE)

# Conteúdo não-referência (agradecimentos, créditos, CVs, cabeçalhos de subseção)
NON_REF_CONTENT = [
    'agradec', 'crédito', 'ilustraç', 'currículo',
    'fapesp', 'cnpq', 'capes', 'bolsista',
    'fontes primárias', 'artigos de jornais',
    'engenheiro e proprietário',
]

# Headers de seção bibliográfica que se infiltram como prefixo das refs
# Ex: "Escritos Banham, Reyner..." → "Banham, Reyner..."
# Ex: "Teses e Dissertações Cotrim, Marcio..." → "Cotrim, Marcio..."
SECTION_HEADER_PREFIXES = [
    'Escritos ',
    'Livros ',
    'Revistas e Periódicos ',
    'Teses e Dissertações ',
    'Dissertações e Teses ',
    'Artigos e Periódicos ',
    'Artigos em Periódicos ',
    'Artigos em periódicos ',
    'Artigos ',
    'Periódicos ',
    'Números monográficos de periódicos ',
    'Números Monográficos de Periódicos ',
    'Referências Bibliográficas ',
    'Bibliografia ',
    'Fontes Bibliográficas ',
    'Sites eletrônicos ',
    'Sites Eletrônicos ',
    'Sites ',
    'Capítulos de livros ',
    'Capítulos de Livros ',
    'Documentos ',
    'Documentos Oficiais ',
    # Variantes ES
    'Fuente de imágenes ',
    'Fuente de Imágenes ',
    'Bibliografía ',
    'Libros ',
    'Revistas ',
    'Tesis ',
    'Artículos ',
    'Documentos oficiales ',
    'Documentos Oficiales ',
    'Referencias bibliográficas ',
    'Referencias Bibliográficas ',
    'Referencias ',
]

# Headers de seção standalone (sem ref depois — remover inteiramente)
SECTION_HEADER_STANDALONE = re.compile(
    r'^(Escritos|Livros|Revistas e Periódicos|Teses e Dissertações|'
    r'Dissertações e Teses|Artigos e Periódicos|Artigos em [Pp]eriódicos|'
    r'Artigos|Periódicos|Números [Mm]onográficos de [Pp]eriódicos|'
    r'Referências Bibliográficas|Bibliografia|Fontes Bibliográficas|'
    r'Sites [Ee]letrônicos|Sites|Documentos|Documentos Oficiais|'
    r'Capítulos de [Ll]ivros|Fontes|Notas|'
    # Variantes ES
    r'Fuente de [Ii]mágenes|Bibliografía|Libros|Revistas|'
    r'Tesis|Artículos|Documentos [Oo]ficiales|'
    r'Referencias [Bb]ibliográficas|Referencias)\.?\s*$',
    re.IGNORECASE
)

# Page break marker (⏐ = U+23D0 ou │ = U+2502, ou | entre espaços)
# Pode ter caracteres PUA (U+F8E6 etc.) adjacentes
PAGE_BREAK_RE = re.compile(r'\s*[⏐│\|][\uf000-\uf8ff]*\s*\d+\s+')


def is_body_text(ref):
    """Detecta body text capturado como referência (erro de boundary na extração).

    Body text: parágrafos narrativos longos sem estrutura bibliográfica.
    """
    ref = ref.strip()
    if len(ref) < 200:
        return False
    if ABNT_AUTHOR_RE.match(ref):
        return False
    # Chicago: Sobrenome, Nome
    if re.match(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóúâêôãõç]+,\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóúâêôãõç]', ref):
        return False
    return has_narrative_structure(ref)


def is_gross_junk(ref):
    """Detecta lixo grosso: figure captions, body text, agradecimentos, headers.

    Passada 0 do sweep — remove antes de processar fragmentos/endnotes.
    """
    r = ref.strip()
    if not r:
        return True
    # Figure captions
    if FIGURE_RE.match(r):
        return True
    # Standalone section headers
    if SECTION_HEADER_STANDALONE.match(r):
        return True
    # Image metadata / markup
    if r.startswith('[IMAGE') or r.startswith('[image'):
        return True
    # Non-ref content markers
    r_lower = r.lower()
    for marker in NON_REF_CONTENT:
        if marker in r_lower:
            return True
    # Body text (parágrafos narrativos longos)
    if is_body_text(r):
        return True
    return False

# Boundary de split: ponto final + espaço + SOBRENOME, Nome (padrão ABNT)
ABNT_BOUNDARY_RE = re.compile(
    r'(?<=\.)\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][A-ZÁÉÍÓÚÂÊÔÃÕÇÑ]+,\s+[A-Z])'
)

# Boundary alternativa: ano+ponto + espaço + SOBRENOME
YEAR_BOUNDARY_RE = re.compile(
    r'(?<=\d{4}\.)\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][A-ZÁÉÍÓÚÂÊÔÃÕÇÑ]+,\s+[A-Z])'
)

# Boundary Chicago/APA: ponto + espaço + Sobrenome, Nome (mixed case)
# Ex: "...2005. Barone, Ana Cláudia" ou "...1966. Bastos, Maria Alice"
CHICAGO_BOUNDARY_RE = re.compile(
    r'(?<=\.)\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóúâêôãõç]+,\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóúâêôãõç])'
)

# Boundary por ano (com/sem ponto) + espaço + Nome (Chicago inline)
# Ex: "...1975 Giovanni Damiani" ou "...1959, p.231-235 Amâncio Guedes"
YEAR_CHICAGO_RE = re.compile(
    r'(?<=\d{4})\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóúâêôãõç]+[,\s]+[A-Z])'
)

# Boundary por publisher + ano/ponto + espaço + novo autor
# Ex: "...MIT Press, 2003. Sobrenome, Nome. Title..."
# Não usa lookbehind variável — usa grupo de captura e split manual
PUBLISHER_BOUNDARY_WORDS = ('Press', 'Editora', 'Editorial', 'Edições', 'Editions', 'Verlag', 'Publishers', 'Publisher')


NARRATIVE_THRESHOLD = 3

# Pré-compilar marcadores narrativos (evita re.compile por chamada)
_NARRATIVE_MARKERS = [re.compile(p, re.IGNORECASE) for p in [
    r'\bque\s', r'\bpara\s', r'\bcomo\s', r'\bquando\s', r'\bonde\s',
    r'\bporém\b', r'\bcontudo\b', r'\bentretanto\b', r'\btambém\b',
    r'\bapesar\s+de\b', r'\bembora\b', r'\benquanto\b',
    r'\bsendo\b', r'\bfoi\b', r'\bforam\b', r'\bsão\b',
    r'\bdeste\b', r'\bdesta\b', r'\bdesses\b', r'\bdessas\b',
    r'\bneste\b', r'\bnesta\b', r'\bnesse\b', r'\bnessa\b',
    r'\baqui\b', r'\bassim\b', r'\bportanto\b',
    r'\bwhich\b', r'\bthat\b', r'\bwhere\b', r'\bhowever\b',
    r'\balthough\b', r'\btherefore\b', r'\bthus\b',
    # Espanhol
    r'\buna\s', r'\bcuya\b', r'\bcuyo\b', r'\baunque\b',
    r'\bsin\s+embargo\b', r'\bademás\b', r'\btambién\b',
    r'\bdonde\b', r'\bcuando\b', r'\bsobre\b',
    r'\bdesde\b', r'\bhacia\b', r'\bmientras\b',
]]


def has_narrative_structure(text):
    """Detecta se o texto tem estrutura narrativa (nota/comentário) vs bibliográfica.

    Retorna True se ≥3 marcadores narrativos encontrados (early exit).
    """
    count = 0
    for m in _NARRATIVE_MARKERS:
        if m.search(text):
            count += 1
            if count >= NARRATIVE_THRESHOLD:
                return True
    return False


def is_bibliographic_ref(ref):
    """Determina se uma entrada é referência bibliográfica (True) ou nota (False).

    Critério: referência = dados bibliográficos (autor, título, editora, ano).
    Nota = texto narrativo/comentário que pode citar fontes inline.

    Aceita qualquer norma (ABNT, Chicago, APA, Vancouver).
    """
    ref = ref.strip()
    if not ref or len(ref) < 10:
        return False

    # Padrão ABNT claro: SOBRENOME, Nome
    if ABNT_AUTHOR_RE.match(ref):
        # Mesmo ABNT pode ser nota se muito longa e narrativa
        if len(ref) > 500 and has_narrative_structure(ref):
            return False
        return True

    # Periódico como entrada
    if PERIODICAL_RE.match(ref):
        return True

    # Entrada com aspas (título sem autor) — mas pode ser citação (nota)
    if QUOTED_ENTRY_RE.match(ref):
        if len(ref) > 500 and has_narrative_structure(ref):
            return False
        return True

    # Começa com letra minúscula: provavelmente continuação ou comentário
    if ref[0].islower():
        return False

    # Número de nota no início
    if NOTE_NUMBER_RE.match(ref):
        return False

    # Palavras que iniciam comentário/endnote
    for starter in NON_REF_STARTERS:
        if ref.startswith(starter):
            return False

    # Referência curta (<60) que parece fragmento → NÃO é ref independente
    if len(ref) < 60 and is_fragment(ref):
        return False

    # Referência curta (<500) sem padrão de nota → manter
    if len(ref) <= 500:
        return True

    # Ref longa (>500): verificar se é narrativa
    if has_narrative_structure(ref):
        return False

    # Na dúvida, manter
    return True


def is_fragment(ref):
    """Detecta se uma entrada é fragmento de ref anterior (quebra de linha no PDF).

    Fragmentos são pedaços de referência que ficaram separados por causa
    de quebra de página ou linha no pdftotext. Devem ser JUNTADOS à ref
    anterior, não removidos.

    Retorna True se é fragmento.
    """
    r = ref.strip()
    if not r:
        return False

    # Citações abreviadas são refs independentes, NUNCA fragmentos
    if re.match(r'^(Idem|Ibidem|Ibíd|Ibid|Op\.\s*cit|Id\.\s)', r, re.IGNORECASE):
        return False

    # Começa com minúscula: quase certamente continuação
    if r[0].islower():
        return True

    # Ano isolado numa linha (ex: "2003." ou "1999")
    if re.match(r'^\d{4}\.?\s*$', r):
        return True

    # URL isolada (continuação de ref anterior)
    if re.match(r'^(https?://|www\.)', r, re.IGNORECASE):
        return True

    # "Disponível em:" isolado (sem URL na mesma linha)
    if re.match(r'^Disponível\s+em\s*:?\s*$', r, re.IGNORECASE):
        return True

    # Muito curto e parece final de ref (editora, ano, páginas)
    if len(r) < 60:
        # Padrão: "Cidade: Editora, ANO." ou "São Paulo, ANO." ou "p. NN-NN."
        # Aceita nomes compostos: "Buenos Aires:", "La Habana,", "São Paulo,"
        if re.match(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóúâêôãõç\s]+[,:]\s+', r):
            # SAFEGUARD: não pegar refs Chicago curtas ("Banham, Reyner.")
            # Se parece "Sobrenome, Nome" (autor), NÃO é fragmento
            if not re.match(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóúâêôãõç]+,\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóúâêôãõç]+', r):
                return True
        # Padrão: "ANO. p. NN" ou "v. N, p. NN"
        if re.match(r'^\d{4}[.,]', r):
            return True
        # Padrão: "p. 123-456." ou "pp. 123-456"
        if re.match(r'^p{1,2}\.\s*\d', r):
            return True
        # Padrão: termina com ano e/ou ponto (ex: "Concepción, 2012.")
        if re.search(r'\d{4}[.,]?\s*$', r):
            # Não deve ser uma ref Chicago completa — verificar se tem estrutura de ref
            # Refs completas têm título (aspas ou itálico): "Author. Title. City, 2012."
            if '"' not in r and '«' not in r and r.count('.') <= 2:
                return True
        # Padrão: termina com "p. N-N." (páginas — final de ref)
        if re.search(r'p\.\s*\d+[-–]?\d*\.?\s*$', r):
            return True

    # Começa com ano isolado: "1960. In: FERREIRA..." ou "2009. Disponível em..."
    if re.match(r'^\d{4}\.\s+(In:|Disponível|Available|Acesso|Retrieved)', r):
        return True

    # Começa com "In:" ou "Disponível em" (continuação de ref)
    if re.match(r'^(In:|Disponível\s+em|Available\s+(at|from)|Acesso\s+em)', r, re.IGNORECASE):
        return True

    # Começa com editora/publisher patterns
    if re.match(r'^(Editora|Ed\.|Editorial|Publisher|University\s+Press)', r, re.IGNORECASE):
        return True

    # Padrão de página/volume (continuação)
    if re.match(r'^(vol\.|v\.\s*\d|n\.\s*\d|nº\s*\d)', r, re.IGNORECASE):
        return True

    # Padrão: continuação com "En" (espanhol para "In:")
    if re.match(r'^En\s+[A-Z]', r) and len(r) < 80:
        return True

    # NOTA: padrão "SIGLA, Cidade, Ano" (ex: "UFRN, Natal, Fevereiro 2019.") é
    # ambíguo — pode ser fragmento de ref anterior (local de evento) ou autor
    # institucional legítimo (IPHAN, IBGE). Deixar para a revisão LLM (1.2c).

    return False


def is_numbered_endnote(ref):
    """Detecta endnote numerada que contém referência bibliográfica.

    Retorna (True, stripped_ref) se é endnote com ref, (False, None) se não.
    """
    r = ref.strip()
    m = re.match(r'^(\d{1,3})\s+', r)
    if not m:
        return False, None

    stripped = r[m.end():]
    if is_bibliographic_ref(stripped):
        return True, stripped
    return False, None


def split_concatenated_refs(ref_text):
    """Tenta separar refs concatenadas (ABNT ou Chicago) numa única string.

    Retorna lista de partes (1 elemento = não separou).
    Aceita ABNT (SOBRENOME, Nome) e Chicago (Sobrenome, Nome).
    """
    # Passo 0: backfill em-dash (—. ou –.) — mesmo autor, outra obra
    # Ex: "Arango, Silvia. Obra 1. 2012. —. Obra 2. Bogotá, 1990."
    # O "—." substitui o nome do autor na norma Chicago/ES.
    emdash_parts = re.split(r'(?<=\.)\s+[—–]\.\s+', ref_text)
    if len(emdash_parts) > 1:
        # Extrair autor da primeira parte e prepor às demais
        first = emdash_parts[0]
        author = None
        # Chicago: "Sobrenome, Nome."
        m = re.match(r'^([A-ZÁÉÍÓÚÂÊÔÃÕÇÑa-záéíóúâêôãõç][^.]+\.)\s', first)
        if m:
            author = m.group(1)
        if author:
            result = [first]
            for part in emdash_parts[1:]:
                result.append(f'{author} {part}')
            return result

    # Passo 1: boundary por autor ABNT (ALL CAPS) após ponto
    parts = ABNT_BOUNDARY_RE.split(ref_text)
    if len(parts) > 1:
        return parts

    # Passo 2: boundary por autor ABNT após ano
    parts = YEAR_BOUNDARY_RE.split(ref_text)
    if len(parts) > 1:
        return parts

    # Passo 3: boundary Chicago (mixed case) após ponto
    parts = CHICAGO_BOUNDARY_RE.split(ref_text)
    if len(parts) > 1:
        # Validar: cada parte deve ter conteúdo significativo
        if all(len(p.strip()) > 30 for p in parts):
            return parts

    # Passo 4: boundary Chicago após ano
    parts = YEAR_CHICAGO_RE.split(ref_text)
    if len(parts) > 1:
        if all(len(p.strip()) > 30 for p in parts):
            return parts

    # Passo 5: boundary por publisher (Press, Editora, etc.) + ano + novo autor
    for pw in PUBLISHER_BOUNDARY_WORDS:
        # Padrão: "...Press, 2003. Autor..." ou "...Editora. Autor..."
        pattern = re.compile(
            re.escape(pw) + r'[.,]\s+(?:\d{4}[.,]?\s+)?(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ])'
        )
        parts = pattern.split(ref_text)
        if len(parts) > 1 and all(len(p.strip()) > 30 for p in parts):
            # Re-anexar o publisher word à parte anterior
            result = []
            matches = list(pattern.finditer(ref_text))
            prev = 0
            for m in matches:
                result.append(ref_text[prev:m.start()].rstrip() + ' ' + ref_text[m.start():m.end()].split()[0])
                prev = m.end()
            if prev < len(ref_text):
                result.append(ref_text[prev:].strip())
            result = [p.strip() for p in result if p.strip() and len(p.strip()) > 30]
            if len(result) > 1:
                return result

    # Passo 6: pipe separator (refs separadas por | )
    if ' | ' in ref_text:
        parts = [p.strip() for p in ref_text.split(' | ') if p.strip()]
        if len(parts) > 1 and all(len(p) > 15 for p in parts):
            return parts

    return [ref_text]


# ── Limpeza de keywords ──────────────────────────────────────────────────────

# Template garbage patterns (instruções do template em vez de keywords reais)
TEMPLATE_GARBAGE_RE = re.compile(
    r'(máximo\s+\d|separados\s+com|espaçamento|parágrafo\s+de\s+\d+\s*pt'
    r'|título\s+em\s+negrito|alinhamento|entre\s*linhas)',
    re.IGNORECASE
)

# Padrões de lixo em keywords: título do artigo, body text, captions
KW_JUNK_RE = re.compile(
    r'^(Introdução|Figure\s|Figura\s|Fonte:|Source:|http|file:///|'
    r'O presente|Este artigo|The present|This article|'
    r'"[A-Z])',  # citação entre aspas
    re.IGNORECASE
)


_VALID_KW_COLS = {'keywords', 'keywords_en', 'keywords_es'}


def clean_keywords(conn, slug, dry_run):
    """Limpeza automática de keywords: split, garbage, trimming.

    Operações:
    1. Remover template garbage (instruções do formulário)
    2. Separar keywords aglutinadas (separadores: '. ', ' . ', ' / ', ', ')
    3. Trim de pontuação final (., ;)
    4. Remover duplicatas (case-insensitive)

    NÃO normaliza capitalização — isso depende do dict.db e é feito
    pelo normalizar_maiusculas.py ou manualmente.

    Retorna dict com contadores.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT id, keywords, keywords_en, keywords_es
        FROM articles WHERE seminar_slug = ?
        ORDER BY id
    """, (slug,))
    rows = cur.fetchall()

    stats = {'garbage': 0, 'split': 0, 'trimmed': 0, 'dedup': 0, 'articles': 0}

    for art_id, kw, kw_en, kw_es in rows:
        art_changed = False

        for field_val, col in [(kw, 'keywords'), (kw_en, 'keywords_en'), (kw_es, 'keywords_es')]:
            if col not in _VALID_KW_COLS:
                raise ValueError(f"Invalid column: {col}")
            if not field_val:
                continue
            try:
                kws = json.loads(field_val)
            except (json.JSONDecodeError, TypeError):
                print(f"  WARN: {art_id} {col}: JSON inválido, pulando")
                continue
            new_kws = []
            changed = False

            for k in kws:
                k = k.strip()
                # Limpar zero-width spaces e control chars
                k = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', k).strip()
                if not k:
                    continue

                # 1a. Template garbage — strip prefix or remove entirely
                if TEMPLATE_GARBAGE_RE.search(k):
                    # Check if there's a useful keyword after the template text
                    # Pattern: "(título em negrito): keyword" or "arial 10, entre linhas..."
                    m = re.search(r'[):]\s*(.+)$', k)
                    if m and len(m.group(1).strip()) > 1 and not TEMPLATE_GARBAGE_RE.search(m.group(1)):
                        k = m.group(1).strip()
                        changed = True
                        print(f"  {art_id}.{col}: TEMPLATE prefix removido: \"{k[:60]}\"")
                        new_kws.append(k)
                    else:
                        stats['garbage'] += 1
                        changed = True
                        print(f"  {art_id}.{col}: GARBAGE removido: \"{k[:60]}\"")
                    continue

                # 1b. Junk patterns (body text, titles, captions, URLs)
                if KW_JUNK_RE.match(k):
                    stats['garbage'] += 1
                    changed = True
                    print(f"  {art_id}.{col}: JUNK removido: \"{k[:60]}\"")
                    continue

                # 1c. Newlines (keyword with body text bleeding in)
                if '\n' in k:
                    # Keep only text before first newline
                    clean = k.split('\n')[0].strip().rstrip('.,;')
                    if len(clean) > 1:
                        k = clean
                        changed = True
                    else:
                        stats['garbage'] += 1
                        changed = True
                        print(f"  {art_id}.{col}: NEWLINE removido: \"{k[:60]}\"")
                        continue

                # 1d. ALL CAPS block (≥15 chars, likely title text infiltrated)
                # Preserva siglas curtas (CIAM, IPHAN, UNESCO etc.)
                if len(k) >= 15 and re.match(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ\s:–—\-]{15,}$', k):
                    stats['garbage'] += 1
                    changed = True
                    print(f"  {art_id}.{col}: ALL CAPS removido: \"{k[:60]}\"")
                    continue

                # 1e. Garbled (words stuck together, no spaces)
                if len(k) > 25 and ' ' not in k:
                    stats['garbage'] += 1
                    changed = True
                    print(f"  {art_id}.{col}: GARBLED removido: " + repr(k[:60]))
                    continue

                # 1f. Too long (>80 chars) — likely body text, not a keyword
                if len(k) > 80:
                    stats['garbage'] += 1
                    changed = True
                    print(f"  {art_id}.{col}: LONGA removida ({len(k)}c): \"{k[:60]}\"")
                    continue

                # 2. Split por separadores
                # '. ' ou '.' sem espaço (exceto abreviações comuns)
                if re.search(r'(?<![A-Z])\.\s*(?=[A-Z])', k) and len(k) > 30:
                    parts = re.split(r'\s*\.\s*', k)
                    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 1]
                    if len(parts) >= 2:
                        new_kws.extend(parts)
                        stats['split'] += len(parts) - 1
                        changed = True
                        print(f"  {art_id}.{col}: SPLIT (.): \"{k[:60]}\" → {parts}")
                        continue

                # ' / ' separator
                if ' / ' in k:
                    parts = [p.strip() for p in k.split(' / ') if p.strip()]
                    if len(parts) >= 2:
                        new_kws.extend(parts)
                        stats['split'] += len(parts) - 1
                        changed = True
                        print(f"  {art_id}.{col}: SPLIT (/): \"{k[:60]}\" → {parts}")
                        continue

                # ', ' separator — só se cada parte parece keyword independente
                # (não separar "São Paulo, SP" ou "Análise de obra, Vilanova Artigas")
                if ', ' in k and len(k) > 40:
                    parts = [p.strip() for p in k.split(', ') if p.strip()]
                    # Heurística: só separar se cada parte tem ≥3 chars e não contém
                    # padrões de nome composto (Ex: "Vilanova, Artigas" seria falso)
                    if (len(parts) >= 2 and
                            all(len(p) >= 3 for p in parts) and
                            not any(p[0].islower() for p in parts[1:])):
                        new_kws.extend(parts)
                        stats['split'] += len(parts) - 1
                        changed = True
                        print(f"  {art_id}.{col}: SPLIT (,): \"{k[:60]}\" → {parts}")
                        continue

                # 3. Trim trailing punctuation
                stripped = k.rstrip('.,;')
                if stripped != k:
                    stats['trimmed'] += 1
                    changed = True
                    k = stripped

                new_kws.append(k)

            # 4. Dedup (case-insensitive, preserve first occurrence)
            seen = set()
            deduped = []
            for k in new_kws:
                lower = k.lower()
                if lower in seen:
                    stats['dedup'] += 1
                    changed = True
                else:
                    seen.add(lower)
                    deduped.append(k)
            new_kws = deduped

            if changed:
                art_changed = True
                if new_kws:
                    if not dry_run:
                        cur.execute(f"UPDATE articles SET {col} = ? WHERE id = ?",
                                    (json.dumps(new_kws, ensure_ascii=False), art_id))
                else:
                    # All keywords were garbage → set to NULL
                    if not dry_run:
                        cur.execute(f"UPDATE articles SET {col} = NULL WHERE id = ?",
                                    (art_id,))

        if art_changed:
            stats['articles'] += 1

    if not dry_run and stats['articles']:
        conn.commit()

    print(f"\n  Keywords: {stats['articles']} artigos alterados, "
          f"{stats['garbage']} garbage, {stats['split']} split, "
          f"{stats['trimmed']} trimmed, {stats['dedup']} dedup")
    return stats


# ── Handlers por categoria ───────────────────────────────────────────────────

def _find_best_jsonl(fontes_dir, art_id):
    """Encontra o melhor .jsonl para um artigo: fontes_docx/ > fontes_plumber/.

    Retorna caminho do .jsonl ou None."""
    parent = os.path.dirname(fontes_dir)
    for subdir in ('fontes_docx', 'fontes_plumber'):
        jsonl_path = os.path.join(parent, subdir, f'{art_id}.jsonl')
        if os.path.exists(jsonl_path):
            return jsonl_path
    # Fallback: procurar no próprio fontes_dir
    jsonl_path = os.path.join(fontes_dir, f'{art_id}.jsonl')
    if os.path.exists(jsonl_path):
        return jsonl_path
    return None


def _read_fontes_lines(fontes_dir, art_id):
    """Lê linhas da melhor fonte disponível. Hierarquia: fontes_docx/ > fontes_plumber/ > fontes/ (.txt).
    Retorna lista de linhas ou None."""
    # Tentar .jsonl (docx > plumber)
    jsonl_path = _find_best_jsonl(fontes_dir, art_id)
    if jsonl_path:
        lines = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    block = json.loads(line)
                except (json.JSONDecodeError, TypeError):
                    continue
                text = block.get('text', '').strip()
                if text:
                    lines.extend(text.split('\n'))
        return [l + '\n' for l in lines]
    # Fallback: .txt
    txt_path = os.path.join(fontes_dir, f'{art_id}.txt')
    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.readlines()
    return None


def fix_a07(conn, slug, issues, fontes_dir, dry_run):
    """A07: Extrair abstract_en do fontes/ quando marcador existe."""
    fixed = 0
    cur = conn.cursor()

    article_ids = set(i['article_id'] for i in issues if i['check'] == 'A07')
    if not article_ids:
        return 0

    for art_id in sorted(article_ids):
        lines = _read_fontes_lines(fontes_dir, art_id)
        if not lines:
            print(f"  {art_id}: fonte não encontrada")
            continue

        abstract = extract_abstract_en(lines)
        if abstract and len(abstract) > 50:
            print(f"  {art_id}: abstract_en extraído ({len(abstract)} chars)")
            if not dry_run:
                cur.execute("UPDATE articles SET abstract_en = ? WHERE id = ?",
                            (abstract, art_id))
            fixed += 1
        else:
            print(f"  {art_id}: extração falhou ou texto muito curto")

    if not dry_run and fixed:
        conn.commit()
    return fixed


def fix_a08(conn, slug, issues, fontes_dir, dry_run):
    """A08: Extrair keywords_en do fontes/ quando marcador existe."""
    fixed = 0
    cur = conn.cursor()

    article_ids = set(i['article_id'] for i in issues if i['check'] == 'A08')
    if not article_ids:
        return 0

    for art_id in sorted(article_ids):
        lines = _read_fontes_lines(fontes_dir, art_id)
        if not lines:
            print(f"  {art_id}: fonte não encontrada")
            continue

        keywords = extract_keywords_en(lines)
        if keywords:
            print(f"  {art_id}: keywords_en extraídas ({len(keywords)} keywords)")
            if not dry_run:
                cur.execute("UPDATE articles SET keywords_en = ? WHERE id = ?",
                            (json.dumps(keywords, ensure_ascii=False), art_id))
            fixed += 1
        else:
            print(f"  {art_id}: extração falhou")

    if not dry_run and fixed:
        conn.commit()
    return fixed


def fix_a10(conn, slug, issues, dry_run):
    """A10: Resolver backfills — substituir ____ pelo autor da ref anterior."""
    fixed = 0
    cur = conn.cursor()

    # Agrupar issues por artigo
    articles = defaultdict(list)
    for issue in issues:
        if issue['check'] == 'A10':
            articles[issue['article_id']].append(issue['ref_index'])

    if not articles:
        return 0

    for art_id, ref_indices in sorted(articles.items()):
        cur.execute("SELECT references_ FROM articles WHERE id = ?", (art_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            continue

        try:
            refs = json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            print(f"  WARN: {art_id}: JSON inválido em references_, pulando")
            continue
        changed = False

        for idx in sorted(ref_indices):
            if idx >= len(refs):
                continue
            ref = refs[idx]
            m = UNDERSCORE_START.match(ref.strip())
            if not m:
                continue

            rest = m.group(2) if m.group(2) else ''

            # Encontrar autor: chain-walk para trás (pode haver cadeia de ______)
            author = None
            if idx > 0:
                for j in range(idx - 1, -1, -1):
                    prev = refs[j].strip()
                    if not UNDERSCORE_START.match(prev):
                        author = extract_author(prev)
                        break
                if author:
                    refs[idx] = author + ' ' + rest if rest else author
                    print(f"  {art_id} ref[{idx}]: backfill → {author[:40]}")
                    changed = True
                else:
                    print(f"  {art_id} ref[{idx}]: autor da ref anterior não extraído")
            else:
                print(f"  {art_id} ref[0]: backfill na primeira ref (precisa revisão manual)")

        if changed and not dry_run:
            cur.execute("UPDATE articles SET references_ = ? WHERE id = ?",
                        (json.dumps(refs, ensure_ascii=False), art_id))
            fixed += 1

    if not dry_run and fixed:
        conn.commit()
    return fixed


def fix_a11(conn, slug, issues, dry_run):
    """A11: Refs longas — split concatenadas + remover não-referências."""
    cur = conn.cursor()

    # Agrupar por artigo
    articles = defaultdict(list)
    for issue in issues:
        if issue['check'] == 'A11':
            articles[issue['article_id']].append(issue['ref_index'])

    if not articles:
        return 0, 0, 0

    total_split = 0
    total_removed = 0
    articles_changed = 0

    for art_id, ref_indices in sorted(articles.items()):
        cur.execute("SELECT references_ FROM articles WHERE id = ?", (art_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            continue

        try:
            refs = json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            print(f"  WARN: {art_id}: JSON inválido em references_, pulando")
            continue
        new_refs = []
        art_split = 0
        art_removed = 0

        for i, ref in enumerate(refs):
            if i in ref_indices and len(ref) > 500:
                # Tentar split
                parts = split_concatenated_refs(ref)
                if len(parts) > 1:
                    # Cada parte: verificar se é ref ou não
                    for part in parts:
                        part = part.strip()
                        if part and is_bibliographic_ref(part):
                            new_refs.append(part)
                        elif part:
                            art_removed += 1
                    art_split += len(parts) - 1
                else:
                    # Não separou — verificar se é ref ou não
                    if is_bibliographic_ref(ref):
                        new_refs.append(ref)
                    else:
                        art_removed += 1
            else:
                new_refs.append(ref)

        if art_split > 0 or art_removed > 0:
            if art_split:
                print(f"  {art_id}: {art_split} refs split")
            if art_removed:
                print(f"  {art_id}: {art_removed} não-refs removidas")

            if not dry_run:
                cur.execute("UPDATE articles SET references_ = ? WHERE id = ?",
                            (json.dumps(new_refs, ensure_ascii=False), art_id))
            total_split += art_split
            total_removed += art_removed
            articles_changed += 1

    if not dry_run and articles_changed:
        conn.commit()
    return articles_changed, total_split, total_removed


def fix_a12(conn, slug, issues, dry_run):
    """A12: Remover não-referências do campo references_."""
    cur = conn.cursor()

    # Agrupar por artigo
    articles = defaultdict(list)
    for issue in issues:
        if issue['check'] == 'A12':
            articles[issue['article_id']].append(issue['ref_index'])

    if not articles:
        return 0

    total_removed = 0

    for art_id, ref_indices in sorted(articles.items()):
        cur.execute("SELECT references_ FROM articles WHERE id = ?", (art_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            continue

        try:
            refs = json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            print(f"  WARN: {art_id}: JSON inválido em references_, pulando")
            continue
        indices_to_remove = set(ref_indices)
        new_refs = [r for i, r in enumerate(refs) if i not in indices_to_remove]
        removed = len(refs) - len(new_refs)

        if removed > 0:
            print(f"  {art_id}: {removed} não-refs removidas")
            if not dry_run:
                cur.execute("UPDATE articles SET references_ = ? WHERE id = ?",
                            (json.dumps(new_refs, ensure_ascii=False), art_id))
            total_removed += removed

    if not dry_run and total_removed:
        conn.commit()
    return total_removed


def fix_a13(conn, slug, issues, dry_run):
    """A13: Juntar URLs órfãs à ref anterior."""
    cur = conn.cursor()

    # Agrupar por artigo
    articles = defaultdict(list)
    for issue in issues:
        if issue['check'] == 'A13':
            articles[issue['article_id']].append(issue['ref_index'])

    if not articles:
        return 0

    total_joined = 0

    for art_id, ref_indices in sorted(articles.items()):
        cur.execute("SELECT references_ FROM articles WHERE id = ?", (art_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            continue

        try:
            refs = json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            print(f"  WARN: {art_id}: JSON inválido em references_, pulando")
            continue
        indices_to_remove = set()

        for idx in sorted(ref_indices, reverse=True):
            if idx >= len(refs) or idx == 0:
                continue
            url = refs[idx].strip()
            # Juntar à ref anterior
            refs[idx - 1] = refs[idx - 1].rstrip() + ' ' + url
            indices_to_remove.add(idx)

        if indices_to_remove:
            new_refs = [r for i, r in enumerate(refs) if i not in indices_to_remove]
            print(f"  {art_id}: {len(indices_to_remove)} URLs juntadas à ref anterior")
            if not dry_run:
                cur.execute("UPDATE articles SET references_ = ? WHERE id = ?",
                            (json.dumps(new_refs, ensure_ascii=False), art_id))
            total_joined += len(indices_to_remove)

    if not dry_run and total_joined:
        conn.commit()
    return total_joined


# ── Fix A19: abstract truncado ────────────────────────────────────────────────

# Marcadores que terminam a seção de abstract PT
PT_ABS_END_MARKERS = [
    re.compile(r'^\s*Palavras[\s-]*[Cc]have', re.IGNORECASE),
    re.compile(r'^\s*PALAVRAS[\s-]*CHAVE', re.IGNORECASE),
    re.compile(r'^\s*Abstract\s*:?\s*$', re.IGNORECASE),
    re.compile(r'^\s*ABSTRACT\s*:?\s*$', re.IGNORECASE),
    re.compile(r'^\s*Keywords?\s*:', re.IGNORECASE),
    re.compile(r'^\s*Resumen\s*:?\s*$', re.IGNORECASE),
]

# Marcadores que terminam a seção de abstract EN
EN_ABS_END_MARKERS = [
    re.compile(r'^\s*Keywords?\s*:', re.IGNORECASE),
    re.compile(r'^\s*KEY\s*WORDS?\s*:', re.IGNORECASE),
    re.compile(r'^\s*KEYWORDS?\s*:', re.IGNORECASE),
    re.compile(r'^\s*Introdução\b', re.IGNORECASE),
    re.compile(r'^\s*Introduction\b', re.IGNORECASE),
    re.compile(r'^\s*\d+[\.\)]\s+Introdução', re.IGNORECASE),
    re.compile(r'^\s*\d+[\.\)]\s+Introduction', re.IGNORECASE),
]

# Marcadores que iniciam a seção de abstract PT
PT_ABS_START_MARKERS = [
    re.compile(r'^\s*Resumo\s*:?\s*$', re.IGNORECASE),
    re.compile(r'^\s*RESUMO\s*:?\s*$', re.IGNORECASE),
]

# Números de página isolados (inseridos pelo pdftotext em quebras de página)
PAGE_NUMBER_RE = re.compile(r'^\s*\d{1,3}\s*$')


def re_extract_abstract(lines, field, current_text):
    """Tenta re-extrair abstract do fontes/ quando o atual está truncado.

    Retorna o texto corrigido ou None se não conseguir melhorar.
    """
    if not lines or not current_text:
        return None

    # Limpar números de página soltos
    cleaned_lines = []
    for line in lines:
        if PAGE_NUMBER_RE.match(line):
            continue
        cleaned_lines.append(line)

    full_text = ''.join(cleaned_lines)

    if field == 'abstract_en':
        # Usar extractor dedicado
        result = extract_abstract_en(cleaned_lines)
        if result and len(result) > len(current_text) and result.strip()[-1] in '.?!"\')»':
            return result
        return None

    if field in ('abstract', 'abstract_es'):
        # Para PT/ES: buscar o abstract no texto usando marcadores
        start_markers = PT_ABS_START_MARKERS if field == 'abstract' else [
            re.compile(r'^\s*Resumen\s*:?\s*$', re.IGNORECASE),
            re.compile(r'^\s*RESUMEN\s*:?\s*$', re.IGNORECASE),
        ]
        end_markers = PT_ABS_END_MARKERS if field == 'abstract' else [
            re.compile(r'^\s*Palabras[\s-]*[Cc]laves?\s*:', re.IGNORECASE),
            re.compile(r'^\s*Palabras[\s-]*[Cc]have\s*:', re.IGNORECASE),  # hybrid PT/ES
            re.compile(r'^\s*Abstract\s*:?\s*$', re.IGNORECASE),
            re.compile(r'^\s*ABSTRACT\s*:?\s*$', re.IGNORECASE),
        ]

        # Encontrar início do abstract
        start_idx = None
        for i, line in enumerate(cleaned_lines):
            for m in start_markers:
                if m.match(line):
                    start_idx = i + 1
                    break
            if start_idx is not None:
                break

        if start_idx is None:
            return None

        # Coletar linhas até o marcador de fim
        abs_lines = []
        for i in range(start_idx, len(cleaned_lines)):
            line = cleaned_lines[i]
            # Verificar se é marcador de fim
            is_end = False
            for m in end_markers:
                if m.match(line):
                    is_end = True
                    break
            if is_end:
                break
            abs_lines.append(line.strip())

        if not abs_lines:
            return None

        # Juntar e limpar
        result = ' '.join(l for l in abs_lines if l)
        result = re.sub(r'\s+', ' ', result).strip()

        if len(result) > len(current_text) and result[-1] in '.?!"\')»':
            return result

    return None


def read_plumber_refs(fontes_dir, art_id):
    """Lê referências do fontes estruturado (fontes_docx/ > fontes_plumber/).

    Retorna lista de strings de referência, ou None se não disponível.
    Usa apenas blocos com role='reference', excluindo footnotes e body text.
    """
    jsonl_path = _find_best_jsonl(fontes_dir, art_id)
    if not jsonl_path:
        return None

    _json = json
    refs_text = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                block = _json.loads(line)
            except _json.JSONDecodeError:
                continue
            if block.get('role') == 'reference':
                refs_text.append(block.get('text', ''))

    if not refs_text:
        return None

    # Juntar todos os blocos de referência e depois separar por ref individual
    # Os blocos podem conter múltiplas refs concatenadas (mesmo bloco de texto)
    full_text = '\n'.join(refs_text)

    # Separar por padrão ABNT (SOBRENOME, Nome) ou Chicago (Sobrenome, Nome)
    # no início de linha
    lines = full_text.split('\n')
    refs = []
    current = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Nova ref: começa com padrão de autor
        if (re.match(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ]{2,},\s', stripped) or
                re.match(r'^[A-Z][a-záéíóú]+,\s+[A-Z]', stripped) or
                re.match(r'^\[', stripped)):  # [s.a], [v.a]
            if current:
                refs.append(' '.join(current))
            current = [stripped]
        else:
            current.append(stripped)
    if current:
        refs.append(' '.join(current))

    return refs if refs else None


def read_plumber_abstract(fontes_dir, art_id, field='abstract'):
    """Lê abstract do fontes estruturado (fontes_docx/ > fontes_plumber/).

    Retorna texto do abstract, ou None se não disponível.
    field: 'abstract' para PT/principal, 'abstract_en' para EN.

    Para abstract_en, usa extract_en_from_plumber() de extrair_metadados_en.py
    que faz extração estruturada com verificação de blocos adjacentes.
    """
    jsonl_path = _find_best_jsonl(fontes_dir, art_id)
    if not jsonl_path:
        return None

    _json = json
    blocks = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                blocks.append(_json.loads(line))
            except (_json.JSONDecodeError, TypeError):
                continue

    # Para abstract_en: usar extração estruturada (com blocos adjacentes)
    if field == 'abstract_en':
        try:
            from extrair_metadados_en import extract_en_from_plumber
            result = extract_en_from_plumber(blocks)
            return result.get('abstract_en')
        except ImportError:
            pass

    # Para abstract PT: coletar blocos abstract
    abstract_blocks = [b for b in blocks if b.get('role') == 'abstract']
    if not abstract_blocks:
        return None

    in_en = False
    pt_parts = []

    for b in blocks:
        text = b.get('text', '').strip()
        if b.get('role') in ('heading', 'subheading'):
            if re.match(r'^(?:\d+[\.\s]*)?Abstract\b', text, re.IGNORECASE):
                in_en = True
            elif re.match(r'^(?:\d+[\.\s]*)?Resum[eo]\b', text, re.IGNORECASE):
                in_en = False
        elif b.get('role') == 'abstract':
            first_line = text.split('\n')[0].strip()
            if re.match(r'^Abstract\s*:', first_line, re.IGNORECASE):
                in_en = True
            elif re.match(r'^Resum[eo]\s*:', first_line, re.IGNORECASE):
                in_en = False

            if not in_en:
                pt_parts.append(text)

    return '\n'.join(pt_parts).strip() if pt_parts else None


def find_alt_source(fontes_dir, art_id):
    """Procura fontes alternativas ao pdftotext: fontes_doc/, docx, rtf, odt.

    Retorna path do .txt alternativo ou None.
    A hierarquia de preferência é:
    1. fontes_doc/{id}-doc.txt (texto convertido de .doc/.docx via LibreOffice)
    2. fontes_doc/{id}.txt
    """
    # Tentar fontes_doc/ (conversão de .doc/.docx)
    parent = os.path.dirname(fontes_dir)
    fontes_doc = os.path.join(parent, 'fontes_doc')
    if os.path.isdir(fontes_doc):
        for suffix in [f'{art_id}-doc.txt', f'{art_id}.txt']:
            alt = os.path.join(fontes_doc, suffix)
            if os.path.exists(alt):
                return alt
    return None


def fix_a19(conn, slug, issues, fontes_dir, dry_run):
    """A19: Re-extrair abstracts truncados do fontes/.

    Estratégia de re-extração:
    1. Se fontes_doc/ tem versão do artigo (convertido de .doc/.docx), usar primeiro
       (qualidade melhor que pdftotext — sem quebras de página, colunas, etc.)
    2. Senão, re-extrair do fontes/ (pdftotext) com limpeza de números de página
    3. Só substituir se o resultado for mais longo E terminar com pontuação válida
    """
    fixed = 0
    cur = conn.cursor()

    a19_issues = [i for i in issues if i['check'] == 'A19']
    if not a19_issues or not fontes_dir:
        return 0

    _VALID_ABSTRACT_COLS = {'abstract', 'abstract_en', 'abstract_es'}

    for issue in a19_issues:
        art_id = issue['article_id']
        field = issue['field']
        if field not in _VALID_ABSTRACT_COLS:
            raise ValueError(f"fix_a19: campo inválido '{field}'")

        # Ler abstract atual
        cur.execute(f"SELECT {field} FROM articles WHERE id = ?", (art_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            continue
        current = row[0].strip()

        # Tentar fonte alternativa primeiro (fontes_doc/)
        result = None
        alt_path = find_alt_source(fontes_dir, art_id)
        if alt_path:
            with open(alt_path, 'r', encoding='utf-8', errors='replace') as f:
                alt_lines = f.readlines()
            result = re_extract_abstract(alt_lines, field, current)
            if result:
                print(f"  {art_id}.{field}: re-extraído de fontes_doc/ ({len(current)}→{len(result)} chars)")

        # Tentar fontes_plumber/ (extração estruturada via pdfplumber)
        if not result and fontes_dir:
            plumber_result = read_plumber_abstract(fontes_dir, art_id, field)
            if plumber_result and len(plumber_result) > len(current) and plumber_result.strip()[-1] in '.?!"\')»':
                result = plumber_result
                print(f"  {art_id}.{field}: re-extraído de fontes_plumber/ ({len(current)}→{len(result)} chars)")

        # Fallback: fonte padrão (pdftotext ou plumber)
        if not result:
            lines = _read_fontes_lines(fontes_dir, art_id)
            if not lines:
                print(f"  {art_id}: fonte não encontrada")
                continue

            result = re_extract_abstract(lines, field, current)
            if result:
                print(f"  {art_id}.{field}: re-extraído ({len(current)}→{len(result)} chars)")

        if result:
            if not dry_run:
                cur.execute(f"UPDATE articles SET {field} = ? WHERE id = ?",
                            (result, art_id))
            fixed += 1
        else:
            print(f"  {art_id}.{field}: re-extração não melhorou")

    if not dry_run and fixed:
        conn.commit()
    return fixed


# ── Varredura completa de refs (sem depender do validation.json) ─────────────

def strip_section_header(ref):
    """Remove header de seção preposto ou aposto a uma referência.

    Ex: "Escritos Banham, Reyner. Teoria..." → "Banham, Reyner. Teoria..."
    Ex: "Revistas e Periódicos" → None (standalone header, remove entirely)
    Ex: "Rowe, Colin. ... 1999. Revistas e Periódicos" → "Rowe, Colin. ... 1999."
    """
    r = ref.strip()
    # Prefixo: header antes da ref
    for prefix in SECTION_HEADER_PREFIXES:
        if r.startswith(prefix):
            remainder = r[len(prefix):]
            if remainder and is_bibliographic_ref(remainder):
                return remainder

    # Sufixo: header no final da ref (colado após ponto final ou espaço)
    for prefix in SECTION_HEADER_PREFIXES:
        header = prefix.strip()
        # Procurar no final: "... 1999. Revistas e Periódicos"
        pattern = re.compile(r'\s+' + re.escape(header) + r'\s*$')
        m = pattern.search(r)
        if m:
            before = r[:m.start()].rstrip()
            if before and len(before) > 30:
                return before

    return ref


def split_at_page_break(ref):
    """Divide entrada com marcador de quebra de página (⏐ + número).

    Ex: "USP. São Carlos, 2003 ⏐ 27 Zein, Ruth Verde..." → 2 partes
    """
    m = PAGE_BREAK_RE.search(ref)
    if m:
        before = ref[:m.start()].strip()
        after = ref[m.end():].strip()
        # O "after" pode ter um número de página residual no início
        after = re.sub(r'^\d+\s+', '', after).strip()
        parts = []
        if before:
            parts.append(before)
        if after:
            parts.append(after)
        return parts
    return [ref]


def truncate_body_text(ref):
    """Trunca body text que se juntou ao final de uma referência.

    Ex: "Tese de doutorado. ETSAB-UPC. Pag. 145. Vilanova Artigas já utilizava..."
    → "Tese de doutorado. ETSAB-UPC."

    Retorna ref limpa, ou None se a ref inteira é body text.
    """
    r = ref.strip()
    if len(r) < 80:
        return r

    # Detectar início de texto narrativo após dados bibliográficos
    # Padrão: frase com verbo narrativo após ponto final
    narrative_starts = re.compile(
        r'(?<=\.)\s+(?='
        r'(?:[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ][a-záéíóúâêôãõç]+\s+(?:já|antes|depois|foi|eram|'
        r'comenta|utilizava|observa|afirma|também|posteriormente|'
        r'entretanto|todavia|contudo|porém|assim|logo|então|'
        r'argumenta|propõe|sugere|destaca|define|explica|'
        r'menciona|descreve|sustenta|demonstra|discute|analisa))'
        r'|(?:Na\s+sua\s+)|(?:No\s+seu\s+)|(?:Em\s+seu\s+)'
        r'|(?:Neste\s+)|(?:Nesta\s+)|(?:Segundo\s+)'
        r')'
    )
    m = narrative_starts.search(r)
    if m:
        before = r[:m.start()].rstrip()
        # Verificar que a parte antes tem conteúdo bibliográfico mínimo
        if len(before) > 20:
            return before

    return r


def normalize_ref_for_dedup(ref):
    """Normaliza ref para comparação de near-duplicates."""
    r = ref.strip().lower()
    # Remover URLs (ANTES de remover pontuação para que http:// seja reconhecido)
    r = re.sub(r'<?\s*https?://\S+>?', '', r)
    # Remover pontuação e espaços extras
    r = re.sub(r'[:.;,]+', '', r)
    r = re.sub(r'\s+', ' ', r)
    # Remover "op cit", "pag N" variações
    r = re.sub(r'\bp[aá]g\.?\s*\d+', '', r)
    # Normalizar meses abreviados PT/EN/ES (dez→dec, jan→jan, fev→feb, etc.)
    month_map = {
        'jan': 'jan', 'fev': 'feb', 'mar': 'mar', 'abr': 'apr', 'mai': 'may',
        'jun': 'jun', 'jul': 'jul', 'ago': 'aug', 'set': 'sep', 'out': 'oct',
        'nov': 'nov', 'dez': 'dec',
        'ene': 'jan', 'feb': 'feb', 'abr': 'apr', 'may': 'may',
        'ago': 'aug', 'sep': 'sep', 'oct': 'oct', 'dic': 'dec',
    }
    for pt, en in month_map.items():
        r = re.sub(rf'\b{pt}\b', en, r)
    return r.strip()


def sweep_all_refs(conn, slug, dry_run):
    """Varredura completa de refs em 8 passadas:

    0. Remover lixo grosso: body text, figure captions, agradecimentos, headers standalone
    0b. Strip headers de seção preposto a refs
    0c. Split em marcadores de page break (⏐)
    1. Juntar fragmentos à ref anterior (quebras de página/linha do pdftotext)
    2. Limpar endnotes numeradas: se contém ref, extrair; senão, remover
    3. Split de refs concatenadas (>500 chars)
    4. Remover não-referências (notas, comentários, CVs)
    5. Truncar body text do final de refs mistas
    6. Remover near-duplicates

    Não depende do validation.json — processa diretamente o banco.
    Mais abrangente que fix_a11/fix_a12 (que só processam issues reportados).
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT id, references_ FROM articles
        WHERE seminar_slug = ? AND references_ IS NOT NULL AND references_ != '[]'
    """, (slug,))

    total_notes_cut = 0
    total_junk = 0
    total_header_stripped = 0
    total_pagebreak = 0
    total_joined = 0
    total_endnote_stripped = 0
    total_endnote_removed = 0
    total_split = 0
    total_removed = 0
    total_truncated = 0
    total_dedup = 0
    articles_changed = 0

    for art_id, refs_text in cur.fetchall():
        try:
            refs = json.loads(refs_text)
        except (json.JSONDecodeError, TypeError):
            print(f"  WARN: {art_id}: refs JSON inválido, pulando")
            continue
        original_refs = list(refs)
        art_junk = 0
        art_header_stripped = 0
        art_pagebreak = 0
        art_joined = 0
        art_endnote_stripped = 0
        art_endnote_removed = 0
        art_split = 0
        art_removed = 0
        art_truncated = 0
        art_dedup = 0

        # ── Passada 0-pre: cortar bloco de NOTAS numeradas no final ──────
        # Muitos artigos têm BIBLIOGRAFIA seguida de NOTAS. As notas são
        # numeradas (1., 2., 3. ou ¹²³) e contêm narrativa/Op.cit./Ibid.
        # Detectar o ponto de corte e remover tudo depois.
        art_notes_cut = 0
        note_indicators = re.compile(
            r'^(\d{1,3}[.)]\s|[¹²³⁴⁵⁶⁷⁸⁹⁰]+\s|'
            r'Op\.\s*cit|Ibid|Idem\b|Cfr\.\s|'
            r'Ver\s+(também|igualmente|especialmente)\b)',
            re.IGNORECASE
        )
        # Encontrar o ponto de corte: sequência de 3+ entradas consecutivas
        # no final que são notas (numeradas ou com marcadores de nota)
        note_start = len(refs)
        consecutive_notes = 0
        for i in range(len(refs) - 1, -1, -1):
            r = refs[i].strip()
            if note_indicators.match(r) or (has_narrative_structure(r) and len(r) > 100):
                consecutive_notes += 1
                note_start = i
            else:
                # Se já acumulou 3+ notas consecutivas, parar
                if consecutive_notes >= 3:
                    break
                # Senão, resetar
                consecutive_notes = 0
                note_start = len(refs)
        if consecutive_notes >= 3 and note_start < len(refs):
            art_notes_cut = len(refs) - note_start
            refs = refs[:note_start]

        # ── Passada 0: remover lixo grosso + strip hífens iniciais ─────────
        clean0 = []
        for ref in refs:
            ref = ref.strip()
            if not ref:
                continue
            # Strip hífens/traços iniciais (marcadores de lista)
            ref = re.sub(r'^[-–—]+\s*', '', ref).strip()
            if not ref:
                continue
            if is_gross_junk(ref):
                art_junk += 1
            else:
                clean0.append(ref)
        refs = clean0

        # ── Passada 0b: strip headers de seção preposto a refs ───────────
        clean0b = []
        for ref in refs:
            stripped = strip_section_header(ref)
            if stripped != ref:
                art_header_stripped += 1
            clean0b.append(stripped)
        refs = clean0b

        # ── Passada 0c: split em page break markers (⏐) ─────────────────
        clean0c = []
        for ref in refs:
            parts = split_at_page_break(ref)
            if len(parts) > 1:
                art_pagebreak += len(parts) - 1
            clean0c.extend(parts)
        refs = clean0c

        # ── Passada 1: juntar fragmentos à ref anterior ──────────────────
        # Safeguard: só juntar se NÃO for uma ref bibliográfica por si só
        # (ex: "Banham, Reyner. op. cit. p. 361" é ref curta, não fragmento)
        merged = []
        for ref in refs:
            ref = ref.strip()
            if not ref:
                continue
            if merged and is_fragment(ref) and not is_bibliographic_ref(ref):
                # Juntar ao último elemento
                merged[-1] = merged[-1].rstrip() + ' ' + ref
                art_joined += 1
            else:
                merged.append(ref)
        refs = merged

        # ── Passada 2: endnotes numeradas ────────────────────────────────
        cleaned = []
        for ref in refs:
            is_endnote, stripped = is_numbered_endnote(ref)
            if is_endnote and stripped:
                # Endnote com ref bibliográfica dentro: manter só a ref
                cleaned.append(stripped)
                art_endnote_stripped += 1
            elif NOTE_NUMBER_RE.match(ref.strip()):
                # Endnote numérica sem ref bibliográfica: remover
                art_endnote_removed += 1
            else:
                cleaned.append(ref)
        refs = cleaned

        # ── Passada 3: split de refs concatenadas (>300 chars) ───────────
        split_refs = []
        for ref in refs:
            if len(ref) > 300:
                parts = split_concatenated_refs(ref)
                if len(parts) > 1:
                    for part in parts:
                        part = part.strip()
                        if part:
                            split_refs.append(part)
                    art_split += len(parts) - 1
                else:
                    split_refs.append(ref)
            else:
                split_refs.append(ref)
        refs = split_refs

        # ── Passada 4: remover não-referências ───────────────────────────
        pass4 = []
        for ref in refs:
            if is_bibliographic_ref(ref):
                pass4.append(ref)
            else:
                art_removed += 1
        refs = pass4

        # ── Passada 5: truncar body text do final de refs mistas ─────────
        pass5 = []
        for ref in refs:
            truncated = truncate_body_text(ref)
            if truncated and truncated != ref:
                art_truncated += 1
                pass5.append(truncated)
            elif truncated:
                pass5.append(truncated)
        refs = pass5

        # ── Passada 6: remover near-duplicates ───────────────────────────
        final_refs = []
        seen_normalized = set()
        for ref in refs:
            norm = normalize_ref_for_dedup(ref)
            if norm in seen_normalized:
                art_dedup += 1
            else:
                seen_normalized.add(norm)
                final_refs.append(ref)

        changed = (art_notes_cut > 0 or art_junk > 0 or art_header_stripped > 0 or
                   art_pagebreak > 0 or art_joined > 0 or art_endnote_stripped > 0 or
                   art_endnote_removed > 0 or art_split > 0 or art_removed > 0 or
                   art_truncated > 0 or art_dedup > 0)

        if changed:
            details = []
            if art_notes_cut:
                details.append(f"{art_notes_cut} notas cortadas do final")
            if art_junk:
                details.append(f"{art_junk} lixo grosso removido")
            if art_header_stripped:
                details.append(f"{art_header_stripped} headers de seção removidos")
            if art_pagebreak:
                details.append(f"{art_pagebreak} page breaks split")
            if art_joined:
                details.append(f"{art_joined} fragmentos juntados")
            if art_endnote_stripped:
                details.append(f"{art_endnote_stripped} endnotes limpas")
            if art_endnote_removed:
                details.append(f"{art_endnote_removed} endnotes removidas")
            if art_split:
                details.append(f"{art_split} refs split")
            if art_removed:
                details.append(f"{art_removed} não-refs removidas")
            if art_truncated:
                details.append(f"{art_truncated} body text truncado")
            if art_dedup:
                details.append(f"{art_dedup} duplicatas removidas")
            print(f"  {art_id}: {', '.join(details)}")

            if not dry_run:
                cur.execute("UPDATE articles SET references_ = ? WHERE id = ?",
                            (json.dumps(final_refs, ensure_ascii=False), art_id))
            total_notes_cut += art_notes_cut
            total_junk += art_junk
            total_header_stripped += art_header_stripped
            total_pagebreak += art_pagebreak
            total_joined += art_joined
            total_endnote_stripped += art_endnote_stripped
            total_endnote_removed += art_endnote_removed
            total_split += art_split
            total_removed += art_removed
            total_truncated += art_truncated
            total_dedup += art_dedup
            articles_changed += 1

    if not dry_run and articles_changed:
        conn.commit()

    print(f"\n  Varredura completa: {articles_changed} artigos alterados")
    if total_notes_cut:
        print(f"  Notas cortadas do final: {total_notes_cut}")
    if total_junk:
        print(f"  Lixo grosso removido: {total_junk}")
    if total_header_stripped:
        print(f"  Headers de seção removidos: {total_header_stripped}")
    if total_pagebreak:
        print(f"  Page breaks split: {total_pagebreak}")
    if total_joined:
        print(f"  Fragmentos juntados: {total_joined}")
    if total_endnote_stripped:
        print(f"  Endnotes limpas (ref extraída): {total_endnote_stripped}")
    if total_endnote_removed:
        print(f"  Endnotes removidas (sem ref): {total_endnote_removed}")
    if total_split:
        print(f"  Refs split: {total_split}")
    if total_removed:
        print(f"  Não-refs removidas: {total_removed}")
    if total_truncated:
        print(f"  Body text truncado: {total_truncated}")
    if total_dedup:
        print(f"  Duplicatas removidas: {total_dedup}")

    return articles_changed, total_split, total_removed


# ── Main ─────────────────────────────────────────────────────────────────────

def run_one_pass(conn, slug, issues, fontes_dir, dry_run, only=None):
    """Executa um passe de correções. Retorna dict de resultados."""
    counts = defaultdict(int)
    for i in issues:
        counts[i['check']] += 1

    results = {}

    # A07: abstract_en
    if 'A07' in counts and (not only or only == 'A07'):
        print(f"── A07: Extrair abstract_en ({counts['A07']} artigos) ──")
        if fontes_dir:
            results['A07'] = fix_a07(conn, slug, issues, fontes_dir, dry_run)
        else:
            results['A07'] = 0
        print()

    # A08: keywords_en
    if 'A08' in counts and (not only or only == 'A08'):
        print(f"── A08: Extrair keywords_en ({counts['A08']} artigos) ──")
        if fontes_dir:
            results['A08'] = fix_a08(conn, slug, issues, fontes_dir, dry_run)
        else:
            results['A08'] = 0
        print()

    # A10: backfills
    if 'A10' in counts and (not only or only == 'A10'):
        print(f"── A10: Resolver backfills ({counts['A10']} refs) ──")
        results['A10'] = fix_a10(conn, slug, issues, dry_run)
        print()

    # A12: não-referências (ANTES de A11)
    if 'A12' in counts and (not only or only == 'A12'):
        print(f"── A12: Remover não-referências ({counts['A12']} refs) ──")
        results['A12'] = fix_a12(conn, slug, issues, dry_run)
        print()

    # A11: refs longas
    if 'A11' in counts and (not only or only == 'A11'):
        print(f"── A11: Split refs longas ({counts['A11']} refs) ──")
        arts, split, removed = fix_a11(conn, slug, issues, dry_run)
        results['A11'] = {'articles': arts, 'split': split, 'removed': removed}
        print()

    # A13: URLs órfãs
    if 'A13' in counts and (not only or only == 'A13'):
        print(f"── A13: Juntar URLs órfãs ({counts['A13']} refs) ──")
        results['A13'] = fix_a13(conn, slug, issues, dry_run)
        print()

    # A19: abstracts truncados
    if 'A19' in counts and (not only or only == 'A19'):
        print(f"── A19: Re-extrair abstracts truncados ({counts['A19']} artigos) ──")
        if fontes_dir:
            results['A19'] = fix_a19(conn, slug, issues, fontes_dir, dry_run)
        else:
            results['A19'] = 0
        print()

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Corrige issues do validate_metadata.py sistematicamente')
    parser.add_argument('--slug', required=True, help='Seminário a processar')
    parser.add_argument('--dry-run', action='store_true',
                        help='Mostrar o que seria feito sem alterar o banco')
    parser.add_argument('--only', metavar='CHECK',
                        help='Processar apenas este check (ex: A11)')
    parser.add_argument('--sweep-refs', action='store_true',
                        help='Varredura completa de refs (não depende do validation.json)')
    parser.add_argument('--clean-keywords', action='store_true',
                        help='Limpeza de keywords (split, garbage, trim, dedup)')
    parser.add_argument('--loop', action='store_true',
                        help='Ciclo validate→fix→validate até convergir (max 5 iterações)')
    args = parser.parse_args()

    slug = args.slug
    conn = sqlite3.connect(DB_PATH)

    # Limpeza de keywords (independente do validation.json)
    if args.clean_keywords:
        print(f"=== Limpeza de keywords — {slug} ===")
        clean_keywords(conn, slug, args.dry_run)
        if args.dry_run:
            print("\nDRY RUN — nenhuma alteração aplicada")
        conn.close()
        return

    # Varredura completa de refs (independente do validation.json)
    if args.sweep_refs:
        print(f"=== Varredura completa de referências — {slug} ===")
        sweep_all_refs(conn, slug, args.dry_run)
        if args.dry_run:
            print("\nDRY RUN — nenhuma alteração aplicada")
        conn.close()
        return

    # Modo loop: validate → fix → validate até convergir
    if args.loop and not args.dry_run:
        # Import validate_metadata inline (circular dep prevention)
        from validate_metadata import validate_seminar, save_report

        fontes_dir, fontes_tipo = find_fontes_dir(slug)
        only = args.only.upper() if args.only else None
        # IMPORTANTE: rodar --sweep-refs ANTES de --loop (são comandos separados).
        # O sweep resolve A10/A11/A12/A13. Depois re-rodar clean_references.py (1.2b+).
        # O loop foca apenas em extração de fontes/ (A07, A08, A19).
        fixable_checks = {'A07', 'A08', 'A19'}

        for iteration in range(1, 6):
            print(f"\n{'='*60}")
            print(f"=== Iteração {iteration} — {slug} ===")
            print(f"{'='*60}\n")

            # 1. Validar
            issues, auto_fixed, profile = validate_seminar(conn, slug, fix=True)

            # 2. Filtrar issues corrigíveis
            fixable = [i for i in issues
                       if i['check'] in fixable_checks and not i.get('auto_fixable')]
            if only:
                fixable = [i for i in fixable if i['check'] == only]

            if not fixable:
                print(f"\nZero issues corrigíveis restantes. Convergiu em {iteration} iterações.")
                save_report(slug, issues, auto_fixed, profile)
                break

            counts = defaultdict(int)
            for i in fixable:
                counts[i['check']] += 1
            print(f"Issues corrigíveis: {', '.join(f'{k}={v}' for k, v in sorted(counts.items()))}")
            print()

            # 3. Corrigir
            results = run_one_pass(conn, slug, fixable, fontes_dir, dry_run=False, only=only)

            # 4. Verificar se algo mudou
            total_fixed = 0
            for r in results.values():
                if isinstance(r, dict):
                    total_fixed += r.get('split', 0) + r.get('removed', 0) + r.get('articles', 0)
                elif isinstance(r, int):
                    total_fixed += r

            if total_fixed == 0:
                print(f"\nNenhuma correção aplicada. Restantes são dados genuinamente ausentes.")
                save_report(slug, issues, auto_fixed, profile)
                break
        else:
            print(f"\nATENÇÃO: Não convergiu em 5 iterações. Verificar manualmente.")

        # Final: salvar relatório
        issues, auto_fixed, profile = validate_seminar(conn, slug, fix=True)
        save_report(slug, issues, auto_fixed, profile)

        remaining = [i for i in issues if not i.get('auto_fixable')]
        print(f"\n=== Resultado final: {len(remaining)} issues restantes ===")
        remaining_counts = defaultdict(int)
        for i in remaining:
            remaining_counts[i['check']] += 1
        for check, count in sorted(remaining_counts.items()):
            print(f"  {check}: {count}")

        conn.close()
        return

    # Modo single-pass (default)
    report_path = os.path.join(BASE_DIR, 'revisao', f'{slug}-validation.json')
    if not os.path.exists(report_path):
        print(f"ERRO: {report_path} não encontrado. Rode validate_metadata.py primeiro.")
        conn.close()
        sys.exit(1)

    with open(report_path, 'r') as f:
        report = json.load(f)

    issues = report.get('issues', [])
    if not issues:
        print(f"Nenhum issue para corrigir em {slug}")
        conn.close()
        return

    only = args.only.upper() if args.only else None
    if only:
        issues = [i for i in issues if i['check'] == only]
        if not issues:
            print(f"Nenhum issue {only} encontrado")
            conn.close()
            return

    counts = defaultdict(int)
    for i in issues:
        counts[i['check']] += 1

    print(f"=== Correção de issues — {slug} ===")
    print(f"Issues a processar: {', '.join(f'{k}={v}' for k, v in sorted(counts.items()))}")
    print()

    fontes_dir, fontes_tipo = find_fontes_dir(slug)
    results = run_one_pass(conn, slug, issues, fontes_dir, args.dry_run, only)

    # Resumo
    print("=== Resumo ===")
    for check, result in sorted(results.items()):
        if isinstance(result, dict):
            print(f"  {check}: {result}")
        else:
            print(f"  {check}: {result} corrigidos")

    skipped = [c for c in counts if c not in results]
    if skipped:
        print(f"  Não corrigíveis automaticamente: {', '.join(sorted(skipped))}")

    if args.dry_run:
        print("\nDRY RUN — nenhuma alteração aplicada")
    else:
        print("\nAlterações aplicadas. Re-rodar validate_metadata.py para verificar.")

    conn.close()


if __name__ == '__main__':
    main()
