#!/usr/bin/env python3
"""
Normaliza maiúsculas/minúsculas nos títulos conforme FUNAG.

Regras:
- Tudo minúscula, exceto:
  - Primeira letra do título: maiúscula
  - Primeira letra do subtítulo: minúscula (regra FUNAG)
  - Siglas: maiúsculas (BNH, USP, IPHAN)
  - Nomes próprios: capitalizado (Niemeyer, Brasília, Pedregulho)
"""

import yaml
import re
from pathlib import Path

YAML_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/yaml")

# Siglas (sempre maiúsculas)
SIGLAS = {
    'bnh', 'iphan', 'sphan', 'dphan', 'ufmg', 'usp', 'ufrj', 'unb', 'ufba',
    'ufrgs', 'ufpe', 'ufrn', 'ufc', 'ufpb', 'ufpr', 'ufsc', 'ufu', 'ufg',
    'iab', 'cau', 'crea', 'mes', 'mesp', 'dop', 'iap', 'iaps', 'fcp', 'dhp',
    'sfh', 'fgts', 'inocoop', 'cohab', 'cdhu', 'sudene', 'chesf', 'dnocs',
    'novacap', 'epucs', 'ciam', 'uia', 'docomomo', 'unesco', 'onu',
    'masp', 'mam', 'mac', 'moma',
    'abi', 'oab', 'senai', 'sesi', 'senac', 'sesc',
    'puc', 'faap', 'fau', 'fauusp', 'faufba', 'ead', 'eesc',
    'ibge', 'ibama', 'incra', 'inss', 'cef', 'bb', 'bndes', 'banespa',
    'df', 'rj', 'sp', 'mg', 'ba', 'pe', 'ce', 'rs', 'pr', 'sc', 'go', 'mt',
    'ms', 'pa', 'am', 'ma', 'pi', 'rn', 'pb', 'al', 'se', 'es', 'to', 'ro',
    'ac', 'ap', 'rr',
    'eua', 'usa', 'uk', 'urss',
    'gt', 'ii', 'iii', 'iv', 'xx', 'xxi', 'xix', 'xviii',
    'us', 'mapi',
}

# Nomes próprios (capitalizar)
NOMES_PROPRIOS = {
    # Arquitetos
    'niemeyer', 'lucio', 'lúcio', 'costa', 'reidy', 'affonso', 'burle', 'marx',
    'artigas', 'vilanova', 'rocha', 'lina', 'bardi', 'warchavchik', 'bratke',
    'oswaldo', 'mindlin', 'lelé', 'filgueiras', 'borsoi', 'delfim', 'amorim',
    'heitor', 'maia', 'neto', 'nunes', 'attílio', 'bolonha', 'aldary', 'toledo',
    'leão', 'graeff', 'cardozo', 'portinari', 'giorgi', 'tenreiro',
    'corbusier', 'mies', 'rohe', 'gropius', 'wright', 'aalto', 'kahn', 'koenig',
    'campolina', 'schwab', 'zein', 'ficher', 'segawa', 'bruand', 'chacel',
    'carvalho', 'flávio', 'mauro', 'peixoto', 'coury',
    'elgson', 'ribeiro', 'gomes', 'heep', 'petrônio', 'cunha', 'lima',
    'kubitschek', 'juscelino', 'vargas', 'getúlio', 'capanema', 'gustavo',
    'jorge', 'silva', 'luiz', 'luis', 'diederichsen', 'jéssica', 'jessica',
    'fernando', 'eduardo', 'roberto', 'carlos', 'antonio', 'antônio',
    'josé', 'pedro', 'paulo', 'joão', 'ana', 'marcos', 'marcelo',
    # Lugares
    'brasil', 'brazil', 'brasília', 'brasilia', 'rio', 'janeiro', 'são', 'paulo',
    'belo', 'horizonte', 'salvador', 'recife', 'fortaleza', 'curitiba',
    'porto', 'alegre', 'belém', 'manaus', 'goiânia', 'uberlândia', 'sorocaba',
    'cataguases', 'ouro', 'preto', 'diamantina', 'mariana', 'petrópolis',
    'ceilândia', 'pampulha', 'pedregulho', 'paranaíba', 'maranhão', 'luís',
    'minas', 'gerais', 'bahia', 'pernambuco', 'ceará', 'paraná', 'goiás',
    'triângulo', 'mineiro', 'capixaba', 'alto', 'paranaense',
    'nordeste', 'norte', 'sul', 'sudeste',
    'portugal', 'madrid', 'stuttgart', 'weissenhof', 'pena', 'furada',
    'lamel', 'house', 'maringá', 'ribeirão', 'pessoense', 'joão', 'pessoa',
    'estrela', "d'alva", "d´alva", 'alva', 'habitacional',
    # Obras/Publicações
    'itamaraty', 'planalto', 'alvorada', 'congresso', 'nacional',
    'copan', 'guinle', 'ibirapuera', 'castelão',
    'módulo', 'acrópole', 'habitat', 'projeto',
    # Pessoas
    'humberto', 'oscar', 'le', 'pierre', 'adolf', 'franz', 'heep',
    'joel', 'maria', 'carmo', 'ruth', 'verde',
}

