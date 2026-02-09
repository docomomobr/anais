# Devlog - Migração Docomomo para OJS

Registro de aprendizados e decisões técnicas durante a migração.

---

## 2026-01-27 - Seminários nacionais → Momopedia BR

Os dados dos seminários nacionais (`nacionais/sdbr01.yaml` a
`sdbr15.yaml`) foram copiados para o projeto Momopedia BR
(`~/Dropbox/docomomo/momopedia_br/data/nacionais/`). O projeto
Momopedia é a enciclopédia de arquitetos, obras e publicações do
movimento moderno brasileiro, derivada dos Anais. Os YAML de
metadados são insumo para o pipeline de extração de entidades e
geração de verbetes.

O original permanece aqui como registro do trabalho de migração.

---

## 2026-01-13 - Extração de Autores dos PDFs

### Problema
Os PDFs dos anais têm formatos variados de listagem de autores, dificultando a extração automática.

### Formatos Identificados

#### Formato 1: Maiúsculas com ponto-e-vírgula (sdnne07)
```
EVILLYN BIAZATTI DE ARAÚJO; RICARDO SILVEIRA CASTOR;
                  VICTÓRIA FERREIRA SOARES TAPAJÓS
```
- Autores separados por `;`
- Tudo em maiúsculas
- Pode quebrar em múltiplas linhas

#### Formato 2: Maiúsculas com números em parênteses (sdnne09)
```
BARRETO, EDUARDA (1); MILANI, VANESSA (2); MAZINE, THAIS (3)
```
ou
```
NATÁLIA MIRANDA VIEIRA-DE-ARAÚJO (1); JOSÉ CLEWTON DO
     NASCIMENTO (2); GEORGE ALEXANDRE FERREIRA DANTAS (3)
```
- Números indicam ordem de afiliação
- Pode quebrar em múltiplas linhas

#### Formato 3: SOBRENOME, Nome (sdnne07)
```
CHAVES, Celma (1); LIMA, Rodrigo Augusto de (2); VIGGIANO, Laís (3)
```
- Sobrenome em maiúsculas, seguido de vírgula
- Nome em capitalização normal
- Números em parênteses

### Soluções Implementadas

#### 1. Junção de linhas quebradas
```python
# Detecta linhas que terminam com preposição ou maiúsculas
# e junta com a próxima linha
if re.search(r'\b(DE|DA|DO|E|DOS|DAS|Y)\s*$', linha):
    linha = linha + ' ' + prox_linha
```

#### 2. Detecção de múltiplos formatos
```python
# Três casos de detecção
eh_linha_autores = False

# Caso 1: Com números (1), (2) e maiúsculas
if tem_autores_numerados and re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]', linha_limpa):
    eh_linha_autores = True

# Caso 2: Só maiúsculas com ponto-e-vírgula
elif ';' in linha and re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s;]+$', linha_limpa):
    eh_linha_autores = True

# Caso 3: SOBRENOME, Nome (n)
elif tem_autores_numerados and re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]+,\s*[A-Za-z]', linha.strip()):
    eh_linha_autores = True
```

#### 3. Tratamento de nomes com hífen
```python
# Regex deve incluir hífen para nomes como VIEIRA-DE-ARAÚJO
re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s\.\(\)0-9\-]+$', parte)
```

#### 4. Parsing de SOBRENOME, Nome
```python
# Detecta formato "SOBRENOME, Nome" (vírgula após sobrenome)
if ',' in nome_completo and re.match(r'^[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]+,', nome_completo):
    partes = nome_completo.split(',', 1)
    sobrenome = partes[0].strip()
    nome = partes[1].strip()
```

### Filtros para evitar títulos como autores
```python
palavras_titulo = [
    'ARQUITETURA', 'MODERNA', 'MODERNIST', 'ARCHITECTURE', 'MODERN',
    'RESIDENTIAL', 'RESIDENCIAL', 'BUILDING', 'HOUSE', 'CAMPUS',
    'PATRIMÔNIO', 'HERITAGE', 'URBANISMO', 'PROJETO', 'HISTORY',
    # ... mais palavras
]
```

### Resultados

