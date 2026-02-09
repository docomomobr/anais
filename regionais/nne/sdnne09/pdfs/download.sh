#!/bin/bash
# Download PDFs do 9º Seminário Docomomo N/NE - São Luís (2022)
# Fonte: https://www.docomomobrasil.com

BASE="https://www.docomomobrasil.com"
DIR="/home/danilomacedo/Dropbox/docomomo/26-27/site/migracao/nne/sdnne09/pdfs"
cd "$DIR"

# Função para normalizar nome de arquivo
normalize_name() {
    local name="$1"
    # Converte para minúsculas e remove acentos
    name=$(echo "$name" | tr '[:upper:]' '[:lower:]')
    name=$(echo "$name" | sed '
        s/[áàâãä]/a/g
        s/[éèêë]/e/g
        s/[íìîï]/i/g
        s/[óòôõö]/o/g
        s/[úùûü]/u/g
        s/ç/c/g
        s/ñ/n/g
    ')
    # Remove caracteres especiais
    name=$(echo "$name" | tr -cd 'a-z0-9_-')
    # Remove underscores/hífens duplicados
    name=$(echo "$name" | sed 's/__*/_/g; s/--*/-/g; s/_-/-/g; s/-_/-/g')
    # Remove underscore/hífen no início ou fim
    name=$(echo "$name" | sed 's/^[_-]//; s/[_-]$//')
    echo "$name"
}

# Função para truncar nome (max 6 palavras)
truncate_name() {
    local name="$1"
    local max=6
    local words=$(echo "$name" | tr '_-' '\n' | head -n $max | tr '\n' '_')
    echo "${words%_}"
}

# Lista de URLs e nomes curtos
declare -A ARTICLES
ARTICLES["01"]="/wp-content/uploads/2022/06/A-CONTRIBUICAO-DO-ENGENHEIRO-FREITAS-DINIZ-PARA-O-CONSTRUCAO-DA-CIDADE-MODERNA-DE-SAO-LUIS-%E2%80%93-MA-1.pdf|contribuicao_engenheiro_freitas_diniz_sao_luis"
ARTICLES["02"]="/wp-content/uploads/2022/06/ACACIO-GIL-BORSOI-E-SUA-PRODUCAO-ARQUITETONICA-MODERNA-EM-TERESINA.pdf|acacio_gil_borsoi_teresina"
ARTICLES["03"]="/wp-content/uploads/2022/06/ADAPTABILIDADE-DE-SOLUCOES-PROJETUAIS-TRAZIDAS-POR-IMIGRANTES-JAPONESES-A-AMAZONIA-AMAPAENSE-NO-PERIODO-MODERNO-JANARISTA.pdf|adaptabilidade_solucoes_imigrantes_japoneses_amazonia"
ARTICLES["04"]="/wp-content/uploads/2022/06/ANTIGA-RECEITA-FEDERAL-DE-CUIABA.pdf|antiga_receita_federal_cuiaba"
ARTICLES["05"]="/wp-content/uploads/2022/06/ARQUITETURA-E-ICONOGRAFIA.pdf|arquitetura_e_iconografia_teresina"
ARTICLES["06"]="/wp-content/uploads/2022/06/BINA-FONYAT.pdf|bina_fonyat"
ARTICLES["07"]="/wp-content/uploads/2022/06/CLORINDO-TESTA.pdf|clorindo_testa_primeiros_anos"
ARTICLES["08"]="/wp-content/uploads/2022/06/CONEXOES-ARQUITETONICAS-MODERNAS-RECIFENSES-EM-CAMPINA-GRANDEPARAIBA.pdf|conexoes_arquitetonicas_recifenses_campina_grande"
ARTICLES["09"]="/wp-content/uploads/2022/06/DEPOIS-DO-PILOTIS.pdf|depois_do_pilotis"
ARTICLES["10"]="/wp-content/uploads/2022/06/ENTRE-O-PREFABRICADO-E-O-PREEXISTENTE.pdf|entre_prefabricado_preexistente_cuiaba"
ARTICLES["11"]="/wp-content/uploads/2022/06/INFLUENCIA-DA-MEDICINA-E-DA-HIGIENE-NA-ARQUITETURA-MODERNA-EUROPEIA-DO-SECULO-XX.pdf|influencia_medicina_higiene_arquitetura"
ARTICLES["12"]="/wp-content/uploads/2022/06/INTERPRETACOES-DA-HISTORIA-DO-LUGAR.pdf|interpretacoes_historia_goiania"
ARTICLES["13"]="/wp-content/uploads/2022/06/MODERNIDADES-VERNACULARES.pdf|modernidades_vernaculares_maranhao"
ARTICLES["14"]="/wp-content/uploads/2022/06/MODERNO-E-EFICIENTE.pdf|moderno_eficiente_fortaleza"
ARTICLES["15"]="/wp-content/uploads/2022/06/MULHERES-MODERNAS.pdf|mulheres_modernas_sao_luis"
ARTICLES["16"]="/wp-content/uploads/2022/06/NAVEGANDO-NO-PARAISO.pdf|navegando_paraiso_casa_douglas"
ARTICLES["17"]="/wp-content/uploads/2022/06/NORDESTE-NA-HISTORIOGRAFIA-DA-ARQUITETURA-BRASILEIRA.pdf|nordeste_historiografia_arquitetura"
ARTICLES["18"]="/wp-content/uploads/2022/06/O-AEROPORTO-SCHIPOL-E-MARIUS-DUINTJER.pdf|aeroporto_schiphol_marius_duintjer"
ARTICLES["19"]="/wp-content/uploads/2022/06/O-BRASIL-EM-BRASILIA.pdf|brasil_em_brasilia_unb"
ARTICLES["20"]="/wp-content/uploads/2022/06/O-EDIFICIO-PIEDADE-DO-ENGENHEIRO-JUDAH-LEVY-EM-BELEM.pdf|edificio_piedade_judah_levy_belem"
ARTICLES["21"]="/wp-content/uploads/2022/06/O-MODERNISMO-CEARENSE-NO-FEMININO.pdf|modernismo_cearense_nelia_romero"
ARTICLES["22"]="/wp-content/uploads/2022/06/O-SERTAO-TAMBEM-E-MODERNO.pdf|sertao_moderno_sesi_crato"
ARTICLES["23"]="/wp-content/uploads/2022/06/OBITUARIO-DIGITAL-DA-ARQUITETURA-MODERNA-EM-FORTALEZA.pdf|obituario_digital_fortaleza_borsoi"
ARTICLES["24"]="/wp-content/uploads/2022/06/PALACIO-DA-ALVORADA.pdf|palacio_alvorada"
ARTICLES["25"]="/wp-content/uploads/2022/06/REGINALDO-ESTEVES-E-A-CONSTRUCAO-TECTONICA.pdf|reginaldo_esteves_construcao_tectonica"
ARTICLES["26"]="/wp-content/uploads/2022/06/TAO-LONGE-TAO-PERTO.pdf|tao_longe_tao_perto_nicia_bormann"
ARTICLES["27"]="/wp-content/uploads/2022/06/ADAPTACOES-E-DESCARACTERIZACOES-DOS-PREDIOS-MODERNOS-PARA-NOVOS-USOS.pdf|adaptacoes_descaracterizacoes_bequimao"
ARTICLES["28"]="/wp-content/uploads/2022/06/AMARO-FIUZA.pdf|amaro_fiuza_campina_grande"
ARTICLES["29"]="/wp-content/uploads/2022/06/ARQUITETURA-CIVICA-DOS-ANOS-30-E-40.pdf|arquitetura_civica_anos_30_40_mato_grosso"
ARTICLES["30"]="/wp-content/uploads/2022/06/ARQUITETURA-ESCOLA-MODERNA-E-SAUDE.pdf|arquitetura_escolar_moderna_saude"
ARTICLES["31"]="/wp-content/uploads/2022/06/ARQUITETURA-MODERNA-DO-SECULO-XX-EM-SAO-LUIS.pdf|arquitetura_moderna_seculo_xx_sao_luis"
ARTICLES["32"]="/wp-content/uploads/2022/06/MEMORIAL-MARIA-ARAGAO.pdf|memorial_maria_aragao"
ARTICLES["33"]="/wp-content/uploads/2022/06/MULHERES-MODERNAS-1.pdf|mulheres_modernas_producao_feminina"
ARTICLES["34"]="/wp-content/uploads/2022/06/O-TIJOLO-E-O-CONCRETO-NA-ARQUITETURA-INSTITUCIONAL-EM-GOIANIA-1970-80.pdf|tijolo_concreto_goiania"
ARTICLES["35"]="/wp-content/uploads/2022/06/OS-BRISES-NA-ARQUITETURA-MODERNA-EM-FORTALEZA.pdf|brises_arquitetura_fortaleza"
ARTICLES["36"]="/wp-content/uploads/2022/06/ANLISE1.pdf|analise_pmcmv_sao_luis"
ARTICLES["37"]="/wp-content/uploads/2022/06/A-CONSERVACAO-ATRAVES-DO-SEU-SIGNIFICADO.pdf|conservacao_significado_padre_cicero"
ARTICLES["38"]="/wp-content/uploads/2022/06/CINE-SAO-LUIZ.pdf|cine_sao_luiz"
ARTICLES["39"]="/wp-content/uploads/2022/06/EDIFICIO-COLONIAL-E-O-MODERNISMO-NO-CENTRO-HISTORICO-DE-SAO-LUIS.pdf|edificio_colonial_modernismo_sao_luis"
ARTICLES["40"]="/wp-content/uploads/2022/06/MURAL-DE-CONCRETO-POLICROMADO-DA-FACHADA-DO-EDIFICIO-OSCAR-PEREIRA.pdf|mural_concreto_oscar_pereira"
ARTICLES["41"]="/wp-content/uploads/2022/06/O-CINE-TEATRO-MUNICIPAL-DE-BARBALHA-%E2%80%93-CE.pdf|cine_teatro_barbalha"
ARTICLES["42"]="/wp-content/uploads/2022/06/PATRIMONIO-INTELIGENTE-E-DOCUMENTACAO-DA-PROTOMODERNIDADE.pdf|patrimonio_inteligente_estacao_campina_grande"
ARTICLES["43"]="/wp-content/uploads/2022/06/SEDE-DO-BNB-DO-JUAZEIRO-DO-NORTE-CE.pdf|sede_bnb_juazeiro_norte"
ARTICLES["44"]="/wp-content/uploads/2022/06/MANUTENCAO-DO-PATRIMONIO-ARQUITETONICO.pdf|conservacao_estacao_barbalha"
ARTICLES["45"]="/wp-content/uploads/2022/06/MODERNIDADES-EM-ALCANTARA-MA.pdf|modernidades_alcantara"
ARTICLES["46"]="/wp-content/uploads/2022/06/ABORDAGEM-TECTONICA-NA-LEITURA-DE-OBRAS-RESIDENCIAIS.pdf|abordagem_tectonica_lina_bo_bardi"
ARTICLES["47"]="/wp-content/uploads/2022/06/ARTE-ARQUITETURA-E-PAISAGEM.pdf|arte_arquitetura_paisagem_tarsila"
ARTICLES["48"]="/wp-content/uploads/2022/06/MODERNIZACAO-LUDOVICENSE.pdf|modernizacao_ludovicense_ponte_sarney"
ARTICLES["49"]="/wp-content/uploads/2022/06/O-RECONCAVO-E-O-RECONVEXO.pdf|reconcavo_reconvexo_lina_salvador"
ARTICLES["50"]="/wp-content/uploads/2022/06/APROXIMACOES-ENTRE-LINA-BO-BARDI-E-GLAUBER-ROCHA.pdf|aproximacoes_lina_glauber"
ARTICLES["51"]="/wp-content/uploads/2022/06/ANALISE-DA-FUNCIONALIDADE.pdf|analise_funcionalidade_pmcmv"

echo "Baixando 51 PDFs do 9º Seminário Docomomo N/NE - São Luís (2022)..."
echo ""

for num in $(printf '%02d\n' {1..51}); do
    if [ -n "${ARTICLES[$num]}" ]; then
        IFS='|' read -r url name <<< "${ARTICLES[$num]}"
        filename="${num}_${name}.pdf"
        echo "[$num/51] $filename"
        wget -q --show-progress -O "$filename" "${BASE}${url}" 2>/dev/null || curl -s -o "$filename" "${BASE}${url}"
    fi
done

echo ""
echo "Download concluído!"
echo "Total: $(ls -1 *.pdf 2>/dev/null | wc -l) arquivos"
echo "Tamanho: $(du -sh . | cut -f1)"
