#!/usr/bin/env python3
"""Process sdrj04: split PDF, extract metadata, update YAML."""
import subprocess, re, os, yaml

BASE_DIR = "/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/rio/sdrj04"
PDF_DIR = os.path.join(BASE_DIR, "pdfs")
SOURCE_PDF = os.path.join(PDF_DIR, "sdrj04_anais.pdf")
YAML_FILE = "/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/rio/sdrj04.yaml"

TOC = [
    (9, "Eixo 1 - O risco moderno no Rio", "artigo"),
    (26, "Eixo 1 - O risco moderno no Rio", "artigo"),
    (45, "Eixo 1 - O risco moderno no Rio", "artigo"),
    (65, "Eixo 1 - O risco moderno no Rio", "artigo"),
    (82, "Eixo 1 - O risco moderno no Rio", "artigo"),
    (98, "Eixo 1 - O risco moderno no Rio", "artigo"),
    (122, "Eixo 1 - O risco moderno no Rio", "painel"),
    (127, "Eixo 1 - O risco moderno no Rio", "painel"),
    (134, "Eixo 2 - O moderno em risco no Rio", "artigo"),
    (150, "Eixo 2 - O moderno em risco no Rio", "artigo"),
    (168, "Eixo 2 - O moderno em risco no Rio", "artigo"),
    (185, "Eixo 2 - O moderno em risco no Rio", "artigo"),
    (201, "Eixo 2 - O moderno em risco no Rio", "artigo"),
    (218, "Eixo 2 - O moderno em risco no Rio", "artigo"),
    (235, "Eixo 2 - O moderno em risco no Rio", "artigo"),
    (257, "Eixo 2 - O moderno em risco no Rio", "painel"),
    (275, "Workshop", "workshop"),
]

TITLES = {
    0: ("A Casa Lota de Macedo Soares", "contribui\u00e7\u00f5es modernas na arquitetura contempor\u00e2nea carioca"),
    1: ("O apartamento carioca na d\u00e9cada de 1920 e o primeiro edif\u00edcio moderno de habita\u00e7\u00e3o coletiva", None),
    2: ("Contribui\u00e7\u00e3o \u00e0 quest\u00e3o do g\u00eanero na habita\u00e7\u00e3o e no urbanismo modernos no Rio de Janeiro", "Carmen Portinho"),
    3: ("Arquitetura em risco", "um estudo sobre a obra de Antonio Virzi no Rio de Janeiro e sua import\u00e2ncia como patrim\u00f4nio de uma moderna arquitetura carioca"),
    4: ("A magia das imagens", "representa\u00e7\u00f5es do Brasil em Brazil Builds"),
    5: ("A arquitetura hospitalar protomoderna no Instituto Nise da Silveira", None),
    6: ("BIM do Pal\u00e1cio Gustavo Capanema, Rio de Janeiro-RJ", "estudos da evolu\u00e7\u00e3o hist\u00f3rica construtiva 1937-1945"),
    7: ("As escolas dos anos 1950", None),
    8: ("Riscos para o patrim\u00f4nio moderno na cidade do Rio de Janeiro influenciados pelas mudan\u00e7as clim\u00e1ticas", None),
    9: ("Usos contempor\u00e2neos do patrim\u00f4nio moderno da sa\u00fade", "o caso do Albergue da Boa Vontade e do Instituto Vital Brazil"),
    10: ("Desafios da preserva\u00e7\u00e3o do patrim\u00f4nio moderno", "o caso do Pavilh\u00e3o Arthur Neiva"),
    11: ("Preserva\u00e7\u00e3o da arquitetura moderna", "a Cidade Universit\u00e1ria da UFRJ"),
    12: ("Preserva\u00e7\u00e3o da arquitetura moderna na Funda\u00e7\u00e3o Oswaldo Cruz", "o caso do antigo Pavilh\u00e3o da Febre Amarela"),
    13: ("O Moderno Modesto Carioca, mas nem tanto", "do risco ao risco"),
    14: ("Edif\u00edcio Jorge Machado Moreira", "movimento moderno em chamas"),
    15: ("Parque do Flamengo", "patrim\u00f4nio paisag\u00edstico moderno para a contemporaneidade"),
    16: ("Riscos e aprendizados do Moderno Universit\u00e1rio", None),
}

