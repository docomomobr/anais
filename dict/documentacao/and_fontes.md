# **Arquitetura de Dados e Resolução de Entidades: Um Framework Exaustivo para Desambiguação de Autoria (AND) em Coleções de Arquitetura no Open Journal Systems (OJS)**

## **1\. Introdução e Contextualização do Problema**

A integridade dos registros bibliográficos em bibliotecas digitais contemporâneas enfrenta um desafio existencial conhecido como Desambiguação de Nomes de Autor (Author Name Disambiguation \- AND). Em repositórios acadêmicos que operam em escala, como é o caso de instalações robustas do Open Journal Systems (OJS) contendo milhares de artigos, a ambiguidade autoral não é apenas um inconveniente administrativo, mas uma barreira fundamental à recuperação da informação e à análise cienciométrica precisa. No domínio específico da arquitetura e do urbanismo, este desafio é exponencialmente amplificado por idiossincrasias históricas e profissionais que diferenciam este campo das ciências exatas ou biomédicas. A construção de uma pipeline de AND eficaz exige, portanto, uma convergência sofisticada entre engenharia de dados, ciência da informação e a aplicação de normas de autoridade específicas do domínio, como o *Union List of Artist Names* (ULAN) do Getty Research Institute.

O fenômeno da ambiguidade manifesta-se através de duas patologias primárias nos dados: a sinonímia, onde um único autor aparece sob múltiplas variações de nome (por exemplo, "Le Corbusier", "C.E. Jeanneret", "Charles-Édouard Jeanneret-Gris"), e a polissemia, ou homonímia, onde um único literal de nome (como "J. Silva") refere-se a múltiplos indivíduos distintos.1 Em uma coleção massiva de artigos de arquitetura, a ausência de identificadores persistentes (PIDs) históricos, como o ORCID, nos metadados legados obriga a implementação de métodos algorítmicos para reconstruir as identidades autorais. A literatura recente, cobrindo o período de 2016 a 2024, sugere que as abordagens puramente heurísticas são insuficientes, apontando para a necessidade de soluções híbridas que combinem técnicas de *blocking* (blocagem), aprendizado de máquina supervisionado e validação contra vocabulários controlados.3

Este relatório técnico detalha a arquitetura, os métodos, os códigos e as normas necessárias para estabelecer uma infraestrutura de AND resiliente. O objetivo não é apenas limpar os dados existentes, mas estabelecer um "banco de dados intermediário de desambiguação" (Disambiguation Workbench) que atue como uma camada de inteligência entre os dados brutos do OJS e a representação pública canônica dos autores. A análise a seguir integra evidências de pesquisas de ponta e documentação técnica para fornecer um roteiro de implementação que respeite tanto a complexidade do esquema de banco de dados do OJS quanto as nuances teóricas da autoria arquitetônica.

### **1.1 O Estado da Arte em AND (2016-2025)**

A evolução das técnicas de desambiguação sofreu uma mudança paradigmática na última década. Historicamente, sistemas baseados em regras manuais dominavam o campo, dependendo de correspondências exatas de strings ou heurísticas simples. No entanto, levantamentos sistemáticos da literatura entre 2016 e 2025 indicam uma migração massiva para abordagens baseadas em Aprendizado Profundo (*Deep Learning*) e Grafos de Conhecimento Acadêmico (*Scholarly Knowledge Graphs* \- SKGs).1 A complexidade computacional inerente à comparação de todos os pares de registros possíveis (![][image1]) exigiu o desenvolvimento de estratégias de *blocking* eficientes e métodos de representação vetorial (embeddings) que capturam o contexto semântico e relacional dos autores.

As abordagens contemporâneas mais promissoras tratam o problema de AND não como uma simples tarefa de classificação binária (mesmo/não-mesmo), mas como um problema de agrupamento em grafos heterogêneos. Métodos como o MFAND (*Multiple Features Driven AND*) e o DHGN (*Dual-channel Heterogeneous Graph Network*) exemplificam essa tendência, utilizando redes neurais para aprender representações latentes de autores baseadas em coautoria, afiliação institucional e conteúdo textual dos resumos.4 No entanto, para uma aplicação prática em um ambiente de produção OJS, onde os recursos computacionais podem ser limitados e a latência é uma preocupação, a literatura aponta que métodos híbridos — combinando a eficiência de algoritmos de *clustering* tradicionais (como o *Hierarchical Agglomerative Clustering*) com a precisão de modelos de aprendizado ativo — oferecem o melhor equilíbrio entre custo e benefício.4

É crucial notar que, embora o estado da arte acadêmico foque pesadamente em redes neurais complexas, a implementação prática em bibliotecas digitais frequentemente se beneficia mais da curadoria assistida por máquina. Ferramentas e bibliotecas em Python, como dedupe e recordlinkage, implementam versões robustas de aprendizado ativo que permitem ao especialista em domínio treinar o modelo com um número reduzido de exemplos rotulados, alcançando alta precisão sem a necessidade de vastos conjuntos de dados de treinamento pré-existentes, que são escassos no campo da arquitetura.7

### **1.2 Especificidades do Domínio da Arquitetura**

A desambiguação em arquitetura apresenta desafios que não são adequadamente resolvidos por algoritmos genéricos treinados em bases de dados biomédicas (como PubMed) ou de ciência da computação (como DBLP). A natureza da autoria em arquitetura é fluida e muitas vezes coletiva. A distinção entre o "arquiteto projetista", o "escritório de arquitetura" (pessoa jurídica) e o "autor do texto crítico" é frequentemente tênue nos metadados legados. Além disso, a prevalência de nomes transliterados de alfabetos não latinos e a tradição de usar pseudônimos ou nomes artísticos (por exemplo, "Le Corbusier") exigem o uso de arquivos de autoridade especializados.9

