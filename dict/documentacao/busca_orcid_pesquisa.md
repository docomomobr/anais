# **Arquitetura de Desambiguação de Autoria em Escala: Automação via CLI e Inteligência Artificial para Recuperação de Identificadores ORCID em Anais de Seminários**

## **Introdução à Complexidade da Atribuição de Identidade Acadêmica**

A gestão da identidade digital na comunicação científica transcendeu a simples catalogação bibliográfica para se tornar um desafio computacional de alta complexidade, situado na interseção entre a Ciência da Informação e a Engenharia de Dados. A demanda específica por recuperar Identificadores Abertos de Pesquisador e Colaborador (ORCID) para uma lista de 2.000 autores oriundos de seminários acadêmicos apresenta um microcosmo do problema global de Desambiguação de Nomes de Autores (AND \- *Author Name Disambiguation*). Diferente de artigos em periódicos indexados, que frequentemente possuem metadados estruturados e DOIs (Digital Object Identifiers) atribuídos na fonte, os anais de seminários e conferências — muitas vezes classificados como literatura cinzenta ou semipublicada — sofrem de inconsistências crônicas de metadados. Nomes abreviados, ausência de afiliações padronizadas e a falta de links diretos para perfis de autor tornam a busca manual não apenas ineficiente, mas probabilisticamente propensa ao erro.

A resolução deste problema exige o abandono de scripts lineares simples em favor de uma arquitetura de software robusta, operada via Interface de Linha de Comando (CLI), que orquestre fluxos de dados assíncronos e utilize Grandes Modelos de Linguagem (LLMs) como motores de inferência semântica. A escala de 2.000 entidades, embora pareça modesta para padrões de Big Data, é suficientemente grande para inviabilizar a verificação humana e suficientemente complexa para falhar em abordagens determinísticas baseadas puramente em correspondência de strings (string matching). A homonímia — onde múltiplos pesquisadores compartilham o nome "J. Silva" ou "Wei Zhang" — e a sinonímia — onde o mesmo pesquisador publica como "Jane Doe" e "J. R. Doe" — exigem uma abordagem que combine a precisão estrutural de grafos de conhecimento (como OpenAlex e Semantic Scholar) com a capacidade de raciocínio contextual da Inteligência Artificial Generativa.1

Este relatório técnico delineia uma estratégia abrangente para automatizar a recuperação de ORCIDs, detalhando a seleção de APIs, o design da CLI em Python, a engenharia de prompts para desambiguação via LLM e as táticas de otimização de custos e desempenho. A análise fundamenta-se na premissa de que a automação eficaz não busca apenas "encontrar um número", mas estabelecer um vínculo de identidade confiável e verificável dentro do ecossistema de pesquisa global.

## ---

**1\. O Ecossistema de Metadados e a Seleção de Fontes de Verdade**

Para automatizar a busca de ORCIDs com alta revocação (recall) e precisão, é imperativo compreender que o próprio registro ORCID (orcid.org) não é, paradoxalmente, a melhor ferramenta de *descoberta* primária. O registro ORCID é populado voluntariamente pelos usuários ("opt-in"), o que resulta em milhões de perfis esparsos ou privados, onde a busca por nome retorna resultados ambíguos sem metadados de afiliação ou publicação suficientes para uma confirmação segura.3 A estratégia de automação deve, portanto, adotar uma abordagem federada, utilizando agregadores de metadados que enriquecem os dados do ORCID com inferências externas.

### **1.1 A Ascensão do OpenAlex como Motor de Descoberta Primária**

O OpenAlex emergiu como a infraestrutura crítica para bibliometria computacional, superando limitações de bases proprietárias e oferecendo uma API aberta e performática. Diferente do Crossref, que depende do depósito de metadados pelas editoras (que frequentemente omitem ORCIDs em anais de congressos), o OpenAlex ingere dados de múltiplas fontes — incluindo o próprio dump público do ORCID, Crossref, PubMed e repositórios institucionais — e aplica algoritmos de aprendizado de máquina para criar clusters de identidade.4

A relevância do OpenAlex para a lista de 2.000 autores de seminários reside na sua capacidade de "Desambiguação Canônica". Quando um autor publica um trabalho, o OpenAlex tenta vinculá-lo a um cluster existente baseado em coautoria, citações e afiliação. Se o OpenAlex já associou um ORCID a *qualquer* trabalho desse cluster, a API retorna o identificador, mesmo que o artigo específico do seminário não o tenha metadatado originalmente.5

