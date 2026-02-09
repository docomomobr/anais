#!/usr/bin/env python3
"""Pipeline completo sdsul05."""
import yaml, subprocess, re, os, shutil, unicodedata

class OrderedDumper(yaml.SafeDumper):
    pass
def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())
OrderedDumper.add_representer(dict, dict_representer)

BASE = '/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sul'
PDFS = os.path.join(BASE, 'sdsul05', 'pdfs')
YAML_OUT = os.path.join(BASE, 'sdsul05.yaml')

issue = {
    'slug': 'sdsul05',
    'title': '5\u00ba Semin\u00e1rio Docomomo Sul, Porto Alegre, 2016',
    'subtitle': None,
    'description': 'PELLEGRINI, Ana Carolina; COMAS, Carlos Eduardo (org.). Anais do V Semin\u00e1rio Docomomo Sul, Porto Alegre, 25-26 jul. 2016 [recurso eletr\u00f4nico]. Porto Alegre: PROPAR/UFRGS, 2016.',
    'year': 2016, 'volume': 1, 'number': 5, 'date_published': '2016-07-25',
    'publisher': 'PROPAR/UFRGS',
    'editors': ['Ana Carolina Pellegrini', 'Carlos Eduardo Comas'],
    'source': 'https://www.ufrgs.br/propar/anais-do-5o-seminario-docomomo-sul/',
}