AUTHORS = {
    0: [
        {"givenname": "Pauline Fonini", "familyname": "Felin", "email": "pffelin@ucs.br", "affiliation": "UCS", "country": "BR"},
        {"givenname": "Monika Maria", "familyname": "Stumpp", "email": "monistumpp@hotmail.com", "affiliation": "UFRGS", "country": "BR"},
    ],
    1: [{"givenname": "Tatiana de Souza", "familyname": "Gaspar", "email": "gaspar@exemplo.com", "affiliation": "", "country": "BR"}],
    2: [{"givenname": "Marcela Marques", "familyname": "Abla", "email": "abla@exemplo.com", "affiliation": "", "country": "BR"}],
    3: [
        {"givenname": "Gabriel Botelho Neves da", "familyname": "Rosa", "email": "rosa@exemplo.com", "affiliation": "", "country": "BR"},
        {"givenname": "Giulia Gobbi Fernandes", "familyname": "Schiavini", "email": "schiavini@exemplo.com", "affiliation": "", "country": "BR"},
    ],
    4: [{"givenname": "Helio", "familyname": "Herbst", "email": "herbst@exemplo.com", "affiliation": "UFRRJ", "country": "BR"}],
    5: [{"givenname": "Luiz Paulo Leal de", "familyname": "Oliveira", "email": "oliveira@exemplo.com", "affiliation": "", "country": "BR"}],
    6: [{"givenname": "Cristiane Lopes", "familyname": "Canuto", "email": "cricanuto@gmail.com", "affiliation": "PROARQ-UFRJ", "country": "BR"}],
    7: [{"givenname": "Noemia Lucia Barradas", "familyname": "Fernandes", "email": "fernandes@exemplo.com", "affiliation": "", "country": "BR"}],
    8: [{"givenname": "Carla Maria Teixeira", "familyname": "Coelho", "email": "coelho@exemplo.com", "affiliation": "", "country": "BR"}],
    9: [
        {"givenname": "Barbara Cortizo de", "familyname": "Aguiar", "email": "aguiar@exemplo.com", "affiliation": "COC-Fiocruz", "country": "BR"},
        {"givenname": "Priscila Fonseca da", "familyname": "Silva", "email": "silva@exemplo.com", "affiliation": "", "country": "BR"},
        {"givenname": "Rosana Soares", "familyname": "Zouain", "email": "zouain@exemplo.com", "affiliation": "COC-Fiocruz", "country": "BR"},
    ],
    10: [
        {"givenname": "Barbara Cortizo de", "familyname": "Aguiar", "email": "aguiar@exemplo.com", "affiliation": "COC-Fiocruz", "country": "BR"},
        {"givenname": "Elisabete Edelvita Chaves da", "familyname": "Silva", "email": "esilva@exemplo.com", "affiliation": "COC-Fiocruz", "country": "BR"},
        {"givenname": "In\u00eas El-Jaick", "familyname": "Andrade", "email": "andrade@exemplo.com", "affiliation": "COC-Fiocruz", "country": "BR"},
        {"givenname": "Rosana Soares", "familyname": "Zouain", "email": "zouain2@exemplo.com", "affiliation": "COC-Fiocruz", "country": "BR"},
    ],
    11: [{"givenname": "Patricia Cavalcante", "familyname": "Cordeiro", "email": "cordeiro@exemplo.com", "affiliation": "", "country": "BR"}],
    12: [{"givenname": "Rosana Soares", "familyname": "Zouain", "email": "zouain@exemplo.com", "affiliation": "COC-Fiocruz", "country": "BR"}],
    13: [
        {"givenname": "Julio Cesar Ribeiro", "familyname": "Sampaio", "email": "sampaio@exemplo.com", "affiliation": "UFRRJ", "country": "BR"},
        {"givenname": "Claudio Antonio Santos Lima", "familyname": "Carlos", "email": "carlos@exemplo.com", "affiliation": "", "country": "BR"},
        {"givenname": "Cristiane Souza", "familyname": "Gon\u00e7alves", "email": "goncalves@exemplo.com", "affiliation": "", "country": "BR"},
    ],
    14: [{"givenname": "Paulo", "familyname": "Jardim", "email": "jardim@exemplo.com", "affiliation": "", "country": "BR"}],
    15: [{"givenname": "Vinicius Ferreira", "familyname": "Mattos", "email": "vinicius.ferreira.mattos@gmail.com", "affiliation": "PROURB-UFRJ", "country": "BR"}],
    16: [
        {"givenname": "Renato da Gama-Rosa", "familyname": "Costa", "email": "costa@exemplo.com", "affiliation": "COC-Fiocruz", "country": "BR"},
        {"givenname": "Andr\u00e9a de Lacerda Pess\u00f4a", "familyname": "Borde", "email": "borde@exemplo.com", "affiliation": "PROURB-UFRJ", "country": "BR"},
        {"givenname": "Cristina", "familyname": "Coelho", "email": "ccoelho@exemplo.com", "affiliation": "COC-Fiocruz", "country": "BR"},
    ],
}


