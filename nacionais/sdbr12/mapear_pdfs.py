#!/usr/bin/env python3
"""
Script para mapear PDFs aos artigos YAML do sdbr12.
Usa correspondência de título e autores para encontrar o PDF correto.
"""

import os
import re
import yaml
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes")
YAML_DIR = BASE_DIR / "yaml"
ANAIS_DIR = BASE_DIR / "anais"

def normalizar(texto):
    """Remove acentos, pontuação e converte para minúsculas."""
    if not texto:
        return ""
    import unicodedata
    # Remove acentos
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    # Remove pontuação e converte para minúsculas
    texto = re.sub(r'[^\w\s]', ' ', texto.lower())
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def extrair_sobrenome(nome_completo):
    """Extrai o sobrenome de um nome completo."""
    partes = nome_completo.strip().split()
    if partes:
        return partes[-1].upper()
    return ""

def similaridade(a, b):
    """Calcula similaridade entre duas strings."""
    return SequenceMatcher(None, normalizar(a), normalizar(b)).ratio()

def carregar_yaml(caminho):
    """Carrega um arquivo YAML."""
    with open(caminho, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def salvar_yaml(caminho, dados):
    """Salva um arquivo YAML sem truncar strings."""
    with open(caminho, 'w', encoding='utf-8') as f:
        yaml.dump(dados, f, default_flow_style=False, allow_unicode=True, width=10000)

def listar_pdfs():
    """Lista todos os PDFs disponíveis."""
    pdfs = []
    for root, dirs, files in os.walk(ANAIS_DIR):
        # Ignorar diretórios de programação e folha de rosto
        if 'programacao' in root or 'programação' in root:
            continue
        for f in files:
            if f.endswith('.pdf') and not f.startswith('folha'):
                caminho = os.path.join(root, f)
                pdfs.append(caminho)
    return pdfs

def extrair_info_pdf(nome_pdf):
    """Extrai informações do nome do PDF."""
    # Formato: E01-SOBRENOME, INICIAL. Titulo do artigo..pdf
    # ou: E02-SOBRENOME_ SOBRENOME2. Titulo..pdf
    nome = os.path.basename(nome_pdf)

    # Remove extensão
    nome = re.sub(r'\.pdf$', '', nome, flags=re.IGNORECASE)

    # Extrai eixo
    match_eixo = re.match(r'E0?(\d)', nome)
    eixo = int(match_eixo.group(1)) if match_eixo else None

    # Remove prefixo do eixo
    nome = re.sub(r'^E0?\d-?', '', nome)

    # Tenta separar autores e título pelo último ponto antes do título
    # Formato comum: SOBRENOME, INICIAL_ SOBRENOME2. Titulo..
    partes = nome.split('. ', 1)
    if len(partes) == 2:
        autores_str = partes[0]
        titulo = partes[1].rstrip('.')
    else:
        # Tenta split por hífen
        partes = nome.split(' - ', 1)
        if len(partes) == 2:
            autores_str = partes[0]
            titulo = partes[1].rstrip('.')
        else:
            autores_str = ""
            titulo = nome

    # Extrai sobrenomes dos autores
    sobrenomes = []
    # Padrões: SOBRENOME, I._ SOBRENOME2 ou SOBRENOME_ et al.
    autores_partes = re.split(r'[_,;]', autores_str)
    for parte in autores_partes:
        parte = parte.strip()
        if parte and len(parte) > 2 and parte not in ['et al', 'et al.']:
            # Pega a primeira palavra (geralmente o sobrenome)
            palavras = parte.split()
            if palavras:
                sobrenome = palavras[0].strip('.')
                if len(sobrenome) > 2:
                    sobrenomes.append(sobrenome.upper())

    return {
        'eixo': eixo,
        'sobrenomes': sobrenomes,
        'titulo': titulo,
        'titulo_norm': normalizar(titulo)
    }

def encontrar_pdf_correspondente(yaml_data, pdfs_info):
    """Encontra o PDF que corresponde a um artigo YAML."""
    titulo_yaml = yaml_data.get('titulo', '')
    autores_raw = yaml_data.get('autores_raw', [])

    # Extrai sobrenomes dos autores do YAML
    sobrenomes_yaml = []
    for autor in autores_raw:
        sobrenome = extrair_sobrenome(autor)
        if sobrenome:
            sobrenomes_yaml.append(sobrenome)

    titulo_norm = normalizar(titulo_yaml)

    melhores = []

    for caminho, info in pdfs_info.items():
        score = 0

        # Verifica correspondência de sobrenomes
        sobrenomes_comuns = set(sobrenomes_yaml) & set(info['sobrenomes'])
        if sobrenomes_comuns:
            score += len(sobrenomes_comuns) * 30

        # Verifica correspondência de título
        sim_titulo = similaridade(titulo_yaml, info['titulo'])
        score += sim_titulo * 70

        # Verifica palavras-chave do título
        palavras_yaml = set(titulo_norm.split())
        palavras_pdf = set(info['titulo_norm'].split())
        palavras_comuns = palavras_yaml & palavras_pdf
        # Remove palavras muito comuns
        palavras_comuns -= {'de', 'da', 'do', 'das', 'dos', 'e', 'a', 'o', 'as', 'os', 'em', 'no', 'na', 'um', 'uma'}
        if palavras_comuns:
            score += len(palavras_comuns) * 5

        if score > 20:  # Threshold mínimo
            melhores.append((score, caminho, info))

    # Ordena por score decrescente
    melhores.sort(reverse=True, key=lambda x: x[0])

    if melhores:
        return melhores[0][1], melhores[0][0]
    return None, 0

def main():
    print("Carregando lista de PDFs...")
    pdfs = listar_pdfs()
    print(f"  Encontrados {len(pdfs)} PDFs")

    # Analisa todos os PDFs
    pdfs_info = {}
    for pdf in pdfs:
        info = extrair_info_pdf(pdf)
        pdfs_info[pdf] = info

    # Lista de YAMLs sem PDF mapeado
    yamls_sem_pdf = []
    for yaml_file in sorted(YAML_DIR.glob("sdbr12-*.yaml")):
        dados = carregar_yaml(yaml_file)
        if dados.get('arquivo_pdf_original') is None:
            yamls_sem_pdf.append(yaml_file)

    print(f"\nProcessando {len(yamls_sem_pdf)} artigos sem PDF mapeado...")

    mapeados = 0
    nao_mapeados = []

    for yaml_file in yamls_sem_pdf:
        dados = carregar_yaml(yaml_file)
        artigo_id = dados.get('id', yaml_file.stem)
        titulo = dados.get('titulo', '')[:60]

        pdf_encontrado, score = encontrar_pdf_correspondente(dados, pdfs_info)

        if pdf_encontrado and score > 40:
            # Atualiza o YAML
            nome_pdf = os.path.basename(pdf_encontrado)
            dados['arquivo_pdf_original'] = nome_pdf
            salvar_yaml(yaml_file, dados)

            print(f"  ✓ {artigo_id}: {titulo}...")
            print(f"    → {nome_pdf} (score: {score:.1f})")
            mapeados += 1

            # Remove do pool de PDFs disponíveis
            del pdfs_info[pdf_encontrado]
        else:
            print(f"  ✗ {artigo_id}: {titulo}...")
            nao_mapeados.append((artigo_id, dados))

    print(f"\n=== Resumo ===")
    print(f"Mapeados automaticamente: {mapeados}")
    print(f"Não mapeados: {len(nao_mapeados)}")

    if nao_mapeados:
        print("\nArtigos não mapeados (precisam revisão manual):")
        for artigo_id, dados in nao_mapeados:
            titulo = dados.get('titulo', '')[:70]
            autores = dados.get('autores_raw', [])[:2]
            autores_str = ', '.join(autores) if autores else 'Sem autor'
            print(f"  - {artigo_id}: {titulo}")
            print(f"    Autores: {autores_str}")

    print("\nPDFs restantes não mapeados:")
    for pdf in pdfs_info.keys():
        nome = os.path.basename(pdf)
        print(f"  - {nome}")

if __name__ == "__main__":
    main()
