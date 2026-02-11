# **Relatório de Investigação Avançada: Aplicação de Reconhecimento de Entidades Nomeadas (NER) e Normalização Semântica para Correção de Metadados em Arquitetura e Urbanismo**

## **1\. Introdução à Crise da Qualidade de Metadados em Repositórios Científicos**

A integridade dos metadados bibliográficos constitui a espinha dorsal da infraestrutura global de conhecimento. Em um ecossistema acadêmico cada vez mais digitalizado e interconectado, a precisão dos títulos e subtítulos de publicações não é meramente uma questão de rigor editorial, mas um requisito fundamental para a descoberta, indexação e interoperabilidade de dados.1 No entanto, repositórios institucionais e sistemas de gestão de revistas, como o *Open Journal Systems* (OJS), enfrentam uma crise silenciosa de qualidade de dados. Erros tipográficos, inconsistências de capitalização, variações linguísticas e ambiguidades semânticas degradam a capacidade de recuperação da informação, resultando em "silos" de conhecimento inacessíveis e na subutilização de acervos científicos valiosos.2

No domínio específico da Arquitetura e Urbanismo, este desafio é exacerbado pela complexidade intrínseca da linguagem disciplinar. Títulos de artigos nesta área frequentemente entrelaçam nomes de arquitetos (entidades do tipo *Pessoa*), edifícios ou complexos urbanos (entidades do tipo *Lugar* ou *Obra*), materiais de construção (*Conceitos*) e terminologias estilísticas que variam diacronicamente e geograficamente. Um corretor ortográfico tradicional, baseado em dicionários léxicos estáticos, é incapaz de distinguir entre um erro de digitação e um neologismo arquitetônico, ou entre o uso de "Brutalismo" como um estilo histórico e "brutalismo" como um adjetivo pejorativo.

Este relatório propõe e detalha uma arquitetura de pesquisa e implementação técnica baseada em Reconhecimento de Entidades Nomeadas (NER \- *Named Entity Recognition*) e Processamento de Linguagem Natural (PLN) para a correção automatizada e normalização de grafias em títulos e subtítulos. Inspirando-se em avanços recentes na desambiguação de nomes de autores (AND \- *Author Name Disambiguation*) 4, transferimos metodologias de *Deep Learning* e *Graph Neural Networks* para o tratamento de entidades arquitetônicas, integrando-as a vocabulários controlados de autoridade global, especificamente os tesauros do *Getty Research Institute* (AAT, TGN, ULAN). A análise abrange desde a teoria algorítmica até a implementação prática em APIs REST do OJS, culminando na necessidade imperativa de interfaces *Human-in-the-Loop* (HITL) para validação editorial.

### **1.1. A Natureza Multifacetada do Erro em Metadados de Arquitetura**

A degradação dos metadados não ocorre de forma uniforme. Em análises de repositórios digitais, observa-se que os erros em títulos e subtítulos podem ser categorizados em níveis de complexidade que exigem estratégias de correção distintas. O projeto *MetaEnhance*, focado na melhoria de qualidade de Teses e Dissertações Eletrônicas (ETDs), identificou que a simples detecção de campos vazios ou nulos é insuficiente; o verdadeiro desafio reside na "sujeira" semântica e sintática dos dados existentes.1

No contexto da arquitetura, identificamos cinco tipologias críticas de erro que afetam títulos e subtítulos:

1. **Erros de Reconhecimento Óptico (OCR) e Digitação:** Comuns em acervos digitalizados ou na entrada manual de dados legados. Exemplos incluem a substituição de caracteres visualmente similares ("l" por "1", "rn" por "m") ou a fusão de palavras ("concretoarmado"). Em títulos arquitetônicos, isso pode desfigurar nomes de edifícios históricos ou topônimos, tornando-os irreconhecíveis para motores de busca.2  
2. **Variância de Nomenclatura e Sinonímia:** Um mesmo material ou técnica pode ser referenciado de múltiplas formas. O termo "Concreto Aparente" pode aparecer como "Betão à vista" (em variantes do português), "Béton Brut" (francês técnico) ou "Exposed Concrete". Sem normalização, a busca por um termo exclui os demais.  
3. **Ambiguidades de Entidades Nomeadas:** Termos que possuem significados distintos dependendo do contexto. A palavra "Planalto" pode referir-se a uma característica geográfica genérica ou, no contexto de Brasília, ao "Palácio do Planalto". Um corretor não contextual falhará em capitalizar corretamente a segunda instância.  
4. **Inconsistência de Capitalização (Case Sensitivity):** Títulos acadêmicos frequentemente sofrem com a formatação em CAIXA ALTA herdada de sistemas antigos, ou com a aplicação incorreta de *Title Case* em preposições e artigos. Em arquitetura, a distinção entre "igreja" (edifício genérico) e "Igreja" (parte de um nome próprio, ex: "Igreja da Pampulha") é crucial.  
5. **Desafios Multilíngues e de Tradução:** A arquitetura é uma disciplina global. Títulos frequentemente misturam termos em latim, italiano, francês e inglês. O tratamento incorreto de diacríticos (acentos) em nomes estrangeiros (ex: "Mies van der Rohe" vs. "Mies Van Der Rohe") gera duplicação de entidades nos índices.

A tabela a seguir resume o impacto destes erros na recuperação da informação:

