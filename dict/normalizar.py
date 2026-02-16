#!/usr/bin/env python3
"""
Biblioteca de normalização FUNAG de maiúsculas/minúsculas.

Trata as tipologias de erro #3 (ambiguidade de entidades) e #4 (capitalização)
descritas em dict/documentacao/ner_fontes.md. Lê dicionário do dict.db.

Passadas:
  1a — palavra a palavra: siglas, nomes, lugares, áreas, movimentos
  2a — expressões consolidadas (regex multi-palavra)
  3a — toponímicos contextuais (capitalizados após movimento/área/expressão)

Regras FUNAG:
- Tudo minúscula, exceto:
  - Primeira letra do título: maiúscula
  - Primeira letra do subtítulo: minúscula
  - Siglas: MAIÚSCULAS (BNH, USP, IPHAN)
  - Nomes próprios: Capitalizado (Niemeyer, Brasília)
  - Áreas do saber: Capitalizado (Arquitetura, Urbanismo)
  - Movimentos/períodos: Capitalizado (Modernismo, Art Déco)
  - Expressões consolidadas: forma canônica (Patrimônio Moderno)
  - Lugares: Capitalizado (Fortaleza, Bahia)
  - Toponímicos após movimento/área: Capitalizado (Brutalismo Paulista)

Uso como módulo:
    from dict.normalizar import normalizar_texto
    titulo = normalizar_texto("ARQUITETURA MODERNA EM BRASÍLIA", eh_subtitulo=False)

Uso standalone:
    python3 dict/normalizar.py "ARQUITETURA MODERNA EM BRASÍLIA"
    python3 dict/normalizar.py --subtitulo "o caso de São Paulo"
"""

import os
import re
import sqlite3
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DIR, 'dict.db')

# ╔══════════════════════════════════════════════════════════════════════╗
# ║  ATENÇÃO: Todos os dados de dicionário (nomes, siglas, lugares,    ║
# ║  movimentos, toponímicos, expressões) residem no dict.db.          ║
# ║  NUNCA adicionar listas de palavras diretamente neste script.      ║
# ║  Para adicionar entradas: editar dict/init_db.py e rodar --reset.  ║
# ╚══════════════════════════════════════════════════════════════════════╝

# Cache em memória (carregado do dict.db)
_SIGLAS = set()
_NOMES = {}        # word_lower → canonical
_LUGARES = {}      # word_lower → canonical
_AREAS = {}        # word_lower → canonical
_MOVIMENTOS = {}   # word_lower → canonical
_TOPONIMICOS = {}  # word_lower → canonical
_EXPRESSOES = {}   # expr_lower → canonical
_loaded = False


def load_dict(db_path=None):
    """Carrega dicionário do banco para sets/dicts em memória."""
    global _SIGLAS, _NOMES, _LUGARES, _AREAS, _MOVIMENTOS, _TOPONIMICOS, _EXPRESSOES, _loaded
    if _loaded:
        return

    path = db_path or DB_PATH
    if not os.path.exists(path):
        print(f'AVISO: {path} não encontrado, dicionário vazio.', file=sys.stderr)
        _loaded = True
        return

    conn = sqlite3.connect(path)
    rows = conn.execute('SELECT word, category, canonical FROM dict_names').fetchall()
    conn.close()

    for word, cat, canonical in rows:
        if cat == 'sigla':
            _SIGLAS.add(word)
        elif cat == 'nome':
            _NOMES[word] = canonical
        elif cat == 'lugar':
            _LUGARES[word] = canonical
        elif cat == 'area':
            _AREAS[word] = canonical
        elif cat == 'movimento':
            _MOVIMENTOS[word] = canonical
        elif cat == 'toponimico':
            _TOPONIMICOS[word] = canonical
        elif cat == 'expressao':
            _EXPRESSOES[word] = canonical

    _loaded = True


def reload_dict(db_path=None):
    """Força recarga do dicionário."""
    global _SIGLAS, _NOMES, _LUGARES, _AREAS, _MOVIMENTOS, _TOPONIMICOS, _EXPRESSOES, _loaded
    _SIGLAS = set()
    _NOMES = {}
    _LUGARES = {}
    _AREAS = {}
    _MOVIMENTOS = {}
    _TOPONIMICOS = {}
    _EXPRESSOES = {}
    _loaded = False
    load_dict(db_path)


def stats():
    """Retorna estatísticas do dicionário carregado."""
    load_dict()
    return {
        'siglas': len(_SIGLAS),
        'nomes': len(_NOMES),
        'lugares': len(_LUGARES),
        'areas': len(_AREAS),
        'movimentos': len(_MOVIMENTOS),
        'toponimicos': len(_TOPONIMICOS),
        'expressoes': len(_EXPRESSOES),
        'total': len(_SIGLAS) + len(_NOMES) + len(_LUGARES) +
                 len(_AREAS) + len(_MOVIMENTOS) + len(_TOPONIMICOS) +
                 len(_EXPRESSOES),
    }


