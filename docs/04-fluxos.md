# 04 — Fluxos do processo legislativo no SAPL

Este documento percorre o ciclo de vida de uma proposição, do gabinete até virar lei
consolidada, indicando **onde cada etapa vive no código**.

## Visão geral do ciclo

```
 [gabinete]        [protocolo]        [secretaria]         [plenário]        [publicação]
 Proposicao ──▶ Protocolo ──▶ MateriaLegislativa ──▶ SessaoPlenaria ──▶ NormaJuridica
     │                              │  ▲                    │                  │
     │                         Tramitacao (loop)      RegistroVotacao      Dispositivo
     │                              │                 VotoParlamentar      (compilação)
     └── hash_code / recibo    Relatoria/Parecer                                │
                                                                          rede LexML
```

## 1. Proposição — o rascunho do autor

**Modelo:** `Proposicao` (`sapl/materia/models.py:858`)

Um usuário do grupo **Autor** (vinculado a um `Autor` por `OperadorAutor`) cria uma
proposição: escolhe `TipoProposicao`, escreve a `descricao` (ementa) e anexa o texto — ou o
redige diretamente no editor de texto articulado (`GenericRelation` para `TextoArticulado`).

A proposição não tem número oficial ainda. Seus estados são derivados de campos de data, e
não de uma máquina de estados explícita:

| Estado | Como é determinado |
|---|---|
| Em elaboração | `data_envio is None` |
| Enviada | `data_envio` preenchida, `data_recebimento` nula |
| Recebida / incorporada | `data_recebimento` preenchida |
| Devolvida | `data_devolucao` preenchida + `justificativa_devolucao` |

