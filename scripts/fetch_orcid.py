#!/usr/bin/env python3
"""Busca ORCIDs dos autores via OpenAlex (primário) e API pública ORCID (fallback).

Pipeline de busca:
  1. OpenAlex /authors (ML-based disambiguation, agrega ORCID de múltiplas fontes)
  2. ORCID /v3.0/search (fallback se OpenAlex não encontrou)

Fase 1 (--search): Busca nas APIs, classifica resultados, salva em JSON.
Fase 2 (--review): Mostra candidatos ambíguos para revisão.
Fase 3 (--apply):  Aplica ORCIDs confirmados ao banco.

Uso:
    python3 scripts/fetch_orcid.py --search              # Busca nas APIs
    python3 scripts/fetch_orcid.py --search --resume     # Retoma busca interrompida
    python3 scripts/fetch_orcid.py --search --recheck-days 180  # Re-checa autores verificados há 6+ meses
    python3 scripts/fetch_orcid.py --review              # Mostra candidatos para revisão
    python3 scripts/fetch_orcid.py --apply               # Aplica ORCIDs ao banco
    python3 scripts/fetch_orcid.py --scrape-faculty      # Raspa páginas de docentes (dry-run)
    python3 scripts/fetch_orcid.py --scrape-faculty --apply  # Raspa e aplica
    python3 scripts/fetch_orcid.py --stats               # Estatísticas do resultado

Versionamento:
    Cada execução registra orcid_checked_at e orcid_pipeline_version na tabela authors.
    Use --recheck-days N para re-verificar autores checados há mais de N dias ou com
    versão do pipeline anterior à atual.
"""

import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

# Versão do pipeline — incrementar ao adicionar fontes, corrigir bugs, ou
# alterar critérios de matching. Permite saber se vale a pena re-checar autores.
# Changelog:
#   1.0 — API ORCID apenas (search + employments)
#   2.0 — OpenAlex (primário) + Crossref + Semantic Scholar + ORCID API (fallback)
#         + exclusões de falsos positivos + name_compatible corrigido (rejeita iniciais)
PIPELINE_VERSION = '2.0'

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE, 'anais.db')
RESULTS_PATH = os.path.join(BASE, 'orcid_results.json')

ORCID_API = 'https://pub.orcid.org/v3.0'
OPENALEX_API = 'https://api.openalex.org'
OPENALEX_EMAIL = 'danilo@docomomobrasil.com'  # Polite Pool
REQUEST_DELAY = 0.5  # seconds between API requests
OPENALEX_DELAY = 0.15  # OpenAlex Polite Pool allows ~10 req/s
MAX_PROFILES = 5      # max profiles to check per author

# Siglas de universidades brasileiras → nomes completos (para matching)
# A API ORCID armazena nomes completos das instituições.
SIGLA_KEYWORDS = {
    'USP': ['São Paulo', 'Sao Paulo'],
    'UFRGS': ['Rio Grande do Sul'],
    'UFBA': ['Bahia'],
    'UFPE': ['Pernambuco'],
    'UFC': ['Ceará', 'Ceara'],
    'UFRJ': ['Rio de Janeiro'],
    'UFMG': ['Minas Gerais'],
    'UnB': ['Brasília', 'Brasilia'],
    'UFSC': ['Santa Catarina'],
    'UFPR': ['Paraná', 'Parana'],
    'UFG': ['Goiás', 'Goias'],
    'UFMT': ['Mato Grosso'],
    'UFAL': ['Alagoas'],
    'UFPA': ['Pará', 'Para'],
    'UFPB': ['Paraíba', 'Paraiba'],
    'UFRN': ['Rio Grande do Norte'],
    'UFCG': ['Campina Grande'],
    'UFPI': ['Piauí', 'Piaui'],
    'UFS': ['Sergipe'],
    'UFOP': ['Ouro Preto'],
    'UFPel': ['Pelotas'],
    'UFRR': ['Roraima'],
    'UFT': ['Tocantins'],
    'UFRRJ': ['Rural', 'Rio de Janeiro'],
    'UNICAMP': ['Campinas'],
    'UNESP': ['Estadual Paulista'],
    'UERJ': ['Estado do Rio de Janeiro'],
    'UEL': ['Londrina'],
    'UEM': ['Maringá', 'Maringa'],
    'UEMA': ['Maranhão', 'Maranhao'],
    'UEPA': ['Estado do Pará', 'Estado do Para'],
    'Mackenzie': ['Mackenzie', 'Presbiteriana'],
    'UPM': ['Mackenzie', 'Presbiteriana'],
    'PUC': ['Pontifícia', 'Pontificia', 'PUC'],
    'UNICAP': ['Católica de Pernambuco', 'Catolica de Pernambuco'],
    'UNISINOS': ['Vale do Rio dos Sinos'],
    'ULBRA': ['Luterana'],
    'Fiocruz': ['Fiocruz', 'Oswaldo Cruz'],
    'IPHAN': ['IPHAN', 'Patrimônio Histórico', 'Patrimonio Historico'],
    'UNIFOR': ['Fortaleza'],
    'UNIP': ['Paulista'],
    'USJT': ['São Judas', 'Sao Judas'],
}