def _eh_capitalizavel(word_lower):
    """Verifica se uma palavra está em algum dicionário de capitalização."""
    return (word_lower in _SIGLAS or word_lower in _NOMES or
            word_lower in _LUGARES or word_lower in _AREAS or
            word_lower in _MOVIMENTOS)


def normalizar_palavra(palavra, posicao, inicio_frase):
    """Normaliza uma palavra individual."""
    load_dict()

    # d'Alva, d'água etc.
    if palavra.lower().startswith("d'") or palavra.lower().startswith("d´"):
        return palavra[0] + palavra[1] + palavra[2:].capitalize()

    # Preserva pontuação ao redor
    match = re.match(r'^([^\w]*)(\w+)([^\w]*)$', palavra, re.UNICODE)
    if not match:
        return palavra

    prefixo, nucleo, sufixo = match.groups()
    nucleo_lower = nucleo.lower()

    # Sigla: maiúscula
    if nucleo_lower in _SIGLAS:
        return prefixo + nucleo.upper() + sufixo

    # Nome próprio: capitalizar
    if nucleo_lower in _NOMES:
        return prefixo + _NOMES[nucleo_lower] + sufixo

    # Lugar: capitalizar
    if nucleo_lower in _LUGARES:
        return prefixo + _LUGARES[nucleo_lower] + sufixo

    # Área do saber: capitalizar
    if nucleo_lower in _AREAS:
        return prefixo + _AREAS[nucleo_lower] + sufixo

    # Movimento: capitalizar
    if nucleo_lower in _MOVIMENTOS:
        return prefixo + _MOVIMENTOS[nucleo_lower] + sufixo

    # Início de frase: capitalizar
    if inicio_frase and posicao == 0:
        return prefixo + nucleo.capitalize() + sufixo

    # Resto: minúscula
    return prefixo + nucleo_lower + sufixo


def normalizar_texto(texto, eh_subtitulo=False):
    """Normaliza um texto (título ou subtítulo) conforme FUNAG."""
    load_dict()

    if not texto:
        return texto

    # Remove ponto final se houver (mas preserva abreviações como "E.U.A.")
    if texto.endswith('.'):
        last_word = texto.split()[-1] if texto.split() else ''
        # Só remove se a última palavra não tem pontos internos (abreviação)
        if '.' not in last_word[:-1]:
            texto = texto[:-1]

    palavras = texto.split()
    resultado = []
    # Rastrear início de frase (após ponto final, ? ou !)
    inicio_nova_frase = False

    for i, palavra in enumerate(palavras):
        # Detectar se a palavra anterior terminou com pontuação de fim de frase
        if i > 0 and resultado:
            prev = resultado[-1]
            if prev.endswith('?') or prev.endswith('!'):
                inicio_nova_frase = True
            elif prev.endswith('.'):
                core = re.sub(r'[^\w]', '', prev)
                # Não é nova frase se:
                # - Último alfa antes do ponto é maiúsculo (sigla: "MG.", "UFPE.")
                # - Núcleo curto ≤3 chars (abreviação: "Jr.", "h.", "m.", "ee.", "Dr.")
                if not (prev[-2:-1].isupper() or len(core) <= 3):
                    inicio_nova_frase = True

        if '-' in palavra and not palavra.startswith('-'):
            # Tratar cada parte do hífen
            partes = palavra.split('-')
            partes_norm = []
            for j, parte in enumerate(partes):
                p_norm = normalizar_palavra(
                    parte, i if j == 0 else 1,
                    inicio_frase=(i == 0 and j == 0) and not eh_subtitulo)
                partes_norm.append(p_norm)
            resultado.append('-'.join(partes_norm))
        elif '/' in palavra and not palavra.startswith('http'):
            # Tratar cada parte da barra
            partes = palavra.split('/')
            partes_norm = []
            for j, parte in enumerate(partes):
                if parte:
                    p_norm = normalizar_palavra(
                        parte, i if j == 0 else 1,
                        inicio_frase=(i == 0 and j == 0) and not eh_subtitulo)
                    partes_norm.append(p_norm)
                else:
                    partes_norm.append(parte)
            resultado.append('/'.join(partes_norm))
        else:
            inicio_frase = ((i == 0) and not eh_subtitulo) or inicio_nova_frase
            palavra_norm = normalizar_palavra(palavra, i if not inicio_nova_frase else 0, inicio_frase)
            inicio_nova_frase = False

            # Subtítulo: forçar minúscula na 1a palavra (exceto sigla/nome/lugar/area/mov)
            if eh_subtitulo and i == 0:
                nucleo = re.sub(r'[^\w]', '', palavra.lower())
                if not _eh_capitalizavel(nucleo):
                    if palavra_norm and palavra_norm[0].isupper():
                        palavra_norm = palavra_norm[0].lower() + palavra_norm[1:]

            resultado.append(palavra_norm)

    texto_resultado = ' '.join(resultado)

    # Aplicar expressões consolidadas (segunda passada)
    # Usa \b para evitar match dentro de palavras (ex: "aeroporto" ≠ "Porto")
    for expr, repl in _EXPRESSOES.items():
        pattern = re.compile(r'\b' + re.escape(expr) + r'\b', re.IGNORECASE)
        texto_resultado = pattern.sub(repl, texto_resultado)

    # Capitalizar toponímicos após movimentos/áreas (terceira passada)
    # Regra FUNAG: adjetivos pátrios são capitalizados em expressões
    # consolidadas (ex: "Brutalismo Paulista", "Arquitetura Brasileira")
    texto_resultado = _capitalizar_toponimicos(texto_resultado)

    return texto_resultado


