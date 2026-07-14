// Teste local do _worker.js: simula env.ASSETS e exercita as rotas.
import { readFile } from 'node:fs/promises';
import worker from './_worker.js';

const files = {};
for (const f of ['redirects.json', '404.html', 'index.html'])
  files['/' + f] = await readFile(new URL(f, import.meta.url), 'utf8');

const env = { ASSETS: { fetch: async (req) => {
  const p = new URL(typeof req === 'string' ? req : req.url).pathname;
  const body = files[p] ?? files['/index.html'];
  return new Response(body, { status: 200 });
}}};

let fail = 0;
async function check(path, wantStatus, wantLoc) {
  const res = await worker.fetch(new Request('https://publicacoes.test' + path), env);
  const loc = res.headers.get('Location') || '';
  const ok = res.status === wantStatus && (!wantLoc || loc.includes(wantLoc));
  if (!ok) { fail++; console.log(`FAIL ${path}: ${res.status} ${loc}`); }
  else console.log(`ok   ${path} → ${res.status} ${loc}`);
}

await check('/anais/article/view/1000', 301, '/brasil/sdbr09/sdbr09-012/');
await check('/anais/article/view/1000/', 301, '/brasil/sdbr09/sdbr09-012/');   // barra final
await check('/anais/article/view/1000/2013', 301, '/brasil/sdbr09/sdbr09-012/'); // galley
await check('/anais/article/download/1000/2013', 301, '/brasil/sdbr09/sdbr09-012/');
await check('/anais/article/view/197', 301, '/brasil/sdbr01/sdbr01-001/');
await check('/anais/article/view/1420', 301, '/brasil/sdbr02/');   // front matter
await check('/anais/issue/view/14', 301, '/brasil/sdbr03/');
await check('/anais', 301, 'anais.docomomobrasil.com');
await check('/anais/about', 301, '/expediente/');
await check('/revista', 301, 'revista.docomomobrasil.com');
await check('/revista/rota/desconhecida', 301, 'revista.docomomobrasil.com');
await check('/', 200);
await check('/anais/article/view/999999', 404);
await check('/qualquer/coisa', 404);

console.log(fail ? `${fail} FALHAS` : 'TODOS OS 14 TESTES PASSARAM');
process.exit(fail ? 1 : 0);