| Característica | API Pública ORCID | API OpenAlex | API Crossref | API Semantic Scholar |
| :---- | :---- | :---- | :---- | :---- |
| **Foco Primário** | Identidade (Auth) | Grafo de Conhecimento | Metadados de Obras (DOI) | Grafo Semântico de Citações |
| **Busca por Nome** | Estrita (Solr), alta homonímia | Fuzzy, agrupada por entidade | Via query bibliográfica | Focada em relevância/impacto |
| **Cobertura ORCID** | Apenas dados inseridos pelo usuário | Agregada de múltiplas fontes | Depende do depósito da editora | Inferida e importada |
| **Rate Limits (Grátis)** | \~12 req/seg (estrito) | 100k/dia (Polite Pool) | Flexível (Polite Pool) | Requer chave para alto volume |
| **Contexto Seminários** | Baixo (muitos perfis vazios) | Alto (indexa repositórios) | Médio (depende de DOI) | Alto (foco em CS/STEM) |

A análise comparativa indica que o OpenAlex deve ser o ponto de entrada do pipeline de automação. Sua API permite filtrar buscas por instituição (last\_known\_institution) e fornece um relevance\_score que auxilia na triagem inicial.7 Além disso, a recente migração do algoritmo de desambiguação do OpenAlex (julho de 2023\) melhorou drasticamente a precisão na vinculação de ORCIDs, especialmente para nomes não-anglófonos, mitigando problemas históricos de fragmentação de perfis.5

### **1.2 O Papel do Crossref e Semantic Scholar como Validadores**

Enquanto o OpenAlex serve para a descoberta ampla, o Crossref e o Semantic Scholar atuam como validadores contextuais. Para anais de seminários que possuem DOIs, a API do Crossref (api.crossref.org/works) permite uma busca inversa: em vez de buscar o autor, busca-se o título do trabalho apresentado no seminário. A resposta JSON do Crossref contém a lista de autores validada pela editora, frequentemente incluindo o ORCID autenticado no momento da submissão.9 Esta rota "Trabalho ![][image1] Autor" é computacionalmente mais cara (exige uma busca por título para cada linha), mas oferece a maior precisão possível ("Ground Truth"), pois o vínculo foi feito pelo próprio autor ou editor.11

O Semantic Scholar, por sua vez, oferece métricas como paperCount e hIndex através de sua Graph API. Essas métricas são vitais para heurísticas de desambiguação: se o autor da lista é um estudante de mestrado apresentando em um seminário júnior, um candidato retornado pela API com 20.000 citações e h-index 50 é provavelmente um homônimo falso positivo (um pesquisador sênior com o mesmo nome).12

## ---

**2\. Arquitetura de Software: CLI Assíncrona em Python**

A automação de 2.000 consultas requer uma mudança de paradigma de scripts sequenciais (síncronos) para uma arquitetura orientada a eventos (assíncrona). Em um script sequencial simples, com uma latência média de API de 1,5 segundos por requisição (considerando overhead de rede e processamento), o processamento total levaria cerca de 50 minutos, sem contar retries por falhas. Uma arquitetura assíncrona bem desenhada pode reduzir esse tempo para menos de 5 minutos, respeitando os limites de taxa (rate limits) das APIs.

### **2.1 Design da Interface de Linha de Comando (CLI)**

Para ferramentas de engenharia de dados acadêmicos, a biblioteca Click (Command Line Interface Creation Kit) ou Typer é superior ao módulo padrão argparse. O Click permite a criação de comandos aninhados, gestão robusta de tipos de dados e geração automática de documentação, o que é essencial para a reprodutibilidade científica e manutenção do código por equipes de pesquisa.14 A CLI deve ser projetada para aceitar arquivos de entrada (CSV/Excel) e sinalizadores de configuração que alterem o comportamento do pipeline sem necessidade de reescrita de código.

**Estrutura Recomendada do Comando CLI:**

Bash

