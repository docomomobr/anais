#!/usr/bin/env python3
"""
Cria o banco dict.db com schema e entradas manuais iniciais.

Categorias:
- sigla:     sempre MAIÚSCULA (BNH, USP, IPHAN)
- nome:      capitalizado (Niemeyer, Brasília)
- lugar:     capitalizado (Fortaleza, Bahia)
- area:      capitalizado (Arquitetura, Urbanismo)
- movimento: capitalizado (Modernismo, Art Déco)
- expressao: forma canônica multi-palavra (Patrimônio Moderno, João Pessoa)

Uso:
    python3 dict/init_db.py [--reset]
"""

import argparse
import os
import sqlite3

DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DIR, 'dict.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS dict_names (
    word TEXT PRIMARY KEY,
    category TEXT NOT NULL CHECK (category IN ('sigla','nome','lugar','area','movimento','expressao','toponimico')),
    canonical TEXT NOT NULL,
    source TEXT DEFAULT 'manual'
);
CREATE INDEX IF NOT EXISTS idx_dict_category ON dict_names(category);
"""

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  ATENÇÃO: Todos os dados de dicionário devem ser definidos AQUI    ║
# ║  (e gravados no dict.db). NUNCA adicionar listas de nomes,        ║
# ║  siglas, lugares, movimentos ou toponímicos diretamente no         ║
# ║  código dos scripts (normalizar.py, normalizar_maiusculas.py).     ║
# ║  Os scripts leem TUDO do banco.                                    ║
# ╚══════════════════════════════════════════════════════════════════════╝

# ── Entradas manuais iniciais ──────────────────────────────────────────

SIGLAS = [
    'ABI', 'ABNT', 'ANCAP', 'BANESPA', 'BB', 'BIM', 'BNB', 'BNDES', 'BNH',
    'BRT', 'CAP', 'CAU', 'CDHU', 'CEF', 'CHESF', 'CIAM', 'COHAB', 'CREA',
    'CRUSP', 'CUCA', 'DHP', 'DNOCS', 'DOCOMOMO', 'DOP', 'DPHAN', 'EBSERH',
    'EFL', 'EMURB', 'ENBA', 'EPRN', 'ESAL', 'FAU', 'FAUUSP', 'FDE', 'FGTS',
    'FIESP', 'FUNAI', 'FUNARTE', 'FUNDAJ', 'HIG', 'IAB', 'IAU', 'IBGE',
    'IBPC', 'ICOMOS', 'IESP', 'INSS', 'IPEN', 'IPHAN', 'IPHAE', 'IPT',
    'ITEP', 'MEC', 'MESP', 'MST', 'NOVACAP', 'OJS', 'PAC', 'PUC', 'SBPC',
    'SENAC', 'SENAI', 'SESC', 'SESI', 'SIG', 'SPHAN', 'SUDENE', 'UFAL',
    'UFBA', 'UFC', 'UFCG', 'UFES', 'UFF', 'UFG', 'UFJF', 'UFMA', 'UFMG',
    'UFMS', 'UFMT', 'UFOP', 'UFPA', 'UFPB', 'UFPE', 'UFPI', 'UFPR', 'UFRGS',
    'UFRJ', 'UFRN', 'UFSC', 'UFSCAR', 'UFSM', 'UFT', 'UFU', 'UFV',
    'UNB', 'UNDB', 'UNESP', 'UNICAMP', 'UNICAP', 'UNICEP', 'UNIFACISA',
    'UNILA', 'UNIMEP', 'UNIP', 'UNISINOS', 'UNIVASF', 'UPM', 'USP',
    'VANT', 'ZEIS',
    # UFs brasileiras
    'AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 'MS',
    'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 'RS', 'SC',
    'SE', 'SP', 'TO',
    # Romanos comuns
    'II', 'III', 'IV', 'VI', 'VII', 'VIII', 'IX', 'XI', 'XII', 'XIII', 'XIV',
    'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX', 'XXI',
    # Outros
    'ABEA', 'ANTAC', 'CBCM', 'PPGAU', 'PROARQ', 'PROPAR', 'PROURB',
    'SBPJor', 'TICCIH', 'UNESCO',
]

AREAS = {
    'arquitetura': 'Arquitetura',
    'engenharia': 'Engenharia',
    'geografia': 'Geografia',
    'história': 'História',
    'sociologia': 'Sociologia',
    'urbanismo': 'Urbanismo',
}

MOVIMENTOS = {
    'art déco': 'Art Déco',
    'art nouveau': 'Art Nouveau',
    'bauhaus': 'Bauhaus',
    'brutalismo': 'Brutalismo',
    'classicismo': 'Classicismo',
    'concretismo': 'Concretismo',
    'construtivismo': 'Construtivismo',
    'ecletismo': 'Ecletismo',
    'expressionismo': 'Expressionismo',
    'funcionalismo': 'Funcionalismo',
    'futurismo': 'Futurismo',
    'higienismo': 'Higienismo',
    'modernidade': 'Modernidade',
    'modernismo': 'Modernismo',
    'neoconcretismo': 'Neoconcretismo',
    'neoclassicismo': 'Neoclassicismo',
    'neoclássico': 'Neoclássico',
    'pós-modernismo': 'Pós-Modernismo',
    'racionalismo': 'Racionalismo',
    'renascimento': 'Renascimento',
    'tropicalismo': 'Tropicalismo',
    'vanguarda': 'Vanguarda',
}

LUGARES = {
    'alagoas': 'Alagoas', 'amazônia': 'Amazônia', 'amazonas': 'Amazonas',
    'amapá': 'Amapá', 'bahia': 'Bahia', 'belém': 'Belém', 'brasília': 'Brasília',
    'campinas': 'Campinas', 'ceará': 'Ceará', 'curitiba': 'Curitiba',
    'espírito': 'Espírito', 'florianópolis': 'Florianópolis',
    'fortaleza': 'Fortaleza', 'goiânia': 'Goiânia', 'goiás': 'Goiás',
    'manaus': 'Manaus', 'maranhão': 'Maranhão', 'minas': 'Minas',
    'natal': 'Natal', 'niterói': 'Niterói', 'nordeste': 'Nordeste',
    'norte': 'Norte', 'olinda': 'Olinda', 'palmas': 'Palmas', 'paraíba': 'Paraíba',
    'paraná': 'Paraná', 'pará': 'Pará', 'pernambuco': 'Pernambuco',
    'piauí': 'Piauí', 'recife': 'Recife', 'rio': 'Rio',
    'salvador': 'Salvador', 'santos': 'Santos', 'sergipe': 'Sergipe',
    'sudeste': 'Sudeste', 'sul': 'Sul', 'teresina': 'Teresina',
    'tocantins': 'Tocantins', 'uberlândia': 'Uberlândia', 'viçosa': 'Viçosa',
    'acre': 'Acre', 'aracaju': 'Aracaju', 'belo': 'Belo',
    'campina': 'Campina', 'caxias': 'Caxias', 'centro-oeste': 'Centro-Oeste',
    'chapecó': 'Chapecó', 'ceilândia': 'Ceilândia',
    'copacabana': 'Copacabana', 'cuiabá': 'Cuiabá',
    'horizonte': 'Horizonte', 'ipanema': 'Ipanema',
    'itajaí': 'Itajaí', 'joinville': 'Joinville',
    'londrina': 'Londrina', 'macapá': 'Macapá', 'maceió': 'Maceió',
    'maringá': 'Maringá', 'mariana': 'Mariana',
    'pelotas': 'Pelotas', 'petrolina': 'Petrolina', 'petrópolis': 'Petrópolis',
    'piracicaba': 'Piracicaba', 'rondônia': 'Rondônia', 'roraima': 'Roraima',
    'santa': 'Santa', 'catarina': 'Catarina',
    'grande': 'Grande', 'são': 'São', 'luís': 'Luís',
    'alegre': 'Alegre', 'carlos': 'Carlos', 'paulo': 'Paulo',
    'pedro': 'Pedro', 'josé': 'José',
    'vitória': 'Vitória',
    'pampulha': 'Pampulha', 'pedregulho': 'Pedregulho',
    'leme': 'Leme', 'leblon': 'Leblon', 'lapa': 'Lapa',
    'guarulhos': 'Guarulhos', 'osasco': 'Osasco', 'sorocaba': 'Sorocaba',
    'ribeirão': 'Ribeirão', 'preto': 'Preto',
    'juiz': 'Juiz', 'fora': 'Fora',
    'feira': 'Feira', 'santana': 'Santana',
    'taguatinga': 'Taguatinga', 'sobradinho': 'Sobradinho',
    'ibirapuera': 'Ibirapuera', 'ipiranga': 'Ipiranga',
    'tijuca': 'Tijuca', 'botafogo': 'Botafogo', 'flamengo': 'Flamengo',
    'gavea': 'Gávea', 'gávea': 'Gávea',
    'laranjeiras': 'Laranjeiras', 'catete': 'Catete',
    'glória': 'Glória', 'méier': 'Méier',
    'jacarepaguá': 'Jacarepaguá',
    'paraíso': 'Paraíso', 'higienópolis': 'Higienópolis',
    'consolação': 'Consolação', 'perdizes': 'Perdizes',
    'pinheiros': 'Pinheiros', 'pacaembu': 'Pacaembu',
    'penha': 'Penha', 'mooca': 'Mooca',
    'serra': 'Serra',
    'argentina': 'Argentina', 'chile': 'Chile', 'colômbia': 'Colômbia',
    'cuba': 'Cuba', 'méxico': 'México', 'paraguai': 'Paraguai',
    'peru': 'Peru', 'uruguai': 'Uruguai', 'venezuela': 'Venezuela',
    'portugal': 'Portugal', 'espanha': 'Espanha', 'itália': 'Itália',
    'frança': 'França', 'alemanha': 'Alemanha', 'inglaterra': 'Inglaterra',
    'japão': 'Japão', 'áfrica': 'África', 'europa': 'Europa',
    'américa': 'América', 'ásia': 'Ásia',
}

# Adjetivos pátrios/toponímicos — capitalizados APENAS quando seguem
# movimento, área ou expressão consolidada (ex: "Brutalismo Paulista").
# Quando isolados, ficam em minúscula (ex: "a cultura paulista").
# A lógica contextual está em normalizar.py.
TOPONIMICOS = {
    # Brasil e regiões
    'brasileira': 'Brasileira', 'brasileiro': 'Brasileiro',
    'brasileiras': 'Brasileiras', 'brasileiros': 'Brasileiros',
    'nortista': 'Nortista', 'nortistas': 'Nortistas',
    'nordestina': 'Nordestina', 'nordestino': 'Nordestino',
    'nordestinas': 'Nordestinas', 'nordestinos': 'Nordestinos',
    'sulista': 'Sulista', 'sulistas': 'Sulistas',
    # Estados
    'acreana': 'Acreana', 'acreano': 'Acreano',
    'alagoana': 'Alagoana', 'alagoano': 'Alagoano',
    'amapaense': 'Amapaense', 'amapaenses': 'Amapaenses',
    'amazonense': 'Amazonense', 'amazonenses': 'Amazonenses',
    'amazônica': 'Amazônica', 'amazônico': 'Amazônico',
    'amazônicas': 'Amazônicas', 'amazônicos': 'Amazônicos',
    'baiana': 'Baiana', 'baiano': 'Baiano',
    'baianas': 'Baianas', 'baianos': 'Baianos',
    'brasiliense': 'Brasiliense', 'brasilienses': 'Brasilienses',
    'capixaba': 'Capixaba', 'capixabas': 'Capixabas',
    'catarinense': 'Catarinense', 'catarinenses': 'Catarinenses',
    'cearense': 'Cearense', 'cearenses': 'Cearenses',
    'fluminense': 'Fluminense', 'fluminenses': 'Fluminenses',
    'goiana': 'Goiana', 'goiano': 'Goiano',
    'goianas': 'Goianas', 'goianos': 'Goianos',
    'maranhense': 'Maranhense', 'maranhenses': 'Maranhenses',
    'mato-grossense': 'Mato-Grossense',
    'matogrossense': 'Matogrossense',
    'sul-mato-grossense': 'Sul-Mato-Grossense',
    'mineira': 'Mineira', 'mineiro': 'Mineiro',
    'mineiras': 'Mineiras', 'mineiros': 'Mineiros',
    'paraense': 'Paraense', 'paraenses': 'Paraenses',
    'paraibana': 'Paraibana', 'paraibano': 'Paraibano',
    'paranaense': 'Paranaense', 'paranaenses': 'Paranaenses',
    'paulista': 'Paulista', 'paulistas': 'Paulistas',
    'pernambucana': 'Pernambucana', 'pernambucano': 'Pernambucano',
    'pernambucanas': 'Pernambucanas', 'pernambucanos': 'Pernambucanos',
    'piauiense': 'Piauiense', 'piauienses': 'Piauienses',
    'potiguar': 'Potiguar', 'potiguares': 'Potiguares',
    'rondoniense': 'Rondoniense', 'roraimense': 'Roraimense',
    'sergipana': 'Sergipana', 'sergipano': 'Sergipano',
    'tocantinense': 'Tocantinense', 'tocantinenses': 'Tocantinenses',
    # Capitais e cidades
    'belorizontina': 'Belorizontina', 'belorizontino': 'Belorizontino',
    'belenense': 'Belenense', 'belenenses': 'Belenenses',
    'campineira': 'Campineira', 'campineiro': 'Campineiro',
    'carioca': 'Carioca', 'cariocas': 'Cariocas',
    'cuiabana': 'Cuiabana', 'cuiabano': 'Cuiabano',
    'curitibana': 'Curitibana', 'curitibano': 'Curitibano',
    'florianopolitana': 'Florianopolitana', 'florianopolitano': 'Florianopolitano',
    'fortalezense': 'Fortalezense', 'fortalezenses': 'Fortalezenses',
    'ludovicense': 'Ludovicense', 'ludovicenses': 'Ludovicenses',
    'macapaense': 'Macapaense',
    'manauara': 'Manauara', 'manauaras': 'Manauaras',
    'natalense': 'Natalense', 'natalenses': 'Natalenses',
    'palmense': 'Palmense', 'palmenses': 'Palmenses',
    'paulistana': 'Paulistana', 'paulistano': 'Paulistano',
    'paulistanas': 'Paulistanas', 'paulistanos': 'Paulistanos',
    'portoalegrense': 'Portoalegrense', 'porto-alegrense': 'Porto-Alegrense',
    'recifense': 'Recifense', 'recifenses': 'Recifenses',
    'soteropolitana': 'Soteropolitana', 'soteropolitano': 'Soteropolitano',
    'teresinense': 'Teresinense', 'teresinenses': 'Teresinenses',
    'uberlandense': 'Uberlandense',
    # Países
    'alemã': 'Alemã', 'alemão': 'Alemão', 'alemãs': 'Alemãs', 'alemães': 'Alemães',
    'argentina': 'Argentina', 'argentino': 'Argentino',
    'argentinas': 'Argentinas', 'argentinos': 'Argentinos',
    'chilena': 'Chilena', 'chileno': 'Chileno',
    'colombiana': 'Colombiana', 'colombiano': 'Colombiano',
    'cubana': 'Cubana', 'cubano': 'Cubano',
    'espanhola': 'Espanhola', 'espanhol': 'Espanhol',
    'francesa': 'Francesa', 'francês': 'Francês',
    'holandesa': 'Holandesa', 'holandês': 'Holandês',
    'inglesa': 'Inglesa', 'inglês': 'Inglês',
    'italiana': 'Italiana', 'italiano': 'Italiano',
    'japonesa': 'Japonesa', 'japonês': 'Japonês',
    'mexicana': 'Mexicana', 'mexicano': 'Mexicano',
    'paraguaia': 'Paraguaia', 'paraguaio': 'Paraguaio',
    'peruana': 'Peruana', 'peruano': 'Peruano',
    'portuguesa': 'Portuguesa', 'português': 'Português',
    'uruguaia': 'Uruguaia', 'uruguaio': 'Uruguaio',
    'venezuelana': 'Venezuelana', 'venezuelano': 'Venezuelano',
    # Continentes
    'africana': 'Africana', 'africano': 'Africano',
    'americana': 'Americana', 'americano': 'Americano',
    'americanas': 'Americanas', 'americanos': 'Americanos',
    'asiática': 'Asiática', 'asiático': 'Asiático',
    'europeia': 'Europeia', 'europeu': 'Europeu',
    'europeias': 'Europeias', 'europeus': 'Europeus',
    # Compostos
    'latino-americana': 'Latino-Americana', 'latino-americano': 'Latino-Americano',
    'latino-americanas': 'Latino-Americanas', 'latino-americanos': 'Latino-Americanos',
    'ibero-americana': 'Ibero-Americana', 'ibero-americano': 'Ibero-Americano',
    'luso-brasileira': 'Luso-Brasileira', 'luso-brasileiro': 'Luso-Brasileiro',
    'sul-americana': 'Sul-Americana', 'sul-americano': 'Sul-Americano',
}

EXPRESSOES = {
    'arquitetura moderna': 'Arquitetura Moderna',
    'arquitetura contemporânea': 'Arquitetura Contemporânea',
    'art déco': 'Art Déco',
    'art nouveau': 'Art Nouveau',
    'base aérea': 'Base Aérea',
    'bo bardi': 'Bo Bardi',
    'boa vista': 'Boa Vista',
    'buenos aires': 'Buenos Aires',
    'cabo branco': 'Cabo Branco',
    'campina grande': 'Campina Grande',
    'cidade jardim': 'Cidade Jardim',
    'cidade moderna': 'Cidade Moderna',
    'centro cultural': 'Centro Cultural',
    'centro de exportadores': 'Centro de Exportadores',
    'centro de saúde': 'Centro de Saúde',
    'centro histórico': 'Centro Histórico',
    'centro oeste': 'Centro-Oeste',
    'chapéu de palha': 'Chapéu de Palha',
    'cine são luiz': 'Cine São Luiz',
    'delta do jacuí': 'Delta do Jacuí',
    'duque de caxias': 'Duque de Caxias',
    'educação patrimonial': 'Educação Patrimonial',
    'escola carioca': 'Escola Carioca',
    'escola do recife': 'Escola do Recife',
    'escola paulista': 'Escola Paulista',
    'estação ferroviária': 'Estação Ferroviária',
    'estação nova': 'Estação Nova',
    'guerra mundial': 'Guerra Mundial',
    'hospital universitário': 'Hospital Universitário',
    'hotel internacional': 'Hotel Internacional',
    'joão pessoa': 'João Pessoa',
    'juazeiro do norte': 'Juazeiro do Norte',
    'kneese de mello': 'Kneese de Mello',
    'le corbusier': 'Le Corbusier',
    'mato grosso': 'Mato Grosso',
    'minha casa minha vida': 'Minha Casa Minha Vida',
    'modernização brasileira': 'Modernização Brasileira',
    'movimento moderno': 'Movimento Moderno',
    'nossa senhora': 'Nossa Senhora',
    'nova friburgo': 'Nova Friburgo',
    'ouro preto': 'Ouro Preto',
    'patrimônio cultural': 'Patrimônio Cultural',
    'paisagem cultural': 'Paisagem Cultural',
    'paisagem urbana': 'Paisagem Urbana',
    'paisagismo moderno': 'Paisagismo Moderno',
    'patrimônio arquitetônico': 'Patrimônio Arquitetônico',
    'patrimônio edificado': 'Patrimônio Edificado',
    'patrimônio histórico': 'Patrimônio Histórico',
    'patrimônio industrial': 'Patrimônio Industrial',
    'patrimônio moderno': 'Patrimônio Moderno',
    'plano piloto': 'Plano Piloto',
    'porto alegre': 'Porto Alegre',
    'pouso alegre': 'Pouso Alegre',
    'rio branco': 'Rio Branco',
    'rio de janeiro': 'Rio de Janeiro',
    'rio grande': 'Rio Grande',
    'santo andré': 'Santo André',
    'são carlos': 'São Carlos',
    'são luís': 'São Luís',
    'são paulo': 'São Paulo',
    'são pedro': 'São Pedro',
    'são josé': 'São José',
    'serra do navio': 'Serra do Navio',
    'urbanismo moderno': 'Urbanismo Moderno',
    'viña del mar': 'Viña del Mar',
    'vila amazonas': 'Vila Amazonas',
    'vila serra do navio': 'Vila Serra do Navio',
}


def init_db(reset=False):
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    def upsert(word, category, canonical, source='manual'):
        conn.execute(
            'INSERT OR REPLACE INTO dict_names (word, category, canonical, source) '
            'VALUES (?, ?, ?, ?)',
            (word, category, canonical, source))

    # Siglas
    for s in SIGLAS:
        upsert(s.lower(), 'sigla', s.upper(), 'manual')

    # Áreas
    for word, canonical in AREAS.items():
        upsert(word, 'area', canonical, 'manual')

    # Movimentos
    for word, canonical in MOVIMENTOS.items():
        upsert(word, 'movimento', canonical, 'manual')

    # Lugares
    for word, canonical in LUGARES.items():
        upsert(word, 'lugar', canonical, 'manual')

    # Toponímicos
    for word, canonical in TOPONIMICOS.items():
        upsert(word, 'toponimico', canonical, 'manual')

    # Expressões
    for word, canonical in EXPRESSOES.items():
        upsert(word, 'expressao', canonical, 'manual')

    conn.commit()

    # Stats
    for cat, in conn.execute('SELECT DISTINCT category FROM dict_names ORDER BY category'):
        n = conn.execute('SELECT COUNT(*) FROM dict_names WHERE category=?', (cat,)).fetchone()[0]
        print(f'  {cat}: {n}')
    total = conn.execute('SELECT COUNT(*) FROM dict_names').fetchone()[0]
    print(f'  TOTAL: {total}')

    conn.close()
    print(f'\n→ {DB_PATH}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Inicializar dict.db')
    parser.add_argument('--reset', action='store_true', help='Recriar do zero')
    args = parser.parse_args()
    init_db(reset=args.reset)
