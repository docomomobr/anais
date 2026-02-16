#!/usr/bin/env python3
"""
Normaliza maiúsculas/minúsculas nos títulos conforme norma brasileira de capitalização.
Adaptado de nacionais/sdbr12_fontes/normalizar_maiusculas.py para seminários SP.

Regras:
- Tudo minúscula, exceto:
  - Primeira letra do título: maiúscula
  - Primeira letra do subtítulo: minúscula
  - Siglas: maiúsculas (BNH, USP, IPHAN)
  - Nomes próprios: capitalizado (Niemeyer, Brasília, Pedregulho)
"""

import yaml
import re
import sys
from pathlib import Path

BASE_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/sp")

class OrderedDumper(yaml.SafeDumper):
    pass
def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())
OrderedDumper.add_representer(dict, dict_representer)


# Siglas (sempre maiúsculas)
SIGLAS = {
    # Instituições
    'bnh', 'iphan', 'sphan', 'dphan', 'conpresp', 'condephaat',
    'ufmg', 'usp', 'ufrj', 'unb', 'ufba', 'ufrgs', 'ufpe', 'ufrn', 'ufc',
    'ufpb', 'ufpr', 'ufsc', 'ufu', 'ufg', 'ufmt', 'ufma', 'ufam', 'ufpa',
    'ufes', 'ufcg', 'unicamp', 'unesp', 'unicep', 'unisanta',
    'iab', 'cau', 'crea', 'mes', 'mesp', 'dop', 'iap', 'iaps',
    'fcp', 'dhp', 'sfh', 'fgts', 'inocoop', 'cohab', 'cdhu',
    'sudene', 'chesf', 'dnocs', 'novacap', 'ciam', 'uia', 'docomomo', 'unesco',
    'masp', 'mam', 'mac', 'moma',
    'abi', 'oab', 'senai', 'sesi', 'senac', 'sesc',
    'puc', 'faap', 'fau', 'fauusp', 'faufba', 'faus', 'ead', 'eesc',
    'ibge', 'ibama', 'incra', 'inss', 'cef', 'bb', 'bndes', 'banespa', 'bnb',
    # Estados
    'df', 'rj', 'sp', 'mg', 'ba', 'pe', 'ce', 'rs', 'pr', 'sc', 'go', 'mt',
    'ms', 'pa', 'am', 'ma', 'pi', 'rn', 'pb', 'al', 'se', 'es', 'to', 'ro',
    'ac', 'ap', 'rr',
    # Outros
    'eua', 'usa', 'uk', 'urss',
    'gt', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x',
    'xx', 'xxi', 'xix', 'xviii', 'xvii', 'xvi',
    'us', 'mapi',
    # SP-específicas
    'ee', 'fumest', 'page', 'iapc', 'fece', 'conesp', 'fde',
    'ipesp', 'sbpc', 'detran', 'aphrp', 'vant', 'sulacap',
    'jk', 'mmm', 'propar', 'proarq', 'mdu', 'iau', 'mac',
    'gil', 'igepac',
    'iapi', 'cerpemob',
    # Nota: 'arena' NÃO é sigla aqui (é empresa construtora Arena)
    # 'v' está incluído para algarismos romanos
}

