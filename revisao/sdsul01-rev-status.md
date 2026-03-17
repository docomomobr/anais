# sdsul01 — Rev-status

## Estado: Fase 0/1 parcial — INCOMPLETO

Pipeline iniciado mas NÃO seguido na ordem. Etapas abaixo precisam ser refeitas do zero seguindo o pipeline_revisao.md.

### O que foi feito (fora de ordem):
- 0.1 Levantar padrão ✅ (48 arts, 42 pt-BR + 6 es, keywords 1/48, refs 43/48)
- 1.1a normalizar_maiusculas.py ✅ (19 alterados, 3 falsos positivos corrigidos)
- 1.2a clean_references.py ✅ (2 backfills)
- 1.5 validate --fix ✅ (2 auto-fix A17, 36 issues reportados)

### O que NÃO foi feito:
- ❌ 0.0 Checkpoint inicial (dump + commit)
- ❌ 0.2 Identificar artigos fora do padrão
- ❌ 0.3 Reinspecionar PDFs fora do padrão
- ❌ 0.3b Extrair fontes pdfplumber
- ❌ 0.4 Preencher lacunas
- ❌ 0.5 Verificar abstracts (truncamento/idiomas)
- ❌ 0.6 Extrair metadados EN
- ❌ 1.1b Normalizar títulos EN/ES
- ❌ 1.1c Revisão LLM de títulos
- ❌ 1.2b sweep_refs
- ❌ 1.2c Revisão LLM de refs
- ❌ 1.3 Keywords
- ❌ 1.6 Auditoria final
- ❌ Fase 2 — HTML de revisão

### Próxima sessão: retomar do 0.0, seguindo pipeline na ordem.
