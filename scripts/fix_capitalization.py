#!/usr/bin/env python3
"""Fix capitalization errors in titles and subtitles.

Applies fixes to anais.db and regional YAML files.
Only touches regional seminars (never sdbr*).
"""
import sqlite3
import glob
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, 'anais.db')

db = sqlite3.connect(DB)
cur = db.cursor()
total = 0

def fix(old, new):
    """Case-sensitive REPLACE on title and subtitle, only regionals."""
    global total
    for f in ('title', 'subtitle'):
        cur.execute(
            f"UPDATE articles SET {f} = REPLACE({f}, ?, ?) "
            f"WHERE {f} GLOB ? AND seminar_slug NOT LIKE 'sdbr%'",
            (old, new, f'*{old}*'))
        if cur.rowcount:
            total += cur.rowcount
            print(f"  {f}: '{old}' → '{new}' ({cur.rowcount})")


# ═══════════════════════════════════════════════════════════════
# Phase 1: Single-word proper nouns (always names, safe globally)
# Must run BEFORE acronyms (ibitinga before ibit)
# ═══════════════════════════════════════════════════════════════
print("── Phase 1: Person names ──")
for old, new in [
    ('niemeyer', 'Niemeyer'), ('severiano', 'Severiano'), ('delfim', 'Delfim'),
    ('premol', 'Premol'), ('neudson', 'Neudson'), ('svensson', 'Svensson'),
    ('palumbo', 'Palumbo'), ('lotufo', 'Lotufo'), ('chadler', 'Chadler'),
    ('bratke', 'Bratke'), ('fonyat', 'Fonyat'), ('christiano', 'Christiano'),
    ('guaspari', 'Guaspari'), ('duvivier', 'Duvivier'), ('palanti', 'Palanti'),
    ('stockler', 'Stockler'), ('cascaldi', 'Cascaldi'), ('toscano', 'Toscano'),
    ('nielsen', 'Nielsen'), ('pilon', 'Pilon'), ('rino', 'Rino'),
    ('nise', 'Nise'), ('lucio', 'Lucio'), ('vilanova', 'Vilanova'),
    ('artigas', 'Artigas'), ('gautherot', 'Gautherot'), ('koolhaas', 'Koolhaas'),
    ('giacomo', 'Giacomo'), ('odiléa', 'Odiléa'), ('waldemar', 'Waldemar'),
    ('tarsila', 'Tarsila'), ('porchat', 'Porchat'), ('capua', 'Capua'),
    ('félix', 'Félix'), ('eusébio', 'Eusébio'), ('athos', 'Athos'),
    ('bulcão', 'Bulcão'), ('marcel', 'Marcel'), ('sebastião', 'Sebastião'),
    ('tertuliano', 'Tertuliano'), ('dionísio', 'Dionísio'), ('zélia', 'Zélia'),
    ('joseísa', 'Joseísa'), ('manchete', 'Manchete'), ('palomo', 'Palomo'),
]:
    fix(old, new)

print("\n── Phase 1b: Place names ──")
for old, new in [
    ('luzimangues', 'Luzimangues'), ('santarém', 'Santarém'),
    ('birigui', 'Birigui'), ('promissão', 'Promissão'), ('barbalha', 'Barbalha'),
    ('ibitinga', 'Ibitinga'), ('hollywood', 'Hollywood'),
    ('guaianases', 'Guaianases'), ('guararapes', 'Guararapes'),
    ('mackenzie', 'Mackenzie'),
]:
    fix(old, new)


# ═══════════════════════════════════════════════════════════════
# Phase 2: Acronyms (after ibitinga fix to avoid ibit clash)
# ═══════════════════════════════════════════════════════════════
print("\n── Phase 2: Acronyms ──")
for old, new in [
    ('sqs', 'SQS'), ('efsc', 'EFSC'), ('ufam', 'UFAM'), ('ibit', 'IBIT'),
]:
    fix(old, new)
# JK (2 chars — use leading space for safety)
fix(' jk', ' JK')


# ═══════════════════════════════════════════════════════════════
# Phase 3: Multi-word phrases (context-sensitive words)
# Some words changed in phase 1, so patterns account for that
# ═══════════════════════════════════════════════════════════════
print("\n── Phase 3: Multi-word phrases ──")
for old, new in [
    # Short words that can't be single-word replaced
    ('Lina bo,', 'Lina Bo,'), ('Lina bo ', 'Lina Bo '),
    ('rem Koolhaas', 'Rem Koolhaas'),
    # Common words only capitalized in compound proper nouns
    ('Porto velho', 'Porto Velho'),
    ('Porto nacional', 'Porto Nacional'),
    ('Minas gerais', 'Minas Gerais'),
    ('agreste paraibano', 'Agreste Paraibano'),
    ('Agreste paraibano', 'Agreste Paraibano'),
    ('taques Bittencourt', 'Taques Bittencourt'),
    ('Delgado perez', 'Delgado Perez'),
    ('delgado perez', 'Delgado Perez'),
    ('La villette', 'La Villette'),
    ('Engenheiro dória', 'Engenheiro Dória'),
    ('engenheiro dória', 'Engenheiro Dória'),
    ('taba Guaianases', 'Taba Guaianases'),
    ('revista projeto', 'Revista Projeto'),
    ('Revista projeto', 'Revista Projeto'),
    ('lord hotel', 'Lord Hotel'),
    ('Lord hotel', 'Lord Hotel'),
    ('casa & Jardim', 'Casa & Jardim'),
]:
    fix(old, new)


