#!/usr/bin/env python3
"""
Script para processar todos os artigos do 12º Seminário Docomomo Brasil
Extrai metadados completos dos arquivos Word e gera YAMLs
"""

import os
import re
import yaml
from pathlib import Path
from docx import Document

# Diretórios
BASE = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/anais")
OUT = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/yaml")

# Eixos e seus nomes
EIXOS = {
    1: "Eixo 1 - A recepção e a difusão da arquitetura e urbanismo modernos brasileiros",
    2: "Eixo 2 - Práticas de preservação da arquitetura e do urbanismo modernos",
    3: "Eixo 3 - Práticas (ações e projetos) de Educação Patrimonial",
    4: "Eixo 4 - A formação dos futuros profissionais e a preservação do Movimento Moderno"
}

# Custom YAML representer para strings multiline
def str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_representer)


def find_pdf_for_docx(docx_path, eixo_num):
    """Tenta encontrar o PDF correspondente ao Word"""
    docx_name = Path(docx_path).stem.lower()

    # Diretórios de PDF por eixo
    pdf_dirs = {
        1: [BASE / "EIXO 1" / "Eixo 1 PDF",
            BASE / "EIXO 1" / "Eixo 1 corrigido para os anais (joao)"],
        2: [BASE / "EIXO 2" / "Eixo 2"],
        3: [BASE / "EIXO 3" / "Eixo 3"],
        4: [BASE / "EIXO 4" / "Eixo 4"]
    }

    for pdf_dir in pdf_dirs.get(eixo_num, []):
        if pdf_dir.exists():
            for pdf in pdf_dir.glob("*.pdf"):
                pdf_lower = pdf.stem.lower()
                # Correspondência exata ou parcial
                if docx_name in pdf_lower or pdf_lower in docx_name:
                    return pdf.name
                # Tenta por autor
                docx_words = set(docx_name.replace("_", " ").replace("-", " ").split())
                pdf_words = set(pdf_lower.replace("_", " ").replace("-", " ").split())
                if len(docx_words & pdf_words) >= 2:
                    return pdf.name
    return None


def extract_article(docx_path, article_id, eixo_num):
    """Extrai artigo completo do Word"""
    try:
        doc = Document(docx_path)
    except Exception as e:
        print(f"  ERRO ao abrir: {e}")
        return None

    paragraphs = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append({
                'text': text,
                'style': para.style.name if para.style else 'Normal'
            })

    if not paragraphs:
        return None

    # Encontrar índices das seções
    resumo_idx = None
    abstract_idx = None
    refs_idx = None

    for i, p in enumerate(paragraphs):
        text_upper = p['text'].upper()
        if text_upper == 'RESUMO' and resumo_idx is None:
            resumo_idx = i
        elif text_upper in ['ABSTRACT', 'RESUMEN'] and abstract_idx is None:
            abstract_idx = i
        elif refs_idx is None:
            if text_upper.startswith('REFERÊNCIAS') or text_upper.startswith('BIBLIOGRAFIA'):
                refs_idx = i
            elif 'REFERÊNCIAS BIBLIOGRÁFICAS' in text_upper:
                refs_idx = i

    # Extrair título (geralmente nos primeiros parágrafos)
    titulo = ""
    subtitulo = None

    for i in range(min(5, len(paragraphs))):
        text = paragraphs[i]['text']
        # Pular linha do eixo
        if any(x in text.upper() for x in ['EIXO', 'A RECEPÇÃO', 'PRÁTICAS DE PRESERVAÇÃO',
                                            'EDUCAÇÃO PATRIMONIAL', 'A FORMAÇÃO']):
            continue
        # Título com subtítulo
        if ':' in text and len(text) > 15 and len(text) < 300:
            parts = text.split(':', 1)
            titulo = parts[0].strip()
            subtitulo = parts[1].strip()
            break
        elif len(text) > 15 and len(text) < 300:
            titulo = text
            break

    # Autores (entre título e resumo)
    autores_raw = []
    if resumo_idx:
        for i in range(2, resumo_idx):
            text = paragraphs[i]['text']
            if '@' not in text and 'CEP' not in text.upper() and len(text) < 80:
                if text != titulo and (subtitulo is None or text != subtitulo):
                    if not any(x in text.upper() for x in ['EIXO', 'RESUMO', 'ABSTRACT']):
                        autores_raw.append(text)

    # Resumo
    resumo = []
    palavras_chave = []
    if resumo_idx:
        end = abstract_idx if abstract_idx else (refs_idx if refs_idx else len(paragraphs))
        for i in range(resumo_idx + 1, min(end, resumo_idx + 10)):
            text = paragraphs[i]['text']
            if text.upper().startswith('PALAVRAS-CHAVE:') or text.upper().startswith('PALAVRAS CHAVE:'):
                kw = text.split(':', 1)[1].strip()
                palavras_chave = [k.strip().rstrip('.') for k in kw.split(';') if k.strip()]
            elif text.upper() not in ['ABSTRACT', 'RESUMEN']:
                resumo.append(text)

    # Abstract/Resumen
    abstract = []
    keywords = []
    text_start_idx = None

    if abstract_idx:
        for i in range(abstract_idx + 1, min(refs_idx if refs_idx else len(paragraphs), abstract_idx + 10)):
            text = paragraphs[i]['text']
            if text.upper().startswith('KEYWORDS:') or text.upper().startswith('PALABRAS'):
                kw = text.split(':', 1)[1].strip() if ':' in text else text
                keywords = [k.strip().rstrip('.') for k in kw.split(';') if k.strip()]
                text_start_idx = i + 1
                break
            else:
                abstract.append(text)

    # Texto principal
    texto = []
    figuras = []

    if text_start_idx:
        text_end = refs_idx if refs_idx else len(paragraphs)
        for i in range(text_start_idx, text_end):
            text = paragraphs[i]['text']
            # Caso referências concatenadas
            if 'Referências Bibliográficas' in text or 'REFERÊNCIAS BIBLIOGRÁFICAS' in text:
                parts = re.split(r'Referências Bibliográficas|REFERÊNCIAS BIBLIOGRÁFICAS', text)
                if parts[0].strip():
                    texto.append(parts[0].strip())
                break
            elif text.startswith('Fig.') or text.startswith('Figura'):
                figuras.append({'legenda': text, 'numero': len(figuras) + 1})
            else:
                texto.append(text)

    # Referências
    referencias = []
    if refs_idx:
        for i in range(refs_idx + 1, len(paragraphs)):
            text = paragraphs[i]['text']
            if text.upper().strip() not in ['REFERÊNCIAS', 'REFERÊNCIAS BIBLIOGRÁFICAS', 'BIBLIOGRAFIA']:
                referencias.append(text)

    # Imagens do docx
    imagens = []
    try:
        for rel_id, rel in doc.part.rels.items():
            if "image" in rel.target_ref:
                imagens.append({'path': rel.target_ref})
    except:
        pass

    # Figuras completas
    figuras_completas = []
    for i, fig in enumerate(figuras):
        fig_data = {'numero': fig['numero'], 'legenda': fig['legenda']}
        if i < len(imagens):
            fig_data['arquivo'] = imagens[i]['path']
        figuras_completas.append(fig_data)

    # PDF correspondente
    pdf_original = find_pdf_for_docx(docx_path, eixo_num)

    return {
        'id': article_id,
        'seminario': 'sdbr12',
        'secao': EIXOS[eixo_num],
        'titulo': titulo if titulo else Path(docx_path).stem,
        'subtitulo': subtitulo,
        'locale': 'pt-BR',
        'autores_raw': autores_raw if autores_raw else None,
        'resumo': '\n'.join(resumo) if resumo else None,
        'palavras_chave': palavras_chave if palavras_chave else None,
        'resumo_en': '\n'.join(abstract) if abstract else None,
        'palavras_chave_en': keywords if keywords else None,
        'texto': '\n\n'.join(texto) if texto else None,
        'figuras': figuras_completas if figuras_completas else None,
        'referencias': referencias if referencias else None,
        'arquivo_fonte': Path(docx_path).name,
        'arquivo_pdf_original': pdf_original,
        'arquivo_pdf': f"{article_id}.pdf",
        'status': 'pendente_revisao'
    }


