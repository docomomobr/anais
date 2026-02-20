# OJS 3.3 Native XML Import — Pesquisa e recomendacoes

Pesquisa realizada em 2026-02-11, baseada na documentacao oficial PKP, forum da comunidade e relatos de migracoes reais.

## Fontes consultadas

1. [Code4Lib — An XML-Based Migration from Digital Commons to OJS](https://journal.code4lib.org/articles/15988) — Migracao de 93 issues da Oregon State University
2. [PKP Forum — Native XML Plugin import file size error](https://forum.pkp.sfu.ca/t/native-xml-plugin-import-file-size-error/29542) — Limite de tamanho de arquivo
3. [PKP Forum — Problems importing native XML 3.3.0.21](https://forum.pkp.sfu.ca/t/problems-importing-native-xml-3-3-0-21/97271) — Erros de importacao e submissoes orfas
4. [pkp-lib #7898 — Thoughts about how to improve native XML import/export](https://github.com/pkp/pkp-lib/issues/7898) — Limitacoes reconhecidas pelo PKP
5. [pkp-lib #3276 — Native XML import fails on batch insert](https://github.com/pkp/pkp-lib/issues/3276) — Falhas em importacao em lote
6. [PKP Forum — Moving a large number of back issues](https://forum.pkp.sfu.ca/t/moving-a-large-number-of-back-issues-and-articles-into-ojs-from-other-source/64816) — Estrategia para migracao massiva
7. [PKP Forum — OJS native XML import/export no-embed option](https://forum.pkp.sfu.ca/t/ojs-native-xml-import-export-no-embed-option/72850) — Importacao sem PDFs embutidos

## Recomendacoes documentadas

### Agrupamento de artigos por XML

- O padrao do plugin e **1 XML por issue** (edicao). Cada XML contem a issue com todas as secoes e artigos.
- A migracao Code4Lib (fonte 1) fez 93 issues, 1 XML por issue, com sucesso.
- **NUNCA colocar 2+ issues no mesmo XML** — o importador cria issues duplicadas ou corrompe o banco (fonte 4).
- Para importacao **com PDFs em base64**: dividir em 1 artigo por XML (PDFs inflam ~37%, facilmente ultrapassa o limite). Abordagem validada na importacao do sdbr12 (82 XMLs, 1 artigo cada).

### Tamanho maximo de arquivo

- Padrao: **8 MB**, definido por `upload_max_filesize` e `post_max_size` do PHP (fonte 2).
- Nao e limitacao do plugin, e do PHP/servidor. Configuravel pelo admin.
- Nginx: tambem precisa de `client_max_body_size`.
- Nossos XMLs regionais sem PDFs: 66KB-506KB (bem abaixo).

### Numero de artigos por XML

- **Sem limite documentado**. A migracao Code4Lib importou issues inteiras sem problema.
- Na pratica, issues com muitos artigos (65+) levam mais tempo de processamento no servidor.

### PDFs embutidos

- Formato: `<embed encoding="base64">` dentro de `<submission_file>`.
- Aumentam ~37% o tamanho do arquivo original.
- Alternativa: importar so metadados, anexar PDFs depois pela interface editorial.
- Para producao, 1 artigo por XML com PDF e o caminho seguro.

### Metodos de importacao

| Metodo | Via | Vantagem | Desvantagem |
|--------|-----|----------|-------------|
| Web UI | Navegador | Sem automacao | Manual, 1 por vez |
| Web API | `uploadImportXML` + `importBounce` + `import` | Automatizavel | Sujeito a timeout de sessao e rate limiting |
| CLI | `php tools/importExport.php NativeImportExportPlugin import file.xml journal admin` | Robusto, sem sessao | Requer SSH |

### Problemas conhecidos

1. **Sessao expira durante importacao** (fonte 3, 5): O OJS web nao foi projetado para importacao automatizada em lote. Apos 5-7 uploads consecutivos, a sessao pode expirar ou o servidor pode rate-limitar.

2. **Issues duplicadas vazias**: Quando a importacao falha parcialmente, o OJS cria a issue mas nao insere os artigos. Importacoes subsequentes criam novas issues com o mesmo `url_path`. Limpeza manual necessaria.

3. **Submissoes orfas** (fonte 3): Importacoes falhadas podem deixar submissions sem publication no banco. Query de verificacao:
   ```sql
   SELECT s.submission_id FROM submissions s
   LEFT JOIN publications p ON s.current_publication_id = p.publication_id
   WHERE p.publication_id IS NULL
   ```

4. **Feedback de erro pouco claro** (fonte 4): Erros retornados pelo importador nem sempre indicam o problema real. Testar com 1-2 XMLs antes de rodar lote completo.

5. **Incompatibilidade entre versoes** (fonte 4): XMLs exportados de uma versao podem nao importar em outra. Sempre gerar XMLs frescos para a versao alvo.

### Pos-importacao

- A "edicao atual" (current issue) precisa ser definida manualmente.
- Verificar se o indice de busca foi atualizado.
- Conferir na pagina real (nao so na API) se abstract e keywords estao visiveis.

## Experiencia pratica do projeto (2026-02-11)

### Ambiente de teste (docomomo.ojs.com.br)

- OJS 3.3.0.21
- 21 seminarios regionais, 938 artigos esperados
- XMLs sem PDFs (so metadados), 66-506KB cada
- Importacao via web API automatizada (`scripts/import_ojs.py`)
- **Resultado**: 13/21 importados com sucesso apos multiplas tentativas
- **Problema principal**: sessao expira a cada 3-5 operacoes. Re-login funciona mas e lento.
- **Efeito colateral**: 34 issues duplicadas vazias criadas por tentativas falhadas. Limpeza via API levou ~10 minutos.

### Ambiente de producao (publicacoes.docomomobrasil.com)

- Servidor diferente (IP 216.238.104.86 vs 96.30.204.146 do teste)
- sdbr12 importado com sucesso (82 XMLs, 1 artigo por XML, via web API) — sem problemas de rate limiting
- Sem SSH disponivel. Provedor orientou nao usar IA na producao.

### Regras operacionais

1. **Deu problema → para → apaga → recomeca limpo**. Nunca retentar sem limpar issues vazias/parciais.
2. Para 1 artigo por XML: se falha, limpar so o artigo, nao a issue.
3. Para 1 issue por XML: se falha, limpar a issue inteira.
4. Verificar contagem apos cada importacao. Se parcial, apagar e parar.
5. Delays minimos: 30s entre importacoes para evitar rate limiting.