# Palavras compostas com hífen onde segunda parte deve ser capitalizada
COMPOSTOS_PROPRIOS = {
    'sul-americanos': 'sul-americanos',  # mantém minúscula
    'centro-oeste': 'Centro-Oeste',
}

ORDEM_CAMPOS = [
    'id', 'seminario', 'secao', 'titulo', 'subtitulo', 'locale',
    'autores_raw', 'resumo', 'palavras_chave', 'resumo_en', 'palavras_chave_en',
    'texto', 'figuras', 'referencias',
    'arquivo_fonte', 'arquivo_pdf_original', 'arquivo_pdf', 'status'
]


def normalizar_palavra(palavra, posicao, inicio_frase):
    """Normaliza uma palavra."""
    # Caso especial: d'Alva, d´Alva (com apóstrofo)
    if palavra.lower().startswith("d'") or palavra.lower().startswith("d´"):
        return palavra[0] + palavra[1] + palavra[2:].capitalize()

    # Preserva pontuação
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

    palavras = texto.split()
    resultado = []

    for i, palavra in enumerate(palavras):
        # Verifica se é palavra composta
        if '-' in palavra and palavra.lower() in COMPOSTOS_PROPRIOS:
            resultado.append(COMPOSTOS_PROPRIOS[palavra.lower()])
        else:
            # Para subtítulo, primeira palavra inicia com minúscula
            # exceto se for nome próprio ou sigla
            inicio_frase = (i == 0) and not eh_subtitulo
            palavra_norm = normalizar_palavra(palavra, i, inicio_frase)

            # Se for subtítulo e primeira palavra, forçar minúscula
            # a menos que seja sigla ou nome próprio
            if eh_subtitulo and i == 0:
                nucleo = re.sub(r'[^\w]', '', palavra.lower())
                if nucleo not in SIGLAS and nucleo not in NOMES_PROPRIOS:
                    # Força minúscula na primeira letra
                    if palavra_norm and palavra_norm[0].isupper():
                        palavra_norm = palavra_norm[0].lower() + palavra_norm[1:]

            resultado.append(palavra_norm)

    return ' '.join(resultado)


def salvar_yaml_ordenado(caminho, dados):
    """Salva YAML mantendo ordem dos campos."""
    dados_ordenados = {}
    for campo in ORDEM_CAMPOS:
        if campo in dados:
            dados_ordenados[campo] = dados[campo]
    for campo in dados:
        if campo not in dados_ordenados:
            dados_ordenados[campo] = dados[campo]

    class OrderedDumper(yaml.SafeDumper):
        pass

    def dict_representer(dumper, data):
        return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

    OrderedDumper.add_representer(dict, dict_representer)

    with open(caminho, 'w', encoding='utf-8') as f:
        yaml.dump(dados_ordenados, f, Dumper=OrderedDumper, default_flow_style=False,
                  allow_unicode=True, width=10000, sort_keys=False)


def main():
    print("Normalizando maiúsculas/minúsculas...\n")

    alterados = 0
    for yaml_file in sorted(YAML_DIR.glob("sdbr12-*.yaml")):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            dados = yaml.safe_load(f)

        titulo_orig = dados.get('titulo', '')
        subtitulo_orig = dados.get('subtitulo')

        titulo_novo = normalizar_texto(titulo_orig, eh_subtitulo=False)
        subtitulo_novo = normalizar_texto(subtitulo_orig, eh_subtitulo=True) if subtitulo_orig else None

        mudou = (titulo_novo != titulo_orig) or (subtitulo_novo != subtitulo_orig)

        if mudou:
            print(f"{yaml_file.name}:")
            if titulo_novo != titulo_orig:
                print(f"  titulo:    {titulo_orig}")
                print(f"           → {titulo_novo}")
            if subtitulo_novo != subtitulo_orig:
                print(f"  subtitulo: {subtitulo_orig}")
                print(f"           → {subtitulo_novo}")
            print()

            dados['titulo'] = titulo_novo
            dados['subtitulo'] = subtitulo_novo
            salvar_yaml_ordenado(yaml_file, dados)
            alterados += 1

    print(f"=== Total: {alterados} arquivos alterados ===")


if __name__ == "__main__":
    main()