Diferentemente de áreas onde a afiliação institucional (Universidade X, Departamento Y) é um forte discriminador, arquitetos frequentemente operam em múltiplos domínios simultaneamente: mantêm práticas privadas, lecionam em múltiplas instituições e participam de coletivos temporários. Isso significa que a "afiliação" nos metadados do OJS é altamente variável e temporalmente instável. Um algoritmo que penalize fortemente a discrepância de afiliação falhará ao identificar que "Zaha Hadid", "Zaha Hadid Architects" e "Z. Hadid (AA School)" referem-se à mesma entidade canônica. Portanto, a pipeline deve incorporar lógica difusa (*fuzzy logic*) e conhecimento de domínio externo, especificamente através da integração com o ULAN, que mapeia essas relações complexas.11

## **2\. Ecossistema de Dados e Infraestrutura OJS**

Para projetar uma pipeline eficaz, é imperativo compreender profundamente a estrutura de dados subjacente do Open Journal Systems (OJS), especificamente nas versões 3.x e 3.4, que introduziram mudanças significativas na modelagem de dados de autores e publicações. A extração e manipulação desses dados exigem uma navegação cuidadosa entre tabelas normalizadas e estruturas de dados semi-estruturadas (JSON).

### **2.1 Análise do Esquema de Banco de Dados OJS**

O OJS opera sobre um banco de dados relacional (tipicamente MySQL ou PostgreSQL). A arquitetura de dados para autores não reside em uma única tabela, mas está distribuída em um modelo que separa a entidade principal de seus atributos estendidos. A tabela central authors serve como o ponto de ancoragem, contendo identificadores primários e chaves estrangeiras que ligam o autor a uma submissão específica (submission\_id) e, por extensão, a uma publicação (publication\_id).13 No entanto, os metadados ricos — essenciais para a desambiguação, como afiliação, biografia e ORCID — são frequentemente armazenados na tabela author\_settings.

A tabela author\_settings opera sob um padrão Entidade-Atributo-Valor (EAV) ou, nas versões mais recentes como a 3.4, utiliza colunas específicas para armazenamento de locale (idioma) e valores que podem ser serializados. Isso apresenta um desafio imediato para a extração SQL direta: os dados necessários para o *blocking* e comparação não estão prontamente disponíveis em colunas planas. Para construir o *dataset* de entrada para a pipeline de AND, é necessário executar consultas SQL complexas que realizam o "pivô" desses atributos, transformando linhas de configurações em colunas de um DataFrame.15

| Tabela | Função na Pipeline AND | Desafios de Extração |
| :---- | :---- | :---- |
| authors | Entidade base. Contém email, given\_name, family\_name (em versões antigas) e chaves de ligação. | Registros duplicados são a norma; cada coautoria cria uma nova linha, mesmo para o mesmo autor real. |
| author\_settings | Armazena affiliation, orcid, biography. | Requer joins múltiplos ou agregação condicional para extrair atributos específicos por idioma (locale). |
| publications | Contexto temporal e de título. Liga autores a date\_published. | Essencial para desambiguação temporal (ex: distinguir homônimos por décadas de atividade). |
| submissions | Status do artigo. | Necessário para filtrar apenas artigos publicados e ignorar rascunhos ou rejeitados. |
| user\_groups | Define o papel do contribuidor (Autor, Tradutor, etc.). | Permite filtrar papéis não-autorais que não devem ser processados na pipeline de AND.17 |

### **2.2 A Transição JSON no OJS 3.4**

Com a atualização para o OJS 3.4, houve uma mudança significativa na forma como certos metadados são manipulados e armazenados, movendo-se em direção a payloads JSON mais estruturados, especialmente na interação via API. Embora o banco de dados ainda mantenha tabelas relacionais, a lógica de aplicação e os endpoints da API REST agora esperam e retornam objetos JSON complexos para colaboradores (contributors). Isso afeta diretamente a estratégia de "escrita de volta" (*write-back*) da pipeline. Enquanto a leitura pode ser feita via SQL para performance (processamento em lote de milhares de registros), a atualização dos registros desambiguados deve, idealmente, ocorrer via API para garantir que ganchos de evento (*event hooks*), como a reindexação de busca e notificações de ORCID, sejam disparados corretamente.18

A documentação da API do OJS 3.4 detalha endpoints específicos para a gestão de contribuidores (POST /submissions/{id}/publications/{id}/contributors), mas alerta para complexidades na validação de esquemas. A pipeline deve ser capaz de construir payloads que respeitem a estrutura de localização (ex: {"affiliation": {"pt\_BR": "USP", "en\_US": "University of São Paulo"}}), o que exige que o script de desambiguação seja "ciente de localidade" (*locale-aware*).18 A ignorância dessa estrutura pode resultar em perda de dados multilingues, algo crítico em revistas de arquitetura que frequentemente publicam em múltiplos idiomas.

### **2.3 Estratégias de Acesso aos Dados**

Para uma coleção de milhares de artigos, a latência da API REST para a extração inicial (leitura) pode ser proibitiva. A estratégia recomendada, baseada nas práticas de engenharia de dados, é uma abordagem híbrida:

1. **Extração (Leitura):** Acesso direto ao banco de dados (SQL) para gerar o *snapshot* inicial dos dados. Isso permite a execução de *joins* otimizados e a extração de todo o corpus em segundos ou minutos.  
2. **Processamento:** Realizado externamente em um ambiente Python (o "Disambiguation Workbench").  
3. **Carga (Escrita):** Atualização via API REST para garantir a integridade referencial e de aplicação, ou via SQL cirúrgico em tabelas de *staging* se a API se mostrar insuficiente para atualizações em massa de IDs canônicos.

