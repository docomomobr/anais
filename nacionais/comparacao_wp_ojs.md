# Comparação WordPress vs OJS - Seminários Nacionais Docomomo Brasil

Data: 2026-01-14

## Resumo Geral

| Seminário | WordPress | OJS/YAML | Diferença | Status |
|-----------|-----------|----------|-----------|--------|
| sdbr01 | 1* | 7 | - | ⚠️ WP só tem livro |
| sdbr02 | 1* | 24 | - | ⚠️ WP só tem livro |
| sdbr03 | 57 | 56 | +1 | ≈ OK |
| sdbr04 | 0* | 79 | - | ⚠️ WP sem artigos |
| sdbr05 | 61 | 56 | +5 | ❓ Verificar |
| sdbr06 | 64 | 64 | 0 | ✅ OK |
| sdbr07 | 70 | 62 | +8 | ❌ 8 faltando no OJS |
| sdbr08 | 193 | 184 | +9 | ❌ Verificar |
| sdbr09 | 171 | 170 | +1 | ≈ OK |
| sdbr10 | 119 | 118 | +1 | ≈ OK |
| sdbr11 | 0* | 101 | - | ⚠️ WP sem artigos |
| sdbr12 | 0* | 0 | 0 | ⚠️ Sem anais |
| sdbr13 | 181 | 181 | 0 | ✅ OK |
| sdbr14 | 122 | 122 | 0 | ✅ OK |
| sdbr15 | 102 | 101 | +1 | ❌ 1 faltando no OJS |

\* Seminários onde o WordPress não tem lista de artigos individuais (apenas informações gerais ou livro único)

---

## Análise por Seminário

### Seminários com correspondência exata (✅)
- **sdbr06** (Niterói 2005): 64 = 64
- **sdbr13** (Salvador 2019): 181 = 181
- **sdbr14** (Belém 2021): 122 = 122

### Seminários aproximadamente OK (≈)
- **sdbr03** (São Paulo 1999): WP tem 57, OJS tem 56 (diferença de 1)
- **sdbr09** (Brasília 2011): WP tem 171, OJS tem 170 (diferença de 1)
- **sdbr10** (Curitiba 2013): WP tem 119, OJS tem 118 (diferença de 1)

### Seminários com artigos faltando no OJS (❌)

#### sdbr07 (Porto Alegre 2007): 8 artigos faltando no OJS
1. A Praça do maquis.
2. A praça e a piazza: Transitoriedade e permanência no esquema clássico de cidade.
3. Centro de convicência Djalma Marinho – UFRN. A "sobrevida" de uma obra da arquitetura moderna em Natal.
4. José de Souza Reis e o SPHAN: da inconfidência à glória
5. A modernidade figurativa da Casa Curutchet
6. Cinqüenta anos depois: a atuação do Ipesp e dos arquitetos modernos paulistas na construção de edifícios escolares em São Paulo de 1959 – 1962
7. El Palacio de Congresos, um tipo del siglo XX
8. Conservação e requalificação de grandes conjuntos habitacionais modernistas: Reflexões sobre a experiência escandinava recente

#### sdbr05 (São Carlos 2003): ~5 artigos a verificar
WordPress tem 61, OJS tem 56.

#### sdbr08 (Rio de Janeiro 2009): ~9 artigos a verificar
Artigos identificados faltando:
1. Arquitetura, historiografia e historia operativa nos anos 1960
2. Cartas da America: arquitetura e modernidade
3. R E C O N S T R U I N D O C A J U E I R O S E C O : Arquitetura, política social e cultura popular em Pernambuco (1960-64)

### Seminários sem lista de artigos no WordPress (⚠️)

#### sdbr01 (Salvador 1995) e sdbr02 (Salvador 1997)
O WordPress contém apenas o livro de anais completo em PDF único, não artigos individuais.

#### sdbr04 (Viçosa 2001)
O Course contém apenas informações gerais sobre o seminário (chamada de trabalhos, subtemas), sem lista de artigos.

#### sdbr11 (Recife 2016)
O Course existe mas não tem lista de artigos com PDFs.

#### sdbr12 (Uberlândia 2017)
Seminário ainda não migrado para OJS. ISBN: 978-85-64554-03-0

#### sdbr15 (São Paulo 2024)
Não existe como Course no WordPress. Os 101 artigos no OJS vieram de outra fonte.

---

## Conclusões

1. **Correspondência exata**: 3 seminários (sdbr06, sdbr13, sdbr14)
2. **Aproximadamente OK**: 3 seminários (sdbr03, sdbr09, sdbr10) - diferenças de apenas 1 artigo
3. **Artigos faltando no OJS**: Pelo menos 8 artigos identificados no sdbr07, verificar sdbr05 e sdbr08
4. **WordPress incompleto**: Vários seminários (01, 02, 04, 11, 15) não têm lista de artigos no WordPress

## Próximos Passos

1. [ ] Adicionar ao OJS os 8 artigos identificados do sdbr07
2. [ ] Fazer comparação detalhada título a título do sdbr05 e sdbr08
3. [ ] Verificar se os artigos do sdbr01, sdbr02, sdbr04, sdbr11 e sdbr15 têm outra fonte
4. [ ] Migrar anais do sdbr12 (Uberlândia 2017) quando disponível
