

---
sdbr13-024:
    references: tem diversos splits indevidos. revisar.
sdbr13-098:
    title: 'O arquiteto da diplomacia'
sdbr13-176:
    title: 'O papel da associação de críticos de arte no debate arquitetônico da década de 50'
    subtitle: 'uma análise a partir da imprensa brasileira'
sdbr13-123:
    abstract_es e keywords_es: constam no artigo. extrair e revisar.
sdbr13-038:
    title: 'Entre o contraste e a analogia,
o regional e o internacional'
    subtitle: 'diálogos entre ossatura independente e muro estrutural em intervenções sobre o construído, do Museu das Missões ao Museu do Pão'
sdbr13-045:
    keywords_en: está com lixo (título)
sdbr13-073:
    keywords_en: está com lixo (título)
sdbr13-081: 
    subtitle: 'do Grupo Arquitetura Nova (GAN) à contemporaneidade'
sdbr13-143:
    abstract: na verdade, esse é o abstract_es. o artigo não tem abstract em PT.
sdbr13-010:
    references: tem pelo menos um split errado (GAMELEIRA...)
---


Instruções complementares:

1. Ao aplicar as correções, registrá-las progressivamente, e diagnosticar as causas dos problemas.
2. Verificar com LLM se tudo foi devidamente corrigido.
3. Tendo identificado as causas, ajustar o pipeline_revisao.md, os scripts e as instruções ao LLM para que problemas análogos sejam detectados pelo pipeline na fase de revisão, sem necessidade de intervenção humana.

depois de implementar tudo:

você é um engenheiro de software. revise o pipeline_revisao.md e seus scripts de modo a     
encontrar lints, erros de lógica, redundância, riscos de loops etc.                           

- - -

Observação geral:

- Lembrar de colocar no pipeline de busca por orcid outras combinações de sobrenome da pessoa, após completar o nome todo.

por exemplo, se um autor se chama Fulano Sousa Silva Campos

pode ser que o orcid dele esteja como:

- Fulano Sousa Silva Campos
- Fulano Campos
- Fulano Sousa S. Campos
- Fulano S. Silva Campos
- Fulano S. S. Campos
- Fulano Sousa Silva
- Fulano Sousa
- Fulano Silva
- etc.

Isso porque não necessariamente as pessoas adotam sempre o último sobrenome como fixo, sobretudo em mulheres casadas que usam sobrenome do marido formalmente, mas que preferem seguir assinando com o nome de solteira.



