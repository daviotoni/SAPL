# 01 — Panorama institucional

## O que é

O **SAPL (Sistema de Apoio ao Processo Legislativo)** é uma ferramenta desenvolvida pelo
**Programa Interlegis**, do Senado Federal, para informatizar e agilizar o processo
legislativo em Câmaras Municipais e Assembleias Legislativas. É oferecido **gratuitamente**
às Casas Legislativas brasileiras.

O produto atende simultaneamente a dois públicos:

- **Interno** — parlamentares e servidores: registram proposições, controlam tramitação,
  organizam a pauta e conduzem sessões plenárias.
- **Externo** — o cidadão: consulta a produção legislativa, a legislação vigente, a
  composição da Mesa e das comissões, as pautas e os resultados de votação.

## Funcionalidades declaradas pelo Interlegis

- Elaboração e tramitação de proposições
- Organização de sessões plenárias
- Manutenção da base de leis do município/estado
- Consultas sobre Mesa Diretora, comissões e votações
- Acompanhamento da produção legislativa pelos cidadãos

Na **versão 3.1** entraram, entre outros, o **Painel Eletrônico** (placar de plenário,
cronômetro, votação interativa) e a **Compilação de Textos Articulados** (ver
[doc 05](05-compilacao.md)).

## Como uma Casa Legislativa adere

Dois requisitos são exigidos pelo Interlegis:

1. A Casa deve possuir **Acordo de Cooperação Técnica (ACT)** vigente com o Senado Federal.
2. A **hospedagem de DNS** do domínio da Casa deve estar configurada no Interlegis.

Cumpridos esses requisitos, a instância é normalmente provisionada na infraestrutura do
Interlegis, sob o domínio `.leg.br`. Como o software é livre, uma Casa também pode
instalá-lo em infraestrutura própria (ver [doc 08](08-ambiente-local.md)) — mas aí assume o
custo de operação, backup e atualização.

### Onde pedir suporte

- **Central de Soluções / FAQ** e abertura de chamados: `suporte.interlegis.leg.br`
- **Discord "Somos Interlegis"**: https://discord.gg/fzXSbhZbcy
- **Perguntas frequentes**: https://github.com/interlegis/sapl/wiki/Perguntas-Frequentes

## Ambiente de demonstração

O Interlegis mantém uma instância pública para testes:

- URL: https://sapl31demo.interlegis.leg.br
- Usuário: `admin` — Senha: `Interlegis@2025`

É o caminho mais rápido para entender a interface antes de mergulhar no código: vale
percorrer, nessa ordem, os menus **Matérias Legislativas → Sessão Plenária → Normas
Jurídicas → Sistema**.

## Linha do tempo das versões

| Versão | Situação |
|---|---|
| 2.5 | Geração anterior (stack Zope/Plone). Ainda existe base histórica; há rotina documentada de migração MySQL 2.5 → 3.1 |
| 3.1 | Geração atual, reescrita em Django. Numeração evolui como `3.1.<minor>-RC<n>` |
| 3.1.162+ | Passa a exigir **Google reCAPTCHA** para recuperar senha e para acompanhamento de matéria/documento — chaves geradas pela própria Casa em *Sistema → Tabelas Auxiliares → Configurações da Aplicação* |
| 3.1.163+ | Solr passa a rodar em modo *cloud* com ZooKeeper; `docker-compose.yml` movido para `dist/` |
| 3.1.165 | Última série no momento deste estudo: `Last-Modified` na API, expansão dinâmica de campos, refatoração do rate limiter |

O arquivo `CHANGES.md` na raiz do repositório é o registro canônico e vale a leitura: ele
mostra que o desenvolvimento é contínuo e majoritariamente conduzido pela equipe do
Interlegis (SPDT), com contribuições externas via pull request no GitHub.

## Licença e governança

- Licença: **GNU GPL v3** (`LICENSE.txt`).
- Código no GitHub (`interlegis/sapl`), com espelho no Gitea institucional
  (`git.interlegis.leg.br/SPDT/sapl`).
- Há `docs/CONTRIBUTING.md` e `docs/CODE_OF_CONDUCT.md` no repositório, além de
  `docs/howtogit.rst` com o fluxo de trabalho de branches esperado dos contribuidores.
