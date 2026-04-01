# sdbr16 — Runner de revisão

Pipeline: revisao | Gerado: 2026-03-31 | Artigos: 320
Referência: [pipeline_revisao.md](../docs/pipeline_revisao.md)

## Cobertura inicial

| Campo | N/320 | % |
|-------|-------|---|
| abstract | 307 | 96% |
| abstract_en | 3 | 1% |
| keywords | 228 | 71% |
| keywords_en | 0 | 0% |
| references | 263 | 82% |
| title_en | 0 | 0% |
| sections | 39 | — |

---

## Fase 0 — Diagnóstico e preenchimento

- [ ] **0.0** Checkpoint: `sqlite3 anais.db .dump > anais.sql` + commit
- [ ] **0.1** Levantar padrão de metadados (query cobertura → classificar campos)
- [ ] **0.2** Listar artigos fora do padrão (campos esperados mas ausentes)
- [ ] **0.3** Reinspecionar PDFs dos artigos fora do padrão (hierarquia: docx → plumber → pdftotext)
- [ ] **0.3b** Extrair fontes plumber
  ```
  python3 scripts/extrair_fontes_plumber.py --slug sdbr16 --profile-only
  python3 scripts/extrair_fontes_plumber.py --slug sdbr16
  ```
- [ ] **0.4** Seções/sessões — verificar nesta ordem:
  1. `fontes/` do seminário (HTML/XML de DVDs, sumários, programas)
  2. Folha de rosto dos artigos (cabeçalho do PDF indica eixo/sessão)
  3. Site original (campo `source` na tabela `seminars`)
  4. Busca na internet / Wayback Machine
  5. Site PROPAR (apenas Sul): `https://www.ufrgs.br/propar/wp-content/uploads/`
- [ ] **0.5** Preencher lacunas no banco (salvar JSON antes, verificar idioma dos abstracts)
- [ ] **0.6** Extrair metadados EN `[SKIP: abstract_en < 30%]`: `python3 scripts/extrair_metadados_en.py --slug sdbr16`
- [ ] **0.7** Extrair metadados ES (title_es, subtitle_es, abstract_es, keywords_es do plumber — independe do locale)
- [ ] **0.8** Verificar abstracts + auto-fix
  ```
  python3 scripts/validate_metadata.py --slug sdbr16 --fix
  ```
  Depois: varredura manual (truncamento, lixo, cruzamento de idiomas)

## Fase 1 — Revisão automática

- [ ] **1.1a** Títulos PT: seed + normalizar + revisão LLM
  ```
  python3 dict/seed_authors.py && python3 dict/seed_titles.py --apply
  python3 scripts/normalizar_maiusculas.py --slug sdbr16 --dry-run
  python3 scripts/normalizar_maiusculas.py --slug sdbr16
  ```
  → Revisão LLM palavra por palavra (ver §1.1a)
- [ ] **1.1b** Títulos EN/ES:
  ```
  python3 scripts/normalizar_titulos_en.py --slug sdbr16 --dry-run
  python3 scripts/normalizar_titulos_en.py --slug sdbr16
  ``` `[SKIP: title_en = 0]`
- [ ] **1.1c** Revisão LLM títulos EN/ES (cada título vs PDF) `[SKIP: title_en = 0]`
- [ ] **1.2a** Refs limpeza base
  ```
  python3 scripts/clean_references.py --slug sdbr16 --dry-run
  python3 scripts/clean_references.py --slug sdbr16
  python3 scripts/check_references.py --slug sdbr16 --summary
  ```
- [ ] **1.2b** Refs sweep (8 passadas)
  ```
  python3 scripts/fix_validation_issues.py --slug sdbr16 --sweep-refs --dry-run
  python3 scripts/fix_validation_issues.py --slug sdbr16 --sweep-refs
  ```
- [ ] **1.2b+** Re-backfills: `python3 scripts/clean_references.py --slug sdbr16`
- [ ] **1.2c** Refs revisão LLM — TODOS os artigos vs fontes (ver §1.2c)
- [ ] **1.3** Keywords
  ```
  python3 scripts/fix_validation_issues.py --slug sdbr16 --clean-keywords --dry-run
  python3 scripts/fix_validation_issues.py --slug sdbr16 --clean-keywords
  ```
