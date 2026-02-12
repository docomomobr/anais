#!/usr/bin/env python3
"""
Import split XML batches into OJS test server.

Imports batches for the 8 remaining regional seminars. Each seminar's articles
were split into batches of 5 to work around server timeout/WAF issues.

Usage:
    python3 scripts/import_batches.py --test-one sdsul06       # test 1 batch
    python3 scripts/import_batches.py --slug sdsul06            # all batches for one
    python3 scripts/import_batches.py --all                     # all 8 seminars
    python3 scripts/import_batches.py --verify                  # check state
    python3 scripts/import_batches.py --cleanup-slug sdsul06    # wipe one issue

Rules:
- NEVER import nationals (sdbr*)
- Fresh session for each batch
- 30-second delay between batches
- Stop on any failure
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
SPLIT_DIR = os.path.join(BASE_DIR, 'xml_test', 'split')

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

BATCH_DELAY = 30  # seconds between batches
SEMINAR_DELAY = 60  # seconds between seminars

# Only regional seminars
TARGET_SLUGS = [
    'sdnne07', 'sdnne08',
    'sdsp08', 'sdsp09',
    'sdsul02', 'sdsul03', 'sdsul05', 'sdsul06',
]


def fresh_session(base_url, username, password):
    """Create fresh session, login, return (session, csrf_token)."""
    s = requests.Session()
    resp = s.post(
        f'{base_url}/login/signIn',
        data={'username': username, 'password': password},
        allow_redirects=True, timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f'Login failed: HTTP {resp.status_code}')

    resp = s.get(
        f'{base_url}/management/importexport/plugin/NativeImportExportPlugin',
        timeout=30,
    )
    match = re.search(r'"csrfToken":"([^"]+)"', resp.text)
    if not match:
        raise RuntimeError('Could not get CSRF token')
    return s, match.group(1)


def upload_and_import(base_url, session, csrf, filepath):
    """Upload + import one XML. Returns (success, message)."""
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
        return False, f'upload HTTP {resp.status_code}'
    match = re.search(r'"temporaryFileId":"?(\d+)', resp.text)
    if not match:
        return False, f'no temporaryFileId: {resp.text[:200]}'
    temp_id = match.group(1)

    # 2. importBounce
    session.post(
        f'{base_url}/management/importexport/plugin/'
        'NativeImportExportPlugin/importBounce',
        data={'csrfToken': csrf, 'temporaryFileId': temp_id},
        timeout=30,
    )

    # 3. Execute import
    try:
        resp = session.get(
            f'{base_url}/management/importexport/plugin/'
            'NativeImportExportPlugin/import',
            params={'temporaryFileId': temp_id, 'csrfToken': csrf},
            timeout=600,
        )
        text = resp.text
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False, 'timeout/connection lost'

    if not text:
        return False, 'empty response'
    if 'xito' in text:
        return True, 'OK'
    errors = re.findall(r'<li>([^<]+)</li>', text)
    if errors:
        return False, '; '.join(e.strip()[:120] for e in errors[:5])
    return False, f'unknown response: {text[:300]}'


def load_all_issues(base_url, session):
    """Load all issues. Returns list of {id, slug}."""
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


def count_issue_articles(base_url, session, issue_id):
    """Count articles in an issue. Returns -1 on error."""
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


def get_issue_submission_ids(base_url, session, issue_id):
    """Return list of submission IDs for an issue."""
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
    """Unpublish and delete a submission."""
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
    """Delete an issue (must be empty)."""
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
    """Delete all articles in an issue and then the issue itself."""
    sub_ids = get_issue_submission_ids(base_url, session, issue_id)
    if sub_ids:
        print(f'    Deleting {len(sub_ids)} articles from issue {issue_id} ({slug})...')
        for sub_id in sub_ids:
            delete_submission(base_url, session, csrf, sub_id)
            time.sleep(1)
    if delete_issue(base_url, session, csrf, issue_id):
        print(f'    Issue {issue_id} ({slug}) deleted')
        return True
    else:
        print(f'    WARNING: could not delete issue {issue_id} ({slug})')
        return False


def get_expected_counts(db_path):
    """Read expected article counts per seminar."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT seminar_slug, COUNT(*) FROM articles "
        "WHERE seminar_slug NOT LIKE 'sdbr%' GROUP BY seminar_slug"
    ).fetchall()
    conn.close()
    return dict(rows)