$ orcid-miner hunt \\  
    \--input "anais\_seminario\_2024.csv" \\  
    \--output "resultados\_enriquecidos.jsonl" \\  
    \--use-ai \\  
    \--ai-model "gpt-4o-mini" \\  
    \--concurrency 10 \\  
    \--email "pesquisador@universidade.edu.br"

A inclusão do parâmetro \--email é crucial para acessar o "Polite Pool" das APIs do OpenAlex e Crossref. Este mecanismo, uma convenção de etiqueta na web semântica, oferece aos usuários identificados limites de taxa mais generosos e tempos de resposta mais rápidos, essenciais para cargas de trabalho em lote.10

### **2.2 Gerenciamento de Concorrência e Rate Limiting**

O maior risco técnico ao processar 2.000 requisições não é a complexidade do código, mas o bloqueio por "Denial of Service" (DoS) involuntário. As APIs públicas impõem limites estritos: o ORCID permite cerca de 12-24 requisições por segundo (RPS) com rajadas curtas 17; o OpenAlex sugere 100 RPS globalmente, mas na prática, a latência de rede atua como um limitador natural.16

A implementação deve utilizar o padrão Semaphore da biblioteca asyncio do Python para controlar o número máximo de "workers" simultâneos. Além disso, é mandatório implementar uma lógica de "Backoff Exponencial". Quando uma API retorna o código de status HTTP 429 (Too Many Requests), o script não deve tentar novamente imediatamente. Ele deve esperar um tempo base multiplicado por um fator a cada falha subsequente (ex: 2s, 4s, 8s, 16s), garantindo que o sistema se recupere e a conta IP não seja banida.20

A biblioteca aiohttp é a escolha padrão para o cliente HTTP assíncrono, permitindo manter uma sessão TCP persistente (ClientSession), o que reduz significativamente o overhead de *handshake* SSL/TLS em milhares de conexões repetidas.22

### **2.3 Pipeline de Processamento de Dados**

O fluxo de dados proposto segue uma arquitetura de "Funil de Desambiguação":

1. **Ingestão e Normalização:** O script lê o CSV e normaliza os nomes (remoção de acentos, padronização de caixa alta/baixa, tratamento de sufixos como "Junior" ou "Neto"). Caracteres especiais e erros de codificação são comuns em anais de seminários e devem ser tratados nesta etapa.1  
2. **Busca Ampliada (Broad Search):** Para cada autor, o script consulta o OpenAlex (/authors) e, se disponível o título do artigo, o Crossref (/works).  
3. **Filtragem Heurística:** O script aplica regras determinísticas. Se o nome é "Maria Silva" e a afiliação no CSV é "USP", elimina-se candidatos com afiliações diferentes ou desconhecidas.  
4. **Resolução via IA (Fallback):** Os casos que permanecem ambíguos (vários candidatos plausíveis ou nenhum candidato óbvio) são separados para processamento pelo LLM.  
5. **Persistência Atômica:** Os resultados são gravados em disco linha a linha (ou em pequenos lotes) para evitar perda de dados em caso de crash do script no registro 1.999.23

## ---

**3\. Inteligência Artificial na Desambiguação: Além da Busca Exata**

A limitação fundamental das APIs clássicas é a incapacidade de realizar inferências semânticas. Um script tradicional falha ao tentar conectar um autor listado como "Dept. de Biologia Celular" a um perfil com afiliação "Instituto de Biociências", pois as strings são diferentes. A Inteligência Artificial, especificamente os LLMs, atua como um motor de raciocínio probabilístico capaz de superar essas barreiras semânticas.

### **3.1 LLMs como Árbitros de Identidade**

A estratégia de integração de IA para esta lista de 2.000 nomes não envolve o treinamento de um modelo (o que seria custoso e desnecessário), mas o uso de **RAG (Retrieval-Augmented Generation)** em um contexto de classificação "zero-shot" ou "few-shot". O script Python coleta os metadados "sujos" do seminário e os metadados "candidatos" das APIs e constrói um prompt para o LLM decidir qual é o correto.24

Estudos recentes demonstram que LLMs enriquecidos com dados de coautoria e afiliação superam métodos baseados apenas em regras para a tarefa de desambiguação.26 O modelo pode analisar, por exemplo, que o título do artigo no seminário ("Análise de Polímeros Condutores") tem alta afinidade semântica com o histórico de publicações de um candidato do OpenAlex focado em "Ciência dos Materiais", validando o ORCID desse candidato mesmo que a afiliação institucional tenha mudado ligeiramente.