def strip_accents(s):
    """Remove acentos para comparação."""
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def first_real_name(givenname):
    """Extrai o primeiro nome real (não partícula, não inicial) do givenname."""
    particles = {'de', 'da', 'do', 'dos', 'das', 'e', 'del', 'di', 'van', 'von'}
    parts = givenname.strip().split()
    for p in parts:
        clean = p.replace('.', '').replace(',', '').strip()
        if not clean:
            continue
        if clean.lower() in particles:
            continue
        if len(clean) <= 2:
            continue  # initial like "M." or "L."
        return clean
    return None


def is_initials_only(givenname):
    """Verifica se o givenname contém apenas iniciais ou abreviações."""
    parts = givenname.strip().split()
    particles = {'de', 'da', 'do', 'dos', 'das', 'e'}
    for p in parts:
        clean = p.replace('.', '').replace(',', '').strip()
        if not clean:
            continue
        if clean.lower() in particles:
            continue
        if len(clean) > 2:
            return False
    return True


def openalex_search(fullname, filter_br=True):
    """Busca autor no OpenAlex por nome completo.

    Retorna lista de candidatos com orcid, display_name, institutions, works_count.
    Se filter_br=True, filtra por instituição brasileira.
    """
    query = urllib.parse.quote(fullname)
    url = f'{OPENALEX_API}/authors?search={query}'
    if filter_br:
        url += '&filter=last_known_institutions.country_code:BR'
    url += '&per_page=5'

    headers = {
        'Accept': 'application/json',
        'User-Agent': f'fetch_orcid/1.0 (mailto:{OPENALEX_EMAIL})',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        results = []
        for item in data.get('results', []):
            orcid_url = item.get('orcid')
            orcid_id = orcid_url.replace('https://orcid.org/', '') if orcid_url else None
            institutions = []
            for inst in item.get('last_known_institutions', []) or []:
                institutions.append({
                    'name': inst.get('display_name', ''),
                    'country': inst.get('country_code', ''),
                })
            results.append({
                'openalex_id': item.get('id', ''),
                'display_name': item.get('display_name', ''),
                'orcid': orcid_id,
                'institutions': institutions,
                'works_count': item.get('works_count', 0),
                'cited_by_count': item.get('cited_by_count', 0),
            })
        return results
    except Exception as e:
        print(f'    ERRO OpenAlex: {e}')
        return []


def openalex_find_orcid(fullname, db_gn, db_fn, db_affil):
    """Tenta encontrar ORCID via OpenAlex. Retorna (orcid, source_detail) ou (None, None).

    Busca primeiro com filtro BR, depois sem filtro se necessário.
    Valida compatibilidade de nome e afiliação.
    """
    # Busca com filtro BR
    candidates = openalex_search(fullname, filter_br=True)

    # Filtrar candidatos com ORCID e nome compatível
    valid = []
    for c in candidates:
        if not c['orcid']:
            continue
        # Extrair givenname/familyname do display_name
        parts = c['display_name'].rsplit(' ', 1)
        orc_gn = parts[0] if len(parts) > 1 else c['display_name']
        orc_fn = parts[1] if len(parts) > 1 else ''
        if name_compatible(db_gn, db_fn, orc_gn, orc_fn):
            valid.append(c)

    if len(valid) == 1:
        c = valid[0]
        org_names = [i['name'] for i in c['institutions']]
        return c['orcid'], {
            'source': 'openalex_br',
            'display_name': c['display_name'],
            'orgs': org_names,
            'works_count': c['works_count'],
        }

    if len(valid) > 1 and db_affil:
        # Tentar desambiguar por afiliação
        for c in valid:
            orcid_orgs = [{'name': i['name'], 'country': i['country']} for i in c['institutions']]
            if affiliation_matches(db_affil, orcid_orgs):
                org_names = [i['name'] for i in c['institutions']]
                return c['orcid'], {
                    'source': 'openalex_br_affil',
                    'display_name': c['display_name'],
                    'orgs': org_names,
                    'works_count': c['works_count'],
                }

    # Se não achou com filtro BR, tentar sem filtro (autor pode ter mudado de país)
    if not valid:
        time.sleep(OPENALEX_DELAY)
        candidates = openalex_search(fullname, filter_br=False)
        valid_all = []
        for c in candidates:
            if not c['orcid']:
                continue
            parts = c['display_name'].rsplit(' ', 1)
            orc_gn = parts[0] if len(parts) > 1 else c['display_name']
            orc_fn = parts[1] if len(parts) > 1 else ''
            if name_compatible(db_gn, db_fn, orc_gn, orc_fn):
                valid_all.append(c)

        if len(valid_all) == 1:
            c = valid_all[0]
            org_names = [i['name'] for i in c['institutions']]
            return c['orcid'], {
                'source': 'openalex_global',
                'display_name': c['display_name'],
                'orgs': org_names,
                'works_count': c['works_count'],
            }

    return None, None


# ─── Crossref author search ──────────────────────────────────

CROSSREF_API = 'https://api.crossref.org'
CROSSREF_DELAY = 0.3  # Polite Pool


def crossref_find_orcid(fullname, db_gn, db_fn):
    """Busca ORCID via Crossref works por nome de autor.

    Procura works com esse autor e verifica se algum tem ORCID.
    Retorna (orcid, source_detail) ou (None, None).
    """
    query = urllib.parse.quote(fullname)
    url = f'{CROSSREF_API}/works?query.author={query}&rows=5&select=author,title'

    headers = {
        'Accept': 'application/json',
        'User-Agent': f'fetch_orcid/1.0 (mailto:{OPENALEX_EMAIL})',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f'CR-err ', end='', flush=True)
        return None, None

    items = data.get('message', {}).get('items', [])
    found_orcids = {}  # orcid → (name, title)

    for item in items:
        title = (item.get('title') or [''])[0]
        for author in item.get('author', []):
            orcid_url = author.get('ORCID', '')
            if not orcid_url:
                continue
            orcid_id = orcid_url.replace('http://orcid.org/', '').replace('https://orcid.org/', '')
            cr_gn = author.get('given', '')
            cr_fn = author.get('family', '')
            if name_compatible(db_gn, db_fn, cr_gn, cr_fn):
                if orcid_id not in found_orcids:
                    found_orcids[orcid_id] = (f'{cr_gn} {cr_fn}', title)

    if len(found_orcids) == 1:
        orcid_id, (cr_name, title) = list(found_orcids.items())[0]
        return orcid_id, {
            'source': 'crossref',
            'display_name': cr_name,
            'title': title[:80],
        }

    return None, None


# ─── Semantic Scholar author search ──────────────────────────

S2_API = 'https://api.semanticscholar.org/graph/v1'
S2_DELAY = 0.6  # 100 req/5 min sem API key


def semantic_scholar_find_orcid(fullname, db_gn, db_fn):
    """Busca ORCID via Semantic Scholar author search.

    Retorna (orcid, source_detail) ou (None, None).
    """
    query = urllib.parse.quote(fullname)
    url = f'{S2_API}/author/search?query={query}&fields=name,externalIds,affiliations,paperCount&limit=5'

    headers = {
        'Accept': 'application/json',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f'S2-err ', end='', flush=True)
        return None, None

    results = data.get('data', [])
    valid = []

    for item in results:
        ext_ids = item.get('externalIds') or {}
        orcid_id = ext_ids.get('ORCID')
        if not orcid_id:
            continue

        s2_name = item.get('name', '')
        parts = s2_name.rsplit(' ', 1)
        s2_gn = parts[0] if len(parts) > 1 else s2_name
        s2_fn = parts[1] if len(parts) > 1 else ''

        if name_compatible(db_gn, db_fn, s2_gn, s2_fn):
            valid.append({
                'orcid': orcid_id,
                'name': s2_name,
                'affiliations': item.get('affiliations', []),
                'paper_count': item.get('paperCount', 0),
            })

    if len(valid) == 1:
        c = valid[0]
        return c['orcid'], {
            'source': 'semantic_scholar',
            'display_name': c['name'],
            'affiliations': c['affiliations'][:3],
            'paper_count': c['paper_count'],
        }

    return None, None


def orcid_search(familyname, givenname_first):
    """Busca ORCID por familyname + primeiro nome."""
    fn = urllib.parse.quote(familyname)
    gn = urllib.parse.quote(givenname_first)
    url = f'{ORCID_API}/search/?q=family-name:{fn}+AND+given-names:{gn}'

    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return data
    except Exception as e:
        print(f'    ERRO search: {e}')
        return None


def orcid_employments(orcid_id):
    """Busca empregadores de um perfil ORCID."""
    url = f'{ORCID_API}/{orcid_id}/employments'
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        orgs = []
        for group in data.get('affiliation-group', []):
            for s in group.get('summaries', []):
                emp = s.get('employment-summary', {})
                org = emp.get('organization', {})
                name = org.get('name', '')
                addr = org.get('address', {})
                country = addr.get('country', '')
                city = addr.get('city', '')
                orgs.append({'name': name, 'country': country, 'city': city})
        return orgs
    except Exception as e:
        print(f'    ERRO employments: {e}')
        return []


def orcid_person(orcid_id):
    """Busca dados pessoais de um perfil ORCID (nome completo)."""
    url = f'{ORCID_API}/{orcid_id}/person'
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        name = data.get('name', {})
        gn = name.get('given-names', {}).get('value', '') if name.get('given-names') else ''
        fn = name.get('family-name', {}).get('value', '') if name.get('family-name') else ''
        return {'givenname': gn, 'familyname': fn}
    except Exception as e:
        print(f'    ERRO person: {e}')
        return {}


def has_br_affiliation(orgs):
    """Verifica se algum empregador é brasileiro."""
    for org in orgs:
        if org.get('country') == 'BR':
            return True
        name_lower = org.get('name', '').lower()
        if any(kw in name_lower for kw in ['brasil', 'brazil', 'brasileir']):
            return True
    return False


def affiliation_matches(db_affil, orcid_orgs):
    """Verifica se a afiliação do banco bate com algum empregador ORCID."""
    if not db_affil:
        return False

    # Extrair sigla principal da afiliação do banco (ex: "FAU-USP" → "USP")
    parts = re.split(r'[-/ ]', db_affil.strip())
    siglas = [p.strip() for p in parts if p.strip()]

    for sigla in siglas:
        keywords = SIGLA_KEYWORDS.get(sigla, [])
        if not keywords:
            # Tentar a sigla como substring
            keywords = [sigla]

        for org in orcid_orgs:
            org_name = org.get('name', '')
            org_lower = org_name.lower()
            org_noacc = strip_accents(org_lower)
            for kw in keywords:
                kw_lower = kw.lower()
                kw_noacc = strip_accents(kw_lower)
                if kw_lower in org_lower or kw_noacc in org_noacc:
                    return True
                if sigla.upper() in org_name.upper():
                    return True

    return False


def get_db_affiliation(cur, author_id):
    """Busca a afiliação mais recente do autor no banco."""
    cur.execute("""
        SELECT aa.affiliation, a.seminar_slug
        FROM article_author aa
        JOIN articles a ON aa.article_id = a.id
        WHERE aa.author_id = ? AND aa.affiliation IS NOT NULL AND aa.affiliation != ''
        ORDER BY a.seminar_slug DESC
        LIMIT 1
    """, (author_id,))
    row = cur.fetchone()
    return row[0] if row else None


def get_author_articles(cur, author_id):
    """Retorna títulos dos artigos do autor."""
    cur.execute("""
        SELECT a.id, a.title FROM article_author aa
        JOIN articles a ON aa.article_id = a.id
        WHERE aa.author_id = ?
        ORDER BY a.seminar_slug
    """, (author_id,))
    return cur.fetchall()


def name_compatible(db_gn, db_fn, orcid_gn, orcid_fn):
    """Verifica se o nome ORCID é compatível com o do banco."""
    # familyname deve ser similar
    db_fn_n = strip_accents(db_fn.lower().strip())
    orc_fn_n = strip_accents(orcid_fn.lower().strip())

    # Aceita igualdade ou um contendo o outro
    if db_fn_n != orc_fn_n:
        # Ex: "Lima" vs "Godinho Lima" — um contém o outro
        if db_fn_n not in orc_fn_n and orc_fn_n not in db_fn_n:
            return False

    # Primeiro nome deve ser similar
    db_first = first_real_name(db_gn)
    orc_first = first_real_name(orcid_gn)
    if not db_first or not orc_first:
        # Se um lado tem nome completo e o outro só iniciais, rejeitar
        # (ex: "Cecília" vs "T." — não se pode confirmar)
        return False

    db_f = strip_accents(db_first.lower())
    orc_f = strip_accents(orc_first.lower())
    return db_f == orc_f or db_f.startswith(orc_f) or orc_f.startswith(db_f)


# ─── Fase 1: Busca ────────────────────────────────────────────

def phase_search(resume=False, recheck_days=None):
    """Busca ORCIDs na API pública.

    Args:
        resume: retomar busca interrompida (usa orcid_results.json)
        recheck_days: se > 0, re-checa autores cuja última verificação
                      foi há mais de N dias (mesmo que já tenham sido checados)
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Garantir que as colunas de tracking existem
    cur.execute("PRAGMA table_info(authors)")
    cols = [r[1] for r in cur.fetchall()]
    if 'orcid_checked_at' not in cols:
        cur.execute('ALTER TABLE authors ADD COLUMN orcid_checked_at TEXT')
    if 'orcid_pipeline_version' not in cols:
        cur.execute('ALTER TABLE authors ADD COLUMN orcid_pipeline_version TEXT')
    conn.commit()

    # Carregar resultados anteriores se resumindo
    results = {'confirmed': [], 'candidates': [], 'not_found': [],
               'too_many': [], 'skipped': [], 'already_has': []}
    processed_ids = set()

    if resume and os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH, 'r') as f:
            results = json.load(f)
        for category in results.values():
            for entry in category:
                processed_ids.add(entry.get('author_id'))
        print(f'Retomando: {len(processed_ids)} autores já processados')

    # Carregar exclusões (falsos positivos conhecidos)
    cur.execute("SELECT author_id, orcid FROM orcid_exclusions")
    exclusions = set()
    for row in cur.fetchall():
        exclusions.add((row[0], row[1]))
    if exclusions:
        print(f'Exclusões carregadas: {len(exclusions)}')

    # Determinar cutoff para recheck
    recheck_cutoff = None
    if recheck_days and recheck_days > 0:
        recheck_cutoff = (datetime.now() - timedelta(days=recheck_days)).strftime('%Y-%m-%d')
        print(f'Modo recheck: re-verificando autores checados antes de {recheck_cutoff}')
        print(f'  Pipeline version atual: {PIPELINE_VERSION}')

    # Todos os autores sem ORCID, ordenados por nº de artigos
    cur.execute("""
        SELECT a.id, a.givenname, a.familyname, COUNT(aa.article_id) as n_arts,
               a.orcid_checked_at, a.orcid_pipeline_version
        FROM authors a
        JOIN article_author aa ON aa.author_id = a.id
        WHERE (a.orcid IS NULL OR a.orcid = '')
        GROUP BY a.id
        ORDER BY n_arts DESC
    """)
    authors_raw = cur.fetchall()

    # Filtrar autores conforme modo
    authors = []
    skipped_recent = 0
    for aid, gn, fn, n_arts, checked_at, pv in authors_raw:
        if recheck_cutoff:
            # Modo recheck: incluir se nunca checado OU checado antes do cutoff
            # OU checado com versão mais antiga
            if checked_at and checked_at >= recheck_cutoff and pv == PIPELINE_VERSION:
                skipped_recent += 1
                continue
        authors.append((aid, gn, fn, n_arts))

    total = len(authors)
    print(f'Autores sem ORCID: {len(authors_raw)}')
    if recheck_cutoff and skipped_recent:
        print(f'  Pulando {skipped_recent} já checados recentemente (v{PIPELINE_VERSION})')
    print(f'A processar: {total}')

    def mark_checked(author_id):
        """Registra que o autor foi verificado nesta execução."""
        now = datetime.now().strftime('%Y-%m-%d')
        cur.execute(
            "UPDATE authors SET orcid_checked_at = ?, orcid_pipeline_version = ? WHERE id = ?",
            (now, PIPELINE_VERSION, author_id))

    checked_count = 0  # para commit periódico

    for i, (aid, gn, fn, n_arts) in enumerate(authors):
        if aid in processed_ids:
            continue

        entry = {'author_id': aid, 'name': f'{gn} {fn}', 'n_arts': n_arts}

        # Pular iniciais
        if is_initials_only(gn):
            entry['reason'] = 'initials_only'
            results['skipped'].append(entry)
            mark_checked(aid)
            checked_count += 1
            if (i + 1) % 100 == 0:
                print(f'  [{i+1}/{total}] (pulando iniciais)')
            continue

        first = first_real_name(gn)
        if not first:
            entry['reason'] = 'no_real_name'
            results['skipped'].append(entry)
            mark_checked(aid)
            checked_count += 1
            continue

        print(f'  [{i+1}/{total}] {gn} {fn} ({n_arts} arts)...', end=' ', flush=True)

        db_affil = get_db_affiliation(cur, aid)
        entry['db_affiliation'] = db_affil

        # === Fase A: Tentar OpenAlex primeiro ===
        time.sleep(OPENALEX_DELAY)
        fullname = f'{gn} {fn}'.strip()
        oa_orcid, oa_detail = openalex_find_orcid(fullname, gn, fn, db_affil)
        if oa_orcid and (aid, oa_orcid) not in exclusions:
            entry['orcid'] = oa_orcid
            entry['orcid_name'] = oa_detail.get('display_name', '')
            entry['orgs'] = oa_detail.get('orgs', [])
            entry['source'] = oa_detail.get('source', 'openalex')
            entry['works_count'] = oa_detail.get('works_count', 0)
            results['confirmed'].append(entry)
            print(f'✓ OA {oa_orcid} ({oa_detail.get("display_name", "")})')
            mark_checked(aid)
            checked_count += 1
            # Salvar periodicamente
            if (i + 1) % 10 == 0:
                conn.commit()
                with open(RESULTS_PATH, 'w') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            continue

        # === Fase B: Fallback Crossref ===
        time.sleep(CROSSREF_DELAY)
        cr_orcid, cr_detail = crossref_find_orcid(fullname, gn, fn)
        if cr_orcid and (aid, cr_orcid) not in exclusions:
            entry['orcid'] = cr_orcid
            entry['orcid_name'] = cr_detail.get('display_name', '')
            entry['source'] = 'crossref'
            results['confirmed'].append(entry)
            print(f'✓ CR {cr_orcid} ({cr_detail.get("display_name", "")})')
            mark_checked(aid)
            checked_count += 1
            if (i + 1) % 10 == 0:
                conn.commit()
                with open(RESULTS_PATH, 'w') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            continue

        # === Fase C: Fallback Semantic Scholar ===
        time.sleep(S2_DELAY)
        s2_orcid, s2_detail = semantic_scholar_find_orcid(fullname, gn, fn)
        if s2_orcid and (aid, s2_orcid) not in exclusions:
            entry['orcid'] = s2_orcid
            entry['orcid_name'] = s2_detail.get('display_name', '')
            entry['source'] = 'semantic_scholar'
            results['confirmed'].append(entry)
            print(f'✓ S2 {s2_orcid} ({s2_detail.get("display_name", "")})')
            mark_checked(aid)
            checked_count += 1
            if (i + 1) % 10 == 0:
                conn.commit()
                with open(RESULTS_PATH, 'w') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            continue

        # === Fase D: Fallback API ORCID ===
        time.sleep(REQUEST_DELAY)
        data = orcid_search(fn, first)
        if data is None:
            entry['reason'] = 'api_error'
            results['skipped'].append(entry)
            print('ERRO API')
            mark_checked(aid)
            checked_count += 1
            continue

        num_found = data.get('num-found', 0)

        if num_found == 0:
            results['not_found'].append(entry)
            print('nenhum')
            mark_checked(aid)
            checked_count += 1
            continue

        if num_found > 20:
            # Tentar busca mais específica com givenname completo
            gn_clean = re.sub(r'\b(de|da|do|dos|das|e)\b', '', gn, flags=re.IGNORECASE).strip()
            gn_clean = re.sub(r'\s+', ' ', gn_clean).strip()
            if gn_clean != first:
                time.sleep(REQUEST_DELAY)
                data2 = orcid_search(fn, gn_clean)
                if data2 and 0 < data2.get('num-found', 0) <= 20:
                    data = data2
                    num_found = data2['num-found']
                    print(f'(refinado {num_found}) ', end='', flush=True)
                else:
                    entry['num_found'] = num_found
                    results['too_many'].append(entry)
                    print(f'demais ({num_found})')
                    mark_checked(aid)
                    checked_count += 1
                    continue
            else:
                entry['num_found'] = num_found
                results['too_many'].append(entry)
                print(f'demais ({num_found})')
                mark_checked(aid)
                checked_count += 1
                continue

        # Buscar perfis dos candidatos (limitar a MAX_PROFILES)
        orcid_ids = [r['orcid-identifier']['path'] for r in data.get('result', [])][:MAX_PROFILES]

        confirmed_orcid = None
        candidate_orcids = []

        for oid in orcid_ids:
            time.sleep(REQUEST_DELAY)
            person = orcid_person(oid)
            time.sleep(REQUEST_DELAY)
            orgs = orcid_employments(oid)

            orc_gn = person.get('givenname', '')
            orc_fn = person.get('familyname', '')

            # Verificar compatibilidade de nome
            if not name_compatible(gn, fn, orc_gn, orc_fn):
                continue

            is_br = has_br_affiliation(orgs)
            affil_match = affiliation_matches(db_affil, orgs) if db_affil else False

            org_names = [o.get('name', '') for o in orgs]

            candidate = {
                'orcid': oid,
                'orcid_name': f'{orc_gn} {orc_fn}',
                'orgs': org_names,
                'is_br': is_br,
                'affil_match': affil_match,
            }

            if is_br or affil_match:
                if confirmed_orcid is None:
                    confirmed_orcid = candidate
                else:
                    # Mais de um BR — ambíguo
                    candidate_orcids.append(confirmed_orcid)
                    candidate_orcids.append(candidate)
                    confirmed_orcid = None
            else:
                candidate_orcids.append(candidate)

        if confirmed_orcid and not candidate_orcids:
            entry['orcid'] = confirmed_orcid['orcid']
            entry['orcid_name'] = confirmed_orcid['orcid_name']
            entry['orgs'] = confirmed_orcid['orgs']
            results['confirmed'].append(entry)
            print(f'✓ {confirmed_orcid["orcid"]} ({confirmed_orcid["orcid_name"]})')
        elif num_found == 1 and not confirmed_orcid and candidate_orcids:
            # Único resultado mas sem afiliação BR — candidato
            entry['orcid_options'] = candidate_orcids
            results['candidates'].append(entry)
            c = candidate_orcids[0]
            print(f'? {c["orcid"]} (sem BR, {c.get("orcid_name", "")})')
        elif candidate_orcids:
            entry['orcid_options'] = candidate_orcids
            results['candidates'].append(entry)
            print(f'? {len(candidate_orcids)} candidatos')
        else:
            results['not_found'].append(entry)
            print('nenhum compatível')

        mark_checked(aid)
        checked_count += 1

        # Salvar e commitar periodicamente
        if (i + 1) % 10 == 0:
            conn.commit()
            with open(RESULTS_PATH, 'w') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    # Salvar e commitar resultados finais
    conn.commit()
    with open(RESULTS_PATH, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    conn.close()
    print(f'\nChecagem registrada para {checked_count} autores (pipeline v{PIPELINE_VERSION})')
    print_stats(results)


# ─── Fase 2: Revisão ──────────────────────────────────────────

def phase_review():
    """Mostra candidatos ambíguos para revisão."""
    if not os.path.exists(RESULTS_PATH):
        print(f'Resultados não encontrados: {RESULTS_PATH}')
        print('Execute --search primeiro.')
        sys.exit(1)

    with open(RESULTS_PATH, 'r') as f:
        results = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    candidates = results.get('candidates', [])
    print(f'Candidatos para revisão: {len(candidates)}\n')

    for entry in candidates:
        aid = entry['author_id']
        name = entry['name']
        n_arts = entry.get('n_arts', '?')
        db_affil = entry.get('db_affiliation', '')

        arts = get_author_articles(cur, aid)
        options = entry.get('orcid_options', [])

        print(f'--- {name} (id={aid}, {n_arts} arts, afil: {db_affil or "?"}) ---')
        for art_id, title in arts:
            print(f'  [{art_id}] {title[:70]}')
        print()
        for opt in options:
            orcid = opt['orcid']
            oname = opt.get('orcid_name', '')
            orgs = opt.get('orgs', [])
            is_br = opt.get('is_br', False)
            print(f'  ORCID: {orcid} — {oname}')
            print(f'    BR: {"sim" if is_br else "não"}')
            for org in orgs[:3]:
                print(f'    Org: {org}')
        print()

    conn.close()


# ─── Fase 3: Aplicação ────────────────────────────────────────

def phase_apply():
    """Aplica ORCIDs confirmados ao banco."""
    if not os.path.exists(RESULTS_PATH):
        print(f'Resultados não encontrados: {RESULTS_PATH}')
        sys.exit(1)

    with open(RESULTS_PATH, 'r') as f:
        results = json.load(f)

    confirmed = results.get('confirmed', [])
    if not confirmed:
        print('Nenhum ORCID confirmado para aplicar.')
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    applied = 0
    for entry in confirmed:
        aid = entry['author_id']
        orcid = entry['orcid']

        # Verificar se já tem ORCID
        cur.execute("SELECT orcid FROM authors WHERE id = ?", (aid,))
        row = cur.fetchone()
        if row and row[0]:
            continue

        now = datetime.now().strftime('%Y-%m-%d')
        cur.execute("UPDATE authors SET orcid = ?, orcid_checked_at = ?, orcid_pipeline_version = ? WHERE id = ?",
                    (orcid, now, PIPELINE_VERSION, aid))
        applied += 1
        print(f'  ✓ {entry["name"]} → {orcid}')

    conn.commit()
    conn.close()
    print(f'\nAplicados: {applied} ORCIDs')


# ─── Estatísticas ─────────────────────────────────────────────

def print_stats(results=None):
    """Mostra estatísticas dos resultados."""
    if results is None:
        if not os.path.exists(RESULTS_PATH):
            print(f'Resultados não encontrados: {RESULTS_PATH}')
            sys.exit(1)
        with open(RESULTS_PATH, 'r') as f:
            results = json.load(f)

    confirmed = results.get('confirmed', [])
    oa_count = sum(1 for c in confirmed if c.get('source', '').startswith('openalex'))
    cr_count = sum(1 for c in confirmed if c.get('source') == 'crossref')
    s2_count = sum(1 for c in confirmed if c.get('source') == 'semantic_scholar')
    orcid_count = len(confirmed) - oa_count - cr_count - s2_count

    print(f'\n{"="*50}')
    print(f'Confirmados total:    {len(confirmed)}')
    print(f'  - via OpenAlex:     {oa_count}')
    print(f'  - via Crossref:     {cr_count}')
    print(f'  - via Sem. Scholar: {s2_count}')
    print(f'  - via ORCID API:    {orcid_count}')
    print(f'Candidatos (LLM):  {len(results.get("candidates", []))}')
    print(f'Sem resultado:     {len(results.get("not_found", []))}')
    print(f'Muitos resultados: {len(results.get("too_many", []))}')
    print(f'Pulados:           {len(results.get("skipped", []))}')
    total = sum(len(v) for v in results.values())
    print(f'Total processados: {total}')


def print_check_status():
    """Mostra estatísticas de checagem de ORCIDs no banco."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM authors")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM authors WHERE orcid IS NOT NULL AND orcid != ''")
    with_orcid = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM authors WHERE orcid_checked_at IS NOT NULL")
    checked = cur.fetchone()[0]

    cur.execute("""SELECT orcid_pipeline_version, COUNT(*), MIN(orcid_checked_at), MAX(orcid_checked_at)
                   FROM authors WHERE orcid_checked_at IS NOT NULL
                   GROUP BY orcid_pipeline_version ORDER BY orcid_pipeline_version""")
    versions = cur.fetchall()

    cur.execute("""SELECT COUNT(*) FROM authors
                   WHERE (orcid IS NULL OR orcid = '') AND orcid_checked_at IS NULL""")
    never_checked = cur.fetchone()[0]

    conn.close()

    print(f'Total de autores:      {total}')
    print(f'Com ORCID:             {with_orcid} ({with_orcid*100/total:.1f}%)')
    print(f'Já checados:           {checked} ({checked*100/total:.1f}%)')
    print(f'Nunca checados:        {never_checked}')
    print(f'Pipeline version atual: {PIPELINE_VERSION}')
    print()
    if versions:
        print(f'{"Versão":<10} {"Qtd":>6} {"Primeira":>12} {"Última":>12}')
        print('-' * 44)
        for pv, cnt, min_date, max_date in versions:
            print(f'{pv or "?":<10} {cnt:>6} {min_date or "?":>12} {max_date or "?":>12}')


