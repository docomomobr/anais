# Relatório de importação — OJS teste — 2026-02-11

## Estado atual

**Servidor**: docomomo.ojs.com.br/index.php/ojs (OJS 3.3.0.21)

### Importados com sucesso (13/21):

| Slug | Issue ID | Artigos | Esperado | Status |
|------|----------|---------|----------|--------|
| sdrj04 | 1 | 17 | 17 | OK |
| sdnne02 | 2 | 33 | 33 | OK |
| sdnne05 | 3 | 32 | 32 | OK |
| sdnne09 | 6 | 50 | 50 | OK |
| sdnne10 | 7 | 86 | 85 | OK |
| sdsp03 | 8 | 75 | 74 | OK |
| sdsp05 | 9 | 69 | 68 | OK |
| sdsp06 | 10 | 37 | 37 | OK |
| sdsp07 | 11 | 43 | 43 | OK |
| sdsul01 | 14 | 48 | 48 | OK |
| sdsul04 | 17 | 46 | 46 | OK |
| sdsul07 | 20 | 46 | 46 | OK |
| sdsul08 | 21 | 51 | 51 | OK |

### Faltam importar (8/21):

| Slug | Artigos | Tamanho XML | Tentativas |
|------|---------|-------------|------------|
| sdnne07 | 65 | 317 KB | 3+ (sempre vazio) |
| sdnne08 | 41 | 153 KB | 2+ (sempre vazio) |
| sdsp08 | 40 | 139 KB | 1 (4/40 parcial) |
| sdsp09 | 27 | 77 KB | 2+ (sempre vazio) |
| sdsul02 | 35 | — | Não tentado |
| sdsul03 | 39 | — | Não tentado |
| sdsul05 | 37 | — | Não tentado |
| sdsul06 | 24 | — | Não tentado |

## Limpeza realizada

- 8 issues vazias/duplicatas apagadas (IDs 58, 62, 63, 64, 65, 66, 67, 68)
- Incluía 6 duplicatas de sdsul06 (de tentativas anteriores)
- 3 novas issues vazias criadas e apagadas na tentativa de hoje (IDs 69, 70, 71)
- 1 issue parcial (sdsp08, 4/40) limpa corretamente

## Diagnóstico do bloqueio

O problema é consistente e reprodutível:

1. **Login**: funciona normalmente
2. **Upload do XML** (`uploadImportXML`): funciona, retorna `temporaryFileId`
3. **Import bounce** (`importBounce`): funciona (POST aceito)
4. **Execução do import** (GET `.../import?temporaryFileId=...`): **falha**
   - Resposta: corpo vazio (HTTP 200, mas sem conteúdo)
   - O servidor começa a processar mas a conexão é cortada

**Evidência do caso sdsp08**: 4 dos 40 artigos foram importados antes da resposta
ser cortada. Isso indica que:
- O XML é válido e o processamento começa corretamente
- O servidor processa alguns artigos mas o WAF/proxy corta a requisição
  após certo tempo ou volume de dados
- Não é um problema de formato, schema ou dados — é infraestrutura

**Causa provável**: O Cloudflare ou proxy reverso do provedor (OJS.com.br)
está cortando requisições GET de longa duração. O import de um XML com 65
artigos leva vários segundos de processamento PHP, e a conexão é encerrada
antes de completar.

## Possíveis soluções (para o provedor)

1. **Aumentar timeout no Cloudflare/proxy** para a rota do NativeImportExportPlugin
2. **Whitelist completa** do nosso IP para bypass de WAF (não só challenge bypass)
3. **Acesso SSH** para rodar via CLI: `php tools/importExport.php NativeImportExportPlugin import arquivo.xml ojs editor`
4. **Importar pela interface web manualmente** (mais lento mas pode funcionar)

## Próximos passos

- Enviar mensagem atualizada ao provedor explicando o problema
- Se o provedor não resolver, tentar importar os 8 faltantes pela interface web
- Alternativa: dividir os XMLs maiores em lotes menores (3-5 artigos cada)
  para reduzir o tempo de processamento por requisição