# (num, file, title, [(givenname, familyname, affiliation, email)])
D = []
D.append((1,'01_Adriana_Almeida_Carlos_Martins.pdf','Para al\xe9m da \u201cdifus\xe3o\u201d da Arquitetura Moderna Brasileira: um esfor\xe7o de categoriza\xe7\xe3o',[('Adriana Leal de','Almeida','UNICEP','adrianalalmeida@yahoo.com.br'),('Carlos A. Ferreira','Martins','IAU-USP','cmartins@sc.usp.br')]))
D.append((2,'02_Ana_Cristina_Castagna.pdf','Faculdade de Engenharia de Montevid\xe9u: um novo uso para a velha sala de m\xe1quinas',[('Ana Cristina','Castagna','',None)]))
D.append((3,'03_Andrea_Machado_Silvia_Correa_Angelina_Blomker_Adriana_Sabadi.pdf','Casa Curutchet: um mimo po\xe9tico de Le Corbusier \xe0 Am\xe9rica Latina',[('Andr\xe9a Soler','Machado','',None),('S\xedlvia','Corr\xeaa','',None),('Angelina','Bl\xf6mker','',None),('Adriana','Sabadi','',None)]))
D.append((4,'04_Betina_Martau_Fernando_Duro.pdf','Como qualificar sem descaracterizar: estudo de caso no edif\xedcio da Secretaria Municipal de Obras e Via\xe7\xe3o em Porto Alegre',[('Betina Tschiedel','Martau','',None),('Fernando Duro da','Silva','',None)]))
D.append((5,'05_Bruno_Braga.pdf','A flexibilidade como atributo da Arquitetura Moderna Brasileira e sua vig\xeancia na contemporaneidade',[('Bruno Melo','Braga','',None)]))
D.append((6,'06_Camila_Gonino_Ricardo_Silva.pdf','A preserva\xe7\xe3o do \u201cn\xe3o moderno\u201d como parte do processo de preserva\xe7\xe3o da cidade moderna: o caso de Maring\xe1, PR',[('Camila Thiemi Nakamura','Gonino','UEM','camila.nakamura@ymail.com'),('Ricardo Dias','Silva','UEM',None)]))
D.append((7,'07_Carlos_Castro.pdf','Paredes opacas carregadas. O retorno do limite \u201cn\xe3o moderno\u201d.',[('Carlos','Castro','',None)]))
D.append((8,'08_Carlos_Bahima.pdf','Cidade das Artes no Rio de Janeiro: combina\xe7\xf5es de elementos modernos em meio a distor\xe7\xf5es contempor\xe2neas',[('Carlos Fernando Silva','Bahima','',None)]))
D.append((9,'09_Claudia_stinco.pdf','Heran\xe7as na arquitetura de Vilamaj\xf3',[('Claudia Virginia','Stinco','',None)]))
D.append((10,'10_Daniel_Pitta_Fischmann-1.pdf','Heran\xe7a brutalista: a casa do arquiteto Edenor Buchholz em Porto Alegre',[('Daniel Pitta','Fischmann','',None)]))
D.append((11,'11_Diego_Soares.pdf','Viollet-le-Duc e a Villa Canoas',[('Diego Henrique de Oliveira','Soares','',None)]))
D.append((12,'12_Evelyn_Lima-1.pdf','A persist\xeancia da tradi\xe7\xe3o disciplinar moderna na arquitetura de Oscar Niemeyer para as artes performativas. O Teatro Popular Oscar Niemeyer em Niter\xf3i e o Teatro Raul Cortez em Duque de Caxias',[('Evelyn Furquim Werneck','Lima','UNIRIO','evelyn.lima@unirio.br')]))
D.append((13,'13_Fernanda_Voigt-1.pdf','Reciclagem na Arquitetura Moderna: o conjunto da Pampulha',[('Fernanda Royer','Voigt','',None)]))
D.append((14,'14_Gabriel_Kogan-1.pdf','Tr\xeas contradi\xe7\xf5es sobre a pr\xe1tica de preserva\xe7\xe3o: as interven\xe7\xf5es no edif\xedcio da FAU-USP entre 2007 e 2015',[('Gabriel','Kogan','','gabrielkogan@gmail.com')]))
D.append((15,'15_Humberto_Carta-1.pdf','Brutalismo demi-sec: Resid\xeancia M\xe1rio Petrelli',[('Humberto','Carta','',None)]))
D.append((16,'16_Juliano_Vasconcellos-1.pdf','Crusp e Colina: modula\xe7\xe3o e constru\xe7\xe3o em dois conjuntos residenciais pr\xe9-moldados',[('Juliano Caldas de','Vasconcellos','',None)]))
D.append((17,'17_Katia_Marchetto-1.pdf','Habitar o patrim\xf4nio moderno: o caso do Pedregulho',[('K\xe1tia F.','Marchetto','',None)]))
D.append((18,'18_Leandro_Marquetto_Janerson_Coelho-1.pdf','A materialidade na arquitetura de Eduardo de Almeida: Biblioteca Brasiliana: 2000/2013',[('Leandro Rahmeier','Marchetto','',None),('J\xe2nerson Figueira','Coelho','',None)]))
D.append((19,'19_Manuela_Catafesta-1.pdf','Heran\xe7a industrial moderna: o caso da F\xe1brica Olivetti',[('Manuela','Catafesta','',None)]))
D.append((20,'20_Marcelo_Felicetti-1.pdf','Sergio Bernardes, Bras\xedlia e o \u201cmilagre\u201d (1968/73). O experimentalismo dos projetos para o Instituto Brasileiro do Caf\xe9 \u2013 IBC e o Minist\xe9rio da Marinha \u2013 MM',[('Marcelo Augusto Felicetti da','Silva','',None)]))
D.append((21,'21_Marcelo_Puppi-1.pdf','Do imagin\xe1rio do s\xe9culo XIX ao imagin\xe1rio da arquitetura moderna: o caso da Casa Canoas',[('Marcelo','Puppi','',None)]))
D.append((22,'22_Marcos_Petroli-1.pdf','Banking architecture, late modernism and exposed concrete in Porto Alegre - Brazil',[('Marcos Amado','Petroli','','petrolim@ufl.edu')]))
D.append((23,'23_Marcos_Dornelles-1.pdf','Bernard Rudofsky: duas casas em S\xe3o Paulo, 1939-41',[('Marcos Dornelles dos','Santos','',None)]))
D.append((24,'24_Maria_Luiza_Freitas-1.pdf','Quando os fios se entrela\xe7am, se desenha a trama das constru\xe7\xf5es modernas',[('Maria Luiza Macedo Xavier de','Freitas','',None)]))
D.append((25,'25_Mariana_Jardim-1.pdf','O moderno \xe9 atual: o caso do Conjunto Residencial da Rua Gr\xe9cia',[('Mariana Comerlato','Jardim','',None)]))
D.append((26,'26_Markus_Tomaselli.pdf','Wiener Werkbundsiedlung: Vienna Housing Strategies after the Collapse of the Austrian Empire \u2013 Social Housing in Wien, 1920',[('Markus','Tomaselli','TU Wien','tomaselli@tuwien.ac.at')]))
D.append((27,'27_Nicolas_Palermo.pdf','Escolas modernas em S\xe3o Paulo: Passado e Presente. O FDE sob a \xf3tica das experi\xeancias de Rino Levi, Vilanova Artigas e Jo\xe3o Walter Toscano',[('Nicol\xe1s Sica','Palermo','UFRGS','nicolas.sica@ufrgs.br')]))
D.append((28,'28_Paula_Olivo.pdf','Hangar para o Aeroporto Nacional de Buenos Aires: como Pier Luigi Nervi tentou implantar seu sistema construtivo na Am\xe9rica do Sul',[('Paula Bem','Olivo','',None)]))
D.append((29,'29_Pauline_Felin_Monika_Stumpp.pdf','A Casa Varanda: reverbera\xe7\xe3o moderna na produ\xe7\xe3o contempor\xe2nea brasileira',[('Pauline Fonini','Felin','',None),('Monika Maria','Stumpp','',None)]))
D.append((30,'30_Rafael_Perrone_Simone_Neiva.pdf','Museu Oscar Niemeyer: o anexo como protagonista',[('Rafael Antonio Cunha','Perrone','FAU-USP','racperrone@gmail.com'),('Simone','Neiva','UVV','simoneiva@gmail.com')]))
D.append((31,'31_Rafael_Duarte.pdf','Esplanada ontem, hoje, amanh\xe3',[('Rafael Saldanha','Duarte','',None)]))
D.append((32,'32_Salvador_Gnoato.pdf','Uso e re-uso do Museu Oscar Niemeyer MON',[('Salvador','Gnoato','',None)]))
D.append((33,'33_Suelen_Camerin.pdf','Al\xe9m do tijolo em Solano Ben\xedtez',[('Suelen','Camerin','',None)]))
D.append((34,'34_Suely_Puppi.pdf','Lina Bo Bardi: de Salvador ao Benin',[('Suely de Oliveira Figueir\xeado','Puppi','',None)]))
D.append((35,'35_Tania_Verri_Renato_Anelli.pdf','Jaime Lerner em Maring\xe1: arquitetura e cidade',[('T\xe2nia Nunes Galv\xe3o','Verri','UEM','tngverri@gmail.com'),('Renato Luiz Sobral','Anelli','IAU-USP','renato.anelli@gmail.com')]))
D.append((36,'36_Thais_Luft.pdf','A perman\xeancia do transit\xf3rio: os pavilh\xf5es do Brasil e do Chile para a Expo 92 \u2013 Sevilha',[('Tha\xeds Luft da','Silva','',None)]))
D.append((37,'37_Vanessa_Rosa_Renato_Rego.pdf','Refer\xeancias da modernidade no edif\xedcio para a Biblioteca Municipal de Maring\xe1',[('Vanessa Calazans da','Rosa','',None),('Renato Le\xe3o','Rego','',None)]))

