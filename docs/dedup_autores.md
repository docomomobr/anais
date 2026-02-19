# Pipeline de Deduplicação de Autores

## Visão geral

Autores aparecem com variantes de nome nos YAMLs (abreviações, partículas, typos, familyname incluindo sobrenomes intermediários). O pipeline reduz duplicatas em etapas progressivas, da mais segura à mais agressiva. Etapas automáticas primeiro, LLM depois, humano por último.

Resultado na primeira rodada: 2535 → 2019 autores (-516, 20%).

## Pré-requisito

Banco `anais.db` populado via `init_anais_db.py` + `import_yaml_to_db.py`.

## Etapas (em ordem)

### Etapas automáticas (ordem de confiança decrescente)

#### 1. Enriquecimento via Pilotis (fase 0)

- Cruza email dos autores com `pilotis.db` (sistema financeiro Docomomo)
- Pilotis tem nomes completos em campo único `nome`
- Se email bate mas nome no Pilotis é mais completo, atualiza givenname
- Se atualizar criaria UNIQUE conflict, faz merge em vez de update
- Resultado: ~15 nomes enriquecidos

#### 2. Duplicatas exatas por normalização

- Normaliza nome completo: lowercase, remove acentos (NFKD), junta givenname+familyname
- Agrupa nomes idênticos após normalização
- Pega: acentos diferentes (Cecilia/Cecília), givenname contém parte do familyname
- Ex: "Ana Gabriela Godinho | Lima" = "Ana Gabriela | Godinho Lima"
- **Mais segura e maior volume** — deve rodar cedo para limpar o terreno
- Resultado: ~204 merges (maior etapa!)

#### 3. Auto-merge por abreviação/prefixo

- Agrupa por familyname idêntico
- Para cada par, verifica se um givenname é abreviação do outro:
  - Palavra por palavra: "L." matches "Luiz", "Renato" matches "Renato"
  - Todas as palavras do menor devem ser prefixo/inicial de alguma palavra do maior
- Confiança "alta" se o nome curto tem ≥2 palavras reais (>2 chars, não partícula)
- Auto-merge apenas dos "alta confiança"
- Funciona melhor com nomes já normalizados pela etapa 2
- Resultado: ~70 merges

#### 4. Normalização de partículas no familyname

- Compara autores cujo familyname difere apenas por partícula (da/de/do/dos/das)
- Ex: "Silva" vs "da Silva", "Castro" vs "de Castro"
- Filtra por mesmo primeiro nome real para evitar falsos positivos
- Também pega typos no givenname (Binato/Binatto)
- Complementa a normalização da etapa 2
- Resultado: ~2 merges (a maioria já pega pela etapa 2)

#### 5. Primeiro nome + familyname (variantes de givenname)

- Busca: mesmo primeiro nome real + mesmo familyname, givenname diferente
- Pega casos que a etapa 3 não pegou (baixa confiança, ou givenname com formatação diferente)
- Inclui typos no givenname intermediário (Beisl/Beisi, Nassaralla/Nasralla, Fernandes/Fernandez)
- Resultado: ~27 merges

#### 6. Iniciais → nome completo

- Agrupa por familyname normalizado
- Para cada par, identifica qual tem iniciais (1-2 chars) e qual tem nomes completos
- Verifica que as iniciais do "short" batem com as palavras do "long", em ordem
- **Primeira inicial DEVE bater com primeiro nome** (sem pular) — evita falsos positivos
- Ex: "D. M. | Macedo" → "Danilo Matoso | Macedo" (D=Danilo, M=Matoso)
- Ex: "Celia C. | Gonsales" → "Célia Helena Castro | Gonsales" (C=Castro)
- Pega poucos casos porque as etapas 2-5 já resolvem a maioria das abreviações
- Resultado: ~3 merges

#### 7. Cross-familyname (subset de palavras)

- Agrupa por primeiro nome real (>3 chars)
- Para cada par com familyname diferente, extrai palavras reais de todo o nome
- Se as palavras do menor estão todas contidas no maior (e ≥2 palavras):
  - Ex: {alcilia, afonso} ⊂ {alcilia, afonso, albuquerque, melo}
- Canônico = mais artigos ou nome mais longo
- **Excluir falsos positivos**: nomes genéricos (Maria + Machado), pai/filho (Campos/Campos Neto)
- SKIP_PAIRS para pares conhecidamente diferentes
- Também pega familyname diferente por split (Huapaya vs Huapaya Espinoza)
- Resultado: ~82 merges

#### 8. Coautores em comum

