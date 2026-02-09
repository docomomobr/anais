#!/usr/bin/env python3
"""
Normaliza títulos e subtítulos dos YAMLs conforme regras FUNAG.

Regras:
- Títulos: maiúscula na primeira letra e em nomes próprios/siglas
- Subtítulo: inicia com minúscula (exceto nomes próprios, siglas)
- Siglas: sempre maiúsculas
- Nomes próprios: maiúsculas
"""

import yaml
import re
from pathlib import Path

YAML_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/yaml")

# Siglas conhecidas (sempre maiúsculas)
SIGLAS = {
    'BNH', 'IPHAN', 'UFMG', 'USP', 'UFRJ', 'UNB', 'UFBA', 'UFRGS', 'UFPE',
    'UFRN', 'UFC', 'UFPB', 'UFPR', 'UFSC', 'UFU', 'IAB', 'CAU', 'CREA',
    'SPHAN', 'DPHAN', 'MES', 'MESP', 'DOP', 'IAP', 'IAPS', 'FCP', 'DHP',
    'SFH', 'FGTS', 'INOCOOP', 'COHAB', 'CDHU', 'SUDENE', 'CHESF', 'DNOCS',
    'NOVACAP', 'EPUCS', 'CIAM', 'UIA', 'DOCOMOMO', 'UNESCO', 'ONU',
    'MASP', 'MAM', 'MAC', 'MoMA', 'MOMA',
    'ABI', 'OAB', 'SENAI', 'SESI', 'SENAC', 'SESC',
    'PUC', 'FAAP', 'FAU', 'FAUUSP', 'FAUFBA', 'EAD', 'EESC',
    'IBGE', 'IBAMA', 'INCRA', 'INSS', 'CEF', 'BB', 'BNDES', 'BANESPA',
    'PDF', 'HTML', 'OJS', 'VANT', 'SIG', 'GIS', 'BIM', 'CAD',
    'DF', 'RJ', 'SP', 'MG', 'BA', 'PE', 'CE', 'RS', 'PR', 'SC', 'GO', 'MT', 'MS', 'PA', 'AM', 'MA', 'PI', 'RN', 'PB', 'AL', 'SE', 'ES', 'TO', 'RO', 'AC', 'AP', 'RR',
    'EUA', 'USA', 'UK', 'URSS',
    'Art', 'Déco', 'Deco',
}