| Tipologia do Erro | Exemplo no Domínio Arquitetônico | Impacto na Indexação | Abordagem de Correção Necessária |
| :---- | :---- | :---- | :---- |
| **Ortográfico / OCR** | "Arquitetura" (sic) / "LeCorbusier" | Falha na busca exata; perda de autoridade. | Fuzzy Matching \+ Dicionário Contextual |
| **Normalização de Entidade** | "Casa de Vidro" vs. "Residência Lina Bo Bardi" | Fragmentação da produção sobre o mesmo objeto. | Entity Linking (Wikidata/Getty) |
| **Ambiguidade Semântica** | "Madeira" (Material) vs. "Madeira" (Ilha/Lugar) | Classificação incorreta em facetas de busca. | NER Contextual (Deep Learning) |
| **Estilo / Formatação** | "O USO DO AÇO" vs. "O uso do aço" | Poluição visual; inconsistência em citações. | Regras Gramaticais \+ Reconhecimento de POS (*Part-of-Speech*) |

## ---

**2\. Fundamentos Teóricos: Do Reconhecimento de Padrões à Compreensão Semântica**

A transição de métodos baseados em regras para métodos baseados em aprendizado profundo (*Deep Learning*) marcou uma mudança de paradigma na correção de textos. Enquanto os sistemas tradicionais operam na superfície léxica (comparando cadeias de caracteres), os sistemas modernos de PNL operam no nível das representações vetoriais (*embeddings*), capturando o significado e o contexto das palavras.

### **2.1. O Estado da Arte em Reconhecimento de Entidades Nomeadas (NER)**

O Reconhecimento de Entidades Nomeadas é a subarefa da extração de informação que busca localizar e classificar elementos atômicos em texto em categorias predefinidas. Para a correção de títulos em arquitetura, as categorias padrão (Pessoa, Organização, Local) são insuficientes. É necessário um esquema de anotação granular que inclua *MATERIAL*, *ESTILO*, *PERÍODO*, *TÉCNICA* e *EDIFÍCIO*.

#### **2.1.1. Arquiteturas baseadas em Transformers (BERT e SciBERT)**

Os modelos de linguagem baseados na arquitetura Transformer, como o BERT (*Bidirectional Encoder Representations from Transformers*), representam o estado da arte atual. O mecanismo de "atenção" (*self-attention*) permite que o modelo pondere a importância de cada palavra em relação a todas as outras na frase, independentemente da distância posicional.

Para o domínio científico, o **SciBERT** 4 oferece vantagens significativas sobre o BERT genérico. Treinado em um corpus massivo de 1,14 milhão de artigos do *Semantic Scholar*, o SciBERT possui um vocabulário (WordPiece) otimizado para a terminologia técnica e acadêmica. Isso é crucial para a arquitetura, onde termos como "Fachada", "Pilotis" ou "Brise-soleil" possuem frequências e contextos de uso muito específicos, distintos da linguagem comum. A capacidade do SciBERT de gerar *embeddings* contextuais permite desambiguar, por exemplo, se a palavra "Design" no título refere-se a uma metodologia de projeto ou a uma disciplina curricular.

#### **2.1.2. Modelos Híbridos e Redes Convolucionais em Grafos (GCN)**

Inspirados pelas pesquisas em Desambiguação de Nomes de Autores (AND) 4, a aplicação de Redes Convolucionais em Grafos (GCN) oferece um caminho promissor para a correção de títulos. Em um repositório acadêmico, um artigo não é uma ilha; ele está conectado a autores, instituições, palavras-chave e citações.

Uma abordagem híbrida proposta para AND combina representações textuais (geradas pelo BERT) com representações estruturais (geradas por GCNs sobre o grafo de citações). Analogamente, para corrigir o título de um artigo sobre "Habitação Social", o sistema pode analisar não apenas o texto do título, mas também as palavras-chave associadas e o histórico de publicações do autor. Se o autor frequentemente publica sobre "Social Housing" e o título atual apresenta "Socail Housing" (erro tipográfico), a evidência estrutural do grafo reforça a correção com maior confiança do que a análise textual isolada.

### **2.2. O Papel dos Dados de Treinamento: O Projeto ArchiText**

Nenhum modelo de NER funciona sem dados de treinamento de alta qualidade. O projeto **ArchiText** 9 ilustra a importância de *corpora* específicos de domínio. Ao minerar textos de periódicos de arquitetura espanhola (1939-1975), os pesquisadores criaram um dataset anotado que permite treinar modelos para reconhecer entidades específicas da história e teoria da arquitetura.

A utilização de datasets como o ArchiText para o *fine-tuning* (ajuste fino) de modelos pré-treinados é essencial. Um modelo genérico pode identificar "Oscar Niemeyer" como uma PESSOA, mas falhará em identificar "Cobogó" como um MATERIAL ou "Azulejaria" como uma TÉCNICA. O ajuste fino com dados anotados (como os provenientes do ArchiText ou de descrições de imagens arquitetônicas 10) especializa os pesos da rede neural para detectar as sutilezas da nomenclatura arquitetônica, permitindo correções ortográficas que respeitam o vocabulário técnico.

## ---

**3\. A Verdade Normalizada: Vocabulários Controlados e Linked Open Data (LOD)**

