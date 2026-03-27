#!/usr/bin/env python3
"""
Extrai nomes próprios prováveis dos títulos/subtítulos de artigos.

Heurística: palavras capitalizadas que não são início de frase,
não são siglas conhecidas, e não estão no dicionário.
Gera candidatos para revisão antes de inserir no dict.db.

Uso:
    python3 dict/seed_titles.py                        # mostra candidatos
    python3 dict/seed_titles.py --apply                # insere no dict.db
    python3 dict/seed_titles.py --source outro.db      # usa outro banco
"""

import argparse
import os
import re
import sqlite3

DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DB = os.path.join(DIR, 'dict.db')
DEFAULT_SOURCE = os.path.join(os.path.dirname(DIR), 'anais.db')

# Palavras comuns que aparecem capitalizadas por erro mas não são nomes
STOPWORDS = {
    'a', 'à', 'ao', 'aos', 'as', 'até', 'com', 'como', 'contra', 'da', 'das',
    'de', 'del', 'do', 'dos', 'e', 'em', 'entre', 'era', 'foi', 'há', 'já',
    'mais', 'mas', 'na', 'nas', 'nem', 'no', 'nos', 'não', 'o', 'os', 'ou',
    'para', 'pela', 'pelas', 'pelo', 'pelos', 'por', 'que', 'se', 'sem',
    'seu', 'seus', 'sob', 'sobre', 'sua', 'suas', 'são', 'só', 'também',
    'toda', 'todas', 'todo', 'todos', 'um', 'uma', 'uns',
    # Palavras comuns em títulos acadêmicos que não são nomes próprios
    'análise', 'estudo', 'caso', 'projeto', 'projetos', 'proposta', 'reflexões',
    'edifício', 'edifícios', 'casa', 'casas', 'cidade', 'cidades',
    'patrimônio', 'memória', 'memórias', 'moderna', 'moderno', 'modernas', 'modernos',
    'arquitetura', 'urbanismo', 'preservação', 'documentação', 'restauro',
    'habitação', 'habitacional', 'conjunto', 'conjuntos', 'residencial', 'residenciais',
    'construção', 'espaço', 'espaços', 'lugar', 'lugares', 'paisagem', 'paisagens',
    'anos', 'século', 'séculos', 'processo', 'práticas',
    'história', 'registro', 'inventário', 'levantamento', 'mapeamento',
    'notas', 'considerações', 'contribuição', 'contribuições',
    'aproximações', 'perspectivas', 'olhares', 'diálogos',
    # Substantivos comuns que aparecem capitalizados em títulos mas não são nomes
    'arte', 'artes', 'centro', 'estado', 'estados', 'hotel', 'museu', 'museus',
    'plano', 'universidade', 'faculdade', 'instituto', 'escola', 'biblioteca',
    'teatro', 'cinema', 'igreja', 'catedral', 'capela', 'palácio', 'palácios',
    'parque', 'praça', 'rua', 'avenida', 'ponte', 'estação', 'terminal',
    'campus', 'sede', 'vila', 'bairro', 'região', 'zona',
    'programa', 'política', 'políticas', 'nacional', 'federal', 'estadual', 'municipal',
    'modernidade', 'modernização', 'industrialização', 'urbanização',
    'movimento', 'movimentos', 'período', 'fase', 'legado', 'herança',
    'identidade', 'cultura', 'cultural', 'social', 'público', 'pública',
    'internacional', 'mundial', 'brasileiro', 'brasileira', 'brasileiros',
    'novo', 'nova', 'novos', 'novas', 'velho', 'velha',
    'grande', 'pequeno', 'alto', 'baixo',
    'secretaria', 'ministério', 'conselho', 'departamento', 'diretoria',
    'prédio', 'prédios', 'bloco', 'blocos', 'torre', 'torres',
    'mercado', 'feira', 'hospital', 'clube', 'associação', 'fundação',
    'jardim', 'jardins', 'reserva', 'área', 'setor',
    'cap', 'eixo', 'mesa', 'sessão', 'grupo', 'temático', 'temática',
    'completo', 'completos', 'resumo', 'resumos', 'expandido', 'expandidos',
    'comunicação', 'comunicações', 'relato', 'relatos', 'experiência',
    # Adjetivos, substantivos comuns e palavras contextuais (não são nomes próprios)
    'abolição', 'ação', 'administrativo', 'aeroporto', 'arquitetônico',
    'arquivo', 'artístico', 'atlântico', 'auditório', 'barra',
    'belas', 'bienal', 'brutalista', 'caixa', 'calçadão',
    'cemitério', 'centenário', 'central', 'clínicas', 'colonial',
    'companhia', 'congresso', 'contemporânea', 'contemporâneo', 'correios',
    'críticos', 'design', 'diretor', 'distrito', 'educação',
    'embaixada', 'esplanada', 'extraordinário', 'ferroviária', 'forte',
    'fórum', 'fundo', 'gaúcha', 'gaúcho', 'gestão',
    'governo', 'governador', 'grand', 'historiografia', 'histórico',
    'house', 'indústria', 'industrial', 'infância', 'irmãos',
    'justiça', 'laboratório', 'latina', 'latino', 'legislativa',
    'marine', 'minha', 'misericórdia', 'missões', 'modernista',
    'módulo', 'operária', 'operário', 'oeste', 'palace',
    'patrimonial', 'pavilhão', 'pensões', 'planalto', 'plásticas',
    'popular', 'praia', 'prefeito', 'prefeitura', 'presidente',
    'refeitório', 'regional', 'república', 'residência', 'revista',
    'sanatório', 'saúde', 'seminário', 'senhora', 'triângulo',
    'tribunal', 'universitária', 'universitário', 'urbana', 'urbano',
    'vidro', 'builds', 'concrete', 'déco', 'art',
    'base', 'campo', 'vista', 'piloto', 'passo',
    'navio', 'fora', 'palha', 'cristo',
    # Genéricos encontrados erroneamente no dict (sdsul08, 2026-03-23)
    'águas', 'técnica', 'técnicas', 'panorama', 'obras', 'obra',
    'serviço', 'criação', 'ensaio', 'encontro', 'sertão',
    'arquitetônica', 'arquitetônicas', 'arquitetônico', 'arquitetônicos',
    'infraestrutura', 'infraestruturas', 'superestrutura',
    'mobilidade', 'resiliência', 'sustentabilidade',
    'enchente', 'enchentes', 'inundação', 'inundações',
    'proteção', 'defesa', 'sistema', 'sistemas',
    'produção', 'dispositivo', 'dispositivos', 'controle',
    'ambiental', 'climática', 'climático',
    'subordinação', 'subversão', 'aproveitamento',
    'heroicos', 'pragmáticos', 'pertinência', 'regeneração',
    'estruturar', 'desconstruindo',
    # Genéricos encontrados erroneamente no dict (sdnne02, 2026-03-24)
    'arquiteto', 'arquitetos', 'materiais', 'tombamento', 'tradição',
    'anexo', 'judiciário',
    # Genéricos encontrados erroneamente no dict (sdnne03, 2026-03-24)
    'antiga', 'exposições', 'marítima', 'migrantes', 'severinos',
    # Genéricos encontrados erroneamente no dict (sdnne04, 2026-03-25)
    'circulação', 'tessituras', 'tectônicas', 'envelopado', 'mágica',
    'esperança', 'presente', 'desenho', 'conservação', 'apartamentos',
    'arenas', 'desportivas', 'iconográfico', 'escritório', 'professor',
    'referência', 'intervenção', 'escolar',
    # Genéricos encontrados erroneamente no dict (sdnne05, 2026-03-25)
    'homem', 'fábrica', 'adequação', 'ciudad', 'modernistas', 'madeira',
    # Genéricos encontrados erroneamente no dict (sdnne06, 2026-03-25)
    'complexo', 'desenvolvimento', 'edificado', 'elementos', 'longo',
    'monumento', 'monumentos', 'residências', 'tectônica', 'urbanos',
    'vernacular',
    # Genéricos encontrados erroneamente no dict (sdnne06, 2026-03-25)
    'antigo', 'interrompido', 'privado',
    # Genéricos encontrados erroneamente no dict (sdsp06, 2026-03-27)
    'ensino', 'teoria', 'sociedade', 'industriais', 'três',
    # Genéricos encontrados erroneamente no dict (sdsp07, 2026-03-27)
    'galeria', 'interiores', 'exposição',
    # Genéricos encontrados erroneamente no dict (sdsp08, 2026-03-27)
    'desenhos', 'pesquisas', 'ferroviário', 'bienais',
    'fontes', 'escolas', 'concurso',
}