- Para cada par de autores com ≥2 palavras em comum no nome completo
- Verifica se compartilham coautores (mesmos artigos com outros autores)
- Sinal mais poderoso na literatura de desambiguação (AND)
- Cuidado: coautor em comum pode ser orientador — não é prova isolada
- Confirmar que Eloane ≠ Eliane (coautoras no mesmo artigo = diferentes!)
- Resultado: ~3 merges

#### 9. Afiliação em comum

- Para cada par de candidatos das etapas 7-8 ainda não resolvidos (e os ambíguos da fase 3)
- Compara afiliação (`article_author.affiliation`) dos dois autores
- Mesma afiliação + nomes compatíveis = forte indicativo de mesma pessoa
- Afiliação diferente não descarta (pessoa muda de instituição), mas reduz confiança
- Útil especialmente para nomes com familyname diferente (casamento, nome abreviado)
- Ex: "Paula Maciel" (UNICAP, sdnne01) = "Paula Maciel Silva" (UNICAP, sdnne08) — mesma afiliação confirmou merge
- Dados de afiliação variam: podem estar no YAML, no PDF, ou ausentes. Nem sempre disponível
- Resultado: complementar às etapas 7-8 (resolve casos que ficaram ambíguos)

### Etapas com LLM

#### 10. Revisão por LLM

- Recebe os casos de baixa confiança (da etapa 2) e os pares duvidosos das etapas 4-9
- Sub-agrupa por first_two_real_words para separar pessoas diferentes no mesmo familyname
- LLM analisa: temas dos artigos, coautores, afiliações, período temporal
- Identifica falsos positivos (ex: Ana Gabriela ≠ Ana Laura ≠ Ana Carolina, todas Lima)
- Aplica merges claros, lista incertos para revisão humana
- Pode consultar Lattes/Google Scholar/ORCID para desambiguar
- Resultado: ~100 merges

### Etapas manuais (humano)

#### 11. Resolução manual de casos específicos

- Casos que nem LLM resolve: pai/filho, homônimos, nomes genéricos
- Pai/filho (Andrey Rosenthal Schlee vs Andrey de Aspiazu Schlee) — NÃO mergear
- Pesquisa Lattes para desambiguar (ex: Ana Lima — inconclusivo, mantida separada)
- Consulta direta ao autor quando possível (Ana Gabriela confirmou que sdbr02-018 NÃO é dela)

## Ordem de execução

```bash
python3 scripts/init_anais_db.py
python3 scripts/import_yaml_to_db.py
python3 scripts/dedup_authors.py          # etapas 1-9 (automáticas)
# Etapa 10: revisão LLM dos casos ambíguos
# Etapa 11: resolução manual dos casos restantes
python3 scripts/dump_anais_db.py
```

## Regras importantes

- **Sempre registrar variantes** em `author_variants` antes de mergear
- **Enriquecer email/orcid** do canônico se a variante tem e o canônico não
- **Mover author_variants** do deletado para o canônico (FK constraint)
- **UPDATE OR IGNORE** nos article_author (evita PK duplicada se ambos no mesmo artigo)
- **DELETE restos** de article_author e author_variants antes de deletar o autor
- **Junior/Filho/Neto** são sufixos, não familyname separado — cuidado com pai/filho
- **Hispânicos** (duplo sobrenome): Vázquez Ramos, não mergear com só "Ramos"
- **Alcília** é exemplo de caso complexo: Melo vs Costa (casamento?), com/sem "e", typo "Aluquerque"

## Falsos positivos conhecidos

| Par | Motivo |
|-----|--------|
| Andrey Rosenthal Schlee ↔ Andrey de Aspiazu Schlee | Pai e filho, coautores em sdsul07-012 |
| Ana Gabriela Godinho Lima ↔ Ana Laura Godinho Lima | Irmãs(?), coautoras em sdsp03-049 |
| Ana Carolina Gleria Lima ≠ Ana Gabriela/Ana Laura | Pessoa diferente, Ribeirão Preto |
| Ana Lima (sdbr02-018) | Não é Ana Gabriela (confirmado pela própria) |
| Candido Malta Campos ↔ Campos Neto | Possivelmente avô/neto |
| Maria V. S. Machado ≠ Maria Beatriz P. Machado | Iniciais diferentes = pessoas diferentes |
| Eloane de Jesus Ramos Cantuária ↔ Eliane Ramos Cantuária | Coautoras no mesmo artigo (sdnne05), nomes diferentes (Eloane ≠ Eliane) |

## Métricas de referência

| Métrica | Valor |
|---------|-------|
| Autores brutos (import) | 2535 + 110 (sdnne10) + 150 (sdnne01+03) |
| Após dedup completa | 2218 |
| Redução | ~22% |
| Variantes registradas | 898 |
| Vínculos preservados | 4155 |
| Top autor | Alcília Afonso (35 arts) |