# Nomes próprios (capitalizar)
NOMES_PROPRIOS = {
    # Arquitetos / Pessoas
    'niemeyer', 'lucio', 'lúcio', 'costa', 'reidy', 'affonso', 'burle', 'marx',
    'artigas', 'vilanova', 'rocha', 'lina', 'bardi', 'warchavchik', 'bratke',
    'oswaldo', 'mindlin', 'lelé', 'filgueiras', 'borsoi', 'delfim', 'amorim',
    'heitor', 'maia', 'neto', 'nunes', 'attílio', 'bolonha', 'aldary', 'toledo',
    'leão', 'graeff', 'cardozo', 'portinari', 'giorgi', 'tenreiro',
    'corbusier', 'mies', 'gropius', 'wright', 'aalto', 'kahn',
    'campolina', 'schwab', 'zein', 'ficher', 'segawa', 'bruand', 'chacel',
    'flávio', 'mauro', 'peixoto', 'coury',
    'elgson', 'ribeiro', 'gomes', 'heep', 'petrônio', 'cunha', 'lima',
    'kubitschek', 'juscelino', 'vargas', 'getúlio', 'capanema', 'gustavo',
    'jorge', 'silva', 'luiz', 'luis', 'diederichsen',
    'fernando', 'eduardo', 'roberto', 'carlos', 'antonio', 'antônio',
    'josé', 'pedro', 'paulo', 'joão', 'ana', 'marcos', 'marcelo',
    # SP-específicas
    'kneese', 'mello', 'tibau', 'sanovicz', 'almeida', 'penteado',
    'toscano', 'odiléa', 'gilioli', 'ubyrajara', 'santoro', 'francisco',
    'caron', 'levi', 'rino', 'neutra', 'richard',
    'graziosi', 'mario', 'lefrève', 'rodrigo', 'ferro', 'sérgio',
    'zolko', 'gregório', 'pilon', 'jacques', 'palanti', 'giancarlo',
    'broos', 'hans', 'schneider', 'maurício', 'fragelli', 'marcello',
    'vigliecca', 'hector', 'guedes', 'joaquim', 'cordeiro', 'waldemar',
    'zanettini', 'siegbert', 'grinover', 'duschenes', 'ronaldo',
    'caiuby', 'geraldo', 'muzi', 'dantas', 'macedo', 'cornelsen',
    'hollander', 'kurt', 'schoedon', 'wolfgang', 'capello',
    'calatrava', 'santiago', 'darcy', 'brizola', 'leonel',
    'lauro', 'hélio', 'duarte', 'fábio',
    'carvalho', 'nadir',
    'calabi', 'daniele',
    'berquó', 'bordano', 'ninca', 'gastão', 'castro', 'tadeu',
    'popconcreto',
    'amortex', 'belzer',
    'crispiniano', 'conselheiro',
    'walter', 'val', 'arthur', 'ayrton', 'lolô',
    'ciccillo', 'matarazzo', 'pirapama',
    'philomena', 'cardoso', 'oliveira',
    # sdsp09-specific
    'raposo', 'lineu', 'borges', 'gregori', 'christiano', 'stockler', 'neves',
    'farroupilha', 'marahú', 'anchieta', 'irajá', 'princesa', 'isabel',
    'cará', 'pae',
    'mackenzie', 'arena',
    # sdsp03-specific
    'libeskind', 'david', 'perret', 'piacentini', 'dubugras', 'abrahão',
    'villares', 'warchavchik', 'cascaldi',
    'jaraguá', 'congonhas', 'tietê', 'pacaembu', 'bauru', 'promissão',
    'lausanne', 'columbus', 'itália', 'itaúsa', 'conceição',
    'marília', 'limeira', 'japurá', 'jaguara',
    'victor', 'reidy', 'pedrosa',
    'severo', 'pilon',
    'hespéria', 'heep',
    'itápolis', 'califórnia', 'samuel', 'azevedo', 'ramos',
    'taques', 'bittencourt', 'mário', 'cinelândia', 'luís',
    # Lugares
    'brasil', 'brazil', 'brasília', 'brasilia', 'rio', 'janeiro',
    'são', 'paulo', 'santos',
    'belo', 'horizonte', 'salvador', 'recife', 'fortaleza', 'curitiba',
    'porto', 'alegre', 'belém', 'manaus', 'goiânia', 'uberlândia',
    'sorocaba', 'campinas', 'piracicaba', 'botucatu', 'araraquara',
    'cataguases', 'ouro', 'preto', 'diamantina', 'mariana', 'petrópolis',
    'ceilândia', 'pampulha', 'pedregulho', 'paranaíba', 'maranhão',
    'minas', 'gerais', 'bahia', 'pernambuco', 'ceará', 'paraná', 'goiás',
    'triângulo', 'capixaba', 'paranaense',
    'nordeste', 'norte', 'sul', 'sudeste',
    'portugal', 'madrid', 'stuttgart', 'weissenhof', 'lisboa', 'osaka',
    'maringá', 'ribeirão', 'pessoense', 'pessoa', 'londrina', 'niterói',
    'estrela', 'natal', 'timóteo',
    # Bairros SP
    'ibirapuera', 'higienópolis', 'mooca', 'morumbi',
    'copan', 'guinle', 'castelão',
    'ibitinga', 'caraíba', 'guarujá', 'pernambuco',
    # Edificações/Publicações
    'itamaraty', 'planalto', 'alvorada', 'congresso',
    'módulo', 'acrópole', 'habitat',
    'coliseu', 'germaine', 'gemini',
    # Pessoas genéricas (primeiros nomes comuns)
    'humberto', 'oscar', 'le', 'pierre', 'adolf', 'franz',
    'joel', 'maria', 'carmo', 'ruth', 'verde',
    'liliana', 'crispiniano', 'tomie', 'ohtake',
    'ângela', 'amaro', 'lobbe', 'adolfo',
}

