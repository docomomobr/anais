# Devlog — Verificação de referências bibliográficas

Data: 2026-02-16

## Contexto

As referências bibliográficas dos 1942 artigos com refs no `anais.db` foram extraídas automaticamente de PDFs e fontes diversas. A extração automática introduziu três tipos de erro:

1. **Referências concatenadas**: múltiplas referências na mesma linha (separador não detectado)
2. **Não-referências**: trechos de texto corrido, legendas de figuras, notas de rodapé, URLs soltas
3. **Fragmentos**: referências incompletas ou continuações da referência anterior

## Script

`scripts/check_references.py` — detecta problemas via heurísticas:

### Heurísticas de detecção

| Tipo | Heurística | Limiar |
|------|-----------|--------|
| Concatenada (provável) | Comprimento > 800 chars | Alto |
| Concatenada (possível) | Comprimento > 400 chars | Médio |
| Concatenada (padrão) | Regex "ano. SOBRENOME," no meio do texto | Alto |
| Não-referência | Começa com minúscula (não é autor) | Médio |
| Não-referência | Legenda de figura (`Fig.`, `Fonte:`) | Alto |
| Não-referência | Alta proporção de palavras comuns (> 35%) | Médio |
| Não-referência | Sem ano e sem ponto | Alto |
| Fragmento | Comprimento < 25 chars | Alto |
| Fragmento | Referência vazia | Alto |

### Uso

```bash
# Resumo por seminário
python3 scripts/check_references.py --summary

# Detalhe de um seminário
python3 scripts/check_references.py --slug sdsul04

# Filtrar por tipo
python3 scripts/check_references.py --type concatenada
python3 scripts/check_references.py --type nao_ref
python3 scripts/check_references.py --type curta
```

## Resultado

```
Total de referências: 36409
Problemas detectados: 3341 (9.2%)
  - Concatenadas: 1341
  - Não-referências: 1471
  - Curtas/fragmentos: 529
```

### Seminários mais problemáticos

| Slug | Refs | Concat | Não-ref | Curta | % problemas |
|------|------|--------|---------|-------|-------------|
| sdsul05 | 962 | 238 | 213 | 25 | 49.5% |
| sdsul04 | 383 | 96 | 141 | 15 | 65.8% |
| sdnne10 | 3427 | 84 | 263 | 86 | 12.6% |
| sdbr10 | 854 | 127 | 53 | 5 | 21.7% |
| sdsul07 | 1239 | 50 | 78 | 107 | 19.0% |
| sdrj04 | 400 | 45 | 71 | 2 | 29.5% |

### Padrões observados

- **sdsul04 e sdsul05**: extração de PDFs capturou corpo do texto junto com as referências. Muitas "refs" são parágrafos narrativos inteiros.
- **sdnne10**: dados do Even3 — muitos resumos expandidos com refs de baixa qualidade.
- **sdbr10**: referências concatenadas (separador não detectado na extração).
- **sdsul07**: muitas refs curtas (fragmentos de refs cortadas).
- **sdrj04**: mix de URLs concatenadas e legendas de figuras.

## Limitações

- Heurísticas baseadas em comprimento e padrões textuais — falsos positivos e negativos são esperados.
- Referências em inglês/espanhol podem gerar falsos positivos na heurística de "palavras comuns".
- Refs com múltiplos autores (ex: "SILVA, A.; SANTOS, B.; OLIVEIRA, C.") podem ser marcadas como concatenadas pelo padrão "ano. SOBRENOME,".
- O script detecta mas não corrige — correção requer revisão manual ou re-extração dos PDFs.
