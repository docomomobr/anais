#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrai autores dos PDFs do sdnne07 com parser melhorado
Formatos encontrados:
1. AUTOR1; AUTOR2; AUTOR3 (separados por ponto-vírgula, em maiúsculas)
2. AUTOR (1); AUTOR (2) (com números em parênteses)
3. Cada autor em linha separada seguida de sua afiliação
"""

import os
import re
import subprocess
import yaml
from pathlib import Path

def extrair_texto_pdf(pdf_path, max_chars=8000):
    """Extrai texto do PDF usando pdftotext"""
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', str(pdf_path), '-'],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout[:max_chars]
    except Exception as e:
        print(f"  Erro: {e}")
        return ""

def normalizar_nome(nome):
    """Converte nome de MAIÚSCULAS para Title Case"""
    if not nome:
        return nome
    # Remove espaços extras
    nome = re.sub(r'\s+', ' ', nome).strip()
    # Converte para title case
    nome = nome.title()
    # Corrige preposições comuns em nomes brasileiros
    nome = re.sub(r'\b(Da|De|Do|Das|Dos|E)\b', lambda m: m.group(1).lower(), nome)
    return nome

def extrair_autores(texto):
    """Extrai autores de diferentes formatos do sdnne07"""
    autores = []
    linhas = texto.split('\n')

    # Primeiro, busca linhas com nomes de autores (em maiúsculas)
    # Tenta identificar o formato usado

    # Coleta linhas relevantes (antes do RESUMO)
    linhas_cabecalho_raw = []
    for i, linha in enumerate(linhas[:80]):
        linha_strip = linha.strip()
        if re.match(r'^RESUMO\b', linha_strip, re.IGNORECASE):
            break
        linhas_cabecalho_raw.append((i, linha_strip))

    # Junta linhas que contêm autores quebrados
    # Detecta linhas que terminam com nome incompleto (sem fechar parênteses)
    linhas_cabecalho = []
    i = 0
    while i < len(linhas_cabecalho_raw):
        idx, linha = linhas_cabecalho_raw[i]
        deve_juntar = False

        # Caso 1: Linha com autores numerados (ex: NOME (1); NOME (2))
        if re.search(r'\(\d+\)', linha):
            abertos = linha.count('(')
            fechados = linha.count(')')

            if abertos > fechados:
                deve_juntar = True
            elif re.search(r'\b(DE|DA|DO|E|DOS|DAS|Y)\s*$', linha, re.IGNORECASE):
                deve_juntar = True
            elif re.search(r'[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]{2,}\s*$', linha):
                if i + 1 < len(linhas_cabecalho_raw):
                    prox_linha = linhas_cabecalho_raw[i + 1][1]
                    # Próxima linha tem mais autores numerados ou é continuação
                    if re.search(r'\(\d+\)', prox_linha) or re.match(r'^\s*[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]', prox_linha):
                        deve_juntar = True

        # Caso 2: Linha com autores separados por ; sem números (ex: NOME1; NOME2;)
        # Termina com ; ou com preposição, próxima linha é maiúsculas
        elif ';' in linha and re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]', linha.strip()):
            if linha.rstrip().endswith(';') or re.search(r'\b(DE|DA|DO|E|DOS|DAS)\s*$', linha, re.IGNORECASE):
                if i + 1 < len(linhas_cabecalho_raw):
                    prox_linha = linhas_cabecalho_raw[i + 1][1]
                    # Próxima linha começa com maiúsculas e não é número de afiliação
                    if re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]', prox_linha) and not re.match(r'^\d+\.', prox_linha):
                        deve_juntar = True

        if deve_juntar and i + 1 < len(linhas_cabecalho_raw):
            prox_idx, prox_linha = linhas_cabecalho_raw[i + 1]
            linha = linha + ' ' + prox_linha
            i += 1

        linhas_cabecalho.append((idx, linha))
        i += 1

    # Busca padrões de autores
    autores_encontrados = []

    # Padrão 1: Linha com múltiplos autores separados por ponto-vírgula
    # Ex: "EVILLYN BIAZATTI DE ARAÚJO; RICARDO SILVEIRA CASTOR" ou "NOME (1); NOME (2)"
    for idx, linha in linhas_cabecalho:
        # Remove números em parênteses para detectar o padrão
        linha_limpa = re.sub(r'\s*\(\d+\)\s*', ' ', linha).strip()

        # Verifica se a linha tem autores separados por ponto-e-vírgula ou vírgula
        tem_autores_numerados = re.search(r'\(\d+\)', linha)

        # Três casos: com números (1), (2); sem números mas em maiúsculas com ;; ou formato SOBRENOME, Nome (n)
        eh_linha_autores = False
        if tem_autores_numerados and re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]', linha_limpa):
            eh_linha_autores = True
        elif ';' in linha and re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s;]+$', linha_limpa):
            # Linha toda em maiúsculas com ponto-e-vírgula (sem números)
            eh_linha_autores = True
        elif tem_autores_numerados and re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]+,\s*[A-Za-záéíóúàâêôãõç]', linha.strip()):
            # Formato SOBRENOME, Nome (n) - sobrenome em maiúsculas, vírgula, nome em minúsculas
            eh_linha_autores = True

        if eh_linha_autores:
            # Verifica se é uma linha de autores (maiúsculas, não é título)
            # Separa por ponto-e-vírgula ou por vírgula seguida de espaço e nome em maiúsculas
            if ';' in linha:
                partes = [p.strip() for p in linha.split(';') if p.strip()]
            else:
                # Separa por ), seguido de espaço e próximo nome
                partes = re.split(r'\)\s*,\s*(?=[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ])', linha)
                partes = [p.strip() + ')' if not p.strip().endswith(')') else p.strip() for p in partes]
                partes = [p for p in partes if p.strip()]

            # Palavras que indicam que é um título, não um autor
            palavras_titulo = [
                'ARQUITETURA', 'MODERNA', 'MODERNIST', 'ARCHITECTURE', 'MODERN',
                'RESIDENTIAL', 'RESIDENCIAL', 'BUILDING', 'HOUSE', 'CAMPUS',
                'PATRIMÔNIO', 'HERITAGE', 'URBANISMO', 'PROJETO', 'CITY',
                'HISTÓRIA', 'HISTORY', 'HISTÓRICO', 'ANALYSIS', 'ANÁLISE',
                'INTERVENÇÃO', 'INTERVENTION'
            ]

            # Verifica se é formato SOBRENOME, Nome (n) - aceita minúsculas
            formato_sobrenome_nome = all(
                re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\-]*,\s*[A-Za-záéíóúàâêôãõç]', p.strip())
                for p in partes
            )

            # Todas as partes devem ser maiúsculas ou ter números em parênteses
            # Inclui hífen para nomes compostos como VIEIRA-DE-ARAÚJO
            todas_maiusculas = formato_sobrenome_nome or all(
                re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s\.\(\)0-9\-]+$', p.replace(',', ''))
                for p in partes
            )

            # Verifica se alguma parte contém palavras de título
            tem_palavra_titulo = any(
                any(pt in p.upper() for pt in palavras_titulo)
                for p in partes
            )

            if todas_maiusculas and len(partes) >= 1 and not tem_palavra_titulo:
                for i, parte in enumerate(partes, 1):
                    # Remove número em parênteses se existir
                    num_match = re.search(r'\((\d+)\)', parte)
                    num = int(num_match.group(1)) if num_match else i
                    nome_completo = re.sub(r'\s*\(\d+\)\s*', '', parte).strip()

                    if nome_completo and len(nome_completo) > 3:
                        autores_encontrados.append({
                            'nome_completo': nome_completo,
                            'num': num,
                            'linha_idx': idx
                        })

                if autores_encontrados:
                    break

    # Se não encontrou com ponto-vírgula, tenta encontrar autores em linhas separadas
    if not autores_encontrados:
        for idx, linha in linhas_cabecalho:
            # Padrão: Nome em maiúsculas sozinho na linha (possivelmente com número)
            # Ex: "ALCILIA AFONSO DE ALBUQUERQUE E MELO" ou "MARIA ANTÔNIA PESSOA (1)"
            linha_limpa = linha.strip()

            # Remove número em parênteses
            num_match = re.search(r'\((\d+)\)', linha_limpa)
            nome_sem_num = re.sub(r'\s*\(\d+\)\s*', '', linha_limpa).strip()

            # Verifica se parece um nome (maiúsculas, não muito longo, sem palavras comuns)
            # Lista expandida de palavras que indicam que é um título, não um autor
            palavras_titulo = [
                # Português
                'RESUMO', 'ABSTRACT', 'ARQUITETURA', 'MODERNA', 'MODERNIST',
                'HOUSE', 'BUILDING', 'URBANISMO', 'PATRIMÔNIO', 'HERITAGE',
                'SEMINÁRIO', 'DOCOMOMO', 'KEYWORDS', 'PALAVRAS', 'PROJETO',
                'CAMPUS', 'PARQUE', 'CENTRO', 'HOTEL', 'CIDADE', 'URBANO',
                'HISTÓRICO', 'ANÁLISE', 'CONSTRUÇÃO', 'INTERVENÇÃO',
                # Espanhol (títulos traduzidos)
                'ARQUITECTURA', 'RESIDENCIAL', 'UTILIZACIÓN', 'LADRILHO',
                'LADRILLO', 'HIDRÁULICO', 'CONSTRUCCIÓN', 'PROYECTOS',
                'PLANIFICACIÓN', 'FÍSICO', 'DISCUSIÓN', 'INTERVENCIONES',
                'TRADICIÓN', 'NORDESTE', 'BRASILEÑO', 'POÉTICA',
                # Inglês (títulos traduzidos)
                'ARCHITECTURE', 'RESIDENTIAL', 'HYDRAULIC', 'TILE', 'MODERN',
                'PHYSICAL', 'PLANNING', 'HISTORY', 'DISCUSSION', 'INTERVENTION',
                'TRADITION', 'NORTHEAST', 'BRAZILIAN', 'POETICS', 'MATERIALIZED',
                'PROJECTION', 'PIONEER', 'IMPACTS', 'STADIUMS', 'FOOTBALL',
                'MULTIFUNCTIONAL', 'CONTEXT', 'ANALYSIS'
            ]

            # Detecta se começa com artigos/preposições de espanhol/inglês
            comeca_com_artigo = re.match(r'^(EL|LA|LOS|LAS|THE|IN|OF|UN|UNA|EN|DEL|DE LA|DOS|DAS)\s+', nome_sem_num, re.IGNORECASE)

            if (re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]+$', nome_sem_num) and
                len(nome_sem_num) > 5 and len(nome_sem_num) < 80 and
                not comeca_com_artigo and
                not any(x in nome_sem_num.upper() for x in palavras_titulo)):

                num = int(num_match.group(1)) if num_match else len(autores_encontrados) + 1
                autores_encontrados.append({
                    'nome_completo': nome_sem_num,
                    'num': num,
                    'linha_idx': idx
                })

    # Para cada autor encontrado, busca afiliação e email
    for autor_info in autores_encontrados:
        nome_completo = autor_info['nome_completo']
        num = autor_info['num']
        linha_idx = autor_info['linha_idx']

        # Separa nome e sobrenome
        # Detecta formato "SOBRENOME, Nome" (vírgula após sobrenome)
        if ',' in nome_completo and re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]+,', nome_completo):
            partes_virgula = nome_completo.split(',', 1)
            sobrenome = normalizar_nome(partes_virgula[0].strip())
            nome = normalizar_nome(partes_virgula[1].strip()) if len(partes_virgula) > 1 else ''
        else:
            partes = nome_completo.split()
            if len(partes) >= 2:
                nome = normalizar_nome(partes[0])
                sobrenome = normalizar_nome(' '.join(partes[1:]))
            else:
                nome = normalizar_nome(nome_completo)
                sobrenome = ''

        autor = {
            'nome': nome,
            'sobrenome': sobrenome,
            'afiliacao': None,
            'email': None,
            'principal': num == 1
        }

        # Busca afiliação e email nas linhas seguintes
        texto_afiliacao = []
        email_encontrado = None

        # Busca pela afiliação numerada (ex: "1. Doutorado em...")
        for i in range(linha_idx + 1, min(len(linhas), linha_idx + 20)):
            linha = linhas[i].strip()

            # Para no RESUMO
            if re.match(r'^RESUMO\b', linha, re.IGNORECASE):
                break

            # Busca linha que começa com o número do autor
            if re.match(rf'^{num}\.\s+', linha):
                afil_texto = re.sub(rf'^{num}\.\s+', '', linha).strip()
                texto_afiliacao.append(afil_texto)

                # Continua coletando linhas de afiliação até encontrar email ou próximo autor
                for j in range(i + 1, min(len(linhas), i + 6)):
                    prox_linha = linhas[j].strip()

                    # Para em linha vazia, próximo número ou RESUMO
                    if not prox_linha or re.match(r'^\d+\.\s+', prox_linha):
                        break
                    if re.match(r'^RESUMO\b', prox_linha, re.IGNORECASE):
                        break
                    # Para se encontrar outro autor em maiúsculas
                    if re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]+$', prox_linha):
                        break

                    texto_afiliacao.append(prox_linha)

                break

            # Busca por "E-mail:" ou email direto
            email_match = re.search(r'E-?mail:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', linha, re.IGNORECASE)
            if not email_match:
                email_match = re.search(r'^([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$', linha)

            if email_match and not email_encontrado:
                # Verifica se este email corresponde a este autor (por posição)
                # Conta quantos emails já foram encontrados antes desta linha
                emails_antes = 0
                for k in range(linha_idx + 1, i):
                    if re.search(r'@', linhas[k]):
                        emails_antes += 1

                if emails_antes == num - 1:
                    email_encontrado = email_match.group(1).lower()

        # Processa texto de afiliação
        if texto_afiliacao:
            afil_full = ' '.join(texto_afiliacao)

            # Extrai email do texto de afiliação se ainda não encontrou
            if not email_encontrado:
                email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', afil_full)
                if email_match:
                    email_encontrado = email_match.group(1).lower()
                    afil_full = afil_full.replace(email_match.group(1), '').strip()

            # Remove URLs e limpa
            afil_full = re.sub(r'https?://\S+', '', afil_full)
            afil_full = re.sub(r'http://\S+', '', afil_full)
            afil_full = re.sub(r'E-?mail:\s*', '', afil_full, flags=re.IGNORECASE)
            afil_full = re.sub(r'\s+', ' ', afil_full).strip()
            afil_full = afil_full.rstrip(',').strip()

            if afil_full and len(afil_full) > 5:
                autor['afiliacao'] = afil_full

        if email_encontrado:
            autor['email'] = email_encontrado

        autores.append(autor)

    return autores

def processar_diretorio(pdf_dir):
    """Processa todos os PDFs e extrai autores"""
    pdf_dir = Path(pdf_dir)
    resultados = {}

    pdfs = sorted(pdf_dir.glob('*.pdf'))
    total = len(pdfs)

    for i, pdf in enumerate(pdfs, 1):
        print(f"[{i}/{total}] {pdf.name}")

        texto = extrair_texto_pdf(pdf)
        if texto:
            autores = extrair_autores(texto)
            if autores:
                resultados[pdf.name] = autores
                for a in autores:
                    email = a.get('email', 'sem email')
                    print(f"    - {a['nome']} {a['sobrenome']} <{email}>")
            else:
                print(f"    (nenhum autor encontrado)")

    return resultados

def atualizar_yaml(yaml_path, autores_extraidos, pdf_dir):
    """Atualiza o YAML com os autores extraídos"""
    print(f"\nAtualizando: {yaml_path}")

    with open(yaml_path, 'r', encoding='utf-8') as f:
        dados = yaml.safe_load(f)

    # Lista de PDFs na ordem
    pdf_dir = Path(pdf_dir)
    arquivos_pdf = sorted([f.name for f in pdf_dir.glob('*.pdf')])

    artigos = dados.get('artigos', [])
    atualizados = 0

    for i, artigo in enumerate(artigos):
        if i < len(arquivos_pdf):
            arquivo_pdf = arquivos_pdf[i]

            if arquivo_pdf in autores_extraidos:
                novos_autores = autores_extraidos[arquivo_pdf]
                if novos_autores:
                    artigo['autores'] = novos_autores
                    atualizados += 1

    dados['artigos'] = artigos

    # Salva
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(dados, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, width=200)

    print(f"Artigos atualizados: {atualizados}/{len(artigos)}")

def main():
    pdf_dir = "/home/danilomacedo/Dropbox/docomomo/26-27/site/migracao/nne/sdnne07/pdfs"
    yaml_path = "/home/danilomacedo/Dropbox/docomomo/26-27/site/migracao/nne/sdnne07.yaml"

    print("Extraindo autores dos PDFs do sdnne07...\n")
    autores = processar_diretorio(pdf_dir)

    print(f"\nTotal de PDFs com autores extraídos: {len(autores)}")

    atualizar_yaml(yaml_path, autores, pdf_dir)

if __name__ == '__main__':
    main()