# Expressões compostas (multi-palavra) que precisam de capitalização especial
EXPRESSOES_COMPOSTAS = {
    'são paulo': 'São Paulo',
    'são carlos': 'São Carlos',
    'são vicente': 'São Vicente',
    'são judas': 'São Judas',
    'santo amaro': 'Santo Amaro',
    'cidade jardim': 'Cidade Jardim',
    'jardim ângela': 'Jardim Ângela',
    'novo santo': 'Novo Santo',
    'vila madalena': 'Vila Madalena',
    'mies van der rohe': 'Mies van der Rohe',
    'le corbusier': 'Le Corbusier',
    'bo bardi': 'Bo Bardi',
    'kneese de mello': 'Kneese de Mello',
    'mendes da rocha': 'Mendes da Rocha',
    'de mello': 'de Mello',
    'art déco': 'Art Déco',
    'art deco': 'Art Déco',
    'educação patrimonial': 'Educação Patrimonial',
    'patrimônio cultural': 'Patrimônio Cultural',
    'plano de ação': 'Plano de Ação',
    'paulo eiró': 'Paulo Eiró',
    'mario de andrade': 'Mario de Andrade',
    'mário de andrade': 'Mário de Andrade',
    'rio de janeiro': 'Rio de Janeiro',
    'campina grande': 'Campina Grande',
    'ribeirão preto': 'Ribeirão Preto',
    'porto de santos': 'Porto de Santos',
    'baixada santista': 'Baixada Santista',
    'centro histórico': 'Centro Histórico',
    'estado novo': 'Estado Novo',
    'movimento moderno': 'Movimento Moderno',
    'cultura artística': 'Cultura Artística',
    'harmonia de tênis': 'Harmonia de Tênis',
    'casa do povo': 'Casa do Povo',
    'seminário docomomo': 'Seminário Docomomo',
    'convênio escolar': 'Convênio Escolar',
    'caixa econômica': 'Caixa Econômica',
    'são judas tadeu': 'São Judas Tadeu',
    'gastão de castro lima': 'Gastão de Castro Lima',
    'ninca bordano': 'Ninca Bordano',
    'casa berquó': 'Casa Berquó',
    'biblioteca mário de andrade': 'Biblioteca Mário de Andrade',
    'cinema de rua': 'cinema de rua',
    'santo amaro v': 'Santo Amaro V',
    'nova central': 'Nova Central',
    'teatro municipal': 'Teatro Municipal',
    'teatro paulo eiró': 'Teatro Paulo Eiró',
    'escola estadual': 'Escola Estadual',
    'ayrton lolô cornelsen': 'Ayrton Lolô Cornelsen',
    'ciccillo matarazzo': 'Ciccillo Matarazzo',
    'pavilhão ciccillo matarazzo': 'Pavilhão Ciccillo Matarazzo',
    'museu de arte': 'Museu de Arte',
    'doze de outubro': 'Doze de Outubro',
    'colégio doze de outubro': 'Colégio Doze de Outubro',
    'santa cruz': 'Santa Cruz',
    'princesa isabel': 'Princesa Isabel',
    'terminal princesa isabel': 'Terminal Princesa Isabel',
    'memorial jk': 'Memorial JK',
    'casa de saúde anchieta': 'Casa de Saúde Anchieta',
    'palácio farroupilha': 'Palácio Farroupilha',
    'christiano stockler das neves': 'Christiano Stockler das Neves',
    'lineu borges de macedo': 'Lineu Borges de Macedo',
    'márlio raposo dantas': 'Márlio Raposo Dantas',
    'pae cará': 'Pae Cará',
    'grupo escolar': 'Grupo Escolar',
    'mac usp': 'MAC USP',
    # sdsp03-specific
    'são josé dos campos': 'São José dos Campos',
    'são josé': 'São José',
    'parque do ibirapuera': 'Parque do Ibirapuera',
    'teatro oficina': 'Teatro Oficina',
    'carta de atenas': 'Carta de Atenas',
    'centro novo': 'Centro Novo',
    'centro cívico': 'Centro Cívico',
    'alto tietê': 'Alto Tietê',
    'vale do paraíba': 'Vale do Paraíba',
    'hospital das clínicas': 'Hospital das Clínicas',
    'edifício itália': 'Edifício Itália',
    'santa maria': 'Santa Maria',
    'cidade universitária': 'Cidade Universitária',
    'cidade nova': 'Cidade Nova',
    'eduardo longo': 'Eduardo Longo',
    'flávio império': 'Flávio Império',
    'victor dubugras': 'Victor Dubugras',
    'ricardo severo': 'Ricardo Severo',
    'david libeskind': 'David Libeskind',
    'vila mariana': 'Vila Mariana',
    'rua santa cruz': 'rua Santa Cruz',
    'gregori warchavchik': 'Gregori Warchavchik',
    'barão de jaguara': 'Barão de Jaguara',
    'centro empresarial itaúsa': 'Centro Empresarial Itaúsa',
    'edifício lausanne': 'Edifício Lausanne',
    'edifício columbus': 'Edifício Columbus',
    'edifício sul-americano': 'Edifício Sul-Americano',
    'hotel jaraguá': 'Hotel Jaraguá',
    'abadia santa maria': 'Abadia Santa Maria',
    'museu de arte moderna': 'Museu de Arte Moderna',
    'revista habitat': 'revista Habitat',
    'parque ibirapuera': 'Parque Ibirapuera',
    'carta atenas': 'Carta Atenas',
    'carta de atenas': 'Carta de Atenas',
    'ramos de azevedo': 'Ramos de Azevedo',
    'taques bittencourt': 'Taques Bittencourt',
    'arquitetura moderna': 'Arquitetura Moderna',
    'parque da cidade': 'Parque da Cidade',
    'casa de arte': 'Casa de Arte',
    'avenida são luís': 'Avenida São Luís',
    'avenida são luis': 'Avenida São Luís',
    'triângulo mineiro': 'Triângulo Mineiro',
    'cinelândia paulistana': 'Cinelândia paulistana',
}

