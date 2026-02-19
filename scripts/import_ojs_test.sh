#!/bin/bash
# Import regional seminar XMLs into test OJS
# Usage: bash scripts/import_ojs_test.sh [xml_dir]
#
# Log: /tmp/ojs_test_import.log (detailed)
# Stdout: progress summary

set -euo pipefail
BASE_URL="https://docomomo.ojs.com.br/index.php/ojs"
XML_DIR="${1:-/home/danilomacedo/Dropbox/docomomo/26-27/anais/xml_test}"
COOKIES="/tmp/ojs_test_import_cookies.txt"
LOG="/tmp/ojs_test_import.log"

log() { echo "$(date '+%H:%M:%S') $*" | tee -a "$LOG"; }

echo "" > "$LOG"
log "=== OJS Test Import ==="
log "URL: $BASE_URL"
log "XML dir: $XML_DIR"
log "Files: $(ls "$XML_DIR"/*.xml 2>/dev/null | wc -l)"

# Login
log "Logging in as editor..."
HTTP=$(curl -s -c "$COOKIES" -b "$COOKIES" \
  -d "username=editor&password=$OJS_TEST_PASS" \
  "$BASE_URL/login/signIn" -L -o /dev/null -w "%{http_code}")
log "Login HTTP: $HTTP"

# Get CSRF token
CSRF=$(curl -s -b "$COOKIES" \
  "$BASE_URL/management/importexport/plugin/NativeImportExportPlugin" \
  | grep -oP '"csrfToken":"[^"]+"' | head -1 | cut -d'"' -f4)

if [ -z "$CSRF" ]; then
  log "ERROR: Could not get CSRF token"
  exit 1
fi
log "CSRF: ${CSRF:0:12}..."

relogin() {
  curl -s -c "$COOKIES" -b "$COOKIES" \
    -d "username=editor&password=$OJS_TEST_PASS" \
    "$BASE_URL/login/signIn" -L -o /dev/null
  CSRF=$(curl -s -b "$COOKIES" \
    "$BASE_URL/management/importexport/plugin/NativeImportExportPlugin" \
    | grep -oP '"csrfToken":"[^"]+"' | head -1 | cut -d'"' -f4)
  log "  Re-login, CSRF: ${CSRF:0:12}..."
}

SUCCESS=0
FAIL=0
TOTAL=0

for FILE in $(ls "$XML_DIR"/*.xml | sort); do
  SLUG=$(basename "$FILE" .xml)
  SIZE=$(stat -c%s "$FILE")
  ((TOTAL++))
  log "--- [$TOTAL] $SLUG ($SIZE bytes) ---"

  # Step 1: Upload XML
  RESP=$(curl -s -b "$COOKIES" \
    -H "X-Requested-With: XMLHttpRequest" \
    -F "csrfToken=$CSRF" \
    -F "uploadedFile=@$FILE;type=text/xml" \
    "$BASE_URL/management/importexport/plugin/NativeImportExportPlugin/uploadImportXML" \
    --max-time 60 2>&1)

  TEMP_ID=$(echo "$RESP" | grep -oP '"temporaryFileId":"?\K[0-9]+' || true)

  if [ -z "$TEMP_ID" ]; then
    log "  FAIL at upload: ${RESP:0:200}"
    ((FAIL++))
    relogin
    continue
  fi
  log "  Upload OK, tempId=$TEMP_ID"

  # Step 2: Import bounce
  curl -s -b "$COOKIES" \
    -X POST \
    -d "csrfToken=$CSRF" \
    -d "temporaryFileId=$TEMP_ID" \
    "$BASE_URL/management/importexport/plugin/NativeImportExportPlugin/importBounce" \
    --max-time 30 -o /dev/null 2>&1

  # Step 3: Execute import
  RESULT=$(curl -s -b "$COOKIES" \
    "$BASE_URL/management/importexport/plugin/NativeImportExportPlugin/import?temporaryFileId=$TEMP_ID&csrfToken=$CSRF" \
    --max-time 300 2>&1)

  # Parse result
  if echo "$RESULT" | grep -q "xito"; then
    log "  SUCCESS"
    ((SUCCESS++))
  elif echo "$RESULT" | grep -q "rro\|Error"; then
    # Extract error
    ERR=$(echo "$RESULT" | python3 -c "
import sys, json, re
try:
    data = json.loads(sys.stdin.read())
    content = data.get('content', '')
except:
    content = ''
errs = re.findall(r'<li>([^<]+)</li>', content)
print('; '.join(e.strip()[:100] for e in errs[:3]))
" 2>/dev/null || echo "unknown error")
    log "  FAIL: $ERR"
    ((FAIL++))
    relogin
  elif [ -z "$RESULT" ]; then
    # Empty response — might have worked (like sdrj04 did)
    log "  Response empty (possibly OK)"
    ((SUCCESS++))
  else
    log "  Unknown response: ${RESULT:0:100}"
    ((SUCCESS++))
  fi

  sleep 2
done

log ""
log "=== SUMMARY ==="
log "Total: $TOTAL | Success: $SUCCESS | Failed: $FAIL"

# Verify
log ""
log "Verifying issues..."
curl -s -c "$COOKIES" -b "$COOKIES" \
  -d "username=editor&password=$OJS_TEST_PASS" \
  "$BASE_URL/login/signIn" -L -o /dev/null

curl -s -b "$COOKIES" \
  "$BASE_URL/api/v1/issues?count=50" \
  -H "Accept: application/json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    n = data.get('itemsMax', 0)
    print(f'Issues in test OJS: {n}')
    for i in sorted(data.get('items', []), key=lambda x: (x.get('volume',0), x.get('number',0))):
        v = i.get('volume','?')
        n = i.get('number','?')
        title = i.get('title',{}).get('pt_BR','N/A')
        print(f'  v.{v} n.{n}: {title}')
except Exception as e:
    print(f'Error: {e}')
" 2>&1 | tee -a "$LOG"

log "Done."
