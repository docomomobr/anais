/**
 * Endpoint OAI-PMH 2.0 dos Anais Docomomo Brasil — Cloudflare Worker.
 *
 * Lê o catálogo pré-gerado (scripts/gerar_oai.py → /oai-data/catalog.json
 * no site estático) e implementa os 6 verbos do protocolo. Sem estado,
 * sem banco: todo o conteúdo vem do catálogo, cacheado na borda.
 *
 * Deploy: colar no painel Cloudflare Workers (dash.cloudflare.com) —
 * ver oai/README.md para o passo a passo.
 */

const CATALOG_URL = 'https://anais.docomomobrasil.com/oai-data/catalog.json';
const PAGE_SIZE = 100;
const CACHE_TTL = 3600; // 1h — catálogo muda raramente

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const p = url.searchParams;
    const baseURL = url.origin + url.pathname;
    const verb = p.get('verb') || '';

    let catalog;
    try {
      const res = await fetch(CATALOG_URL, {
        cf: { cacheTtl: CACHE_TTL, cacheEverything: true },
      });
      if (!res.ok) throw new Error(`catalog ${res.status}`);
      catalog = await res.json();
    } catch (e) {
      return xmlResponse(errorXml(baseURL, verb, 'badVerb',
        'Catálogo indisponível no momento'), 503);
    }

    const handlers = {
      Identify: identify,
      ListMetadataFormats: listMetadataFormats,
      ListSets: listSets,
      ListIdentifiers: listItems,
      ListRecords: listItems,
      GetRecord: getRecord,
    };
    const handler = handlers[verb];
    if (!handler) {
      return xmlResponse(errorXml(baseURL, '', 'badVerb',
        'Verbo OAI-PMH ilegal ou ausente'));
    }
    return xmlResponse(handler(catalog, p, baseURL, verb));
  },
};

// ---------------------------------------------------------------- verbos

function identify(catalog, p, baseURL) {
  const r = catalog.repository;
  return wrap(baseURL, 'Identify', {}, `
  <Identify>
    <repositoryName>${esc(r.name)}</repositoryName>
    <baseURL>${esc(baseURL)}</baseURL>
    <protocolVersion>2.0</protocolVersion>
    <adminEmail>${esc(r.admin_email)}</adminEmail>
    <earliestDatestamp>${r.earliest}</earliestDatestamp>
    <deletedRecord>no</deletedRecord>
    <granularity>YYYY-MM-DD</granularity>
    <description>
      <oai-identifier xmlns="http://www.openarchives.org/OAI/2.0/oai-identifier"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai-identifier http://www.openarchives.org/OAI/2.0/oai-identifier.xsd">
        <scheme>oai</scheme>
        <repositoryIdentifier>anais.docomomobrasil.com</repositoryIdentifier>
        <delimiter>:</delimiter>
        <sampleIdentifier>oai:anais.docomomobrasil.com:${esc(catalog.records[0]?.id || 'sdbr01-001')}</sampleIdentifier>
      </oai-identifier>
    </description>
  </Identify>`);
}

function listMetadataFormats(catalog, p, baseURL) {
  const id = p.get('identifier');
  if (id && !catalog.records.some((r) => r.oai_id === id)) {
    return errorXml(baseURL, 'ListMetadataFormats', 'idDoesNotExist',
      'Identificador desconhecido');
  }
  return wrap(baseURL, 'ListMetadataFormats', {}, `
  <ListMetadataFormats>
    <metadataFormat>
      <metadataPrefix>oai_dc</metadataPrefix>
      <schema>http://www.openarchives.org/OAI/2.0/oai_dc.xsd</schema>
      <metadataNamespace>http://www.openarchives.org/OAI/2.0/oai_dc/</metadataNamespace>
    </metadataFormat>
  </ListMetadataFormats>`);
}

function listSets(catalog, p, baseURL) {
  const sets = catalog.sets.map((s) => `
    <set><setSpec>${esc(s.spec)}</setSpec><setName>${esc(s.name)}</setName></set>`).join('');
  return wrap(baseURL, 'ListSets', {}, `\n  <ListSets>${sets}\n  </ListSets>`);
}