def get_full_text(fp):
    try: return subprocess.run(['pdftotext',fp,'-'],capture_output=True,text=True,timeout=60).stdout
    except: return ''

def get_page_count(fp):
    try:
        for l in subprocess.run(['pdfinfo',fp],capture_output=True,text=True,timeout=30).stdout.splitlines():
            if l.startswith('Pages:'): return int(l.split(':')[1].strip())
    except: pass
    return None

def extract_references(text):
    m = re.search(r'REFER\xcanCIAS|REFERENCIAS|BIBLIOGRAPHY|REFERENCES|NOTAS\s+E\s+REFER\xcanCIAS', text, re.IGNORECASE)
    if not m: return []
    refs, cur = [], ''
    for l in text[m.end():].strip().split('\n'):
        l = l.strip()
        if not l:
            if cur: refs.append(cur.strip()); cur = ''
            continue
        if re.match(r'^(ANEXO|AP\xcanDICE)', l, re.IGNORECASE): break
        if re.match(r'^[A-Z\xc0-\xd6]{2,}[,.]', l) or re.match(r'^\d+[\.\)]\s', l):
            if cur: refs.append(cur.strip())
            cur = l
        elif re.match(r'^_+', l):
            if cur: refs.append(cur.strip())
            cur = l
        else: cur += ' ' + l
    if cur: refs.append(cur.strip())
    return [re.sub(r'\s+',' ',r).strip() for r in refs if len(r.strip())>15 and not r.strip().startswith('http')]

