-- D1 do worker de claims (anais Docomomo Brasil)
-- Criar via painel: Storage & Databases → D1 → create → console → colar.

CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER,          -- id no anais.db (tokens de campanha); NULL no fluxo orgânico
    slug TEXT NOT NULL,         -- slug da página de autor
    email TEXT NOT NULL,
    nome TEXT NOT NULL,         -- como a pessoa quer constar
    orcid TEXT,                 -- validado (formato + nome compatível na API)
    nome_orcid TEXT,            -- nome oficial do perfil ORCID no momento da validação
    obs TEXT,                   -- correções em texto livre
    processado INTEGER DEFAULT 0,  -- 0 = na fila; 1 = aplicado/decidido na curadoria
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS optouts (
    email TEXT PRIMARY KEY,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS solicitacoes (   -- rate limit do fluxo orgânico
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    slug TEXT NOT NULL,
    criado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_solic_email ON solicitacoes(email, criado_em);