A correção ortográfica implica a existência de uma forma "correta" ou canônica. Em arquitetura e história da arte, a autoridade global para terminologia é o conjunto de vocabulários mantido pelo *Getty Research Institute*. A integração destes vocabulários via *Linked Open Data* (LOD) transforma o processo de correção em um processo de enriquecimento semântico.11

### **3.1. Getty Art & Architecture Thesaurus (AAT)**

O AAT é um tesauro estruturado que contém termos genéricos, cobrindo conceitos, materiais, estilos, culturas e atributos físicos.14 Ele não é apenas uma lista de palavras, mas uma hierarquia polierárquica rica.

* **Aplicação na Correção:** Quando um título menciona "tijolo de vidro", o NER identifica a entidade MATERIAL. O sistema consulta o AAT e encontra o conceito, mas também descobre que ele é um tipo de "blobo de vidro" e está relacionado a "alvenaria". Isso permite não apenas corrigir a grafia (caso esteja escrito "tijolo de vidor"), mas normalizar para o termo preferencial em português ou inglês, dependendo do idioma alvo do metadado.  
* **Estrutura de Dados:** O AAT é disponibilizado como LOD, permitindo consultas SPARQL complexas. Cada conceito possui um ID único (ex: aat:300011068), termos preferenciais, termos alternativos (sinônimos) e notas de escopo. O uso de IDs estáveis resolve o problema da mudança de grafia ao longo do tempo.

### **3.2. Getty Thesaurus of Geographic Names (TGN)**

O TGN foca em nomes de lugares, incluindo cidades, sítios arqueológicos e nações, com ênfase em locais de importância histórica e artística.17

* **Importância para Urbanismo:** Em títulos sobre urbanismo, a precisão toponímica é vital. O TGN permite desambiguar "Salvador" (cidade no Brasil) de "Salvador" (nome próprio ou cidade em outro país) através de coordenadas e hierarquias espaciais. Se um título menciona "Plano Piloto de Brasíla" (erro), o TGN permite corrigir para "Brasília" e associar o ID geográfico, facilitando a plotagem em mapas de distribuição de pesquisa.

### **3.3. Union List of Artist Names (ULAN)**

O ULAN contém nomes de artistas e arquitetos, incluindo variantes ortográficas, pseudônimos e alterações de nome (casamento, títulos nobiliárquicos).18

* **Normalização de Autoria e Objeto:** Frequentemente, arquitetos são citados de forma abreviada ("Le Corbusier", "Corbu", "Jeanneret"). O ULAN agrupa todas essas variantes sob um único identificador. Isso é crucial para corrigir títulos biográficos. Se um artigo é submetido com o título "A influência de L. Mies no Brasil", o sistema pode sugerir a expansão para "A influência de Ludwig Mies van der Rohe no Brasil", aumentando a recuperabilidade do documento.

### **3.4. Consultas SPARQL para Validação**

A interação com estes vocabulários é realizada através de *endpoints* SPARQL. Esta linguagem de consulta semântica permite perguntas sofisticadas que validam a coerência dos termos encontrados no NER.

Exemplo de lógica de consulta para validar um material arquitetônico:

*"Encontre o termo preferencial em português para qualquer conceito no AAT que corresponda difusamente à string 'concreto armdo' e que pertença à faceta 'Materiais'."*

Essa capacidade de filtrar por faceta (garantindo que estamos buscando um material e não um estilo) reduz drasticamente os falsos positivos na correção automática.20

## ---

**4\. Arquitetura Técnica do Pipeline de Correção**

A implementação de um sistema robusto de correção de metadados exige uma arquitetura de pipeline modular. Detalhamos abaixo os componentes técnicos, bibliotecas e fluxos de dados necessários, desenhados para operar em harmonia com plataformas de publicação como o OJS.

### **4.1. Ingestão e Pré-processamento**

O primeiro estágio envolve a extração e limpeza preliminar dos dados.

* **Fontes de Dados:** Acesso via API REST do OJS ou conexão direta ao banco de dados (para operações em lote iniciais).  
* **Detecção de Idioma:** Utilização de bibliotecas como langdetect ou modelos fasttext para identificar o idioma do título. Títulos em português exigem modelos NER diferentes de títulos em inglês.  
* **Sanitização:** Remoção de tags HTML (\<i\>, \<sup\>, \<br\>) que são comuns em títulos científicos (especialmente para fórmulas químicas ou nomes de espécies, embora menos frequentes em arquitetura, tags de itálico para termos estrangeiros são comuns). O uso da biblioteca BeautifulSoup em Python é recomendado para esta limpeza segura.23

### **4.2. O Motor de NER e Entity Linking**

Este é o núcleo inteligente do sistema. Recomendamos o uso da biblioteca **spaCy** (v3.0+) devido à sua arquitetura eficiente, suporte a transformers e facilidade de integração em pipelines de produção.24

#### **Comparativo Técnico: spaCy vs. Flair**

| Característica | spaCy | Flair | Recomendação para este Projeto |
| :---- | :---- | :---- | :---- |
| **Arquitetura** | CNN, Transformers (via spacy-transformers) | Embeddings contextualizados (Flair Embeddings), BiLSTM-CRF | **spaCy** pela velocidade e ecossistema industrial. |
| **Precisão (SOTA)** | Alta (com modelos trf) | Muito Alta (frequentemente supera SOTA em benchmarks acadêmicos) | **Flair** para fases de *fine-tuning* offline; **spaCy** para inferência em tempo real. |
| **Entity Linking** | Componente nativo (EntityLinker) | Menos maduro, focado em NER puro | **spaCy** facilita a conexão com KBs externas. |
| **Facilidade de Uso** | API orientada a objetos, pipeline intuitivo | API orientada a pesquisa, mais verbosa | **spaCy** para integração com OJS e WebApps. |

