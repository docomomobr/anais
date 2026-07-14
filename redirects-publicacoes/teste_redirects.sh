#!/usr/bin/env bash
# Teste de aceitação dos redirects 301 de publicacoes.docomomobrasil.com.
# Uso: bash teste_redirects.sh https://anais-docomomo-redirects.pages.dev  (ou domínio real)
set -u
BASE="${1:?informe a URL base}"
falhas=0
check() {
  local path="$1" want="$2" loc="${3:-}"
  local resp; resp=$(curl -sI --max-time 20 "$BASE$path")
  local got; got=$(echo "$resp" | head -1 | grep -oE '[0-9]{3}')
  local gotloc; gotloc=$(echo "$resp" | grep -i '^location:' | tr -d '\r' | cut -d' ' -f2)
  if [ "$got" != "$want" ]; then echo "FAIL $path: status $got (esperado $want)"; falhas=$((falhas+1)); return; fi
  if [ -n "$loc" ] && [[ "$gotloc" != *"$loc"* ]]; then echo "FAIL $path: Location=$gotloc (esperado conter $loc)"; falhas=$((falhas+1)); return; fi
  echo "ok   $path → $got ${gotloc:+$gotloc}"
}
check /anais/article/view/1000 301 /brasil/sdbr09/sdbr09-012/
check /anais/article/view/1000/2013 301 /brasil/sdbr09/sdbr09-012/
check /anais/article/download/1000/2013 301 /brasil/sdbr09/sdbr09-012/
check /anais/article/view/197 301 /brasil/sdbr01/sdbr01-001/
check /anais/article/view/1420 301 /brasil/sdbr02/
check /anais/issue/view/14 301 /brasil/sdbr03/
check /anais 301 anais.docomomobrasil.com
check /anais/about 301 /expediente/
check /revista 301 revista.docomomobrasil.com
check /revista/issue/archive 301 revista.docomomobrasil.com
check /revista/rota/desconhecida 301 revista.docomomobrasil.com
check / 200
check /anais/article/view/999999 404
check /qualquer/coisa/inexistente 404
echo; [ $falhas -eq 0 ] && echo "TODOS OS TESTES PASSARAM" || echo "$falhas FALHAS"
exit $falhas
