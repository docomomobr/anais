#!/usr/bin/env python3
"""
Extrai metadados faltantes dos PDFs do sdsul02 e atualiza o YAML.
Uso: python3 extrair_metadados_pdf.py
"""
import os, re, subprocess, yaml
from collections import OrderedDict

YAML_PATH = "/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul/sdsul02.yaml"
PDF_DIR = "/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul/sdsul02/pdfs"

class OrderedDumper(yaml.SafeDumper):
    pass

def dict_representer(dumper, data):
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())

OrderedDumper.add_representer(OrderedDict, dict_representer)
OrderedDumper.add_representer(dict, dict_representer)

FIELD_ORDER = ["id","title","subtitle","authors","section","locale",
    "file","file_original","pages_count",
    "abstract","abstract_en","keywords","keywords_en","references"]

def ordered_article(a):
    r = OrderedDict()
    for k in FIELD_ORDER:
        if k in a: r[k] = a[k]
    for k in a:
        if k not in r: r[k] = a[k]
    return r

def pdf_text(path):
    try:
        r = subprocess.run(["pdftotext","-layout",path,"-"],capture_output=True,text=True,timeout=30)
        return r.stdout
    except: return ""

def clean(t):
    t = re.sub(r"[ \t]+", " ", t)
    lines = t.split("\n")
    merged, buf = [], ""
    for l in lines:
        l = l.strip()
        if not l:
            if buf: merged.append(buf); buf = ""
            continue
        buf = (buf + " " + l) if buf else l
    if buf: merged.append(buf)
    return "\n".join(merged)

def single(t):
    return re.sub(r"\s+", " ", re.sub(r"\n", " ", t)).strip()

def extract_abstract_pt(text):
    pats = [
        r"(?:^|\n)\s*[Rr][Ee][Ss][Uu][Mm][Oo]\s*[:\-]?\s*\n(.*?)(?:\n\s*(?:Abstract|ABSTRACT|Palavr|PALAVR|Key\s*-?\s*[Ww]ord|Introdu|INTRODU|\d+\s*$))",
        r"(?:^|\n)\s*[Rr][Ee][Ss][Uu][Mm][Oo]\s*[:\-]\s*(.*?)(?:\n\s*(?:Abstract|ABSTRACT|Palavr|PALAVR|Key\s*-?\s*[Ww]ord|Introdu|INTRODU))",
    ]
    for p in pats:
        m = re.search(p, text, re.DOTALL|re.MULTILINE)
        if m:
            a = single(clean(m.group(1).strip()))
            if len(a) > 50: return a
    return None

def extract_abstract_header(text, title):
    """Extract abstract from header block between Fechar and keywords/Abstract markers."""
    fechar_pos = text.find("Fechar")
    if fechar_pos < 0: return None
    # Find first keywords/abstract marker after Fechar
    markers = [
        (r"Palavras[\s-]*[Cc]have", re.IGNORECASE),
        (r"PALAVRAS[\s-]*CHAVE", 0),
        (r"Key[\s-]*[Ww]ords?", 0),
        (r"KEYWORDS?", 0),
        (r"\bAbstract\b", 0),
        (r"\bABSTRACT\b", 0),
    ]
    end_pos = None
    for pat, flags in markers:
        m = re.search(pat, text[fechar_pos+6:], flags)
        if m:
            pos = fechar_pos + 6 + m.start()
            if end_pos is None or pos < end_pos:
                end_pos = pos
    if end_pos is None: return None
    block = text[fechar_pos+6:end_pos].strip()
    if not block: return None
    # Parse into paragraphs, filtering out author/address info
    lines = block.split("\n")
    paras, cur = [], []
    skip_words = ["@","cep:","cep ","fone:","fone ","tel:","endere","e-mail","email","fax","rua ","av.","avenida"]
    for l in lines:
        s = l.strip()
        if not s:
            if cur: paras.append(" ".join(cur)); cur = []
            continue
        low = s.lower()
        if any(x in low for x in skip_words):
            if cur: paras.append(" ".join(cur)); cur = []
            continue
        if re.match(r"^(Arquiteto|Mestre|Doutor|Professor|Mestrando|Doutorando)", s):
            if cur: paras.append(" ".join(cur)); cur = []
            continue
        cur.append(s)
    if cur: paras.append(" ".join(cur))
    # Find the longest paragraph that is not the title
    tl = title.lower().strip()[:30]
    best = None
    for p in paras:
        pc = re.sub(r"\s+", " ", p).strip()
        pc_low = pc.lower().strip()
        # Skip short matches that are just the title line
        is_just_title = (pc_low[:30] == tl or pc_low.startswith(tl)) and len(pc) < len(title) + 50
        if is_just_title: continue
        if len(pc) < 80: continue
        if best is None or len(pc) > len(best): best = pc
    return best if best and len(best) > 80 else None