### **3.2 Engenharia de Prompt para Dados Bibliográficos**

A qualidade da resposta da IA depende estritamente da estrutura do prompt. Para automação via CLI, a saída do LLM deve ser estruturada (JSON), não textual.

**Template de Prompt Sugerido:**

"Você é um especialista em bibliometria e desambiguação de autores.

**Entrada:**

* Autor Alvo: {nome\_csv}  
* Afiliação Alvo: {afiliacao\_csv}  
* Título do Trabalho: {titulo\_seminario}

**Candidatos Recuperados (API OpenAlex):**

{json\_candidatos}

**Tarefa:** Analise semanticamente a compatibilidade entre o Autor Alvo e os Candidatos. Considere variações de nome, equivalência de instituições (ex: siglas vs nomes completos) e relevância temática do trabalho.

**Saída:** Retorne APENAS um objeto JSON com o formato: {'best\_match\_id': '...', 'confidence\_score': 0.0-1.0, 'reasoning': '...'}. Se nenhum candidato for viável, retorne null."

A inclusão do título do trabalho no prompt é vital. Modelos como o GPT-4o demonstram capacidade notável de correlacionar tópicos de pesquisa a partir de títulos, servindo como uma "impressão digital" intelectual do autor.25

### **3.3 Análise de Custo e Eficiência: Batch API vs. Real-Time**

Para processar 2.000 autores, o custo é uma consideração de engenharia. O uso do modelo gpt-4o (topo de linha) pode ser proibitivo ou desnecessário para casos simples. A recomendação técnica é uma abordagem hierárquica:

1. **Tier 1 (Script Python):** Resolve matches exatos (Nome \+ Afiliação idênticos). Custo zero.  
2. **Tier 2 (GPT-4o-mini):** Resolve casos de pequena variação de string ou abreviações. O modelo "mini" é ordens de magnitude mais barato e suficiente para tarefas de normalização.28  
3. **Tier 3 (GPT-4o):** Acionado apenas para conflitos complexos (ex: dois homônimos na mesma instituição em áreas adjacentes).

Além disso, a OpenAI introduziu a **Batch API**, que permite enviar arquivos JSONL com milhares de requisições para processamento assíncrono com uma janela de retorno de 24 horas. Esta modalidade oferece um desconto de 50% sobre os preços de tabela e limites de taxa (Rate Limits) significativamente maiores, sendo a solução ideal para um relatório que não exige tempo real.30 Para uma lista de 2.000 nomes, o custo estimado via Batch API com gpt-4o-mini seria trivial (provavelmente menos de US$ 5,00), democratizando o acesso a ferramentas de desambiguação de nível industrial.

## ---

**4\. Implementação Técnica: O Guia do Desenvolvedor**

A seguir, apresenta-se a lógica detalhada para a implementação da ferramenta CLI, integrando as APIs do OpenAlex e a inteligência do LLM.

### **4.1 Setup do Ambiente e Dependências**

A ferramenta deve ser construída sobre o Python 3.10+, utilizando um ambiente virtual (venv) para isolamento. As bibliotecas essenciais incluem:

* click: Interface de linha de comando.  
* aiohttp: Cliente HTTP assíncrono.  
* pydantic: Validação de dados e esquemas JSON.  
* openai: Cliente da API de IA.  
* pandas: Manipulação eficiente do CSV de entrada/saída.  
* rich: Para barras de progresso visuais e formatação de logs no terminal.  
* tenacity: Para implementação robusta de lógica de retry.21

### **4.2 Fluxo de Código (Pseudocódigo Narrativo)**

O núcleo da aplicação (main.py) orquestra a leitura do arquivo e a distribuição de tarefas. O uso de asyncio.gather permite lançar lotes de tarefas (ex: 50 por vez) para o pool de conexões.

**Componente 1: O Buscador (Searcher)** A função de busca deve encapsular a lógica de "Polite Pool". Ao instanciar o aiohttp.ClientSession, deve-se injetar o cabeçalho User-Agent: my-tool/1.0 (mailto:meu\_email@dominio.com). Isso garante acesso privilegiado à API do OpenAlex. A busca deve priorizar o endpoint /works se o título do artigo estiver disponível, pois o link Autor-Obra é mais forte que o link Nome-Autor. Se o título não estiver disponível, o fallback é o endpoint /authors com filtros de afiliação.4