# Nomes próprios conhecidos (pessoas, lugares, obras)
NOMES_PROPRIOS = {
    # Arquitetos
    'Niemeyer', 'Oscar', 'Lucio', 'Lúcio', 'Costa', 'Reidy', 'Affonso', 'Eduardo',
    'Burle', 'Marx', 'Roberto', 'Marcelo', 'Milton', 'Maurício',
    'Artigas', 'Vilanova', 'Mendes', 'Rocha', 'Paulo', 'Lina', 'Bardi',
    'Warchavchik', 'Gregori', 'Rino', 'Levi', 'Bratke', 'Oswaldo',
    'Mindlin', 'Henrique', 'Jorge', 'Moreira', 'Vital', 'Brazil',
    'Lelé', 'João', 'Filgueiras', 'Lima', 'Acácio', 'Gil', 'Borsoi',
    'Delfim', 'Amorim', 'Heitor', 'Maia', 'Neto', 'Luis', 'Nunes',
    'Attílio', 'Corrêa', 'Camargo', 'Almeida', 'Francisco', 'Bolonha',
    'Aldary', 'Toledo', 'Carlos', 'Leão', 'Ernani', 'Vasconcellos',
    'Alcides', 'Rocha', 'Miranda', 'Magnani', 'Severiano', 'Porto',
    'Abelardo', 'Souza', 'Hélio', 'Duarte', 'Icaro', 'Castro', 'Mello',
    'Edgar', 'Graeff', 'Demétrio', 'Ribeiro', 'Décio', 'Tozzi',
    'Joaquim', 'Cardozo', 'Cândido', 'Portinari', 'Ceschiatti', 'Alfredo',
    'Bruno', 'Giorgi', 'José', 'Pedrosa', 'Mário', 'Andrade', 'Oswald',
    'Manuel', 'Bandeira', 'Drummond', 'Capanema', 'Gustavo',
    'Le', 'Corbusier', 'Mies', 'Rohe', 'Gropius', 'Wright', 'Frank', 'Lloyd',
    'Aalto', 'Alvar', 'Kahn', 'Louis', 'Siza', 'Álvaro', 'Ando', 'Tadao',
    'Zaha', 'Hadid', 'Gehry', 'Piano', 'Renzo', 'Foster', 'Norman',
    'Joel', 'Campolina', 'Saul', 'Vilela', 'Marques', 'Miguel', 'Vorcaro',
    'Maria', 'Carmo', 'Schwab', 'Ruth', 'Verde', 'Zein',
    'Sylvia', 'Ficher', 'Hugo', 'Segawa', 'Carlos', 'Lemos', 'Yves', 'Bruand',
    'Lauro', 'Cavalcanti', 'Roberto', 'Conduru', 'Abilio', 'Guerra',
    'Fernando', 'Chacel', 'Haruyoshi', 'Ono', 'Rosa', 'Kliass',
    'Flávio', 'Carvalho', 'Humberto', 'Mauro', 'Peixoto',
    # Lugares
    'Brasil', 'Brazil', 'Brasília', 'Brasilia', 'Rio', 'Janeiro', 'São', 'Paulo',
    'Belo', 'Horizonte', 'Salvador', 'Recife', 'Fortaleza', 'Curitiba',
    'Porto', 'Alegre', 'Belém', 'Manaus', 'Goiânia', 'Campinas', 'Santos',
    'Niterói', 'Uberlândia', 'Ribeirão', 'Preto', 'Juiz', 'Fora',
    'Cataguases', 'Ouro', 'Diamantina', 'Mariana', 'Congonhas', 'Tiradentes',
    'Petrópolis', 'Friburgo', 'Teresópolis', 'Campos', 'Goytacazes',
    'Pampulha', 'Pedregulho', 'Ceilândia', 'Taguatinga', 'Planaltina',
    'Copacabana', 'Ipanema', 'Leblon', 'Flamengo', 'Botafogo', 'Tijuca',
    'Minas', 'Gerais', 'Bahia', 'Pernambuco', 'Ceará', 'Paraná', 'Goiás',
    'Paraíba', 'Maranhão', 'Piauí', 'Alagoas', 'Sergipe', 'Espírito', 'Santo',
    'Triângulo', 'Mineiro', 'Paranaíba', 'Zona', 'Mata',
    'Nordeste', 'Norte', 'Sul', 'Sudeste', 'Centro-Oeste',
    'Portugal', 'Lisboa', 'Madrid', 'Paris', 'Roma', 'Berlim', 'Londres',
    'Nova', 'York', 'Chicago', 'Los', 'Angeles', 'Tóquio', 'Pequim',
    'Stuttgart', 'Weissenhof', 'Marselha', 'Chandigarh',
    'Alva', 'Estrela',
    # Obras/Publicações
    'Itamaraty', 'Itamarati', 'Planalto', 'Alvorada', 'Jaburu',
    'Ministério', 'Educação', 'Saúde', 'Fazenda', 'Justiça', 'Trabalho',
    'Congresso', 'Nacional', 'Senado', 'Câmara', 'Deputados',
    'Catedral', 'Metropolitana', 'Teatro', 'Municipal', 'Nacional',
    'Biblioteca', 'Museu', 'Arte', 'Moderna', 'Contemporânea',
    'Pedregulho', 'Prefeito', 'Mendes', 'Moraes',
    'Parque', 'Guinle', 'Ibirapuera', 'Flamengo',
    'Copan', 'Itália', 'Triângulo', 'Esther', 'Columbus',
    'Hotel', 'Quitandinha', 'Ouro', 'Verde', 'Tropical', 'Nacional',
    'Builds', 'Módulo', 'Acrópole', 'Habitat', 'Projeto', 'Casa',
    'Carré', 'Bleu', "L'Architecture", "d'Aujourd'hui",
    # Períodos/Movimentos
    'Modernismo', 'Modernista', 'Moderno', 'Moderna', 'Modernos', 'Modernas',
    'Colonial', 'Colônia', 'Império', 'República',
    'Barroco', 'Neoclássico', 'Eclético', 'Ecletismo',
    'Contemporâneo', 'Contemporânea',
    'Racionalismo', 'Racionalista', 'Brutalismo', 'Brutalista',
    'Internacional', 'Tropicalismo',
}

# Palavras que devem ficar em minúsculas (artigos, preposições, conjunções)
MINUSCULAS = {
    'a', 'o', 'as', 'os', 'um', 'uma', 'uns', 'umas',
    'de', 'da', 'do', 'das', 'dos', 'dum', 'duma',
    'em', 'na', 'no', 'nas', 'nos', 'num', 'numa',
    'por', 'para', 'pela', 'pelo', 'pelas', 'pelos',
    'com', 'sem',
    'e', 'ou', 'mas', 'nem', 'que', 'se', 'como',
    'entre', 'sobre', 'sob', 'até', 'após', 'desde', 'durante',
    'à', 'às', 'ao', 'aos',
    'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or', 'but',
    'y', 'el', 'la', 'los', 'las', 'del', 'en', 'con', 'por', 'para',
}


def eh_sigla(palavra):
    """Verifica se é uma sigla."""
    # Sigla conhecida
    if palavra.upper() in SIGLAS:
        return True
    # Padrão de sigla: 2-5 letras maiúsculas
    if re.match(r'^[A-Z]{2,5}$', palavra):
        return True
    # Sigla com número (ex: M2, 3D)
    if re.match(r'^[A-Z0-9]{2,5}$', palavra) and any(c.isalpha() for c in palavra):
        return True
    return False


def eh_nome_proprio(palavra):
    """Verifica se é um nome próprio conhecido."""
    # Remove pontuação para comparação
    palavra_limpa = re.sub(r'[^\w]', '', palavra)
    return palavra_limpa in NOMES_PROPRIOS or palavra_limpa.capitalize() in NOMES_PROPRIOS


