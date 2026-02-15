#!/usr/bin/env python3
"""
Importa XMLs no OJS via Native XML Plugin.

Modos de operação:
  --import           Importa XMLs faltantes (sessão fresca por XML)
  --cleanup          Limpa issues duplicadas/vazias/parciais
  --verify           Verifica estado atual (lista issues e contagens)
  --upload-galleys   Upload PDFs de edição completa como issue galleys
  --dry-run          Apenas lista XMLs sem conectar

Regras:
- Sessão FRESCA para cada XML (evita rate limiting)
- Mínimo de chamadas API por sessão (login → upload → import → fim)
- Após importar, NÃO verifica contagem na mesma sessão
- Verificação é feita em modo separado (--verify)
- Se a resposta do import vier vazia, tenta verificar se os artigos
  foram importados mesmo assim (fire-and-check)
- NUNCA deixar issues vazias ou parciais no servidor

Uso:
    python3 scripts/import_ojs.py --env test                    # importa faltantes
    python3 scripts/import_ojs.py --env test --slug sdnne07     # importa um
    python3 scripts/import_ojs.py --env test --cleanup          # só limpa duplicatas
    python3 scripts/import_ojs.py --env test --verify           # verifica estado
    python3 scripts/import_ojs.py --env test --dry-run          # só lista
"""

import argparse
import glob
import os
import re
import sqlite3
import sys
import time

import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ENVS = {
    'test': {
        'url': 'https://docomomo.ojs.com.br/index.php/ojs',
        'username': 'editor',
        'password': '***',
    },
    'prod': {
        'url': 'https://publicacoes.docomomobrasil.com/anais',
        'username': 'dmacedo',
        'password': '***',
    },
}

IMPORT_DELAY = 60  # segundos entre importações (cooldown do servidor)


def fresh_session(base_url, username, password):
    """Cria sessão nova, faz login, retorna (session, csrf_token)."""
    s = requests.Session()
    # Login
    resp = s.post(
        f'{base_url}/login/signIn',
        data={'username': username, 'password': password},
        allow_redirects=True, timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f'Login falhou: HTTP {resp.status_code}')
    # CSRF
    resp = s.get(
        f'{base_url}/management/importexport/plugin/NativeImportExportPlugin',
        timeout=30,
    )
    match = re.search(r'"csrfToken":"([^"]+)"', resp.text)
    if not match:
        raise RuntimeError('Não obteve CSRF token')
    return s, match.group(1)


def upload_and_import(base_url, session, csrf, filepath):
    """Upload + import de um XML. Retorna (sucesso, mensagem, temp_id)."""
    # 1. Upload
    with open(filepath, 'rb') as f:
        resp = session.post(
            f'{base_url}/management/importexport/plugin/'
            'NativeImportExportPlugin/uploadImportXML',
            headers={'X-Requested-With': 'XMLHttpRequest'},
            data={'csrfToken': csrf},
            files={'uploadedFile': (os.path.basename(filepath), f, 'text/xml')},
            timeout=120,
        )
    if resp.status_code != 200:
        return False, f'upload HTTP {resp.status_code}', None
    match = re.search(r'"temporaryFileId":"?(\d+)', resp.text)
    if not match:
        return False, f'sem temporaryFileId: {resp.text[:200]}', None
    temp_id = match.group(1)

    # 2. importBounce
    session.post(
        f'{base_url}/management/importexport/plugin/'
        'NativeImportExportPlugin/importBounce',
        data={'csrfToken': csrf, 'temporaryFileId': temp_id},
        timeout=30,
    )

    # 3. Executar import (pode demorar)
    try:
        resp = session.get(
            f'{base_url}/management/importexport/plugin/'
            'NativeImportExportPlugin/import',
            params={'temporaryFileId': temp_id, 'csrfToken': csrf},
            timeout=600,
        )
        text = resp.text
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False, 'timeout/conexão perdida na execução', temp_id

    if not text:
        return False, 'resposta vazia', temp_id
    if 'xito' in text:
        return True, 'OK', temp_id
    errors = re.findall(r'<li>([^<]+)</li>', text)
    if errors:
        return False, '; '.join(e.strip()[:120] for e in errors[:5]), temp_id
    return False, f'resposta desconhecida: {text[:200]}', temp_id