def get_batch_files(slug):
    """Get sorted list of batch files for a slug."""
    pattern = os.path.join(SPLIT_DIR, f'{slug}_batch*.xml')
    return sorted(glob.glob(pattern))


def import_batches_for_slug(env, slug, expected_count):
    """Import all batches for one seminar. Returns (success, articles_imported)."""
    base = env['url']
    batches = get_batch_files(slug)
    if not batches:
        print(f'  No batch files found for {slug}')
        return False, 0

    print(f'\n{"="*60}')
    print(f'{slug}: {len(batches)} batches, expected {expected_count} articles')
    print(f'{"="*60}')

    for i, batch_file in enumerate(batches, 1):
        batch_name = os.path.basename(batch_file)
        size = os.path.getsize(batch_file)

        print(f'\n  [{i}/{len(batches)}] {batch_name} ({size:,} bytes)')

        # Fresh session for each batch
        try:
            s, csrf = fresh_session(base, env['username'], env['password'])
        except Exception as e:
            print(f'    LOGIN FAILED: {e}')
            return False, 0

        print(f'    Session OK, CSRF: {csrf[:16]}...')

        # Upload + import
        try:
            ok, msg = upload_and_import(base, s, csrf, batch_file)
        except Exception as e:
            print(f'    EXCEPTION: {e}')
            ok, msg = False, str(e)

        if ok:
            print(f'    OK')
        else:
            print(f'    FAILED: {msg}')

            # If empty response, wait and check if articles were actually imported
            if 'empty' in msg or 'timeout' in msg or 'vazia' in msg:
                print(f'    Waiting 90s to check if server processed it anyway...')
                time.sleep(90)
                try:
                    s2, csrf2 = fresh_session(base, env['username'], env['password'])
                    issues = load_all_issues(base, s2)
                    slug_issues = [iss for iss in issues if iss['slug'] == slug]
                    if slug_issues:
                        count = count_issue_articles(base, s2, slug_issues[0]['id'])
                        print(f'    Server has {count} articles for {slug}')
                        if count > 0 and i == 1:
                            # First batch seems to have worked despite empty response
                            print(f'    Continuing with next batch...')
                            del s2
                            if i < len(batches):
                                print(f'    Waiting {BATCH_DELAY}s...')
                                time.sleep(BATCH_DELAY)
                            continue
                    del s2
                except Exception:
                    pass

            print(f'    STOPPING. Clean up may be needed.')
            return False, 0

        # Delay between batches
        if i < len(batches):
            print(f'    Waiting {BATCH_DELAY}s...')
            time.sleep(BATCH_DELAY)

    # Verify final count
    print(f'\n  Verifying {slug}...')
    time.sleep(10)
    try:
        s, csrf = fresh_session(base, env['username'], env['password'])
        issues = load_all_issues(base, s)
        slug_issues = [iss for iss in issues if iss['slug'] == slug]
        if slug_issues:
            count = count_issue_articles(base, s, slug_issues[0]['id'])
            print(f'  {slug}: {count} articles (expected {expected_count})')
            if count >= expected_count:
                print(f'  SUCCESS!')
                return True, count
            else:
                print(f'  PARTIAL: only {count}/{expected_count}')
                return False, count
        else:
            print(f'  Issue not found after import!')
            return False, 0
    except Exception as e:
        print(f'  Verification error: {e}')
        return False, -1