## **3\. Projeto do "Disambiguation Workbench": Banco de Dados Intermediário**

Não se deve jamais executar algoritmos de desambiguação destrutivos diretamente no banco de dados de produção do OJS. A prática padrão em engenharia de confiabilidade exige a criação de um ambiente intermediário, aqui denominado "Disambiguation Workbench". Este é um banco de dados independente (preferencialmente PostgreSQL devido ao seu suporte superior a JSON e correspondência difusa) que atua como uma área de manobra para os dados extraídos, processados e canônicos.19

### **3.1 Esquema SQL para o Workbench**

O esquema do Workbench deve refletir o ciclo de vida da desambiguação: dados brutos \-\> blocagem \-\> clustering \-\> canonização. Abaixo, apresenta-se uma definição formal (DDL) para as tabelas essenciais deste ambiente.

SQL

\-- Criação do Schema para isolamento lógico  
CREATE SCHEMA disambiguation\_lab;

\-- Tabela de Staging: Cópia fiel (mas plana) dos dados do OJS  
CREATE TABLE disambiguation\_lab.raw\_authors (  
    staging\_id SERIAL PRIMARY KEY,  
    ojs\_author\_id INT NOT NULL,      \-- ID original no OJS  
    ojs\_submission\_id INT NOT NULL,  
    ojs\_publication\_id INT NOT NULL,  
    first\_name VARCHAR(255),  
    last\_name VARCHAR(255),  
    email VARCHAR(255),  
    affiliation TEXT,                \-- Texto completo da afiliação  
    orcid\_original VARCHAR(30),      \-- ORCID se existir no OJS  
    raw\_json\_settings JSONB,         \-- Cópia de segurança de settings complexos  
    article\_title TEXT,              \-- Contexto para desambiguação  
    publication\_year INT,            \-- Contexto temporal  
    created\_at TIMESTAMP DEFAULT CURRENT\_TIMESTAMP  
);

\-- Tabela de Blocagem: Mapeamento de registros para blocos de comparação  
CREATE TABLE disambiguation\_lab.blocking\_map (  
    staging\_id INT REFERENCES disambiguation\_lab.raw\_authors(staging\_id),  
    block\_key VARCHAR(100),          \-- Ex: "L.CORBUSIER" ou Phonetic code  
    INDEX idx\_block\_key (block\_key)  
);

\-- Tabela de Clusters: O resultado do algoritmo de AND  
CREATE TABLE disambiguation\_lab.author\_clusters (  
    cluster\_id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    primary\_canonical\_name VARCHAR(255),  
    confidence\_score NUMERIC(5,4),   \-- Grau de certeza do cluster (0.0-1.0)  
    review\_status VARCHAR(20) DEFAULT 'PENDING' \-- PENDING, VERIFIED, MERGED  
);

\-- Tabela de Entidades Canônicas: A "Verdade" (Golden Records)  
CREATE TABLE disambiguation\_lab.canonical\_entities (  
    canonical\_id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),  
    cluster\_id UUID REFERENCES disambiguation\_lab.author\_clusters(cluster\_id),  
    display\_name VARCHAR(255) NOT NULL,  
    ulan\_id VARCHAR(50),             \-- Link para Getty ULAN  
    ulan\_uri VARCHAR(255),           \-- URI completo do ULAN  
    orcid\_verified VARCHAR(30),      \-- ORCID validado  
    is\_architect BOOLEAN DEFAULT FALSE, \-- Flag de domínio  
    notes TEXT  
);

\-- Tabela de Mapeamento Final: Liga o ID do OJS à Entidade Canônica  
CREATE TABLE disambiguation\_lab.resolution\_map (  
    ojs\_author\_id INT REFERENCES disambiguation\_lab.raw\_authors(ojs\_author\_id),  
    canonical\_id UUID REFERENCES disambiguation\_lab.canonical\_entities(canonical\_id),  
    match\_method VARCHAR(50),        \-- Ex: 'DEDUPE\_ML', 'ORCID\_MATCH', 'MANUAL'  
    match\_score FLOAT,  
    updated\_in\_ojs BOOLEAN DEFAULT FALSE  
);

Este esquema permite rastreabilidade completa. Se o algoritmo cometer um erro ("over-merging" de dois arquitetos distintos), é possível reverter o mapeamento na tabela resolution\_map sem perder os dados brutos ou a estrutura canônica já validada.21 O uso de UUIDs para os clusters e entidades canônicas previne conflitos de ID e facilita a exportação de dados para sistemas externos ou Linked Data.

## **4\. Pipeline de AND \- Fase 1: Ingestão e Blocagem**

A primeira etapa operacional da pipeline é a ingestão de dados e a aplicação de estratégias de blocagem (*blocking*). A blocagem é uma técnica de redução de dimensionalidade essencial: em vez de comparar cada autor com todos os outros milhares de autores (o que seria computacionalmente inviável), comparam-se apenas autores que compartilham certas características chave, colocando-os no mesmo "bloco".23

### **4.1 Estratégias de Extração SQL**

A consulta SQL para alimentar a tabela raw\_authors deve lidar com a fragmentação do OJS. Utiliza-se a função setting\_value condicional para extrair nomes e afiliações. É crucial normalizar o texto já nesta fase (remoção de espaços extras, conversão para minúsculas para índices de busca), embora a *display version* deva ser preservada.

Python

