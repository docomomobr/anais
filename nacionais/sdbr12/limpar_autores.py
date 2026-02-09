#!/usr/bin/env python3
"""
Limpa o campo autores_raw nos YAMLs do sdbr12.

Problemas detectados:
- Endereços postais misturados
- Telefones
- Títulos acadêmicos (PhD, MSc, Doutor)
- Afiliações inline
- Placeholders ("Instituição, Endereço...")
- Traços no final dos nomes
- "graduação XXXX" inline
"""

import yaml
import re
from pathlib import Path

YAML_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/yaml")

# Padrões que indicam que NÃO é um nome de autor
PADROES_EXCLUIR = [
    r'^\d+',  # Começa com número (endereço)
    r'^\+\d',  # Telefone internacional
    r'^[PF]:\s*\+',  # Telefone/Fax com prefixo P: ou F:
    r'\d{5}-?\d{3}',  # CEP brasileiro
    r'\d{5}$',  # Termina com CEP (5 dígitos)
    r'@',  # Email
    r'orcid\.org',  # ORCID
    r'\b(Rua|Av\.|Avenida|Street|St\.|Room|Cra\.|ap\s+\d)\b',  # Endereço
    r'\b(PhD|MSc|Dr\.|Dra\.|Prof\.|Profa\.)\b',  # Títulos acadêmicos como linha separada
    r'^(PhD|MSc|Doutor|Mestre|Professor|Graduando|Mestrando|Doutorando)',  # Título no início
    r'Instituição,\s*Endereço',  # Placeholder
    r'Cidade,\s*País',  # Placeholder
    r'^\s*-?\s*$',  # Linha vazia ou só traço
    r'^(Universidade|Universidad|Faculdade|Facultad|Instituto|Institute)\b',  # Nome de instituição
    r',\s*(Il|CA|NY|TX|FL)\s*\d*$',  # Cidade americana com estado
    r'Nome\s+Completo\s+Autor',  # Placeholder
    r'^[A-Z]{2,}-[A-Z]{2,}\b',  # Sigla composta (MDU-UFPE)
    r'oficina\s+\w+\d+',  # Número de sala/escritório
]

# Padrões para limpar do nome
PADROES_LIMPAR = [
    (r'\s*-\s*$', ''),  # Traço no final
    (r',\s*graduação\s+\w+', ''),  # ", graduação XXXX"
    (r',\s*grad\.\s+\w+', ''),  # ", grad. XXXX"
    (r'\s+\d+$', ''),  # Números no final (ex: "Nome 1")
]

# Siglas de universidades (para detectar afiliação inline)
UNIVERSIDADES = [
    'UFMG', 'USP', 'UFRJ', 'UNB', 'UFBA', 'UFRGS', 'UFPE', 'UFRN', 'UFC',
    'UFPB', 'UFPR', 'UFSC', 'UFU', 'UFG', 'UFES', 'UFMA', 'UFPI', 'UFAL',
    'UFS', 'UFMT', 'UFMS', 'UFPA', 'UFAM', 'UEMA', 'UNICAMP', 'UNESP',
    'PUC', 'MACKENZIE', 'FAAP', 'UNICEP', 'IIT', 'MIT', 'AA',
]

ORDEM_CAMPOS = [
    'id', 'seminario', 'secao', 'titulo', 'subtitulo', 'locale',
    'autores_raw', 'resumo', 'palavras_chave', 'resumo_en', 'palavras_chave_en',
    'texto', 'figuras', 'referencias',
    'arquivo_fonte', 'arquivo_pdf_original', 'arquivo_pdf', 'status'
]


def eh_linha_excluir(linha):
    """Verifica se a linha deve ser excluída."""
    if not linha or not linha.strip():
        return True

    for padrao in PADROES_EXCLUIR:
        if re.search(padrao, linha, re.IGNORECASE):
            return True

    # Verifica se é afiliação (sigla de universidade + endereço)
    for uni in UNIVERSIDADES:
        if uni in linha.upper() and ('Rua' in linha or 'rua' in linha or
                                      re.search(r'\d{5}', linha) or
                                      'Endereço' in linha):
            return True

    return False


def limpar_nome(nome):
    """Limpa um nome de autor."""
    if not nome:
        return None

    nome = nome.strip()

    # Aplica padrões de limpeza
    for padrao, substituto in PADROES_LIMPAR:
        nome = re.sub(padrao, substituto, nome, flags=re.IGNORECASE)

    nome = nome.strip()

    # Verifica se sobrou algo válido (pelo menos 2 palavras ou nome composto)
    if not nome or len(nome) < 3:
        return None

    # Verifica se parece um nome (tem pelo menos uma letra maiúscula no início de palavra)
    palavras = nome.split()
    if len(palavras) < 2:
        return None

    return nome


def processar_autores(autores_raw):
    """Processa lista de autores, removendo lixo."""
    if not autores_raw:
        return []

    autores_limpos = []
    for autor in autores_raw:
        if eh_linha_excluir(autor):
            continue

        nome_limpo = limpar_nome(autor)
        if nome_limpo:
            autores_limpos.append(nome_limpo)

    return autores_limpos


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
    print("Limpando campo autores_raw...\n")

    alterados = 0
    problemas = []

    for yaml_file in sorted(YAML_DIR.glob("sdbr12-*.yaml")):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            dados = yaml.safe_load(f)

        autores_orig = dados.get('autores_raw', [])
        autores_limpos = processar_autores(autores_orig)

        # Verifica se houve mudança
        if autores_orig != autores_limpos:
            print(f"{yaml_file.name}:")
            print(f"  ANTES:  {autores_orig}")
            print(f"  DEPOIS: {autores_limpos}")
            print()

            dados['autores_raw'] = autores_limpos if autores_limpos else None
            salvar_yaml_ordenado(yaml_file, dados)
            alterados += 1

        # Registra problemas (sem autores)
        if not autores_limpos:
            problemas.append(yaml_file.name)

    print(f"{'=' * 60}")
    print(f"Total alterados: {alterados}")

    if problemas:
        print(f"\nArtigos SEM autores ({len(problemas)}):")
        for p in problemas:
            print(f"  - {p}")


if __name__ == "__main__":
    main()