def cmd_test_one(env, slug, expected):
    """Test by importing just 1 batch for a slug."""
    base = env['url']
    batches = get_batch_files(slug)
    if not batches:
        print(f'No batch files found for {slug}')
        return

    batch_file = batches[0]
    batch_name = os.path.basename(batch_file)
    size = os.path.getsize(batch_file)

    print(f'Test import: {batch_name} ({size:,} bytes)')

    try:
        s, csrf = fresh_session(base, env['username'], env['password'])
    except Exception as e:
        print(f'LOGIN FAILED: {e}')
        return

    print(f'Session OK, CSRF: {csrf[:16]}...')

    try:
        ok, msg = upload_and_import(base, s, csrf, batch_file)
    except Exception as e:
        print(f'EXCEPTION: {e}')
        return

    if ok:
        print(f'SUCCESS! Batch imported.')
    else:
        print(f'FAILED: {msg}')
        if 'empty' in msg or 'timeout' in msg or 'vazia' in msg:
            print(f'Waiting 90s to check...')
            time.sleep(90)
            try:
                s2, _ = fresh_session(base, env['username'], env['password'])
                issues = load_all_issues(base, s2)
                slug_issues = [iss for iss in issues if iss['slug'] == slug]
                if slug_issues:
                    count = count_issue_articles(base, s2, slug_issues[0]['id'])
                    print(f'Server has {count} articles for {slug}')
                else:
                    print(f'No issue found for {slug}')
            except Exception as e2:
                print(f'Check failed: {e2}')

    # Verify
    time.sleep(5)
    try:
        s2, _ = fresh_session(base, env['username'], env['password'])
        issues = load_all_issues(base, s2)
        slug_issues = [iss for iss in issues if iss['slug'] == slug]
        if slug_issues:
            count = count_issue_articles(base, s2, slug_issues[0]['id'])
            exp = expected.get(slug, '?')
            print(f'\nResult: {slug} has {count} articles (expected total: {exp})')
        else:
            print(f'\nNo issue created for {slug}')
    except Exception:
        pass


def cmd_import_slug(env, slug, expected):
    """Import all batches for one seminar."""
    exp_count = expected.get(slug, 0)
    ok, count = import_batches_for_slug(env, slug, exp_count)
    if ok:
        print(f'\n{slug} fully imported: {count} articles')
    else:
        print(f'\n{slug} INCOMPLETE. Check server state with --verify.')


def cmd_import_all(env, expected):
    """Import all 8 remaining seminars."""
    # Check which ones are already done
    base = env['url']
    print('Checking existing issues...')
    s, _ = fresh_session(base, env['username'], env['password'])
    existing = load_all_issues(base, s)
    existing_slugs = {iss['slug'] for iss in existing}
    del s

    to_import = [slug for slug in TARGET_SLUGS if slug not in existing_slugs]
    if not to_import:
        print('All 8 seminars already have issues on the server.')
        return

    # Sort smallest first (to import quickly and detect problems early)
    to_import.sort(key=lambda s: expected.get(s, 999))

    print(f'\n{len(to_import)} seminars to import:')
    for slug in to_import:
        batches = get_batch_files(slug)
        print(f'  {slug}: {expected.get(slug, "?")} articles, {len(batches)} batches')

    results = {}
    for i, slug in enumerate(to_import, 1):
        exp_count = expected.get(slug, 0)
        print(f'\n\n[SEMINAR {i}/{len(to_import)}]')
        ok, count = import_batches_for_slug(env, slug, exp_count)
        results[slug] = (ok, count)

        if not ok:
            print(f'\n*** STOPPING: {slug} failed ***')
            break

        if i < len(to_import):
            print(f'\nWaiting {SEMINAR_DELAY}s before next seminar...')
            time.sleep(SEMINAR_DELAY)

    # Summary
    print(f'\n\n{"="*60}')
    print(f'SUMMARY')
    print(f'{"="*60}')
    for slug, (ok, count) in results.items():
        exp = expected.get(slug, '?')
        status = 'OK' if ok else 'FAILED'
        print(f'  {slug}: {count}/{exp} articles [{status}]')


