#!/usr/bin/env python3
"""
Validação abrangente de metadados de artigos no anais.db.

Roda APÓS a revisão automática (Fase 1) e ANTES do HTML de revisão (Fase 2).
Detecta erros que passaram pela limpeza automática e os classifica em:
- Auto-fix: corrigíveis por heurística (aplicados com --fix)
- Report: requerem revisão humana ou LLM

Complementa (não duplica) os scripts existentes:
- validar_abstracts.py: swaps PT↔EN, truncamento, keywords vazadas
- check_references.py: refs concatenadas por padrão, fragmentos curtos

Princípio: entender o padrão do evento antes de sinalizar campos faltantes.
Se <30% dos artigos têm abstract_en, não sinalizar falta de abstract_en.

Uso:
    python3 scripts/validate_metadata.py --slug sdbr09 --dry-run
    python3 scripts/validate_metadata.py --slug sdbr09 --fix
    python3 scripts/validate_metadata.py --slug sdbr09 --report-only
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'anais.db')

# Importar de scripts existentes
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))
from clean_references import UNDERSCORE_START, BARE_URL
from extrair_metadados_en import find_fontes_dir, ABSTRACT_MARKERS, KW_EN_MARKERS
from validar_abstracts import detect_language

# ── Padrões ──────────────────────────────────────────────────────────────────

# Marcadores de abstract/resumen em espanhol no fontes/
RESUMEN_MARKERS = [
    re.compile(r'^\s*RESUMEN\s*:?\s*$', re.IGNORECASE),
    re.compile(r'^\s*Resumen\s*:?\s*$'),
]

# Marcadores de keywords ES
KW_ES_MARKERS = [
    re.compile(r'^\s*Palabras[\s-]*[Cc]laves?\s*:', re.IGNORECASE),
    re.compile(r'^\s*PALABRAS[\s-]*CLAVES?\s*:', re.IGNORECASE),
]

# Conteúdo não-referência nas refs
# CUIDADO: "Martins Fontes" é editora, "Fontes" é sobrenome — não pegar esses.
# Padrões devem exigir posição (início da ref) ou contexto (": ", "das figuras").
NONREF_PATTERNS = [
    re.compile(r'^\s*(Currículo|Curriculum Vitae|Curriculum Lattes)\b', re.IGNORECASE),
    re.compile(r'^\s*CV\s+', re.IGNORECASE),
    re.compile(r'\b(agradeciment|financiament|bolsa de pesquisa|bolsista)\b', re.IGNORECASE),
    re.compile(r'\b(FAPESP|CNPq|CAPES|FAPERJ|FAPEMIG)\b.*\b(processo|bolsa|apoio|projeto)\b', re.IGNORECASE),
    re.compile(r'^\s*Fontes?\s+(das?\s+)?(figuras?|imagens?|ilustraç)', re.IGNORECASE),
    re.compile(r'^\s*Créditos?\s+(das?\s+)?(figuras?|imagens?|ilustraç|fotos?)', re.IGNORECASE),
    re.compile(r'^\s*Fonte:\s', re.IGNORECASE),
    re.compile(r'^\s*Crédito:\s', re.IGNORECASE),
]

# Contaminação de abstract (CV, email, afiliação)
EMAIL_RE = re.compile(r'\S+@\S+\.\S+')
AFFILIATION_START = re.compile(
    r'^\s*(\d\s*)?(Professor[ae]?\s+(d[aoe]|adjunt|titular|associad)|'
    r'Doutor[ae]?\s+(em|pel[ao])|Mestrando|Doutorando|Graduando|'
    r'Arquiteto[ae]?\s+(e\s+urbanista|formad[ao]|pel[ao])|'
    r'Bolsista|Pesquisador[ae]?\s+(d[aoe]|n[ao])|Docente|Discente|'
    r'Mestre\s+em|Doutor\s+em)',
    re.IGNORECASE
)

# Limiar para "campo esperado" no perfil do seminário
FIELD_THRESHOLD = 0.30  # 30%


def build_profile(cur, slug):
    """Constrói perfil do seminário: % de preenchimento por campo."""
    cur.execute("""
        SELECT COUNT(*) FROM articles
        WHERE seminar_slug = ? AND document_type NOT IN ('mesa', 'resumo')
    """, (slug,))
    total = cur.fetchone()[0]
    if total == 0:
        return None

    fields = {
        'abstract': "abstract IS NOT NULL AND abstract != ''",
        'abstract_en': "abstract_en IS NOT NULL AND abstract_en != ''",
        'abstract_es': "abstract_es IS NOT NULL AND abstract_es != ''",
        'keywords': "keywords IS NOT NULL AND keywords != '' AND keywords != '[]'",
        'keywords_en': "keywords_en IS NOT NULL AND keywords_en != '' AND keywords_en != '[]'",
        'keywords_es': "keywords_es IS NOT NULL AND keywords_es != '' AND keywords_es != '[]'",
        'references_': "references_ IS NOT NULL AND references_ != '' AND references_ != '[]'",
    }

    profile = {'total': total, 'locale_es': 0}
    for field, condition in fields.items():
        cur.execute(f"""
            SELECT COUNT(*) FROM articles
            WHERE seminar_slug = ? AND document_type NOT IN ('mesa', 'resumo')
            AND {condition}
        """, (slug,))
        count = cur.fetchone()[0]
        profile[field] = count
        profile[f'{field}_pct'] = count / total

    cur.execute("""
        SELECT COUNT(*) FROM articles
        WHERE seminar_slug = ? AND document_type NOT IN ('mesa', 'resumo')
        AND locale = 'es'
    """, (slug,))
    profile['locale_es'] = cur.fetchone()[0]

    return profile


def is_field_expected(profile, field):
    """Retorna True se o campo é esperado (≥30% preenchido no seminário)."""
    return profile.get(f'{field}_pct', 0) >= FIELD_THRESHOLD


def has_marker(lines, markers):
    """Verifica se alguma linha do fontes/ tem um dos marcadores."""
    for line in lines:
        for m in markers:
            if m.match(line):
                return True
    return False


def read_fontes(fontes_dir, article_id):
    """Lê o arquivo fontes/ de um artigo. Retorna lista de linhas ou None."""
    # Tentar {id}.txt (sem .pdf)
    base = article_id
    path = os.path.join(fontes_dir, f'{base}.txt')
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.readlines()
    except Exception:
        return None


# ── Checks ───────────────────────────────────────────────────────────────────

def check_cross_language(article, profile):
    """A01-A04: cruzamentos de idioma (abs vs kw no mesmo idioma)."""
    issues = []
    aid = article['id']

    # A01: abstract_en existe mas keywords_en falta
    if article['abstract_en'] and not article['keywords_en']:
        if is_field_expected(profile, 'keywords_en'):
            issues.append({
                'check': 'A01', 'article_id': aid, 'field': 'keywords_en',
                'severity': 'warning', 'auto_fixable': False,
                'detail': 'abstract_en presente mas keywords_en faltando',
                'suggestion': 'Extrair keywords_en do fontes/ ou do PDF',
            })

    # A02: keywords_en existe mas abstract_en falta
    if article['keywords_en'] and not article['abstract_en']:
        if is_field_expected(profile, 'abstract_en'):
            issues.append({
                'check': 'A02', 'article_id': aid, 'field': 'abstract_en',
                'severity': 'warning', 'auto_fixable': False,
                'detail': 'keywords_en presente mas abstract_en faltando',
                'suggestion': 'Extrair abstract_en do fontes/ ou do PDF',
            })

    # A03: abstract_es existe mas keywords_es falta
    if article['abstract_es'] and not article['keywords_es']:
        issues.append({
            'check': 'A03', 'article_id': aid, 'field': 'keywords_es',
            'severity': 'warning', 'auto_fixable': False,
            'detail': 'abstract_es presente mas keywords_es faltando',
            'suggestion': 'Extrair keywords_es do fontes/ ou do PDF',
        })

    # A04: keywords_es existe mas abstract_es falta
    if article['keywords_es'] and not article['abstract_es']:
        issues.append({
            'check': 'A04', 'article_id': aid, 'field': 'abstract_es',
            'severity': 'warning', 'auto_fixable': False,
            'detail': 'keywords_es presente mas abstract_es faltando',
            'suggestion': 'Extrair abstract_es do fontes/ ou do PDF',
        })

    return issues


def check_locale_fields(article):
    """A05-A06: locale=es mas campos ES vazios (abstract e keywords em campo PT)."""
    issues = []
    aid = article['id']

    if article['locale'] != 'es':
        return issues

    # A05 REMOVIDO: em locale=es, abstract já contém o resumo em espanhol.
    # Copiar abstract→abstract_es é redundante (A21 NULLaria de volta, criando ciclo).
    # abstract_es é para artigos PT/EN que TAMBÉM têm resumen em ES (segundo idioma).

    # A06 REMOVIDO: mesma lógica do A05 — em locale=es, keywords já está em espanhol.
    # keywords_es é para artigos PT/EN que TAMBÉM têm palabras clave em ES.

    return issues


def check_fontes_markers(article, fontes_lines, profile):
    """A07-A09: marcadores no fontes/ indicam metadados não extraídos."""
    issues = []
    aid = article['id']

    if fontes_lines is None:
        return issues

    # A07: marcador "Abstract" no fontes/ mas abstract_en vazio
    if not article['abstract_en'] and is_field_expected(profile, 'abstract_en'):
        if has_marker(fontes_lines, ABSTRACT_MARKERS):
            issues.append({
                'check': 'A07', 'article_id': aid, 'field': 'abstract_en',
                'severity': 'info', 'auto_fixable': False,
                'detail': 'Marcador "Abstract" encontrado no fontes/ mas abstract_en vazio',
                'suggestion': 'Rodar extrair_metadados_en.py --force ou extrair manualmente',
            })

    # A08: marcador "Keywords" no fontes/ mas keywords_en vazio
    if not article['keywords_en'] and is_field_expected(profile, 'keywords_en'):
        if has_marker(fontes_lines, KW_EN_MARKERS):
            issues.append({
                'check': 'A08', 'article_id': aid, 'field': 'keywords_en',
                'severity': 'info', 'auto_fixable': False,
                'detail': 'Marcador "Keywords" encontrado no fontes/ mas keywords_en vazio',
                'suggestion': 'Rodar extrair_metadados_en.py --force ou extrair manualmente',
            })

    # A09: marcador "Resumen" no fontes/ mas abstract_es vazio
    if not article['abstract_es']:
        if article['locale'] == 'es' or is_field_expected(profile, 'abstract_es'):
            if has_marker(fontes_lines, RESUMEN_MARKERS):
                issues.append({
                    'check': 'A09', 'article_id': aid, 'field': 'abstract_es',
                    'severity': 'info', 'auto_fixable': False,
                    'detail': 'Marcador "Resumen" encontrado no fontes/ mas abstract_es vazio',
                    'suggestion': 'Extrair abstract_es do fontes/ ou do PDF',
                })

    return issues


def check_refs_backfill(article):
    """A10: backfill pendente — refs começando com marcadores de repetição."""
    issues = []
    refs = article.get('refs_parsed', [])
    if not refs:
        return issues

    for i, ref in enumerate(refs):
        ref_stripped = ref.strip()
        if UNDERSCORE_START.match(ref_stripped):
            issues.append({
                'check': 'A10', 'article_id': article['id'], 'field': 'references_',
                'severity': 'warning', 'auto_fixable': False,
                'ref_index': i,
                'detail': f'Backfill pendente: "{ref_stripped[:60]}..."',
                'suggestion': 'Verificar extract_author() na ref anterior ou corrigir manualmente',
            })

    return issues


def check_refs_long(article):
    """A11: refs > 500 chars (provavelmente concatenadas).

    Nota: sweep_refs usa threshold de 300 para TENTAR split, mas não reporta
    se não acha boundary. Aqui reportamos apenas >500 — alta probabilidade
    de concatenação genuína. Refs de 300-500 chars são comuns (teses, URLs).
    """
    issues = []
    refs = article.get('refs_parsed', [])
    if not refs:
        return issues

    for i, ref in enumerate(refs):
        if len(ref) > 500:
            issues.append({
                'check': 'A11', 'article_id': article['id'], 'field': 'references_',
                'severity': 'warning', 'auto_fixable': False,
                'ref_index': i,
                'detail': f'Ref muito longa ({len(ref)} chars), possível concatenação: "{ref[:80]}..."',
                'suggestion': 'Verificar e separar se necessário',
            })

    return issues


def check_refs_nonref(article):
    """A12: conteúdo não-referência nas refs."""
    issues = []
    refs = article.get('refs_parsed', [])
    if not refs:
        return issues

    for i, ref in enumerate(refs):
        for pattern in NONREF_PATTERNS:
            if pattern.search(ref):
                issues.append({
                    'check': 'A12', 'article_id': article['id'], 'field': 'references_',
                    'severity': 'warning', 'auto_fixable': False,
                    'ref_index': i,
                    'detail': f'Possível não-referência: "{ref[:80]}..."',
                    'suggestion': 'Verificar e remover se não for referência bibliográfica',
                })
                break  # só 1 issue por ref

    return issues


def check_refs_orphan_urls(article):
    """A13: URLs órfãs (ref é só URL — clean_references deveria ter juntado)."""
    issues = []
    refs = article.get('refs_parsed', [])
    if not refs:
        return issues

    for i, ref in enumerate(refs):
        if BARE_URL.match(ref.strip()):
            issues.append({
                'check': 'A13', 'article_id': article['id'], 'field': 'references_',
                'severity': 'info', 'auto_fixable': False,
                'ref_index': i,
                'detail': f'URL órfã: "{ref.strip()[:80]}"',
                'suggestion': 'Juntar à ref anterior ou verificar se é ref válida',
            })

    return issues


def check_abstract_contamination(article):
    """A14: abstract contém email, afiliação ou CV."""
    issues = []
    aid = article['id']

    for field_name in ('abstract', 'abstract_en', 'abstract_es'):
        text = article.get(field_name)
        if not text:
            continue

        problems = []

        # Email no abstract
        if EMAIL_RE.search(text):
            problems.append('contém email')

        # Afiliação no início
        first_line = text.split('\n')[0] if '\n' in text else text[:100]
        if AFFILIATION_START.match(first_line):
            problems.append('começa com afiliação/título acadêmico')

        if problems:
            issues.append({
                'check': 'A14', 'article_id': aid, 'field': field_name,
                'severity': 'warning', 'auto_fixable': False,
                'detail': f'{field_name}: {", ".join(problems)}',
                'suggestion': 'Verificar e limpar o abstract',
            })

    return issues


def check_locale_mismatch(article):
    """A15: locale não bate com o idioma do abstract."""
    issues = []
    aid = article['id']

    if not article['abstract']:
        return issues

    lang, conf = detect_language(article['abstract'])
    if conf < 0.5:
        return issues

    locale = article['locale']
    locale_lang = 'pt' if locale and locale.startswith('pt') else locale

    if lang == 'es' and locale_lang != 'es':
        issues.append({
            'check': 'A15', 'article_id': aid, 'field': 'locale',
            'severity': 'warning', 'auto_fixable': True,
            'detail': f'Abstract detectado como espanhol (conf={conf:.2f}) mas locale={locale}',
            'suggestion': 'Corrigir locale para "es"',
            'fix_action': {'set_field': 'locale', 'value': 'es'},
        })
    elif lang == 'en' and locale_lang != 'en':
        issues.append({
            'check': 'A15', 'article_id': aid, 'field': 'locale',
            'severity': 'info', 'auto_fixable': False,
            'detail': f'Abstract detectado como inglês (conf={conf:.2f}) mas locale={locale}',
            'suggestion': 'Verificar se locale deveria ser "en"',
        })

    return issues


# Regex para detectar encoding ruim (caracteres comuns em PDFs com fontes problemáticas)
# ĕ, ė, ĩ = ligaduras/substituições erradas
BAD_ENCODING_RE = re.compile(r'[ĕėĖĘ]')
# Espaços entre letras: 4+ letras isoladas em sequência (ex: "Es te a rtigo")
# Threshold alto para evitar falsos positivos com preposições
SPACED_LETTERS_RE = re.compile(r'(?<!\w)[a-záéíóú] [a-záéíóú] [a-záéíóú] [a-záéíóú](?!\w)')


def check_bad_encoding(article):
    """A24: encoding ruim em campos de texto (fontes problemáticas no PDF).

    Detecta caracteres substitutos (ĕ, ė) e espaços entre letras ("Es te a rtigo").
    Não é auto-fixável — requer extração via imagem do PDF (pdftoppm + leitura visual).
    """
    issues = []
    aid = article['id']

    for field_name in ('abstract', 'abstract_en', 'abstract_es', 'title', 'subtitle'):
        text = article.get(field_name)
        if not text:
            continue
        problems = []
        if BAD_ENCODING_RE.search(text):
            problems.append('caracteres substitutos')
        if SPACED_LETTERS_RE.search(text):
            problems.append('espaços entre letras')
        if problems:
            issues.append({
                'check': 'A24', 'article_id': aid, 'field': field_name,
                'severity': 'error', 'auto_fixable': False,
                'detail': f'{field_name}: encoding ruim ({", ".join(problems)})',
                'suggestion': 'Re-extrair via imagem do PDF (pdftoppm + leitura visual)',
            })

    # Checar keywords
    for col in ('keywords', 'keywords_en', 'keywords_es'):
        kws = article.get(col)
        if not kws or not isinstance(kws, list):
            continue
        for k in kws:
            if BAD_ENCODING_RE.search(k) or SPACED_LETTERS_RE.search(k):
                issues.append({
                    'check': 'A24', 'article_id': aid, 'field': col,
                    'severity': 'error', 'auto_fixable': False,
                    'detail': f'{col}: encoding ruim em keyword "{k[:40]}"',
                    'suggestion': 'Re-extrair via imagem do PDF',
                })
                break

    return issues


# Regex para detectar control characters (exceto \n, \r, \t)
CONTROL_CHAR_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')


def check_control_chars(article):
    """A16: control characters em campos de texto."""
    issues = []
    aid = article['id']

    text_fields = [
        ('abstract', article.get('abstract')),
        ('abstract_en', article.get('abstract_en')),
        ('abstract_es', article.get('abstract_es')),
    ]
    # Também checar title e subtitle se disponíveis
    for fname in ('title', 'subtitle', 'title_en', 'subtitle_en'):
        val = article.get(fname)
        if val:
            text_fields.append((fname, val))

    for field_name, text in text_fields:
        if not text:
            continue
        matches = CONTROL_CHAR_RE.findall(text)
        if matches:
            chars = ', '.join(f'U+{ord(c):04X}' for c in set(matches))
            issues.append({
                'check': 'A16', 'article_id': aid, 'field': field_name,
                'severity': 'warning', 'auto_fixable': True,
                'detail': f'{field_name}: control characters encontrados: {chars}',
                'suggestion': 'Remover control characters',
                'fix_action': {'strip_control_chars': field_name},
            })

    # Checar nas refs
    for i, ref in enumerate(article.get('refs_parsed', [])):
        if CONTROL_CHAR_RE.search(ref):
            chars = ', '.join(f'U+{ord(c):04X}' for c in set(CONTROL_CHAR_RE.findall(ref)))
            issues.append({
                'check': 'A16', 'article_id': aid, 'field': 'references_',
                'severity': 'warning', 'auto_fixable': True,
                'ref_index': i,
                'detail': f'ref[{i}]: control characters: {chars}',
                'suggestion': 'Remover control characters',
                'fix_action': {'strip_control_chars_ref': i},
            })

    # Checar nas keywords
    for col in ('keywords', 'keywords_en', 'keywords_es'):
        kws = article.get(col)
        if not kws or not isinstance(kws, list):
            continue
        for j, k in enumerate(kws):
            if CONTROL_CHAR_RE.search(k):
                issues.append({
                    'check': 'A16', 'article_id': aid, 'field': col,
                    'severity': 'warning', 'auto_fixable': True,
                    'detail': f'{col}[{j}]: control characters',
                    'suggestion': 'Remover control characters',
                    'fix_action': {'strip_control_chars_kw': col},
                })
                break  # um issue por campo é suficiente

    return issues


def check_duplicate_refs(article):
    """A17: referências duplicadas no mesmo artigo."""
    issues = []
    refs = article.get('refs_parsed', [])
    if len(refs) < 2:
        return issues

    seen = {}
    dup_indices = []
    for i, ref in enumerate(refs):
        normalized = ref.strip().lower()
        if normalized in seen:
            dup_indices.append(i)
        else:
            seen[normalized] = i

    if dup_indices:
        issues.append({
            'check': 'A17', 'article_id': article['id'], 'field': 'references_',
            'severity': 'warning', 'auto_fixable': True,
            'detail': f'{len(dup_indices)} referências duplicadas',
            'suggestion': 'Remover duplicatas',
            'fix_action': {'dedup_refs': True},
            'dup_indices': dup_indices,
        })

    return issues


def check_no_authors(article, conn):
    """A18: artigo sem autores vinculados."""
    issues = []
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM article_author WHERE article_id = ?",
                (article['id'],))
    count = cur.fetchone()[0]
    if count == 0:
        issues.append({
            'check': 'A18', 'article_id': article['id'], 'field': 'authors',
            'severity': 'error', 'auto_fixable': False,
            'detail': 'Artigo sem autores vinculados',
            'suggestion': 'Verificar article_author e vincular autores',
        })
    return issues


def check_abstract_overflow(article):
    """A20: abstract anormalmente longo (corpo do texto vazou para dentro do abstract).

    Abstracts genuínos raramente passam de 5000 chars (~700 palavras).
    Se > 5000, provavelmente o extrator capturou o corpo do artigo inteiro.
    """
    issues = []
    aid = article['id']
    THRESHOLD = 5000

    for field_name in ('abstract', 'abstract_en', 'abstract_es'):
        text = article.get(field_name)
        if not text:
            continue
        if len(text) > THRESHOLD:
            issues.append({
                'check': 'A20', 'article_id': aid, 'field': field_name,
                'severity': 'error', 'auto_fixable': True,
                'detail': f'{field_name}: {len(text)} chars (provável corpo do texto vazado)',
                'suggestion': 'Truncar no marcador de keywords ou re-extrair do fontes/',
                'fix_action': {'truncate_abstract': field_name},
            })

    return issues


def check_abstract_es_garbage(article):
    """A21: abstract_es com lixo de cruzamento de idiomas.

    Detecta abstract_es que contém texto EN (abstract_en, keywords_en, page breaks)
    porque a extração não parou no marcador de keywords ES.
    """
    issues = []
    aid = article['id']
    text = article.get('abstract_es')
    if not text or len(text) < 100:
        return issues

    # Marcadores de lixo EN no abstract_es
    garbage_markers = [
        re.compile(r'\bAbstract\b', re.IGNORECASE),
        re.compile(r'\bKeywords?\s*:', re.IGNORECASE),
        re.compile(r'\bKey[- ]?words?\s*:', re.IGNORECASE),
        re.compile(r'⏐'),  # page break marker
    ]

    found = []
    for marker in garbage_markers:
        if marker.search(text):
            found.append(marker.pattern)

    if found:
        issues.append({
            'check': 'A21', 'article_id': aid, 'field': 'abstract_es',
            'severity': 'warning', 'auto_fixable': True,
            'detail': f'abstract_es contém lixo EN: {", ".join(found[:3])}',
            'suggestion': 'Truncar no marcador de keywords ES ou setar NULL',
            'fix_action': {'clean_abstract_es': True},
        })

    # Também: abstract_es == abstract (redundância em artigos locale=es)
    if (article.get('locale') == 'es' and article.get('abstract') and
            text.strip() == article['abstract'].strip()):
        issues.append({
            'check': 'A21', 'article_id': aid, 'field': 'abstract_es',
            'severity': 'info', 'auto_fixable': True,
            'detail': 'abstract_es idêntico ao abstract (redundante para locale=es)',
            'suggestion': 'Setar abstract_es = NULL',
            'fix_action': {'null_field': 'abstract_es'},
        })

    return issues


# Regex para figure captions
FIGURE_CAPTION_RE = re.compile(
    r'^(Figura|Fig\.?|Figure|Imagem|Foto|Photo|Ilustração)\s*\d', re.IGNORECASE
)


def check_refs_body_text(article):
    """A22: refs com body text ou figure captions.

    Detecta entradas que são parágrafos narrativos longos (>200 chars com estrutura
    de discurso) ou legendas de figuras, não referências bibliográficas.
    Auto-fix: remove as entradas detectadas.
    """
    issues = []
    refs = article.get('refs_parsed', [])
    if not refs:
        return issues

    # Marcadores de narrativa (2+ = body text)
    NARRATIVE_PT = ['este artigo', 'este trabalho', 'neste sentido', 'a partir de',
                    'o presente', 'como resultado', 'dessa forma', 'portanto',
                    'no entanto', 'além disso', 'assim como', 'foi murado',
                    'foram adicionad', 'antes de ingressar', 'posteriormente']
    NARRATIVE_EN = ['this paper', 'this article', 'this study', 'in this sense',
                    'as a result', 'therefore', 'however', 'furthermore',
                    'moreover', 'in addition']
    NARRATIVE_ES = ['este artículo', 'este trabajo', 'en este sentido',
                    'a partir de', 'como resultado', 'por lo tanto',
                    'sin embargo', 'además']

    remove_indices = []

    for i, ref in enumerate(refs):
        ref_stripped = ref.strip()
        is_body = False

        # Figure caption
        if FIGURE_CAPTION_RE.match(ref_stripped):
            is_body = True

        # Body text: longo + narrativo + sem padrão de autor
        if not is_body and len(ref_stripped) > 200:
            ref_lower = ref_stripped.lower()
            narrative_count = 0
            for markers in (NARRATIVE_PT, NARRATIVE_EN, NARRATIVE_ES):
                for m in markers:
                    if m in ref_lower:
                        narrative_count += 1
            if narrative_count >= 2:
                # Verificar se NÃO é referência (sem padrão ABNT/Chicago)
                if not re.match(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇÑ]{2,},\s', ref_stripped):
                    if not re.match(r'^[A-Z][a-z]+,\s+[A-Z]', ref_stripped):
                        is_body = True

        if is_body:
            remove_indices.append(i)

    if remove_indices:
        details = '; '.join(
            f'[{i}] "{refs[i].strip()[:60]}..."' for i in remove_indices
        )
        issues.append({
            'check': 'A22', 'article_id': article['id'], 'field': 'references_',
            'severity': 'warning', 'auto_fixable': True,
            'detail': f'{len(remove_indices)} entrada(s) não-referência: {details}',
            'suggestion': 'Remover entradas de body text/legendas',
            'fix_action': {'remove_refs': remove_indices},
        })

    return issues


def check_abstract_en_in_abstract(article):
    """A23: abstract_en colado no final do abstract PT.

    Padrão frequente: extração captura PT+EN como bloco único no campo abstract.
    Detecta marcadores EN no campo abstract: "Abstract:", "The present paper",
    "This article", "This work", "This study", "In this paper".
    Auto-fix: separa PT e EN.
    """
    issues = []
    aid = article['id']
    text = article.get('abstract')
    if not text or len(text) < 200:
        return issues

    # Marcadores de início de abstract EN dentro do texto PT
    EN_BOUNDARY = re.compile(
        r'(?<=[.!?])\s+'
        r'(?=(?:Abstract\s*:?\s+)?'
        r'(?:The\s+(?:present\s+)?(?:paper|article|work|study|research)\b|'
        r'This\s+(?:paper|article|work|study|research)\b|'
        r'In\s+this\s+(?:paper|article|work|study)\b))',
        re.IGNORECASE
    )

    m = EN_BOUNDARY.search(text)
    if m and m.start() > 100:
        # Também verificar "Abstract:" standalone
        pass
    else:
        # Tentar "Abstract:" como boundary
        m = re.search(r'\s+Abstract\s*:\s+', text)
        if m and m.start() > 100:
            pass
        else:
            m = None

    # Verificar "Palavras-chave:" no meio (indica boundary PT keywords → EN)
    if not m:
        kw_m = re.search(r'\s*Palavras[\s\u00AD\u002D\u2010-\u2015‐-]*[Cc]have\s*:', text)
        if kw_m and kw_m.start() > 100:
            after_kw = text[kw_m.end():]
            en_m = re.search(r'(?:Abstract\s*:?\s*)?(?:The\s+|This\s+|In\s+this\s+)', after_kw, re.IGNORECASE)
            if en_m:
                m = type('Match', (), {'start': lambda self: kw_m.start()})()

    if m:
        issues.append({
            'check': 'A23', 'article_id': aid, 'field': 'abstract',
            'severity': 'warning', 'auto_fixable': True,
            'detail': f'abstract_en colado no abstract PT (boundary em pos {m.start()})',
            'suggestion': 'Separar PT e EN',
            'fix_action': {'split_abstract_en': m.start()},
        })

    return issues


def check_abstract_truncation(article):
    """A19: abstract possivelmente truncado (não termina com pontuação de fim de frase)."""
    issues = []
    aid = article['id']

    for field_name in ('abstract', 'abstract_en', 'abstract_es'):
        text = article.get(field_name)
        if not text or len(text) < 80:
            continue
        text = text.strip()
        if text and text[-1] not in '.?!"\')»':
            # Pegar os últimos 40 chars para contexto
            tail = text[-40:]
            issues.append({
                'check': 'A19', 'article_id': aid, 'field': field_name,
                'severity': 'warning', 'auto_fixable': False,
                'detail': f'{field_name}: possível truncamento (termina com "...{tail}")',
                'suggestion': 'Re-extrair do fontes/ via fix_validation_issues.py',
            })

    return issues


# ── Main ─────────────────────────────────────────────────────────────────────

def validate_seminar(conn, slug, fix=False, dry_run=False):
    """Valida metadados de um seminário. Retorna (issues, auto_fixed, profile)."""
    cur = conn.cursor()

    profile = build_profile(cur, slug)
    if not profile:
        print(f"  Seminário {slug}: nenhum artigo encontrado")
        return [], [], None

    # Carregar artigos
    cur.execute("""
        SELECT id, file, locale, document_type,
               abstract, abstract_en, abstract_es,
               keywords, keywords_en, keywords_es,
               references_,
               title, subtitle, title_en, subtitle_en
        FROM articles
        WHERE seminar_slug = ? AND document_type NOT IN ('mesa', 'resumo')
        ORDER BY file
    """, (slug,))
    rows = cur.fetchall()

    # Localizar fontes/
    fontes_dir = find_fontes_dir(slug)

    all_issues = []
    auto_fixed = []

    for row in rows:
        article = {
            'id': row[0], 'file': row[1], 'locale': row[2], 'document_type': row[3],
            'abstract': row[4], 'abstract_en': row[5], 'abstract_es': row[6],
            'keywords': None, 'keywords_en': None, 'keywords_es': None,
            'refs_parsed': [],
            'title': row[11], 'subtitle': row[12],
            'title_en': row[13], 'subtitle_en': row[14],
        }

        # Parse JSON fields
        for i, field in enumerate(('keywords', 'keywords_en', 'keywords_es'), 7):
            raw = row[i]
            if raw and raw.strip() and raw.strip() != '[]':
                try:
                    parsed = json.loads(raw)
                    article[field] = parsed if parsed else None
                except (json.JSONDecodeError, TypeError):
                    # Try as comma-separated text
                    article[field] = [k.strip() for k in raw.split(',') if k.strip()]

        # Parse refs
        refs_raw = row[10]
        if refs_raw and refs_raw.strip() and refs_raw.strip() != '[]':
            try:
                article['refs_parsed'] = json.loads(refs_raw)
            except (json.JSONDecodeError, TypeError):
                pass

        # Ler fontes/
        fontes_lines = read_fontes(fontes_dir, article['id']) if fontes_dir else None

        # Rodar todas as checagens
        issues = []
        issues.extend(check_cross_language(article, profile))
        issues.extend(check_locale_fields(article))
        issues.extend(check_fontes_markers(article, fontes_lines, profile))
        issues.extend(check_refs_backfill(article))
        issues.extend(check_refs_long(article))
        issues.extend(check_refs_nonref(article))
        issues.extend(check_refs_orphan_urls(article))
        issues.extend(check_abstract_contamination(article))
        issues.extend(check_locale_mismatch(article))
        issues.extend(check_control_chars(article))
        issues.extend(check_duplicate_refs(article))
        issues.extend(check_no_authors(article, conn))
        issues.extend(check_abstract_overflow(article))
        issues.extend(check_abstract_es_garbage(article))
        issues.extend(check_refs_body_text(article))
        issues.extend(check_abstract_en_in_abstract(article))
        issues.extend(check_bad_encoding(article))
        issues.extend(check_abstract_truncation(article))

        # Aplicar auto-fixes
        for issue in issues:
            if issue.get('auto_fixable') and fix and not dry_run:
                action = issue.get('fix_action', {})
                if 'copy_field' in action:
                    src = action['copy_field']
                    dst = action['to_field']
                    val = article.get(src)
                    if val is not None:
                        if isinstance(val, list):
                            val_db = json.dumps(val, ensure_ascii=False)
                        else:
                            val_db = val
                        cur.execute(f"UPDATE articles SET {dst} = ? WHERE id = ?",
                                    (val_db, article['id']))
                        auto_fixed.append(issue)
                elif 'set_field' in action:
                    field = action['set_field']
                    val = action['value']
                    cur.execute(f"UPDATE articles SET {field} = ? WHERE id = ?",
                                (val, article['id']))
                    auto_fixed.append(issue)
                elif 'strip_control_chars' in action:
                    field = action['strip_control_chars']
                    val = article.get(field)
                    if val:
                        cleaned = CONTROL_CHAR_RE.sub('', val)
                        cur.execute(f"UPDATE articles SET {field} = ? WHERE id = ?",
                                    (cleaned, article['id']))
                        auto_fixed.append(issue)
                elif 'strip_control_chars_ref' in action:
                    refs = article.get('refs_parsed', [])
                    new_refs = [CONTROL_CHAR_RE.sub('', r) for r in refs]
                    cur.execute("UPDATE articles SET references_ = ? WHERE id = ?",
                                (json.dumps(new_refs, ensure_ascii=False), article['id']))
                    auto_fixed.append(issue)
                elif 'strip_control_chars_kw' in action:
                    col = action['strip_control_chars_kw']
                    kws = article.get(col)
                    if kws and isinstance(kws, list):
                        cleaned = [CONTROL_CHAR_RE.sub('', k) for k in kws]
                        cur.execute(f"UPDATE articles SET {col} = ? WHERE id = ?",
                                    (json.dumps(cleaned, ensure_ascii=False), article['id']))
                        auto_fixed.append(issue)
                elif 'truncate_abstract' in action:
                    field = action['truncate_abstract']
                    text = article.get(field, '')
                    if text and len(text) > 5000:
                        # Tentar truncar no marcador de keywords
                        kw_markers = [
                            r'Palavras[\s-]*[Cc]have[s]?\s*:',
                            r'Keywords?\s*:',
                            r'Key\s*[Ww]ords?\s*:',
                            r'Palabras[\s-]*[Cc]laves?\s*:',
                            r'PALAVRAS[\s-]*CHAVE',
                            r'KEYWORDS?',
                        ]
                        best_pos = len(text)
                        for pattern in kw_markers:
                            m = re.search(pattern, text)
                            if m and m.start() > 100 and m.start() < best_pos:
                                best_pos = m.start()
                        if best_pos < len(text):
                            truncated = text[:best_pos].rstrip()
                            # Limpar: remover trailing whitespace/pipe
                            truncated = truncated.rstrip(' |')
                            cur.execute(f"UPDATE articles SET {field} = ? WHERE id = ?",
                                        (truncated, article['id']))
                            auto_fixed.append(issue)
                        else:
                            # Sem marcador: truncar em 4500 chars no último ponto
                            last_dot = text.rfind('.', 0, 4500)
                            if last_dot > 100:
                                truncated = text[:last_dot + 1]
                                cur.execute(f"UPDATE articles SET {field} = ? WHERE id = ?",
                                            (truncated, article['id']))
                                auto_fixed.append(issue)
                elif 'clean_abstract_es' in action:
                    text = article.get('abstract_es', '')
                    if text:
                        # Truncar no primeiro marcador EN
                        kw_markers = [
                            r'Palabras[\s-]*[Cc]have[s]?\s*:',
                            r'Palabras[\s-]*[Cc]laves?\s*:',
                            r'\bAbstract\b',
                            r'\bKeywords?\s*:',
                            r'⏐',
                        ]
                        best_pos = len(text)
                        for pattern in kw_markers:
                            m = re.search(pattern, text)
                            if m and m.start() > 50 and m.start() < best_pos:
                                best_pos = m.start()
                        if best_pos < len(text):
                            cleaned = text[:best_pos].rstrip()
                            if len(cleaned) > 50:
                                cur.execute("UPDATE articles SET abstract_es = ? WHERE id = ?",
                                            (cleaned, article['id']))
                            else:
                                cur.execute("UPDATE articles SET abstract_es = NULL WHERE id = ?",
                                            (article['id'],))
                            auto_fixed.append(issue)
                        else:
                            # Se não encontrou marcador, setar NULL
                            cur.execute("UPDATE articles SET abstract_es = NULL WHERE id = ?",
                                        (article['id'],))
                            auto_fixed.append(issue)
                elif 'null_field' in action:
                    field = action['null_field']
                    cur.execute(f"UPDATE articles SET {field} = NULL WHERE id = ?",
                                (article['id'],))
                    auto_fixed.append(issue)
                elif 'dedup_refs' in action:
                    refs = article.get('refs_parsed', [])
                    seen = set()
                    deduped = []
                    for ref in refs:
                        norm = ref.strip().lower()
                        if norm not in seen:
                            seen.add(norm)
                            deduped.append(ref)
                    cur.execute("UPDATE articles SET references_ = ? WHERE id = ?",
                                (json.dumps(deduped, ensure_ascii=False), article['id']))
                    article['refs_parsed'] = deduped  # sync in-memory
                    auto_fixed.append(issue)
                elif 'remove_refs' in action:
                    refs = article.get('refs_parsed', [])
                    indices_to_remove = set(action['remove_refs'])
                    cleaned = [r for i, r in enumerate(refs) if i not in indices_to_remove]
                    cur.execute("UPDATE articles SET references_ = ? WHERE id = ?",
                                (json.dumps(cleaned, ensure_ascii=False), article['id']))
                    article['refs_parsed'] = cleaned  # sync in-memory
                    auto_fixed.append(issue)
                elif 'split_abstract_en' in action:
                    pos = action['split_abstract_en']
                    text = article.get('abstract', '')
                    if text and pos > 100 and pos < len(text):
                        pt_part = text[:pos].strip()
                        en_part = text[pos:].strip()
                        # Limpar marcadores
                        en_part = re.sub(r'^Abstract\s*:?\s*', '', en_part, flags=re.IGNORECASE).strip()
                        # Remover keywords do final do EN
                        kw_m = re.search(r'\s*(Keywords?\s*:|Key-?\s*words?\s*:)', en_part, re.IGNORECASE)
                        if kw_m:
                            en_part = en_part[:kw_m.start()].strip()
                        # Remover keywords do final do PT
                        kw_m = re.search(r'\s*Palavras[\s\u00AD\u002D\u2010-\u2015\u200B‐-]*[Cc]have\s*:', pt_part)
                        if kw_m:
                            pt_part = pt_part[:kw_m.start()].strip()
                        if len(pt_part) > 50 and len(en_part) > 30:
                            cur.execute("UPDATE articles SET abstract = ?, abstract_en = ? WHERE id = ?",
                                        (pt_part, en_part, article['id']))
                            article['abstract'] = pt_part
                            article['abstract_en'] = en_part
                            auto_fixed.append(issue)

        all_issues.extend(issues)

    if fix and not dry_run:
        conn.commit()

    return all_issues, auto_fixed, profile


def print_summary(slug, issues, auto_fixed, profile):
    """Imprime resumo no console."""
    print(f"\n=== Validação de metadados — {slug} ===")

    if not profile:
        print("  Nenhum artigo encontrado")
        return

    total = profile['total']
    parts = [f"{total} artigos"]
    for field, label in [('abstract_en', 'abs_en'), ('keywords_en', 'kw_en'),
                         ('abstract_es', 'abs_es'), ('keywords_es', 'kw_es'),
                         ('references_', 'refs')]:
        pct = profile.get(f'{field}_pct', 0)
        if pct > 0:
            parts.append(f"{label} {pct:.0%}")
    if profile['locale_es'] > 0:
        parts.append(f"locale=es {profile['locale_es']}")
    print(f"Perfil: {' | '.join(parts)}")
    print()

    # Agrupar por check
    check_counts = {}
    check_fix = {}
    check_report = {}
    for issue in issues:
        c = issue['check']
        check_counts[c] = check_counts.get(c, 0) + 1
        if issue.get('auto_fixable'):
            check_fix[c] = check_fix.get(c, 0) + 1
        else:
            check_report[c] = check_report.get(c, 0) + 1

    # Descrições dos checks
    check_desc = {
        'A01': 'abs_en sem kw_en',
        'A02': 'kw_en sem abs_en',
        'A03': 'abs_es sem kw_es',
        'A04': 'kw_es sem abs_es',
        'A05': 'locale_es→abs_es',
        'A06': 'locale_es→kw_es',
        'A07': 'fontes: Abstract',
        'A08': 'fontes: Keywords',
        'A09': 'fontes: Resumen',
        'A10': 'backfill pendente',
        'A11': 'ref longa (concat?)',
        'A12': 'não-ref em refs',
        'A13': 'URL órfã',
        'A14': 'abstract contaminado',
        'A15': 'locale mismatch',
        'A16': 'control chars',
        'A17': 'refs duplicadas',
        'A18': 'sem autores',
        'A19': 'abstract truncado?',
        'A20': 'abstract overflow',
        'A21': 'abstract_es lixo EN',
        'A22': 'body text em refs',
        'A23': 'abstract_en no abstract',
        'A24': 'encoding ruim',
    }

    if not check_counts:
        print("  Nenhum problema encontrado ✓")
        return

    print(f"  {'Check':<6} {'Descrição':<22} {'Issues':>6}  {'Fix':>4}  {'Report':>6}")
    print(f"  {'─'*6} {'─'*22} {'─'*6}  {'─'*4}  {'─'*6}")

    total_issues = 0
    total_fix = 0
    total_report = 0
    for c in sorted(check_counts.keys()):
        n = check_counts[c]
        f = check_fix.get(c, 0)
        r = check_report.get(c, 0)
        desc = check_desc.get(c, c)
        total_issues += n
        total_fix += f
        total_report += r
        print(f"  {c:<6} {desc:<22} {n:>6}  {f:>4}  {r:>6}")

    print(f"  {'─'*6} {'─'*22} {'─'*6}  {'─'*4}  {'─'*6}")
    print(f"  {'TOTAL':<6} {'':<22} {total_issues:>6}  {total_fix:>4}  {total_report:>6}")
    print()

    if auto_fixed:
        print(f"  Auto-fixed: {len(auto_fixed)} issues")
    report_issues = [i for i in issues if not i.get('auto_fixable')]
    if report_issues:
        articles_with_issues = len(set(i['article_id'] for i in report_issues))
        print(f"  Para revisão: {len(report_issues)} issues em {articles_with_issues} artigos")


def save_report(slug, issues, auto_fixed, profile):
    """Salva relatório JSON."""
    report_path = os.path.join(BASE_DIR, 'revisao', f'{slug}-validation.json')

    report_issues = [i for i in issues if not i.get('auto_fixable')]
    # Candidatos para revisão LLM (category B)
    category_b = []
    b_articles = set()
    for issue in report_issues:
        aid = issue['article_id']
        if issue['check'] in ('A14', 'A11') and aid not in b_articles:
            category_b.append({
                'article_id': aid,
                'checks_flagged': [i['check'] for i in report_issues if i['article_id'] == aid],
                'reason': issue['detail'],
            })
            b_articles.add(aid)

    report = {
        'slug': slug,
        'date': str(date.today()),
        'total_articles': profile['total'] if profile else 0,
        'profile': {k: v for k, v in profile.items() if not k.endswith('_pct')} if profile else {},
        'auto_fixed': [{k: v for k, v in i.items() if k != 'fix_action'} for i in auto_fixed],
        'issues': [{k: v for k, v in i.items() if k != 'fix_action'} for i in report_issues],
        'category_b_candidates': category_b,
    }

    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n→ {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Validação abrangente de metadados (complementa validar_abstracts e check_references)')
    parser.add_argument('--slug', help='Processar apenas este seminário')
    parser.add_argument('--dry-run', action='store_true',
                        help='Mostrar o que seria feito sem alterar o banco')
    parser.add_argument('--fix', action='store_true',
                        help='Aplicar auto-fixes ao banco')
    parser.add_argument('--report-only', action='store_true',
                        help='Apenas gerar relatório, sem auto-fixes')
    args = parser.parse_args()

    if args.report_only:
        args.fix = False

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if args.slug:
        slugs = [args.slug]
    else:
        cur.execute("SELECT DISTINCT seminar_slug FROM articles ORDER BY seminar_slug")
        slugs = [r[0] for r in cur.fetchall()]

    for slug in slugs:
        issues, auto_fixed, profile = validate_seminar(
            conn, slug, fix=args.fix, dry_run=args.dry_run)
        print_summary(slug, issues, auto_fixed, profile)

        if args.slug:
            save_report(slug, issues, auto_fixed, profile)

    if args.dry_run:
        print("\nDRY RUN — nenhuma alteração aplicada")
    elif args.fix:
        print(f"\nALTERAÇÕES APLICADAS")

    conn.close()


if __name__ == '__main__':
    main()