# ─── Fase 4: Raspagem de páginas de docentes ─────────────────

FACULTY_YAML = os.path.join(BASE, 'dict', 'faculty_pages.yaml')


def scrape_faculty_page(url):
    """Raspa uma página de docentes e extrai pares (nome, orcid).

    Abordagem genérica: encontra todos os ORCIDs no HTML e busca o nome
    mais próximo anterior em tags comuns (a, strong, b, h2-h4, td, span).
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (fetch_orcid scraper)',
        'Accept': 'text/html',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        ctx = __import__('ssl').create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = __import__('ssl').CERT_NONE
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'    ERRO fetch {url}: {e}')
        return []

    # Encontrar todos os ORCIDs na página
    results = []
    for m in re.finditer(r'orcid\.org/(\d{4}-\d{4}-\d{4}-[\dX]{4})', html):
        orcid_id = m.group(1)
        # Procurar nome no contexto anterior (até 800 chars antes)
        start = max(0, m.start() - 800)
        context = html[start:m.start()]

        # Extrair nomes de tags comuns (o último encontrado é o mais próximo)
        name_patterns = [
            r'<a[^>]*>([^<]{3,60})</a>',
            r'<strong>([^<]{3,60})</strong>',
            r'<b>([^<]{3,60})</b>',
            r'<h[2-5][^>]*>([^<]{3,60})</h[2-5]>',
            r'<td[^>]*>([^<]{3,60})</td>',
            r'<span[^>]*>([^<]{3,60})</span>',
            r'<p[^>]*>([^<]{3,60})</p>',
        ]

        candidates = []
        for pat in name_patterns:
            for nm in re.finditer(pat, context):
                text = nm.group(1).strip()
                text = re.sub(r'<[^>]+>', '', text).strip()  # remove tags internas
                # Filtrar: deve ter 2+ palavras, pelo menos uma maiúscula,
                # não ser email, link, ou tag
                if (len(text.split()) >= 2
                        and re.search(r'[A-ZÀ-Ü]', text)
                        and '@' not in text
                        and 'http' not in text.lower()
                        and '<' not in text
                        and not re.match(r'^[\d\s./-]+$', text)):
                    candidates.append((nm.start(), text))

        if candidates:
            # Pegar o mais próximo do ORCID (último na lista, pois finditer é em ordem)
            candidates.sort(key=lambda x: x[0])
            best_name = candidates[-1][1]
            # Limpar HTML entities
            best_name = best_name.replace('&amp;', '&').replace('&nbsp;', ' ')
            best_name = re.sub(r'&#?\w+;', '', best_name).strip()
            results.append((best_name, orcid_id))

    # Deduplicar por ORCID (mesmo ORCID pode aparecer múltiplas vezes)
    seen = set()
    unique = []
    for name, orcid_id in results:
        if orcid_id not in seen:
            seen.add(orcid_id)
            unique.append((name, orcid_id))

    return unique


def phase_scrape_faculty(apply=False):
    """Raspa páginas de docentes e cruza com autores sem ORCID."""
    try:
        import yaml
    except ImportError:
        print('ERRO: PyYAML necessário. pip install pyyaml')
        sys.exit(1)

    if not os.path.exists(FACULTY_YAML):
        print(f'Arquivo não encontrado: {FACULTY_YAML}')
        sys.exit(1)

    with open(FACULTY_YAML, 'r') as f:
        pages = yaml.safe_load(f)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # TODOS os autores sem ORCID
    cur.execute("""
        SELECT a.id, a.givenname, a.familyname
        FROM authors a
        WHERE (a.orcid IS NULL OR a.orcid = '')
    """)
    all_authors_no_orcid = [(aid, gn, fn) for aid, gn, fn in cur.fetchall()]

    # Index por familyname normalizado → autores
    from collections import defaultdict
    fn_index = defaultdict(list)
    for aid, gn, fn in all_authors_no_orcid:
        fn_norm = strip_accents(fn.lower().strip())
        fn_index[fn_norm].append((aid, gn, fn))

    total_found = 0
    total_new = 0
    applied_ids = []

    for page in pages:
        url = page.get('url', '')
        program = page.get('program', '')
        if not url:
            continue

        print(f'\n--- {program} ---')
        print(f'    {url}')

        time.sleep(0.5)
        faculty = scrape_faculty_page(url)
        if not faculty:
            print(f'    Nenhum ORCID encontrado na página')
            continue

        print(f'    {len(faculty)} docentes com ORCID na página')
        total_found += len(faculty)

        # Cruzar cada docente com TODOS os autores sem ORCID (por familyname)
        for page_name, page_orcid in faculty:
            page_parts = page_name.strip().split()
            if len(page_parts) < 2:
                continue

            fn_page = strip_accents(page_parts[-1].lower())
            candidates = fn_index.get(fn_page, [])

            for aid, gn, fn in candidates:
                # Primeiro nome deve bater
                first_page = strip_accents(page_parts[0].lower())
                first_db = strip_accents(gn.split()[0].lower()) if gn.split() else ''
                if first_page != first_db:
                    continue

                # Verificar compatibilidade completa
                if not name_compatible(gn, fn, ' '.join(page_parts[:-1]), page_parts[-1]):
                    continue

                # Verificação extra para faculty scrape: se ambos têm 3+ nomes,
                # o segundo nome deve ser compatível para evitar falsos positivos
                # (ex: "Eduardo Galbes Breda de Lima" vs "Eduardo Rocha Lima")
                db_parts = gn.split()
                particles = {'de', 'da', 'do', 'dos', 'das', 'e', 'del', 'di'}
                db_real = [p for p in db_parts if p.lower() not in particles]
                pg_real = [p for p in page_parts[:-1] if p.lower() not in particles]
                if len(db_real) >= 2 and len(pg_real) >= 2:
                    second_db = strip_accents(db_real[1].lower())
                    second_pg = strip_accents(pg_real[1].lower())
                    if second_db != second_pg and not second_db.startswith(second_pg) and not second_pg.startswith(second_db):
                        continue

                # Match!
                total_new += 1
                if apply:
                    now = datetime.now().strftime('%Y-%m-%d')
                    cur.execute("""UPDATE authors SET orcid = ?, orcid_checked_at = ?,
                                  orcid_pipeline_version = ? WHERE id = ? AND (orcid IS NULL OR orcid = '')""",
                                (page_orcid, now, PIPELINE_VERSION, aid))
                    applied_ids.append(aid)
                    print(f'    ✓ {gn} {fn} ← {page_orcid} ({page_name})')
                else:
                    print(f'    ? {gn} {fn} ← {page_orcid} ({page_name})')

    if apply and applied_ids:
        conn.commit()

    conn.close()

    print(f'\n{"="*50}')
    print(f'Docentes com ORCID encontrados: {total_found}')
    print(f'Matches com autores sem ORCID: {total_new}')
    if apply:
        print(f'Aplicados ao banco: {len(applied_ids)}')
    else:
        print('(use --scrape-faculty --apply para aplicar)')


def main():
    if '--search' in sys.argv:
        resume = '--resume' in sys.argv
        recheck_days = None
        for i, arg in enumerate(sys.argv):
            if arg == '--recheck-days' and i + 1 < len(sys.argv):
                recheck_days = int(sys.argv[i + 1])
        phase_search(resume=resume, recheck_days=recheck_days)
    elif '--review' in sys.argv:
        phase_review()
    elif '--apply' in sys.argv and '--scrape-faculty' not in sys.argv:
        phase_apply()
    elif '--scrape-faculty' in sys.argv:
        do_apply = '--apply' in sys.argv
        phase_scrape_faculty(apply=do_apply)
    elif '--check-status' in sys.argv:
        print_check_status()
    elif '--stats' in sys.argv:
        print_stats()
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