**Fluxo de Processamento no spaCy:**

1. **Tokenização:** Segmentação do título em palavras e pontuação.  
2. **POS Tagging:** Identificação de classes gramaticais (Substantivo, Verbo, Adjetivo). Isso ajuda a proteger verbos de correções indevidas baseadas em dicionários de substantivos.  
3. **NER (Transformer):** O modelo (ex: pt\_core\_news\_lg ou um modelo customizado SciBERT) identifica spans de entidades.  
4. **Componente Customizado de Linking:** Um componente Python personalizado consulta as APIs do Getty/Wikidata.  
   * *Algoritmo de Matching:* Utiliza-se RapidFuzz ou TheFuzz 27 para calcular a Distância de Levenshtein entre a entidade extraída e os candidatos na base de conhecimento.  
   * *Threshold:* Se a similaridade for \> 85% e \< 100%, marca-se como "Sugestão de Correção". Se for \< 85%, marca-se como "Entidade Desconhecida".

### **4.3. Implementação de Entity Linking com Base de Conhecimento Customizada**

O spaCy permite a criação de uma *KnowledgeBase* (KB) em memória para desambiguação rápida.24 Para arquitetura, recomenda-se "pré-popular" uma KB do spaCy com os termos mais frequentes do AAT e TGN.

Python

\# Exemplo conceitual de configuração de KB no spaCy  
from spacy.kb import KnowledgeBase  
import spacy

nlp \= spacy.load("pt\_core\_news\_lg")  
kb \= KnowledgeBase(vocab=nlp.vocab, entity\_vector\_length=300)

\# Adicionar entidades do Getty AAT (pré-processadas)  
kb.add\_entity(entity="aat:300011068", freq=500, entity\_vector=vector\_concreto)  
kb.add\_alias(alias="betão armado", entities=\["aat:300011068"\], probabilities=\[0.9\])  
kb.add\_alias(alias="concreto armdo", entities=\["aat:300011068"\], probabilities=\[0.8\]) \# Variante com erro

Essa abordagem híbrida (KB local para velocidade \+ API remota para cobertura exaustiva) equilibra performance e precisão.

## ---

**5\. Integração com o Open Journal Systems (OJS)**

A aplicação das correções geradas pelo pipeline no ambiente de produção do OJS exige um entendimento profundo de sua estrutura de dados e interfaces de programação (APIs). A manipulação direta do banco de dados SQL é desencorajada devido ao risco de corrupção de integridade referencial e inconsistência de caches.

### **5.1. Estrutura de Metadados no Banco de Dados OJS**

No OJS 3.x, os metadados das publicações são armazenados seguindo um modelo EAV (*Entity-Attribute-Value*) na tabela publication\_settings.29

* Esta tabela relaciona publication\_id com pares de chave-valor (setting\_name, setting\_value) e, crucialmente, locale.  
* Isso significa que um título não é uma coluna única; é uma linha onde setting\_name \= 'title' e locale \= 'pt\_BR', e outra linha onde locale \= 'en\_US'.  
* O pipeline de correção deve, portanto, respeitar a localidade. Corrigir um título em inglês usando regras de gramática portuguesa resultaria em erros graves (ex: minúsculas em substantivos próprios).

### **5.2. Estratégia de Atualização via API REST**

A API REST do OJS é o mecanismo seguro para leitura e escrita. A partir da versão 3.2, e com melhorias significativas na 3.4, o OJS suporta operações completas de CRUD sobre submissões e publicações.32

#### **Fluxo de Atualização (Request Lifecycle):**

1. **Autenticação:** Obtenção de um *API Token* (Bearer Token) associado a um usuário com papel de Editor ou Gerente de Revista.  
2. **GET Submission:** Recuperação dos metadados atuais via GET /submissions/{submissionId}/publications/{publicationId}.  
3. **Parsing JSON:** O JSON retornado contém objetos aninhados para campos multilíngues:  
   JSON  
   "title": {  
       "pt\_BR": "A Arquitetura de Brasilia",  
       "en\_US": "The Architecture of Brasilia"  
   }

4. **Aplicação da Correção:** O script Python atualiza o valor da chave específica no dicionário JSON.  
5. **PUT Request:** Envio dos dados corrigidos via PUT /submissions/{submissionId}/publications/{publicationId}.33  
   * *Atenção:* O payload do PUT deve conter o objeto de publicação completo ou parcial dependendo da versão da API. Na versão 3.4, é crucial notar que campos como title agora aceitam HTML, exigindo que o script de correção não remova tags intencionais (como itálicos em nomes científicos) durante a sanitização, ou as restaure antes do envio.32

#### **Exemplo de Script de Atualização (Python/Requests)**

Utilizando a biblioteca requests, padrão da indústria para interações HTTP em Python 23, o script deve implementar tratamento de erros robusto (retentativas em caso de falha de rede, log de erros HTTP 403/404).

Python

import requests  
import json

