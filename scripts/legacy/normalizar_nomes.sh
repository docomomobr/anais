#!/bin/bash
# Script utilitário para normalizar nomes de arquivos PDF
# Uso: ./normalizar_nomes.sh [diretório]
#
# Regras:
# - Remove acentos (á→a, ç→c, etc.)
# - Remove caracteres especiais (' " ( ) etc.)
# - Trunca nomes longos (máx. 6 palavras após prefixo numérico)
# - Converte para minúsculas
# - Mantém prefixos numéricos (001_, 02_, etc.)

DIR="${1:-.}"
MAX_WORDS=6

if [ ! -d "$DIR" ]; then
    echo "Erro: Diretório '$DIR' não encontrado."
    exit 1
fi

cd "$DIR" || exit 1

normalize_name() {
    local name="$1"
    # Remove acentos
    name=$(echo "$name" | sed '
        s/[áàâãäÁÀÂÃÄ]/a/g
        s/[éèêëÉÈÊË]/e/g
        s/[íìîïÍÌÎÏ]/i/g
        s/[óòôõöÓÒÔÕÖ]/o/g
        s/[úùûüÚÙÛÜ]/u/g
        s/[çÇ]/c/g
        s/[ñÑ]/n/g
    ')
    # Converte para minúsculas
    name=$(echo "$name" | tr '[:upper:]' '[:lower:]')
    # Remove caracteres especiais (preserva letras, números, underline, hífen, ponto)
    name=$(echo "$name" | sed "s/[\"'(){}[\]<>!@#\$%^&*+=|\\:;,?]//g")
    # Limpa duplicados e artefatos
    name=$(echo "$name" | sed 's/__*/_/g; s/--*/-/g; s/_-/-/g; s/-_/-/g; s/\.\.*\././g')
    # Remove underscore/hífen antes de .pdf
    name=$(echo "$name" | sed 's/[_-]\.pdf/.pdf/g')
    echo "$name"
}

truncate_name() {
    local name="$1"
    # Extrai prefixo numérico (ex: 001_, 02_)
    local prefix=$(echo "$name" | grep -oE '^[0-9]+_')
    local rest="${name#$prefix}"
    local ext="${rest##*.}"
    rest="${rest%.$ext}"

    # Conta palavras (separadas por _ ou -)
    local words=$(echo "$rest" | tr '_-' '\n' | wc -l)

    if [ "$words" -gt "$MAX_WORDS" ]; then
        local truncated=$(echo "$rest" | tr '_-' '\n' | head -n "$MAX_WORDS" | tr '\n' '_')
        truncated="${truncated%_}"
        echo "${prefix}${truncated}.${ext}"
    else
        echo "$name"
    fi
}

echo "Normalizando arquivos em: $DIR"
echo ""
count=0

for file in *.pdf *.PDF 2>/dev/null; do
    [ -f "$file" ] || continue

    newname=$(normalize_name "$file")
    newname=$(truncate_name "$newname")

    if [ "$file" != "$newname" ]; then
        echo "  $file"
        echo "  → $newname"
        echo ""
        mv "$file" "$newname"
        count=$((count + 1))
    fi
done

echo "Concluído! $count arquivo(s) renomeado(s)."