_VALID_TABLES = {'articles', 'authors'}
_VALID_COLS = {'title', 'subtitle', 'title_en', 'subtitle_en', 'title_es', 'subtitle_es'}


def extract_candidates(source_db, table='articles',
                       title_col='title', subtitle_col='subtitle'):
    """Extrai candidatos a nomes próprios dos títulos."""
    if table not in _VALID_TABLES:
        raise ValueError(f"Invalid table: {table}")
    if title_col not in _VALID_COLS:
        raise ValueError(f"Invalid column: {title_col}")
    if subtitle_col not in _VALID_COLS:
        raise ValueError(f"Invalid column: {subtitle_col}")

    if not os.path.exists(DICT_DB):
        print(f'ERRO: {DICT_DB} não existe. Rode init_db.py primeiro.')
        return {}

    src = sqlite3.connect(source_db)
    try:
        rows = src.execute(f'SELECT {title_col}, {subtitle_col} FROM {table}').fetchall()
    finally:
        src.close()

    dict_conn = sqlite3.connect(DICT_DB)
    try:
        existing = set(
            r[0] for r in dict_conn.execute('SELECT word FROM dict_names').fetchall()
        )
    finally:
        dict_conn.close()

    # Contar ocorrências de cada candidato
    candidates = {}  # word_lower → {canonical, count, contexts}

    for title, subtitle in rows:
        for text in [title, subtitle]:
            if not text:
                continue
            words = text.split()
            for i, word in enumerate(words):
                # Limpar pontuação
                clean = re.sub(r'^[^\w]+|[^\w]+$', '', word, flags=re.UNICODE)
                if not clean or len(clean) < 3:
                    continue
                low = clean.lower()

                # Pular se já no dicionário
                if low in existing:
                    continue

                # Pular stopwords
                if low in STOPWORDS:
                    continue

                # Interessam apenas palavras com primeira maiúscula
                # (exceto a primeira palavra do título, que sempre é maiúscula)
                if i == 0:
                    continue
                if not clean[0].isupper():
                    continue
                # Pular se é toda maiúscula (possível sigla não catalogada)
                if clean.isupper():
                    continue
                # Pular compostos com UF (Grande-PB, Natal/RN, Santos/SP)
                if re.search(r'[-/][A-Z]{2}$', clean):
                    continue

                canonical = clean[0].upper() + clean[1:]
                if low not in candidates:
                    candidates[low] = {'canonical': canonical, 'count': 0, 'contexts': []}
                candidates[low]['count'] += 1
                if len(candidates[low]['contexts']) < 3:
                    ctx = text[:80]
                    if ctx not in candidates[low]['contexts']:
                        candidates[low]['contexts'].append(ctx)

    return candidates