\# Exemplo conceitual de extração com SQLAlchemy e Pandas  
import pandas as pd  
from sqlalchemy import create\_engine

def extract\_from\_ojs(db\_connection\_str):  
    """  
    Extrai dados complexos de autores do OJS transformando linhas EAV em colunas.  
    """  
    sql\_query \= """  
    SELECT   
        a.author\_id, a.publication\_id, a.email,  
        p.date\_published,  
        COALESCE(s\_given.setting\_value, '') as given\_name,  
        COALESCE(s\_family.setting\_value, '') as family\_name,  
        s\_aff.setting\_value as affiliation,  
        s\_orcid.setting\_value as orcid  
    FROM authors a  
    JOIN publications p ON a.publication\_id \= p.publication\_id  
    \-- Left joins para pivotar author\_settings  
    LEFT JOIN author\_settings s\_given ON a.author\_id \= s\_given.author\_id AND s\_given.setting\_name \= 'givenName'  
    LEFT JOIN author\_settings s\_family ON a.author\_id \= s\_family.author\_id AND s\_family.setting\_name \= 'familyName'  
    LEFT JOIN author\_settings s\_aff ON a.author\_id \= s\_aff.author\_id AND s\_aff.setting\_name \= 'affiliation'  
    LEFT JOIN author\_settings s\_orcid ON a.author\_id \= s\_orcid.author\_id AND s\_orcid.setting\_name \= 'orcid'  
    WHERE p.status \= 3 \-- Apenas publicados  
    """  
    engine \= create\_engine(db\_connection\_str)  
    return pd.read\_sql(sql\_query, engine)

### **4.2 Algoritmos de Blocagem para Arquitetura**

Para nomes de arquitetos, estratégias de blocagem padrão (como Soundex) podem falhar devido à diversidade linguística. A literatura recomenda uma abordagem de *multipass blocking* (blocagem em múltiplos passos) 6:

1. **Bloco 1 \- Iniciais \+ Sobrenome:** Agrupa "F. Wright" e "Frank L. Wright". É tolerante a abreviações de prenomes.  
2. **Bloco 2 \- Bi-gramas do Sobrenome:** Útil para lidar com erros de digitação leves no início do sobrenome (ex: "Niemeyer" vs "Neimeyer").  
3. **Bloco 3 \- Afiliação (Tokenizado):** Agrupa autores que compartilham tokens raros na afiliação (ex: "Bauhaus"), útil quando os nomes são muito comuns (ex: "J. Müller" na Bauhaus).

A biblioteca Python recordlinkage fornece ferramentas eficientes para criar esses índices de blocagem antes de passar os pares candidatos para a fase de resolução detalhada.8

## **5\. Pipeline de AND \- Fase 2: Resolução e Clustering**

O coração da pipeline é o processo de decisão: dado um par de registros dentro de um bloco, eles representam a mesma pessoa? Aqui, o uso da biblioteca dedupe é altamente recomendado para o ecossistema Python, pois ela implementa um paradigma de aprendizado ativo que se adapta às especificidades dos dados fornecidos.7

### **5.1 Métricas de Distância e Engenharia de Features**

Para a arquitetura, as métricas de comparação de strings (distância) devem ser escolhidas com cuidado:

* **Jaro-Winkler:** Superior ao Levenshtein para nomes próprios, pois penaliza menos erros no final da string e mais no início, lidando bem com abreviações comuns em citações acadêmicas.  
* **Cosine Similarity (TF-IDF):** Essencial para campos de afiliação e títulos de artigos. A afiliação "Faculty of Architecture, University of Porto" e "Porto School of Architecture" têm baixa similaridade de string (Levenshtein), mas alta similaridade de cosseno devido aos tokens compartilhados ("Architecture", "Porto").23  
* **Coautoria:** A presença de coautores compartilhados é um dos sinais mais fortes de identidade. Se Autor A e Autor B escreveram com o Autor C, a probabilidade de serem a mesma pessoa aumenta drasticamente. Isso pode ser modelado como uma feature de intersecção de conjuntos no dedupe.

### **5.2 Implementação com dedupe**

O script abaixo ilustra como configurar o dedupe para aprender as nuances dos dados de arquitetura. O processo de "Active Learning" solicitará ao usuário que rotule pares duvidosos (ex: "É 'R. Koolhaas' o mesmo que 'Rem Koolhaas'?"), refinando os pesos de probabilidade do modelo logístico interno.

Python

import dedupe  
import pandas as pd

def train\_dedupe\_model(df\_data, settings\_file='dedupe\_settings.json'):  
    \# Definição de campos com métricas específicas  
    fields \=

    deduper \= dedupe.Dedupe(fields)  
      
    \# Preparação dos dados (formato dict para dedupe)  
    data\_d \= df\_data.to\_dict(orient='index')  
      
    \# Fase de Treinamento Ativo  
    deduper.prepare\_training(data\_d)  
    print("Iniciando rotulagem manual...")  
    dedupe.console\_label(deduper) \# Interface de linha de comando para sim/não  
      
    deduper.train()  
      
    \# Salvar pesos aprendidos  
    with open(settings\_file, 'wb') as sf:  
        deduper.write\_settings(sf)  
          
    return deduper

A saída deste processo não é apenas pares combinados, mas *clusters* de registros. O dedupe utiliza um algoritmo de fechamento transitivo hierárquico para garantir que se A=B e B=C, então A, B e C pertençam ao mesmo cluster.28

### **5.3 Abordagens Avançadas (Grafos)**

