# Auditoria do Pipeline de Producao — 2026-03-16

Auditoria completa do pipeline de producao (Zenodo + Hugo + Deploy) por dois auditores especializados em publicacoes academicas.

---

## Veredicto geral

O pipeline esta **bem acima da media** para publicacoes academicas. Cobre Google Scholar (Highwire Press), Dublin Core, Schema.org JSON-LD, COinS, Signposting (FAIR), Open Graph, Twitter Cards, e 4 formatos de exportacao de citacao (BibTeX, RIS, CSL-JSON, YAML). A maioria dos repositorios institucionais nao chega a esse nivel.

---

## O que esta bem feito

### Templates e Metadados
- **Google Scholar / Highwire Press** — Todas as tags criticas presentes: citation_title, citation_author, citation_publication_date, citation_conference_title, citation_pdf_url, citation_doi, citation_isbn, citation_firstpage, citation_lastpage, citation_abstract, citation_language, citation_author_institution, citation_author_orcid. Mais completo que a maioria das instalacoes OJS.
- **Dublin Core** — Cobertura abrangente incluindo DCTERMS.bibliographicCitation e DCTERMS.extent.
- **Signposting (FAIR)** — Links cite-as, item, license, describedby, author presentes. ResourceSync signposting map (signmap.xml). Raro e excelente para descoberta por maquinas.
- **COinS** — Presente nas paginas de artigo E nas listagens de eventos (COinS individual por artigo). Zotero captura citacoes de ambos contextos.
- **Exportacoes de citacao** — BibTeX, RIS, CSL-JSON, YAML com MIME types corretos e Hugo output formats customizados.
- **Acessibilidade** — Skip link, aria-label na nav, :focus-visible, HTML5 semantico (article, nav, main, header, footer, section), design responsivo.
- **Performance** — font-display: swap no Google Fonts, Pagefind para busca client-side (sem dependencia de servidor), GoatCounter (privacy-friendly, sem cookies), system font stack para body text.
- **Citacao ABNT** — Formato NBR 6023:2018 correto no bloco "Como citar".

### Pipeline de Dados
- **API InvenioRDM correta** — Uso correto da API nova (nao a legacy deprecated).
- **Upload 3-step** — initiate/content/commit conforme docs InvenioRDM.
- **Retry com backoff** — Logica de retry com backoff exponencial para erros de rede.
- **Limpeza de draft orfao** — _delete_draft() previne registros orfaos no Zenodo.
- **Idempotente** — Skip-existing por padrao, re-execucao segura.
- **SQL parametrizado** — Sem risco de SQL injection.
- **Rate limiting** — 1.5s entre artigos.

---

## Issues encontrados

### CRITICOS (corrigir antes de producao)

#### H3. Licenca CC-BY-4.0 vs CC-BY-NC-ND-4.0
- **Arquivos**: upload_zenodo.py (cc-by-4.0) vs db2hugo.py (cc-by-nc-nd-4.0)
- **Impacto**: Licencas incompativeis. Uma vez publicado no Zenodo com CC-BY, nao da para restringir depois. CC-BY permite uso comercial e derivados; CC-BY-NC-ND nao.
- **Acao**: Decidir qual licenca e alinhar ambos os scripts.

#### H1. File handle exaurido no retry do upload
- **Arquivo**: upload_zenodo.py, _upload_file()
- **Impacto**: Se o upload do PDF falha e o retry roda, o ponteiro do arquivo ja esta no EOF. Segunda tentativa envia 0 bytes.
- **Acao**: Re-abrir arquivo ou ler para memoria antes do retry.

#### H2. upload_volume nao limpa draft orfao
- **Arquivo**: upload_zenodo.py, upload_volume()
- **Impacto**: Se upload do PDF do volume falha, draft fica pendurado no Zenodo.
- **Acao**: Adicionar _delete_draft() como em upload_article().

### ALTOS

#### H4. JSON-LD usa Periodical em vez de Book para proceedings
- **Arquivo**: site/layouts/partials/jsonld.html
- **Impacto**: Google Scholar espera Book para proceedings, nao Periodical.
- **Acao**: Reverter para Book (anais de congresso sao publicacao em livro, nao periodico).

#### RIS: idioma hardcoded e campo SP com range inteiro
- **Arquivo**: site/layouts/artigo/single.ris
- **Impacto**: Artigos em ES/EN exportam LA=pt. Campo SP tem "123-145" em vez de SP=123 + EP=145 separados.
- **Acao**: Usar locale do artigo; split SP/EP.

