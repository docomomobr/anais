#!/usr/bin/env python3
"""
Estrutura o campo autores_raw usando Claude API.

Transforma dados brutos em formato OJS estruturado.
"""

import yaml
import json
import time
import anthropic
from pathlib import Path

YAML_DIR = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/nacionais/sdbr12_fontes/yaml")

ORDEM_CAMPOS = [
    'id', 'seminario', 'secao', 'titulo', 'subtitulo', 'locale',
    'autores_raw', 'autores', 'resumo', 'palavras_chave', 'resumo_en', 'palavras_chave_en',
    'texto', 'figuras', 'referencias',
    'arquivo_fonte', 'arquivo_pdf_original', 'arquivo_pdf', 'status'
]

PROMPT_TEMPLATE = """Extraia os autores desta lista bruta de um artigo acadêmico brasileiro.

DADOS BRUTOS:
{autores_raw}

INSTRUÇÕES:
1. Identifique apenas os NOMES DE PESSOAS (ignore endereços, telefones, emails, afiliações, títulos acadêmicos, placeholders)
2. Separe nome (givenname) e sobrenome (familyname) no padrão brasileiro:
   - givenname: primeiro nome (e nomes do meio, se houver)
   - familyname: último sobrenome
   - Exemplo: "Maria Beatriz Camargo Cappello" → givenname: "Maria Beatriz Camargo", familyname: "Cappello"
3. Se identificar afiliação associada a um autor, inclua no campo affiliation (apenas nome da instituição, sem endereço)
4. Se houver email, inclua no campo email
5. O primeiro autor é primary_contact: true

RETORNE APENAS JSON válido, sem explicações:
[
  {{"givenname": "...", "familyname": "...", "affiliation": "...", "email": "...", "primary_contact": true}},
  {{"givenname": "...", "familyname": "...", "affiliation": "...", "email": "...", "primary_contact": false}}
]

Se não houver autores identificáveis, retorne: []
"""


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


def processar_autores_com_llm(client, autores_raw):
    """Envia autores_raw para Claude e retorna estruturado."""
    if not autores_raw:
        return []

    prompt = PROMPT_TEMPLATE.format(autores_raw=autores_raw)

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = response.content[0].text.strip()

    # Tenta parsear JSON
    try:
        # Remove possíveis marcadores de código
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
        texto = texto.strip()

        autores = json.loads(texto)

        # Limpa campos vazios
        for autor in autores:
            for campo in list(autor.keys()):
                if not autor[campo] or autor[campo] in ["...", "", None]:
                    del autor[campo]

        return autores
    except json.JSONDecodeError as e:
        print(f"    ERRO JSON: {e}")
        print(f"    Resposta: {texto[:200]}")
        return None


def main():
    client = anthropic.Anthropic()

    print("Estruturando autores com Claude API...\n")

    processados = 0
    erros = []

    yaml_files = sorted(YAML_DIR.glob("sdbr12-*.yaml"))
    total = len(yaml_files)

    for i, yaml_file in enumerate(yaml_files, 1):
        with open(yaml_file, 'r', encoding='utf-8') as f:
            dados = yaml.safe_load(f)

        autores_raw = dados.get('autores_raw')

        # Pula se já tem autores estruturados ou não tem raw
        if dados.get('autores') or not autores_raw:
            print(f"[{i}/{total}] {yaml_file.name}: pulado (já processado ou sem autores)")
            continue

        print(f"[{i}/{total}] {yaml_file.name}...")
        print(f"    raw: {autores_raw}")

        autores = processar_autores_com_llm(client, autores_raw)

        if autores is not None:
            dados['autores'] = autores if autores else None
            salvar_yaml_ordenado(yaml_file, dados)
            processados += 1
            print(f"    → {autores}")
        else:
            erros.append(yaml_file.name)

        # Rate limiting
        time.sleep(0.5)

    print(f"\n{'=' * 60}")
    print(f"Total processados: {processados}")

    if erros:
        print(f"\nErros ({len(erros)}):")
        for e in erros:
            print(f"  - {e}")


if __name__ == "__main__":
    main()
