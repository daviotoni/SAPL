# 08 — Subindo um ambiente

Três caminhos, do mais rápido ao mais completo.

## Caminho 0 — Só olhar

Instância pública de demonstração do Interlegis:

- https://sapl31demo.interlegis.leg.br — `admin` / `Interlegis@2025`

Sem instalar nada. Suficiente para entender a interface e o vocabulário antes de abrir o
código.

## Caminho 1 — Docker Compose (recomendado para estudo)

O arquivo de produção é `dist/docker-compose.yml`. Ele sobe quatro serviços:

| Serviço | Imagem | Porta |
|---|---|---|
| `sapldb` | `postgres:10.5-alpine` | 5433 → 5432 |
| `zoo1` | ZooKeeper | interna |
| `solr1` | `solr:8.11` | 8983 |
| `sapl` | `interlegis/sapl:<versão>` | 80/8000 |

```bash
git clone --depth 1 https://github.com/interlegis/sapl
cd sapl/dist
# ajuste a tag da imagem em docker-compose.yml para a versão desejada
docker compose up -d
docker compose logs -f sapl
```

Variáveis de ambiente relevantes no serviço `sapl` (definidas no compose):

| Variável | Uso |
|---|---|
| `ADMIN_PASSWORD`, `ADMIN_EMAIL` | Superusuário criado no primeiro *boot* |
| `DEBUG` | Nunca `True` em produção |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_USE_TLS` | SMTP para notificações e recuperação de senha |
| `DATABASE_URL` | Conexão (formato `dj-database-url`) |
| `USE_SOLR`, `SOLR_URL` | Ativa a busca textual |
| `RATE_LIMITER_RATE` | Limite de requisições (default `35/m` desde 3.1.165-RC2) |

A configuração é lida por `python-decouple`, então tudo pode vir de variáveis de ambiente
ou de um arquivo `.env`.

> **Cuidado documentado no README oficial:** a migração para Solr Cloud na versão 3.1.162+
> exigiu recriar containers. O README sugere `docker system prune -a -f --volumes`, que
> **apaga todos os containers e volumes do host, inclusive o banco**. Faça backup do
> PostgreSQL antes e prefira remover apenas os recursos do projeto (`docker compose down -v`
> no diretório certo) em vez do `prune` global.

Após restaurar um dump, pare e reinicie os containers para disparar a indexação textual.

## Caminho 2 — Ambiente de desenvolvimento

### 2a. Com Docker (mais simples)

```bash
# sem o container do PostgreSQL (usa o Postgres da máquina)
docker compose -f docker/docker-compose-dev.yml up

# com o container do PostgreSQL
docker compose -f docker/docker-compose-dev-db.yml up
```

Documentado em `docs/ambiente-dev.md`.

### 2b. Nativo (virtualenv)

`docs/instalacao31.rst` traz o roteiro completo. Em resumo:

```bash
# dependências de sistema (Debian/Ubuntu)
sudo apt-get install git python3-dev libpq-dev graphviz-dev graphviz pkg-config \
  postgresql postgresql-contrib python3-psycopg2 build-essential libxml2-dev \
  libjpeg-dev libssl-dev libffi-dev libxslt1-dev python3-venv \
  poppler-utils antiword default-jre

# banco
sudo -u postgres psql -c "CREATE ROLE sapl LOGIN ENCRYPTED PASSWORD 'sapl' NOSUPERUSER INHERIT CREATEDB NOCREATEROLE NOREPLICATION;"
sudo -u postgres psql -c "CREATE DATABASE sapl WITH OWNER = sapl ENCODING = 'UTF8' LC_COLLATE = 'pt_BR.UTF-8' LC_CTYPE = 'pt_BR.UTF-8' TEMPLATE template0;"

# projeto
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev-requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Note as dependências não óbvias: **`default-jre`** (Java, para o Solr), **`poppler-utils`**
e **`antiword`** (extração de texto de PDF e `.doc` para indexação), **`graphviz`**
(geração de diagramas de modelo via `django-extensions`).

O roteiro oficial ainda cita Ubuntu 16.04 e `virtualenvwrapper` — está datado, mas a
sequência lógica continua válida.

### Restaurar uma base

```bash
./scripts/restore_db.sh -f <caminho-do-dump>
./scripts/restore_db.sh -f <caminho-do-dump> -p 5433   # Postgres em container
```

### Frontend

```bash
cd frontend
yarn install
yarn serve     # dev server
yarn build     # gera webpack-stats.json lido por django-webpack-loader
```

## Testes

```bash
pip install -r requirements/test-requirements.txt
pytest                      # configuração em pytest.ini / conftest.py
pytest sapl/materia         # um app
```

Há testes por app (`sapl/<app>/tests/`) e testes gerais na raiz do pacote
(`sapl/test_general.py`, `sapl/test_urls.py`, `sapl/test_utils.py`) — este último é útil
para detectar URLs quebradas depois de mexer em rotas.

## Deploy em produção

`docs/deploy.rst` descreve **Nginx + Gunicorn**. Pontos de atenção:

- `DEBUG=False`, `ALLOWED_HOSTS` correto e `SECRET_KEY` própria.
- Estáticos servidos por Nginx (ou WhiteNoise), com `collectstatic` executado.
- Solr e ZooKeeper **não** devem ficar expostos publicamente.
- Backup do PostgreSQL **e** dos arquivos de mídia (`media/`) — os textos originais das
  matérias vivem no disco, não no banco.
- Manifestos Kubernetes de exemplo em `docker/k8s/`.