| Seminário | Total | Extraídos | Taxa |
|-----------|-------|-----------|------|
| sdnne09   | 50    | 50        | 100% |
| sdnne07   | 65    | 57        | 88%  |

### Scripts Criados

- `extrair_autores_sdnne09.py` - Parser específico para formato do sdnne09
- `extrair_autores_sdnne07.py` - Parser genérico para múltiplos formatos
- `limpar_autores.py` - Remove títulos/graus dos nomes (Doutor Em..., Professor...)
- `limpar_yaml.py` - Remove caracteres "!" e textos extras

### Lições Aprendidas

1. **Não assumir formato único** - Cada seminário pode ter formatação diferente
2. **Juntar linhas antes de parsear** - Quebras de linha no PDF são imprevisíveis
3. **Incluir caracteres especiais nos regex** - Hífen, cedilha, acentos
4. **Filtrar palavras de título** - Em português, espanhol e inglês
5. **Tratar formato SOBRENOME, Nome** - Comum em publicações acadêmicas

---

## 2026-01-13 - Normalização de Nomes de Arquivos

### Problema
Nomes de arquivos PDF com acentos e caracteres especiais causam problemas.

### Solução
Script `normalizar_nomes.sh`:
- Remove acentos (á→a, ç→c)
- Remove caracteres especiais (' " etc)
- Trunca em 6 palavras
- Formato: `NNN_titulo_truncado.pdf`

---

## 2026-01-13 - Limpeza de YAMLs

### Problema
Caracteres "!" apareciam nos textos extraídos.

### Causa
O pdftotext interpreta alguns elementos gráficos como "!".

### Solução
```python
texto = re.sub(r'\s*!\s*', ' ', texto)
texto = re.sub(r'^!\s*', '', texto)
texto = re.sub(r'\s*!$', '', texto)
```

---

## 2026-01-13 - Revisão por IA dos YAMLs

### Problema
Scripts de extração automática geraram dados com problemas que passaram despercebidos:
- Fragmentos de títulos parseados como nomes de autores
- Bios com endereços postais e texto "E-mail:" no final
- Capitalização inconsistente de títulos e subtítulos
- Siglas em minúscula (bnb, sesi, xx, xxi)

### Abordagem
Revisão manual assistida por IA usando comandos `Grep` para encontrar padrões problemáticos e `Edit` para correções diretas. Scripts automáticos não conseguiram lidar com a variedade de casos.

### Problemas Encontrados e Corrigidos

#### 1. Autores falsos (fragmentos de título)
```yaml
# ANTES - fragmento de título parseado como autor
- givenname: Ceará
  familyname: The Padre Cícero Memorial In Juazeiro Do Norte

# DEPOIS - autor removido
```

Padrões de busca usados:
```bash
grep -E "familyname:.*\b(In|The|And|Of|To|For)\b"
grep -E "familyname:.*[A-Z]{4,}"
```

#### 2. Bios com lixo
```yaml
# ANTES
bio: 'Doutora em projetos arquitetônicos pela ETSAB/UPC. E-mail:'
bio: 'Graduando em Arquitetura e Urbanismo pela UFCG. Endereço Postal: Rua Getúlio Vargas'

# DEPOIS
bio: Doutora em projetos arquitetônicos pela ETSAB/UPC
bio: Graduando em Arquitetura e Urbanismo pela UFCG
```

Padrões de busca:
```bash
grep -E "bio:.*E-mail:"
grep -E "bio:.*\b(Rua|Av\.|Avenida|Endereço)\b"
```

#### 3. Bios incompletas
```yaml
# ANTES - informação sem contexto
bio: Arquitetura e Urbanismo

# DEPOIS - preferível null a dado incompleto
bio: null
```

#### 4. Capitalização de siglas e séculos
```yaml
# ANTES
title: Sede do bnb do Juazeiro do Norte
subtitle: produção arquitetônica feminina no século xx e xxi

# DEPOIS
title: Sede do BNB de Juazeiro do Norte, CE
subtitle: produção arquitetônica feminina no século XX e XXI
```

Padrões de busca:
```bash
grep -E "\b(bnb|xx|xix|xxi|sesi|senai)\b"
```

#### 5. Capitalização de subtítulos
```yaml
# ANTES - maiúsculas indevidas
subtitle: Estratégias Projetuais de Edifícios Escolares Paulistas

# DEPOIS - norma brasileira (subtítulo em minúscula)
subtitle: estratégias projetuais de edifícios escolares paulistas
```

### Resultados

| Seminário | Autores falsos | Bios corrigidas | Títulos ajustados |
|-----------|----------------|-----------------|-------------------|
| sdnne09   | 5 removidos    | 4               | ~25               |
| sdnne07   | 0              | 10              | 5                 |

### Lições Aprendidas

1. **Revisão por IA é mais eficaz** - Scripts não conseguem prever todos os casos edge
2. **Grep para encontrar, Edit para corrigir** - Buscar padrões, corrigir manualmente
3. **Dados incompletos = null** - Melhor não ter dado do que ter dado errado
4. **Siglas sempre maiúsculas** - BNB, SESI, XX, XXI
5. **Subtítulos começam minúscula** - Exceto nomes próprios e siglas

---

## Ordem de Processamento dos Seminários

Seminários ordenados por facilidade de extração de dados.

### Nível 1 - Dados estruturados (Even3)
| Seminário | Fonte | Formato | Status |
|-----------|-------|---------|--------|
| N/NE X - Campina Grande 2024 | Even3 | Metadados + PDFs estruturados | ⬜ Pendente |

### Nível 2 - PDF compilado com sumário
| Seminário | Fonte | Formato | Status |
|-----------|-------|---------|--------|
| Sul 7º - Porto Alegre 2022 | UFRGS PROPAR | PDF único com índice | ⬜ Pendente |
| SP 5º - 2017 | docomomobrasil | e-book com ISBN | ⬜ Pendente |
| SP 6º - 2018 | docomomobrasil | e-book com ISBN | ⬜ Pendente |

### Nível 3 - PDFs individuais organizados
| Seminário | Fonte | Formato | Status |
|-----------|-------|---------|--------|
| Sul 3º - 2010 | UFRGS PROPAR | Artigos individuais | ⬜ Pendente |
| Sul 4º - 2013 | UFRGS PROPAR | Artigos individuais | ⬜ Pendente |
| Sul 5º - 2016 | UFRGS PROPAR | Artigos individuais | ⬜ Pendente |
| Sul 2º - 2008 | docomomobrasil | PDF download | ⬜ Pendente |
| Sul 6º - 2019 | docomomobrasil | PDF download | ⬜ Pendente |
| Rio 1º - 2008 | docomomobrasil | PDF único | ⬜ Pendente |

### Nível 4 - Precisam tratamento manual
| Seminário | Fonte | Problema | Status |
|-----------|-------|----------|--------|
| N/NE 2º - Salvador 2008 | Google Drive | ZIP a extrair | ⬜ Pendente |
| N/NE 5º - Fortaleza 2014 | Docomomo CE | Disperso por eixos | ⬜ Pendente |
| N/NE 6º - Teresina 2016 | docomomobrasil | Só resumos | ⬜ Pendente |

### Já processados ✅
| Seminário | Artigos | Status |
|-----------|---------|--------|
| N/NE 7º - Manaus 2018 | 65 | ✅ Completo |
| N/NE 9º - São Luís 2022 | 50 | ✅ Completo |

### Não localizados (buscar com organizadores)
- N/NE 1º - Recife 2006 (UFPE/UNICAP)
- N/NE 3º - João Pessoa 2010 (UFPB)
- N/NE 4º - Natal 2012 (UFRN)
- N/NE 8º - Palmas 2021 (UFT)
- SP 8º - 2022 (UNIP)
- Rio 2º, 3º, 4º (Núcleo Rio)
- CE 1º, 2º (será incorporado ao N/NE)

---

## 2026-01-14 - Verificação da Migração dos Seminários Nacionais para OJS

### Contexto

Uma empresa foi contratada para migrar os anais dos seminários nacionais Docomomo Brasil para o sistema OJS (Open Journal Systems). A migração foi concluída.

### Histórico da Sessão

1. **Migração original**: Empresa terceirizada migrou anais dos seminários nacionais (1º ao 15º, exceto 12º) para o OJS em `publicacoes.docomomobrasil.com/anais`

2. **Reorganização do WordPress**: Para evitar links duplicados na web, decidiu-se:
   - Criar cópias das páginas de eventos como **Pages** do WordPress (sem listas de artigos)
   - Colocar os posts originais publicados como "Courses" (plugin Educaz) como **rascunho**
   - Arquivo HTML da listagem de rascunhos salvo em: `base/courses-rascunhos.html`

3. **Arquivos PDF**: Identificados os PDFs dos artigos que ainda ocupam espaço no WordPress. Usuário confirmou ação irreversível de exclusão futura.

4. **Indexação local do OJS**: Criados arquivos YAML espelhando todos os metadados do OJS:
   - Pasta: `/migracao/nacionais/`
   - Arquivos: `sdbr01.yaml` a `sdbr15.yaml` (exceto sdbr12)
   - Total: **1.325 artigos** em 14 edições

   | Seminário | Local | Ano | Artigos |
   |-----------|-------|-----|---------|
   | sdbr01 | Recife | 1995 | 7 |
   | sdbr02 | Salvador | 1997 | 24 |
   | sdbr03 | São Paulo | 1999 | 56 |
   | sdbr04 | Viçosa | 2001 | 79 |
   | sdbr05 | São Carlos | 2003 | 56 |
   | sdbr06 | Niterói | 2005 | 64 |
   | sdbr07 | Porto Alegre | 2007 | 62 |
   | sdbr08 | Rio de Janeiro | 2009 | 184 |
   | sdbr09 | Brasília | 2011 | 170 |
   | sdbr10 | Curitiba | 2013 | 118 |
   | sdbr11 | Recife | 2016 | 101 |
   | sdbr12 | Uberlândia | 2017 | ⏳ (não está no OJS) |
   | sdbr13 | Salvador | 2019 | 181 |
   | sdbr14 | Belém | 2021 | 122 |
   | sdbr15 | São Carlos/SP | 2023 | 101 |

5. **12º Seminário (Uberlândia, 2017)**: Não está disponível no OJS. Site original (www.12docomomobrasil.com) está fora do ar. Aguardando anais da organização (Maria Beatriz Camargo Cappello, Marta dos Santos Camisassa - PPGAU/FAUED/UFU). ISBN: 978-85-64554-03-0.

6. **Próximo passo**: Acessar os Courses em rascunho no WordPress para extrair listas originais de artigos e comparar com os YAMLs do OJS, verificando se todos os artigos foram migrados corretamente.

### Credenciais Disponíveis (em CLAUDE.md)

- WordPress Admin: `admindocomomo` / `***`
- WordPress REST API: Application Password `***`
- FTP: `ftp.app.docomomobrasil.com` / `app` / `***`
- **Nota**: O tipo "course" (Educaz) NÃO tem endpoint REST API

### IDs dos Courses (Rascunhos)

Extraídos de `base/courses-rascunhos.html`:

| Seminário | Post ID | Slug |
|-----------|---------|------|
| 1º Salvador 1995 | 3870 | 1-seminario-docomomo-brasil-salvador |
| 2º Salvador 1997 | 3673 | 2-seminario-docomomo-brasil-salvador |
| 3º São Paulo 1999 | 1787 | 3-seminario-docomomo-brasil-sao-paulo |
| 4º Viçosa 2001 | 1786 | 4-seminario-docomomo-brasil-vicosa |
| 5º São Carlos 2003 | 1785 | 5-seminario-docomomo-brasil-sao-carlos |
| 6º Niterói 2005 | 1784 | 6-seminario-docomomo-brasil-niteroi |
| 7º Porto Alegre 2007 | 1783 | 7-seminario-docomomo-brasil-porto-alegre |
| 8º Rio de Janeiro 2009 | 1782 | 8-seminario-docomomo-brasil-rio-de-janeiro |
| 9º Brasília 2011 | 1781 | 9-seminario-docomomo-brasil-brasilia |
| 10º Curitiba 2013 | 1613 | 10o-seminario-docomomo-brasil |
| 11º Recife 2016 | 1615 | 11o-seminario-docomomo-brasil |
| 12º Uberlândia 2017 | 3020 | 12o-seminario-docomomo-brasil-uberlandia |
| 13º Salvador 2019 | 3676 | 13o-seminario-docomomo-brasil-salvador |
| 14º Belém 2021 | 4376 | 14o-seminario-docomomo-brasil-belem |

---

## 2026-01-15 - Exclusão de PDFs dos Seminários Nacionais do WordPress

### Contexto

Com a migração dos anais dos seminários nacionais para o OJS concluída, os PDFs hospedados no WordPress tornaram-se redundantes. Decidiu-se excluí-los para liberar espaço no servidor.

### Método de Acesso aos PDFs

Os PDFs dos artigos estavam vinculados aos Courses (plugin Educaz) de forma especial:
- **NÃO** estavam como media vinculada (parent) ao post
- Estavam sendo renderizados pelo plugin Educaz no frontend

**Para acessar os PDFs de Courses em rascunho:**

```bash
# Passo 1: Login via wp-login.php (HTTP Basic Auth NÃO funciona para previews)
curl -s -c /tmp/wp_cookies.txt -b /tmp/wp_cookies.txt \
  -d "log=admindocomomo&pwd=***&wp-submit=Log+In&testcookie=1" \
  -d "redirect_to=https%3A%2F%2Fdocomomobrasil.com%2Fwp-admin%2F" \
  "https://docomomobrasil.com/wp-login.php" -L > /dev/null

# Passo 2: Acessar preview usando cookies de sessão
curl -s -b /tmp/wp_cookies.txt \
  "https://docomomobrasil.com/?post_type=course&p={POST_ID}&preview=true" \
  | grep -oE 'href="[^"]*\.pdf"' | sed 's/href="//;s/"$//'
```

**Nota:** Este método foi documentado em CLAUDE.md para uso futuro com seminários regionais.

### Processo de Extração

1. **Login no WordPress** via wp-login.php com cookies de sessão
2. **Acesso ao preview** de cada um dos 14 Courses (seminários nacionais)
3. **Extração dos links** de PDFs do HTML renderizado
4. **Consolidação** em lista única

### Resultado da Extração

| Seminário | Post ID | PDFs |
|-----------|---------|------|
| 1º Salvador 1995 | 3870 | 1 (livro) |
| 2º Salvador 1997 | 3673 | 1 (livro) |
| 3º São Paulo 1999 | 1787 | ~40 |
| 4º Viçosa 2001 | 1786 | ~80 |
| 5º São Carlos 2003 | 1785 | ~55 |
| 6º Niterói 2005 | 1784 | ~65 |
| 7º Porto Alegre 2007 | 1783 | ~60 |
| 8º Rio de Janeiro 2009 | 1782 | ~185 |
| 9º Brasília 2011 | 1781 | ~170 |
| 10º Curitiba 2013 | 1613 | ~55 (CON_*.pdf) |
| 11º Recife 2016 | 1615 | ~75 (OBR_*.pdf) |
| 12º Uberlândia 2017 | 3020 | 0 (sem anais) |
| 13º Salvador 2019 | 3676 | ~150 |
| 14º Belém 2021 | 4376 | ~122 |
| **Total** | | **1039 PDFs únicos** |

### Análise Pré-Exclusão

Antes de excluir, verificou-se:

1. **Quantos estão na biblioteca de mídia:** 1017
2. **Quantos só existem como arquivos:** 22 (PDFs com acentos no nome)
3. **Tamanho estimado:** ~522 MB (média de 514 KB por arquivo)

### Processo de Exclusão

#### Via API WordPress (1017 PDFs)

```bash
# Buscar IDs dos PDFs na biblioteca
curl -s -u "admindocomomo:psXb..." \
  "https://docomomobrasil.com/wp-json/wp/v2/media?per_page=100&mime_type=application/pdf&page={N}"

# Deletar cada PDF
curl -s -X DELETE -u "admindocomomo:psXb..." \
  "https://docomomobrasil.com/wp-json/wp/v2/media/{ID}?force=true"
```

**Resultado:**
- 1ª rodada: 930 deletados, 87 falhas (rate limit)
- 2ª rodada: 87 deletados, 0 falhas
- **Total via API: 1017 deletados**

#### PDFs Órfãos (22 arquivos)

Os 22 PDFs que só existiam como arquivos (não na biblioteca de mídia) não puderam ser deletados:
- Não há acesso FTP ao servidor principal (docomomobrasil.com)
- São arquivos com acentos no nome (codificados como %C3%...)
- Origem: 1 do 2º Seminário, 21 do 14º Seminário Belém
- Tamanho estimado: ~11 MB

**Status:** Pendente (requer acesso via painel da hospedagem ou FTP)

### Arquivos Gerados

- `pdfs_seminarios_nacionais.txt` - Lista completa dos 1039 PDFs (paths relativos)
- `/tmp/ids_to_delete.txt` - IDs da biblioteca de mídia
- `/tmp/so_no_servidor.txt` - 22 PDFs órfãos pendentes

### Espaço Liberado

| Categoria | Arquivos | Tamanho |
|-----------|----------|---------|
| Deletados via API | 1017 | ~511 MB |
| Pendentes (órfãos) | 22 | ~11 MB |
| **Total** | 1039 | **~522 MB** |

### Lições Aprendidas

1. **HTTP Basic Auth não funciona para previews** - Requer login via wp-login.php com cookies
2. **Plugin Educaz armazena PDFs de forma especial** - Não como media vinculada ao post
3. **Rate limit da API** - Deletar em lotes com pausa entre requisições
4. **PDFs com acentos** - Podem não estar na biblioteca de mídia (só arquivos)
5. **Sempre verificar antes de deletar** - Confirmar que são dos seminários corretos

---

## Pendências

### Exclusão de 22 PDFs órfãos do servidor

**Status:** ⏳ Pendente (requer acesso ao painel da hospedagem ou FTP)

**Problema:**
- 22 PDFs dos seminários nacionais existem apenas como arquivos no servidor
- Não estão na biblioteca de mídia do WordPress (não podem ser deletados via API)
- São arquivos com acentos no nome (codificados como %C3%...)

**Origem:**
- 1 PDF do 2º Seminário Salvador 1997 (2020/04)
- 21 PDFs do 14º Seminário Belém 2021 (2021/12)

**Tamanho estimado:** ~11 MB

**Lista de arquivos:** `pdfs_orfaos_pendentes.txt`

**Solução:**
1. Acessar painel da hospedagem (cPanel/Plesk) ou obter credenciais FTP do servidor principal
2. Navegar até `/wp-content/uploads/2020/04/` e `/wp-content/uploads/2021/12/`
3. Deletar os 22 arquivos listados

---

### Correção de títulos e subtítulos no OJS

**Status:** ⏳ Pendente (aguardando acesso de Journal Manager)

**Problema:**
- A maioria dos títulos no OJS está em CAIXA ALTA
- Subtítulos não estão separados (concatenados com `:` no título)

**Exemplo:**
```
OJS atual:   "ARQUITETURAS DE ASSISTÊNCIA PÚBLICA E SAÚDE EM SALVADOR..."
YAML correto: title: "Arquiteturas de Assistência Pública e Saúde em Salvador..."

OJS atual:   "O Quartel General do Exército: do projeto de Niemeyer..."
YAML correto: title: "O Quartel General do Exército"
              subtitle: "do projeto de Niemeyer à dinâmica política de 2023"
```

**Situação dos dados:**
- YAMLs locais (sdbr01-sdbr15) já estão normalizados com títulos corretos
- Exceção: sdbr12 está vazio (aguardando anais da organização)

**Solução proposta:**
1. Obter acesso de Journal Manager no OJS
2. Ativar Native XML Plugin
3. Exportar XML de cada issue
4. Cruzar com YAMLs e gerar XML corrigido
5. Reimportar no OJS

**Custo estimado:** Mínimo (dados já levantados, só cruzamento)

---

*Este arquivo é atualizado conforme novos aprendizados surgem.*