class OrderedDumper(yaml.SafeDumper):
    pass

def _dict_rep(dumper, data):
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())
def _none_rep(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:null", "null")
def _str_rep(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)

OrderedDumper.add_representer(dict, _dict_rep)
OrderedDumper.add_representer(type(None), _none_rep)
OrderedDumper.add_representer(str, _str_rep)


def extract_text(sp, ep):
    r = subprocess.run(["pdftotext", "-f", str(sp), "-l", str(ep), SOURCE_PDF, "-"], capture_output=True, text=True)
    return r.stdout

def split_pdf(start, end, out):
    subprocess.run(["qpdf", "--empty", "--pages", SOURCE_PDF, f"{start}-{end}", "--", out], check=True, capture_output=True)

def end_pages():
    eps = []
    for i in range(len(TOC)):
        eps.append(TOC[i+1][0] - 1 if i+1 < len(TOC) else 278)
    return eps

def extract_meta(text):
    """Extract abstracts and keywords. Handles two-column PDF layout where
    RESUMO and ABSTRACT headers appear consecutively, followed by PT paragraph
    then EN paragraph separated by blank lines."""
    res = {"resumo": None, "resumo_en": None, "resumo_es": None, "palavras_chave": [], "palavras_chave_en": []}
    text = re.sub(r"-\n", "", text)
    lines = text.split("\n")

    # Detect two-column layout: RESUMO followed closely by ABSTRACT
    two_col = False
    two_col_lang = "en"
    resumo_line = None
    abstract_line = None
    for i, line in enumerate(lines):
        s = line.strip()
        if s == "RESUMO":
            resumo_line = i
        if s in ("ABSTRACT", "ABSTRACT:", "RESUMEN", "RESUMEN:") and resumo_line is not None:
            if i - resumo_line <= 3:  # headers within 3 lines = two-column
                two_col = True
                if s.startswith("RESUMEN"):
                    two_col_lang = "es"
                else:
                    two_col_lang = "en"
            abstract_line = i
            break

    if two_col and abstract_line is not None:
        # Two-column: collect paragraphs after ABSTRACT header
        # First non-empty paragraph = PT resumo, second = EN abstract
        paragraphs = []
        current_para = ""
        start_idx = abstract_line + 1
        for i in range(start_idx, len(lines)):
            s = lines[i].strip()
            # Stop at keywords or author info
            if re.match(r"^Palavras[- ]?chave", s, re.I): break
            if re.match(r"^Key[- ]?words?", s, re.I): break
            if "DOCOMOMO-RIO" in s.upper(): continue
            if re.match(r"^\d+$", s): continue
            if not s:
                if current_para:
                    paragraphs.append(current_para.strip())
                    current_para = ""
                continue
            current_para += " " + s
        if current_para:
            paragraphs.append(current_para.strip())

        if len(paragraphs) >= 2:
            res["resumo"] = paragraphs[0]
            if two_col_lang == "es":
                res["resumo_es"] = paragraphs[1]
            else:
                res["resumo_en"] = paragraphs[1]
        elif len(paragraphs) == 1:
            res["resumo"] = paragraphs[0]
    else:
        # Standard layout: separate RESUMO and ABSTRACT sections
        rtext, atext, estext = "", "", ""
        in_r, in_a, in_es = False, False, False
        for i, line in enumerate(lines):
            s = line.strip()
            if s == "RESUMO":
                in_r, in_a, in_es = True, False, False; continue
            if s in ("ABSTRACT", "ABSTRACT:"):
                in_r, in_a, in_es = False, True, False; continue
            if s in ("RESUMEN", "RESUMEN:"):
                in_r, in_a, in_es = False, False, True; continue
            if re.match(r"^Palavras[- ]?chave", s, re.I):
                in_r, in_es = False, False; break
            if re.match(r"^Key[- ]?words?", s, re.I):
                in_a = False; break
            if s and "DOCOMOMO-RIO" in s.upper(): continue
            if re.match(r"^\d+$", s): continue
            if in_r and s: rtext += " " + s
            elif in_a and s: atext += " " + s
            elif in_es and s: estext += " " + s
        res["resumo"] = rtext.strip() or None
        res["resumo_en"] = atext.strip() or None
        res["resumo_es"] = estext.strip() or None

    # Extract keywords (always scan full text)
    for i, line in enumerate(lines):
        s = line.strip()
        kw_pt = re.match(r"^Palavras[- ]?chave[s]?\s*[:.]?\s*(.*)", s, re.I)
        kw_en = re.match(r"^Key[- ]?words?\s*[:.]?\s*(.*)", s, re.I)
        if kw_pt:
            kt = kw_pt.group(1).strip()
            j = i + 1
            while j < len(lines) and lines[j].strip() and not re.match(r"^(Key|ABSTRACT|RESUMEN|Palavras|\w+@)", lines[j].strip(), re.I):
                kt += " " + lines[j].strip(); j += 1
            kt = re.sub(r"\.$", "", kt)
            kws = [k.strip().rstrip(".") for k in re.split(r"[;]", kt) if k.strip()]
            if len(kws) == 1:
                kws = [k.strip().rstrip(".") for k in re.split(r"[,]", kt) if k.strip()]
            res["palavras_chave"] = kws
        if kw_en:
            kt = kw_en.group(1).strip()
            j = i + 1
            while j < len(lines) and lines[j].strip() and not re.match(r"^(Palavras|RESUMO|RESUMEN|\w+@)", lines[j].strip(), re.I):
                kt += " " + lines[j].strip(); j += 1
            kt = re.sub(r"\.$", "", kt)
            kws = [k.strip().rstrip(".") for k in re.split(r"[;]", kt) if k.strip()]
            if len(kws) == 1:
                kws = [k.strip().rstrip(".") for k in re.split(r"[,]", kt) if k.strip()]
            res["palavras_chave_en"] = kws
    return res

def extract_refs(text):
    refs = []
    pats = [r"REFER[\u00ca|E]NCIAS\s*BIBLIOGR", r"REFER[\u00ca|E]NCIAS", r"BIBLIOGRAFIA"]
    rs = None
    for p in pats:
        m = re.search(p, text, re.I)
        if m: rs = m.end(); break
    if rs is None: return refs
    rt = text[rs:]
    rt = re.sub(r"\n\d+\n", "\n", rt)
    rt = re.sub(r"IV SEMIN.*?DO RISCO AO RISCO", "", rt)
    cur = ""
    for line in rt.strip().split("\n"):
        s = line.strip()
        if not s:
            if cur: refs.append(cur.strip()); cur = ""
            continue
        if re.match(r"^[A-Z\u00c0-\u00dc][A-Z\u00c0-\u00dc]+[,.]", s) or re.match(r"^\d+[.)]\s", s):
            if cur: refs.append(cur.strip())
            cur = s
        elif re.match(r"^_+", s):
            if cur: refs.append(cur.strip())
            cur = s
        else:
            cur += " " + s
    if cur: refs.append(cur.strip())
    return [r for r in refs if len(r) > 20 and not r.startswith("FONTE")]


def main():
    eps = end_pages()
    print(f"Processing {len(TOC)} entries")
    articles = []
    for idx, (sp, section, atype) in enumerate(TOC):
        ep = eps[idx]
        aid = f"sdrj04-{idx+1:03d}"
        pname = f"{aid}.pdf"
        ppath = os.path.join(PDF_DIR, pname)
        title, subtitle = TITLES[idx]
        print(f"[{idx+1:02d}] p.{sp}-{ep} | {title[:65]}...")
        split_pdf(sp, ep, ppath)
        fp_text = extract_text(sp, min(sp+2, ep))
        full_text = extract_text(sp, ep)
        meta = extract_meta(fp_text)
        refs = extract_refs(full_text)
        auths = []
        for i, ad in enumerate(AUTHORS[idx]):
            auths.append({"givenname": ad["givenname"], "familyname": ad["familyname"],
                          "email": ad["email"], "affiliation": ad["affiliation"],
                          "country": ad["country"], "primary_contact": i == 0})
        art = {"id": aid, "seminario": "sdrj04", "secao": section, "tipo": atype, "titulo": title}
        if subtitle: art["subtitulo"] = subtitle
        art["locale"] = "pt-BR"
        art["autores"] = auths
        if meta["resumo"]: art["resumo"] = meta["resumo"]
        if meta["resumo_en"]: art["resumo_en"] = meta["resumo_en"]
        if meta["resumo_es"]: art["resumo_es"] = meta["resumo_es"]
        if meta["palavras_chave"]: art["palavras_chave"] = meta["palavras_chave"]
        if meta["palavras_chave_en"]: art["palavras_chave_en"] = meta["palavras_chave_en"]
        art["paginas"] = f"{sp}-{ep}"
        art["arquivo_pdf"] = pname
        if refs: art["referencias"] = refs
        articles.append(art)
        hr = "Y" if meta["resumo"] else "N"
        ha = "Y" if meta["resumo_en"] else "N"
        hk = "Y" if meta["palavras_chave"] else "N"
        print(f"     {ep-sp+1}pp Resumo:{hr} Abstract:{ha} KW:{hk} Refs:{len(refs)}")

    with open(YAML_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data["articles"] = articles
    with open(YAML_FILE, "w", encoding="utf-8") as f:
        yaml.dump({"issue": data["issue"], "articles": articles}, f,
                  Dumper=OrderedDumper, default_flow_style=False,
                  allow_unicode=True, width=10000, sort_keys=False)

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total: {len(articles)}")
    for t in ["artigo","painel","workshop"]:
        print(f"  {t}: {sum(1 for a in articles if a['tipo']==t)}")
    for e in ["Eixo 1","Eixo 2","Workshop"]:
        print(f"  {e}: {sum(1 for a in articles if e in a.get('secao',''))}")
    for k,l in [("resumo","resumo"),("abstract","resumo_en"),("palavras_chave","palavras_chave"),("referencias","referencias")]:
        print(f"  Com {k}: {sum(1 for a in articles if a.get(l))}/{len(articles)}")
    print(f"\nYAML: {YAML_FILE}")
    print(f"PDFs: {PDF_DIR}")

if __name__ == "__main__":
    main()
