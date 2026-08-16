# 10 — SAPL-DC: o sistema da CMDC

Depois do estudo do SAPL/Interlegis (docs 01–09), este repositório passou a abrigar o
**SAPL-DC** — sistema novo, enxuto e moderno, inspirado na modelagem do SAPL e **adaptado
ao processo legislativo da Câmara Municipal de Duque de Caxias**, conforme seu Regimento
Interno (Resolução nº 1.835/2000 e alterações) e a Lei Orgânica do Município.

## Decisões de projeto

| Decisão | SAPL/Interlegis | SAPL-DC |
|---|---|---|
| Stack | Django 2.2 (EOL) + Vue 2 | **Django 5.2 + DRF**, templates server-side sem build JS |
| Modelos | 130+ | **~25**, só o que a CMDC usa |
| CRUD | framework próprio (`sapl.crud`) + YAML | **Django admin** configurado |
| Busca | Solr + ZooKeeper | consulta simples no banco (evolutível p/ Postgres FTS) |
| Banco | PostgreSQL 10 | SQLite (dev) / **PostgreSQL 16** (produção) |
| Análise Prévia | inexistente | **módulo próprio** (diferencial da CMDC) |

## O que veio do Regimento Interno da CMDC

Fonte: [Regimento Interno (PDF oficial)](https://www.cmdc.rj.gov.br/wp-content/uploads/2013/06/Regimento_Interno_da_Camara.pdf)

| Artigo | Regra | Onde está no código |
|---|---|---|
| Art. 24, §1º | Mesa: Presidente, 2 Vice-Presidentes, 2 Secretários | seed `MESA_2025_2027` + `CargoMesa` |
| Art. 54 | Prazos de parecer: 3 dias (urgência), 9 (prioridade), 15 (ordinária) | `Tramitacao.data_prazo` (help text) |
| Art. 74 | Sessões preparatórias, ordinárias (ter/qua/qui 17h30–19h30), extraordinárias (máx. 3h), solenes | `SessaoPlenaria.Tipo` |
| Art. 75 | Partes: **Expediente Inicial, Ordem do Dia, Expediente Final** | `ItemPauta.Fase` |
| Art. 87, §1º | Espécies de proposição: PELOM, PLC, PL, PR, PDL, PLD, Emenda, Indicação, Requerimento, Recurso | seed `TIPOS_MATERIA` |
| Art. 88 | 9 hipóteses de inadmissibilidade | `AnalisePrevia.admissibilidade_art88`, status "Devolvida ao autor" |
| Art. 91 | Regimes: Urgência, Tramitação Especial, Prioridade, Ordinária | `Materia.Regime` |
| Art. 92 | Técnica legislativa (numeração ordinal até o 9º, "Parágrafo Único"…) | `AnalisePrevia.tecnica_legislativa` |
| Art. 93 | Parecer contrário de todas as comissões → arquivamento | status "Rejeitada — parecer contrário das comissões" |
| Art. 95 | Arquivamento ao fim da legislatura | status "Arquivada (art. 95, RI)" |
| Art. 142 | 8 hipóteses de prejudicialidade | `AnalisePrevia.prejudicialidade_art142`, resultado "Prejudicada" |
| Art. 162 | Aprovado em 1º turno → Redação Final na CLJR | `ItemPauta.Turno.REDACAO_FINAL`, status "Em Redação Final" |

## O fluxo APL → Análise Prévia → PL

O Anteprojeto de Lei (APL) não consta do rol do art. 87 — é o instrumento da **prática
administrativa da CMDC**: a proposição do gabinete passa pela **Análise Prévia** da
Procuradoria/Assessoria Técnica Legislativa antes de se converter em projeto.

```
APL protocolado ──▶ Análise Prévia ──▶ admissível? ──▶ Materia.transformar_em(PL)
                    (art. 88, art. 142,      │
                     constitucionalidade     └─ não ──▶ "Devolvida ao autor"
                     material/formal,
                     técnica legislativa)
```

- `TipoMateria.exige_analise_previa=True` marca o APL.
- `AnalisePrevia` registra cada item do exame (admissibilidade, prejudicialidade,
  constitucionalidade material/formal objetiva/formal subjetiva, técnica legislativa),
  a fundamentação e a conclusão.
- `Materia.transformar_em()` cria o PL vinculado ao APL de origem (`materia_origem`),
  copiando ementa, autoria e número de processo, e encerra a tramitação do APL.

## Dados reais carregados (`python manage.py seed_cmdc`)

| Dado | Fonte oficial |
|---|---|
| 29 vereadores da 20ª Legislatura | [cmdc.rj.gov.br/?page_id=29390](https://www.cmdc.rj.gov.br/?page_id=29390) |
| Mesa Diretora 2025-2027 | [cmdc.rj.gov.br/?page_id=144](https://www.cmdc.rj.gov.br/?page_id=144) |
| 30 comissões permanentes + presidentes | [cmdc.rj.gov.br/?page_id=3017](https://www.cmdc.rj.gov.br/?page_id=3017) |

**Lacunas conhecidas** (completar pelo admin):

1. A página oficial de vereadores se declara "em processo de atualização" — conferir se
   há 30ª vaga e suplentes em exercício.
2. Filiações partidárias: só as noticiadas na posse foram registradas (Claudio
   Thomaz/PRD, Junior Reis/MDB, Catiti/PDT).
3. Composição completa das comissões (vices e membros) — o site publica só os presidentes.

## Como rodar

```bash
# desenvolvimento
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_cmdc
python manage.py createsuperuser
python manage.py runserver
# portal: http://localhost:8000  admin: /admin  API: /api/

# testes
python manage.py test

# produção
cp .env.example .env  # defina SECRET_KEY, ALLOWED_HOSTS, POSTGRES_PASSWORD
docker compose up -d
```

## Superfícies

- **Portal público** (`/`): matérias com busca e tramitação, sessões com pauta por fase
  regimental, votações nominais voto a voto, normas, vereadores, Mesa e comissões.
- **Admin** (`/admin/`): operação completa — matérias com autoria, Análise Prévia,
  tramitação, pareceres e documentos em uma tela; sessões com pauta e presenças;
  votações com votos individuais.
- **API REST** (`/api/`): leitura pública de vereadores, matérias (com tramitação atual),
  análises prévias, normas, comissões, sessões e votações (com votos nominais) — filtros
  e busca via query string.

## Próximos passos naturais

1. Completar as lacunas de dados (partidos, membros de comissões, 30ª vaga).
2. Perfis de permissão por setor (Protocolo, Procuradoria, Plenário, Atas) — espelhando
   os grupos do SAPL estudados no doc 06.
3. Geração da pauta e do resumo da sessão em PDF (integração com o fluxo do Setor de Atas).
4. Importação do acervo de normas do site atual (`cmdc.rj.gov.br`).
5. Busca de texto integral (PostgreSQL FTS) quando os arquivos forem anexados.
