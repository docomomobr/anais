#!/usr/bin/env python3
"""Remonta o texto integral (markdown) de artigos a partir dos fontes_plumber.

Piloto da frente fulltext (devlog 2026-07-14). Estratégia: os blocos do
plumber já vêm etiquetados por papel tipográfico (per-seminário); aqui:

  1. moldura fora — blocos cujo texto se repete em ≥3 páginas (cabeçalho/
     rodapé corrido) e blocos `pagenum`;
  2. legendas fora — padrões "Figura/Foto/Tabela/Quadro/Gráfico N" e
     "Fonte:" (decisão editorial: sem imagens, sem legendas);
  3. resumos fora — role `abstract` (a página do artigo já os exibe);
  4. corpo = heading/subheading/body em ordem (página, y), com refluxo de
     parágrafos e des-hifenização;
  5. notas (role `footnote` não-moldura) agrupadas ao fim em "Notas",
     com numeração recuperada do PDF via pymupdf (número sobrescrito =
     span só-dígitos menor e com baseline elevada; cobre notas de rodapé
     E de fim). Requer .venv-fulltext/bin/python; sem pymupdf, sai sem
     numeração;
  6. referências FORA — a página do artigo já as exibe, curadas, do banco;
  7. corpo começa no primeiro heading (folha de rosto fora).

Saída: um .md por artigo no diretório indicado — NADA é publicado; o
gate é a revisão humana (ver feedback registrado: sem "html porco").

Uso:
    python3 scripts/extrair_fulltext.py --slug sdnne10 --outdir /tmp/fulltext
    python3 scripts/extrair_fulltext.py --slug sdnne10 --article sdnne10-010 --outdir DIR
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    import pymupdf
except ImportError:
    pymupdf = None

CAPTION_RE = re.compile(
    r'^\s*(Figura|Foto|Fotografia|Tabela|Quadro|Gráfico|Imagem|Mapa|Prancha)s?\s*\d|^\s*Fonte\s*[:–]',
    re.I)
REPEAT_MIN_PAGES = 3


def _norm(text):
    return re.sub(r'\s+', ' ', text).strip().lower()


def _key(text, n=40):
    """Chave de casamento: só letras/dígitos, minúscula, primeiros n chars."""
    return re.sub(r'[^a-z0-9à-ú]', '', _norm(text))[:n]


def _reflow(text):
    """Junta quebras de linha internas; des-hifeniza fim de linha."""
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    text = re.sub(r'\s*\n\s*', ' ', text)
    return re.sub(r'  +', ' ', text).strip()


def load_blocks(path):
    return [json.loads(l) for l in open(path)]


def frame_texts(blocks):
    """Textos de moldura: repetem (normalizados) em ≥REPEAT_MIN_PAGES páginas."""
    seen = {}
    for b in blocks:
        key = _norm(b['text'])[:120]
        if not key:
            continue
        seen.setdefault(key, set()).add(b['page'])
    return {k for k, pages in seen.items() if len(pages) >= REPEAT_MIN_PAGES}


def anotacoes_do_pdf(pdf_path):
    """Assinatura tipográfica de sobrescrito (dígito menor + baseline
    elevada) → (defs, calls): definições de nota {chave_do_texto: num}
    e chamadas no corpo [(num, cauda_do_texto_anterior)]."""
    if not pymupdf or not os.path.isfile(pdf_path):
        return {}, []
    defs, calls = {}, []
    doc = pymupdf.open(pdf_path)
    for page in doc:
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                spans = [sp for sp in line.get('spans', []) if sp['text'].strip()]
                for i, sp in enumerate(spans):
                    if not re.fullmatch(r'\d{1,3}', sp['text'].strip()):
                        continue
                    num = int(sp['text'].strip())
                    viz = spans[i + 1] if i == 0 and len(spans) > 1 else (spans[i - 1] if i > 0 else None)
                    if not viz:
                        continue
                    if not (sp['size'] < viz['size'] - 0.3
                            and sp['origin'][1] < viz['origin'][1] - 0.5):
                        continue
                    if i == 0:  # início de linha = definição da nota
                        chave = _key(' '.join(x['text'] for x in spans[1:]))
                        if chave:
                            defs.setdefault(chave, num)
                    else:       # meio de linha = chamada no corpo
                        calls.append((num, spans[i - 1]['text'][-24:]))
    doc.close()
    return defs, calls


def marcar_chamadas(text, calls):
    """Troca o dígito colado pela sintaxe pandoc: palavra1 → palavra[^1].
    Se o dígito sobrescrito nem chegou ao texto (pdfplumber às vezes o
    descarta), insere o marcador logo após a cauda de contexto."""
    for num, cauda in calls:
        cauda = cauda.strip()
        feito = False
        for tam in (12, 8, 5):
            alvo = re.escape(cauda[-tam:]) + str(num) + r'(?=[\s.,;:)\]]|$)'
            novo, n = re.subn(alvo, cauda[-tam:] + f'[^{num}]', text, count=1)
            if n:
                text, feito = novo, True
                break
        if not feito:
            for tam in (16, 12):
                alvo = re.escape(cauda[-tam:]) + r'(?=[\s.,;:)\]])'
                novo, n = re.subn(alvo, cauda[-tam:] + f'[^{num}]', text, count=1)
                if n:
                    text = novo
                    break
    return text


def montar(blocks, nota_nums=None, calls=None):
    frames = frame_texts(blocks)

    def is_frame(b):
        return _norm(b['text'])[:120] in frames

    def keep(b):
        if b['role'] in ('pagenum', 'abstract'):
            return False
        if is_frame(b):
            return False
        if CAPTION_RE.search(b['text']):
            return False
        return True

    SECTION_HEADINGS = re.compile(
        r'^\s*(NOTAS?|REFER[EÊ]NCIAS( BIBLIOGR[AÁ]FICAS)?|BIBLIOGRAFIA)\s*$', re.I)
    # seções que não entram no fulltext (a página já as exibe): ao encontrar
    # um heading destes, pula até o próximo heading
    DROP_SECTIONS = re.compile(
        r'^\s*(RESUMO|ABSTRACT|RESUMEN|PALAVRAS[- ]CHAVE|KEY ?WORDS?|PALABRAS[- ]CLAVES?)\b', re.I)
    corpo, notas = [], []
    dropping = False
    for b in sorted(blocks, key=lambda x: (x['page'], x['y'])):
        if not keep(b):
            continue
        if b['role'] in ('heading', 'subheading'):
            dropping = bool(DROP_SECTIONS.match(_reflow(b['text'])))
        elif dropping and b['role'] in ('body', 'small'):
            continue
        text = _reflow(b['text'])
        if not text:
            continue
        if b['role'] == 'reference':
            continue  # página do artigo já exibe as referências do banco
        elif b['role'] == 'footnote':
            if nota_nums:
                k = _key(text)
                num = next((v for kk, v in nota_nums.items()
                            if k.startswith(kk[:24]) or kk.startswith(k[:24])), None)
                if num is not None:
                    notas.append((num, text))
                    ultima_nota_pg = b['page']
                elif notas and b['page'] == locals().get('ultima_nota_pg'):
                    n0, t0 = notas[-1]
                    notas[-1] = (n0, t0 + ' ' + text)  # continuação da nota
                else:
                    corpo.append('> ' + text)  # citação em bloco (fonte menor)
            else:
                notas.append((10**6, text))
        elif b['role'] in ('heading', 'subheading'):
            # título de seção; página 1 tem título/autores — headings de p1 ficam fora
            if b['page'] == 1:
                continue
            if SECTION_HEADINGS.match(text):
                continue  # geramos os nossos ("Notas"); refs ficam fora
            nivel = '##' if b['role'] == 'heading' else '###'
            corpo.append(f'\n{nivel} {text}\n')
        elif b['role'] in ('body', 'small'):
            if b['page'] == 1 and b['role'] == 'small':
                continue  # afiliações/rosto
            corpo.append(text)

    # fundir parágrafos partidos entre blocos/páginas: bloco que não termina
    # em pontuação final + próximo começa com minúscula
    fundido = []
    for par in corpo:
        if (fundido and not par.startswith('#') and not fundido[-1].startswith('#')
                and not re.search(r'[.!?:;»”"]\s*$', fundido[-1])
                and par[:1].islower()):
            fundido[-1] = fundido[-1] + ' ' + par
        else:
            fundido.append(par)

    # folha de rosto fora: corpo começa no primeiro heading, se houver
    primeiro = next((i for i, p in enumerate(fundido) if p.startswith('\n##')), None)
    if primeiro:
        fundido = fundido[primeiro:]

    md = '\n\n'.join(fundido)
    if calls:
        md = marcar_chamadas(md, calls)  # uma vez, sobre o texto inteiro
    if notas:
        notas.sort(key=lambda x: x[0])
        numeradas = [f'[^{n}]: {t}' for n, t in notas if n < 10**6]
        soltas = [t for n, t in notas if n >= 10**6]
        if numeradas:
            md += '\n\n' + '\n\n'.join(numeradas)
        if soltas:
            md += '\n\n## Notas\n\n' + '\n\n'.join(soltas)
    return md


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--slug', required=True)
    ap.add_argument('--article')
    ap.add_argument('--outdir', required=True)
    args = ap.parse_args()

    # localizar fontes_plumber do seminário
    hits = []
    for grupo in ('nne', 'se', 'sul'):
        d = os.path.join(BASE_DIR, 'regionais', grupo, args.slug, 'fontes_plumber')
        if os.path.isdir(d):
            hits.append(d)
    for top in ('nacionais', 'internacional'):
        d = os.path.join(BASE_DIR, top, args.slug, 'fontes_plumber')
        if os.path.isdir(d):
            hits.append(d)
    if not hits:
        sys.exit(f'fontes_plumber não encontrado para {args.slug}')
    src = hits[0]

    os.makedirs(args.outdir, exist_ok=True)
    files = sorted(f for f in os.listdir(src) if f.endswith('.jsonl'))
    if args.article:
        files = [f for f in files if f.startswith(args.article)]
    pdf_dir = os.path.join(os.path.dirname(src), 'pdfs')
    for f in files:
        art = f[:-6]
        defs, calls = anotacoes_do_pdf(os.path.join(pdf_dir, art + '.pdf'))
        md = montar(load_blocks(os.path.join(src, f)), defs, calls)
        out = os.path.join(args.outdir, art + '.md')
        with open(out, 'w') as fh:
            fh.write(md + '\n')
        palavras = len(md.split())
        print(f'{art}: {palavras} palavras → {out}')


if __name__ == '__main__':
    main()
