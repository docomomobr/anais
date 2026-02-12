#!/usr/bin/env python3
"""
Split large OJS Native XML files into smaller batches of N articles each.

Each batch keeps the full issue wrapper (id, description, issue_identification,
date_published, last_modified, sections) and contains only a subset of articles.

Uses regex-based string splitting (NOT ElementTree) to preserve the exact XML
formatting and namespace declarations of the original files. This is critical
because OJS's parser expects xmlns:xsi on <article> and <publication> elements.

Usage:
    python3 scripts/split_xml_batches.py [--batch-size N] [--slugs slug1,slug2,...]
"""

import argparse
import math
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XML_DIR = os.path.join(BASE_DIR, 'xml_test')
OUT_DIR = os.path.join(XML_DIR, 'split')

# Only regional seminars — NEVER nationals
TARGET_SLUGS = [
    'sdnne07', 'sdnne08',
    'sdsp08', 'sdsp09',
    'sdsul02', 'sdsul03', 'sdsul05', 'sdsul06',
]


def split_xml(xml_path, slug, batch_size, out_dir):
    """Split a single XML file into batches using string manipulation."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the <articles> block
    articles_start = content.find('<articles>')
    articles_end = content.find('</articles>')
    if articles_start == -1 or articles_end == -1:
        print(f"  WARNING: No <articles> block found in {slug}.xml, skipping")
        return 0, []

    # Extract parts
    header = content[:articles_start]  # Everything before <articles>
    footer = content[articles_end + len('</articles>'):]  # Everything after </articles>
    articles_block = content[articles_start + len('<articles>'):articles_end]

    # Split individual articles using regex
    # Each article starts with <article and ends with </article>
    # Use a regex that captures each complete <article>...</article> block
    article_pattern = re.compile(
        r'(\s*<article\b.*?</article>)',
        re.DOTALL
    )
    articles = article_pattern.findall(articles_block)
    total = len(articles)

    if total == 0:
        print(f"  WARNING: No articles found in {slug}.xml, skipping")
        return 0, []

    num_batches = math.ceil(total / batch_size)
    print(f"  {slug}: {total} articles -> {num_batches} batches of max {batch_size}")

    batch_info = []

    for batch_idx in range(num_batches):
        start = batch_idx * batch_size
        end = min(start + batch_size, total)
        batch_articles = articles[start:end]

        # Reconstruct the XML
        batch_content = header + '<articles>'
        for article in batch_articles:
            batch_content += article
        batch_content += '\n  </articles>'
        batch_content += footer

        # Build output filename
        batch_num = batch_idx + 1
        filename = f"{slug}_batch{batch_num:02d}.xml"
        out_path = os.path.join(out_dir, filename)

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)

        batch_info.append((filename, len(batch_articles)))
        print(f"    {filename}: {len(batch_articles)} articles")

    return num_batches, batch_info


def main():
    parser = argparse.ArgumentParser(description='Split OJS Native XML into batches')
    parser.add_argument('--batch-size', type=int, default=5,
                        help='Max articles per batch (default: 5)')
    parser.add_argument('--slugs', type=str, default=None,
                        help='Comma-separated list of slugs to process (default: all 8)')
    parser.add_argument('--outdir', type=str, default=OUT_DIR,
                        help='Output directory for batch files')
    args = parser.parse_args()

    slugs = args.slugs.split(',') if args.slugs else TARGET_SLUGS

    # Safety check: never process nationals
    for slug in slugs:
        if slug.startswith('sdbr'):
            print(f"ERROR: Refusing to process national seminar {slug}")
            sys.exit(1)

    # Create output directory
    os.makedirs(args.outdir, exist_ok=True)

    print(f"Splitting XMLs into batches of {args.batch_size} articles")
    print(f"Input:  {XML_DIR}")
    print(f"Output: {args.outdir}")
    print()

    total_batches = 0
    total_articles = 0
    summary = []

    for slug in sorted(slugs):
        xml_path = os.path.join(XML_DIR, f'{slug}.xml')
        if not os.path.exists(xml_path):
            print(f"  WARNING: {xml_path} not found, skipping")
            continue

        num_batches, batch_info = split_xml(xml_path, slug, args.batch_size, args.outdir)
        total_batches += num_batches
        articles_in_slug = sum(count for _, count in batch_info)
        total_articles += articles_in_slug
        summary.append((slug, articles_in_slug, num_batches, batch_info))

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Slug':<12} {'Articles':>8} {'Batches':>8}")
    print("-" * 32)
    for slug, arts, batches, _ in summary:
        print(f"{slug:<12} {arts:>8} {batches:>8}")
    print("-" * 32)
    print(f"{'TOTAL':<12} {total_articles:>8} {total_batches:>8}")
    print()
    print(f"Generated {total_batches} batch files in {args.outdir}")


if __name__ == '__main__':
    main()
