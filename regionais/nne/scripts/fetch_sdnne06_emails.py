#!/usr/bin/env python3
"""
Fetch sdnne06 articles from Outlook email (docomomonnetrabalhos@hotmail.com).

Uses Chrome session cookies via browser_cookie3 to authenticate,
then navigates Outlook Web via Playwright to list emails and download attachments.

DOM strategy:
- Email list items: aria-label contains sender, subject, date, attachment info
- Opened email headings: IDs ending in _SUBJECT, _FROM, _DATETIME, _ATTACHMENTS
"""

import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

FONTES_DIR = Path(__file__).resolve().parent.parent / "sdnne06" / "fontes"
EMAILS_DIR = FONTES_DIR / "emails"
ATTACH_DIR = FONTES_DIR / "attachments"
EMAILS_DIR.mkdir(parents=True, exist_ok=True)
ATTACH_DIR.mkdir(parents=True, exist_ok=True)


def get_chrome_cookies():
    """Extract Chrome session cookies for Outlook/Hotmail domains."""
    import browser_cookie3
    domains = ['.live.com', '.login.live.com', 'outlook.live.com',
               '.microsoft.com', '.login.microsoftonline.com']
    all_cookies = []
    seen = set()
    for domain in domains:
        try:
            cj = browser_cookie3.chrome(domain_name=domain)
            for c in cj:
                key = (c.domain, c.name, c.path)
                if key not in seen:
                    seen.add(key)
                    cookie = {'name': c.name, 'value': c.value, 'domain': c.domain,
                              'path': c.path, 'secure': bool(c.secure), 'httpOnly': False}
                    if c.expires and c.expires > 0:
                        cookie['expires'] = float(c.expires)
                    all_cookies.append(cookie)
        except:
            pass
    print(f"Extracted {len(all_cookies)} cookies from Chrome")
    return all_cookies


def parse_aria_label(label):
    """Parse the aria-label of an email list item into components."""
    info = {
        'has_attachment': False,
        'is_replied': False,
        'is_collapsed': False,
        'raw_label': label
    }

    text = label

    # Remove prefixes
    if text.startswith('Recolhido '):
        info['is_collapsed'] = True
        text = text[len('Recolhido '):]
    if text.startswith('Tem anexos '):
        info['has_attachment'] = True
        text = text[len('Tem anexos '):]
    if text.startswith('Respondida '):
        info['is_replied'] = True
        text = text[len('Respondida '):]
    if text.startswith('Tem anexos '):
        info['has_attachment'] = True
        text = text[len('Tem anexos '):]
    if text.startswith('Respondida '):
        info['is_replied'] = True
        text = text[len('Respondida '):]

    # Try to extract date (dd/mm/yyyy pattern)
    date_match = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', text)
    if date_match:
        info['date'] = date_match.group(1)
        # Split at date: before = sender + subject, after = preview
        before = text[:date_match.start()].strip()
        after = text[date_match.end():].strip()
        info['preview'] = after[:300] if after else ''

        # In "before", the sender name comes first, then the subject
        # But they're concatenated without clear delimiter
        info['sender_and_subject'] = before
    else:
        info['sender_and_subject'] = text

    return info


def extract_email_detail(page):
    """Extract detailed info from the currently opened email in the reading pane."""
    detail = {}

    result = page.evaluate("""() => {
        const data = {};

        // Get all headings with specific ID patterns
        const headings = document.querySelectorAll('[id*="_SUBJECT"], [id*="_FROM"], [id*="_DATETIME"], [id*="_ATTACHMENTS"], [id*="_TO"]');
        for (const h of headings) {
            const id = h.id;
            const text = h.innerText || '';
            if (id.includes('_SUBJECT')) {
                if (!data.subjects) data.subjects = [];
                data.subjects.push(text.trim());
            } else if (id.includes('_FROM')) {
                if (!data.froms) data.froms = [];
                data.froms.push(text.trim());
            } else if (id.includes('_DATETIME')) {
                if (!data.dates) data.dates = [];
                data.dates.push(text.trim());
            } else if (id.includes('_ATTACHMENTS')) {
                if (!data.attachments) data.attachments = [];
                data.attachments.push(text.trim());
            }
        }

        // Get message body
        const bodyEl = document.querySelector('[id*="_BODY"]') ||
                       document.querySelector('.allowTextSelection [dir="ltr"]') ||
                       document.querySelector('.allowTextSelection [dir="rtl"]');
        if (bodyEl) {
            data.body = bodyEl.innerText?.substring(0, 2000) || '';
        }

        // Get conversation subject from CONV heading
        const convSubject = document.querySelector('[id^="CONV_"][id$="_SUBJECT"]');
        if (convSubject) {
            data.conversation_subject = convSubject.innerText?.trim() || '';
        }

        return data;
    }""")

    return result


def download_attachments(page, email_index, folder_name):
    """Try to download attachments from the currently opened email."""
    downloaded = []

    try:
        # Look for attachment links with aria-labels containing file info
        att_links = page.evaluate("""() => {
            const links = [];
            document.querySelectorAll('[aria-label]').forEach(el => {
                const label = el.getAttribute('aria-label') || '';
                if (label.match(/\\.(doc|docx|pdf|ppt|pptx|odt|rtf|txt|zip|rar)/i) &&
                    label.includes('Abrir')) {
                    links.push({
                        label: label,
                        href: el.href || '',
                        tagName: el.tagName
                    });
                }
            });
            return links;
        }""")

        if att_links:
            for att in att_links:
                # Extract filename from aria-label (e.g., "COCM.16.CAMILLA.doc Abrir 3 MB")
                label = att['label']
                name_match = re.match(r'^(.+?)\s+Abrir\s+', label)
                if name_match:
                    filename = name_match.group(1).strip()
                    downloaded.append({
                        'filename': filename,
                        'label': label,
                        'downloaded': False  # Will download in Phase 2
                    })

    except Exception as e:
        print(f"    Error checking attachments: {e}")

    return downloaded