# Palavras compostas com hífen
COMPOSTOS_PROPRIOS = {
    'centro-oeste': 'Centro-Oeste',
    'transformar-se': 'transformar-se',
    'fau-usp': 'FAU-USP',
    'fau-mack': 'FAU-Mack',
    'iau-usp': 'IAU-USP',
    'detran-sp': 'DETRAN-SP',
    'iab-sp': 'IAB-SP',
    'mac-usp': 'MAC-USP',
    'igepac-sp': 'IGEPAC-SP',
}

# Disciplinas/áreas do saber (norma brasileira: maiúscula)
AREAS_SABER = {
    'arquitetura', 'urbanismo', 'história', 'geografia', 'filosofia',
    'sociologia', 'engenharia', 'arte', 'artes', 'design',
    'fotografia', 'teatro', 'música',
}

# Movimentos/períodos (norma brasileira: maiúscula)
MOVIMENTOS = {
    'modernismo', 'brutalismo', 'concretismo', 'neoclassicismo', 'neocolonial',
    'ecletismo', 'racionalismo', 'funcionalismo', 'renascimento',
}


def normalizar_palavra(palavra, posicao, inicio_frase):
    """Normaliza uma palavra."""
    # Caso especial: d'Alva, d´Alva (com apóstrofo)
    if palavra.lower().startswith("d'") or palavra.lower().startswith("d´"):
        return palavra[0] + palavra[1] + palavra[2:].capitalize()

    # Preserva pontuação ao redor
    match = re.match(r'^([^\w]*)(\w+)([^\w]*)$', palavra, re.UNICODE)
    if not match:
        return palavra

    prefixo, nucleo, sufixo = match.groups()
    nucleo_lower = nucleo.lower()

    # Inicial de nome (letra única + ponto): maiúscula
    if len(nucleo) == 1 and sufixo.startswith('.'):
        return prefixo + nucleo.upper() + sufixo

    # Sigla: maiúscula
    if nucleo_lower in SIGLAS:
        return prefixo + nucleo.upper() + sufixo

    # Nome próprio: capitalizar
    if nucleo_lower in NOMES_PROPRIOS:
        return prefixo + nucleo.capitalize() + sufixo

    # Área do saber: capitalizar
    if nucleo_lower in AREAS_SABER:
        return prefixo + nucleo.capitalize() + sufixo

    # Movimento/período: capitalizar
    if nucleo_lower in MOVIMENTOS:
        return prefixo + nucleo.capitalize() + sufixo

    # Início de frase: capitalizar
    if inicio_frase:
        return prefixo + nucleo.capitalize() + sufixo

    # Resto: minúscula
    return prefixo + nucleo_lower + sufixo


