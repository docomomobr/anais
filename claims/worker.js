/**
 * Worker de claims dos Anais Docomomo Brasil — auto-identificação de autores.
 *
 * Fluxos:
 *  1. Campanha: e-mail leva link mágico GET /c/{token} (token = HMAC
 *     assinado com author_id+email — stateless, gerado pela mala direta).
 *     O formulário POST /c/{token} valida ORCID (formato + nome compatível
 *     na API pública) e grava o claim no D1. NADA escreve no anais.db:
 *     a fila de claims é revisada por humanos.
 *  2. Orgânico: botão "Este sou eu" na página de autor → POST /solicitar
 *     (email + slug) → e-mail com link mágico via Brevo.
 *  3. Opt-out: GET /o/{token} grava descadastro em 1 clique.
 *
 * Bindings (painel Cloudflare):
 *  - D1: DB (schema em claims/schema.sql)
 *  - Secrets: CLAIM_SECRET (HMAC), BREVO_API_KEY
 *  - Vars: EMAIL_FROM (ex.: "Docomomo Brasil <contato@docomomobrasil.com>")
 */

const SITE = 'https://anais.docomomobrasil.com';

// ─────────────────────────────── token HMAC (stateless)

async function hmac(secret, msg) {
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(secret),
    { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(msg));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, '0')).join('').slice(0, 32);
}

function b64url(s) {
  return btoa(unescape(encodeURIComponent(s))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function unb64url(s) {
  return decodeURIComponent(escape(atob(s.replace(/-/g, '+').replace(/_/g, '/'))));
}

export async function gerarToken(secret, payload) { // payload: {a: author_id, e: email, s: slug}
  const corpo = b64url(JSON.stringify(payload));
  return `${corpo}.${await hmac(secret, corpo)}`;
}

async function lerToken(secret, token) {
  const [corpo, sig] = (token || '').split('.');
  if (!corpo || !sig) return null;
  if (await hmac(secret, corpo) !== sig) return null;
  try { return JSON.parse(unb64url(corpo)); } catch { return null; }
}

// ─────────────────────────────── validação ORCID

const ORCID_RE = /^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$/;

function tokens(s) {
  return new Set((s || '').normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z ]/g, ' ').split(/\s+/).filter(Boolean));
}

async function validarOrcid(orcid, nome) {
  if (!ORCID_RE.test(orcid)) return { ok: false, motivo: 'formato inválido' };
  const r = await fetch(`https://pub.orcid.org/v3.0/${orcid}/personal-details`,
                        { headers: { Accept: 'application/json' } });
  if (!r.ok) return { ok: false, motivo: 'ORCID não encontrado' };
  const d = await r.json();
  const n = d.name || {};
  const oficial = `${n['given-names']?.value || ''} ${n['family-name']?.value || ''}`;
  const a = tokens(nome), b = tokens(oficial);
  const inter = [...a].filter((t) => b.has(t)).length;
  if (b.size && inter < 1) {
    return { ok: false, motivo: `o perfil ORCID pertence a "${oficial.trim()}" — confira o número` };
  }
  return { ok: true, nome_orcid: oficial.trim() };
}

// ─────────────────────────────── páginas HTML

function pagina(titulo, corpo) {
  return new Response(`<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>${titulo} — Anais Docomomo Brasil</title>
<style>body{font-family:system-ui,sans-serif;max-width:34rem;margin:8vh auto;padding:0 1rem;line-height:1.55;color:#222}
label{display:block;margin:1rem 0 .2rem;font-weight:600}input,textarea{width:100%;padding:.5rem;border:1px solid #bbb;border-radius:4px;font:inherit}
button{margin-top:1.2rem;padding:.6rem 1.4rem;background:#1a5276;color:#fff;border:0;border-radius:4px;font:inherit;cursor:pointer}
.erro{background:#fdecea;border-left:3px solid #c0392b;padding:.6rem .8rem}
.ok{background:#eafaf1;border-left:3px solid #1e8449;padding:.6rem .8rem}
small{color:#666}</style></head><body>
<p><a href="${SITE}">← anais.docomomobrasil.com</a></p>
${corpo}
</body></html>`, { headers: { 'Content-Type': 'text/html; charset=UTF-8' } });
}

function formulario(payload, token, msg = '') {
  return pagina('Conferência de dados de autor', `
<h1>Conferência de dados</h1>
${msg}
<p>Você está identificado(a) pelo e-mail <strong>${payload.e}</strong>
para a página de autor <a href="${SITE}/autores/${payload.s}/">${payload.s}</a>.</p>
<form method="post">
  <label for="nome">Nome como deseja constar nos anais</label>
  <input id="nome" name="nome" required maxlength="120">
  <label for="orcid">ORCID (opcional — formato 0000-0000-0000-0000)</label>
  <input id="orcid" name="orcid" pattern="\\d{4}-\\d{4}-\\d{4}-\\d{3}[\\dX]" placeholder="deixe vazio se não tiver">
  <label for="obs">Correções ou observações (trabalhos faltando, grafia, afiliação…)</label>
  <textarea id="obs" name="obs" rows="4" maxlength="2000"></textarea>
  <button>Enviar conferência</button>
  <p><small>Sua resposta entra em fila de revisão editorial — nada é
  alterado automaticamente. Dados usados apenas para a curadoria dos anais.</small></p>
</form>`);
}

