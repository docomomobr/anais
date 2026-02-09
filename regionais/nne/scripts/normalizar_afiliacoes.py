#!/usr/bin/env python3
"""
Normaliza afiliações dos autores nos YAMLs dos seminários regionais N/NE.

Regra: campo affiliation deve conter apenas sigla(s) da instituição.
Ex: "Departamento de Arquitetura e Urbanismo, Faculdade de Arquitetura" → "FAET-UFMT"
"""

import yaml
import re
from pathlib import Path

BASE = Path("/home/danilomacedo/Dropbox/docomomo/26-27/anais/regionais/nne")

# Mapeamento de afiliações para sigla normalizada.
# Chave: afiliação original (lowercase, stripped). Valor: sigla.
MAPA_AFILIACOES = {
    # === UFMT ===
    'departamento de arquitetura e urbanismo, faculdade de arquitetura': 'FAET-UFMT',
    'faculdade de artes visuais': 'FAET-UFMT',

    # === UFAM ===
    # (sem variações específicas encontradas)

    # === UFRR ===
    'bacharelado em arquitetura e urbanismo, laboratório de práticas de projeto e pesquisa do curso de arquitetura e urbanismo da ufrr': 'CAU-UFRR',
    'curso de arquitetura e urbanismo, ufrr': 'CAU-UFRR',
    'departamento de arquitetura e urbanismo, ufrr': 'DAU-UFRR',
    'departamento de administração, ufrr': 'UFRR',
    'instituto de geociências da ufrr': 'IGEO-UFRR',

    # === UFCG ===
    'departamento de arquitetura e urbanismo da universidade federal de campina grande (ufcg)': 'DAU-UFCG',
    'universidade federal de campina grande (ufcg)': 'UFCG',
    'universidade federal de campina grande': 'UFCG',
    'universidade federal de campina grande - ufcg': 'UFCG',
    'universidade federal de campina grande (ufcg). membro do grupo de pesquisa e extensão estúdia |estudos integrados em arquitetura|': 'UFCG',
    'uaec/ctrn, ufcg': 'UAEC-UFCG',
    'ufcg - uaec': 'UAEC-UFCG',
    'ufcg. ctrn': 'CTRN-UFCG',
    'ufcg': 'UFCG',
    'etsab/upc. professora adjunta do curso de arquitetura e urbanismo, ufcg': 'UFCG',

    # === UFPE ===
    'departamento de arquitetura e urbanismo, ufpe': 'DAU-UFPE',
    'dau/ ufpe': 'DAU-UFPE',
    'ppg-mdu ufpe': 'MDU-UFPE',
    'ppg-mdu ufpe. dep. de arquitetura da universidade católica de pernambuco': 'MDU-UFPE',

    # === UFC ===
    'departamento de arquitetura e urbanismo - ufc': 'DAU-UFC',
    'departamento de arquitetura e urbanismo ufc': 'DAU-UFC',
    'departamento de arquitetura e urbanismo da ufc': 'DAU-UFC',
    'departamento de arquitetura e urbanismo – ufc': 'DAU-UFC',
    'ufc': 'UFC',
    'universidade federal do ceará - ufc': 'UFC',
    'bolsista de extensão, daud-ufc': 'DAUD-UFC',
    'centro universitário sete de setembro – uni7': 'UNI7',

    # === UFBA ===
    'faculdade de arquitetura ufba': 'FAUFBA',
    'faculdade de arquitetura e urbanismo, ufba': 'FAUFBA',
    'ppgau/ufba': 'PPGAU-UFBA',
    'bolsista fapesb, universidade federal da bahia (salvador, ba)': 'UFBA',

    # === UFPA ===
    'fau-ufpa': 'FAU-UFPA',
    'faculdade de arquitetura e urbanismo, ufpa': 'FAU-UFPA',
    'ppgau-itec/ufpa. universidade federal do pará. faculdade de arquitetura e urbanismo': 'PPGAU-UFPA',
    'fau/ ppgau-itec/ufpa. universidade federal do pará. faculdade de arquitetura e urbanismo': 'PPGAU-UFPA',
    'programa de pós-graduação em arquitetura e urbanismo, ufpa': 'PPGAU-UFPA',

    # === UFRJ ===
    'prourb - ufrj': 'PROURB-UFRJ',
    'instituto alberto luiz coimbra de pós-graduação e pesquisa em engenharia – coppe/ufrj': 'COPPE-UFRJ',

    # === UFRGS ===
    'história e crítica da arquitetura pela universidade federal do rio grande do sul, propar - ufrgs': 'PROPAR-UFRGS',
    'departamento de arquitetura da ufrgs': 'DA-UFRGS',
    'universidade federal do rio grande do sul': 'UFRGS',
    'professora adjunta ufrgs': 'UFRGS',

    # === UFRN ===
    'universidade federal do rio grande do norte - ufrn': 'UFRN',

    # === USP ===
    'eesc-usp': 'EESC-USP',
    'faculdade de arquitetura e urbanismo universidade de são paulo': 'FAUUSP',

    # === Mackenzie ===
    'fau mackenzie': 'FAU-Mackenzie',
    'faculdade de arquitetura e urbanismo universidade presbiteriana mackenzie – upm': 'FAU-Mackenzie',
    'universidade presbiteriana mackenzie - upm': 'Mackenzie',
    'universidade presbiteriana mackenzie': 'Mackenzie',

    # === UnB ===
    'departamento de arquitetura e urbanismo - ufr, instituto de relações internacionais - irel na universidade de brasília': 'FAU-UnB',
    'departamento de arquitetura e urbanismo - ufrr, instituto de relações internacionais - irel na universidade de brasília': 'FAU-UnB',
    'faculdade de arquitetura e urbanismo da universidade de brasília (ppg-fau unb)': 'PPG-FAU-UnB',
    'universidade de brasília': 'UnB',
    'programa de pós-graduação da faculdade de arquitetura e urbanismo - ppg fau-unb, universidade de brasília. mestrando no programa de pós-graduação da faculdade de arquitetura e urbanismo - ppg fau-unb': 'PPG-FAU-UnB',
    'programa de pós-graduação da faculdade de arquitetura e urbanismo - ppg fau-unb. .b, universidade de brasília. professora e pesquisadora do programa de pós-graduação da faculdade de arquitetura e urbanismo - ppg fau-unb. .b': 'PPG-FAU-UnB',

    # === UFAL ===
    'fau/ ufal ppgau/deha/fau/ufal': 'FAU-UFAL',

    # === UFPI ===
    'universidade federal do piauí': 'UFPI',

    # === UFT ===
    'uft': 'UFT',
    'universidade federal do tocantins (cau-uft)': 'CAU-UFT',

    # === UNAMA ===
    'ccet - centro de ciências exatas e tecnologia, universidade da amazônia - unama': 'CCET-UNAMA',

    # === UEA ===
    'engenharia civil, universidade do estado do amazonas - uea': 'UEA',

    # === UNICAP ===
    'cct unicap. dep. de arquitetura da universidade católica de pernambuco': 'UNICAP',
    'universidade católica de pernambuco': 'UNICAP',

    # === UEMA ===
    'fau - uema': 'FAU-UEMA',
    'universidade estadual do maranhão, fau - uema': 'FAU-UEMA',
    'universidade estadual do maranhão. uema': 'UEMA',
    'universidade estadual do maranhão': 'UEMA',
    'uema': 'UEMA',
    'faculdade de arquitetura e urbanismo, universidade estadual do maranhão': 'FAU-UEMA',

    # === UNDB ===
    'unidade de ensino superior dom bosco (undb)': 'UNDB',
    'centro universitário undb': 'UNDB',
    'undb': 'UNDB',

    # === UNIFAP ===
    'curso de arquitetura e urbanismo, departamento de ciências exatas e tecnológicas, unifap': 'UNIFAP',
    'unifap': 'UNIFAP',

    # === UNIPÊ ===
    'centro universitário de joão pessoa - unipê': 'UNIPÊ',

    # === UNIFAVIP ===
    'departamento de arquitetura e urbanismo – unifavip| wyden': 'UNIFAVIP',

    # === Estácio ===
    'centro universitário estácio do ceará': 'Estácio-CE',

    # === IPHAN ===
    'mestrado profissional do instituto do patrimônio histórico e artístico nacional - mp/iphan': 'MP-IPHAN',

    # === Outros ===
    'centro de cultura': 'Centro de Cultura',
    'rede arquitetos': 'Rede Arquitetos',
    'faculdade de arquitetura e urbanismo': 'FAU',

    # === Estrangeiras ===
    'universitat politècnica de catalunya (upc)': 'UPC',

    # === UFG ===
    'universidade federal de goiás': 'UFG',
    'programa de pós-graduação em história da ufg': 'PPG-História-UFG',

    # === UFPB ===
    'daud-ufpb': 'DAUD-UFPB',
    'ppgau-ufpb': 'PPGAU-UFPB',

    # === Universidade de Lisboa ===
    'fa-u lisboa': 'FA-ULisboa',
    'universidade de lisboa': 'ULisboa',
    'universidade de lisboa - fa-ulisboa': 'FA-ULisboa',

    # === UFMT (sdnne09) ===
    'universidade federal de mato grosso': 'UFMT',

    # === Senado ===
    'senado federal': 'Senado Federal',

    # === Outros (sdnne09) ===
    'centro educacional dom alberto': 'Dom Alberto',
    'conservadora-restauradora, pós-graduada em ciência e engenharia de materiais, unileya': 'UNILEYA',
    'conservadora-restauradora, pós-graduanda em patrimônio arquitetônico e urbano, unileya': 'UNILEYA',

    # === Departamento genérico (Facisa) ===
    'departamento de arquitetura e urbanismo da faculdade de ciências sociais aplicadas (facisa)': 'Facisa',
}


