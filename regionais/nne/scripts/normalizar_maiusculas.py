#!/usr/bin/env python3
"""
Normaliza maiúsculas/minúsculas nos títulos e subtítulos conforme FUNAG.
Adaptado para YAMLs consolidados dos seminários regionais N/NE.

Regras:
- Tudo minúscula, exceto:
  - Primeira letra do título: maiúscula
  - Primeira letra do subtítulo: minúscula (regra FUNAG)
  - Siglas: maiúsculas (BNH, USP, IPHAN)
  - Nomes próprios: capitalizado (Niemeyer, Brasília, Pedregulho)
  - Disciplinas/áreas do saber: Maiúscula (Arquitetura, Urbanismo)
  - Movimentos/períodos: Maiúscula (Modernismo, Art Déco)
"""

import yaml
import re
from pathlib import Path

BASE = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/nne")

# Siglas (sempre maiúsculas)
SIGLAS = {
    'bnh', 'iphan', 'sphan', 'dphan', 'ufmg', 'usp', 'ufrj', 'unb', 'ufba',
    'ufrgs', 'ufpe', 'ufrn', 'ufc', 'ufpb', 'ufpr', 'ufsc', 'ufu', 'ufg',
    'ufmt', 'ufam', 'ufcg', 'ufrr', 'ufma', 'ufpi', 'ufpa', 'uft', 'ufal',
    'unifap', 'undb', 'uema', 'unipê',
    'iab', 'cau', 'crea', 'mes', 'mesp', 'dop', 'iap', 'iaps', 'fcp', 'dhp',
    'sfh', 'fgts', 'inocoop', 'cohab', 'cdhu', 'sudene', 'chesf', 'dnocs',
    'novacap', 'epucs', 'ciam', 'uia', 'docomomo', 'unesco', 'onu',
    'masp', 'mam', 'mac', 'moma',
    'abi', 'oab', 'senai', 'sesi', 'senac', 'sesc',
    'puc', 'faap', 'fau', 'fauusp', 'faufba', 'ead', 'eesc',
    'ibge', 'ibama', 'incra', 'inss', 'cef', 'bb', 'bndes', 'bnb', 'banespa',
    'df', 'rj', 'sp', 'mg', 'ba', 'pe', 'ce', 'rs', 'pr', 'sc', 'go', 'mt',
    'ms', 'pa', 'am', 'ma', 'pi', 'rn', 'pb', 'al', 'se', 'es', 'to', 'ro',
    'ac', 'ap', 'rr',
    'eua', 'usa', 'uk', 'urss', 'upc',
    'gt', 'ii', 'iii', 'iv', 'xx', 'xxi', 'xix', 'xviii', 'xvii', 'xvi',
    'us', 'mapi', 'tfa', 'vant', 'cuca', 'lic',
    'pmcmv',
    # Institutos e órgãos
    'iapi', 'iapc', 'ibc', 'iab', 'sbpc', 'fumest',
    # Edifícios e conjuntos
    'crusp', 'maesa', 'iceia', 'sqs', 'ibit',
    # Empresas e organizações
    'texaco', 'ancap', 'ucovi',
    # Tecnologia e sistemas
    'bim', 'brt',
    # Universidades e escolas
    'ufsm', 'fabico', 'fde',
    # Outros
    'mmm', 'ee', 'jk', 'cap', 'mon', 'fam', 'efsc', 'f1', 'mm',
}

