# 09 — Roteiro de estudo

Ordem sugerida para sair do zero até conseguir contribuir. Cada etapa tem um objetivo
verificável.

## Etapa 1 — O domínio antes do código (1 sessão)

Abrir a instância de demonstração (https://sapl31demo.interlegis.leg.br, `admin` /
`Interlegis@2025`) e **executar um ciclo completo**:

1. Cadastrar uma legislatura, uma sessão legislativa e dois parlamentares.
2. Criar uma proposição pelo módulo do autor e enviá-la.
3. Receber a proposição no protocolo — ela vira matéria legislativa.
4. Tramitar a matéria para uma comissão e de volta ao plenário.
5. Criar uma sessão plenária, incluir a matéria na Ordem do Dia, registrar presença e votar.
6. Transformar o resultado em norma jurídica e gerar a ata.

**Objetivo:** saber dizer, sem consultar, a diferença entre *proposição*, *matéria*,
*documento administrativo* e *norma*. Sem isso, o código não faz sentido.

## Etapa 2 — Mapa do repositório (1 sessão)

```bash
git clone --depth 1 https://github.com/interlegis/sapl && cd sapl
```

Ler nesta ordem:

1. `README.rst` — avisos operacionais e índice da documentação
2. `CHANGES.md` (primeiras 100 linhas) — o que a equipe está mexendo agora
3. `requirements/requirements.txt` — a stack inteira em 40 linhas
4. `sapl/settings.py` — apps instalados, `DRFAUTOAPI`, configuração de Solr e mídia
5. `sapl/urls.py` — o mapa de rotas

**Objetivo:** conseguir localizar qualquer funcionalidade a partir da URL do navegador.

## Etapa 3 — Modelos (2 a 3 sessões)

Ler só os `models.py`, nesta ordem — ela segue a dependência entre apps:

```
sapl/base/models.py           → CasaLegislativa, AppConfig, Autor
sapl/parlamentares/models.py  → Legislatura, Parlamentar, Mandato, Partido
sapl/materia/models.py        → MateriaLegislativa, Proposicao, Tramitacao
sapl/protocoloadm/models.py   → Protocolo, DocumentoAdministrativo
sapl/sessao/models.py         → SessaoPlenaria, OrdemDia, RegistroVotacao
sapl/norma/models.py          → NormaJuridica, NormaRelacionada
sapl/comissoes/models.py      → Comissao, Composicao, Reuniao
```

Truque útil: gerar o diagrama de entidades com `django-extensions` (já é dependência, e o
`graphviz` está nos requisitos de sistema):

```bash
python manage.py graph_models materia sessao norma -o dominio.png
```

**Objetivo:** desenhar de memória o caminho `Proposicao → Protocolo → MateriaLegislativa →
Tramitacao → OrdemDia → RegistroVotacao → NormaJuridica`.

## Etapa 4 — As duas abstrações centrais (1 a 2 sessões)

Sem entender `crud` e `rules`, o resto do código parece incompleto — porque grande parte
dele é gerada.

1. `sapl/rules/__init__.py` — o docstring é a melhor documentação do projeto
2. `sapl/rules/map_rules.py` + um arquivo de grupo (`group_materia.py`)
3. `sapl/crud/base.py` — `Crud`, `MasterDetailCrud`, `PermissionRequiredContainerCrudMixin`
4. Um `layouts.yaml` qualquer + `sapl/crispy_layout_mixin.py`

**Objetivo:** responder "onde eu mexo para que o Operador de Comissões passe a poder editar
X?" e "onde eu mexo para mudar a ordem dos campos do formulário de norma?".

## Etapa 5 — API (1 sessão)

1. `drfautoapi/drfautoapi.py` — `ApiViewSetConstrutor.build_class`
2. `sapl/api/views.py` — `SaplApiViewSetConstrutor`, `LastModifiedDecorator`
3. `sapl/api/views_materia.py` — um exemplo de `@customize`
4. Swagger da instância de demonstração: `/api/schema/swagger-ui/`

**Objetivo:** acrescentar mentalmente um endpoint customizado sem escrever um ViewSet do
zero.

## Etapa 6 — Compilação (2 sessões)

O módulo mais denso. Ler `sapl/compilacao/models.py` na ordem:
`TipoDispositivo` (l. 590) → `TipoDispositivoRelationship` → `TextoArticulado` →
`Dispositivo` (l. 954). Ver [doc 05](05-compilacao.md).

**Objetivo:** explicar por que existem quatro datas (`inicio_vigencia`, `fim_vigencia`,
`inicio_eficacia`, `fim_eficacia`) e para que serve `texto_atualizador`.

## Etapa 7 — Contribuir

1. Subir o ambiente de desenvolvimento ([doc 08](08-ambiente-local.md)).
2. Rodar `pytest` e ver a suíte passar.
3. Ler `docs/CONTRIBUTING.md` e `docs/howtogit.rst`.
4. Escolher uma *issue* pequena no GitHub (`interlegis/sapl`).
5. Conversar no Discord "Somos Interlegis" antes de investir em algo grande.

## Perguntas para testar o entendimento

1. Por que `Protocolo` tem campos separados de `user`/`ip` para data e hora informadas
   manualmente?
2. O que acontece quando `RegistroVotacao` recebe `ordem` **e** `expediente` preenchidos?
3. Por que `VotoParlamentar` guarda `ordem`/`expediente` se `RegistroVotacao` já guarda?
4. Para que serve `MateriaEmTramitacao` se já existe `Tramitacao`?
5. Qual a diferença entre a posição 1 e a posição 2 das tuplas em `sapl/rules/group_*.py`?
6. Como o SAPL representa "Parágrafo único" versus "§ 1º" sem `if` no código?
7. Como uma `Comissao` pode ser autora de uma matéria, se `Autoria` aponta para `Autor`?
8. Por que `default-jre`, `poppler-utils` e `antiword` são dependências de sistema?

*(Respostas: 1 — fé pública do protocolo, doc 03; 2 — `ValidationError` no `clean()`,
doc 04; 3 — votação interativa grava votos antes do registro existir, doc 03; 4 — é uma
view de banco com a última tramitação, doc 03; 5 — permissões do grupo versus permissões
públicas na API, doc 06; 6 — `rotulo_prefixo_texto` com `;` em `TipoDispositivo`, doc 05;
7 — `Autor` usa `GenericForeignKey`, doc 03; 8 — Solr precisa de Java, e os outros dois
extraem texto de PDF/`.doc` para indexação, doc 08.)*

## Temas para aprofundamento

- **Modernização da stack**: Django 2.2 e Vue 2 estão fora de suporte. Qual seria o caminho
  de migração de menor risco para um sistema com 130+ modelos e centenas de instâncias em
  produção?
- **Compilação vs. Akoma Ntoso / LexML-BR**: o quanto o modelo `Dispositivo` se aproxima do
  padrão internacional de representação de normas?
- **Dado aberto**: o que a API pública do SAPL permite construir em cima (painéis de
  transparência, monitoramento legislativo, análise comparada entre municípios)?
