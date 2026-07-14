# publicacoes.docomomobrasil.com — redirects 301 (Cloudflare Pages)

Substitui as páginas de meta refresh (GitHub Pages, repo
`docomomobr/publicacoes`) por redirecionamentos HTTP 301 reais,
transferindo a autoridade das URLs antigas do OJS para
`anais.docomomobrasil.com` e `revista.docomomobrasil.com`.

## Conteúdo

- `_worker.js` — Pages Function: 301 por lookup no mapa; raiz = página-hub;
  URL desconhecida = 404 de cortesia (**sem** redirect pra home — o Google
  trata redirect-para-home em massa como soft-404).
- `redirects.json` — mapa gerado por `scripts/gerar_redirects_netlify.py`
  (repo anais): 1.610 rotas exatas + 1.421 artigos por ojs_id (cobre
  `view/{id}[/{galley}]` e `download/{id}/*`). NÃO editar à mão.
- `index.html` — página-hub da raiz (o domínio serve Anais E Revista).
- `404.html` — cortesia, noindex.
- `test-worker.mjs` — 14 casos: `node test-worker.mjs`.

## Deploy (conta Cloudflare tesouraria, a mesma do worker OAI)

1. Painel → Workers & Pages → Create → **Pages** → "Upload assets"
   (direct upload). Nome sugerido: `publicacoes-redirects`.
2. Arrastar TODOS os arquivos desta pasta (o `_worker.js` na raiz ativa
   o modo avançado de Functions automaticamente).
3. Testar na URL provisória `https://publicacoes-redirects.pages.dev`:
   abrir `/anais/article/view/1000` no navegador (deve cair na página
   do artigo no site novo) — ou rodar os curls do teste de aceitação.
4. Custom domains → Add: `publicacoes.docomomobrasil.com`
   (Cloudflare instrui e valida via CNAME; TLS automático).
5. No provedor DNS: editar o CNAME de `publicacoes`
   (de `docomomobr.github.io` para `publicacoes-redirects.pages.dev`).
6. Validar no domínio real:
   `curl -sI https://publicacoes.docomomobrasil.com/anais/article/view/1000 | head -3`
   → deve responder `301` com `location:` da página nova.

## Rollback

Reverter o CNAME para `docomomobr.github.io` — o GitHub Pages com o
meta refresh continua intacto e volta a responder em minutos.

## Atualização do mapa

Regenerar com `python3 scripts/gerar_redirects_netlify.py CLONE SAIDA`
no repo anais e re-subir `redirects.json` no painel (ou novo upload).