def extract_abstract_en(text):
    pats = [
        r"(?:^|\n)\s*[Aa][Bb][Ss][Tt][Rr][Aa][Cc][Tt]\s*[:\-]?\s*\n(.*?)(?:\n\s*(?:Key\s*-?\s*[Ww]ord|KEYWORD|Introdu|INTRODU|\d+\s*[.)]?\s+[A-Z]))",
        r"(?:^|\n)\s*[Aa][Bb][Ss][Tt][Rr][Aa][Cc][Tt]\s*[:\-]\s*(.*?)(?:\n\s*(?:Key\s*-?\s*[Ww]ord|KEYWORD|Introdu|INTRODU))",
    ]
    for p in pats:
        m = re.search(p, text, re.DOTALL|re.MULTILINE)
        if m:
            a = single(clean(m.group(1).strip()))
            if len(a) > 50: return a
    m = re.search(r"(?:Abstract|ABSTRACT)\s*\n(.*?)(?:\n\s*(?:Key\s*-?\s*[Ww]ord|KEYWORD))", text, re.DOTALL)
    if m:
        a = single(clean(m.group(1).strip()))
        if len(a) > 50: return a
    return None

def extract_abstract_en_alt(text):
    m = re.search(r"(?:Palavras[\s-]*[Cc]have|PALAVRAS[\s-]*CHAVE)[^\n]*\n(.*?)(?:\n\s*Key\s*-?\s*[Ww]ord)", text, re.DOTALL)
    if not m: return None
    block = clean(m.group(1).strip())
    best = None
    for p in block.split("\n"):
        pc = re.sub(r"\s+", " ", p).strip()
        if len(pc) > 100:
            if best is None or len(pc) > len(best): best = pc
    return best if best and len(best) > 100 else None

def parse_kw(text):
    if not text: return None
    text = text.strip().rstrip(".")
    sep = ";" if ";" in text else ","
    kws = [k.rstrip(".").strip() for k in text.split(sep) if k.strip() and len(k.strip()) > 1]
    return kws if kws else None

def extract_kw_pt(text):
    pats = [
        r"[Pp]alavras[\s-]*[Cc]have[s]?\s*[:\-]\s*(.*?)(?:\n\s*\n|\n\s*(?:Abstract|ABSTRACT|Key\s*-?\s*[Ww]ord|Introdu|INTRODU|\d+\s*$))",
        r"PALAVRAS[\s-]*CHAVE[S]?\s*[:\-]\s*(.*?)(?:\n\s*\n|\n\s*(?:Abstract|ABSTRACT|Key|Introdu|INTRODU))",
    ]
    for p in pats:
        m = re.search(p, text, re.DOTALL|re.MULTILINE)
        if m:
            raw = re.sub(r"\s+", " ", re.sub(r"\s*\n\s*", " ", m.group(1).strip()))
            return parse_kw(raw)
    m = re.search(r"[Pp]alavras[\s-]*[Cc]have[s]?\s*[:\-]\s*(.+)", text)
    if m:
        raw = re.sub(r"\s+", " ", m.group(1).strip().split("\n")[0])
        return parse_kw(raw)
    return None

def extract_kw_en(text):
    pats = [
        r"[Kk]ey[\s-]*[Ww]ords?\s*[:\-]\s*(.*?)(?:\n\s*\n|\n\s*(?:Introdu|INTRODU|Resumo|RESUMO|\d+\s*[.)]?\s+[A-Z]|\d+\s*$))",
        r"KEYWORDS?\s*[:\-]\s*(.*?)(?:\n\s*\n|\n\s*(?:Introdu|INTRODU|Resumo|RESUMO))",
    ]
    for p in pats:
        m = re.search(p, text, re.DOTALL|re.MULTILINE)
        if m:
            raw = re.sub(r"\s+", " ", re.sub(r"\s*\n\s*", " ", m.group(1).strip()))
            return parse_kw(raw)
    m = re.search(r"[Kk]ey[\s-]*[Ww]ords?\s*[:\-]\s*(.+)", text)
    if m:
        raw = re.sub(r"\s+", " ", m.group(1).strip().split("\n")[0])
        return parse_kw(raw)
    return None