def count_issue_articles(base_url, session, issue_id):
    """Conta artigos de uma issue. Retorna -1 se erro."""
    try:
        resp = session.get(
            f'{base_url}/api/v1/submissions',
            params={'issueIds': issue_id, 'count': 1},
            headers={'Accept': 'application/json'}, timeout=30,
        )
        if resp.status_code != 200:
            return -1
        return resp.json().get('itemsMax', 0)
    except Exception:
        return -1


def load_all_issues(base_url, session):
    """Carrega TODAS as issues. Retorna lista de {id, slug}."""
    issues = []
    offset = 0
    while True:
        try:
            resp = session.get(
                f'{base_url}/api/v1/issues',
                params={'count': 50, 'offset': offset},
                headers={'Accept': 'application/json'}, timeout=30,
            )
        except Exception:
            break
        if resp.status_code != 200:
            break
        data = resp.json()
        items = data.get('items', [])
        if not items:
            break
        for iss in items:
            url = iss.get('publishedUrl', '') or ''
            slug = url.rstrip('/').split('/')[-1] if url else None
            if slug and slug not in ('ojs', 'anais'):
                issues.append({'id': iss['id'], 'slug': slug})
        if offset + len(items) >= data.get('itemsMax', 0):
            break
        offset += 50
    return issues


def get_issue_submission_ids(base_url, session, issue_id):
    """Retorna lista de submission IDs de uma issue."""
    ids = []
    offset = 0
    while True:
        try:
            resp = session.get(
                f'{base_url}/api/v1/submissions',
                params={'issueIds': issue_id, 'count': 100, 'offset': offset},
                headers={'Accept': 'application/json'}, timeout=30,
            )
            if resp.status_code != 200:
                break
            data = resp.json()
        except Exception:
            break
        items = data.get('items', [])
        if not items:
            break
        ids.extend(item['id'] for item in items)
        if len(ids) >= data.get('itemsMax', 0):
            break
        offset += 100
    return ids


def delete_submission(base_url, session, csrf, sub_id):
    """Despublica e deleta um submission."""
    try:
        resp = session.get(
            f'{base_url}/api/v1/submissions/{sub_id}',
            headers={'Accept': 'application/json'}, timeout=15,
        )
        if resp.status_code != 200:
            return False
        pub_id = resp.json().get('currentPublicationId')
        if pub_id:
            session.put(
                f'{base_url}/api/v1/submissions/{sub_id}/publications/{pub_id}/unpublish',
                headers={'X-Csrf-Token': csrf, 'Accept': 'application/json'},
                timeout=15,
            )
        resp = session.delete(
            f'{base_url}/api/v1/submissions/{sub_id}',
            headers={'X-Csrf-Token': csrf, 'Accept': 'application/json'},
            timeout=15,
        )
        return resp.status_code == 200
    except Exception:
        return False


def delete_issue(base_url, session, csrf, issue_id):
    """Deleta uma issue (deve estar sem artigos)."""
    try:
        resp = session.post(
            f'{base_url}/$$$call$$$/grid/issues/back-issue-grid/delete-issue',
            data={'csrfToken': csrf, 'issueId': issue_id},
            timeout=30,
        )
        return resp.status_code == 200
    except Exception:
        return False


def wipe_issue(base_url, session, csrf, issue_id, slug=''):
    """Apaga todos os artigos de uma issue e depois a issue em si."""
    sub_ids = get_issue_submission_ids(base_url, session, issue_id)
    if sub_ids:
        print(f'    apagando {len(sub_ids)} artigos da issue {issue_id} ({slug})...')
        for i, sub_id in enumerate(sub_ids):
            delete_submission(base_url, session, csrf, sub_id)
            time.sleep(1)
    if delete_issue(base_url, session, csrf, issue_id):
        print(f'    issue {issue_id} ({slug}) apagada')
        return True
    else:
        print(f'    AVISO: não conseguiu apagar issue {issue_id} ({slug})')
        return False