Para casos onde a ambiguidade persiste (ex: nomes chineses comuns sem afiliação clara), métodos baseados em grafos como GCNs (*Graph Convolutional Networks*) podem ser explorados. No entanto, a complexidade de implementação é significativamente maior. Uma alternativa pragmática é analisar a "Ponte" no grafo de coautoria: se a fusão de dois nós criar um "super-autor" com um número implausível de conexões ou áreas temáticas desconexas, o *merge* deve ser rejeitado.4

## **6\. Pipeline de AND \- Fase 3: Canonização e Controle de Autoridade**

Uma vez que os registros foram agrupados, a pipeline deve "eleger" um nome canônico para representar o cluster. Na arquitetura, a mera seleção da string mais longa não é suficiente; é necessário validar contra autoridades externas para garantir a precisão histórica e profissional.

### **6.1 Integração com o Getty ULAN**

O *Union List of Artist Names* (ULAN) é a autoridade *de facto* para arquitetura. A integração deve ser feita via SPARQL, consultando o endpoint do Getty (http://vocab.getty.edu/sparql). A consulta deve ser sofisticada o suficiente para filtrar por papel ("architect"), evitando falsos positivos com pintores ou escultores homônimos.9

#### **Script de Consulta SPARQL para Arquitetos**

Abaixo, um exemplo de script Python utilizando SPARQLWrapper para buscar arquitetos no ULAN e recuperar o ID canônico.

Python

from SPARQLWrapper import SPARQLWrapper, JSON

def query\_ulan\_architect(name\_string):  
    sparql \= SPARQLWrapper("http://vocab.getty.edu/sparql.json")  
    \# Consulta otimizada: Busca pelo termo, filtra por tipo 'Person' e verifica 'architect' no escopo  
    query \= f"""  
    SELECT?Subject?Term?ScopeNote?Nationality WHERE {{  
     ?Subject a gvp:PersonConcept;  
               luc:term "{name\_string}";  
               gvp:prefLabelGVP.  
      OPTIONAL {{?Subject gvp:parentString?ScopeNote }}  
      FILTER regex(?ScopeNote, "architect", "i")  
    }} LIMIT 1  
    """  
    sparql.setQuery(query)  
    sparql.setReturnFormat(JSON)  
    results \= sparql.query().convert()  
      
    if results\["results"\]\["bindings"\]:  
        \# Retorna o ID ULAN e o Nome Preferencial (ex: "Niemeyer, Oscar")  
        item \= results\["results"\]\["bindings"\]  
        return item\["value"\], item\["value"\]  
    return None, None

A resposta do ULAN deve ser usada para popular a tabela canonical\_entities no Workbench. Se um cluster for validado pelo ULAN, ele ganha o status de "Alta Confiança".

### **6.2 Regras de Desempate (Tie-Breaking) na Canonização**

Se o ULAN não retornar resultados (o que é comum para acadêmicos contemporâneos menores ou estudantes), a pipeline deve aplicar regras de desempate heurísticas para escolher o nome de exibição 32:

1. **Prioridade ORCID:** Se algum registro no cluster tiver um ORCID validado, use o nome associado a esse registro.  
2. **Completude:** Prefira "Maria da Silva" a "M. Silva".  
3. **Frequência:** Prefira a grafia que aparece na maioria das publicações do cluster (voto majoritário).  
4. **Recência:** Prefira a grafia usada na publicação mais recente (refletindo possíveis mudanças de nome legal ou profissional).

## **7\. Padronização, Normas e Ética**

A pipeline de AND não opera no vácuo; ela deve aderir a padrões de metadados para garantir a interoperabilidade futura e a preservação digital.

### **7.1 Dublin Core e MARC21**

Ao desambiguar e reexportar os dados, os campos devem ser mapeados para padrões internacionais.

* **Dublin Core:** O nome canônico deve popular dc:creator. O papel específico (ex: "Desenhista") deve, se possível, ser preservado em dc:contributor ou através de qualificadores (refinamentos) do Dublin Core.34  
* **MARC21:** Para integração com catálogos de bibliotecas, a distinção entre entrada principal (campo 100\) e secundária (campo 700\) é vital. O ID do ULAN deve ser inserido no subcampo $0 (Authority record control number) ou $1 (Real World Object URI) dos campos MARC, permitindo que bibliotecários utilizem os dados desambiguados.

### **7.2 Considerações Éticas e GDPR**

A desambiguação automatizada pode, inadvertidamente, revelar dados sensíveis ou criar associações falsas prejudiciais (ex: atribuir um artigo polêmico ao autor errado). Em conformidade com regulamentos de proteção de dados (como GDPR), a pipeline deve:

1. Manter um registro de "auditoria" (resolution\_map) que explique *por que* dois registros foram unidos (ex: "Unido por similaridade de email \> 90%").  
2. Oferecer um mecanismo para "desfazer" a desambiguação se um autor contestar o agrupamento.  
3. Evitar inferir dados sensíveis (gênero, etnia) apenas com base no nome para fins de desambiguação, a menos que explicitamente auto-declarados nos metadados.36

## **8\. Manutenção e Atualização Incremental**

Uma coleção de OJS não é estática; novos artigos são submetidos continuamente. A pipeline de AND deve ser projetada para manutenção contínua, não apenas como um evento único de limpeza.

### **8.1 Desambiguação Online (Incremental)**

Para novos registros, a pipeline deve operar em modo "Online". Quando um novo artigo é publicado, o script de desambiguação deve tentar associar os novos autores aos clusters canônicos existentes no disambiguation\_lab. Se a similaridade for alta, o novo registro é anexado ao cluster existente. Se for baixa, um novo cluster (potencialmente um novo autor) é criado. Isso previne a degradação da qualidade dos dados ao longo do tempo.38

### **8.2 Integração com ORCID Plugin**

O uso do plugin oficial de ORCID no OJS deve ser incentivado para *novas* submissões. A pipeline de AND proposta atua como um mecanismo corretivo para o passado (legado), enquanto o plugin ORCID atua como um mecanismo preventivo para o futuro. Quando um autor autentica seu ORCID via plugin, essa informação deve ser capturada e usada para "ancorar" o cluster correspondente no Workbench, tornando-o imune a futuras fusões incorretas.39

## **9\. Roteiro de Implementação: Códigos e Ferramentas**

Para operacionalizar esta pesquisa, recomenda-se a seguinte "stack" tecnológica e sequência de scripts:

1. **Ambiente:** Python 3.9+, PostgreSQL 14+.  
2. **Bibliotecas Essenciais:**  
   * pandas, sqlalchemy, psycopg2: Manipulação de dados e I/O de banco.  
   * dedupe: Motor de aprendizado de máquina para resolução de entidades.  
   * recordlinkage: Ferramentas de blocagem e comparação vetorial.  
   * SPARQLWrapper: Conexão com Getty ULAN.  
   * requests: Interação com a API REST do OJS.  
3. **Scripts Necessários (Resumo):**  
   * 01\_extract\_ojs.py: Extrai dados brutos para o Workbench.  
   * 02\_normalize\_block.py: Limpa strings e gera chaves de blocagem.  
   * 03\_train\_dedupe.py: Interface interativa para treinar o modelo.  
   * 04\_cluster\_resolve.py: Executa a clusterização em lote.  
   * 05\_canonize\_ulan.py: Consulta o Getty ULAN e define nomes preferenciais.  
   * 06\_generate\_report.py: Cria relatórios de QA (Quality Assurance) para revisão humana.  
   * 07\_patch\_ojs\_api.py: (Opcional) Escreve os dados limpos de volta ao OJS.

## **10\. Conclusão**

A implementação de uma pipeline de Desambiguação de Nomes de Autor para uma coleção de arquitetura no OJS é um empreendimento de alta complexidade que exige ir além de scripts simples de limpeza de dados. Ela requer uma arquitetura de dados dedicada (o Workbench), o uso de aprendizado de máquina adaptativo (dedupe) para capturar as nuances de afiliação e coautoria, e a ancoragem firme em autoridades de domínio (Getty ULAN). Ao seguir este framework, é possível transformar um repositório de "strings de nomes" desconexas em um grafo de conhecimento rico, onde arquitetos, obras e textos estão inequivocamente conectados, desbloqueando o verdadeiro valor arquivístico e analítico da coleção.

#### **Referências citadas**

1. Deep Learning Approaches to Author Name Disambiguation: A Survey \- IRIS \- Unibo, acessado em fevereiro 10, 2026, [https://cris.unibo.it/handle/11585/1032165](https://cris.unibo.it/handle/11585/1032165)  
2. Recent Developments in Deep Learning-based Author \- CEUR-WS.org, acessado em fevereiro 10, 2026, [https://ceur-ws.org/Vol-3937/paper9.pdf](https://ceur-ws.org/Vol-3937/paper9.pdf)  
3. Deep Learning Approaches to Author Name Disambiguation: A Survey: Deep Learning Approaches to Author...F. Cappelli et al. \- ResearchGate, acessado em fevereiro 10, 2026, [https://www.researchgate.net/publication/396692477\_Deep\_Learning\_Approaches\_to\_Author\_Name\_Disambiguation\_A\_Survey\_Deep\_Learning\_Approaches\_to\_AuthorF\_Cappelli\_et\_al](https://www.researchgate.net/publication/396692477_Deep_Learning_Approaches_to_Author_Name_Disambiguation_A_Survey_Deep_Learning_Approaches_to_AuthorF_Cappelli_et_al)  
4. A Hybrid Machine Learning Method to Author Name Disambiguation \- ACL Anthology, acessado em fevereiro 10, 2026, [https://aclanthology.org/2024.stil-1.21.pdf](https://aclanthology.org/2024.stil-1.21.pdf)  
5. Graph-based methods for Author Name Disambiguation: a survey \- PeerJ, acessado em fevereiro 10, 2026, [https://peerj.com/articles/cs-1536/](https://peerj.com/articles/cs-1536/)  
6. A Knowledge Graph Embeddings based Approach for Author Name Disambiguation using Literals \- FIZ Karlsruhe, acessado em fevereiro 10, 2026, [https://www.fiz-karlsruhe.de/sites/default/files/FIZ/Dokumente/Forschung/ISE/Technical-Report/LAND-Santini.pdf](https://www.fiz-karlsruhe.de/sites/default/files/FIZ/Dokumente/Forschung/ISE/Technical-Report/LAND-Santini.pdf)  
7. dedupeio/dedupe: :id: A python library for accurate and scalable fuzzy matching, record deduplication and entity-resolution. \- GitHub, acessado em fevereiro 10, 2026, [https://github.com/dedupeio/dedupe](https://github.com/dedupeio/dedupe)  
8. About — Python Record Linkage Toolkit 0.15 documentation, acessado em fevereiro 10, 2026, [https://recordlinkage.readthedocs.io/en/latest/about.html](https://recordlinkage.readthedocs.io/en/latest/about.html)  
9. Vocabularies Download Center (Getty Research Institute), acessado em fevereiro 10, 2026, [https://www.getty.edu/research/tools/vocabularies/obtain/download.html](https://www.getty.edu/research/tools/vocabularies/obtain/download.html)  
10. Linking the Getty Vocabularies:, acessado em fevereiro 10, 2026, [https://www.getty.edu/research/tools/vocabularies/harpring\_linking\_presentation\_version.pdf](https://www.getty.edu/research/tools/vocabularies/harpring_linking_presentation_version.pdf)  
11. Exploring Graph Based Approaches for Author Name Disambiguation \- arXiv, acessado em fevereiro 10, 2026, [https://arxiv.org/html/2312.08388v1](https://arxiv.org/html/2312.08388v1)  
12. Advanced OpenRefine Techniques Using the Getty Vocabularies, acessado em fevereiro 10, 2026, [https://www.getty.edu/research/tools/vocabularies/g\_garcia\_openrefine\_workshop\_itwg2020.pdf](https://www.getty.edu/research/tools/vocabularies/g_garcia_openrefine_workshop_itwg2020.pdf)  
13. Database Design \- PKP Docs \- Simon Fraser University, acessado em fevereiro 10, 2026, [https://docs.pkp.sfu.ca/ojs-2-technical-reference/en/database\_design](https://docs.pkp.sfu.ca/ojs-2-technical-reference/en/database_design)  
14. ojs-stable-3\_4\_0 Database \- PKP Docs, acessado em fevereiro 10, 2026, [https://docs.pkp.sfu.ca/dev/database/ojs/3.4/](https://docs.pkp.sfu.ca/dev/database/ojs/3.4/)  
15. Help with upgrading from 3.3.0.22 to 3.5.0-3 \- Software Support \- PKP Forum, acessado em fevereiro 10, 2026, [https://forum.pkp.sfu.ca/t/help-with-upgrading-from-3-3-0-22-to-3-5-0-3/97715](https://forum.pkp.sfu.ca/t/help-with-upgrading-from-3-3-0-22-to-3-5-0-3/97715)  
16. Error upgrading from ojs-3.3.0-20 to ojs-3.4.0-9 \- Software Support \- PKP Forum, acessado em fevereiro 10, 2026, [https://forum.pkp.sfu.ca/t/error-upgrading-from-ojs-3-3-0-20-to-ojs-3-4-0-9/96250](https://forum.pkp.sfu.ca/t/error-upgrading-from-ojs-3-3-0-20-to-ojs-3-4-0-9/96250)  
17. Is there any documentation on how to "fully" create a submission via REST API?, acessado em fevereiro 10, 2026, [https://forum.pkp.sfu.ca/t/is-there-any-documentation-on-how-to-fully-create-a-submission-via-rest-api/74730](https://forum.pkp.sfu.ca/t/is-there-any-documentation-on-how-to-fully-create-a-submission-via-rest-api/74730)  
18. REST API \- OJS (3.4) \- PKP Docs, acessado em fevereiro 10, 2026, [https://docs.pkp.sfu.ca/dev/api/ojs/3.4](https://docs.pkp.sfu.ca/dev/api/ojs/3.4)  
19. Documentation: 18: 5.10. Schemas \- PostgreSQL, acessado em fevereiro 10, 2026, [https://www.postgresql.org/docs/current/ddl-schemas.html](https://www.postgresql.org/docs/current/ddl-schemas.html)  
20. Documentation: 18: CREATE SCHEMA \- PostgreSQL, acessado em fevereiro 10, 2026, [https://www.postgresql.org/docs/current/sql-createschema.html](https://www.postgresql.org/docs/current/sql-createschema.html)  
21. ALIAS: Author Disambiguation in Microsoft Academic Search Engine Dataset \- OpenProceedings.org, acessado em fevereiro 10, 2026, [https://openproceedings.org/2014/conf/edbt/PittsSRM14.pdf](https://openproceedings.org/2014/conf/edbt/PittsSRM14.pdf)  
22. A flow network with a valid flow. | Download Scientific Diagram \- ResearchGate, acessado em fevereiro 10, 2026, [https://www.researchgate.net/figure/A-flow-network-with-a-valid-flow\_fig4\_261404658](https://www.researchgate.net/figure/A-flow-network-with-a-valid-flow_fig4_261404658)  
23. Author Name Disambiguation for PubMed \- PMC \- NIH, acessado em fevereiro 10, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC5530597/](https://pmc.ncbi.nlm.nih.gov/articles/PMC5530597/)  
24. A survey of author name disambiguation techniques: 2010–2016 | The Knowledge Engineering Review | Cambridge Core, acessado em fevereiro 10, 2026, [https://www.cambridge.org/core/journals/knowledge-engineering-review/article/survey-of-author-name-disambiguation-techniques-20102016/EF8B67C2D3BFABBB05F883C899A9934A](https://www.cambridge.org/core/journals/knowledge-engineering-review/article/survey-of-author-name-disambiguation-techniques-20102016/EF8B67C2D3BFABBB05F883C899A9934A)  
25. Data deduplication — Python Record Linkage Toolkit 0.15 documentation, acessado em fevereiro 10, 2026, [https://recordlinkage.readthedocs.io/en/latest/guides/data\_deduplication.html](https://recordlinkage.readthedocs.io/en/latest/guides/data_deduplication.html)  
26. Entity resolution in Python with the dedupe package \- Fivetran, acessado em fevereiro 10, 2026, [https://www.fivetran.com/learn/entity-resolution-in-python-with-the-dedupe-package](https://www.fivetran.com/learn/entity-resolution-in-python-with-the-dedupe-package)  
27. Query-Driven Approach to Entity Resolution \- VLDB Endowment, acessado em fevereiro 10, 2026, [http://www.vldb.org/pvldb/vol6/p1846-altwaijry.pdf](http://www.vldb.org/pvldb/vol6/p1846-altwaijry.pdf)  
28. Deduplicating data \- Python for Data Science 24.3.0, acessado em fevereiro 10, 2026, [https://www.python4data.science/en/24.3.0/clean-prep/deduplicate.html](https://www.python4data.science/en/24.3.0/clean-prep/deduplicate.html)  
29. Basics of Entity Resolution with Python and Dedupe | by District ..., acessado em fevereiro 10, 2026, [https://medium.com/district-data-labs/basics-of-entity-resolution-with-python-and-dedupe-bc87440b64d4](https://medium.com/district-data-labs/basics-of-entity-resolution-with-python-and-dedupe-bc87440b64d4)  
30. Graph-based methods for Author Name Disambiguation: a survey \- PMC \- NIH, acessado em fevereiro 10, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC10557506/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10557506/)  
31. How to Use the ULAN Online (Getty Research Institute), acessado em fevereiro 10, 2026, [https://www.getty.edu/research/tools/vocabularies/ulan/help.html](https://www.getty.edu/research/tools/vocabularies/ulan/help.html)  
32. Algorithmic Contract Theory: A Survey | Foundations and Trends in Theoretical Computer Science | Emerald Publishing, acessado em fevereiro 10, 2026, [https://www.emerald.com/fttcs/article/16/3-4/211/1332655/Algorithmic-Contract-Theory-A-Survey](https://www.emerald.com/fttcs/article/16/3-4/211/1332655/Algorithmic-Contract-Theory-A-Survey)  
33. NAMED ENTITY RECOGNITION – CHALLENGES IN DOCUMENT ANNOTATION, GAZETTEER CONSTRUCTION AND DISAM- BIGUATION \- White Rose eTheses Online, acessado em fevereiro 10, 2026, [https://etheses.whiterose.ac.uk/id/eprint/3866/3/ziqizhang\_thesis-minor-correction.pdf](https://etheses.whiterose.ac.uk/id/eprint/3866/3/ziqizhang_thesis-minor-correction.pdf)  
34. DCMI: Dublin Core™ Metadata Element Set, Version 1.1: Reference Description, acessado em fevereiro 10, 2026, [https://www.dublincore.org/documents/dces/](https://www.dublincore.org/documents/dces/)  
35. DCMI: Using Dublin Core, acessado em fevereiro 10, 2026, [https://www.dublincore.org/specifications/dublin-core/usageguide/](https://www.dublincore.org/specifications/dublin-core/usageguide/)  
36. ISNI Data Policy, acessado em fevereiro 10, 2026, [https://isni.org/resources/pdfs/isni-data-policy.pdf](https://isni.org/resources/pdfs/isni-data-policy.pdf)  
37. Emancipating human rights: Capitalism and the common good | Leiden Journal of International Law | Cambridge Core, acessado em fevereiro 10, 2026, [https://www.cambridge.org/core/journals/leiden-journal-of-international-law/article/emancipating-human-rights-capitalism-and-the-common-good/8341B2BEE60C7BCD7BA9F99B850FD02A](https://www.cambridge.org/core/journals/leiden-journal-of-international-law/article/emancipating-human-rights-capitalism-and-the-common-good/8341B2BEE60C7BCD7BA9F99B850FD02A)  
38. (PDF) Online Author Name Disambiguation in Evolving Digital Library \- ResearchGate, acessado em fevereiro 10, 2026, [https://www.researchgate.net/publication/359923795\_Online\_Author\_Name\_Disambiguation\_in\_Evolving\_Digital\_Library](https://www.researchgate.net/publication/359923795_Online_Author_Name_Disambiguation_in_Evolving_Digital_Library)  
39. Using the ORCID Public API for author disambiguation in the OpenCitations Corpus, acessado em fevereiro 10, 2026, [https://opencitations.hypotheses.org/958](https://opencitations.hypotheses.org/958)  
40. How to Set Up the ORCID Plugin in OJS and OPS \- PKP Docs, acessado em fevereiro 10, 2026, [https://docs.pkp.sfu.ca/orcid/en/installation-setup](https://docs.pkp.sfu.ca/orcid/en/installation-setup)  
41. Implementing your ORCID Plugin for OJS/OPS? Help is Here., acessado em fevereiro 10, 2026, [https://info.orcid.org/implementing-your-orcid-plugin-for-ojs-ops-help-is-here/](https://info.orcid.org/implementing-your-orcid-plugin-for-ojs-ops-help-is-here/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABkAAAAYCAYAAAAPtVbGAAABWUlEQVR4Xu2TPyiFURiHX0LyLxsyGBkMJkWSDAYZLBYLUlbFymCxGJQURUkGSTEpMiiTpJSEMrgDJpPBYuA59z3fvd95ueW6DHKfeuqc93f6zjnfOUfkj9GMm3iJS1gZxj/DEdZhMe7gehjnThk+YZ/vD+EbFqZG/ALTeGuLEe14iHeiKzkJ4yT7+CqaP+JMGEspJnDU1D9wIDrQfag1jJJM4JotelZw3BYt5XiNw6KT7AapsojdtghjOODbn+UpenABSyS9m8b4ADgVzeO04Tx2ed01zsgc9vv2pOgkbtKIBtyL9R3uTdyLjo10Z5eRM6zy7QrRq/mM1b7mfok7k29Tg8emNiu6Mrcrxxa2pOPsGcQpU6vFF3wQ/S03YZw9q6JvxbIsupsNb05cYZEtQpOkD3TEZFnRi+dYYAPPtugk9Tb4Ch2iNypaaQI74wM87h1c2GKePP+Ad2V6Qy8HjshUAAAAAElFTkSuQmCC>