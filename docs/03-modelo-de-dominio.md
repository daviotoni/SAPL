# 03 — Modelo de domínio

O SAPL tem **mais de 130 modelos**. Este documento mapeia os que sustentam o domínio,
agrupados por app. Ler `models.py` de cada app é, na prática, ler uma tradução do
Regimento Interno de uma Casa Legislativa para tabelas.

## `sapl.base` — a fundação

| Modelo | Papel |
|---|---|
| `CasaLegislativa` | Identidade da instância: nome, sigla, endereço, brasão |
| `AppConfig` | Configurações de comportamento da instância (singleton) |
| `TipoAutor` / `Autor` | **Autoria genérica**: `Autor` aponta por `GenericForeignKey` para `Parlamentar`, `Comissao`, `Bancada`, `Bloco` ou entidade externa |
| `OperadorAutor` | Liga um usuário do sistema a um `Autor` (é assim que um gabinete opera em nome do parlamentar) |
| `AuditLog` | Trilha de auditoria por modelo/objeto |
| `Metadata` | Metadados livres associáveis a registros |

O par `Autor` + `OperadorAutor` é a peça mais importante para entender permissões: o grupo
**Autor** só enxerga as proposições dos autores a que o usuário está vinculado.

## `sapl.parlamentares` — quem legisla

| Modelo | Papel |
|---|---|
| `Legislatura`, `SessaoLegislativa` | Recorte temporal (a legislatura de 4 anos e suas sessões anuais) |
| `Parlamentar` | A pessoa: dados civis, foto, biografia, situação |
| `Mandato` | Vínculo `Parlamentar` × `Legislatura`, com `TipoAfastamento` |
| `Partido`, `Filiacao`, `Coligacao`, `ComposicaoColigacao` | Vida partidária, com histórico datado |
| `MesaDiretora`, `CargoMesa`, `ComposicaoMesa` | Mesa Diretora por sessão legislativa |
| `Bloco`, `BlocoCargo`, `BlocoMembro` | Blocos parlamentares |
| `Frente`, `FrenteCargo`, `FrenteParlamentar` | Frentes parlamentares |
| `Votante` | Habilita um parlamentar a votar no painel eletrônico |
| `Dependente`, `TipoDependente`, `NivelInstrucao`, `SituacaoMilitar` | Cadastro civil complementar |

Repare que quase tudo é **temporalizado**: filiação, mandato e composição têm data de
início e fim, porque uma consulta a uma sessão de 2019 precisa refletir a composição
*daquela* data, não a de hoje.

## `sapl.protocoloadm` — a porta de entrada

| Modelo | Papel |
|---|---|
| `Protocolo` | Numeração `numero/ano` única, data/hora, interessado, autor, tipo de processo. Suporta **anulação** com justificativa, usuário e IP — nunca exclusão |
| `TipoDocumentoAdministrativo`, `DocumentoAdministrativo` | Documentos administrativos (ofícios, requerimentos internos) |
| `TramitacaoAdministrativo`, `StatusTramitacaoAdministrativo` | Tramitação paralela, espelhando a de matérias |
| `Anexado`, `VinculoDocAdminMateria` | Anexação entre documentos e vínculo com matérias legislativas |
| `DocumentoAcessorioAdministrativo` | Anexos |
| `AcompanhamentoDocumento` | Cidadão pede para ser avisado por e-mail sobre um documento |

O `Protocolo` guarda `user`, `ip`, `timestamp` e ainda campos separados para o caso de
**data/hora informadas manualmente** (`timestamp_data_hora_manual`, `user_data_hora_manual`,
`ip_data_hora_manual`). É um cuidado deliberado: o protocolo é ato com fé pública e o
sistema precisa distinguir o carimbo automático do carimbo declarado por servidor.

## `sapl.materia` — o coração (28 modelos)

| Modelo | Papel |
|---|---|
| `TipoMateriaLegislativa` | PL, PLC, PEC, Requerimento, Indicação… configurável por Casa |
| **`MateriaLegislativa`** | A proposição formalizada: `tipo`, `numero`, `ano`, `ementa`, `data_apresentacao`, `regime_tramitacao`, `em_tramitacao`, `texto_original`, indexação, origem externa, apelido, prazo |
| `Autoria` | N:N entre `MateriaLegislativa` e `Autor` (com autor principal) |
| **`Proposicao`** | A matéria *antes* de existir: rascunho do gabinete, com `data_envio`, `data_recebimento`, `data_devolucao` e `hash_code` |
| `HistoricoProposicao` | Trilha das transições da proposição |
| **`Tramitacao`** | Cada passo: `status`, `data_tramitacao`, `unidade_tramitacao_local` → `unidade_tramitacao_destino`, `turno`, `urgente`, `texto` |
| `UnidadeTramitacao` | Órgão/comissão/parlamentar que pode receber uma matéria |
| `StatusTramitacao` | Situação (com indicador de fim de tramitação) |
| `MateriaEmTramitacao` | **View de banco** (`managed = False`) com a última tramitação de cada matéria — otimização de consulta |
| `Relatoria`, `Parecer`, `TipoFimRelatoria` | Designação de relator e parecer |
| `DespachoInicial` | Encaminhamento às comissões |
| `Anexada` | Apensamento de matérias (auto-relacionamento N:N) |
| `Numeracao` | Numerações alternativas/históricas |
| `DocumentoAcessorio`, `TipoDocumento` | Anexos da matéria |
| `AssuntoMateria`, `MateriaAssunto` | Classificação temática |
| `AcompanhamentoMateria` | Cidadão acompanha por e-mail (público, com reCAPTCHA) |
| `Orgao`, `Origem` | Entidades externas de origem |
| `PautaReuniao`, `ConfigEtiquetaMateriaLegislativa` | Apoio operacional |

