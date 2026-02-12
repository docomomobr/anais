#!/usr/bin/env python3
"""Cria o banco anais.db com o schema completo."""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'anais.db')

SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS seminars (
    slug TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    subtitle TEXT,
    year INTEGER NOT NULL,
    volume INTEGER,
    number INTEGER,
    date_published TEXT,
    isbn TEXT,
    doi TEXT,
    description TEXT,
    location TEXT,
    publisher TEXT,
    source TEXT,
    editors TEXT
);

CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seminar_slug TEXT NOT NULL REFERENCES seminars(slug),
    title TEXT NOT NULL,
    abbrev TEXT,
    seq INTEGER DEFAULT 0,
    hide_title INTEGER DEFAULT 0,
    UNIQUE(seminar_slug, title)
);

CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    seminar_slug TEXT NOT NULL REFERENCES seminars(slug),
    section_id INTEGER REFERENCES sections(id),
    title TEXT NOT NULL,
    subtitle TEXT,
    locale TEXT DEFAULT 'pt-BR',
    pages TEXT,
    pages_count INTEGER,
    file TEXT,
    abstract TEXT,
    abstract_en TEXT,
    abstract_es TEXT,
    keywords TEXT,
    keywords_en TEXT,
    keywords_es TEXT,
    references_ TEXT,
    ojs_id TEXT,
    doi TEXT
);

CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    givenname TEXT NOT NULL,
    familyname TEXT NOT NULL,
    email TEXT,
    orcid TEXT,
    UNIQUE(givenname, familyname)
);

CREATE TABLE IF NOT EXISTS author_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL REFERENCES authors(id),
    givenname TEXT NOT NULL,
    familyname TEXT NOT NULL,
    source TEXT,
    UNIQUE(givenname, familyname)
);

CREATE TABLE IF NOT EXISTS article_author (
    article_id TEXT NOT NULL REFERENCES articles(id),
    author_id INTEGER NOT NULL REFERENCES authors(id),
    seq INTEGER DEFAULT 0,
    primary_contact INTEGER DEFAULT 0,
    affiliation TEXT,
    bio TEXT,
    country TEXT DEFAULT 'BR',
    PRIMARY KEY (article_id, author_id)
);

CREATE INDEX IF NOT EXISTS idx_articles_seminar ON articles(seminar_slug);
CREATE INDEX IF NOT EXISTS idx_articles_section ON articles(section_id);
CREATE INDEX IF NOT EXISTS idx_sections_seminar ON sections(seminar_slug);
CREATE INDEX IF NOT EXISTS idx_article_author_author ON article_author(author_id);
CREATE INDEX IF NOT EXISTS idx_article_author_article ON article_author(article_id);
CREATE INDEX IF NOT EXISTS idx_author_variants_author ON author_variants(author_id);
CREATE INDEX IF NOT EXISTS idx_authors_familyname ON authors(familyname);
"""


def main():
    db_path = os.path.abspath(DB_PATH)
    if os.path.exists(db_path):
        print(f'Banco já existe: {db_path}')
        print('Apague manualmente para recriar.')
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.close()
    print(f'Banco criado: {db_path}')

    # Verificar tabelas
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print(f'Tabelas: {", ".join(tables)}')
    conn.close()


if __name__ == '__main__':
    main()