def extract_meta(fp):
    try: text = subprocess.run(['pdftotext','-f','1','-l','3',fp,'-'],capture_output=True,text=True,timeout=60).stdout
    except: return {}
    meta = {}
    m = re.search(r'(?:^|\n)\s*Resumo:?\s*\n?', text, re.IGNORECASE)
    if m:
        after = text[m.end():]
        e = re.search(r'\n\s*(Palavras[\s-]*chave|Keywords?|Abstract|ABSTRACT|Resumen)', after, re.IGNORECASE)
        t = re.sub(r'\s+',' ',(after[:e.start()] if e else after[:2000]).strip()).strip()
        if len(t)>50: meta['abstract'] = t
    m = re.search(r'(?:^|\n)\s*Abstract:?\s*\n?', text, re.IGNORECASE)
    if m:
        after = text[m.end():]
        e = re.search(r'\n\s*(Keywords?|Palavras[\s-]*chave|Resumen)', after, re.IGNORECASE)
        t = re.sub(r'\s+',' ',(after[:e.start()] if e else after[:2000]).strip()).strip()
        if len(t)>50: meta['abstract_en'] = t
    m = re.search(r'(?:^|\n)\s*Palavras[\s-]*chave[s]?\s*:?\s*', text, re.IGNORECASE)
    if m:
        after = text[m.end():]
        e = re.search(r'\n\s*\n|\n\s*(Abstract|ABSTRACT|Keywords?|Resumen|\d+\.?\s)', after, re.IGNORECASE)
        t = re.sub(r'\s+',' ',(after[:e.start()] if e else after[:500]).strip()).strip().rstrip('.')
        kw = [k.strip().rstrip('.') for k in (t.split(';') if ';' in t else t.split(',')) if k.strip()]
        kw = [k for k in kw if len(k)>1]
        if kw: meta['keywords'] = kw
    m = re.search(r'(?:^|\n)\s*Keywords?\s*:?\s*', text, re.IGNORECASE)
    if m:
        after = text[m.end():]
        e = re.search(r'\n\s*\n|\n\s*(Palavras|Resumo|Resumen|\d+\.?\s)', after, re.IGNORECASE)
        t = re.sub(r'\s+',' ',(after[:e.start()] if e else after[:500]).strip()).strip().rstrip('.')
        kw = [k.strip().rstrip('.') for k in (t.split(';') if ';' in t else t.split(',')) if k.strip()]
        kw = [k for k in kw if len(k)>1]
        if kw: meta['keywords_en'] = kw
    return meta

def detect_locale(title):
    tl = title.lower().split()
    if sum(1 for w in ['banking','architecture','late','exposed','concrete','vienna','housing','strategies','after','collapse','social','the','and'] if w in tl) >= 3: return 'en'
    return 'pt-BR'

def rm_acc(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c))

