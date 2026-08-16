# Estudo do SAPL — Sistema de Apoio ao Processo Legislativo

Material de estudo sobre o **SAPL**, software livre desenvolvido pelo **Programa Interlegis
(Senado Federal)** para informatizar o processo legislativo de Câmaras Municipais e
Assembleias Legislativas.

- Página oficial: https://www12.senado.leg.br/interlegis/produtos/sapl
- Código-fonte: https://github.com/interlegis/sapl (espelho em https://git.interlegis.leg.br/SPDT/sapl)
- Demonstração: https://sapl31demo.interlegis.leg.br (`admin` / `Interlegis@2025`)
- Wiki do projeto 3.1: https://colab.interlegis.leg.br/wiki/ProjetoSapl3.1

> Base de referência deste estudo: branch `3.1.x`, commit `4e58d8a` (05/08/2026),
> versão corrente da série **3.1.165-RC2**.

## Resumo executivo

O SAPL é uma aplicação **Django** (Python) de ~80 mil linhas que modela o processo
legislativo inteiro — do protocolo de uma proposição até a norma jurídica consolidada e
sua publicação em rede nacional (LexML). É distribuído gratuitamente às Casas Legislativas
que assinam **Acordo de Cooperação Técnica (ACT)** com o Senado, normalmente hospedado na
infraestrutura do próprio Interlegis (`<sigla>.sapl.leg.br`).

Três coisas o tornam tecnicamente interessante:

1. **Modelagem de domínio jurídico completa** — 130+ modelos cobrindo matérias, tramitação,
   sessões plenárias, votação nominal, comissões, mandatos e normas.
2. **Compilação de textos articulados** — um subsistema (`sapl.compilacao`) que representa
   a lei *artigo a artigo* com vigência temporal, permitindo consultar a redação de uma lei
   em qualquer data e navegar alterações/revogações.
3. **Metaprogramação pesada** — CRUD, permissões e API REST são *gerados* a partir dos
   modelos e de um mapa declarativo de regras, em vez de escritos à mão.

## Índice

| # | Documento | Conteúdo |
|---|---|---|
| 01 | [Panorama institucional](docs/01-panorama.md) | O que é, quem mantém, como uma Casa adere, versões |
| 02 | [Arquitetura e stack](docs/02-arquitetura.md) | Django apps, dependências, infraestrutura, métricas |
| 03 | [Modelo de domínio](docs/03-modelo-de-dominio.md) | As entidades do processo legislativo, app por app |
| 04 | [Fluxos do processo legislativo](docs/04-fluxos.md) | Proposição → protocolo → matéria → tramitação → sessão → norma |
| 05 | [Compilação de textos articulados](docs/05-compilacao.md) | O modelo `Dispositivo`, vigência, alterações |
| 06 | [Permissões, grupos e CRUD](docs/06-permissoes-crud.md) | `sapl.rules`, `sapl.crud`, os 11 perfis de usuário |
| 07 | [API REST e interoperabilidade](docs/07-api-interoperabilidade.md) | drfautoapi, LexML/OAI-PMH, Solr, e-Cidadania |
| 08 | [Subindo um ambiente](docs/08-ambiente-local.md) | Docker Compose, ambiente de desenvolvimento |
| 09 | [Roteiro de estudo](docs/09-roteiro-de-estudo.md) | Ordem sugerida de leitura do código, exercícios |

## Como usar este material

O material foi escrito para ser lido **ao lado do código**. Clone o repositório oficial:

```bash
git clone --depth 1 https://github.com/interlegis/sapl
```

Todas as referências a arquivos (`sapl/materia/models.py:189`) apontam para esse clone.