def update\_ojs\_title(api\_url, api\_token, submission\_id, publication\_id, new\_titles):  
    headers \= {  
        "Authorization": f"Bearer {api\_token}",  
        "Content-Type": "application/json"  
    }  
    endpoint \= f"{api\_url}/submissions/{submission\_id}/publications/{publication\_id}"  
      
    \# Payload contendo apenas os campos a serem atualizados (PATCH behavior simulado)  
    \# Nota: Em algumas versões do OJS, pode ser necessário enviar o objeto completo.  
    payload \= {  
        "title": new\_titles \# Dicionário {'pt\_BR': '...', 'en\_US': '...'}  
    }  
      
    response \= requests.put(endpoint, headers=headers, data=json.dumps(payload))  
      
    if response.status\_code \== 200:  
        return True, response.json()  
    else:  
        return False, response.text

## ---

**6\. O Fator Humano: Implementação de Interfaces "Human-in-the-Loop" (HITL)**

A automação total na correção de registros bibliográficos carrega riscos inerentes. Modelos de IA podem "alucinar" correções ou normalizar indevidamente neologismos intencionais ou grafias arcaicas que devem ser preservadas por razões históricas. A abordagem *Human-in-the-Loop* (HITL) não é apenas uma medida de segurança, mas um componente ativo de melhoria do modelo.36

### **6.1. O Workbench de Curadoria**

Para operacionalizar o HITL, propõe-se o desenvolvimento de uma aplicação web leve, um "Workbench de Curadoria", utilizando o framework **Streamlit**. O Streamlit permite a criação rápida de interfaces de dados em Python puro, conectando-se diretamente aos scripts de NER e à API do OJS.40

**Funcionalidades do Workbench:**

1. **Fila de Revisão:** O sistema apresenta pares de "Original vs. Sugestão" para títulos onde a confiança do modelo está entre um intervalo crítico (ex: 60% a 90%). Correções com confiança \> 99% podem ser aprovadas automaticamente (com log), e \< 60% descartadas.  
2. **Visualização de Diferenças:** Uso de realce visual (estilo *diff*) para mostrar exatamente quais caracteres ou palavras foram alterados.  
3. **Contexto Enriquecido:** Ao lado da sugestão, o sistema exibe o link para a autoridade (Getty AAT/ULAN) que justificou a correção. Isso empodera o editor humano a tomar decisões informadas.  
4. **Feedback Loop (Active Learning):** Quando o editor rejeita uma correção (ex: o sistema tentou corrigir o nome próprio "Lina" para "Linha"), essa decisão é gravada. O dataset de treinamento é atualizado com este "falso positivo", e o modelo é re-treinado periodicamente para não cometer o mesmo erro.42

### **6.2. Benefícios do HITL para Arquitetura**

Em arquitetura, títulos de manifestos ou obras teóricas frequentemente usam jogos de palavras (ex: "Delirious New York"). Um corretor automático poderia tentar higienizar isso. O humano no loop garante a preservação da *intentio auctoris*, enquanto a máquina cuida da normalização de termos técnicos padronizáveis (ex: "Concreto Protendido"). Além disso, o processo de revisão humana gera um "Golden Dataset" anotado de altíssima qualidade, específico para a revista ou repositório em questão, que se torna um ativo valioso para pesquisas futuras.

## ---

**7\. Análise de Impacto e Cenários de Aplicação**

A implementação desta arquitetura de correção e enriquecimento de metadados gera impactos tangíveis e mensuráveis na ecologia da informação científica.

### **7.1. Cenários Práticos de Correção**

#### **Cenário A: Normalização de Materiais**

* **Original:** "Análise da durabilidade do betão aparente em fachadas litorâneas."  
* **Problema:** "Betão aparente" é o termo em PT-PT, mas o repositório busca padronizar para PT-BR ou permitir busca cruzada.  
* **Ação NER:** Identifica "betão aparente" como MATERIAL.  
* **Ação Getty AAT:** Linka ao conceito aat:300011068 (reinforced concrete/betão armado) e suas variantes de acabamento.  
* **Resultado:** O título pode ser mantido (preservando o original), mas o campo de metadados "Assunto" ou "Palavras-chave" é enriquecido automaticamente com "Concreto Aparente", "Exposed Concrete", ampliando a visibilidade.

#### **Cenário B: Correção de Nomes de Edifícios (Topônimos)**

* **Original:** "O modernismo no Palacio Capanema e seus jardins."  
* **Problema:** Falta de acentuação em "Palácio" e uso do nome informal.  
* **Ação NER:** Identifica "Palacio Capanema" como EDIFÍCIO/LUGAR.  
* **Ação TGN/Wikidata:** Identifica a entidade "Edifício Gustavo Capanema" (Ministério da Educação e Saúde).  
* **Resultado:** Sugestão de correção para "O modernismo no Palácio Capanema..." ou nota de metadado ligando ao nome oficial, garantindo que buscas por "Ministério da Educação" também recuperem este artigo.

### **7.2. Impacto na Recuperação da Informação (IR)**

Estudos comparativos indicam que a limpeza de metadados aumenta significativamente as taxas de *Recall* (capacidade de encontrar todos os documentos relevantes) em sistemas de busca. Em testes com o framework MetaEnhance, a correção automatizada alcançou F1-scores entre 0.85 e 1.00 para campos chave 6, sugerindo que a grande maioria dos erros que impedem a descoberta de artigos pode ser eliminada sem intervenção humana extensiva.