def normalizar_texto(texto, eh_subtitulo=False):
    """Normaliza um texto (título ou subtítulo)."""
    if not texto:
        return texto

    # Remove ponto final se houver
    texto = texto.rstrip('.')

    # Primeiro, aplicar expressões compostas
    texto_lower = texto.lower()
    for expr, repl in sorted(EXPRESSOES_COMPOSTAS.items(), key=lambda x: -len(x[0])):
        # Substituir todas as ocorrências (case-insensitive)
        idx = texto_lower.find(expr)
        while idx >= 0:
            texto = texto[:idx] + repl + texto[idx + len(expr):]
            texto_lower = texto.lower()
            idx = texto_lower.find(expr, idx + len(repl))

    palavras = texto.split()
    resultado = []
    apos_ponto = False  # flag: próxima palavra é início de frase (após '. ')

    for i, palavra in enumerate(palavras):
        # Detectar se a palavra anterior terminou com ponto
        if i > 0:
            prev = resultado[-1] if resultado else ''
            if prev.endswith('.'):
                apos_ponto = True

        # Verifica se é palavra composta com hífen
        if '-' in palavra and palavra.lower() in COMPOSTOS_PROPRIOS:
            resultado.append(COMPOSTOS_PROPRIOS[palavra.lower()])
        elif '-' in palavra:
            # Normalizar cada parte do composto separadamente
            partes = palavra.split('-')
            partes_norm = []
            for j, parte in enumerate(partes):
                p_norm = normalizar_palavra(parte, i if j == 0 else 1,
                                            inicio_frase=(i == 0 and j == 0 and not eh_subtitulo) or (j == 0 and apos_ponto))
                partes_norm.append(p_norm)
            resultado.append('-'.join(partes_norm))
        elif '/' in palavra:
            # Normalizar cada parte de palavra com barra (ex: SANTOS/SP)
            partes = palavra.split('/')
            partes_norm = []
            for j, parte in enumerate(partes):
                p_norm = normalizar_palavra(parte, i if j == 0 else 1,
                                            inicio_frase=(i == 0 and j == 0 and not eh_subtitulo) or (j == 0 and apos_ponto))
                partes_norm.append(p_norm)
            resultado.append('/'.join(partes_norm))
        else:
            inicio_frase = ((i == 0) and not eh_subtitulo) or apos_ponto
            palavra_norm = normalizar_palavra(palavra, i, inicio_frase)

            # Se for subtítulo e primeira palavra, forçar minúscula
            # a menos que seja sigla, nome próprio, área ou movimento
            if eh_subtitulo and i == 0:
                nucleo = re.sub(r'[^\w]', '', palavra.lower())
                if (nucleo not in SIGLAS and nucleo not in NOMES_PROPRIOS
                        and nucleo not in AREAS_SABER and nucleo not in MOVIMENTOS):
                    if palavra_norm and palavra_norm[0].isupper():
                        palavra_norm = palavra_norm[0].lower() + palavra_norm[1:]

            resultado.append(palavra_norm)

        apos_ponto = False  # reset flag

    # Reagrupar, verificando se as expressões compostas foram preservadas
    texto_final = ' '.join(resultado)

    # Re-aplicar expressões compostas (podem ter sido quebradas pela normalização)
    texto_lower = texto_final.lower()
    for expr, repl in sorted(EXPRESSOES_COMPOSTAS.items(), key=lambda x: -len(x[0])):
        idx = texto_lower.find(expr)
        while idx >= 0:
            texto_final = texto_final[:idx] + repl + texto_final[idx + len(expr):]
            texto_lower = texto_final.lower()
            idx = texto_lower.find(expr, idx + len(repl))

    return texto_final