def get_expected_counts(db_path):
    """Lê contagem esperada de artigos por seminário."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT seminar_slug, COUNT(*) FROM articles "
        "WHERE seminar_slug NOT LIKE 'sdbr%' GROUP BY seminar_slug"
    ).fetchall()
    conn.close()
    return dict(rows)


def cmd_verify(env, expected):
    """Verifica estado atual do servidor (issues e contagens)."""
    base = env['url']
    print('Login...')
    s, csrf = fresh_session(base, env['username'], env['password'])

    print('Carregando issues...')
    all_issues = load_all_issues(base, s)
    print(f'{len(all_issues)} issues encontradas\n')

    from collections import defaultdict
    by_slug = defaultdict(list)
    for iss in all_issues:
        by_slug[iss['slug']].append(iss['id'])

    good = {}
    problems = []

    for slug, ids in sorted(by_slug.items()):
        exp = expected.get(slug, '?')
        for issue_id in ids:
            count = count_issue_articles(base, s, issue_id)
            if count == -1:
                # Sessão pode ter expirado, refazer
                time.sleep(5)
                s, csrf = fresh_session(base, env['username'], env['password'])
                count = count_issue_articles(base, s, issue_id)

            status = ''
            if isinstance(exp, int):
                if count >= exp:
                    status = ' ✅'
                    good[slug] = issue_id
                elif count == 0:
                    status = ' ❌ VAZIA'
                    problems.append((slug, issue_id, count))
                elif count > 0:
                    status = f' ⚠️ PARCIAL (esperado {exp})'
                    problems.append((slug, issue_id, count))
            print(f'  {slug}: issue {issue_id}, {count} arts (esperado: {exp}){status}')
            time.sleep(2)  # Delay entre contagens

    # Slugs sem issue
    all_slugs = set(expected.keys())
    found_slugs = set(by_slug.keys())
    missing = all_slugs - found_slugs
    if missing:
        print(f'\nSem issue no servidor ({len(missing)}):')
        for slug in sorted(missing):
            print(f'  {slug} ({expected[slug]} artigos)')

    print(f'\n--- Resumo ---')
    print(f'OK: {len(good)}/{len(expected)}')
    if problems:
        print(f'Problemas: {len(problems)}')
    if missing:
        print(f'Faltam: {len(missing)}')

    return good


def cmd_cleanup(env, expected):
    """Limpa issues duplicadas, vazias e parciais."""
    base = env['url']
    print('Login...')
    s, csrf = fresh_session(base, env['username'], env['password'])

    print('Carregando issues...')
    all_issues = load_all_issues(base, s)
    print(f'{len(all_issues)} issues encontradas\n')

    from collections import defaultdict
    by_slug = defaultdict(list)
    for iss in all_issues:
        by_slug[iss['slug']].append(iss['id'])

    to_delete = []

    for slug, ids in sorted(by_slug.items()):
        exp = expected.get(slug, 0)
        good_id = None

        for issue_id in sorted(ids):
            count = count_issue_articles(base, s, issue_id)
            if count == -1:
                time.sleep(5)
                s, csrf = fresh_session(base, env['username'], env['password'])
                count = count_issue_articles(base, s, issue_id)
            if count == -1:
                print(f'  {slug}: issue {issue_id} — ERRO na contagem, pulando')
                continue
            if exp > 0 and count >= exp and good_id is None:
                good_id = issue_id
                print(f'  {slug}: issue {issue_id} OK ({count} arts)')
            else:
                to_delete.append((issue_id, slug, count))
                label = f'{count} arts' if count > 0 else 'vazia'
                if good_id:
                    print(f'  {slug}: issue {issue_id} DUPLICATA ({label})')
                else:
                    print(f'  {slug}: issue {issue_id} ({label}, esperado {exp})')
            time.sleep(2)

    if not to_delete:
        print('\nNenhuma issue para limpar.')
        return

    print(f'\n{len(to_delete)} issues para apagar:')
    for issue_id, slug, count in to_delete:
        label = f'{count} arts' if count > 0 else 'vazia'
        print(f'  issue {issue_id} ({slug}): {label}')

    print('\nApagando...')
    for issue_id, slug, count in to_delete:
        # Sessão fresca para cada deleção pesada
        s, csrf = fresh_session(base, env['username'], env['password'])
        wipe_issue(base, s, csrf, issue_id, slug)
        time.sleep(3)

    print('Limpeza concluída.')


def cmd_import(env, expected, xml_dir, slug_filter=None):
    """Importa XMLs faltantes. Sessão fresca para cada XML."""
    base = env['url']

    # Listar XMLs
    if slug_filter:
        files = [os.path.join(xml_dir, f'{slug_filter}.xml')]
        if not os.path.exists(files[0]):
            print(f'ERRO: {files[0]} não existe')
            sys.exit(1)
    else:
        files = sorted(glob.glob(os.path.join(xml_dir, '*.xml')))
    files = [f for f in files if not os.path.basename(f).startswith('sdbr')]

    # Descobrir quais já existem (sessão 1: só lista issues, sem contar artigos)
    print('Verificando issues existentes...')
    s, csrf = fresh_session(base, env['username'], env['password'])
    existing_issues = load_all_issues(base, s)
    existing_slugs = {iss['slug'] for iss in existing_issues}
    print(f'  {len(existing_slugs)} slugs no servidor')
    del s  # Descarta sessão

    # Filtrar XMLs a importar (exclui os que já têm issue)
    to_import = []
    for f in files:
        slug = os.path.basename(f).replace('.xml', '')
        if slug not in existing_slugs:
            to_import.append(f)
        else:
            print(f'  {slug}: já existe (pulando)')

    if not to_import:
        print('\nTodos os seminários já têm issue no servidor.')
        print('Use --verify para conferir as contagens.')
        return

    print(f'\n{len(to_import)} seminários para importar:\n')

    success = []
    for i, filepath in enumerate(to_import, 1):
        slug = os.path.basename(filepath).replace('.xml', '')
        size = os.path.getsize(filepath)
        exp = expected.get(slug, '?')

        print(f'[{i}/{len(to_import)}] {slug} ({size:,} bytes, esperado: {exp} arts)')

        # Sessão FRESCA para cada XML
        try:
            s, csrf = fresh_session(base, env['username'], env['password'])
        except Exception as e:
            print(f'    ERRO no login: {e}')
            print(f'    PARANDO.')
            sys.exit(1)

        print(f'    sessão nova, CSRF: {csrf[:12]}...')

        # Upload + import
        try:
            ok, msg, temp_id = upload_and_import(base, s, csrf, filepath)
        except Exception as e:
            print(f'    EXCEÇÃO: {e}')
            ok, msg, temp_id = False, str(e), None

        if ok:
            print(f'    OK — importação confirmada pelo servidor')
            success.append(slug)
        else:
            print(f'    Resultado: {msg}')
            # Se a resposta veio vazia, talvez o import tenha funcionado
            # mas o servidor cortou a resposta. Esperar e verificar com sessão nova.
            if 'vazia' in msg or 'timeout' in msg:
                print(f'    Aguardando 120s para o servidor processar...')
                time.sleep(120)
                try:
                    s2, csrf2 = fresh_session(base, env['username'], env['password'])
                    issues2 = load_all_issues(base, s2)
                    slug_issues = [iss for iss in issues2 if iss['slug'] == slug]
                    if slug_issues:
                        issue_id = slug_issues[0]['id']
                        count = count_issue_articles(base, s2, issue_id)
                        if isinstance(exp, int) and count >= exp:
                            print(f'    ✅ SIM! {count} artigos importados (issue {issue_id})')
                            success.append(slug)
                        elif count > 0:
                            print(f'    ⚠️ PARCIAL: {count}/{exp} artigos (issue {issue_id})')
                            print(f'    Apagando issue parcial...')
                            wipe_issue(base, s2, csrf2, issue_id, slug)
                            print(f'    PARANDO.')
                            sys.exit(1)
                        else:
                            print(f'    ❌ Issue {issue_id} criada mas vazia. Apagando...')
                            wipe_issue(base, s2, csrf2, issue_id, slug)
                    else:
                        print(f'    Issue não encontrada — import realmente falhou')
                    del s2
                except Exception as e2:
                    print(f'    Erro na verificação: {e2}')
                    print(f'    PARANDO. Verificar manualmente.')
                    sys.exit(1)
            else:
                # Erro definitivo (não timeout/vazio) — limpar e parar
                print(f'    PARANDO. Limpando issue se criada...')
                time.sleep(5)
                try:
                    s2, csrf2 = fresh_session(base, env['username'], env['password'])
                    issues2 = load_all_issues(base, s2)
                    for iss in issues2:
                        if iss['slug'] == slug and iss['id'] not in [
                            i2['id'] for i2 in existing_issues
                        ]:
                            wipe_issue(base, s2, csrf2, iss['id'], slug)
                except Exception:
                    print(f'    AVISO: não conseguiu limpar. Verificar manualmente.')
                sys.exit(1)

        # Cooldown entre importações
        if i < len(to_import):
            print(f'    Aguardando {IMPORT_DELAY}s...')
            time.sleep(IMPORT_DELAY)

    # Resumo
    print(f'\n{"="*50}')
    print(f'IMPORTADOS: {len(success)}/{len(to_import)}')
    if success:
        print(f'  {", ".join(success)}')

    remaining = len(to_import) - len(success)
    if remaining:
        print(f'FALTARAM: {remaining}')
        print('Use --verify para conferir estado e --import para tentar novamente.')


REGION_MAP = {
    'sdnne': 'regionais/nne',
    'sdmg': 'regionais/se',
    'sdrj': 'regionais/se',
    'sdsp': 'regionais/se',
    'sdsul': 'regionais/sul',
    'sdbr': 'nacionais',
}


def find_volume_pdf(slug):
    """Localiza o PDF do volume completo a partir do slug."""
    db_path = os.path.join(BASE_DIR, 'anais.db')
    conn = sqlite3.connect(db_path)
    row = conn.execute('SELECT volume_pdf FROM seminars WHERE slug = ?', (slug,)).fetchone()
    conn.close()
    if not row or not row[0]:
        return None
    filename = row[0]
    # Determinar diretório
    for prefix, region_dir in REGION_MAP.items():
        if slug.startswith(prefix):
            # Caminhos possíveis: {region}/{slug}/pdfs/{filename} ou {region}/{slug}/{filename}
            for subpath in [
                os.path.join(region_dir, slug, 'pdfs', filename),
                os.path.join(region_dir, slug, filename),
                os.path.join(region_dir, filename),
            ]:
                full = os.path.join(BASE_DIR, subpath)
                if os.path.isfile(full):
                    return full
    return None


def upload_issue_galley(base_url, session, csrf, issue_id, filepath, label='Edição completa'):
    """Upload PDF como issue galley. Retorna True se ok."""
    # Step 1: Add galley entry
    resp = session.post(
        f'{base_url}/$$$call$$$/grid/issues/issue-galley-grid/add-galley',
        data={
            'csrfToken': csrf,
            'issueId': issue_id,
            'label': label,
            'galleyLocale': 'pt_BR',
        },
        timeout=30,
    )
    if resp.status_code != 200:
        return False, f'add-galley HTTP {resp.status_code}'

    # Extrair galleyId da resposta
    match = re.search(r'"issueGalleyId"[:\s]*"?(\d+)', resp.text)
    if not match:
        # Tentar outra forma de extrair o ID
        match = re.search(r'galleyId[=&](\d+)', resp.text)
    if not match:
        return False, f'galleyId não encontrado na resposta add-galley'
    galley_id = match.group(1)

    # Step 2: Upload file
    with open(filepath, 'rb') as f:
        resp = session.post(
            f'{base_url}/$$$call$$$/grid/issues/issue-galley-grid/upload-file',
            data={
                'csrfToken': csrf,
                'issueId': issue_id,
                'issueGalleyId': galley_id,
            },
            files={'uploadedFile': (os.path.basename(filepath), f, 'application/pdf')},
            timeout=600,
        )
    if resp.status_code != 200:
        return False, f'upload-file HTTP {resp.status_code}'

    return True, f'galley {galley_id}'


def cmd_upload_galleys(env, slug_filter=None):
    """Upload PDFs de edição completa como issue galleys."""
    base = env['url']
    db_path = os.path.join(BASE_DIR, 'anais.db')
    conn = sqlite3.connect(db_path)

    # Buscar seminários com volume_pdf
    if slug_filter:
        rows = conn.execute(
            "SELECT slug, volume_pdf FROM seminars WHERE slug = ? AND volume_pdf IS NOT NULL",
            (slug_filter,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT slug, volume_pdf FROM seminars WHERE volume_pdf IS NOT NULL "
            "AND slug NOT LIKE 'sdbr%' ORDER BY slug"
        ).fetchall()
    conn.close()

    if not rows:
        print('Nenhum seminário com volume_pdf encontrado.')
        return

    print(f'{len(rows)} seminários com edição completa\n')

    # Login e listar issues
    s, csrf = fresh_session(base, env['username'], env['password'])
    all_issues = load_all_issues(base, s)
    issue_map = {iss['slug']: iss['id'] for iss in all_issues}

    for slug, volume_pdf in rows:
        pdf_path = find_volume_pdf(slug)
        if not pdf_path:
            print(f'  {slug}: PDF não encontrado ({volume_pdf})')
            continue

        issue_id = issue_map.get(slug)
        if not issue_id:
            print(f'  {slug}: issue não encontrada no OJS')
            continue

        size_mb = os.path.getsize(pdf_path) / 1024 / 1024
        if size_mb > 20:
            print(f'  {slug}: PDF muito grande ({size_mb:.1f} MB > 20 MB limite), pulando')
            continue

        print(f'  {slug}: issue {issue_id}, {size_mb:.1f} MB ... ', end='', flush=True)

        # Sessão fresca para cada upload
        try:
            s, csrf = fresh_session(base, env['username'], env['password'])
        except Exception as e:
            print(f'ERRO login: {e}')
            break

        ok, msg = upload_issue_galley(base, s, csrf, issue_id, pdf_path)
        if ok:
            print(f'OK ({msg})')
        else:
            print(f'ERRO: {msg}')

        time.sleep(5)

    print('\nUpload de galleys concluído.')


PER_ARTICLE_DELAY = 15  # segundos entre artigos (mesmo issue, mais rápido)


def cmd_import_per_article(env, expected, xml_dir, slug_filter=None):
    """Importa XMLs per-article (1 artigo por XML, com PDF embutido).

    Diferenças do cmd_import:
    - Aceita múltiplos XMLs por issue (sdrj04-001.xml, sdrj04-002.xml, ...)
    - Não pula issues existentes (cada XML adiciona 1 artigo à issue)
    - Delay menor entre XMLs (mesmo issue)
    - Para no primeiro erro (não tenta recuperar parciais)
    """
    base = env['url']

    # Listar XMLs
    if slug_filter:
        pattern = os.path.join(xml_dir, f'{slug_filter}-*.xml')
        files = sorted(glob.glob(pattern))
        if not files:
            # Tenta arquivo único (fallback para modo antigo)
            single = os.path.join(xml_dir, f'{slug_filter}.xml')
            if os.path.exists(single):
                files = [single]
            else:
                print(f'ERRO: nenhum XML encontrado para {slug_filter} em {xml_dir}/')
                sys.exit(1)
    else:
        files = sorted(glob.glob(os.path.join(xml_dir, '*.xml')))
    files = [f for f in files if not os.path.basename(f).startswith('sdbr')]

    if not files:
        print('Nenhum XML encontrado.')
        return

    # Group by slug prefix (for progress display)
    from collections import OrderedDict
    by_slug = OrderedDict()
    for f in files:
        name = os.path.basename(f).replace('.xml', '')
        # Extract slug: everything before last dash-number (sdrj04-001 → sdrj04)
        parts = name.rsplit('-', 1)
        if len(parts) == 2 and parts[1].isdigit():
            slug = parts[0]
        else:
            slug = name
        by_slug.setdefault(slug, []).append(f)

    total_files = len(files)
    total_slugs = len(by_slug)
    print(f'{total_files} XMLs para {total_slugs} seminários\n')

    for slug_name in by_slug:
        exp = expected.get(slug_name, '?')
        n = len(by_slug[slug_name])
        sizes = [os.path.getsize(f) for f in by_slug[slug_name]]
        max_size = max(sizes)
        total_size = sum(sizes)
        print(f'  {slug_name}: {n} XMLs, {total_size/1024/1024:.1f} MB total, '
              f'maior: {max_size/1024/1024:.1f} MB (esperado: {exp} arts)')

    print()

    # Import sequentially
    success = 0
    errors = []
    global_idx = 0

    for slug_name, slug_files in by_slug.items():
        exp = expected.get(slug_name, '?')
        print(f'=== {slug_name} ({len(slug_files)} artigos, esperado: {exp}) ===')

        for j, filepath in enumerate(slug_files):
            global_idx += 1
            name = os.path.basename(filepath).replace('.xml', '')
            size = os.path.getsize(filepath)

            print(f'  [{global_idx}/{total_files}] {name} ({size/1024:.0f} KB)', end=' ')
            sys.stdout.flush()

            # Sessão fresca para cada XML
            try:
                s, csrf = fresh_session(base, env['username'], env['password'])
            except Exception as e:
                print(f'ERRO login: {e}')
                errors.append((name, str(e)))
                print('PARANDO.')
                break

            try:
                ok, msg, temp_id = upload_and_import(base, s, csrf, filepath)
            except Exception as e:
                ok, msg = False, str(e)

            if ok:
                print('OK')
                success += 1
            else:
                print(f'ERRO: {msg}')
                errors.append((name, msg))
                # Para per-article, parar no primeiro erro real
                if 'vazia' not in msg and 'timeout' not in msg:
                    print('PARANDO no primeiro erro.')
                    break
                # Se timeout/vazio, tentar continuar (pode ter funcionado)
                print('  (resposta vazia/timeout — continuando)')
                success += 1  # Otimista — verificar depois

            # Delay entre artigos
            if global_idx < total_files:
                time.sleep(PER_ARTICLE_DELAY)

        else:
            # Inner loop completed without break
            continue
        # Inner loop broke — stop outer too
        break

    # Resumo
    print(f'\n{"="*50}')
    print(f'IMPORTADOS: {success}/{total_files}')
    if errors:
        print(f'ERROS: {len(errors)}')
        for name, msg in errors:
            print(f'  {name}: {msg}')
    print(f'\nUse --verify para conferir contagens.')


def main():
    parser = argparse.ArgumentParser(description='Importar XMLs no OJS')
    parser.add_argument('--env', choices=['test', 'prod'], default='test')
    parser.add_argument('--slug', help='Importar apenas este seminário')
    parser.add_argument('--cleanup', action='store_true', help='Só limpar duplicatas')
    parser.add_argument('--verify', action='store_true', help='Verificar estado')
    parser.add_argument('--xml-dir', help='Diretório dos XMLs (default: xml_test/)')
    parser.add_argument('--dry-run', action='store_true', help='Apenas listar')
    parser.add_argument('--per-article', action='store_true',
                       help='Modo per-article: 1 XML por artigo (com PDF embutido)')
    parser.add_argument('--upload-galleys', action='store_true',
                       help='Upload PDFs de edição completa como issue galleys')
    args = parser.parse_args()

    env = ENVS[args.env]
    xml_dir = args.xml_dir or os.path.join(BASE_DIR, 'xml_test')

    # Contagens esperadas do banco
    db_path = os.path.join(BASE_DIR, 'anais.db')
    expected = get_expected_counts(db_path) if os.path.exists(db_path) else {}

    print(f'Ambiente: {args.env} ({env["url"]})')
    print()

    if args.dry_run:
        files = sorted(glob.glob(os.path.join(xml_dir, '*.xml')))
        files = [f for f in files if not os.path.basename(f).startswith('sdbr')]
        if args.per_article and args.slug:
            files = [f for f in files if os.path.basename(f).startswith(args.slug)]
        print(f'Dry-run — {len(files)} XMLs:')
        for f in files:
            name = os.path.basename(f).replace('.xml', '')
            size = os.path.getsize(f)
            print(f'  {name}: {size:,} bytes')
        return

    if args.verify:
        cmd_verify(env, expected)
        return

    if args.cleanup:
        cmd_cleanup(env, expected)
        return

    if args.upload_galleys:
        cmd_upload_galleys(env, args.slug)
        return

    if args.per_article:
        cmd_import_per_article(env, expected, xml_dir, args.slug)
    else:
        cmd_import(env, expected, xml_dir, args.slug)


if __name__ == '__main__':
    main()