Além disso, a interoperabilidade semântica (LOD) transforma o repositório de um arquivo estático para um nó na Web Semântica. Artigos corrigidos e linkados ao Getty AAT podem ser automaticamente integrados a agregadores internacionais de patrimônio cultural (como Europeana ou DPLA), expondo a produção arquitetônica local a uma audiência global.

## ---

**8\. Considerações Finais e Roteiro de Implementação**

A pesquisa exaustiva confirma que a tecnologia atual de PLN e NER atingiu um nível de maturidade suficiente para resolver o problema crônico da qualidade de metadados em arquitetura e urbanismo. A combinação de modelos Transformers (SciBERT) com a autoridade curatorial dos vocabulários Getty oferece o equilíbrio ideal entre automação estatística e precisão semântica.

Para instituições que desejam adotar esta solução, recomenda-se o seguinte roteiro incremental:

1. **Diagnóstico de Dados:** Executar scripts de *profiling* no banco de dados do OJS para quantificar a taxa de erro e identificar os padrões mais comuns (focar primeiro em erros de codificação de caracteres e depois em entidades).  
2. **Protótipo HITL:** Implementar o Workbench Streamlit conectado a uma amostra de dados. Isso permite validar a precisão dos modelos NER sem risco de corromper o banco de dados de produção.  
3. **Integração de Vocabulários:** Desenvolver os conectores para as APIs do Getty AAT e TGN, implementando cache local (Redis) para evitar latência de rede e bloqueios de API.  
4. **Automação Gradual:** Iniciar a correção automática apenas para casos de altíssima confiança (\>98%), mantendo a revisão humana para os demais.  
5. **Política de Governança:** Estabelecer diretrizes claras sobre o que constitui um "erro" versus uma "variação estilística", documentando estas decisões para garantir a consistência a longo prazo.

Em última análise, investir na qualidade dos metadados não é apenas uma tarefa técnica de limpeza; é um investimento na perenidade e na visibilidade da ciência arquitetônica.

### **Referências Citadas no Texto**

4

#### **Referências citadas**

