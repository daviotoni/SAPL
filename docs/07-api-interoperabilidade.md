# 07 — API REST e interoperabilidade

## A API é gerada, não escrita

O SAPL não tem um ViewSet escrito à mão por modelo. Tem `drfautoapi/drfautoapi.py`, um
construtor que **percorre os apps e fabrica, para cada modelo, um serializer, um FilterSet
e um ViewSet** — registrando tudo num `DefaultRouter`.

O ponto de entrada é `SaplApiViewSetConstrutor` (`sapl/api/views.py`), subclasse de
`ApiViewSetConstrutor`. O método `build_class` faz, por modelo:

1. Procura uma classe `<Model>Serializer` no módulo de serializers configurado em
   `settings.DRFAUTOAPI['DEFAULT_SERIALIZER_MODULE']`; se não achar, usa um
   `ModelSerializer` genérico.
2. Procura um `<Model>FilterSet` no módulo de filtros; se não achar, usa `ApiFilterSetMixin`.
3. Monta dinamicamente as classes `ApiSerializer` / `ApiViewSet` com `Meta` derivada.

Ou seja: **convenção de nome é a configuração**. Basta criar `MateriaLegislativaSerializer`
em `sapl/api/serializers.py` para que ele passe a ser usado.

### Customizando um endpoint

Os arquivos `views_materia.py`, `views_sessao.py`, `views_parlamentares.py` etc. usam o
decorador `@customize(Model)` para acrescentar ou sobrescrever comportamento no ViewSet
gerado — *actions* extras, `get_queryset` próprio, permissões específicas. É a válvula de
escape do modelo automático.

Outros utilitários do módulo:

- `BusinessRulesNotImplementedMixin` — bloqueia `create`/`update`/`delete` em endpoints que
  ainda não têm as regras de negócio implementadas. Um jeito honesto de expor leitura sem
  abrir escrita insegura.
- `wrapper_queryset_response_for_drf_action` — adapta o retorno de *actions* customizadas.
- `M2MFilter`, `SplitStringCharFilter`, `filter_id__in` — filtros que aceitam múltiplos ids
  (`?id__in=1,2,3`) e lookups `__in` em campos ManyToMany (#3807).
- **Expansão dinâmica de campos** (`?expand=...`, #3809) — o cliente escolhe quais relações
  vêm embutidas na resposta, evitando N+1 requisições.

### Autorização da API

A camada de permissão da API lê a **posição 2** das tuplas do mapa de `sapl.rules`: o que
está no *set* é público (anônimo); o resto exige autenticação. Ver [doc 06](06-permissoes-crud.md).

Autenticação:

- `POST /api/auth/token` — `obtain_auth_token` do DRF, devolve token por usuário.
- `POST /api/recriar-token/<pk>` — apenas `IsAdminUser`, revoga e recria o token.
- Documentação: `docs/token-auth.rst`.

### Cache e condicionalidade

`LastModifiedDecorator` (`sapl/api/views.py`) adiciona `Last-Modified` aos ViewSets e
responde **304 Not Modified** quando cabe. A data sai, por ordem de preferência, dos campos
`data_ultima_atualizacao` ou `ultima_edicao` do modelo; existe também um caminho alternativo
baseado no `AuditLog`, hoje desativado por padrão mas preservado no código. Em listagens,
considera o resultado **já filtrado** pelo FilterSet — o que torna o cabeçalho correto para
consultas parametrizadas, e não só para o recurso inteiro.

### Documentação automática

Via `drf-spectacular`:

| Rota | Conteúdo |
|---|---|
| `/api/schema/` | Schema OpenAPI |
| `/api/schema/swagger-ui/` | Swagger UI |
| `/api/schema/redoc/` | Redoc |

O jeito mais rápido de conhecer a superfície da API é abrir o Swagger da instância de
demonstração.

### Endpoints `ecidadania`

`sapl/api/views_sessao.py` expõe *actions* `ecidadania` (detalhe e lista) em
`SessaoPlenariaViewSet` — formato voltado a aplicações de transparência/e-Cidadania. As
rotas antigas `/api/sessao-plenaria/` continuam registradas em `sapl/api/deprecated.py`
como compatibilidade, redirecionando conceitualmente para
`/api/sessao/sessaoplenaria/ecidadania`.

## LexML — publicação em rede nacional

`sapl/lexml/` implementa um **provedor OAI-PMH** (`OAIServer.py`, com a biblioteca `pyoai`).
A rede LexML colhe periodicamente os metadados das normas da Casa e os agrega ao portal
nacional, dando à legislação municipal um identificador **URN LexML** padronizado e
tornando-a pesquisável junto com a legislação federal e estadual.

Configuração pela interface: `LexmlProvedor` (dados da Casa como provedora, incluindo o XML
fornecido pela equipe LexML) e `LexmlPublicador`. O campo `equivalente_lexml` em
`TipoNormaJuridica` faz o mapeamento entre a tipologia local e a vocabulário LexML — é o
que garante que a "Lei Ordinária" de uma Câmara seja reconhecida como tal na rede.

## Busca textual — Haystack + Solr

- `django-haystack 3.1` + `pysolr`, com Solr 8.11 em modo *cloud* coordenado por ZooKeeper
  (`kazoo`).
- Indexa não só os campos (`ementa`, `indexacao`, `observacao`) mas o **texto integral dos
  arquivos anexados** — inclusive PDFs, via extração do Solr.
- Configuração e *configsets* em `solr/` e `dist/solr_cloud/`; instruções em `docs/solr.rst`.
- Reindexação é feita por comando de gerenciamento; após restaurar um backup de banco é
  necessário reiniciar os containers para disparar a indexação.

## Outros pontos de integração

- **Saúde**: `/healthz` e `/readyz` (`sapl/api/views_health.py`) — prontos para *probes* de
  Kubernetes.
- **Métricas**: `django-prometheus` + `sapl/metrics.py`.
- **Exportação**: relatórios em PDF (WeasyPrint/ReportLab) e planilhas (`XlsxWriter`) em
  `sapl.relatorios`.
- **reCAPTCHA**: obrigatório desde 3.1.162 nos fluxos públicos de recuperação de senha e
  acompanhamento de matéria/documento; chaves configuradas por Casa em *Sistema → Tabelas
  Auxiliares → Configurações da Aplicação*.
