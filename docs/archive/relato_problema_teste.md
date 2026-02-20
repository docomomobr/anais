# Relato de problema — ambiente de teste OJS

**Data:** 2026-02-11
**Ambiente:** docomomo.ojs.com.br (OJS 3.3.0.21)
**IP de origem:** 189.6.108.8 (IPv4) / 2804:14c:6585:6b2d::/64 (IPv6)

## Resumo

A importação de artigos via Native XML Plugin funciona parcialmente: o login e o upload do arquivo XML são bem-sucedidos, mas a etapa de processamento da importação retorna resposta vazia ou a sessão expira durante o processamento no servidor.

O mesmo procedimento (mesmos scripts, mesma estrutura de XML) funciona sem problemas no ambiente de produção (publicacoes.docomomobrasil.com).

## Procedimento utilizado

A importação via web segue 4 passos:

1. **Login** — `POST /login/signIn` com username/password → OK (HTTP 200, cookie de sessão retornado)
2. **Upload do XML** — `POST /management/importexport/plugin/NativeImportExportPlugin/uploadImportXML` com o arquivo XML → OK (retorna `temporaryFileId`)
3. **Bounce** — `POST /management/importexport/plugin/NativeImportExportPlugin/importBounce` com o `temporaryFileId` → OK (HTTP 200)
4. **Import (processamento)** — `GET /management/importexport/plugin/NativeImportExportPlugin/import?temporaryFileId=XX&csrfToken=YY` → **FALHA: resposta vazia (0 bytes)**

## Detalhes do problema

- Os passos 1-3 sempre funcionam. O passo 4 retorna consistentemente uma resposta vazia.
- O passo 4 é o que dispara o processamento do XML pelo servidor (parsing do XML, criação de issue, inserção dos artigos no banco). É a etapa que mais consome tempo de processamento.
- Os arquivos XML são pequenos: entre 66 KB e 506 KB (contêm apenas metadados, sem PDFs embutidos).
- Mesmo o menor XML (sdsul06.xml, 81 KB, 24 artigos) falha na etapa 4.
- O resultado é que o OJS cria a issue no banco mas não insere os artigos, deixando uma issue vazia.

## Importações que funcionaram (antes do problema começar)

13 dos 21 seminários foram importados com sucesso no ambiente de teste, totalizando 687 artigos. As importações funcionaram com intervalos de 30 segundos entre elas. Após a 13ª importação consecutiva, todas as tentativas subsequentes passaram a falhar.

| Seminário | Artigos | Status |
|-----------|---------|--------|
| sdrj04 | 17 | OK |
| sdnne02 | 33 | OK |
| sdnne05 | 32 | OK |
| sdnne09 | 50 | OK |
| sdnne10 | 86 | OK |
| sdsp03 | 75 | OK |
| sdsp05 | 69 | OK |
| sdsp06 | 37 | OK |
| sdsp07 | 43 | OK |
| sdsul01 | 48 | OK |
| sdsul04 | 46 | OK |
| sdsul07 | 46 | OK |
| sdsul08 | 51 | OK |

## Importações que faltam (todas falhando)

| Seminário | Artigos | Tamanho XML |
|-----------|---------|-------------|
| sdnne07 | 65 | 268 KB |
| sdnne08 | 41 | 223 KB |
| sdsp08 | 43 | 178 KB |
| sdsp09 | 48 | 231 KB |
| sdsul02 | 40 | 144 KB |
| sdsul03 | 20 | 88 KB |
| sdsul05 | 56 | 195 KB |
| sdsul06 | 24 | 81 KB |

## Comparação com produção

No ambiente de produção (publicacoes.docomomobrasil.com, servidor diferente), importamos 82 arquivos XML do 12º Seminário Docomomo Brasil (1 artigo por XML, cada XML com PDF embutido em base64, arquivos de 1-10 MB cada) sem nenhum problema de sessão ou timeout.

## Hipóteses

1. **Timeout de sessão PHP muito curto** — o `session.gc_maxlifetime` do PHP pode estar configurado com valor muito baixo, fazendo a sessão expirar durante o processamento do XML
2. **Timeout de execução PHP** — o `max_execution_time` pode ser insuficiente para o processamento (mesmo que os XMLs sejam pequenos, o OJS faz muitas operações de banco por artigo)
3. **Cloudflare/WAF** — alguma regra de segurança pode estar interrompendo requisições longas ou bloqueando o passo 4 especificamente
4. **Limite de requisições** — rate limiting ativo após N operações na mesma sessão

## O que precisamos

1. Verificar/aumentar os valores de:
   - `session.gc_maxlifetime` (recomendado: 7200 ou mais)
   - `max_execution_time` (recomendado: 300 ou mais)
   - `max_input_time` (recomendado: 300)
2. Verificar se há regra de WAF/Cloudflare que esteja interferindo no processamento de requisições longas
3. Verificar logs de erro do PHP/Apache/Nginx no momento da requisição falhada (deverá mostrar o que está acontecendo no servidor quando a resposta volta vazia)