**Componente 2: O Filtro Inteligente**

Antes de gastar tokens com IA, o script deve tentar resolver a identidade localmente. Se o OpenAlex retornar um único candidato com score de confiança alto e afiliação correspondente (fuzzy match \> 90%), o script aceita o ORCID e segue para o próximo. Isso economiza chamadas de API de IA e acelera o processo.

**Componente 3: O Integrador de IA** Para os casos que falham no filtro local, o script constrói o payload para a API da OpenAI. Se a opção \--batch estiver ativa na CLI, o script não aguarda a resposta; ele grava a requisição em um arquivo .jsonl local. Ao final do processamento do CSV, este arquivo é enviado para a OpenAI Batch API. Um segundo comando CLI (ex: orcid-miner retrieve-batch) seria usado no dia seguinte para baixar os resultados e fundi-los ao CSV original.31

### **4.3 Tratamento de Erros e Resiliência**

Em um lote de 2.000 registros, anomalias de dados são certas (ex: nomes nulos, caracteres invisíveis). O script deve implementar validação defensiva com Pydantic para descartar ou logar linhas inválidas sem interromper o processo global. Um arquivo de log (processing.log) deve registrar cada decisão tomada (ex: "Autor X vinculado ao ORCID Y via OpenAlex (Score 0.95)" ou "Autor Z enviado para desambiguação via IA").

## ---

**5\. Análise de Resultados e Limitações Estruturais**

A aplicação desta arquitetura em dados reais de seminários revela padrões importantes sobre a disponibilidade de identificadores.

### **5.1 Expectativas de Cobertura**

A taxa de sucesso (Recall) da recuperação de ORCIDs varia drasticamente por disciplina. Em áreas de STEM (Ciências, Tecnologia, Engenharia e Matemática), onde a adoção do ORCID é madura e impulsionada por mandatos de financiadores, a taxa de recuperação automática pode superar 80%. Em Humanidades e Ciências Sociais, onde a cultura de identificadores persistentes é mais recente, a taxa pode cair para 40-50%, exigindo maior intervenção manual ou aceitação de incompletude.33

É crucial alinhar as expectativas: a automação não cria dados. Se um autor nunca criou um ORCID ou nunca o vinculou a uma publicação indexada, nenhuma IA poderá "descobrir" esse identificador, pois ele não existe no grafo de conhecimento público. O objetivo da ferramenta é maximizar a recuperação dos identificadores *existentes mas ocultos* pela ambiguidade.

### **5.2 O Fenômeno das "Alucinações de Identidade"**

Um risco inerente ao uso de LLMs é a alucinação, onde o modelo, forçado a escolher um candidato, seleciona um incorreto com alta confiança aparente. Para mitigar isso, o parâmetro temperature do modelo deve ser configurado para 0 (zero), maximizando o determinismo. Além disso, a CLI deve incluir uma flag \--threshold (limiar), onde apenas correspondências com confiança \> 0.85 são aceitas automaticamente. Correspondências com confiança marginal (0.5 \- 0.85) devem ser marcadas no CSV de saída como "Requer Revisão Humana".35

### **5.3 Considerações Éticas e Termos de Uso**

A raspagem de dados (scraping) de interfaces web (como perfis do Google Scholar) é uma violação de termos de serviço e propensa a bloqueios. A arquitetura proposta neste relatório baseia-se estritamente no uso de APIs públicas documentadas (OpenAlex, Crossref, ORCID) e respeita as políticas de uso aceitável através de rate limiting e identificação via e-mail. A privacidade dos autores também é respeitada, pois a ferramenta agrega apenas dados já tornados públicos em repositórios científicos, sem inferir dados sensíveis privados.36

## ---

**Conclusão e Roteiro de Implementação**

A automação da busca de ORCIDs para listas extensas de autores de seminários é um problema solucionável através da convergência de engenharia de dados moderna e inteligência artificial. A dependência exclusiva de busca manual ou scripts simples de correspondência de nomes é insustentável na escala atual da produção científica.