1. Dealing with metadata quality: The legacy of digital library efforts \- ResearchGate, acessado em fevereiro 11, 2026, [https://www.researchgate.net/publication/246946272\_Dealing\_with\_metadata\_quality\_The\_legacy\_of\_digital\_library\_efforts](https://www.researchgate.net/publication/246946272_Dealing_with_metadata_quality_The_legacy_of_digital_library_efforts)  
2. Metadata and Data Quality Problems in the Digital Library \- Journal of Digital Information (JoDI), acessado em fevereiro 11, 2026, [https://jodi-ojs-tdl.tdl.org/jodi/article/view/jodi-171/68](https://jodi-ojs-tdl.tdl.org/jodi/article/view/jodi-171/68)  
3. An Assessment of Metadata Quality: A Case Study of the National Science Digital Library Metadata Repository \- ResearchGate, acessado em fevereiro 11, 2026, [https://www.researchgate.net/publication/28674964\_An\_Assessment\_of\_Metadata\_Quality\_A\_Case\_Study\_of\_the\_National\_Science\_Digital\_Library\_Metadata\_Repository](https://www.researchgate.net/publication/28674964_An_Assessment_of_Metadata_Quality_A_Case_Study_of_the_National_Science_Digital_Library_Metadata_Repository)  
4. A Hybrid Machine Learning Method to Author ... \- ACL Anthology, acessado em fevereiro 11, 2026, [https://aclanthology.org/2024.stil-1.21.pdf](https://aclanthology.org/2024.stil-1.21.pdf)  
5. An Effective Author Name Disambiguation Framework for Large-Scale Publications, acessado em fevereiro 11, 2026, [https://www.researchgate.net/publication/386450969\_An\_Effective\_Author\_Name\_Disambiguation\_Framework\_for\_Large-Scale\_Publications](https://www.researchgate.net/publication/386450969_An_Effective_Author_Name_Disambiguation_Framework_for_Large-Scale_Publications)  
6. \[2303.17661\] MetaEnhance: Metadata Quality Improvement for Electronic Theses and Dissertations of University Libraries \- arXiv, acessado em fevereiro 11, 2026, [https://arxiv.org/abs/2303.17661](https://arxiv.org/abs/2303.17661)  
7. Building a Named Entity Recognition Model for the Legal Domain – RelationalAI, acessado em fevereiro 11, 2026, [https://relational.ai/blog/building-a-named-entity-recognition-model-for-the-legal-domain](https://relational.ai/blog/building-a-named-entity-recognition-model-for-the-legal-domain)  
8. A Hybrid Machine Learning Method to Author Name Disambiguation \- SOL-SBC, acessado em fevereiro 11, 2026, [https://sol.sbc.org.br/index.php/stil/article/download/31122/30925/](https://sol.sbc.org.br/index.php/stil/article/download/31122/30925/)  
9. (PDF) ArchiText Mining: Applying Text Analytics to Research on Modern Architecture, acessado em fevereiro 11, 2026, [https://www.researchgate.net/publication/339307918\_ArchiText\_Mining\_Applying\_Text\_Analytics\_to\_Research\_on\_Modern\_Architecture](https://www.researchgate.net/publication/339307918_ArchiText_Mining_Applying_Text_Analytics_to_Research_on_Modern_Architecture)  
10. Generative AI-powered architectural exterior conceptual design based on the design intent | Journal of Computational Design and Engineering | Oxford Academic, acessado em fevereiro 11, 2026, [https://academic.oup.com/jcde/article/11/5/125/7749580](https://academic.oup.com/jcde/article/11/5/125/7749580)  
11. Linking the Getty Vocabularies:, acessado em fevereiro 11, 2026, [https://www.getty.edu/research/tools/vocabularies/harpring\_linking\_presentation\_version.pdf](https://www.getty.edu/research/tools/vocabularies/harpring_linking_presentation_version.pdf)  
12. Getty Vocabularies and Linked Open Data (LOD) \- Getty Museum, acessado em fevereiro 11, 2026, [https://www.getty.edu/research/tools/vocabularies/Linked\_Data\_Getty\_Vocabularies.pdf](https://www.getty.edu/research/tools/vocabularies/Linked_Data_Getty_Vocabularies.pdf)  
13. Getty Vocabularies as LOD (Getty Research Institute), acessado em fevereiro 11, 2026, [https://www.getty.edu/research/tools/vocabularies/lod/index.html](https://www.getty.edu/research/tools/vocabularies/lod/index.html)  
14. How to Use the AAT Online (Getty Research Institute), acessado em fevereiro 11, 2026, [https://www.getty.edu/research/tools/vocabularies/aat/help.html](https://www.getty.edu/research/tools/vocabularies/aat/help.html)  
15. Art & Architecture Thesaurus (Getty Research Institute), acessado em fevereiro 11, 2026, [https://www.getty.edu/research/tools/vocabularies/aat/](https://www.getty.edu/research/tools/vocabularies/aat/)  
16. Art & Architecture Thesaurus ® \- Getty Museum, acessado em fevereiro 11, 2026, [https://www.getty.edu/research/tools/vocabularies/aat\_in\_depth.pdf](https://www.getty.edu/research/tools/vocabularies/aat_in_depth.pdf)  
17. FORMULATING AND OBTAINING URIs: A GUIDE TO COMMONLY USED VOCABULARIES AND REFERENCE SOURCES \- The Library of Congress, acessado em fevereiro 11, 2026, [https://www.loc.gov/aba/pcc/bibframe/TaskGroups/formulate\_obtain\_URI\_guide.pdf](https://www.loc.gov/aba/pcc/bibframe/TaskGroups/formulate_obtain_URI_guide.pdf)  
18. 6\. Metadata value space, acessado em fevereiro 11, 2026, [https://metadataetc.org/metadatabasics/working.htm](https://metadataetc.org/metadatabasics/working.htm)  
19. Obtain the Getty Vocabularies (Getty Research Institute), acessado em fevereiro 11, 2026, [https://www.getty.edu/research/tools/vocabularies/obtain/index.html](https://www.getty.edu/research/tools/vocabularies/obtain/index.html)  
20. AAT Semantic Representation | Getty Vocabularies: LOD, acessado em fevereiro 11, 2026, [https://www.getty.edu/research/tools/vocabularies/lod/aat\_semantic\_representation.pdf](https://www.getty.edu/research/tools/vocabularies/lod/aat_semantic_representation.pdf)  
21. Aalborg Universitet AI for BIM-Based Sustainable Building Design integrating knowledge discovery and semantic data modelling for, acessado em fevereiro 11, 2026, [https://vbn.aau.dk/ws/files/549423127/PHD\_EkaterinaPetrova.pdf](https://vbn.aau.dk/ws/files/549423127/PHD_EkaterinaPetrova.pdf)  
22. Conservation Process Model \- I.R.I.S., acessado em fevereiro 11, 2026, [https://iris.uniroma1.it/retrieve/307012af-9232-405c-aade-725ec91e4a6b/Acierno\_Conservation%20Process%20Model\_2025.pdf](https://iris.uniroma1.it/retrieve/307012af-9232-405c-aade-725ec91e4a6b/Acierno_Conservation%20Process%20Model_2025.pdf)  
23. Python's 'requests' library: learn HTTP methods, parsing responses, proxy usage, timeouts, and more for efficient web scraping. \- GitHub, acessado em fevereiro 11, 2026, [https://github.com/luminati-io/python-requests](https://github.com/luminati-io/python-requests)  
24. EntityLinker · spaCy API Documentation, acessado em fevereiro 11, 2026, [https://spacy.io/api/entitylinker](https://spacy.io/api/entitylinker)  
25. Named Entity Recognition: A Comprehensive Guide to NLP's Key Technology \- Medium, acessado em fevereiro 11, 2026, [https://medium.com/@kanerika/named-entity-recognition-a-comprehensive-guide-to-nlps-key-technology-636a124eaa46](https://medium.com/@kanerika/named-entity-recognition-a-comprehensive-guide-to-nlps-key-technology-636a124eaa46)  
26. The Complete Guide to Named Entity Recognition (NER): Methods, Tools, and Use Cases \- Kairntech, acessado em fevereiro 11, 2026, [https://kairntech.com/blog/articles/the-complete-guide-to-named-entity-recognition-ner/](https://kairntech.com/blog/articles/the-complete-guide-to-named-entity-recognition-ner/)  
27. seatgeek/thefuzz: Fuzzy String Matching in Python \- GitHub, acessado em fevereiro 11, 2026, [https://github.com/seatgeek/thefuzz](https://github.com/seatgeek/thefuzz)  
28. Entity Linking with spacy/Wikipedia \- python \- Stack Overflow, acessado em fevereiro 11, 2026, [https://stackoverflow.com/questions/60096866/entity-linking-with-spacy-wikipedia](https://stackoverflow.com/questions/60096866/entity-linking-with-spacy-wikipedia)  
29. REST API \- OJS (3.3) \- PKP Docs, acessado em fevereiro 11, 2026, [https://docs.pkp.sfu.ca/dev/api/ojs/3.3](https://docs.pkp.sfu.ca/dev/api/ojs/3.3)  
30. Change table publication\_settings \> setting\_value datatype from TEXT to MEDIUMTEXT, acessado em fevereiro 11, 2026, [https://forum.pkp.sfu.ca/t/change-table-publication-settings-setting-value-datatype-from-text-to-mediumtext/73916](https://forum.pkp.sfu.ca/t/change-table-publication-settings-setting-value-datatype-from-text-to-mediumtext/73916)  
31. Coverage Metadata 2.x-3.x migration \- Software Support \- PKP Community Forum, acessado em fevereiro 11, 2026, [https://forum.pkp.sfu.ca/t/coverage-metadata-2-x-3-x-migration/56273](https://forum.pkp.sfu.ca/t/coverage-metadata-2-x-3-x-migration/56273)  
32. REST API \- OJS (3.4) \- PKP Docs, acessado em fevereiro 11, 2026, [https://docs.pkp.sfu.ca/dev/api/ojs/3.4](https://docs.pkp.sfu.ca/dev/api/ojs/3.4)  
33. Name Disambiguation Scheme Based on Heterogeneous Academic Sites \- MDPI, acessado em fevereiro 11, 2026, [https://www.mdpi.com/2076-3417/14/1/192](https://www.mdpi.com/2076-3417/14/1/192)  
34. Extracting metadata from an article/submission \- OJS 3.4.0-4 \- PKP Forum, acessado em fevereiro 11, 2026, [https://forum.pkp.sfu.ca/t/extracting-metadata-from-an-article-submission-ojs-3-4-0-4/84829](https://forum.pkp.sfu.ca/t/extracting-metadata-from-an-article-submission-ojs-3-4-0-4/84829)  
35. Python Requests Giving Me Missing Metadata When Trying To Upload Attachment, acessado em fevereiro 11, 2026, [https://stackoverflow.com/questions/77841985/python-requests-giving-me-missing-metadata-when-trying-to-upload-attachment](https://stackoverflow.com/questions/77841985/python-requests-giving-me-missing-metadata-when-trying-to-upload-attachment)  
36. aws-samples/human-in-the-loop-llm-eval-blog \- GitHub, acessado em fevereiro 11, 2026, [https://github.com/aws-samples/human-in-the-loop-llm-eval-blog](https://github.com/aws-samples/human-in-the-loop-llm-eval-blog)  
37. The Role of Human-in-the-Loop in AI-Driven Data Management | TDWI, acessado em fevereiro 11, 2026, [https://tdwi.org/articles/2025/09/03/adv-all-role-of-human-in-the-loop-in-ai-data-management.aspx](https://tdwi.org/articles/2025/09/03/adv-all-role-of-human-in-the-loop-in-ai-data-management.aspx)  
38. Build a domain‐aware data preprocessing pipeline: A multi‐agent collaboration approach, acessado em fevereiro 11, 2026, [https://aws.amazon.com/blogs/machine-learning/build-a-domain%E2%80%90aware-data-preprocessing-pipeline-a-multi%E2%80%90agent-collaboration-approach/](https://aws.amazon.com/blogs/machine-learning/build-a-domain%E2%80%90aware-data-preprocessing-pipeline-a-multi%E2%80%90agent-collaboration-approach/)  
39. Revolutionizing Scientific Discovery with AI: Inside the Science Discovery Engine | Science Data Portal \- NASA Science Data, acessado em fevereiro 11, 2026, [https://science.data.nasa.gov/learn/blog/artificial-intelligence-data-discovery](https://science.data.nasa.gov/learn/blog/artificial-intelligence-data-discovery)  
40. An Improved Reference Paper Collection System Using Web Scraping with Three Enhancements \- MDPI, acessado em fevereiro 11, 2026, [https://www.mdpi.com/1999-5903/17/5/195](https://www.mdpi.com/1999-5903/17/5/195)  
41. Building a Video Editing App in Python: How to Serve Videos with Flask and Video.js (Part 3\) | Edlitera, acessado em fevereiro 11, 2026, [https://www.edlitera.com/blog/posts/serve-videos-flask-videojs](https://www.edlitera.com/blog/posts/serve-videos-flask-videojs)  
42. Human-in-the-Loop Pipelines | Union.ai, acessado em fevereiro 11, 2026, [https://www.union.ai/blog-post/human-in-the-loop-pipelines](https://www.union.ai/blog-post/human-in-the-loop-pipelines)  
43. MetaEnhance: Metadata Quality Improvement for Electronic Theses and Dissertations of University Libraries \- IEEE Xplore, acessado em fevereiro 11, 2026, [https://ieeexplore.ieee.org/document/10265916](https://ieeexplore.ieee.org/document/10265916)