# Nomes próprios (capitalizar)
NOMES_PROPRIOS = {
    # Arquitetos brasileiros
    'niemeyer', 'lucio', 'lúcio', 'costa', 'reidy', 'affonso', 'burle', 'marx',
    'artigas', 'vilanova', 'rocha', 'lina', 'bardi', 'warchavchik', 'bratke',
    'oswaldo', 'mindlin', 'lelé', 'filgueiras', 'borsoi', 'delfim', 'amorim',
    'heitor', 'maia', 'neto', 'attílio', 'bolonha', 'aldary', 'toledo',
    'leão', 'graeff', 'cardozo', 'portinari', 'giorgi', 'tenreiro',
    'campolina', 'schwab', 'zein', 'ficher', 'segawa', 'bruand', 'chacel',
    'carvalho', 'flávio', 'mauro', 'peixoto', 'coury',
    'elgson', 'ribeiro', 'gomes', 'heep', 'petrônio', 'cunha', 'lima',
    'severiano', 'porto',
    'ohtake', 'ruy',
    'acácio', 'gil',
    'bernardes', 'sérgio', 'sergio',
    'clorindo', 'testa',
    'duda',
    'bina', 'fonyat',
    'tarsila',
    'glauber',
    # Arquitetos — SP e regionais
    'levi', 'rino', 'eduardo', 'kneese', 'mello',
    'pilon', 'broos', 'franz', 'libeskind',
    'gregori', 'gregório', 'zolko', 'toscano',
    'joaquim', 'liliana', 'guedes', 'mendes', 'andrade',
    'gastão', 'caron', 'miranda', 'alcides', 'sanovicz',
    'hans', 'christiano', 'neves', 'penteado',
    'barbosa', 'santoro', 'palanti', 'marcello', 'fragelli',
    'gilioli', 'ubyrajara', 'odiléa',
    'ferraz', 'millan', 'zanuso',
    # Arquitetos — Sul e Rio da Prata
    'bonet', 'fayet', 'gandolfi', 'vilamajó', 'linzmeyer', 'leo',
    # Arquitetos — N/NE
    'vital', 'modesto', 'david', 'zélia', 'nobre', 'furtado',
    'palumbo', 'athos', 'bulcão', 'hélio', 'duarte',
    'geraldo', 'santana', 'césar', 'milton', 'wallig',
    'pedrosa', 'cleon', 'arialdo', 'pinho', 'alcyr', 'meira',
    'kátia', 'pinto', 'sebastião', 'lins',
    # Arquitetos — RJ
    'moreira', 'arthur', 'soares', 'lota', 'portinho',
    'machado', 'neiva',
    # Arquitetos estrangeiros
    'corbusier', 'mies', 'rohe', 'gropius', 'wright', 'aalto', 'kahn', 'koenig',
    'marius', 'duintjer', 'schiphol',
    'nicia', 'bormann', 'nélida', 'nélia', 'romero',
    'perret', 'piacentini', 'capua',
    'irace', 'otaegui',
    # Industriais e personalidades
    'olivetti', 'ciccillo', 'matarazzo', 'abramo', 'eberle',
    # Políticos
    'kubitschek', 'juscelino', 'vargas', 'getúlio', 'capanema', 'gustavo',
    'janary', 'nunes', 'sarney',
    'kennedy',
    # Outros nomes relevantes
    'reginaldo', 'esteves',
    'amaro', 'fiuza', 'fiúza',
    'freitas', 'diniz',
    'douglas', 'meier', 'richard',
    'maria', 'joaquina', 'aragão',
    'judah', 'levy',
    'oscar', 'pereira',
    'padre', 'cícero',
    'lourdes', 'ramalho',
    'isaías', 'alves',
    'reis', 'magos',
    'espinoso', 'julio',
    'dória',
    'braga',
    'macedo',
    'amaral',
    'antunes',
    'raul', 'cirne',
    'paes', 'nícia',
    'roberto', 'castelo',
    'ramos', 'dutra',
    'pedro', 'dora',
    'alberto', 'carlos',
    'josé', 'jorge',
    'rodrigues', 'souza', 'almeida', 'longo', 'severo', 'fonseca', 'marcos',
    'francisco', 'batista', 'maurício', 'melo', 'magalhães',
    'virzi', 'félix',
    'giacomo', 'dico',
    'beckenkamp', 'kormann',
    # sdnne05
    'armando', 'holanda', 'cavalcanti', 'neudson',
    'antônio', 'antonio', 'araújo', 'araujo',
    'wandenkolk', 'tinoco',
    'miguel', 'caddah',
    'diógenes', 'rebouças',
    'ernani', 'henrique',
    'claudio', 'cláudio', 'massa',
    'farias', 'lagos',
    'joão', 'pessoa',
    'vivaldão', 'machadão',
    'barroso', 'almirante',
    'chile', 'argentina', 'uruguai', 'paraguai', 'colômbia', 'venezuela',
    'méxico', 'peru', 'bolívia', 'equador', 'cuba',
    'frança', 'itália', 'alemanha', 'espanha', 'portugal', 'inglaterra',
    'houssay',
    # Lugares - cidades e estados
    'brasil', 'brazil', 'brasília', 'brasilia', 'rio', 'janeiro', 'paulo',
    'belo', 'horizonte', 'salvador', 'recife', 'fortaleza', 'curitiba',
    'porto', 'alegre', 'belém', 'manaus', 'goiânia', 'uberlândia',
    'cuiabá', 'palmas', 'teresina', 'natal', 'aracaju', 'campina',
    'luís', 'luis', 'luiz', 'olinda', 'niterói',
    'crato', 'barbalha', 'juazeiro', 'bequimão', 'alcântara',
    'minas', 'gerais', 'bahia', 'pernambuco', 'ceará', 'paraná', 'goiás',
    'maranhão', 'piauí', 'tocantins', 'roraima', 'amazonas', 'amapá',
    'mato', 'grosso', 'paraíba',
    'grande',  # em "Campina Grande"
    'nordeste', 'norte', 'sul', 'sudeste',
    'amazônia', 'amazônico',
    # Cidades — SP
    'santos', 'campinas', 'araraquara', 'maringá', 'londrina', 'guarujá', 'jaú',
    # Cidades — Sul e Cone Sul
    'canoas', 'caracas', 'montevidéu', 'farroupilha', 'caxias',
    # Cidades — N/NE
    'maceió', 'macapá',
    # Bairros e localidades
    'pampulha', 'pedregulho', 'pici', 'anauá', 'taumanan',
    'ceilândia', 'ludovicense',
    'higienópolis', 'pompeia', 'califórnia', 'sinimbú',
    'capitólio', 'friburgo', 'imbé',
    # Rios e acidentes geográficos
    'tietê', 'jacuí', 'goitá',
    # Regiões
    'cariri',
    # Estados
    'pará',
    # Obras/Edifícios
    'itamaraty', 'planalto', 'alvorada', 'congresso',
    'copan', 'guinle', 'ibirapuera', 'castelão',
    'piedade',
    # Publicações
    'módulo', 'acrópole', 'habitat',
}