# ═══════════════════════════════════════════════════════════════
# Phase 4: Institutional names (full phrases)
# ═══════════════════════════════════════════════════════════════
print("\n── Phase 4: Institutional names ──")
for old, new in [
    ('Centro administrativo', 'Centro Administrativo'),
    ('Primeira igreja', 'Primeira Igreja'),
    ('privê atlântico', 'Privê Atlântico'),
    ('Privê atlântico', 'Privê Atlântico'),
    ('praça do centenário', 'Praça do Centenário'),
    ('Praça do centenário', 'Praça do Centenário'),
    ('cemitério campo da esperança', 'Cemitério Campo da Esperança'),
    ('Cemitério campo da esperança', 'Cemitério Campo da Esperança'),
    ('Cemitério Campo da esperança', 'Cemitério Campo da Esperança'),
    ('secretaria da educação do estado do Tocantins',
     'Secretaria da Educação do Estado do Tocantins'),
    ('Secretaria da educação do estado do Tocantins',
     'Secretaria da Educação do Estado do Tocantins'),
    ('seminário regional do Nordeste', 'Seminário Regional do Nordeste'),
    ('Seminário regional do Nordeste', 'Seminário Regional do Nordeste'),
    ('parque histórico nacional dos Guararapes',
     'Parque Histórico Nacional dos Guararapes'),
    ('Parque histórico nacional dos Guararapes',
     'Parque Histórico Nacional dos Guararapes'),
    ('Parque Histórico nacional dos Guararapes',
     'Parque Histórico Nacional dos Guararapes'),
]:
    fix(old, new)


# ═══════════════════════════════════════════════════════════════
# Phase 5: Consolidated expressions (norma brasileira de capitalização)
# ═══════════════════════════════════════════════════════════════
print("\n── Phase 5: Consolidated expressions ──")
for old, new in [
    ('Moderna x contemporânea', 'Moderna x Contemporânea'),
    ('Moderna X contemporânea', 'Moderna X Contemporânea'),
    ('Arquitetura protomoderna', 'Arquitetura Protomoderna'),
    ('Arquitetura de interiores', 'Arquitetura de Interiores'),
]:
    fix(old, new)


# ═══════════════════════════════════════════════════════════════
# Phase 6: Subtitles starting with "Uma" → "uma"
# ═══════════════════════════════════════════════════════════════
print("\n── Phase 6: Subtitle 'Uma' → 'uma' ──")
cur.execute("""
    UPDATE articles SET subtitle = 'u' || SUBSTR(subtitle, 2)
    WHERE subtitle GLOB 'Uma *' AND seminar_slug NOT LIKE 'sdbr%'
""")
if cur.rowcount:
    total += cur.rowcount
    print(f"  subtitle: 'Uma ...' → 'uma ...' ({cur.rowcount})")


# Phase 7: removed — "cidade planejada" stays lowercase (not a proper noun)


# ═══════════════════════════════════════════════════════════════
# COMMIT & REPORT
# ═══════════════════════════════════════════════════════════════
db.commit()
db.close()

print(f"\n{'='*50}")
print(f"Total DB changes: {total}")


# ═══════════════════════════════════════════════════════════════
# Phase 8: Apply same fixes to regional YAML files
# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*50}")
print("Fixing YAML files...")

YAML_DIRS = [
    os.path.join(BASE, 'regionais', 'nne'),
    os.path.join(BASE, 'regionais', 'se'),
    os.path.join(BASE, 'regionais', 'sul'),
]

