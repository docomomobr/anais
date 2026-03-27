# Diretrizes do Projeto — Anais Docomomo Brasil

Convenções e referência rápida para migração dos anais dos seminários Docomomo Brasil.

Referência técnica OJS: [`docs/archive/ojs_reference.md`](docs/archive/ojs_reference.md)
Regras de processamento de dados: [`docs/regras_dados.md`](docs/regras_dados.md)
Fontes das seções/eixos temáticos: [`docs/fontes_secoes.md`](docs/fontes_secoes.md)

---

## Seminários revisados — NÃO ALTERAR

44 seminários revisados (sdbr01-15, sdsul01-08, sdpr01-02, sdmg01, sdrj02-04, sdnne01-10, sdsp03, sdsp05-08).
**NÃO modificar seus dados** sem pedido explícito do usuário.
Tabela completa: [`docs/seminarios_revisados.md`](docs/seminarios_revisados.md)

---

## Regras de ouro

### Listas de revisão do usuário

Quando o usuário fornece `revisao/{slug}-rev.md`:
1. Ler o arquivo **inteiro** antes de começar
2. Listar **todos** os itens encontrados
3. Executar **cada item**, sem exceção, na ordem
4. Verificar cada item no banco após execução
5. Reportar checklist completa item a item
6. NÃO buscar outros problemas — isso é outra fase

### Pipeline existente

ANTES de escrever qualquer código ou rodar qualquer comando:
1. Verificar se existe `revisao/{slug}-runner.md` — se sim, **seguir o runner**
2. Se não existe, gerar: `python3 scripts/gerar_runner.py {slug}`
3. Consultar `docs/pipeline_*.md` apenas para detalhes e edge cases — o runner é a fonte primária
4. Verificar se já existe script em `scripts/` ou `regionais/*/scripts/`
5. Se o script existe, USAR. Se não existe, PERGUNTAR antes de criar.
6. NUNCA escrever Python ad-hoc inline quando existe script para a tarefa.
7. NUNCA alterar o banco sem aprovação explícita do usuário.
8. NUNCA gerar, traduzir ou inventar metadados. Títulos, abstracts, keywords (em qualquer idioma) são **extraídos** do PDF/docx/fontes — jamais traduzidos ou gerados por LLM. Campo ausente no documento = campo vazio no banco.

Runners: `python3 scripts/gerar_runner.py SLUG` (revisão) | `--type producao` (publicação) | sem args (lista todos) | `--status` (progresso)

### Hierarquia de fontes para extração

Verificar **nesta ordem**:
1. **doc/docx originais** → `python-docx` (preserva estilos). **NÃO converter para .txt**. Podem estar em `fontes/anais/`.
2. **pdfplumber** → `fontes_plumber/`. Boa qualidade, separa refs de notas por font_size.
3. **pdftotext** → `fontes/`. Fallback.

**SEMPRE verificar doc/docx ANTES de rodar pdfplumber.**
**NUNCA reconstruir manualmente texto fragmentado.**

### Zenodo API (InvenioRDM)

**PUT no draft SUBSTITUI TODO o metadata** — enviar payload **COMPLETO**.

Para corrigir metadados publicados:
1. `POST /api/records/{id}/versions` → draft de nova versão
2. `POST /api/records/{new_id}/draft/actions/files-import` → copia arquivos
3. `PUT /api/records/{new_id}/draft` → payload completo (todos os campos)
4. `POST /api/records/{new_id}/draft/actions/publish`

Community: API exige **UUID** (não slug) — usar `_resolve_community_id()`.
Editors: NÃO incluir ORCID dos editors (spam de notificações). ORCID só nos creators.

---

## Estrutura do Projeto

```
anais/
├── nacionais/           # Seminários nacionais (sdbr01-sdbr15)
├── regionais/
│   ├── nne/             # Norte/Nordeste (sdnne01-10)
│   ├── se/              # Sudeste (sdmg01, sdrj02-04, sdsp03-09)
│   └── sul/             # Sul (sdsul01-08, sdpr01-02)
├── scripts/             # Scripts principais
├── dict/                # NER + Entity Resolution (dict.db, normalizar.py)
├── docs/                # Documentação técnica
├── revisao/             # Revisão humana (runners, fichas, rev.md)
├── site/                # Site Hugo
├── anais.db             # Banco SQLite (gitignored)
└── anais.sql            # Dump textual do banco (versionado)
```

