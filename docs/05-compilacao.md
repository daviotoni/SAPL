# 05 — Compilação de textos articulados

`sapl.compilacao` (8.866 linhas) é o subsistema mais sofisticado do SAPL e uma das
principais novidades da versão 3.1. Ele responde a uma pergunta que um PDF nunca responde:

> **"Qual era a redação do art. 12 desta lei em 3 de março de 2019?"**

## A ideia central

Em vez de tratar a lei como um arquivo, o SAPL a trata como uma **árvore de dispositivos
com vigência temporal**. Cada artigo, parágrafo, inciso e alínea é uma linha no banco, com
data de início e fim de vigência próprias. Alterar um artigo não sobrescreve nada: cria um
novo `Dispositivo`, com nova vigência, apontando para o que substituiu.

## Modelos principais

| Modelo | Papel |
|---|---|
| `TextoArticulado` | O documento articulado. Ligado por `GenericRelation` a `NormaJuridica`, `MateriaLegislativa` ou `Proposicao` |
| `TipoTextoArticulado` | Configura o comportamento por tipo de documento |
| **`Dispositivo`** | A unidade atômica: um artigo, um inciso, uma alínea |
| `TipoDispositivo` | Define o que é "Artigo", "Parágrafo", "Inciso"… e como se numera e renderiza |
| `TipoDispositivoRelationship` | Regras de aninhamento: o que pode ser filho de quê |
| `PerfilEstruturalTextoArticulado` | Conjunto de tipos e regras — permite perfis distintos (lei municipal, regimento, constituição estadual) |
| `Nota`, `TipoNota` | Notas anexadas a dispositivos |
| `Vide`, `TipoVide` | Remissões entre dispositivos ("vide art. 5º") |
| `Publicacao`, `TipoPublicacao`, `VeiculoPublicacao` | Publicação oficial |
| `BaseModel`, `TimestampedMixin` | Infraestrutura comum |

## Anatomia do `Dispositivo`

O modelo (`sapl/compilacao/models.py:954`) tem quatro grupos de campos:

### 1. Posição na árvore

```python
ordem                      # ordem de renderização (passo INTERVALO_ORDEM = 1000)
nivel                      # profundidade; só a articulação recebe nível zero
dispositivo0               # número do dispositivo
dispositivo1 .. dispositivo5   # cinco níveis de variação
```

O salto de 1.000 em `ordem` é um truque clássico: permite inserir dispositivos entre dois
existentes sem renumerar a tabela inteira.

Os campos `dispositivo0..5` implementam a numeração **variante** do direito brasileiro —
`art. 5º-A`, `art. 5º-A-1`. São seis inteiros justamente porque a prática legislativa
permite emendar em profundidade sem renumerar o restante da lei.

### 2. Vigência e eficácia — quatro datas, não duas

```python
inicio_vigencia,  fim_vigencia
inicio_eficacia,  fim_eficacia
```

A distinção é jurídica, não redundância: uma norma pode estar **vigente** mas ainda não ser
**eficaz** (*vacatio legis*), ou ter perdido eficácia continuando vigente. Modelar as duas
separadamente é o que permite ao sistema responder corretamente sobre qualquer data.

Há ainda `inconstitucionalidade` — marcação de dispositivo declarado inconstitucional, que
não é o mesmo que revogado.

### 3. Texto e relação com o dispositivo alterador

```python
texto                  # a redação do dispositivo
texto_atualizador      # como o dispositivo aparece *dentro* do dispositivo que o alterou
rotulo                 # "Art. 5º", "§ 1º", "I -"
```

`texto_atualizador` é a chave da compilação: quando a Lei B altera o art. 5º da Lei A, o
mesmo conteúdo precisa ser exibido de duas formas — como a nova redação vigente na Lei A, e
como o comando ("Art. 5º passa a vigorar com a seguinte redação…") dentro da Lei B. Um
único registro serve aos dois contextos, e `ordem_bloco_atualizador` ordena os dispositivos
dentro do bloco alterador.

Há ainda `TEXTO_PADRAO_DISPOSITIVO_REVOGADO = "(Revogado)"` e `auto_inserido`, para
dispositivos criados automaticamente pela estrutura.

### 4. Ligações

Dispositivos apontam para o pai, para o `TextoArticulado`, para o dispositivo que os
atualizou e para a `Publicacao` correspondente — formando o grafo que permite navegar da
redação atual até a redação original passando por cada alteração.

## `TipoDispositivo` — a gramática configurável

Aqui está a razão de o módulo ser grande: a estrutura de uma lei **não é fixa** entre Casas
e tipos de documento. `TipoDispositivo` parametriza:

```python
FORMATO_NUMERACAO_CHOICES = (
    ('1', '1-Numérico'),
    ('I', 'I-Romano Maiúsculo'),
    ('i', 'i-Romano Minúsculo'),
    ('A', 'A-Alfabético Maiúsculo'),
    ('a', 'a-Alfabético Minúsculo'),
    ('*', 'Tópico - Sem contagem'),
    ('N', 'Sem renderização'),
)

TIPO_NUMERO_ROTULO = (
    ( 0, 'Numeração Cardinal.'),
    (-1, 'Numeração Ordinal.'),
    ( 9, 'Numeração Ordinal até o item nove.'),
)
```

A terceira opção codifica uma regra real da técnica legislativa brasileira: escreve-se
"Art. 1º … Art. 9º" (ordinal) e, a partir do décimo, "Art. 10" (cardinal). O SAPL trata
isso como dado configurável, não como `if` no código.

Outros campos configuram `class_css`, `rotulo_prefixo_html` (renderização) e
`rotulo_prefixo_texto` (edição). O docstring do modelo documenta o comportamento do `;` no
prefixo: se o dispositivo é filho único do seu pai, usa-se o rótulo alternativo após o
ponto e vírgula — a regra de "Parágrafo único" versus "§ 1º".

`TipoDispositivoRelationship` define quais tipos podem ser filhos de quais, e
`PerfilEstruturalTextoArticulado` agrupa tudo num perfil aplicável a um tipo de documento.

## Por que isso importa

Sem compilação, uma Casa publica a lei original e, separadamente, cada lei alteradora — e o
cidadão precisa reconstruir mentalmente o texto vigente. Com compilação:

- consulta-se a **redação vigente hoje** ou **em qualquer data passada**;
- cada dispositivo mostra seu **histórico de alterações**;
- revogações e inconstitucionalidades ficam **visíveis no texto**, não em nota de rodapé;
- o texto é **estruturado**, então é citável, referenciável (`Vide`) e exportável.

É a mesma ideia por trás do LexML e do padrão *Akoma Ntoso*: lei como dado estruturado, não
como documento.

## Por onde entrar no código

1. `sapl/compilacao/models.py` — comece por `TipoDispositivo` (l. 590) e só depois
   `Dispositivo` (l. 954); a ordem inversa confunde.
2. `sapl/compilacao/views.py` — o editor de dispositivos (a parte mais dependente de JS).
3. `sapl/compilacao/utils.py` e os *templatetags* — a renderização do texto articulado.
4. `frontend/src/` — os componentes Vue do editor.
