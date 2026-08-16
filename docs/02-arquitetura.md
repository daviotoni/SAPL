# 02 — Arquitetura e stack

## Visão geral

O SAPL 3.1 é um **monólito Django** servido por Gunicorn atrás de Nginx, com PostgreSQL
como banco, Solr para busca textual e um frontend híbrido: templates Django server-side
(Bootstrap 4 + jQuery) com ilhas de Vue 2 compiladas por Webpack.

```
                 ┌──────────┐
   navegador ───▶│  Nginx   │──▶ estáticos (WhiteNoise/Nginx)
                 └────┬─────┘
                      │
                 ┌────▼─────────────────┐      ┌────────────┐
                 │ Gunicorn + Django    │─────▶│ PostgreSQL │
                 │  sapl.*  (13 apps)   │      └────────────┘
                 │  drfautoapi (API)    │      ┌────────────┐
                 └────┬─────────────────┘─────▶│ Solr +     │
                      │                        │ ZooKeeper  │
                      │ OAI-PMH                └────────────┘
                      ▼
                 rede LexML (harvesting nacional)
```

## Stack (de `requirements/requirements.txt`)

| Camada | Tecnologia | Observação |
|---|---|---|
| Framework | **Django 2.2.28** (LTS, já EOL upstream) | Trava boa parte das decisões: `url()` em vez de `path()`, `ugettext_lazy` |
| Banco | **PostgreSQL** via `psycopg2-binary`, `dj-database-url` | Usa recursos específicos (`django-contrib-postgres`) e *views* materializadas |
| API | **djangorestframework 3.12**, `django-filter`, `drf-spectacular` | Schema OpenAPI + Swagger/Redoc automáticos |
| Busca | **django-haystack 3.1** + `pysolr` + `kazoo` (ZooKeeper) | Indexação de texto integral, inclusive de PDFs |
| Formulários | `django-crispy-forms`, `django-braces`, `django-extra-views` | Layouts declarados em YAML (ver doc 06) |
| PDF/relatórios | `reportlab`, `trml2pdf`, **WeasyPrint 66**, `PyPDF4`, `XlsxWriter` | Duas gerações de geração de relatório convivem |
| Imagens | `Pillow`, `django-image-cropping`, `easy-thumbnails` | Fotos de parlamentares |
| Operação | `gunicorn`, `whitenoise`, `django-prometheus`, `django-ratelimit`, `django-waffle` | Métricas, *rate limit* e *feature flags* |
| Config | `python-decouple` | Configuração por variáveis de ambiente / `.env` |
| Frontend | **Vue 2.7**, Bootstrap-Vue, TinyMCE 7, jQuery, `django-webpack-loader` | Build com `vue-cli-service`, saída lida pelo Django |

Nota importante para quem for contribuir: **Django 2.2 e Vue 2 estão fora de suporte
upstream**. É a maior dívida técnica visível do projeto e condiciona qualquer proposta de
mudança estrutural.

## Os apps Django

Cada app corresponde a um domínio do processo legislativo. Tamanho em linhas de Python
(medido no commit de referência):

| App | LOC | Papel |
|---|---:|---|
| `sapl.materia` | 12.268 | Matérias legislativas, proposições, tramitação, autoria |
| `sapl.sessao` | 11.175 | Sessões plenárias, pauta, presença, votação |
| `sapl.compilacao` | 8.866 | Textos articulados: dispositivos, vigência, alterações |
| `sapl.relatorios` | 8.302 | Geração de PDFs/relatórios (atas, pautas, etiquetas, espelhos) |
| `sapl.base` | 7.392 | Casa Legislativa, configuração da aplicação, autores, *audit log* |
| `sapl.protocoloadm` | 7.244 | Protocolo e documentos administrativos |
| `sapl.parlamentares` | 5.122 | Parlamentares, legislaturas, mandatos, partidos, Mesa, blocos |
| `sapl.norma` | 3.233 | Normas jurídicas, assuntos, vínculos entre normas |
| `sapl.comissoes` | 2.501 | Comissões, composições, reuniões |
| `sapl.crud` | 2.108 | Framework interno de CRUD genérico |
| `sapl.api` | 1.835 | Camada REST |
| `sapl.audiencia` | 1.227 | Audiências públicas |
| `sapl.rules` | 1.107 | Mapa declarativo de permissões e grupos |
| `sapl.painel` | 799 | Painel eletrônico de plenário |
| `sapl.lexml` | 598 | Provedor OAI-PMH para a rede LexML |

Total do pacote Python: **~80 mil linhas**.

Apps auxiliares fora de `sapl/`: `drfautoapi/` (construtor automático de ViewSets, ver
[doc 07](07-api-interoperabilidade.md)) e `frontend/` (código-fonte Vue).

### Dependências entre apps

A direção do acoplamento espelha o próprio processo legislativo:

```
parlamentares ──┐
comissoes ──────┼──▶ materia ──▶ sessao ──▶ painel
base (autor) ───┘        │
                         ▼
protocoloadm ────────▶ norma ──▶ compilacao ──▶ lexml
```

`sapl.base` é a raiz: define `CasaLegislativa`, `AppConfig` (as configurações da instância)
e `Autor` — um modelo genérico que, via `GenericForeignKey`, aponta para um `Parlamentar`,
uma `Comissao`, uma `Bancada` ou o Executivo. É esse truque que permite que "autoria" seja
uniforme em matérias, normas e documentos.

## Infraestrutura de execução

`dist/docker-compose.yml` descreve a topologia de produção recomendada:

| Serviço | Imagem | Papel |
|---|---|---|
| `sapldb` | `postgres:10.5-alpine` | Banco de dados |
| `zoo1` | ZooKeeper | Coordenação do Solr Cloud |
| `solr1` | `solr:8.11` | Índice de busca (heap 1 GB, `security.json` carregado no ZK) |
| `sapl` | `interlegis/sapl:<versão>` | Aplicação Django + Gunicorn |

Há ainda `docker/k8s/` com manifestos Kubernetes, `docker/Dockerfile.dev` e
`docker/docker-compose-dev.yml` para desenvolvimento, e `docker/startup_scripts/` com a
sequência de bootstrap (migrações, criação do superusuário via `ADMIN_PASSWORD`/
`ADMIN_EMAIL`, upload do *configset* do Solr, coleta de estáticos).

## Observabilidade e proteção

- **`django-prometheus`** expõe métricas; há `sapl/metrics.py` e `sapl/health.py` com
  *endpoints* `/healthz` e `/readyz` (`sapl/api/views_health.py`).
- **`django-ratelimit`** protege endpoints sensíveis (protocolo, consulta de matéria e
  norma). O default subiu de `10/m` para `35/m` em 3.1.165-RC2 (`RATE_LIMITER_RATE`).
- **`AuditLog`** (`sapl.base.models`) registra alterações por modelo/objeto — usado
  inclusive como fonte do cabeçalho `Last-Modified` da API.
- **`sapl/middleware/`** e `sapl/logging/` acrescentam `requestId` às requisições, o que
  facilita correlacionar log de aplicação com log de acesso.
- **`django-waffle`** dá *feature flags* (`docs/feature-flags.md`), usadas para liberar
  funcionalidades novas por instância.