def cmd_cleanup_slug(env, slug, expected):
    """Wipe an issue for a specific slug."""
    base = env['url']
    print(f'Cleaning up {slug}...')
    s, csrf = fresh_session(base, env['username'], env['password'])
    issues = load_all_issues(base, s)
    slug_issues = [iss for iss in issues if iss['slug'] == slug]
    if not slug_issues:
        print(f'  No issue found for {slug}')
        return
    for iss in slug_issues:
        count = count_issue_articles(base, s, iss['id'])
        print(f'  Issue {iss["id"]}: {count} articles')
        wipe_issue(base, s, csrf, iss['id'], slug)
        time.sleep(2)
        # May need fresh session after heavy deletions
        s, csrf = fresh_session(base, env['username'], env['password'])


def main():
    parser = argparse.ArgumentParser(description='Import split XML batches into OJS')
    parser.add_argument('--env', choices=['test', 'prod'], default='test')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--test-one', metavar='SLUG',
                       help='Test import of just 1 batch for a slug')
    group.add_argument('--slug', metavar='SLUG',
                       help='Import all batches for one seminar')
    group.add_argument('--all', action='store_true',
                       help='Import all 8 remaining seminars')
    group.add_argument('--verify', action='store_true',
                       help='Verify current server state')
    group.add_argument('--cleanup-slug', metavar='SLUG',
                       help='Wipe issue for a specific slug')
    args = parser.parse_args()

    # Safety check
    for attr in ['test_one', 'slug', 'cleanup_slug']:
        val = getattr(args, attr, None)
        if val and val.startswith('sdbr'):
            print(f'ERROR: Refusing to process national seminar {val}')
            sys.exit(1)

    env = ENVS[args.env]

    # Expected counts from database
    db_path = os.path.join(BASE_DIR, 'anais.db')
    expected = get_expected_counts(db_path) if os.path.exists(db_path) else {}

    print(f'Environment: {args.env} ({env["url"]})')
    print()

    if args.verify:
        # Reuse the verify from import_ojs.py logic
        print('Login...')
        s, csrf = fresh_session(env['url'], env['username'], env['password'])
        print('Loading issues...')
        all_issues = load_all_issues(env['url'], s)
        print(f'{len(all_issues)} issues found\n')

        from collections import defaultdict
        by_slug = defaultdict(list)
        for iss in all_issues:
            by_slug[iss['slug']].append(iss['id'])

        for slug, ids in sorted(by_slug.items()):
            exp = expected.get(slug, '?')
            for issue_id in ids:
                count = count_issue_articles(env['url'], s, issue_id)
                status = ''
                if isinstance(exp, int):
                    if count >= exp:
                        status = ' OK'
                    elif count == 0:
                        status = ' EMPTY'
                    else:
                        status = f' PARTIAL ({count}/{exp})'
                print(f'  {slug}: issue {issue_id}, {count} arts (expected: {exp}){status}')
                time.sleep(1)

        missing = set(expected.keys()) - set(by_slug.keys())
        regional_missing = [s for s in sorted(missing) if not s.startswith('sdbr')]
        if regional_missing:
            print(f'\nMissing ({len(regional_missing)}):')
            for slug in regional_missing:
                print(f'  {slug} ({expected[slug]} articles)')
        return

    if args.test_one:
        cmd_test_one(env, args.test_one, expected)
    elif args.slug:
        cmd_import_slug(env, args.slug, expected)
    elif args.all:
        cmd_import_all(env, expected)
    elif args.cleanup_slug:
        cmd_cleanup_slug(env, args.cleanup_slug, expected)


if __name__ == '__main__':
    main()