// ─────────────────────────────── handler

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const rota = url.pathname;

    // claim: formulário e submissão
    let m = rota.match(/^\/c\/([^/]+)$/);
    if (m) {
      const payload = await lerToken(env.CLAIM_SECRET, m[1]);
      if (!payload) return pagina('Link inválido', '<h1>Link inválido ou expirado</h1><p>Solicite um novo pelo botão "Este sou eu" na sua página de autor.</p>');
      if (request.method === 'GET') return formulario(payload, m[1]);
      if (request.method === 'POST') {
        const f = await request.formData();
        const nome = (f.get('nome') || '').trim();
        const orcid = (f.get('orcid') || '').trim();
        const obs = (f.get('obs') || '').trim();
        if (!nome) return formulario(payload, m[1], '<p class="erro">Informe o nome.</p>');
        let nome_orcid = '';
        if (orcid) {
          const v = await validarOrcid(orcid, nome);
          if (!v.ok) return formulario(payload, m[1], `<p class="erro">ORCID: ${v.motivo}.</p>`);
          nome_orcid = v.nome_orcid;
        }
        await env.DB.prepare(
          `INSERT INTO claims (author_id, slug, email, nome, orcid, nome_orcid, obs, criado_em)
           VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))`)
          .bind(payload.a || null, payload.s, payload.e, nome, orcid, nome_orcid, obs).run();
        return pagina('Recebido', '<h1 class="ok">Recebido — obrigado!</h1><p>Sua conferência entrou na fila de revisão editorial dos anais. Se houver mudanças na sua página, elas aparecem na próxima atualização do site.</p>');
      }
    }

    // opt-out de 1 clique
    m = rota.match(/^\/o\/([^/]+)$/);
    if (m) {
      const payload = await lerToken(env.CLAIM_SECRET, m[1]);
      if (!payload) return pagina('Link inválido', '<h1>Link inválido</h1>');
      await env.DB.prepare(
        `INSERT OR IGNORE INTO optouts (email, criado_em) VALUES (?, datetime('now'))`)
        .bind(payload.e).run();
      return pagina('Descadastrado', '<h1 class="ok">Pronto</h1><p>Você não receberá outras mensagens sobre os anais.</p>');
    }

    // fluxo orgânico: botão "Este sou eu" na página de autor
    if (rota === '/solicitar' && request.method === 'POST') {
      const f = await request.formData();
      const email = (f.get('email') || '').trim().toLowerCase();
      const slug = (f.get('slug') || '').trim();
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) || !/^[a-z0-9-]+$/.test(slug)) {
        return pagina('Dados inválidos', '<h1 class="erro">Dados inválidos</h1>');
      }
      // rate limit simples: 3 pedidos/e-mail/dia
      const { cnt } = await env.DB.prepare(
        `SELECT COUNT(*) cnt FROM solicitacoes WHERE email = ? AND criado_em > datetime('now','-1 day')`)
        .bind(email).first();
      if (cnt >= 3) return pagina('Limite', '<h1>Limite diário atingido</h1><p>Tente novamente amanhã.</p>');
      await env.DB.prepare(
        `INSERT INTO solicitacoes (email, slug, criado_em) VALUES (?, ?, datetime('now'))`)
        .bind(email, slug).run();
      const token = await gerarToken(env.CLAIM_SECRET, { e: email, s: slug });
      await fetch('https://api.brevo.com/v3/smtp/email', {
        method: 'POST',
        headers: { 'api-key': env.BREVO_API_KEY, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sender: parseFrom(env.EMAIL_FROM),
          to: [{ email }],
          subject: 'Anais Docomomo Brasil — link de conferência da página de autor',
          htmlContent: `<p>Você (ou alguém) pediu o link de conferência da página
            <a href="${SITE}/autores/${slug}/">${slug}</a> nos Anais Docomomo Brasil.</p>
            <p><a href="${url.origin}/c/${token}">Abrir o formulário de conferência</a></p>
            <p>Se não foi você, ignore esta mensagem.</p>`,
        }),
      });
      return pagina('Verifique seu e-mail', '<h1 class="ok">Enviado</h1><p>Confira sua caixa de entrada — o link de conferência chega em instantes.</p>');
    }

    return pagina('Anais Docomomo Brasil', '<h1>Conferência de dados de autor</h1><p>Use o botão "Este sou eu" na sua página de autor em <a href="' + SITE + '/autores/">anais.docomomobrasil.com/autores</a>.</p>');
  },
};

function parseFrom(s) {
  const m = (s || '').match(/^(.*)<([^>]+)>$/);
  return m ? { name: m[1].trim(), email: m[2].trim() } : { name: 'Docomomo Brasil', email: s };
}