def capitalizar_palavra(palavra, posicao, eh_subtitulo=False):
    """Capitaliza uma palavra conforme as regras."""
    # Preserva pontuação inicial
    prefixo = ''
    sufixo = ''
    match_inicio = re.match(r'^([^\w]+)', palavra)
    match_fim = re.search(r'([^\w]+)$', palavra)
    if match_inicio:
        prefixo = match_inicio.group(1)
        palavra = palavra[len(prefixo):]
    if match_fim:
        sufixo = match_fim.group(1)
        palavra = palavra[:-len(sufixo)]

    if not palavra:
        return prefixo + sufixo

    # Siglas: sempre maiúsculas
    if eh_sigla(palavra):
        return prefixo + palavra.upper() + sufixo

    # Nomes próprios: capitalizar
    if eh_nome_proprio(palavra):
        return prefixo + palavra.capitalize() + sufixo

    # Palavras que devem ficar em minúsculas (exceto no início)
    if palavra.lower() in MINUSCULAS:
        if posicao == 0 and not eh_subtitulo:
            return prefixo + palavra.capitalize() + sufixo
        else:
            return prefixo + palavra.lower() + sufixo

    # Primeira palavra: capitalizar
    if posicao == 0:
        return prefixo + palavra.capitalize() + sufixo

    # Demais palavras: minúsculas
    return prefixo + palavra.lower() + sufixo


def normalizar_titulo(titulo):
    """Normaliza um título."""
    if not titulo:
        return titulo

    # Separa título e subtítulo
    partes = titulo.split(': ', 1)
    titulo_principal = partes[0]
    subtitulo = partes[1] if len(partes) > 1 else None

    # Processa título principal
    palavras = titulo_principal.split()
    palavras_normalizadas = []
    for i, palavra in enumerate(palavras):
        palavras_normalizadas.append(capitalizar_palavra(palavra, i, eh_subtitulo=False))
    titulo_normalizado = ' '.join(palavras_normalizadas)

    # Processa subtítulo
    if subtitulo:
        palavras_sub = subtitulo.split()
        palavras_sub_norm = []
        for i, palavra in enumerate(palavras_sub):
            palavras_sub_norm.append(capitalizar_palavra(palavra, i, eh_subtitulo=True))
        subtitulo_normalizado = ' '.join(palavras_sub_norm)
        return titulo_normalizado, subtitulo_normalizado

    return titulo_normalizado, None


def processar_yaml(caminho):
    """Processa um arquivo YAML."""
    with open(caminho, 'r', encoding='utf-8') as f:
        dados = yaml.safe_load(f)

    titulo_original = dados.get('titulo', '')
    subtitulo_original = dados.get('subtitulo')

    # Se título está em CAIXA ALTA ou tem problemas
    titulo_norm, subtitulo_extraido = normalizar_titulo(titulo_original)

    # Se tinha subtítulo no campo separado
    if subtitulo_original and not subtitulo_extraido:
        _, subtitulo_norm = normalizar_titulo(': ' + subtitulo_original)
        subtitulo_norm = subtitulo_norm if subtitulo_norm else subtitulo_original
    elif subtitulo_extraido:
        subtitulo_norm = subtitulo_extraido
    else:
        subtitulo_norm = None

    return titulo_original, titulo_norm, subtitulo_original, subtitulo_norm, dados


# Ordem dos campos no YAML
ORDEM_CAMPOS = [
    'id', 'seminario', 'secao', 'titulo', 'subtitulo', 'locale',
    'autores_raw', 'resumo', 'palavras_chave', 'resumo_en', 'palavras_chave_en',
    'texto', 'figuras', 'referencias',
    'arquivo_fonte', 'arquivo_pdf_original', 'arquivo_pdf', 'status'
]


def salvar_yaml_ordenado(caminho, dados):
    """Salva YAML mantendo ordem dos campos."""
    # Ordena os campos
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
    print("Normalizando títulos e subtítulos...\n")

    alterados = 0
    for yaml_file in sorted(YAML_DIR.glob("sdbr12-*.yaml")):
        titulo_orig, titulo_norm, sub_orig, sub_norm, dados = processar_yaml(yaml_file)

        mudou = False

        # Verifica se título mudou
        if titulo_orig != titulo_norm:
            print(f"{yaml_file.name}:")
            print(f"  ANTES:  {titulo_orig}")
            print(f"  DEPOIS: {titulo_norm}")
            dados['titulo'] = titulo_norm
            mudou = True

        # Verifica se subtítulo mudou
        if sub_norm and sub_norm != sub_orig:
            if not mudou:
                print(f"{yaml_file.name}:")
            print(f"  SUB ANTES:  {sub_orig}")
            print(f"  SUB DEPOIS: {sub_norm}")
            dados['subtitulo'] = sub_norm
            mudou = True

        if mudou:
            salvar_yaml_ordenado(yaml_file, dados)
            alterados += 1
            print()

    print(f"\n=== Total: {alterados} arquivos alterados ===")


if __name__ == "__main__":
    main()
