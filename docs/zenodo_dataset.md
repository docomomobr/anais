# Zenodo Dataset — Procedimento de atualização

O **dataset do projeto** (metadados do acervo completo) é um registro Zenodo separado dos artigos individuais. Ele é gerenciado pela integração GitHub→Zenodo, **não** pela API diretamente.

Record: https://zenodo.org/records/19297561

---

## Arquitetura

| Componente | Descrição |
|------------|-----------|
| `.zenodo.json` | Metadados do dataset (título, description, creators, etc.) — formato legacy Zenodo |
| GitHub release | Dispara a criação automática de nova versão no Zenodo |
| `upload_zenodo.py` | **NÃO usar** para o dataset — é para artigos individuais (formato InvenioRDM) |
| `fix_zenodo_metadata.py` | **NÃO usar** para o dataset — mesmo motivo |

### Formatos incompatíveis

O `.zenodo.json` usa a **API legacy** do Zenodo:
```json
{"name": "Sobrenome, Nome", "affiliation": "Instituição", "orcid": "0000-..."}
{"relation": "isSupplementedBy", "resource_type": "other"}
```

Os scripts `upload_zenodo.py` e `fix_zenodo_metadata.py` usam a **API InvenioRDM**:
```json
{"person_or_org": {"family_name": "Sobrenome", "given_name": "Nome"}, "affiliations": [{"name": "Instituição"}]}
{"relation_type": {"id": "issupplementedby"}, "resource_type": {"id": "other"}}
```

Tentar criar/atualizar o dataset via API InvenioRDM (POST /versions, PUT /draft) causa erros de validação porque os campos do `.zenodo.json` não mapeiam diretamente para o formato InvenioRDM.

---

## Fluxo de atualização

### 1. Editar `.zenodo.json`

Na raiz do repositório. Campos que tipicamente mudam:

- `description`: totais de seminários, artigos, autores; tabela de âmbitos; novos parágrafos
- `keywords`: se necessário
- `related_identifiers`: se houver novas relações

### 2. Atualizar o editorial (se aplicável)

Manter sincronizado com `.zenodo.json`:
- `site/content/editorial/index.md` — texto do site
- A description do `.zenodo.json` é uma versão HTML do editorial

### 3. Commit e push

```bash
git add .zenodo.json site/content/editorial/index.md
git commit -m "zenodo: atualiza dataset (N seminários, M artigos)"
git push
```

### 4. Criar release no GitHub

```bash
GH_TOKEN=$(git remote get-url origin | grep -o 'ghp_[^@]*') \
  gh release create vX.Y \
  --title "vX.Y — descrição curta" \
  --notes "changelog em markdown"
```

O Zenodo detecta a release automaticamente e publica nova versão do dataset com os metadados do `.zenodo.json`.

### 5. Verificar

- Acessar https://zenodo.org/records/19297561 e confirmar que a nova versão aparece
- Verificar description, creators, related identifiers

---

## Versionamento

| Tipo de mudança | Versão | Exemplo |
|----------------|--------|---------|
| Novo seminário | minor (v1.1, v1.2) | Adicionar idc06 |
| Correção de metadados | patch (v1.1.1) | Corrigir typo no editorial |
| Novo âmbito ou reestruturação | major (v2.0) | Adicionar livros, mudar schema |

---

## Quando atualizar

- Ao adicionar novo seminário ou âmbito → atualizar totais na description
- Ao mudar editorial, licença ou metadados do projeto
- Ao alterar significativamente a infraestrutura de publicação

---

## Histórico

| Versão | Data | Mudança |
|--------|------|---------|
| v1.0 | 2026-03-28 | 45 seminários, 2.714 artigos, 2.461 autores |
| v1.1 | 2026-03-29 | +idc06 (53 artigos) → 46 seminários, 2.767 artigos, 2.514 autores |