def processar_yaml(yaml_path, dry_run=False):
    """Processa um YAML, normalizando títulos."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    slug = data['issue']['slug']
    alterados = 0

    for art in data['articles']:
        art_id = art.get('id', '?')
        titulo_orig = art.get('title', '')

        # Separar título e subtítulo se contiver ': '
        if ': ' in titulo_orig:
            parts = titulo_orig.split(': ', 1)
            titulo_part = parts[0]
            subtitulo_part = parts[1]

            titulo_novo = normalizar_texto(titulo_part, eh_subtitulo=False)
            subtitulo_novo = normalizar_texto(subtitulo_part, eh_subtitulo=True)
            titulo_final = f'{titulo_novo}: {subtitulo_novo}'
        else:
            titulo_final = normalizar_texto(titulo_orig, eh_subtitulo=False)

        if titulo_final != titulo_orig:
            if dry_run:
                print(f"  {art_id} title:")
                print(f"    ANTES:  {titulo_orig}")
                print(f"    DEPOIS: {titulo_final}")
                print()

            art['title'] = titulo_final
            alterados += 1

        # Normalizar campo subtitle separado (se existir)
        sub_orig = art.get('subtitle', '')
        if sub_orig:
            sub_final = normalizar_texto(sub_orig, eh_subtitulo=True)
            if sub_final != sub_orig:
                if dry_run:
                    print(f"  {art_id} subtitle:")
                    print(f"    ANTES:  {sub_orig}")
                    print(f"    DEPOIS: {sub_final}")
                    print()

                art['subtitle'] = sub_final
                alterados += 1

    if not dry_run and alterados > 0:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, Dumper=OrderedDumper, allow_unicode=True,
                      default_flow_style=False, width=10000, sort_keys=False)

    print(f"{slug}: {alterados} títulos alterados")
    return alterados


def main():
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("=== DRY RUN (sem alterações) ===\n")

    # Processar apenas os que precisam (ALL CAPS)
    yamls = [BASE_DIR / f'sdsp{n:02d}.yaml' for n in [3, 6, 8, 9]]
    total = 0
    for yp in yamls:
        if yp.exists():
            total += processar_yaml(yp, dry_run=dry_run)

    print(f"\n{'='*60}")
    print(f"Total: {total} títulos alterados")
    if dry_run:
        print("(nenhuma alteração feita — remover --dry-run para aplicar)")


if __name__ == '__main__':
    main()