O enum `Tramitacao.TURNO_CHOICES` é um bom retrato da flexibilidade exigida: primeiro,
segundo, único, suplementar, final, "1ª e 2ª votações", "votação única em regime de
urgência" — porque cada Regimento Interno tem sua liturgia.

## `sapl.comissoes`

`TipoComissao` → `Comissao` → `Periodo` → `Composicao` → `Participacao` (com `CargoComissao`).
`Reuniao` registra as reuniões, com `DocumentoAcessorio` próprio. A composição é datada por
período, pelo mesmo motivo temporal já citado.

## `sapl.sessao` — o plenário (28 modelos)

| Grupo | Modelos |
|---|---|
| Sessão | `TipoSessaoPlenaria`, **`SessaoPlenaria`** (abertura, encerramento, legislatura, sessão legislativa) |
| Pauta | `AbstractOrdemDia` → `OrdemDia` e `ExpedienteMateria`; `TipoExpediente`, `ExpedienteSessao` |
| Presença | `SessaoPlenariaPresenca`, `PresencaOrdemDia`, `JustificativaAusencia`, `TipoJustificativa` |
| Mesa | `IntegranteMesa` |
| Oradores | `AbstractOrador` → `Orador`, `OradorExpediente`, `OradorOrdemDia` |
| **Votação** | `TipoResultadoVotacao`, **`RegistroVotacao`**, **`VotoParlamentar`** |
| Bancadas | `Bancada`, `CargoBancada` |
| Outros | `RetiradaPauta`, `TipoRetiradaPauta`, `RegistroLeitura`, `OcorrenciaSessao`, `ConsideracoesFinais`, `Correspondencia`, `ResumoOrdenacao` |

Dois detalhes valem atenção:

- `RegistroVotacao` guarda o **placar agregado** (`numero_votos_sim`, `numero_votos_nao`,
  `numero_abstencoes`) e tem um `clean()` que exige **exatamente um** de `ordem` ou
  `expediente` preenchido — uma matéria é votada ou na Ordem do Dia ou no Expediente, nunca
  nos dois.
- `VotoParlamentar` guarda o **voto individual** (votação nominal). O próprio código
  documenta a redundância de `ordem`/`expediente` nele: na votação interativa pelo painel,
  os votos chegam *antes* de existir um `RegistroVotacao`, então precisam de identificação
  própria.
- `ResumoOrdenacao` permite que cada Casa defina a ordem dos blocos na ata/resumo da sessão.

## `sapl.painel`

Minúsculo (`Painel`, `Cronometro`) e propositalmente assim: o painel eletrônico é sobretudo
**frontend em tempo real** consumindo a API de sessão. O modelo só guarda o estado corrente
do painel e os cronômetros (discurso, aparte, questão de ordem).

## `sapl.norma` — o produto final

| Modelo | Papel |
|---|---|
| **`NormaJuridica`** | Lei, decreto, resolução: tipo, número, ano, ementa, data de publicação, veículo, texto integral |
| `TipoNormaJuridica`, `AssuntoNorma` | Classificação |
| `AutoriaNorma` | Autoria da norma |
| `LegislacaoCitada` | Normas citadas por uma matéria |
| `NormaRelacionada`, `TipoVinculoNormaJuridica` | Grafo entre normas: altera, revoga, regulamenta, é revogada por… |
| `AnexoNormaJuridica` | Anexos |
| `NormaEstatisticas`, `ViewNormasEstatisticas` | Estatísticas (a segunda é *view* de banco) |

`NormaRelacionada` + `TipoVinculoNormaJuridica` formam um **grafo dirigido e tipado de
normas**. É o que permite responder "esta lei ainda vigora?" navegando as relações de
revogação — e é a ponte para o módulo de compilação.

## `sapl.audiencia` e `sapl.lexml`

- `TipoAudienciaPublica`, `AudienciaPublica`, `AnexoAudienciaPublica`: agenda e registro de
  audiências públicas, vinculáveis a matérias.
- `LexmlProvedor`, `LexmlPublicador`: identificação da Casa como provedora de dados na rede
  **LexML** (ver [doc 07](07-api-interoperabilidade.md)).

## `sapl.compilacao`

Tratado à parte em [doc 05](05-compilacao.md) — é o subsistema mais sofisticado do projeto.