- [ ] **1.5** Loop validação: `python3 scripts/fix_validation_issues.py --slug sdbr16 --loop`
- [ ] **1.6** Cobertura de metadados + metadados do seminário (título, ISBN, editora)
- [ ] **1.7** Autores: verificar completude vs PDF (confrontar cada artigo com o PDF)
- [ ] **1.8** Dedup autores: `python3 dict/seed_authors.py && python3 scripts/dedup_authors.py`
- [ ] **1.9** ORCID: `python3 scripts/fetch_orcid.py --search --slug sdbr16` → `--review` → `--apply`
- [ ] **1.10** Revisão LLM final — TODOS os artigos, TODOS os campos vs plumber
  Para CADA artigo: ler o plumber INTEIRO, confrontar CADA campo (título, subtítulo,
  abstract, abstract_en, keywords, keywords_en, title_en, refs) com o texto do PDF.
  Corrigir na hora (R8). Registrar resultado de CADA artigo abaixo.
  **ATENÇÃO**: subtítulo começa com minúscula (exceto nome próprio/sigla/expressão consolidada).
  PDFs em ALL CAPS devem ser convertidos respeitando essa regra.
  Ver §1.10 do pipeline para procedimento detalhado.
  **1.10 — Resultado por artigo:**
  - [ ] sdbr16-001:
  - [ ] sdbr16-002:
  - [ ] sdbr16-003:
  - [ ] sdbr16-004:
  - [ ] sdbr16-005:
  - [ ] sdbr16-006:
  - [ ] sdbr16-007:
  - [ ] sdbr16-008:
  - [ ] sdbr16-009:
  - [ ] sdbr16-010:
  - [ ] sdbr16-011:
  - [ ] sdbr16-012:
  - [ ] sdbr16-013:
  - [ ] sdbr16-014:
  - [ ] sdbr16-015:
  - [ ] sdbr16-016:
  - [ ] sdbr16-017:
  - [ ] sdbr16-018:
  - [ ] sdbr16-019:
  - [ ] sdbr16-020:
  - [ ] sdbr16-021:
  - [ ] sdbr16-022:
  - [ ] sdbr16-023:
  - [ ] sdbr16-024:
  - [ ] sdbr16-025:
  - [ ] sdbr16-026:
  - [ ] sdbr16-027:
  - [ ] sdbr16-028:
  - [ ] sdbr16-029:
  - [ ] sdbr16-030:
  - [ ] sdbr16-031:
  - [ ] sdbr16-032:
  - [ ] sdbr16-033:
  - [ ] sdbr16-034:
  - [ ] sdbr16-035:
  - [ ] sdbr16-036:
  - [ ] sdbr16-037:
  - [ ] sdbr16-038:
  - [ ] sdbr16-039:
  - [ ] sdbr16-040:
  - [ ] sdbr16-041:
  - [ ] sdbr16-042:
  - [ ] sdbr16-043:
  - [ ] sdbr16-044:
  - [ ] sdbr16-045:
  - [ ] sdbr16-046:
  - [ ] sdbr16-047:
  - [ ] sdbr16-048:
  - [ ] sdbr16-049:
  - [ ] sdbr16-050:
  - [ ] sdbr16-051:
  - [ ] sdbr16-052:
  - [ ] sdbr16-053:
  - [ ] sdbr16-054:
  - [ ] sdbr16-055:
  - [ ] sdbr16-056:
  - [ ] sdbr16-057:
  - [ ] sdbr16-058:
  - [ ] sdbr16-059:
  - [ ] sdbr16-060:
  - [ ] sdbr16-061:
  - [ ] sdbr16-062:
  - [ ] sdbr16-063:
  - [ ] sdbr16-064:
  - [ ] sdbr16-065:
  - [ ] sdbr16-066:
  - [ ] sdbr16-067:
  - [ ] sdbr16-068:
  - [ ] sdbr16-069:
  - [ ] sdbr16-070:
  - [ ] sdbr16-071:
  - [ ] sdbr16-072:
  - [ ] sdbr16-073:
  - [ ] sdbr16-074:
  - [ ] sdbr16-075:
  - [ ] sdbr16-076:
  - [ ] sdbr16-077:
  - [ ] sdbr16-078:
  - [ ] sdbr16-079:
  - [ ] sdbr16-080:
  - [ ] sdbr16-081:
  - [ ] sdbr16-082:
  - [ ] sdbr16-083:
  - [ ] sdbr16-084:
  - [ ] sdbr16-085:
  - [ ] sdbr16-086:
  - [ ] sdbr16-087:
  - [ ] sdbr16-088:
  - [ ] sdbr16-089:
  - [ ] sdbr16-090:
  - [ ] sdbr16-091:
  - [ ] sdbr16-092:
  - [ ] sdbr16-093:
  - [ ] sdbr16-094:
  - [ ] sdbr16-095:
  - [ ] sdbr16-096:
  - [ ] sdbr16-097:
  - [ ] sdbr16-098:
  - [ ] sdbr16-099:
  - [ ] sdbr16-100:
  - [ ] sdbr16-101:
  - [ ] sdbr16-102:
  - [ ] sdbr16-103:
  - [ ] sdbr16-104:
  - [ ] sdbr16-105:
  - [ ] sdbr16-106:
  - [ ] sdbr16-107:
  - [ ] sdbr16-108:
  - [ ] sdbr16-109:
  - [ ] sdbr16-110:
  - [ ] sdbr16-111:
  - [ ] sdbr16-112:
  - [ ] sdbr16-113:
  - [ ] sdbr16-114:
  - [ ] sdbr16-115:
  - [ ] sdbr16-116:
  - [ ] sdbr16-117:
  - [ ] sdbr16-118:
  - [ ] sdbr16-119:
  - [ ] sdbr16-120:
  - [ ] sdbr16-121:
  - [ ] sdbr16-122:
  - [ ] sdbr16-123:
  - [ ] sdbr16-124:
  - [ ] sdbr16-125:
  - [ ] sdbr16-126:
  - [ ] sdbr16-127:
  - [ ] sdbr16-128:
  - [ ] sdbr16-129:
  - [ ] sdbr16-130:
  - [ ] sdbr16-131:
  - [ ] sdbr16-132:
  - [ ] sdbr16-133:
  - [ ] sdbr16-134:
  - [ ] sdbr16-135:
  - [ ] sdbr16-136:
  - [ ] sdbr16-137:
  - [ ] sdbr16-138:
  - [ ] sdbr16-139:
  - [ ] sdbr16-140:
  - [ ] sdbr16-141:
  - [ ] sdbr16-142:
  - [ ] sdbr16-143:
  - [ ] sdbr16-144:
  - [ ] sdbr16-145:
  - [ ] sdbr16-146:
  - [ ] sdbr16-147:
  - [ ] sdbr16-148:
  - [ ] sdbr16-149:
  - [ ] sdbr16-150:
  - [ ] sdbr16-151:
  - [ ] sdbr16-152:
  - [ ] sdbr16-153:
  - [ ] sdbr16-154:
  - [ ] sdbr16-155:
  - [ ] sdbr16-156:
  - [ ] sdbr16-157:
  - [ ] sdbr16-158:
  - [ ] sdbr16-159:
  - [ ] sdbr16-160:
  - [ ] sdbr16-161:
  - [ ] sdbr16-162:
  - [ ] sdbr16-163:
  - [ ] sdbr16-164:
  - [ ] sdbr16-165:
  - [ ] sdbr16-166:
  - [ ] sdbr16-167:
  - [ ] sdbr16-168:
  - [ ] sdbr16-169:
  - [ ] sdbr16-170:
  - [ ] sdbr16-171:
  - [ ] sdbr16-172:
  - [ ] sdbr16-173:
  - [ ] sdbr16-174:
  - [ ] sdbr16-175:
  - [ ] sdbr16-176:
  - [ ] sdbr16-177:
  - [ ] sdbr16-178:
  - [ ] sdbr16-179:
  - [ ] sdbr16-180:
  - [ ] sdbr16-181:
  - [ ] sdbr16-182:
  - [ ] sdbr16-183:
  - [ ] sdbr16-184:
  - [ ] sdbr16-185:
  - [ ] sdbr16-186:
  - [ ] sdbr16-187:
  - [ ] sdbr16-188:
  - [ ] sdbr16-189:
  - [ ] sdbr16-190:
  - [ ] sdbr16-191:
  - [ ] sdbr16-192:
  - [ ] sdbr16-193:
  - [ ] sdbr16-194:
  - [ ] sdbr16-195:
  - [ ] sdbr16-196:
  - [ ] sdbr16-197:
  - [ ] sdbr16-198:
  - [ ] sdbr16-199:
  - [ ] sdbr16-200:
  - [ ] sdbr16-201:
  - [ ] sdbr16-202:
  - [ ] sdbr16-203:
  - [ ] sdbr16-204:
  - [ ] sdbr16-205:
  - [ ] sdbr16-206:
  - [ ] sdbr16-207:
  - [ ] sdbr16-208:
  - [ ] sdbr16-209:
  - [ ] sdbr16-210:
  - [ ] sdbr16-211:
  - [ ] sdbr16-212:
  - [ ] sdbr16-213:
  - [ ] sdbr16-214:
  - [ ] sdbr16-215:
  - [ ] sdbr16-216:
  - [ ] sdbr16-217:
  - [ ] sdbr16-218:
  - [ ] sdbr16-219:
  - [ ] sdbr16-220:
  - [ ] sdbr16-221:
  - [ ] sdbr16-222:
  - [ ] sdbr16-223:
  - [ ] sdbr16-224:
  - [ ] sdbr16-225:
  - [ ] sdbr16-226:
  - [ ] sdbr16-227:
  - [ ] sdbr16-228:
  - [ ] sdbr16-229:
  - [ ] sdbr16-230:
  - [ ] sdbr16-231:
  - [ ] sdbr16-232:
  - [ ] sdbr16-233:
  - [ ] sdbr16-234:
  - [ ] sdbr16-235:
  - [ ] sdbr16-236:
  - [ ] sdbr16-237:
  - [ ] sdbr16-238:
  - [ ] sdbr16-239:
  - [ ] sdbr16-240:
  - [ ] sdbr16-241:
  - [ ] sdbr16-242:
  - [ ] sdbr16-243:
  - [ ] sdbr16-244:
  - [ ] sdbr16-245:
  - [ ] sdbr16-246:
  - [ ] sdbr16-247:
  - [ ] sdbr16-248:
  - [ ] sdbr16-249:
  - [ ] sdbr16-250:
  - [ ] sdbr16-251:
  - [ ] sdbr16-252:
  - [ ] sdbr16-253:
  - [ ] sdbr16-254:
  - [ ] sdbr16-255:
  - [ ] sdbr16-256:
  - [ ] sdbr16-257:
  - [ ] sdbr16-258:
  - [ ] sdbr16-259:
  - [ ] sdbr16-260:
  - [ ] sdbr16-261:
  - [ ] sdbr16-262:
  - [ ] sdbr16-263:
  - [ ] sdbr16-264:
  - [ ] sdbr16-265:
  - [ ] sdbr16-266:
  - [ ] sdbr16-267:
  - [ ] sdbr16-268:
  - [ ] sdbr16-269:
  - [ ] sdbr16-270:
  - [ ] sdbr16-271:
  - [ ] sdbr16-272:
  - [ ] sdbr16-273:
  - [ ] sdbr16-274:
  - [ ] sdbr16-275:
  - [ ] sdbr16-276:
  - [ ] sdbr16-277:
  - [ ] sdbr16-278:
  - [ ] sdbr16-279:
  - [ ] sdbr16-280:
  - [ ] sdbr16-281:
  - [ ] sdbr16-282:
  - [ ] sdbr16-283:
  - [ ] sdbr16-284:
  - [ ] sdbr16-285:
  - [ ] sdbr16-m01:
  - [ ] sdbr16-m02:
  - [ ] sdbr16-m03:
  - [ ] sdbr16-m04:
  - [ ] sdbr16-m05:
  - [ ] sdbr16-m06:
  - [ ] sdbr16-m07:
  - [ ] sdbr16-m08:
  - [ ] sdbr16-m09:
  - [ ] sdbr16-m10:
  - [ ] sdbr16-m11:
  - [ ] sdbr16-m12:
  - [ ] sdbr16-m13:
  - [ ] sdbr16-m14:
  - [ ] sdbr16-m15:
  - [ ] sdbr16-m16:
  - [ ] sdbr16-m17:
  - [ ] sdbr16-m18:
  - [ ] sdbr16-m19:
  - [ ] sdbr16-m20:
  - [ ] sdbr16-m21:
  - [ ] sdbr16-m22:
  - [ ] sdbr16-m23:
  - [ ] sdbr16-m24:
  - [ ] sdbr16-m25:
  - [ ] sdbr16-m26:
  - [ ] sdbr16-m27:
  - [ ] sdbr16-m28:
  - [ ] sdbr16-m29:
  - [ ] sdbr16-m30:
  - [ ] sdbr16-m31:
  - [ ] sdbr16-m32:
  - [ ] sdbr16-m33:
  - [ ] sdbr16-m34:
  - [ ] sdbr16-m35:

