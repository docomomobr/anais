
---
sdbr12-005:
    abstract: truncado no início
sdbr12-013:
    subtitle: 'notícias da “Nova São Luís” (1979)'
sdbr12-016:
    subtitle: 'itinerários, preceitos, argumentos e outros pontos no roteiro'
sdbr12-017:
    abstract: tem lixo no início
    abstract_en, keywords_en: na verdade são abstract_es e keywords_es
sdbr12-021:
    references: tem subtítulos de bibliografia e problema de split indevido em VIDESOTT...
sdbr12-023:
    abstract_en: tem lixo no início
sdbr12-043:
    references: tem lixo no princípio, dar uma revisada geral nelas com LLM
sdbr12-048:
    references: estão com hífens estranhos no início
sdbr12-056:
    references: tem subtítulo indevido na lista
sdbr12-058:
    references: tem lixo no final
sdbr12-064:
    title: 'Do Culto Moderno dos Monumentos ao culto dos monumentos modernos'
    references: falta extrair. por que não extraiu antes?
sdbr12-068:
    abstract: está com outros elementos misturados, como o abstract em ingles. 
    abstract_en: revisar também
sdbr12-072:
    abstract_en: tem lixo no início
---


instruções complementares:

1. Ao aplicar as correções, registrá-las progressivamente, e diagnosticar as causas dos problemas.
2. Verificar com LLM se tudo foi devidamente corrigido.
3. Tendo identificado as causas, ajustar o pipeline_revisao.md, os scripts e as instruções ao LLM para que problemas análogos sejam detectados pelo pipeline na fase de revisão, sem necessidade de intervenção humana.

depois de implementar tudo:

você é um engenheiro de software. revise o pipeline_revisao.md e seus scripts de modo a     
encontrar lints, erros de lógica, redundância, riscos de loops etc.                           


