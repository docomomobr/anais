#!/usr/bin/env python3
"""
Fix truncated PDF names in YAML files.
"""

import os
import yaml
from pathlib import Path

BASE_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes")
YAML_DIR = BASE_DIR / "yaml"
ANAIS_DIR = BASE_DIR / "anais"

def listar_pdfs():
    """Lista todos os PDFs disponíveis."""
    pdfs = []
    for root, dirs, files in os.walk(ANAIS_DIR):
        if 'programacao' in root or 'programação' in root:
            continue
        for f in files:
            if f.endswith('.pdf') and not f.startswith('folha'):
                pdfs.append(f)
    return list(set(pdfs))  # Remove duplicates

def carregar_yaml(caminho):
    """Carrega um arquivo YAML."""
    with open(caminho, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def salvar_yaml(caminho, dados):
    """Salva um arquivo YAML sem truncar strings."""
    with open(caminho, 'w', encoding='utf-8') as f:
        yaml.dump(dados, f, default_flow_style=False, allow_unicode=True, width=10000)

def main():
    pdfs = listar_pdfs()
    print(f"Encontrados {len(pdfs)} PDFs únicos")

    corrigidos = 0
    for yaml_file in sorted(YAML_DIR.glob("sdbr12-*.yaml")):
        dados = carregar_yaml(yaml_file)
        pdf_atual = dados.get('arquivo_pdf_original')

        if pdf_atual and pdf_atual != 'null':
            # Verifica se está truncado (termina sem .pdf)
            if not pdf_atual.endswith('.pdf'):
                # Procura o PDF completo
                for pdf in pdfs:
                    if pdf.startswith(pdf_atual[:50]):
                        dados['arquivo_pdf_original'] = pdf
                        salvar_yaml(yaml_file, dados)
                        print(f"✓ {yaml_file.name}: {pdf[:80]}...")
                        corrigidos += 1
                        break
            else:
                # Já está completo, mas vamos re-salvar com width maior
                salvar_yaml(yaml_file, dados)

    print(f"\nTotal corrigidos: {corrigidos}")

if __name__ == "__main__":
    main()