# Áreas do saber e conceitos (capitalizar)
AREAS_SABER = {
    'arquitetura', 'urbanismo', 'engenharia',
    'história', 'geografia', 'sociologia',
}

# Movimentos e conceitos especializados (capitalizar)
MOVIMENTOS = {
    'modernismo', 'modernista', 'modernistas',
    'brutalismo', 'brutalista',
    'neoclássico', 'neoclássica', 'neocolonial',
    'barroco', 'barroca',
    'renascimento',
}

# Expressões consolidadas: se a primeira palavra aparece, capitalizar
EXPRESSOES_CONSOLIDADAS = {
    'educação patrimonial': 'Educação Patrimonial',
    'patrimônio cultural': 'Patrimônio Cultural',
    'patrimônio moderno': 'Patrimônio Moderno',
    'movimento moderno': 'Movimento Moderno',
    'art déco': 'Art Déco',
    'art nouveau': 'Art Nouveau',
    'escola carioca': 'Escola Carioca',
    'escola do recife': 'Escola do Recife',
    'boa vista': 'Boa Vista',
    'bo bardi': 'Bo Bardi',
    'são luís': 'São Luís',
    'são luis': 'São Luis',
    'são luiz': 'São Luiz',
    'são paulo': 'São Paulo',
    'são carlos': 'São Carlos',
    'cine são luiz': 'Cine São Luiz',
    'reis magos': 'Reis Magos',
    'hotel internacional': 'Hotel Internacional',
    'centro cultural': 'Centro Cultural',
    'centro de saúde': 'Centro de Saúde',
    'centro histórico': 'Centro Histórico',
    'estação nova': 'Estação Nova',
    'estação ferroviária': 'Estação Ferroviária',
    'campina grande': 'Campina Grande',
    'juazeiro do norte': 'Juazeiro do Norte',
    'minha casa minha vida': 'Minha Casa Minha Vida',
    'mato grosso': 'Mato Grosso',
    'do norte': 'do Norte',
    'passo da pátria': 'Passo da Pátria',
    'centro de exportadores': 'Centro de Exportadores',
    'hospital universitário': 'Hospital Universitário',
    # sdnne05
    'joão pessoa': 'João Pessoa',
    'ouro preto': 'Ouro Preto',
    'vila serra do navio': 'Vila Serra do Navio',
    'vila amazonas': 'Vila Amazonas',
    'cabo branco': 'Cabo Branco',
    'chapéu de palha': 'Chapéu de Palha',
    'porto alegre': 'Porto Alegre',
    'viña del mar': 'Viña del Mar',
}

# Palavras compostas com hífen
COMPOSTOS_PROPRIOS = {
    'centro-oeste': 'Centro-Oeste',
}


class OrderedDumper(yaml.SafeDumper):
    pass


def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


OrderedDumper.add_representer(dict, dict_representer)


def salvar_yaml(caminho, dados):
    with open(caminho, 'w', encoding='utf-8') as f:
        yaml.dump(dados, f, Dumper=OrderedDumper, default_flow_style=False,
                  allow_unicode=True, width=10000, sort_keys=False)


def normalizar_palavra(palavra, posicao, inicio_frase):
    """Normaliza uma palavra individual."""
    # Caso especial: d'Alva, d'água etc.
    if palavra.lower().startswith("d'") or palavra.lower().startswith("d´"):
        return palavra[0] + palavra[1] + palavra[2:].capitalize()

    # Preserva pontuação ao redor
    match = re.match(r'^([^\w]*)(\w+)([^\w]*)$', palavra, re.UNICODE)
    if not match:
        return palavra

    prefixo, nucleo, sufixo = match.groups()
    nucleo_lower = nucleo.lower()

    # Sigla: maiúscula
    if nucleo_lower in SIGLAS:
        return prefixo + nucleo.upper() + sufixo

    # Nome próprio: capitalizar
    if nucleo_lower in NOMES_PROPRIOS:
        return prefixo + nucleo.capitalize() + sufixo

    # Área do saber: capitalizar
    if nucleo_lower in AREAS_SABER:
        return prefixo + nucleo.capitalize() + sufixo

    # Movimento: capitalizar
    if nucleo_lower in MOVIMENTOS:
        return prefixo + nucleo.capitalize() + sufixo

    # Início de frase: capitalizar
    if inicio_frase and posicao == 0:
        return prefixo + nucleo.capitalize() + sufixo

    # Resto: minúscula
    return prefixo + nucleo_lower + sufixo


