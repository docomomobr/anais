// Teste local do worker de claims: D1 simulado (sqlite em memória via
// Map simples), fetch de ORCID/Brevo stubado. Uso: node claims/test-worker.mjs
import { webcrypto } from 'node:crypto';
globalThis.crypto ??= webcrypto;
const { default: worker, gerarToken } = await import('./worker.js');

// ── stub D1 mínimo (só o que o worker usa)
const mem = { claims: [], optouts: new Set(), solicitacoes: [] };
const DB = {
  prepare(sql) {
    return {
      bind(...args) {
        return {
          async run() {
            if (sql.includes('INSERT INTO claims')) mem.claims.push(args);
            else if (sql.includes('INSERT OR IGNORE INTO optouts')) mem.optouts.add(args[0]);
            else if (sql.includes('INSERT INTO solicitacoes')) mem.solicitacoes.push(args);
          },
          async first() {
            if (sql.includes('COUNT(*) cnt FROM solicitacoes')) {
              return { cnt: mem.solicitacoes.filter((s) => s[0] === args[0]).length };
            }
            return {};
          },
        };
      },
    };
  },
};

const enviados = [];
globalThis.fetch = async (url, opts) => {
  if (String(url).includes('pub.orcid.org')) {
    const orcid = String(url).match(/v3\.0\/([^/]+)/)[1];
    if (orcid === '0000-0002-0332-097X') {
      return new Response(JSON.stringify({ name: { 'given-names': { value: 'Ricardo Alexandre' }, 'family-name': { value: 'Paiva' } } }), { status: 200 });
    }
    if (orcid === '0000-0001-9999-9999') {
      return new Response(JSON.stringify({ name: { 'given-names': { value: 'Fulana' }, 'family-name': { value: 'de Tal' } } }), { status: 200 });
    }
    return new Response('', { status: 404 });
  }
  if (String(url).includes('api.brevo.com')) {
    enviados.push(JSON.parse(opts.body));
    return new Response('{}', { status: 201 });
  }
  throw new Error('fetch inesperado: ' + url);
};

const env = { DB, CLAIM_SECRET: 'segredo-de-teste', BREVO_API_KEY: 'x', EMAIL_FROM: 'Docomomo Brasil <contato@docomomobrasil.com>' };
const B = 'https://claims.test';
let fail = 0;
const ok = (nome, cond) => { console.log(`${cond ? 'ok  ' : (fail++, 'FAIL')} ${nome}`); };

// 1. token de campanha → formulário
const tok = await gerarToken(env.CLAIM_SECRET, { a: 468, e: 'autor@exemplo.org', s: 'macedo-danilo-matoso' });
let r = await worker.fetch(new Request(`${B}/c/${tok}`), env);
let html = await r.text();
ok('GET formulário', r.status === 200 && html.includes('macedo-danilo-matoso') && html.includes('autor@exemplo.org'));

// 2. token adulterado → inválido
r = await worker.fetch(new Request(`${B}/c/${tok.slice(0, -4)}zzzz`), env);
ok('token adulterado rejeitado', (await r.text()).includes('Link inválido'));

// 3. claim com ORCID válido e nome compatível
let fd = new FormData();
fd.set('nome', 'Ricardo Alexandre Paiva'); fd.set('orcid', '0000-0002-0332-097X'); fd.set('obs', '');
r = await worker.fetch(new Request(`${B}/c/${tok}`, { method: 'POST', body: fd }), env);
ok('claim válido gravado', (await r.text()).includes('Recebido') && mem.claims.length === 1);

// 4. ORCID de outra pessoa → recusa com nome do dono
fd = new FormData();
fd.set('nome', 'Ricardo Alexandre Paiva'); fd.set('orcid', '0000-0001-9999-9999');
r = await worker.fetch(new Request(`${B}/c/${tok}`, { method: 'POST', body: fd }), env);
html = await r.text();
ok('ORCID de terceiro recusado', html.includes('Fulana de Tal') && mem.claims.length === 1);

// 5. ORCID formato errado
fd = new FormData(); fd.set('nome', 'X Y'); fd.set('orcid', '1234');
r = await worker.fetch(new Request(`${B}/c/${tok}`, { method: 'POST', body: fd }), env);
ok('formato inválido recusado', (await r.text()).includes('formato'));

// 6. opt-out 1 clique + idempotente
r = await worker.fetch(new Request(`${B}/o/${tok}`), env);
ok('opt-out', (await r.text()).includes('Pronto') && mem.optouts.has('autor@exemplo.org'));
await worker.fetch(new Request(`${B}/o/${tok}`), env);
ok('opt-out idempotente', mem.optouts.size === 1);

// 7. fluxo orgânico: solicitar link → e-mail com token válido
fd = new FormData(); fd.set('email', 'organico@exemplo.org'); fd.set('slug', 'abarca-gonzalo');
r = await worker.fetch(new Request(`${B}/solicitar`, { method: 'POST', body: fd }), env);
ok('solicitação enviada', (await r.text()).includes('Enviado') && enviados.length === 1);
const link = enviados[0].htmlContent.match(/\/c\/([A-Za-z0-9_.-]+)/)[1];
r = await worker.fetch(new Request(`${B}/c/${link}`), env);
ok('token do e-mail abre formulário', (await r.text()).includes('abarca-gonzalo'));

// 8. rate limit (3/dia)
for (let i = 0; i < 3; i++) {
  fd = new FormData(); fd.set('email', 'organico@exemplo.org'); fd.set('slug', 'abarca-gonzalo');
  r = await worker.fetch(new Request(`${B}/solicitar`, { method: 'POST', body: fd }), env);
}
ok('rate limit', (await r.text()).includes('Limite diário'));

console.log(fail ? `${fail} FALHAS` : 'TODOS OS TESTES PASSARAM');
process.exit(fail ? 1 : 0);