A solução recomendada é híbrida: utilizar o **OpenAlex** como a espinha dorsal de dados devido à sua capacidade de agregação e permissividade de API, e empregar **LLMs (via Batch API)** como a camada cognitiva para resolver as ambiguidades inerentes à natureza humana dos nomes. A implementação via **CLI Python assíncrona** garante que o processo seja reprodutível, auditável e escalável, transformando uma tarefa que levaria semanas de trabalho manual em um processo computacional de poucas horas e custo marginal.

Para o pesquisador ou engenheiro de dados encarregado desta tarefa, o próximo passo é a prototipagem do script seguindo a arquitetura de "Semáforos e Filas" descrita, iniciando com um subconjunto de dados (ex: 50 nomes) para calibrar os prompts do LLM e os limiares de confiança antes de executar a carga total de 2.000 autores.

## ---

**Tabelas de Referência Técnica**

### **Comparativo de Custos e Modelos de IA para Desambiguação**

| Modelo IA | Custo Entrada (1M tokens) | Custo Saída (1M tokens) | Capacidade de Raciocínio | Recomendação de Uso |
| :---- | :---- | :---- | :---- | :---- |
| **GPT-4o** | $5.00 ($2.50 Batch) | $15.00 ($7.50 Batch) | Muito Alta (Complexa) | Apenas conflitos difíceis |
| **GPT-4o-mini** | $0.15 ($0.075 Batch) | $0.60 ($0.30 Batch) | Alta (Eficiente) | **Padrão para normalização** |
| **o1-mini** | $3.00 | $12.00 | Raciocínio (Reasoning) | Casos extremos de homonímia |

Nota: Preços estimados baseados na tabela da OpenAI (Fev 2026), sujeitos a alteração. A Batch API oferece 50% de desconto sobre os preços listados.28

### **Estratégia de Rate Limiting por API**

| API | Limite Gratuito Padrão | Limite "Polite Pool" (com E-mail) | Estratégia de Backoff Sugerida |
| :---- | :---- | :---- | :---- |
| **OpenAlex** | Variável / Baixo | 100.000 req/dia, \~10 req/s | Linear (1s, 2s, 3s) |
| **Crossref** | Compartilhado (Lento) | Pool Dedicado (Rápido) | Exponencial (2s, 4s, 8s) |
| **ORCID Public** | \~12-24 req/s (Burst 40\) | Mesmo limite, mas necessário token | Agressivo (Parar por 1 min se 429\) |
| **Semantic Scholar** | 100 req/5 min | Requer API Key para aumento | Exponencial com Jitter |

Fontes de dados para limites:.16

#### **Referências citadas**