def _strip_punct(word):
    """Remove pontuação ao redor de uma palavra, retorna (prefixo, núcleo, sufixo)."""
    m = re.match(r'^([^\w]*)(.+?)([^\w]*)$', word, re.UNICODE)
    if not m:
        return '', word, ''
    return m.groups()


def _capitalizar_toponimicos(texto):
    """Capitaliza toponímicos quando precedidos por movimento, área ou expressão.

    Regras (um adjetivo pátrio é capitalizado se):
    1. Palavra anterior (lowered) está em _MOVIMENTOS ou _AREAS
       Ex: "Brutalismo paulista" → "Brutalismo Paulista"
    2. Palavra 2 posições atrás está em _MOVIMENTOS ou _AREAS,
       e a palavra anterior está capitalizada
       Ex: "Arquitetura Moderna brasileira" → "Arquitetura Moderna Brasileira"
    3. As 2 palavras anteriores formam uma expressão consolidada
       Ex: "Educação Patrimonial brasileira" → "Educação Patrimonial Brasileira"
    """
    words = texto.split()
    if len(words) < 2:
        return texto

    for i in range(1, len(words)):
        _, nucleo, _ = _strip_punct(words[i])
        nucleo_lower = nucleo.lower()

        if nucleo_lower not in _TOPONIMICOS:
            continue

        # Verificar contexto: palavra anterior
        _, prev_nucleo, _ = _strip_punct(words[i - 1])
        prev_lower = prev_nucleo.lower()

        capitalizar = False

        # Regra 1: palavra anterior é movimento ou área
        if prev_lower in _MOVIMENTOS or prev_lower in _AREAS:
            capitalizar = True

        elif i >= 2:
            _, prev2_nucleo, _ = _strip_punct(words[i - 2])
            prev2_lower = prev2_nucleo.lower()

            # Regra 2: 2 posições atrás é movimento/área, anterior capitalizada
            if ((prev2_lower in _MOVIMENTOS or prev2_lower in _AREAS)
                    and prev_nucleo[0:1].isupper()):
                capitalizar = True

            # Regra 3: as 2 palavras anteriores formam expressão consolidada
            elif f'{prev2_lower} {prev_lower}' in _EXPRESSOES:
                capitalizar = True

        if capitalizar:
            pre, nuc, suf = _strip_punct(words[i])
            words[i] = pre + _TOPONIMICOS[nucleo_lower] + suf

    return ' '.join(words)


# ── CLI ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Normalizar texto FUNAG')
    parser.add_argument('texto', nargs='?', help='Texto a normalizar')
    parser.add_argument('--subtitulo', action='store_true',
                        help='Tratar como subtítulo (1a letra minúscula)')
    parser.add_argument('--stats', action='store_true',
                        help='Mostrar estatísticas do dicionário')
    parser.add_argument('--db', help='Caminho alternativo para dict.db')
    args = parser.parse_args()

    if args.db:
        reload_dict(args.db)

    if args.stats:
        s = stats()
        for k, v in s.items():
            print(f'  {k}: {v}')
        sys.exit(0)

    if args.texto:
        print(normalizar_texto(args.texto, eh_subtitulo=args.subtitulo))
    else:
        # Modo interativo: lê stdin linha a linha
        for line in sys.stdin:
            line = line.rstrip('\n')
            if line:
                print(normalizar_texto(line, eh_subtitulo=args.subtitulo))