def extract_refs(text):
    pats = [
        r"(?:^|\n)\s*\d*\s*[.\-\u2013\u2014]?\s*(?:Refer[eê]ncias\s*[Bb]ibliogr[aá]ficas?|REFER[EÊ]NCIAS\s*BIBLIOGR[AÁ]FICAS?)\s*:?\s*\n(.*)",
        r"(?:^|\n)\s*\d*\s*[.\-\u2013\u2014]?\s*(?:Referências|REFERÊNCIAS|Bibliografia|BIBLIOGRAFIA)\s*:?\s*\n(.*)",
        r"(?:^|\n)\s*(?:\d+\s*[.\-\u2013\u2014]\s*)?(?:Referências|REFERÊNCIAS|Bibliografia|BIBLIOGRAFIA)\s*:?\s*\n(.*)",
    ]
    for p in pats:
        m = re.search(p, text, re.DOTALL|re.MULTILINE)
        if m:
            return parse_refs_block(m.group(1).strip())
    return None

def parse_refs_block(block):
    block = re.sub(r"\n\s*\d{1,3}\s*$", "\n", block, flags=re.MULTILINE)
    for marker in ["Créditos das imagens","Créditos","CRÉDITOS","Legendas","LEGENDAS"]:
        idx = block.find(marker)
        if idx > 0: block = block[:idx]
    lines = block.split("\n")
    refs, cur = [], ""
    for l in lines:
        s = l.strip()
        if not s:
            if cur: refs.append(cur.strip()); cur = ""
            continue
        new_ref = bool(re.match(r"^[A-Z\u00C0-\u00DC][A-Z\u00C0-\u00DC\s,\.]+[,\.]", s)) or s.startswith("__") or s.startswith("Cf. ")
        if new_ref and cur:
            refs.append(cur.strip()); cur = s
        elif cur: cur += " " + s
        else: cur = s
    if cur: refs.append(cur.strip())
    return [re.sub(r"\s+"," ",r).strip() for r in refs if len(r.strip())>=15 and not r.startswith("Imprimir") and not r.startswith("Fechar")] or None

def main():
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    articles = data["articles"]
    fields = ["abstract","abstract_en","keywords","keywords_en","references"]
    stats_before = {fld: sum(1 for a in articles if a.get(fld)) for fld in fields}
    total = len(articles)
    updated_count = 0
    for article in articles:
        aid = article["id"]
        pdf_path = os.path.join(PDF_DIR, article.get("file",""))
        if not os.path.exists(pdf_path):
            print(f"  {aid}: PDF nao encontrado"); continue
        needs = {fld: not article.get(fld) for fld in fields}
        if not any(needs.values()): continue
        text = pdf_text(pdf_path)
        if not text: print(f"  {aid}: texto vazio"); continue
        updated = False
        title = article.get("title","")
        if needs["abstract"]:
            a = extract_abstract_pt(text) or extract_abstract_header(text, title)
            if a: article["abstract"] = a; updated = True; print(f"  {aid}: +abstract ({len(a)} chars)")
        if needs["abstract_en"]:
            a = extract_abstract_en(text) or extract_abstract_en_alt(text)
            if a: article["abstract_en"] = a; updated = True; print(f"  {aid}: +abstract_en ({len(a)} chars)")
        if needs["keywords"]:
            k = extract_kw_pt(text)
            if k: article["keywords"] = k; updated = True; print(f"  {aid}: +keywords ({len(k)} items)")
        if needs["keywords_en"]:
            k = extract_kw_en(text)
            if k: article["keywords_en"] = k; updated = True; print(f"  {aid}: +keywords_en ({len(k)} items)")
        if needs["references"]:
            r = extract_refs(text)
            if r: article["references"] = r; updated = True; print(f"  {aid}: +references ({len(r)} items)")
        if updated: updated_count += 1
    stats_after = {fld: sum(1 for a in articles if a.get(fld)) for fld in fields}
    data["articles"] = [ordered_article(a) for a in articles]
    with open(YAML_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                  default_flow_style=False, width=10000, sort_keys=False)
    print()
    print("=" * 60)
    print(f"sdsul02 - Extracao de metadados dos PDFs")
    print(f"Total de artigos: {total}")
    print(f"Artigos atualizados: {updated_count}")
    print("=" * 60)
    hdr = f"{'Campo':<15} {'Antes':>8} {'Depois':>8} {'Novos':>8}"
    print(hdr)
    print("-" * 45)
    for fld in fields:
        b, a = stats_before[fld], stats_after[fld]
        print(f"{fld:<15} {b:>5}/{total:<3} {a:>5}/{total:<3} {'+'+str(a-b):>7}")
    print("-" * 45)
    print()
    print("Artigos ainda sem dados:")
    for fld in fields:
        missing = [a["id"] for a in articles if not a.get(fld)]
        if missing: print(f"  {fld}: {', '.join(missing)}")

if __name__ == "__main__":
    main()
