#!/usr/bin/env python3
"""
Corrige títulos e subtítulos nos YAMLs do sdbr12.

Problemas detectados:
1. titulo contém placeholder ("TÍTULO DO TRABALHO") e subtitulo contém o título real
2. titulo contém título+subtítulo juntos (separados por ": ")
3. titulo em CAIXA ALTA precisa ser normalizado

Regras da norma brasileira de capitalização:
- Título: primeira letra maiúscula, resto minúscula (exceto nomes próprios e siglas)
- Subtítulo: inicia com minúscula (exceto nomes próprios, siglas)
"""

import yaml
import re
from pathlib import Path

YAML_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/yaml")

# Placeholders conhecidos que indicam que o título está errado
PLACEHOLDERS = [
    'TÍTULO DO TRABALHO',
    'TITULO DO TRABALHO',
    'TITLE',
    'TÍTULO',
    'TITULO',
]

# Ordem dos campos no YAML
ORDEM_CAMPOS = [
    'id', 'seminario', 'secao', 'titulo', 'subtitulo', 'locale',
    'autores_raw', 'resumo', 'palavras_chave', 'resumo_en', 'palavras_chave_en',
    'texto', 'figuras', 'referencias',
    'arquivo_fonte', 'arquivo_pdf_original', 'arquivo_pdf', 'status'
]


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


def eh_placeholder(titulo):
    """Verifica se o título é um placeholder."""
    if not titulo:
        return True
    titulo_upper = titulo.strip().upper()
    for p in PLACEHOLDERS:
        if titulo_upper == p or titulo_upper.startswith(p):
            return True
    return False


def eh_caixa_alta(texto):
    """Verifica se o texto está predominantemente em CAIXA ALTA."""
    if not texto:
        return False
    letras = [c for c in texto if c.isalpha()]
    if not letras:
        return False
    maiusculas = sum(1 for c in letras if c.isupper())
    return maiusculas / len(letras) > 0.7


def separar_titulo_subtitulo(texto):
    """Separa título e subtítulo pelo ': '."""
    if not texto:
        return None, None

    # Remove aspas externas se houver
    texto = texto.strip().strip("'\"")

    # Procura o separador ': '
    if ': ' in texto:
        partes = texto.split(': ', 1)
        return partes[0].strip(), partes[1].strip()

    return texto, None


def processar_arquivo(yaml_file):
    """Processa um arquivo YAML e retorna as correções necessárias."""
    with open(yaml_file, 'r', encoding='utf-8') as f:
        dados = yaml.safe_load(f)

    titulo_orig = dados.get('titulo', '')
    subtitulo_orig = dados.get('subtitulo')

    titulo_novo = titulo_orig
    subtitulo_novo = subtitulo_orig
    mudou = False

    # Caso 1: título é placeholder e subtítulo contém o título real
    if eh_placeholder(titulo_orig) and subtitulo_orig:
        titulo_real, sub_real = separar_titulo_subtitulo(subtitulo_orig)
        titulo_novo = titulo_real
        subtitulo_novo = sub_real
        mudou = True

    # Caso 2: título contém título+subtítulo juntos (com ": ")
    elif ': ' in titulo_orig and not subtitulo_orig:
        titulo_novo, subtitulo_novo = separar_titulo_subtitulo(titulo_orig)
        mudou = True

    # Caso 3: título em CAIXA ALTA mas subtítulo já está ok (formatado)
    elif eh_caixa_alta(titulo_orig) and subtitulo_orig and not eh_caixa_alta(subtitulo_orig):
        # O subtítulo parece já estar formatado, provavelmente é o título real
        # Verifica se o subtítulo contém ": " (indicando título: subtítulo)
        if ': ' in subtitulo_orig:
            titulo_real, sub_real = separar_titulo_subtitulo(subtitulo_orig)
            titulo_novo = titulo_real
            subtitulo_novo = sub_real
            mudou = True

    return {
        'dados': dados,
        'titulo_orig': titulo_orig,
        'subtitulo_orig': subtitulo_orig,
        'titulo_novo': titulo_novo,
        'subtitulo_novo': subtitulo_novo,
        'mudou': mudou
    }


def main():
    print("Analisando títulos e subtítulos...\n")

    resultados = []
    for yaml_file in sorted(YAML_DIR.glob("sdbr12-*.yaml")):
        resultado = processar_arquivo(yaml_file)
        resultado['arquivo'] = yaml_file
        resultados.append(resultado)

    # Mostra os que precisam de correção
    print("=" * 80)
    print("CORREÇÕES A FAZER:")
    print("=" * 80)

    alterados = 0
    for r in resultados:
        if r['mudou']:
            alterados += 1
            print(f"\n{r['arquivo'].name}:")
            print(f"  titulo ANTES:    {r['titulo_orig']}")
            print(f"  subtitulo ANTES: {r['subtitulo_orig']}")
            print(f"  titulo DEPOIS:    {r['titulo_novo']}")
            print(f"  subtitulo DEPOIS: {r['subtitulo_novo']}")

    print(f"\n{'=' * 80}")
    print(f"Total: {alterados} arquivos precisam de correção")
    print("=" * 80)

    if alterados > 0:
        resposta = input("\nAplicar correções? (s/n): ")
        if resposta.lower() == 's':
            for r in resultados:
                if r['mudou']:
                    r['dados']['titulo'] = r['titulo_novo']
                    r['dados']['subtitulo'] = r['subtitulo_novo']
                    salvar_yaml_ordenado(r['arquivo'], r['dados'])
                    print(f"  ✓ {r['arquivo'].name}")
            print(f"\n{alterados} arquivos corrigidos.")
        else:
            print("Nenhuma alteração feita.")


if __name__ == "__main__":
    main()