def main():
    parser = argparse.ArgumentParser(
        description='Extrair nomes próprios de títulos para dict.db')
    parser.add_argument('--source', default=DEFAULT_SOURCE,
                        help=f'Banco fonte (default: {DEFAULT_SOURCE})')
    parser.add_argument('--min-count', type=int, default=1,
                        help='Mínimo de ocorrências para incluir (default: 1)')
    parser.add_argument('--apply', action='store_true',
                        help='Inserir candidatos no dict.db')
    args = parser.parse_args()

    candidates = extract_candidates(args.source)
    if not candidates:
        print('Nenhum candidato encontrado.')
        return

    # Filtrar por contagem mínima
    filtered = {k: v for k, v in candidates.items() if v['count'] >= args.min_count}
    sorted_cands = sorted(filtered.items(), key=lambda x: (-x[1]['count'], x[0]))

    print(f'Candidatos a nomes próprios: {len(sorted_cands)} (min {args.min_count} ocorrência(s))\n')

    for word, info in sorted_cands:
        print(f'  {info["canonical"]:30s} ({info["count"]}x)')
        for ctx in info['contexts']:
            print(f'    → {ctx}')

    if args.apply:
        dict_conn = sqlite3.connect(DICT_DB)
        try:
            added = 0
            for word, info in sorted_cands:
                dict_conn.execute(
                    'INSERT OR IGNORE INTO dict_names (word, category, canonical, source) '
                    'VALUES (?, ?, ?, ?)',
                    (word, 'nome', info['canonical'], 'titulos'))
                added += 1
            dict_conn.commit()
            print(f'\nAdicionados: {added}')
        finally:
            dict_conn.close()
    else:
        print(f'\nUse --apply para inserir no dict.db')


if __name__ == '__main__':
    main()
