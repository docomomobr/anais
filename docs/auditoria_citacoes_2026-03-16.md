# Auditoria de Exportacao de Citacoes — 2026-03-16

Validacao dos 4 formatos de exportacao de citacao gerados pelo Hugo (BibTeX, RIS, CSL-JSON, YAML) com parsers automaticos.

---

## Resultado

| Formato | Parseia? | Parser usado | Issues encontrados |
|---------|----------|-------------|-------------------|
| BibTeX | Sim | bibtexparser | Faltavam abstract/keywords (corrigido) |
| RIS | Sim | rispy | Blank lines espurias, abstract com \\n (corrigido) |
| CSL-JSON | Sim | json.load | Trailing \\n no abstract (corrigido); aspas no titulo quebravam JSON (corrigido) |
| YAML | **Nao** | pyyaml | **Indentacao invalida nos autores — quebrava em 100% dos artigos** (corrigido) |

---

## Issues corrigidos

### CRITICO: YAML indentacao dos autores

O template gerava:
```yaml
authors:
- givenname: "Isabel de Lima"
    familyname: "Pinheiro"
```

YAML exige que as chaves do mapping dentro de um item de sequencia estejam na mesma indentacao. Corrigido para:
```yaml
authors:
  - givenname: "Isabel de Lima"
    familyname: "Pinheiro"
```

Tambem aplicado `jsonify` nos valores para escapar aspas em nomes.

### ALTO: BibTeX sem abstract e keywords

O template BibTeX nao emitia os campos `abstract` e `keywords`, presentes nos outros formatos. Citation managers (Zotero, Mendeley) que importam BibTeX perdiam essas informacoes. Adicionados.

### ALTO: CSL-JSON quebrava com aspas no titulo

Titulo `Teorias e praticas "modernistas"...` gerava JSON invalido pois as aspas nao eram escapadas. Corrigido com `jsonify` em todos os campos string (title, container-title, event-title, author names, keyword).

### MEDIO: CSL-JSON trailing newline no abstract

O campo `abstract` terminava com `\n` (vindo do block scalar do front matter Hugo). Corrigido com `strings.TrimRight "\n"` antes do `jsonify`.

### MEDIO: RIS blank lines

O output RIS tinha linhas em branco entre tags, que parsers estritos tratam como separadores de registro. Corrigido com whitespace control (`{{- end }}`).

### MEDIO: RIS SN para ISBN

O campo RIS `SN` e oficialmente para ISSN, mas o template o usava para ISBN de anais. Mantido assim pois e pratica comum e aceita pelos principais parsers. Documentado.

---

## O que funciona bem

- **BibTeX**: parseia com bibtexparser. Multi-author com `and` correto. Caracteres especiais (acentos, em-dash) passam em UTF-8. Tipo `@inproceedings` e key `sdbr15_001` bem formados. `&` escapado para LaTeX.
- **RIS**: parseia com rispy. Autores, keywords (um por tag KW), abstract, SP/EP separados. Language tag presente.
- **CSL-JSON**: parseia com json.load. Campos obrigatorios (title, type, author, issued) presentes. ORCIDs como URIs. Dates em array numerico. Artigos sem metadata opcional geram JSON valido.
- **YAML**: parseia com pyyaml apos correcao. Autores com givenname, familyname, affiliation, orcid. Abstract em block scalar. Keywords em lista.
- **Artigos minimos** (sem subtitle, abstract, keywords) geram exports validos em todos os 4 formatos — guards `{{ with }}` omitem campos ausentes corretamente.
- **Titulos com aspas e em-dash** passam corretamente em todos os formatos.

---

## Artigos testados

- sdbr15-001: rico (ORCID, 3 idiomas, subtitle)
- sdbr15-083: 4 autores, subtitle com em-dash
- sdbr15-089: minimal (sem subtitle, sem abstract, sem keywords)
- sdbr03-005: titulo com aspas duplas (`"modernistas"`)