# Build the full list of (old, new) text replacements
ALL_REPLACEMENTS = [
    # Person names
    ('niemeyer', 'Niemeyer'), ('severiano', 'Severiano'), ('delfim', 'Delfim'),
    ('premol', 'Premol'), ('neudson', 'Neudson'), ('svensson', 'Svensson'),
    ('palumbo', 'Palumbo'), ('lotufo', 'Lotufo'), ('chadler', 'Chadler'),
    ('bratke', 'Bratke'), ('fonyat', 'Fonyat'), ('christiano', 'Christiano'),
    ('guaspari', 'Guaspari'), ('duvivier', 'Duvivier'), ('palanti', 'Palanti'),
    ('stockler', 'Stockler'), ('cascaldi', 'Cascaldi'), ('toscano', 'Toscano'),
    ('nielsen', 'Nielsen'), ('pilon', 'Pilon'), ('rino', 'Rino'),
    ('nise', 'Nise'), ('lucio', 'Lucio'), ('vilanova', 'Vilanova'),
    ('artigas', 'Artigas'), ('gautherot', 'Gautherot'), ('koolhaas', 'Koolhaas'),
    ('giacomo', 'Giacomo'), ('odiléa', 'Odiléa'), ('waldemar', 'Waldemar'),
    ('tarsila', 'Tarsila'), ('porchat', 'Porchat'), ('capua', 'Capua'),
    ('félix', 'Félix'), ('eusébio', 'Eusébio'), ('athos', 'Athos'),
    ('bulcão', 'Bulcão'), ('marcel', 'Marcel'), ('sebastião', 'Sebastião'),
    ('tertuliano', 'Tertuliano'), ('dionísio', 'Dionísio'), ('zélia', 'Zélia'),
    ('joseísa', 'Joseísa'), ('manchete', 'Manchete'), ('palomo', 'Palomo'),
    # Place names (ibitinga before ibit!)
    ('luzimangues', 'Luzimangues'), ('santarém', 'Santarém'),
    ('birigui', 'Birigui'), ('promissão', 'Promissão'), ('barbalha', 'Barbalha'),
    ('ibitinga', 'Ibitinga'), ('hollywood', 'Hollywood'),
    ('guaianases', 'Guaianases'), ('guararapes', 'Guararapes'),
    ('mackenzie', 'Mackenzie'),
    # Acronyms (ibit AFTER ibitinga)
    ('sqs', 'SQS'), ('efsc', 'EFSC'), ('ufam', 'UFAM'), ('ibit', 'IBIT'),
    (' jk', ' JK'),
    # Multi-word phrases
    ('Lina bo,', 'Lina Bo,'), ('Lina bo ', 'Lina Bo '),
    ('rem Koolhaas', 'Rem Koolhaas'),
    ('Porto velho', 'Porto Velho'), ('Porto nacional', 'Porto Nacional'),
    ('Minas gerais', 'Minas Gerais'),
    ('agreste paraibano', 'Agreste Paraibano'),
    ('Agreste paraibano', 'Agreste Paraibano'),
    ('taques Bittencourt', 'Taques Bittencourt'),
    ('Delgado perez', 'Delgado Perez'), ('delgado perez', 'Delgado Perez'),
    ('La villette', 'La Villette'),
    ('Engenheiro dória', 'Engenheiro Dória'),
    ('engenheiro dória', 'Engenheiro Dória'),
    ('taba Guaianases', 'Taba Guaianases'),
    ('revista projeto', 'Revista Projeto'), ('Revista projeto', 'Revista Projeto'),
    ('lord hotel', 'Lord Hotel'), ('Lord hotel', 'Lord Hotel'),
    ('casa & Jardim', 'Casa & Jardim'),
    # Institutional names
    ('Centro administrativo', 'Centro Administrativo'),
    ('Primeira igreja', 'Primeira Igreja'),
    ('privê atlântico', 'Privê Atlântico'), ('Privê atlântico', 'Privê Atlântico'),
    ('praça do centenário', 'Praça do Centenário'),
    ('Praça do centenário', 'Praça do Centenário'),
    ('cemitério campo da esperança', 'Cemitério Campo da Esperança'),
    ('Cemitério campo da esperança', 'Cemitério Campo da Esperança'),
    ('Cemitério Campo da esperança', 'Cemitério Campo da Esperança'),
    ('secretaria da educação do estado do Tocantins',
     'Secretaria da Educação do Estado do Tocantins'),
    ('Secretaria da educação do estado do Tocantins',
     'Secretaria da Educação do Estado do Tocantins'),
    ('seminário regional do Nordeste', 'Seminário Regional do Nordeste'),
    ('Seminário regional do Nordeste', 'Seminário Regional do Nordeste'),
    ('parque histórico nacional dos Guararapes',
     'Parque Histórico Nacional dos Guararapes'),
    ('Parque histórico nacional dos Guararapes',
     'Parque Histórico Nacional dos Guararapes'),
    ('Parque Histórico nacional dos Guararapes',
     'Parque Histórico Nacional dos Guararapes'),
    # Consolidated expressions
    ('Moderna x contemporânea', 'Moderna x Contemporânea'),
    ('Moderna X contemporânea', 'Moderna X Contemporânea'),
    ('Arquitetura protomoderna', 'Arquitetura Protomoderna'),
    ('Arquitetura de interiores', 'Arquitetura de Interiores'),
]

yaml_changes = 0
for d in YAML_DIRS:
    for path in sorted(glob.glob(os.path.join(d, '*.yaml'))):
        with open(path, 'r', encoding='utf-8') as f:
            content = original = f.read()

        for old, new in ALL_REPLACEMENTS:
            content = content.replace(old, new)

        # Fix "Uma " at start of subtitle lines in YAML
        # In YAML, subtitle appears as "subtitle: Uma ..." or "  subtitle: Uma ..."
        import re
        content = re.sub(
            r'(subtitle:\s+)Uma ',
            r'\1uma ',
            content)

        if content != original:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            yaml_changes += 1
            print(f"  Updated: {os.path.basename(path)}")

print(f"\nYAML files updated: {yaml_changes}")
print(f"\nDone! Run: python3 scripts/dump_anais_db.py && python3 scripts/db2hugo.py")