print("="*60+"\nETAPA 1: Construir YAML\n"+"="*60)
articles = []
for num, orig, full_title, auth_raw in D:
    aid = f'sdsul05-{num:03d}'
    if ': ' in full_title:
        p = full_title.split(': ',1); ti,su = p[0],p[1]
    elif '. O ' in full_title and full_title.index('. O ')>10:
        i = full_title.index('. O '); ti,su = full_title[:i],full_title[i+2:]
    else: ti,su = full_title,None
    loc = detect_locale(full_title)
    auths = []
    for i,(g,f,af,em) in enumerate(auth_raw):
        if em is None: em = rm_acc(f.lower()).replace(' ','')+'@exemplo.com'
        auths.append({'givenname':g,'familyname':f,'affiliation':af,'email':em,'primary_contact':i==0})
    a = {'id':aid,'title':ti}
    if su: a['subtitle'] = su
    a['authors'] = auths
    a['section'] = 'Artigos'
    a['locale'] = loc
    a['file'] = f'{aid}.pdf'
    a['file_original'] = orig
    a['abstract'] = None
    a['abstract_en'] = None
    a['keywords'] = []
    a['keywords_en'] = []
    a['references'] = []
    a['pages_count'] = None
    articles.append(a)
print(f"  {len(articles)} artigos")
lc = {}
for a in articles: lc[a['locale']]=lc.get(a['locale'],0)+1
for l,c in sorted(lc.items()): print(f"  {l}: {c}")

print("\n"+"="*60+"\nETAPA 2: Renomear PDFs\n"+"="*60)
ok=0
for a in articles:
    o = os.path.join(PDFS,a['file_original'])
    d = os.path.join(PDFS,a['file'])
    if os.path.exists(d): ok+=1; continue
    if os.path.exists(o): shutil.copy2(o,d); print(f"  {a['file_original']} -> {a['file']}"); ok+=1
    else: print(f"  ERRO: {a['file_original']}")
print(f"  {ok}/{len(articles)} ok")

print("\n"+"="*60+"\nETAPA 3-4: Extrair metadados\n"+"="*60)
stats = dict.fromkeys(['abstract','abstract_en','keywords','keywords_en','references','pages_count'],0)
for a in articles:
    fp = os.path.join(PDFS,a['file'])
    if not os.path.exists(fp): print(f"  WARN: {fp}"); continue
    pc = get_page_count(fp)
    if pc: a['pages_count']=pc; stats['pages_count']+=1
    meta = extract_meta(fp)
    for k in ['abstract','abstract_en','keywords','keywords_en']:
        if meta.get(k): a[k]=meta[k]; stats[k]+=1
    refs = extract_references(get_full_text(fp))
    if refs: a['references']=refs; stats['references']+=1
    print(f"  {a['id']}: res={'S' if a['abstract'] else 'N'} abs={'S' if a['abstract_en'] else 'N'} kw={len(a['keywords'])} kw_en={len(a.get('keywords_en',[]))} refs={len(refs)} pgs={pc}")

print("\n"+"="*60+"\nETAPA 5: Gravar YAML\n"+"="*60)
with open(YAML_OUT,'w',encoding='utf-8') as f:
    yaml.dump({'issue':issue,'articles':articles},f,Dumper=OrderedDumper,width=10000,sort_keys=False,allow_unicode=True,default_flow_style=False)
print(f"  {YAML_OUT}")

print("\n"+"="*60+"\nRESUMO FINAL\n"+"="*60)
print(f"  Total: {len(articles)}")
for k in ['abstract','abstract_en','keywords','keywords_en','references','pages_count']:
    print(f"  {k}: {stats[k]}/{len(articles)}")
ms=[a['id'] for a in articles if not a.get('abstract')]
if ms: print(f"  Sem resumo ({len(ms)}): {', '.join(ms)}")
mk=[a['id'] for a in articles if not a.get('keywords')]
if mk: print(f"  Sem keywords ({len(mk)}): {', '.join(mk)}")