#### CSL-JSON: faltam abstract e keyword
- **Arquivo**: site/layouts/artigo/single.json
- **Impacto**: Citation managers nao recebem resumo e palavras-chave.
- **Acao**: Adicionar campos abstract e keyword.

#### og:image/twitter:image ausentes em paginas nao-artigo
- **Arquivo**: baseof.html / head-meta.html
- **Impacto**: Cards sociais sem imagem fora de paginas de artigo. Arquivo og-default.png referenciado no config nao existe.
- **Acao**: Criar og-default.png; mover fallback para baseof.html.

### MEDIOS

| # | Area | Issue |
|---|------|-------|
| M1 | Upload | Sem retry em HTTP 429 (rate limit) ou 5xx |
| M2 | Scholar | Falta tag citation_keywords |
| M3 | BibTeX | Hifens no key invalidos em alguns processadores |
| M4 | BibTeX | Sem escape de caracteres LaTeX |
| M5 | Acessibilidade | alt="" nas capas (deveriam ter descricao) |
| M6 | SEO | Falta meta name="description" nas paginas de artigo |
| M7 | Dublin Core | ISBN como string, deveria ser URN (urn:isbn:...) |
| M10 | JSON-LD | Sem structured data na pagina de listagem do evento |
| M-prog | Pipeline | Sem progresso [42/1304] no upload (45min+ sem feedback) |
| M-reg | Pipeline | Tabela de upload so lista nacionais — regionais nao documentados |
| M-editor | Upload | _build_editors name parsing naive para nomes brasileiros (rsplit no ultimo espaco) |
| M-comm | Upload | _submit_community e _accept_community_request sem retry |

### BAIXOS

| # | Area | Issue |
|---|------|-------|
| L1 | CSS/i18n | hyphens: auto sem lang nos abstracts EN/ES |
| L2 | Data | event_location vs event_city inconsistencia entre templates |
| L3 | YAML export | Aspas no titulo quebram YAML |
| L4 | Acessibilidade | Sem prefers-reduced-motion |
| L5 | Performance | Google Fonts render-blocking |
| L6 | Acessibilidade | Breadcrumb sem aria-label="Breadcrumb" |
| L7 | Acessibilidade | Search sem role="search" |
| L8 | BibTeX | Falta campo organization/publisher |
| L9 | SEO | Homepage sem h1 |
| L10 | Acessibilidade | Contraste borderline --gray-500 em texto pequeno |
| L-env | .env | Parser nao strip aspas dos valores |
| L-vol | Volume | DOI do volume nao e gravado na tabela seminars |
| L-json | Data | parse_json_field engole erros de JSON silenciosamente |
| L-date | DataCite | publication_date usa data do seminario, nao do artigo individual |

---

## Seguranca

- **Token handling**: Bom. Tokens vem de .env (gitignored) ou --token CLI.
- **SQL injection**: Sem risco. Queries parametrizadas em todo lugar.
- **LIMIT injection**: Seguro (int() e chamado).
- **Credenciais no repo**: Confirmado que nao ha.

## Escalabilidade

- **2679 artigos**: Pipeline suporta. SQLite indexado. Memoria O(1) por artigo.
- **Tempo estimado**: ~1300 nacionais a ~2s cada = ~43min. ~1200 regionais = ~40min. Total ~83min.
- **Hugo generation**: Em memoria, artigos escritos um por vez. Segundos para 2679 artigos.
- **Disco**: Site ~60-80 MB. Limite GitHub Pages: 1 GB.

---

## Prioridades de acao

### Antes do primeiro upload de producao
1. Decidir licenca (H3) — CC-BY ou CC-BY-NC-ND
2. Corrigir file handle no retry (H1)
3. Corrigir draft orfao no upload_volume (H2)
4. Corrigir .env quote stripping (L-env)

### Antes de escalar para regionais
5. Adicionar retry em HTTP 429 (M1)
6. Adicionar progresso [n/total] (M-prog)
7. Documentar plano de upload regional (M-reg)

### Melhorias de templates
8. Reverter JSON-LD para Book (H4)
9. Corrigir RIS (idioma + SP/EP)
10. Adicionar abstract/keyword ao CSL-JSON
11. Criar og-default.png + fallback
12. Adicionar citation_keywords, meta description
13. Corrigir alt text das capas
14. Adicionar lang nos abstracts EN/ES
15. Corrigir acessibilidade (aria-label, role, prefers-reduced-motion)