Regionais: `regionais/{grupo}/{slug}/fontes/` (bruto), `pdfs/` (finais), `fontes_plumber/` (extração).

---

## Credenciais

Em `.credentials` e `.env` (ambos gitignored). Scripts leem de variáveis de ambiente.

---

## Scripts principais

| Script | Função |
|--------|--------|
| `scripts/normalizar_maiusculas.py` | Capitalização nos títulos. `--dry-run`, `--slug` |
| `dict/normalizar.py` | Módulo de normalização. 3 passadas: palavra, expressão, toponímico |
| `scripts/clean_references.py` | Limpeza de refs: split, backfill, join URLs. `--dry-run`, `--slug` |
| `scripts/check_references.py` | Detecta erros em refs. `--summary`, `--slug`, `--type` |
| `scripts/validate_metadata.py` | Validação pós-pipeline. `--fix`, `--dry-run`, `--slug` |
| `scripts/upload_zenodo.py` | Upload PDFs para Zenodo. `--dry-run`, `--all` |
| `scripts/fix_zenodo_metadata.py` | Corrige metadados no Zenodo. `--dry-run`, aceita IDs |
| `scripts/db2hugo.py` | Gera conteúdo Hugo do anais.db |
| `scripts/gerar_revisao_html.py` | HTML de revisão. `SLUG` → `/tmp/revisao-SLUG.html` |
| `scripts/gerar_runner.py` | Gera/consulta runners (checklists executáveis) |

Pipelines: [`pipeline_tratamento.md`](docs/pipeline_tratamento.md) | [`pipeline_revisao.md`](docs/pipeline_revisao.md) | [`pipeline_revisao_humana.md`](docs/pipeline_revisao_humana.md) | [`pipeline_producao.md`](docs/pipeline_producao.md)

---

## Regras de dados — Resumo

Regras completas em [`docs/regras_dados.md`](docs/regras_dados.md).

- **Travessão**: ` - ` isolado → ` — ` (em-dash). Não tocar em intervalos, compostas, siglas, referências.
- **Capitalização**: título maiúscula; subtítulo minúscula (exceto nome próprio/sigla). Expressões consolidadas: "Arquitetura Moderna Brasileira", "Movimento Moderno", "Educação Patrimonial". Usa `dict/normalizar.py` + `dict.db`.
- **Autores**: partículas (de, da, do) no `givenname`; `familyname` = último sobrenome. Hispânicos: duplo sobrenome.
- **Afiliação**: apenas sigla (`FAU-USP`, `PROPAR-UFRGS`). Sem títulos, endereços, emails.
- **ORCID**: formato `0000-0000-0000-0000` (sem URL).

---

## Progresso — Checklist

### Revisão de metadados (pipeline_revisao.md)

- [x] **15 nacionais** (sdbr01-15): 1438 artigos revisados
- [x] **8 Sul** (sdsul01-08): 326 artigos revisados
- [x] **2 Paraná** (sdpr01-02): 45 artigos revisados
- [x] **1 Minas** (sdmg01): 26 artigos revisados
- [x] **3 Rio** (sdrj02-04): 42 artigos revisados
- [x] **10 N/NE** (sdnne01-10): 545 artigos revisados
- [x] **4 Sudeste SP** (sdsp03, sdsp05-08): 262 artigos revisados
- [ ] **1 Sudeste SP** (sdsp09): ~27 artigos pendentes

### Produção (pipeline_producao.md)

- [x] Site Hugo: deploy em `anais.docomomobrasil.com` (GitHub Pages)
- [x] Zenodo: nacionais publicados (community `docomomobr`, CC-BY-4.0)
- [ ] Zenodo: regionais pendentes
- [ ] DOIs via ABEC/Crossref (DOI por edição)
- [ ] Migração OJS → Hugo + redirects

### Infraestrutura

- [x] GitHub: `docomomobr/anais` (público)
- [x] DNS: CNAME `anais.docomomobrasil.com` → `docomomobr.github.io`
- [ ] DNS: CNAME `livros.docomomobrasil.com` (pendente criação no provedor)

---

## Referências complementares

- Devlog (registro cronológico): [`docs/devlog.md`](docs/devlog.md)
- Seminários revisados (tabela + status): [`docs/seminarios_revisados.md`](docs/seminarios_revisados.md)
- OJS (arquivado): [`docs/archive/ojs_reference.md`](docs/archive/ojs_reference.md)
