#!/usr/bin/env python3
"""
Script para corrigir nomes de PDFs truncados nos YAMLs.
Relê os YAMLs e salva novamente com width maior.
"""

import os
import yaml
from pathlib import Path

BASE_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes")
YAML_DIR = BASE_DIR / "yaml"
ANAIS_DIR = BASE_DIR / "anais"

def listar_pdfs():
    """Lista todos os PDFs disponíveis com seus nomes completos."""
    pdfs = {}
    for root, dirs, files in os.walk(ANAIS_DIR):
        if 'programacao' in root or 'programação' in root:
            continue
        for f in files:
            if f.endswith('.pdf') and not f.startswith('folha'):
                # Use o início do nome como chave
                key = f[:60]  # primeiros 60 caracteres
                pdfs[key] = f
    return pdfs

def carregar_yaml(caminho):
    """Carrega um arquivo YAML."""
    with open(caminho, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def salvar_yaml(caminho, dados):
    """Salva um arquivo YAML sem truncar strings."""
    # Usa um representer customizado para strings longas
    def str_representer(dumper, data):
        if '\n' in data:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)

    yaml.add_representer(str, str_representer)

    with open(caminho, 'w', encoding='utf-8') as f:
        yaml.dump(dados, f, default_flow_style=False, allow_unicode=True, width=10000)

def main():
    pdfs = listar_pdfs()

    corrigidos = 0
    for yaml_file in sorted(YAML_DIR.glob("sdbr12-*.yaml")):
        dados = carregar_yaml(yaml_file)
        pdf_atual = dados.get('arquivo_pdf_original')

        if pdf_atual and pdf_atual != 'null' and len(pdf_atual) < 120:
            # Tenta encontrar o PDF completo
            for key, nome_completo in pdfs.items():
                if pdf_atual.startswith(key[:50]) or key.startswith(pdf_atual[:50]):
                    if nome_completo != pdf_atual:
                        dados['arquivo_pdf_original'] = nome_completo
                        salvar_yaml(yaml_file, dados)
                        print(f"Corrigido {yaml_file.name}: {nome_completo}")
                        corrigidos += 1
                    break

    print(f"\nTotal corrigidos: {corrigidos}")

if __name__ == "__main__":
    main()
