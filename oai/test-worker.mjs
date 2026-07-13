// Teste local do worker OAI-PMH: simula fetch() servindo o catálogo local
// e exercita os 6 verbos + erros. Uso: node oai/test-worker.mjs
import { readFile } from 'node:fs/promises';
import worker from './worker.js';

const catalog = await readFile(
  new URL('../site/static/oai-data/catalog.json', import.meta.url), 'utf8');
globalThis.fetch = async () => new Response(catalog, { status: 200 });

const BASE = 'https://oai-test.example/oai';
async function call(qs) {
  const res = await worker.fetch(new Request(`${BASE}?${qs}`));
  return res.text();
}

let failures = 0;
async function check(name, qs, ...expects) {
  const xml = await call(qs);
  const missing = expects.filter((e) => !xml.includes(e));
  if (missing.length) {
    failures++;
    console.log(`FAIL ${name}: faltou ${JSON.stringify(missing)}`);
    console.log(xml.slice(0, 600));
  } else {
    console.log(`ok   ${name}`);
  }
  return xml;
}

await check('Identify', 'verb=Identify',
  '<repositoryName>Anais Docomomo Brasil</repositoryName>',
  '<granularity>YYYY-MM-DD</granularity>');
await check('ListMetadataFormats', 'verb=ListMetadataFormats',
  '<metadataPrefix>oai_dc</metadataPrefix>');
await check('ListSets', 'verb=ListSets', '<setSpec>sdbr01</setSpec>');
await check('GetRecord', 'verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:anais.docomomobrasil.com:sdbr13-146',
  'Casas modernas de Aracaju', '<dc:creator>');
await check('GetRecord idErrado', 'verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:x:nada',
  'idDoesNotExist');
await check('ListIdentifiers', 'verb=ListIdentifiers&metadataPrefix=oai_dc',
  '<resumptionToken', 'completeListSize="3104"');
await check('ListRecords set', 'verb=ListRecords&metadataPrefix=oai_dc&set=sdsul06',
  '<dc:title', 'setSpec>sdsul06');
await check('badVerb', 'verb=Bogus', 'badVerb');
await check('formatoErrado', 'verb=ListRecords&metadataPrefix=marc', 'cannotDisseminateFormat');

// Paginação completa via resumptionToken
let xml = await call('verb=ListIdentifiers&metadataPrefix=oai_dc');
let total = 0, pages = 0;
for (;;) {
  total += (xml.match(/<identifier>/g) || []).length;
  pages++;
  const m = xml.match(/<resumptionToken[^>]*>([^<]+)<\/resumptionToken>/);
  if (!m) break;
  xml = await call(`verb=ListIdentifiers&resumptionToken=${encodeURIComponent(m[1])}`);
}
console.log(`${total === 3104 ? 'ok  ' : (failures++, 'FAIL')} paginação: ${total} identifiers em ${pages} páginas`);

// XML multilíngue num registro com abstract EN
xml = await call('verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:anais.docomomobrasil.com:sdnne07-036');
console.log(xml.includes('xml:lang="en"') ? 'ok   multilíngue (xml:lang=en presente)'
  : (failures++, 'FAIL multilíngue'));

process.exit(failures ? 1 : 0);