class OrderedDumper(yaml.SafeDumper):
    pass


def dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


OrderedDumper.add_representer(dict, dict_representer)


def salvar_yaml(caminho, dados):
    with open(caminho, 'w', encoding='utf-8') as f:
        yaml.dump(dados, f, Dumper=OrderedDumper, default_flow_style=False,
                  allow_unicode=True, width=10000, sort_keys=False)


def normalizar_afiliacao(aff):
    """Normaliza uma afiliação usando o mapa."""
    if not aff:
        return aff

    # Lookup exato (case-insensitive)
    chave = aff.strip().lower()
    if chave in MAPA_AFILIACOES:
        return MAPA_AFILIACOES[chave]

    # Se já é sigla curta (< 20 chars sem espaço ou com hífen), manter
    if len(aff) < 20 and not any(p in aff.lower() for p in ['universidade', 'faculdade', 'departamento', 'programa', 'instituto']):
        return aff

    return aff  # Retorna inalterado se não encontrou match


def processar_seminario(slug):
    yaml_file = BASE / f"{slug}.yaml"

    with open(yaml_file, 'r', encoding='utf-8') as f:
        dados = yaml.safe_load(f)

    alterados = 0
    nao_mapeados = {}

    for artigo in dados['articles']:
        for autor in artigo.get('authors', []):
            aff_orig = autor.get('affiliation')
            if not aff_orig:
                continue

            aff_novo = normalizar_afiliacao(aff_orig)
            if aff_novo != aff_orig:
                autor['affiliation'] = aff_novo
                alterados += 1
            else:
                # Não encontrou no mapa
                chave = aff_orig.strip().lower()
                if len(aff_orig) >= 20 or any(p in chave for p in ['universidade', 'faculdade', 'departamento', 'programa', 'instituto']):
                    nao_mapeados[aff_orig] = nao_mapeados.get(aff_orig, 0) + 1

    salvar_yaml(yaml_file, dados)

    print(f"\n{slug}: {alterados} afiliações normalizadas")
    if nao_mapeados:
        print(f"  Não mapeadas ({len(nao_mapeados)} variações):")
        for aff, count in sorted(nao_mapeados.items()):
            print(f"    [{count}x] {aff}")


def main():
    processar_seminario("sdnne07")
    processar_seminario("sdnne09")
    print("\nConcluído!")


if __name__ == "__main__":
    main()
