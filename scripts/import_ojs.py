#!/usr/bin/env python3
"""
Importa XMLs no OJS via Native XML Plugin.

Modos de operação:
  --import   Importa XMLs faltantes (sessão fresca por XML)
  --cleanup  Limpa issues duplicadas/vazias/parciais
  --verify   Verifica estado atual (lista issues e contagens)
  --dry-run  Apenas lista XMLs sem conectar

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


def main():
    parser = argparse.ArgumentParser(description='Importar XMLs no OJS')
    parser.add_argument('--env', choices=['test', 'prod'], default='test')
    parser.add_argument('--slug', help='Importar apenas este seminário')
    parser.add_argument('--cleanup', action='store_true', help='Só limpar duplicatas')
    parser.add_argument('--verify', action='store_true', help='Verificar estado')
    parser.add_argument('--xml-dir', help='Diretório dos XMLs (default: xml_test/)')
    parser.add_argument('--dry-run', action='store_true', help='Apenas listar')
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
        print(f'Dry-run — {len(files)} XMLs:')
        for f in files:
            slug = os.path.basename(f).replace('.xml', '')
            size = os.path.getsize(f)
            exp = expected.get(slug, '?')
            print(f'  {slug}: {size:,} bytes, {exp} artigos esperados')
        return

    if args.verify:
        cmd_verify(env, expected)
        return

    if args.cleanup:
        cmd_cleanup(env, expected)
        return

    cmd_import(env, expected, xml_dir, args.slug)


if __name__ == '__main__':
    main()