def normalizar_texto(texto, eh_subtitulo=False):
    """Normaliza um texto (título ou subtítulo)."""
    if not texto:
        return texto

    # Remove ponto final se houver
    texto = texto.rstrip('.')

    # Primeiro, aplicar expressões consolidadas
    texto_lower = texto.lower()
    substituicoes = {}
    for expr, repl in EXPRESSOES_CONSOLIDADAS.items():
        idx = texto_lower.find(expr)
        if idx >= 0:
            substituicoes[idx] = (len(expr), repl)

    palavras = texto.split()
    resultado = []

    for i, palavra in enumerate(palavras):
        # Verifica se é palavra composta com hífen
        if '-' in palavra and palavra.lower() in COMPOSTOS_PROPRIOS:
            resultado.append(COMPOSTOS_PROPRIOS[palavra.lower()])
        elif '-' in palavra:
            # Tratar cada parte do hífen
            partes = palavra.split('-')
            partes_norm = []
            for j, parte in enumerate(partes):
                p_fake = normalizar_palavra(parte, i if j == 0 else 1, inicio_frase=(i == 0 and j == 0) and not eh_subtitulo)
                partes_norm.append(p_fake)
            resultado.append('-'.join(partes_norm))
        elif '/' in palavra and not palavra.startswith('http'):
            # Tratar cada parte da barra
            partes = palavra.split('/')
            partes_norm = []
            for j, parte in enumerate(partes):
                if parte:
                    p_norm = normalizar_palavra(parte, i if j == 0 else 1, inicio_frase=(i == 0 and j == 0) and not eh_subtitulo)
                    partes_norm.append(p_norm)
                else:
                    partes_norm.append(parte)
            resultado.append('/'.join(partes_norm))
        else:
            inicio_frase = (i == 0) and not eh_subtitulo
            palavra_norm = normalizar_palavra(palavra, i, inicio_frase)

            # Se for subtítulo e primeira palavra, forçar minúscula
            # a menos que seja sigla ou nome próprio
            if eh_subtitulo and i == 0:
                nucleo = re.sub(r'[^\w]', '', palavra.lower())
                if (nucleo not in SIGLAS and nucleo not in NOMES_PROPRIOS
                    and nucleo not in AREAS_SABER and nucleo not in MOVIMENTOS):
                    if palavra_norm and palavra_norm[0].isupper():
                        palavra_norm = palavra_norm[0].lower() + palavra_norm[1:]

            resultado.append(palavra_norm)

    texto_resultado = ' '.join(resultado)

    # Aplicar expressões consolidadas (segunda passada)
    for expr, repl in EXPRESSOES_CONSOLIDADAS.items():
        # Case-insensitive replace
        pattern = re.compile(re.escape(expr), re.IGNORECASE)
        texto_resultado = pattern.sub(repl, texto_resultado)

    return texto_resultado


def processar_seminario(slug):
    yaml_file = BASE / f"{slug}.yaml"

    with open(yaml_file, 'r', encoding='utf-8') as f:
        dados = yaml.safe_load(f)

    alterados = 0
    for artigo in dados['articles']:
        titulo_orig = artigo.get('title', '')
        subtitulo_orig = artigo.get('subtitle')

        titulo_novo = normalizar_texto(titulo_orig, eh_subtitulo=False)
        subtitulo_novo = normalizar_texto(subtitulo_orig, eh_subtitulo=True) if subtitulo_orig else None

        mudou = (titulo_novo != titulo_orig) or (subtitulo_novo != subtitulo_orig)

        if mudou:
            print(f"{artigo.get('id', '?')}:")
            if titulo_novo != titulo_orig:
                print(f"  T: {titulo_orig}")
                print(f"  →  {titulo_novo}")
            if subtitulo_novo != subtitulo_orig:
                print(f"  S: {subtitulo_orig}")
                print(f"  →  {subtitulo_novo}")
            print()

            artigo['title'] = titulo_novo
            artigo['subtitle'] = subtitulo_novo
            alterados += 1

    salvar_yaml(yaml_file, dados)
    print(f"=== {slug}: {alterados} artigos alterados ===\n")


def main():
    processar_seminario("sdnne07")
    processar_seminario("sdnne09")
    print("Concluído!")


if __name__ == "__main__":
    main()