def process_folder(page, folder_name):
    """Navigate to a folder and extract all email details."""
    emails = []

    # Click on folder
    folder_el = page.locator(f'[data-folder-name="{folder_name}"]').first
    if folder_el.count() == 0:
        print(f"  Folder '{folder_name}' not found")
        return []

    folder_el.click()
    time.sleep(4)

    # Get all items and their aria-labels
    items = page.locator('[role="option"]').all()
    count = len(items)
    print(f"  {count} items in '{folder_name}'")

    if count == 0:
        return []

    for i in range(count):
        try:
            # Re-query items (DOM changes after clicks)
            items = page.locator('[role="option"]').all()
            if i >= len(items):
                break

            item = items[i]

            # Get aria-label from list item
            aria = item.get_attribute('aria-label') or ''
            parsed = parse_aria_label(aria)
            parsed['index'] = i
            parsed['folder'] = folder_name

            # Click to open in reading pane
            item.click()
            time.sleep(2)

            # Extract detailed info from reading pane
            detail = extract_email_detail(page)
            parsed['detail'] = detail

            # Check for attachments
            att_info = download_attachments(page, i, folder_name)
            if att_info:
                parsed['attachment_files'] = att_info

            # Build summary line
            subj = ''
            if detail.get('conversation_subject'):
                subj = detail['conversation_subject']
            elif detail.get('subjects') and detail['subjects'][0]:
                subj = detail['subjects'][0]
            else:
                subj = parsed.get('sender_and_subject', '?')

            sender = ''
            if detail.get('froms'):
                sender = detail['froms'][0]

            date = parsed.get('date', '')
            att_flag = ' [ATT]' if parsed.get('has_attachment') or att_info else ''
            att_list = ', '.join(a['filename'] for a in att_info) if att_info else ''

            print(f"    {i+1}. {subj[:60]} | {sender[:40]} | {date}{att_flag}")
            if att_list:
                print(f"       Attachments: {att_list}")

            emails.append(parsed)

        except Exception as e:
            print(f"    Error on email {i}: {e}")
            emails.append({'index': i, 'folder': folder_name, 'error': str(e)})

    return emails


def main():
    print("=" * 70)
    print("Fetching sdnne06 emails from Outlook")
    print("=" * 70)

    # Step 1: Get Chrome cookies
    print("\n--- Step 1: Extracting Chrome cookies ---")
    cookies = get_chrome_cookies()
    if not cookies:
        print("ERROR: No cookies extracted")
        sys.exit(1)

    # Step 2: Launch Playwright
    print("\n--- Step 2: Launching Playwright ---")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
        )
        context.add_cookies(cookies)
        page = context.new_page()

        try:
            # Navigate to inbox
            print("\n--- Step 3: Navigating to Outlook ---")
            page.goto('https://outlook.live.com/mail/0/inbox')
            time.sleep(8)

            if 'login' in page.url.lower() or 'signin' in page.url.lower():
                print("ERROR: Not logged in!")
                browser.close()
                sys.exit(1)

            print(f"Logged in. URL: {page.url}")

            # Process each folder
            folders = [
                'artigos completos',
                'alagoas', 'amazonas', 'bahia', 'ceará',
                'maranhão', 'paraíba', 'pernambuco', 'piauí',
                'pará', 'rio grande do norte', 'sergipe', 'tocantins',
                'emails docojovem', 'emails docomomo para confirmar'
            ]

            all_emails = []
            for folder_name in folders:
                print(f"\n{'='*50}")
                print(f"Folder: {folder_name}")
                print(f"{'='*50}")

                try:
                    folder_emails = process_folder(page, folder_name)
                    all_emails.extend(folder_emails)
                except Exception as e:
                    print(f"  ERROR: {e}")
                    traceback.print_exc()

            # Save results
            results_path = EMAILS_DIR / "email_listing_detailed.json"
            with open(results_path, 'w') as f:
                json.dump(all_emails, f, indent=2, ensure_ascii=False)

            # Print summary
            print(f"\n{'='*70}")
            print(f"SUMMARY")
            print(f"{'='*70}")
            print(f"Total emails: {len(all_emails)}")

            by_folder = {}
            for e in all_emails:
                f = e.get('folder', '?')
                by_folder.setdefault(f, []).append(e)

            total_attachments = 0
            for folder, emails in by_folder.items():
                att_count = sum(1 for e in emails if e.get('has_attachment') or e.get('attachment_files'))
                total_attachments += att_count
                print(f"\n  {folder}: {len(emails)} emails ({att_count} with attachments)")

            print(f"\nTotal emails with attachments: {total_attachments}")

            # List all unique attachment filenames
            all_files = []
            for e in all_emails:
                for att in e.get('attachment_files', []):
                    all_files.append({
                        'filename': att['filename'],
                        'folder': e.get('folder', '?'),
                        'date': e.get('date', '?')
                    })

            if all_files:
                print(f"\nAll attachment files ({len(all_files)}):")
                for af in all_files:
                    print(f"  {af['filename']} ({af['folder']})")

        except Exception as e:
            print(f"\nFATAL ERROR: {e}")
            traceback.print_exc()
        finally:
            browser.close()

    print("\n--- Done ---")


if __name__ == '__main__':
    main()