def main():
    # Coletar todos os Word por eixo
    word_files = []

    # Eixo 1
    eixo1_dir = BASE / "EIXO 1 - Versão Word" / "Eixo 1 Word"
    if eixo1_dir.exists():
        for f in sorted(eixo1_dir.glob("*.docx")):
            word_files.append((f, 1))

    # Eixo 2
    eixo2_dir = BASE / "EIXO 2 - Versão Word" / "WORD"
    if eixo2_dir.exists():
        for f in sorted(eixo2_dir.glob("*.docx")):
            # Evitar duplicatas
            if "(1)" not in f.name:
                word_files.append((f, 2))

    # Eixo 3
    eixo3_dir = BASE / "EIXO 3 - Versão Word" / "WORD"
    if eixo3_dir.exists():
        for f in sorted(eixo3_dir.glob("*.docx")):
            word_files.append((f, 3))

    # Eixo 4
    eixo4_dir = BASE / "EIXO 4 - Versão Word" / "WORD"
    if eixo4_dir.exists():
        for f in sorted(eixo4_dir.glob("*.docx")):
            word_files.append((f, 4))

    print(f"Total de arquivos Word: {len(word_files)}")
    print(f"Diretório de saída: {OUT}")
    print("=" * 60)

    # Processar cada arquivo
    success = 0
    errors = 0

    for idx, (docx_path, eixo_num) in enumerate(word_files, 1):
        article_id = f"sdbr12-{idx:03d}"
        print(f"[{idx:03d}] {docx_path.name[:50]}...")

        data = extract_article(str(docx_path), article_id, eixo_num)

        if data:
            outfile = OUT / f"{article_id}.yaml"
            with open(outfile, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                         sort_keys=False, width=100)

            # Stats
            texto_len = len(data['texto'].split('\n\n')) if data['texto'] else 0
            refs = len(data['referencias']) if data['referencias'] else 0
            figs = len(data['figuras']) if data['figuras'] else 0
            pdf = "✓" if data['arquivo_pdf_original'] else "✗"
            print(f"       → {texto_len} parágrafos, {figs} figuras, {refs} refs, PDF:{pdf}")
            success += 1
        else:
            print(f"       → ERRO na extração")
            errors += 1

    print("=" * 60)
    print(f"Processados: {success} | Erros: {errors}")
    print(f"YAMLs salvos em: {OUT}")


if __name__ == "__main__":
    main()
