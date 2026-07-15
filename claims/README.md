# Worker de claims — auto-identificação de autores (Anais Docomomo Brasil)

Formulário de conferência de dados de autor (nome, ORCID, correções),
alimentado por links mágicos assinados (HMAC). **Nada escreve no
anais.db**: os claims caem numa fila (D1) revisada na curadoria.

- `worker.js` — 3 fluxos: `/c/{token}` (formulário de conferência),
  `/o/{token}` (opt-out 1 clique), `POST /solicitar` (botão "Este sou
  eu" → e-mail com link via Brevo). ORCID validado em formato **e**
  identidade (nome do perfil na API pública).
- `schema.sql` — tabelas D1 (claims, optouts, solicitacoes).
- `test-worker.mjs` — 10 casos: `node claims/test-worker.mjs`.

## Deploy (conta Cloudflare tesouraria) — passo a passo

1. **Criar o worker**: Workers & Pages → Create → **Worker** (igual ao
   `oai-anais`) → nome `claims-anais` → Deploy → **Edit code** → colar
   `worker.js` → Deploy.

2. **Criar o banco D1**: menu **Storage & Databases → D1 → Create
   database** → nome `claims-anais` → abrir o **Console** do banco →
   colar o conteúdo de `schema.sql` → Execute.

3. **Vincular o banco ao worker**: no worker `claims-anais` →
   **Settings → Bindings → Add → D1 database** → Variable name: `DB`
   → Database: `claims-anais` → Save.

4. **Segredos e variáveis**: no worker → **Settings → Variables and
   Secrets**:
   - Secret `CLAIM_SECRET`: gerar com `openssl rand -hex 32` no
     terminal (guardar também no `.env` do repo anais como
     `CLAIM_SECRET=...` — a mala direta assina os tokens com ele);
   - Secret `BREVO_API_KEY`: copiar do `.env` do Pilotis;
   - Variable `EMAIL_FROM`: `Docomomo Brasil <contato@docomomobrasil.com>`.

5. **Testar**: abrir `https://claims-anais.<conta>.workers.dev/` —
   deve mostrar a página institucional. Gerar um token de teste no
   repo anais e abrir `/c/{token}`.

## Integrações que dependem do worker no ar

- **Mala direta da campanha** (`scripts/gerar_campanha.py`, a criar):
  gera `{link_claim}`/`{link_optout}` por autor assinando com o MESMO
  `CLAIM_SECRET`.
- **Botão "Este sou eu"** nas páginas de autor (template Hugo):
  formulário POST para `https://<worker>/solicitar` com o slug.

## Fila de curadoria

Claims chegam em `claims` (D1) com `processado = 0`. Consulta pelo
console D1 ou `wrangler d1 execute`. Aplicação no anais.db é sempre
manual/assistida (mesmo fluxo da auditoria ORCID de 2026-07-15).
