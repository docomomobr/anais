/**
 * Redirects 301 de publicacoes.docomomobrasil.com — Cloudflare Pages.
 *
 * Substitui as páginas de meta refresh (GitHub Pages) por 301 reais.
 * Mapa em redirects.json (gerado por scripts/gerar_redirects_netlify.py
 * no repo anais): rotas exatas + artigos por ojs_id (cobrindo galley e
 * download). URL desconhecida → 404 de cortesia (NUNCA redirect pra home:
 * o Google trata redirect-para-home em massa como soft-404).
 *
 * Deploy: Cloudflare Pages, upload desta pasta — ver README.md.
 */

const ARTICLE_RE = /^\/anais\/article\/(?:view|download)\/(\d+)(?:\/|$)/;

let MAP = null;

async function loadMap(env) {
  if (!MAP) {
    const res = await env.ASSETS.fetch('https://x/redirects.json');
    MAP = await res.json();
  }
  return MAP;
}

function redirect301(target) {
  return new Response(null, {
    status: 301,
    headers: { Location: target, 'Cache-Control': 'public, max-age=3600' },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';

    // raiz é página-hub (o domínio servia Anais E Revista)
    if (path === '/') {
      return env.ASSETS.fetch(request);
    }

    const map = await loadMap(env);

    // rota exata
    const exact = map.exact[path];
    if (exact) return redirect301(exact);

    // artigo: view/{id}/{galley} e download/{id}/{qualquer}
    const m = path.match(ARTICLE_RE);
    if (m && map.article[m[1]]) return redirect301(map.article[m[1]]);

    // /revista/rota-não-mapeada → raiz da revista (prefixo conhecido)
    if (path === '/revista' || path.startsWith('/revista/')) {
      return redirect301('https://revista.docomomobrasil.com/');
    }

    // desconhecida → 404 de cortesia
    const notFound = await env.ASSETS.fetch(new Request(new URL('/404.html', url.origin)));
    return new Response(notFound.body, {
      status: 404,
      headers: { 'Content-Type': 'text/html; charset=UTF-8' },
    });
  },
};