O código comenta explicitamente que o campo `status` é redundante ("FIXME Campo não é
necessário na modelagem e implementação atual"). Vale saber disso antes de confiar nele.

Ao enviar, o sistema gera um **`hash_code`** e emite um recibo — a prova de que o gabinete
protocolou naquele instante. Cada transição fica em `HistoricoProposicao`.

## 2. Recebimento e protocolo

O servidor do grupo **Operador de Protocolo Administrativo** vê a fila de proposições
enviadas e decide:

- **Devolver** — grava `data_devolucao`, `usuario_devolucao` e a justificativa.
- **Receber/incorporar** — gera um `Protocolo` (`numero/ano`, com `de_proposicao=True`) e
  materializa o objeto definitivo.

A materialização usa uma `GenericForeignKey` na própria `Proposicao`
(`content_type` + `object_id` → `content_object`): dependendo do `TipoProposicao`, a
proposição vira uma **`MateriaLegislativa`**, um **`DocumentoAcessorio`** ou um
**`DocumentoAdministrativo`**. Esse ponteiro genérico é o que permite rastrear, depois, de
qual rascunho veio cada matéria.

> **Protocolo nunca é apagado.** Anular exige a permissão customizada
> `action_anular_protocolo` (declarada em `Protocolo.Meta.permissions`) e grava motivo,
> usuário, IP e timestamp da anulação.

## 3. Matéria legislativa — o objeto oficial

**Modelo:** `MateriaLegislativa` (`sapl/materia/models.py:189`)

Agora existe `PL 42/2026`, com `ementa`, `data_apresentacao`, `regime_tramitacao`,
`texto_original` e `em_tramitacao=True`. A partir daqui, giram em torno dela:

- **`Autoria`** — um ou mais autores, com indicação do autor principal.
- **`DespachoInicial`** — encaminhamento às comissões competentes.
- **`Anexada`** — apensamento a outra matéria (auto-relacionamento N:N via
  `materia_principal` / `materia_anexada`).
- **`Relatoria`** → **`Parecer`** — designação de relator na comissão e parecer emitido.
- **`DocumentoAcessorio`** — emendas, substitutivos, ofícios juntados.
- **`LegislacaoCitada`** — normas citadas no texto.
- **`AcompanhamentoMateria`** — cidadão cadastra e-mail para ser notificado (endpoint
  público, protegido por reCAPTCHA desde 3.1.162).

A geração do próximo número foi **centralizada** em 3.1.165 (issue #3821) — antes havia
mais de um caminho para numerar matéria, com risco de colisão.

## 4. Tramitação — o loop

**Modelo:** `Tramitacao` (`sapl/materia/models.py:1282`)

Cada passo registra `unidade_tramitacao_local` → `unidade_tramitacao_destino`, um
`StatusTramitacao`, `data_tramitacao`, `data_encaminhamento`, `turno`, `urgente`,
`data_fim_prazo` e o `texto` da ação. Guarda também `user`, `ip` e `ultima_edicao`.

Como consultar "onde está a matéria agora" é a operação mais frequente do sistema, existe
`MateriaEmTramitacao` — um modelo com `managed = False` mapeado sobre a **view de banco**
`materia_materiaemtramitacao`, que já entrega matéria + última tramitação + unidade atual
sem subconsulta.

Quando um `StatusTramitacao` marcado como fim de tramitação é aplicado, `em_tramitacao`
volta a `False`.

Documentos administrativos têm um fluxo espelhado e independente:
`TramitacaoAdministrativo` + `StatusTramitacaoAdministrativo`.

## 5. Pauta e sessão plenária

**Modelos:** `SessaoPlenaria`, `OrdemDia`, `ExpedienteMateria` (`sapl/sessao/models.py`)

O Operador de Sessão Plenária cria a `SessaoPlenaria` (tipo, data, legislatura, sessão
legislativa) e monta a pauta incluindo matérias em dois blocos, ambos derivados de
`AbstractOrdemDia`:

- **`ExpedienteMateria`** — matérias do Expediente
- **`OrdemDia`** — matérias da Ordem do Dia

Desde 3.1.165 é possível **selecionar o tipo de votação para várias matérias de uma vez**
ao incluí-las na pauta (#3781).

Durante a sessão registram-se: `SessaoPlenariaPresenca` e `PresencaOrdemDia` (presença é
apurada duas vezes), `IntegranteMesa`, oradores (`OradorExpediente`, `OradorOrdemDia`),
`ExpedienteSessao` (matérias de expediente por tipo), `OcorrenciaSessao`,
`ConsideracoesFinais`, `RetiradaPauta` e `JustificativaAusencia`.

## 6. Votação

Duas camadas complementares:

| Modelo | Conteúdo |
|---|---|
| `RegistroVotacao` | Placar agregado: `numero_votos_sim`, `numero_votos_nao`, `numero_abstencoes`, `tipo_resultado_votacao`, ligado a **`ordem` XOR `expediente`** |
| `VotoParlamentar` | Voto individual por parlamentar (votação nominal) |

Modalidades:

- **Simbólica** — o operador digita o placar; nasce só um `RegistroVotacao`.
- **Nominal** — chamada parlamentar a parlamentar, com `VotoParlamentar` por votante.
- **Interativa (painel eletrônico)** — os parlamentares votam de suas estações; os
  `VotoParlamentar` são gravados **antes** do `RegistroVotacao` existir, e por isso carregam
  `ordem`/`expediente` redundantes. Só quem tem registro em `Votante` pode votar.
- **Leitura** — `RegistroLeitura`, para matérias apenas lidas em plenário.

O `RegistroVotacao.clean()` impede o estado inconsistente de uma votação pertencer
simultaneamente à Ordem do Dia e ao Expediente.

Do resultado sai a **ata** e o **resumo da sessão**, gerados em `sapl.relatorios` com a
ordem de blocos definida por `ResumoOrdenacao`.

## 7. Norma jurídica

Aprovada e sancionada, a matéria vira **`NormaJuridica`**: tipo, número, ano, ementa, data
de publicação, veículo e texto. O vínculo com a matéria de origem é preservado, e o grafo
de `NormaRelacionada` (tipado por `TipoVinculoNormaJuridica`) registra o que ela **altera,
revoga, regulamenta** — e o que a alterou depois.

## 8. Consolidação e publicação

- **Compilação** (`sapl.compilacao`): o texto da norma é decomposto em `Dispositivo`s com
  vigência própria, permitindo consultar a redação vigente em qualquer data — ver
  [doc 05](05-compilacao.md).
- **Busca**: Haystack + Solr indexam ementa, indexação e o texto integral dos arquivos.
- **LexML**: o servidor OAI-PMH (`sapl/lexml/OAIServer.py`) expõe as normas para colheita
  pela rede nacional LexML.
- **Portal público e API**: consulta anônima a matérias, normas, pautas e sessões, mais os
  endpoints `ecidadania` usados por aplicações de transparência.
