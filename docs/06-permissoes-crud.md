# 06 — Permissões, grupos e o framework de CRUD

Duas apps internas — `sapl.rules` e `sapl.crud` — são responsáveis por gerar a maior parte
da interface administrativa e por toda a autorização. Entendê-las é o que separa "ler o
SAPL" de "conseguir mexer no SAPL".

## `sapl.rules` — permissões declarativas

### Os cinco radicais

O Django cria por padrão `add_`, `change_`, `delete_` e `view_`. O SAPL acrescenta dois
radicais próprios via signal `post_migrate` (`create_proxy_permissions`, em
`sapl/rules/apps.py`):

```python
RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE = \
    '.list_', '.detail_', '.add_', '.change_', '.delete_'
```

`list_` e `detail_` foram criados porque, quando a app nasceu, o Django ainda não tinha
`view_` — e o SAPL precisava distinguir **listar** de **ver o detalhe** de um registro.
A permissão completa é montada como `[app_label].[radical]_[model]`, por exemplo
`norma.list_normajuridica`.

### Os grupos

Onze grupos, definidos em `sapl/rules/__init__.py`:

| Grupo | Escopo |
|---|---|
| Operador Administrativo | Documentos administrativos |
| Operador de Protocolo Administrativo | Protocolo, recebimento de proposições |
| Operador de Comissões | Comissões, composições, reuniões |
| Operador de Matéria | Matérias legislativas, tramitação, relatorias |
| Operador de Norma Jurídica | Normas e compilação |
| Operador de Sessão Plenária | Sessões, pauta, votação |
| Operador de Painel Eletrônico | Painel de plenário |
| Operador de Audiência | Audiências públicas |
| Operador Geral | Tabelas auxiliares e configuração |
| Autor | Cria e acompanha as próprias proposições |
| Votante | Vota no painel eletrônico |

Há ainda `SAPL_GROUP_LOGIN_SOCIAL` (reservado, funcionalidade ainda não implementada) e
`SAPL_GROUP_ANONYMOUS` — que **não é um grupo**, e sim um marcador usado no mapa para
anotar explicitamente os modelos com ação anônima permitida (como `AcompanhamentoMateria`).

Esse desenho reflete a divisão real de trabalho numa Casa Legislativa: quem protocola não é
quem monta a pauta, que não é quem opera o painel.

### O mapa de regras

`sapl/rules/map_rules.py` importa um arquivo por grupo (`group_materia.py`,
`group_sessao.py`, …). Cada um exporta um dicionário com esta forma:

```python
rules_group_exemplo = {
    'group': SAPL_GROUP_EXEMPLO,
    'rules': [
        (model_exemplo1, (RP_LIST, RP_DETAIL), set()),
        (model_exemplo2, (RP_LIST, RP_DETAIL, RP_ADD, RP_CHANGE, RP_DELETE),
                         {RP_LIST, RP_DETAIL}),
    ]
}
```

Cada tupla tem **três posições**:

| Posição | Significado |
|---|---|
| 0 | O modelo |
| 1 | Permissões do grupo sobre o modelo — e, ao mesmo tempo, o que o CRUD passa a exigir como credencial |
| 2 | *Set* de permissões **públicas na API** — o que está aqui é acessível anonimamente |

O signal `update_groups` (`post_migrate`) lê o mapa e **cria/atualiza os grupos e suas
permissões no banco**. Ou seja: as permissões não são configuradas na interface — são
código versionado, e uma migração as reaplica.

A posição 2 é a que decide a superfície pública da API. Alterá-la expõe ou fecha dados ao
cidadão — é o ponto do código a tratar com mais cuidado em qualquer contribuição.

## `sapl.crud` — CRUD genérico

`sapl/crud/base.py` (1.597 linhas) implementa um mini-framework sobre as *class-based
views* do Django.

### Classes

| Classe | Papel |
|---|---|
| `Crud` | Fábrica: recebe um modelo e produz as cinco views + URLs |
| `CrudAux` | Variante para tabelas auxiliares (menu *Sistema → Tabelas Auxiliares*) |
| `MasterDetailCrud` | CRUD de entidade **filha** dentro do contexto de um pai (ex.: `Tramitacao` dentro de `MateriaLegislativa`) |
| `CrudBaseForListAndDetailExternalAppView` | Listagem/detalhe de entidade que "mora" em outro app |
| `CrudListView`, `CrudCreateView`, `CrudDetailView`, `CrudUpdateView`, `CrudDeleteView` | As views concretas |
| `PermissionRequiredContainerCrudMixin` | Amarra cada view às permissões do mapa de `rules` |
| `SearchMixin`, `ListWithSearchForm` | Busca embutida nas listagens |

Na prática, um app do SAPL declara algo como `Crud.build(Tramitacao, ...)` e ganha
listagem paginada com busca, formulário de criação, detalhe, edição e exclusão — todos já
protegidos pelas permissões corretas. É por isso que apps grandes têm proporcionalmente
poucas views escritas à mão.

`MasterDetailCrud` é o mais usado no domínio: quase tudo no SAPL é filho de alguma coisa
(tramitação de uma matéria, participação de uma composição, voto de uma votação).

## Layouts em YAML

Os formulários e telas de detalhe não têm HTML escrito campo a campo. O layout é declarado
em arquivos `layouts.yaml` sob `sapl/templates/<app>/`, que são **templates Django
renderizados como YAML** (usam `{% trans %}`) e consumidos por
`sapl/crispy_layout_mixin.py` junto com `django-crispy-forms`.

```yaml
NormaJuridica:
  {% trans 'Identificação Básica' %}:
  - orgao tipo:5  numero:2  ano:2
  - data  esfera_federacao  complemento
  - texto_integral
  - ementa
```

Leitura: o modelo `NormaJuridica` tem um *fieldset* "Identificação Básica"; cada item da
lista é uma **linha** do formulário; campos na mesma linha são separados por espaço; e o
sufixo `:5` é a **largura em colunas** do grid Bootstrap. Trocar a ordem dos campos de um
formulário do SAPL é, normalmente, editar YAML — não Python nem HTML.

Existem também `subnav.yaml` (submenus contextuais), `navbar.yaml` (menu principal) e
`menu_tabelas_auxiliares.yaml`.

## Consequência prática

Para acrescentar uma entidade ao SAPL, o caminho canônico é:

1. Criar o modelo em `sapl/<app>/models.py` e gerar a migração.
2. Registrar as permissões no `group_<perfil>.py` correspondente (e decidir a posição 2 —
   o que é público na API).
3. Declarar o CRUD em `sapl/<app>/views.py` com `Crud`/`MasterDetailCrud`.
4. Descrever o formulário no `layouts.yaml` do app.
5. Acrescentar a entrada em `subnav.yaml`, se precisar aparecer na navegação.

A API REST vem **de graça** — ver [doc 07](07-api-interoperabilidade.md).