## Fase 2 — HTML de revisão + checkpoint

- [ ] **2.0** Validação final + HTML + commit
  ```
  python3 scripts/validate_metadata.py --slug sdbr16 --fix
  python3 scripts/gerar_revisao_html.py sdbr16
  sqlite3 anais.db .dump > anais.sql
  git add anais.sql revisao/sdbr16-* && git commit -m "sdbr16 revisão automática (Fases 0-2)"
  ```

→ Próximo: [pipeline de revisão humana](../docs/pipeline_revisao_humana.md)

## Fase 3 — Aprendizado (após revisão humana)

- [ ] **3.1** Diagnóstico unificado (correções automáticas + humanas → causa raiz)
- [ ] **3.2** Atualizar dict.db (remover genéricos, adicionar nomes próprios)
- [ ] **3.3** Atualizar scripts (se >=3 artigos com mesmo erro não coberto)
- [ ] **3.4** Atualizar pipeline (se gaps na ordem de execução)
- [ ] **3.5** Verificar: dry-run sem regressão
- [ ] **3.6** Registrar aprendizado (JSON + MEMORY.md)
- [ ] **3.7** Revisão de engenharia (autoavaliação + lints)
- [ ] **3.8** Checklist de conclusão
- [ ] **3.9** Fechar: dump + commit + push + CLAUDE.md
