# Endpoint OAI-PMH — Anais Docomomo Brasil

Expõe os 3.104 artigos em Dublin Core trilíngue para agregadores acadêmicos
(BASE, CORE, OpenAIRE, LA Referencia/oasisbr), via protocolo OAI-PMH 2.0.

## Arquitetura

```
anais.db ──gerar_oai.py──▶ site/static/oai-data/catalog.json  (13 MB, no site)
                                        ▲
                                        │ fetch (cache 1h na borda)
                            Cloudflare Worker (worker.js)
                                        ▲
                                        │ ?verb=ListRecords&metadataPrefix=oai_dc
                              BASE / CORE / OpenAIRE
```

O site continua 100% estático no GitHub Pages. O Worker é só a "recepção"
do protocolo: recebe o verbo, filtra o catálogo, responde XML.

## Passo a passo do deploy (uma vez)

1. **Publicar o catálogo**: o `catalog.json` precisa estar no ar em
   `https://anais.docomomobrasil.com/oai-data/catalog.json` — entra no
   próximo deploy normal do site (está em `site/static/`).

2. **Criar conta Cloudflare** (gratuita): https://dash.cloudflare.com/sign-up
   — só email e senha. Não pede cartão, não mexe em DNS.

3. **Criar o Worker**: no painel, *Workers & Pages → Create → Worker*.
   Dê o nome `oai-anais-docomomo` (o endereço final será
   `https://oai-anais-docomomo.<sua-conta>.workers.dev`). Clique *Deploy*
   e depois *Edit code*.

4. **Colar o código**: apague o exemplo, cole o conteúdo de `worker.js`
   inteiro, *Save and deploy*.

5. **Testar** (no navegador):
   - `https://<endereço-do-worker>/?verb=Identify`
   - `.../?verb=ListRecords&metadataPrefix=oai_dc`
   - `.../?verb=ListSets`
   - Validador oficial: https://validator.oaipmh.com/ (colar a URL base)

6. **Cadastrar nos agregadores** (com a URL base do worker):
   - **CORE**: https://core.ac.uk/data-providers (formulário; indexa e avisa
     por email)
   - **BASE**: https://www.base-search.net/about/en/suggest.php
   - **OpenAIRE**: https://provide.openaire.eu (usa o registro do OpenDOAR
     nº 11331, já aprovado)

## Manutenção

- Metadados mudaram no banco? `python3 scripts/gerar_oai.py` e deploy do
  site. O worker não precisa ser tocado (lê o catálogo novo em até 1h).
- Datestamps são preservados por hash de conteúdo: agregadores colhem
  incrementalmente só o que mudou.
- Teste local: `node oai/test-worker.mjs` (11 casos, protocolo completo).

## Limitações conhecidas

- `deletedRecord=no`: registros removidos do catálogo somem sem tombstone
  (para este acervo, remoção é rara/inexistente).
- Apenas `oai_dc` (suficiente para BASE/CORE; RIOXX/OpenAIRE-guidelines
  ficam para depois se algum agregador exigir).
- sdnne06 usa as URLs numéricas atuais (`/nne/sdnne06/43/`); quando os
  slugs forem normalizados, basta regenerar o catálogo.