1. Exploring Graph Based Approaches for Author Name Disambiguation | by Eleventh Hour Enthusiast | Medium, acessado em fevereiro 12, 2026, [https://medium.com/@EleventhHourEnthusiast/exploring-graph-based-approaches-for-author-name-disambiguation-0b6180660a2d](https://medium.com/@EleventhHourEnthusiast/exploring-graph-based-approaches-for-author-name-disambiguation-0b6180660a2d)  
2. Deep Author Name Disambiguation using DBLP Data | by Eleventh Hour Enthusiast, acessado em fevereiro 12, 2026, [https://medium.com/@EleventhHourEnthusiast/deep-author-name-disambiguation-using-dblp-data-bf37a86a9a6b](https://medium.com/@EleventhHourEnthusiast/deep-author-name-disambiguation-using-dblp-data-bf37a86a9a6b)  
3. API Tutorial: Searching the ORCID registry, acessado em fevereiro 12, 2026, [https://info.orcid.org/documentation/api-tutorials/api-tutorial-searching-the-orcid-registry/](https://info.orcid.org/documentation/api-tutorials/api-tutorial-searching-the-orcid-registry/)  
4. Authors \- OpenAlex technical documentation, acessado em fevereiro 12, 2026, [https://docs.openalex.org/api-entities/authors](https://docs.openalex.org/api-entities/authors)  
5. Author disambiguation \- OpenAlex Support, acessado em fevereiro 12, 2026, [https://help.openalex.org/hc/en-us/articles/24347048891543-Author-disambiguation](https://help.openalex.org/hc/en-us/articles/24347048891543-Author-disambiguation)  
6. Announcing the New OpenAlex Author Data \- Google Groups, acessado em fevereiro 12, 2026, [https://groups.google.com/g/openalex-users/c/jzlh1Mp\_s-g](https://groups.google.com/g/openalex-users/c/jzlh1Mp_s-g)  
7. Search authors | OpenAlex technical documentation, acessado em fevereiro 12, 2026, [https://docs.openalex.org/api-entities/authors/search-authors](https://docs.openalex.org/api-entities/authors/search-authors)  
8. Author object | OpenAlex technical documentation, acessado em fevereiro 12, 2026, [https://docs.openalex.org/api-entities/authors/author-object](https://docs.openalex.org/api-entities/authors/author-object)  
9. ORCID auto-update \- Crossref, acessado em fevereiro 12, 2026, [https://www.crossref.org/community/orcid/](https://www.crossref.org/community/orcid/)  
10. REST API \- Crossref, acessado em fevereiro 12, 2026, [https://www.crossref.org/documentation/retrieve-metadata/rest-api/](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)  
11. Getting ORCIDs by DOI \- Academia Stack Exchange, acessado em fevereiro 12, 2026, [https://academia.stackexchange.com/questions/79941/getting-orcids-by-doi](https://academia.stackexchange.com/questions/79941/getting-orcids-by-doi)  
12. Tutorial | Semantic Scholar Academic Graph API, acessado em fevereiro 12, 2026, [https://www.semanticscholar.org/product/api%2Ftutorial](https://www.semanticscholar.org/product/api%2Ftutorial)  
13. Academic Graph API \- Semantic Scholar API, acessado em fevereiro 12, 2026, [https://api.semanticscholar.org/api-docs/](https://api.semanticscholar.org/api-docs/)  
14. argparse \- Click Documentation, acessado em fevereiro 12, 2026, [https://click.palletsprojects.com/en/stable/why/](https://click.palletsprojects.com/en/stable/why/)  
15. Click vs argparse \- Which CLI Package is Better? \- Python Snacks, acessado em fevereiro 12, 2026, [https://www.pythonsnacks.com/p/click-vs-argparse-python](https://www.pythonsnacks.com/p/click-vs-argparse-python)  
16. openalex-docs/how-to-use-the-api/rate-limits-and-authentication.md at main \- GitHub, acessado em fevereiro 12, 2026, [https://github.com/ourresearch/openalex-docs/blob/main/how-to-use-the-api/rate-limits-and-authentication.md](https://github.com/ourresearch/openalex-docs/blob/main/how-to-use-the-api/rate-limits-and-authentication.md)  
17. What are the API usage quotas and limits? \- ORCID, acessado em fevereiro 12, 2026, [https://info.orcid.org/ufaqs/what-are-the-api-limits/](https://info.orcid.org/ufaqs/what-are-the-api-limits/)  
18. Clarification of rate limits in v3.0 \- Google Groups, acessado em fevereiro 12, 2026, [https://groups.google.com/g/orcid-api-users/c/ehv8sCfs-ZM](https://groups.google.com/g/orcid-api-users/c/ehv8sCfs-ZM)  
19. Parallelize openalex API \- python \- Stack Overflow, acessado em fevereiro 12, 2026, [https://stackoverflow.com/questions/74638799/parallelize-openalex-api](https://stackoverflow.com/questions/74638799/parallelize-openalex-api)  
20. Best strategy on managing concurrent calls ? (Python/Asyncio) \- API, acessado em fevereiro 12, 2026, [https://community.openai.com/t/best-strategy-on-managing-concurrent-calls-python-asyncio/849702](https://community.openai.com/t/best-strategy-on-managing-concurrent-calls-python-asyncio/849702)  
21. How To Implement API Rate Limiting and Avoid 429 Too Many Requests \- Geoapify, acessado em fevereiro 12, 2026, [https://www.geoapify.com/how-to-avoid-429-too-many-requests-with-api-rate-limiting/](https://www.geoapify.com/how-to-avoid-429-too-many-requests-with-api-rate-limiting/)  
22. I am trying to use asyncio for millions of API requests but cannot add rate limit \- Reddit, acessado em fevereiro 12, 2026, [https://www.reddit.com/r/learnpython/comments/uxvyj4/i\_am\_trying\_to\_use\_asyncio\_for\_millions\_of\_api/](https://www.reddit.com/r/learnpython/comments/uxvyj4/i_am_trying_to_use_asyncio_for_millions_of_api/)  
23. Production-Grade Bulk API Processing with Python \- Rob Johnson, acessado em fevereiro 12, 2026, [https://www.robkjohnson.com/posts/production-grade-bulk-api-processing-python/](https://www.robkjohnson.com/posts/production-grade-bulk-api-processing-python/)  
24. Author Name Disambiguation using Large Language Models | TU Delft Repository, acessado em fevereiro 12, 2026, [https://repository.tudelft.nl/record/uuid:c7e98b04-b127-4c02-a6c1-e250ae5b0566](https://repository.tudelft.nl/record/uuid:c7e98b04-b127-4c02-a6c1-e250ae5b0566)  
25. Scholar Name Disambiguation with Search-enhanced LLM Across Language \- arXiv, acessado em fevereiro 12, 2026, [https://arxiv.org/html/2411.17102v1](https://arxiv.org/html/2411.17102v1)  
26. LEAD: LLM-enhanced Engine for Author Disambiguation \- arXiv, acessado em fevereiro 12, 2026, [https://arxiv.org/pdf/2511.07168](https://arxiv.org/pdf/2511.07168)  
27. LEAD: LLM-enhanced Engine for Author Disambiguation \- arXiv, acessado em fevereiro 12, 2026, [https://arxiv.org/html/2511.07168v1](https://arxiv.org/html/2511.07168v1)  
28. Pricing | OpenAI API, acessado em fevereiro 12, 2026, [https://developers.openai.com/api/docs/pricing/](https://developers.openai.com/api/docs/pricing/)  
29. API Pricing \- OpenAI, acessado em fevereiro 12, 2026, [https://openai.com/api/pricing/](https://openai.com/api/pricing/)  
30. How to use global batch processing with Azure OpenAI in Microsoft Foundry Models, acessado em fevereiro 12, 2026, [https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/batch?view=foundry-classic](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/batch?view=foundry-classic)  
31. Batch API \- OpenAI for developers, acessado em fevereiro 12, 2026, [https://developers.openai.com/api/docs/guides/batch/](https://developers.openai.com/api/docs/guides/batch/)  
32. Get all works of a particular author without ORCID \- Crossref community forum, acessado em fevereiro 12, 2026, [https://community.crossref.org/t/get-all-works-of-a-particular-author-without-orcid/3751](https://community.crossref.org/t/get-all-works-of-a-particular-author-without-orcid/3751)  
33. Reference Coverage Analysis of OpenAlex compared to Web of Science and Scopus \- arXiv, acessado em fevereiro 12, 2026, [https://arxiv.org/html/2401.16359v1](https://arxiv.org/html/2401.16359v1)  
34. Reference Coverage Analysis of OpenAlex compared to Web of Science and Scopus \- arXiv, acessado em fevereiro 12, 2026, [https://arxiv.org/abs/2401.16359](https://arxiv.org/abs/2401.16359)  
35. Large language models can extract metadata for annotation of human neuroimaging publications \- PMC, acessado em fevereiro 12, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC12405296/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12405296/)  
36. Repository Systems \- ORCID \- Connecting research and researchers, acessado em fevereiro 12, 2026, [https://info.orcid.org/documentation/workflows/repository-systems/](https://info.orcid.org/documentation/workflows/repository-systems/)  
37. ropensci/openalexR: Getting bibliographic records from OpenAlex \- GitHub, acessado em fevereiro 12, 2026, [https://github.com/ropensci/openalexR](https://github.com/ropensci/openalexR)  
38. Blog \- Announcing changes to REST API rate limits \- Crossref, acessado em fevereiro 12, 2026, [https://www.crossref.org/blog/announcing-changes-to-rest-api-rate-limits/](https://www.crossref.org/blog/announcing-changes-to-rest-api-rate-limits/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAXCAYAAADpwXTaAAAAbElEQVR4XmNgGAWjgKogAF2AErABiAXRBckFLkBcgS5ICegBYit0QXIBMxCvBOJKIGZFllgIxLvJwBeA+B0QJzJQCESBeD0Qi6FLkAqYgHgrEEuiS5ADgoE4Gl2QXADyHkqgUwL00AVGwSAAAG69EzceZiPbAAAAAElFTkSuQmCC>