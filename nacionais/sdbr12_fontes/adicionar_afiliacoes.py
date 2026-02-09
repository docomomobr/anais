#!/usr/bin/env python3
"""
Adiciona afiliações aos autores estruturados.
Extrai do autores_raw e normaliza para formato UNIDADE-UNIVERSIDADE.
"""

import yaml
import re
from pathlib import Path

YAML_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/yaml")

# Mapeamento de afiliações para formato normalizado
AFILIACOES = {
    # USP
    'universidade de são paulo, faculdade de arquitetura e urbanismo': 'FAU-USP',
    'faculdade de arquitetura e urbanismo da usp': 'FAU-USP',
    'faculdade de arquitetura e urbanismo, universidade de são paulo': 'FAU-USP',
    'fau usp': 'FAU-USP',
    'fau-usp': 'FAU-USP',
    'fauusp': 'FAU-USP',
    'instituto de arquitetura e urbanismo da usp': 'IAU-USP',
    'instituto de arquitetura e urbanismo, universidade de são paulo': 'IAU-USP',
    'iau usp': 'IAU-USP',
    'iau-usp': 'IAU-USP',
    'universidade de são paulo': 'USP',
    'usp': 'USP',

    # UFRGS
    'propar ufrgs': 'PROPAR-UFRGS',
    'propar-ufrgs': 'PROPAR-UFRGS',
    'propar, ufrgs': 'PROPAR-UFRGS',
    'universidade federal do rio grande do sul': 'UFRGS',
    'ufrgs': 'UFRGS',
    'faculdade de arquitetura, ufrgs': 'FA-UFRGS',
    'faculdade de arquitetura da ufrgs': 'FA-UFRGS',

    # UFPE
    'mdu ufpe': 'MDU-UFPE',
    'mdu-ufpe': 'MDU-UFPE',
    'mdu - ufpe': 'MDU-UFPE',
    'universidade federal de pernambuco': 'UFPE',
    'ufpe': 'UFPE',

    # UFRJ
    'proarq ufrj': 'PROARQ-UFRJ',
    'proarq-ufrj': 'PROARQ-UFRJ',
    'prourb ufrj': 'PROURB-UFRJ',
    'prourb-ufrj': 'PROURB-UFRJ',
    'universidade federal do rio de janeiro': 'UFRJ',
    'ufrj': 'UFRJ',
    'faculdade de arquitetura e urbanismo, ufrj': 'FAU-UFRJ',

    # UnB
    'universidade de brasília': 'UnB',
    'universidade de brasília, faculdade de arquitetura e urbanismo': 'FAU-UnB',
    'faculdade de arquitetura e urbanismo, universidade de brasília': 'FAU-UnB',
    'fau unb': 'FAU-UnB',
    'unb': 'UnB',

    # UFBA
    'universidade federal da bahia': 'UFBA',
    'ufba': 'UFBA',
    'faculdade de arquitetura da ufba': 'FAUFBA',
    'faufba': 'FAUFBA',
    'ppg-au ufba': 'PPGAU-UFBA',

    # UFU
    'universidade federal de uberlândia': 'UFU',
    'ufu': 'UFU',
    'faculdade de arquitetura e urbanismo e design, ufu': 'FAUeD-UFU',
    'faued ufu': 'FAUeD-UFU',

    # Outras federais
    'universidade federal do paraná': 'UFPR',
    'ufpr': 'UFPR',
    'universidade federal de santa catarina': 'UFSC',
    'ufsc': 'UFSC',
    'universidade federal do ceará': 'UFC',
    'ufc': 'UFC',
    'universidade federal do rio grande do norte': 'UFRN',
    'ufrn': 'UFRN',
    'universidade federal da paraíba': 'UFPB',
    'ufpb': 'UFPB',
    'universidade federal do maranhão': 'UFMA',
    'ufma': 'UFMA',
    'universidade federal do pará': 'UFPA',
    'ufpa': 'UFPA',
    'universidade federal de minas gerais': 'UFMG',
    'ufmg': 'UFMG',
    'universidade federal do espírito santo': 'UFES',
    'ufes': 'UFES',
    'universidade federal de goiás': 'UFG',
    'ufg': 'UFG',

    # Estaduais
    'universidade estadual de campinas': 'UNICAMP',
    'unicamp': 'UNICAMP',
    'universidade estadual paulista': 'UNESP',
    'unesp': 'UNESP',
    'universidade estadual de maringá': 'UEM',
    'uem': 'UEM',
    'universidade estadual do maranhão': 'UEMA',
    'uema': 'UEMA',

    # Privadas/Comunitárias
    'pontifícia universidade católica': 'PUC',
    'puc': 'PUC',
    'universidade presbiteriana mackenzie': 'Mackenzie',
    'mackenzie': 'Mackenzie',
    'universidade de sorocaba': 'UNISO',
    'uniso': 'UNISO',
    'unidade de ensino superior dom bosco': 'UNDB',
    'undb': 'UNDB',

    # Estrangeiras
    'universidad de los andes': 'Universidad de los Andes',
    'universidad de los andes, facultad de arquitectura y diseño': 'Universidad de los Andes',
    'illinois institute of technology': 'IIT',
    'iit': 'IIT',
}

