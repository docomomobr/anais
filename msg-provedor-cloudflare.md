Prezado,

Para que possamos testar a importação automática de artigos no ambiente de teste (docomomo.ojs.com.br), precisamos que o nosso IP seja liberado no Cloudflare.

O ambiente está protegido por um challenge do Cloudflare que bloqueia requisições POST feitas via script (curl/API). Precisamos dessas requisições para:

1. Login via API (`/login/signIn`)
2. Upload de XMLs via Native XML Plugin (`/management/importexport/plugin/NativeImportExportPlugin`)
3. Operações administrativas via API REST (`/api/v1/`)

**IPs para liberar:**

- IPv4: `189.6.108.8`
- IPv6: `2804:14c:6585:6b2d::/64`

Basta adicionar uma regra no Cloudflare (Security > WAF > Tools) do tipo "IP Access Rules" com ação "Allow" para esses endereços.

Obrigado!
