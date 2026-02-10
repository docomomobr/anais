#!/usr/bin/env python3
"""Busca ORCIDs dos autores via API pública do ORCID.

Fase 1 (--search): Busca na API, classifica resultados, salva em JSON.
Fase 2 (--review): Mostra candidatos ambíguos para revisão.
Fase 3 (--apply):  Aplica ORCIDs confirmados ao banco.

Uso:
    python3 scripts/fetch_orcid.py --search          # Busca na API (~32 min)
    python3 scripts/fetch_orcid.py --search --resume  # Retoma busca interrompida
    python3 scripts/fetch_orcid.py --review           # Mostra candidatos para revisão
    python3 scripts/fetch_orcid.py --apply            # Aplica ORCIDs ao banco
    python3 scripts/fetch_orcid.py --stats            # Estatísticas do resultado
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

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE, 'anais.db')
RESULTS_PATH = os.path.join(BASE, 'orcid_results.json')

ORCID_API = 'https://pub.orcid.org/v3.0'
REQUEST_DELAY = 0.5  # seconds between API requests
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
        return True  # não dá para comparar, aceitar

    db_f = strip_accents(db_first.lower())
    orc_f = strip_accents(orc_first.lower())
    return db_f == orc_f or db_f.startswith(orc_f) or orc_f.startswith(db_f)


# ─── Fase 1: Busca ────────────────────────────────────────────

def phase_search(resume=False):
    """Busca ORCIDs na API pública."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

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

    # Todos os autores sem ORCID, ordenados por nº de artigos
    cur.execute("""
        SELECT a.id, a.givenname, a.familyname, COUNT(aa.article_id) as n_arts
        FROM authors a
        JOIN article_author aa ON aa.author_id = a.id
        WHERE (a.orcid IS NULL OR a.orcid = '')
        GROUP BY a.id
        ORDER BY n_arts DESC
    """)
    authors = cur.fetchall()
    total = len(authors)
    print(f'Autores sem ORCID: {total}')

    for i, (aid, gn, fn, n_arts) in enumerate(authors):
        if aid in processed_ids:
            continue

        entry = {'author_id': aid, 'name': f'{gn} {fn}', 'n_arts': n_arts}

        # Pular iniciais
        if is_initials_only(gn):
            entry['reason'] = 'initials_only'
            results['skipped'].append(entry)
            if (i + 1) % 100 == 0:
                print(f'  [{i+1}/{total}] (pulando iniciais)')
            continue

        first = first_real_name(gn)
        if not first:
            entry['reason'] = 'no_real_name'
            results['skipped'].append(entry)
            continue

        print(f'  [{i+1}/{total}] {gn} {fn} ({n_arts} arts)...', end=' ', flush=True)

        # Buscar na API
        time.sleep(REQUEST_DELAY)
        data = orcid_search(fn, first)
        if data is None:
            entry['reason'] = 'api_error'
            results['skipped'].append(entry)
            print('ERRO API')
            continue

        num_found = data.get('num-found', 0)

        if num_found == 0:
            results['not_found'].append(entry)
            print('nenhum')
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
                    continue
            else:
                entry['num_found'] = num_found
                results['too_many'].append(entry)
                print(f'demais ({num_found})')
                continue

        # Buscar perfis dos candidatos (limitar a MAX_PROFILES)
        orcid_ids = [r['orcid-identifier']['path'] for r in data.get('result', [])][:MAX_PROFILES]

        db_affil = get_db_affiliation(cur, aid)
        entry['db_affiliation'] = db_affil

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

        # Salvar periodicamente
        if (i + 1) % 10 == 0:
            with open(RESULTS_PATH, 'w') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    # Salvar resultados finais
    with open(RESULTS_PATH, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    conn.close()
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

        cur.execute("UPDATE authors SET orcid = ? WHERE id = ?", (orcid, aid))
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

    print(f'\n{"="*50}')
    print(f'Confirmados (BR):  {len(results.get("confirmed", []))}')
    print(f'Candidatos (LLM):  {len(results.get("candidates", []))}')
    print(f'Sem resultado:     {len(results.get("not_found", []))}')
    print(f'Muitos resultados: {len(results.get("too_many", []))}')
    print(f'Pulados:           {len(results.get("skipped", []))}')
    total = sum(len(v) for v in results.values())
    print(f'Total processados: {total}')


def main():
    if '--search' in sys.argv:
        resume = '--resume' in sys.argv
        phase_search(resume=resume)
    elif '--review' in sys.argv:
        phase_review()
    elif '--apply' in sys.argv:
        phase_apply()
    elif '--stats' in sys.argv:
        print_stats()
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
