Prezado,

Obrigado pela liberação dos IPs no Cloudflare. As requisições chegam ao servidor e conseguimos importar 13 dos 21 seminários com sucesso. Porém os 8 restantes falham sistematicamente.

## O problema

O upload do XML funciona normalmente (retorna `temporaryFileId`), mas a etapa de processamento (GET `.../NativeImportExportPlugin/import?temporaryFileId=...`) retorna **resposta vazia** — o corpo do HTTP 200 vem sem conteúdo.

## Evidência de que é timeout/WAF

Em uma tentativa com um arquivo de 40 artigos (sdsp08), **4 dos 40 artigos foram importados** antes da resposta ser cortada. Isso confirma que:
- O XML é válido e o OJS começa a processá-lo corretamente
- A conexão é encerrada no meio do processamento
- Não é erro no PHP nem no XML — o processamento está sendo interrompido externamente

Os 13 seminários importados com sucesso foram feitos em sessões anteriores, possivelmente antes de alguma mudança na configuração do Cloudflare/proxy.

## O que precisamos

Uma das seguintes soluções resolveria:

1. **Aumentar o timeout** do Cloudflare/proxy para a rota `/management/importexport/` (o processamento de XMLs com 40-65 artigos leva até 30-60 segundos)
2. **Bypass completo de WAF** para o nosso IP `189.6.108.8` (não só bypass do challenge, mas também bypass de regras que cortam requisições longas)
3. **Acesso SSH** temporário para rodar a importação via CLI (`php tools/importExport.php`), que não passa pelo Cloudflare

## Sobre as issues vazias

As issues vazias criadas pelas tentativas falhadas (IDs 58, 62-68) já foram limpas por nós via API. Não há mais lixo no banco.

## Estado atual

- **13/21 seminários importados** (633 artigos no total)
- **8 faltam**: sdnne07 (65 arts), sdnne08 (41), sdsp08 (40), sdsp09 (27), sdsul02 (35), sdsul03 (39), sdsul05 (37), sdsul06 (24)
- Todos os XMLs estão prontos e validados — só falta a importação funcionar

Obrigado!

---

## Atualização (2026-02-11)

Verificamos: o IP não mudou (189.6.108.8). O Cloudflare confirma que não bloqueou nenhuma requisição desse IP. Não há logs de erro no Apache/PHP.

Isso sugere que o problema pode ser no PHP e não no Cloudflare. Possibilidades:

1. **`max_execution_time` do PHP** — se estiver no padrão (30s), o PHP morre silenciosamente ao processar XMLs com muitos artigos, sem gerar log de erro
2. **`memory_limit` do PHP** — o processamento de XML carrega tudo em memória; se o limite for baixo (128M), pode dar OOM sem log visível
3. **Log do PHP-FPM** — se o servidor usa PHP-FPM, os erros podem estar em `/var/log/php-fpm/` ou `/var/log/php*/` em vez do log do Apache

Seria possível verificar os valores atuais do PHP com este comando?

```
php -r "echo 'max_execution_time: '.ini_get('max_execution_time').PHP_EOL.'memory_limit: '.ini_get('memory_limit').PHP_EOL.'error_log: '.ini_get('error_log').PHP_EOL;"
```

Se `max_execution_time` estiver em 30, aumentar para 300 (5 minutos) resolveria o problema. A diretiva fica no `php.ini` ou pode ser configurada por virtual host no Apache.

Enquanto isso, estamos tentando contornar dividindo os XMLs em lotes menores (5 artigos por arquivo) para que o processamento termine mais rápido.