function getRecord(catalog, p, baseURL) {
  const id = p.get('identifier');
  if (p.get('metadataPrefix') !== 'oai_dc') {
    return errorXml(baseURL, 'GetRecord', 'cannotDisseminateFormat',
      'Apenas oai_dc é suportado');
  }
  const rec = catalog.records.find((r) => r.oai_id === id);
  if (!rec) {
    return errorXml(baseURL, 'GetRecord', 'idDoesNotExist',
      'Identificador desconhecido');
  }
  return wrap(baseURL, 'GetRecord',
    { identifier: id, metadataPrefix: 'oai_dc' },
    `\n  <GetRecord>\n${recordXml(rec)}\n  </GetRecord>`);
}

function listItems(catalog, p, baseURL, verb) {
  // resumptionToken carrega os argumentos originais + offset
  let args = {
    metadataPrefix: p.get('metadataPrefix'),
    from: p.get('from'),
    until: p.get('until'),
    set: p.get('set'),
    offset: 0,
  };
  const token = p.get('resumptionToken');
  if (token) {
    try {
      args = JSON.parse(atob(token));
    } catch {
      return errorXml(baseURL, verb, 'badResumptionToken', 'Token inválido');
    }
  }
  if (args.metadataPrefix !== 'oai_dc') {
    return errorXml(baseURL, verb, 'cannotDisseminateFormat',
      'Apenas oai_dc é suportado');
  }
  if (args.set && !catalog.sets.some((s) => s.spec === args.set)) {
    return errorXml(baseURL, verb, 'noRecordsMatch', 'Set desconhecido');
  }

  const match = catalog.records.filter((r) =>
    (!args.from || r.datestamp >= args.from) &&
    (!args.until || r.datestamp <= args.until) &&
    (!args.set || r.sets.includes(args.set)));
  if (!match.length) {
    return errorXml(baseURL, verb, 'noRecordsMatch',
      'Nenhum registro para os critérios');
  }

  const page = match.slice(args.offset, args.offset + PAGE_SIZE);
  const nextOffset = args.offset + PAGE_SIZE;
  let resumption = '';
  if (nextOffset < match.length) {
    const next = btoa(JSON.stringify({ ...args, offset: nextOffset }));
    resumption = `\n    <resumptionToken completeListSize="${match.length}" cursor="${args.offset}">${next}</resumptionToken>`;
  } else if (args.offset > 0) {
    resumption = `\n    <resumptionToken completeListSize="${match.length}" cursor="${args.offset}"/>`;
  }

  const reqAttrs = token
    ? { resumptionToken: token }
    : Object.fromEntries(Object.entries(args)
        .filter(([k, v]) => v && k !== 'offset'));

  const body = verb === 'ListIdentifiers'
    ? page.map((r) => `\n${headerXml(r)}`).join('')
    : page.map((r) => `\n${recordXml(r)}`).join('');
  return wrap(baseURL, verb, reqAttrs,
    `\n  <${verb}>${body}${resumption}\n  </${verb}>`);
}

// ------------------------------------------------------------ formatação

function headerXml(rec, indent = '    ') {
  const sets = rec.sets.map((s) => `<setSpec>${esc(s)}</setSpec>`).join('');
  return `${indent}<header><identifier>${esc(rec.oai_id)}</identifier>` +
    `<datestamp>${rec.datestamp}</datestamp>${sets}</header>`;
}

function recordXml(rec) {
  return `    <record>\n${headerXml(rec, '      ')}\n      <metadata>\n` +
    `${rec.xml}\n      </metadata>\n    </record>`;
}

function wrap(baseURL, verb, reqAttrs, body) {
  const attrs = Object.entries(reqAttrs)
    .map(([k, v]) => ` ${k}="${esc(v)}"`).join('');
  return `<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
  <responseDate>${new Date().toISOString().replace(/\.\d+Z$/, 'Z')}</responseDate>
  <request verb="${esc(verb)}"${attrs}>${esc(baseURL)}</request>${body}
</OAI-PMH>`;
}

function errorXml(baseURL, verb, code, msg) {
  const v = verb ? ` verb="${esc(verb)}"` : '';
  return `<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">
  <responseDate>${new Date().toISOString().replace(/\.\d+Z$/, 'Z')}</responseDate>
  <request${v}>${esc(baseURL)}</request>
  <error code="${code}">${esc(msg)}</error>
</OAI-PMH>`;
}

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function xmlResponse(xml, status = 200) {
  return new Response(xml, {
    status,
    headers: { 'Content-Type': 'text/xml; charset=UTF-8' },
  });
}