# Padrões que indicam afiliação (não nome de pessoa)
PADROES_AFILIACAO = [
    r'^universidade',
    r'^universidad',
    r'^faculdade',
    r'^instituto',
    r'^pontifícia',
    r'^fau[- ]',
    r'^iau[- ]',
    r'^propar',
    r'^prourb',
    r'^proarq',
    r'^mdu[- ]',
    r'^ppg',
    r'\b(usp|ufrj|ufba|ufrgs|ufpe|unb|ufu|ufpr|ufsc|ufc|ufrn|ufpb|ufmg)\b',
]

ORDEM_CAMPOS = [
    'id', 'seminario', 'secao', 'titulo', 'subtitulo', 'locale',
    'autores_raw', 'autores', 'resumo', 'palavras_chave', 'resumo_en', 'palavras_chave_en',
    'texto', 'figuras', 'referencias',
    'arquivo_fonte', 'arquivo_pdf_original', 'arquivo_pdf', 'status'
]


def eh_afiliacao(linha):
    """Verifica se a linha parece ser uma afiliação."""
    if not linha:
        return False
    linha_lower = linha.lower().strip()
    for padrao in PADROES_AFILIACAO:
        if re.search(padrao, linha_lower, re.IGNORECASE):
            return True
    return False


def normalizar_afiliacao(afiliacao):
    """Normaliza afiliação para formato padrão."""
    if not afiliacao:
        return None

    # Limpa a string
    afiliacao_limpa = afiliacao.strip()
    afiliacao_lower = afiliacao_limpa.lower()

    # Remove endereços e informações extras
    afiliacao_lower = re.sub(r',?\s*(rua|av\.|avenida|cra\.).*$', '', afiliacao_lower, flags=re.IGNORECASE)
    afiliacao_lower = afiliacao_lower.strip().rstrip(',').strip()

    # Busca no dicionário
    if afiliacao_lower in AFILIACOES:
        return AFILIACOES[afiliacao_lower]

    # Tenta match parcial
    for chave, valor in AFILIACOES.items():
        if chave in afiliacao_lower or afiliacao_lower in chave:
            return valor

    # Se não encontrou, retorna original (será revisado manualmente)
    return afiliacao_limpa


def extrair_afiliacoes(autores_raw, autores):
    """Extrai afiliações do autores_raw e associa aos autores."""
    if not autores_raw or not autores:
        return autores

    # Estratégia: linhas alternadas (nome, afiliação, nome, afiliação...)
    # Ou: detectar padrão de afiliação na linha seguinte ao nome

    autores_atualizados = []

    for autor in autores:
        nome_completo = f"{autor.get('givenname', '')} {autor.get('familyname', '')}".strip()

        # Busca o nome no autores_raw
        afiliacao_encontrada = None
        for i, linha in enumerate(autores_raw):
            if not linha:
                continue

            # Verifica se esta linha contém o nome do autor
            linha_lower = linha.lower()
            nome_lower = nome_completo.lower()
            familyname_lower = autor.get('familyname', '').lower()

            # Match por sobrenome (mais confiável)
            if familyname_lower and familyname_lower in linha_lower:
                # Próxima linha pode ser a afiliação
                if i + 1 < len(autores_raw):
                    proxima = autores_raw[i + 1]
                    if eh_afiliacao(proxima):
                        afiliacao_encontrada = normalizar_afiliacao(proxima)
                        break

        autor_atualizado = autor.copy()
        if afiliacao_encontrada:
            autor_atualizado['affiliation'] = afiliacao_encontrada

        autores_atualizados.append(autor_atualizado)

    return autores_atualizados


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
    print("Adicionando afiliações aos autores...\n")

    alterados = 0
    sem_afiliacao = []

    for yaml_file in sorted(YAML_DIR.glob("sdbr12-*.yaml")):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            dados = yaml.safe_load(f)

        autores_raw = dados.get('autores_raw')
        autores = dados.get('autores')

        if not autores:
            continue

        autores_com_afiliacao = extrair_afiliacoes(autores_raw, autores)

        # Verifica se houve mudança
        if autores_com_afiliacao != autores:
            dados['autores'] = autores_com_afiliacao
            salvar_yaml_ordenado(yaml_file, dados)
            alterados += 1

            # Mostra resultado
            print(f"{yaml_file.name}:")
            for a in autores_com_afiliacao:
                afil = a.get('affiliation', '(sem)')
                print(f"  {a['givenname']} {a['familyname']} → {afil}")
            print()

        # Registra autores sem afiliação
        for a in autores_com_afiliacao:
            if 'affiliation' not in a:
                sem_afiliacao.append(f"{yaml_file.name}: {a['givenname']} {a['familyname']}")

    print(f"{'=' * 60}")
    print(f"Total alterados: {alterados}")

    if sem_afiliacao:
        print(f"\nAutores sem afiliação ({len(sem_afiliacao)}):")
        for s in sem_afiliacao[:20]:
            print(f"  - {s}")
        if len(sem_afiliacao) > 20:
            print(f"  ... e mais {len(sem_afiliacao) - 20}")


if __name__ == "__main__":
    main()
