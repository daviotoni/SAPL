"""Matérias legislativas e tramitação, conforme o Regimento Interno da
CMDC (Resolução nº 1.835/2000 e alterações).

Referências regimentais:
- Art. 87, §1º — espécies de proposição.
- Art. 88 — hipóteses de inadmissibilidade (base da Análise Prévia).
- Art. 91 — regimes de tramitação: Urgência, Tramitação Especial,
  Prioridade e Tramitação Ordinária.
- Art. 54 — prazos de parecer: 3 (urgência), 9 (prioridade) e
  15 dias (ordinária).
- Art. 142 — hipóteses de prejudicialidade.
- Art. 95 — arquivamento ao fim da legislatura.

O Anteprojeto de Lei (APL) não consta do rol do art. 87: é o instrumento
de prática administrativa da CMDC pelo qual a proposição do gabinete
passa pela Análise Prévia da Procuradoria/Assessoria Técnica Legislativa
antes de se converter em projeto. Aqui é modelado como tipo de matéria
com ``exige_analise_previa=True``.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from parlamentares.models import Comissao, Vereador


class TipoMateria(models.Model):
    sigla = models.CharField('Sigla', max_length=10, unique=True)
    descricao = models.CharField('Descrição', max_length=100)
    exige_analise_previa = models.BooleanField(
        'Exige Análise Prévia?', default=False,
        help_text='APLs passam pela Análise Prévia da Procuradoria '
                  'antes de se converterem em projeto.')
    ordem = models.PositiveIntegerField('Ordem de exibição', default=100)

    class Meta:
        verbose_name = 'Tipo de Matéria'
        verbose_name_plural = 'Tipos de Matéria'
        ordering = ('ordem', 'sigla')

    def __str__(self):
        return f'{self.sigla} — {self.descricao}'


class Autor(models.Model):
    """Autoria unificada: vereador, Mesa, comissão, Executivo ou
    iniciativa popular (equivalente enxuto do Autor genérico do SAPL)."""

    class Tipo(models.TextChoices):
        VEREADOR = 'V', 'Vereador'
        MESA = 'M', 'Mesa Diretora'
        COMISSAO = 'C', 'Comissão'
        PREFEITO = 'P', 'Poder Executivo'
        POPULAR = 'I', 'Iniciativa Popular'

    tipo = models.CharField('Tipo', max_length=1, choices=Tipo.choices)
    vereador = models.OneToOneField(
        Vereador, on_delete=models.PROTECT, null=True, blank=True,
        related_name='autor', verbose_name='Vereador')
    comissao = models.OneToOneField(
        Comissao, on_delete=models.PROTECT, null=True, blank=True,
        related_name='autor', verbose_name='Comissão')
    nome = models.CharField(
        'Nome', max_length=200, blank=True,
        help_text='Preenchido automaticamente para vereador/comissão.')

    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'
        ordering = ('nome',)

    def clean(self):
        if self.tipo == self.Tipo.VEREADOR and not self.vereador:
            raise ValidationError(
                'Autor do tipo Vereador exige o vínculo com um vereador.')
        if self.tipo == self.Tipo.COMISSAO and not self.comissao:
            raise ValidationError(
                'Autor do tipo Comissão exige o vínculo com uma comissão.')

    def save(self, *args, **kwargs):
        if self.vereador:
            self.nome = self.vereador.nome_parlamentar
        elif self.comissao:
            self.nome = self.comissao.nome
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome or self.get_tipo_display()


class Materia(models.Model):
    class Regime(models.TextChoices):
        # Art. 91 do Regimento Interno.
        URGENCIA = 'U', 'Urgência'
        ESPECIAL = 'E', 'Tramitação Especial'
        PRIORIDADE = 'P', 'Prioridade'
        ORDINARIA = 'O', 'Tramitação Ordinária'

    tipo = models.ForeignKey(
        TipoMateria, on_delete=models.PROTECT, related_name='materias',
        verbose_name='Tipo')
    numero = models.PositiveIntegerField('Número')
    ano = models.PositiveIntegerField('Ano')
    processo_numero = models.PositiveIntegerField(
        'Nº do Processo', null=True, blank=True,
        help_text='Processo administrativo (Processo nº XXXX/AAAA).')
    processo_ano = models.PositiveIntegerField(
        'Ano do Processo', null=True, blank=True)
    ementa = models.TextField('Ementa')
    data_apresentacao = models.DateField('Data de Apresentação')
    regime = models.CharField(
        'Regime de Tramitação', max_length=1, choices=Regime.choices,
        default=Regime.ORDINARIA)
    em_tramitacao = models.BooleanField('Em tramitação?', default=True)
    apensada_a = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='apensadas', verbose_name='Apensada à matéria')
    materia_origem = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='materias_derivadas',
        verbose_name='Matéria de origem',
        help_text='Ex.: o APL que deu origem a este Projeto de Lei.')
    texto = models.FileField(
        'Texto integral', upload_to='materias/%Y/', blank=True)
    observacao = models.TextField('Observação', blank=True)
    autores = models.ManyToManyField(
        Autor, through='Autoria', related_name='materias',
        verbose_name='Autores')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Matéria Legislativa'
        verbose_name_plural = 'Matérias Legislativas'
        ordering = ('-ano', '-numero')
        constraints = [
            models.UniqueConstraint(fields=('tipo', 'numero', 'ano'),
                                    name='materia_unica'),
        ]

    def __str__(self):
        return f'{self.tipo.sigla} {self.numero}/{self.ano}'

    @property
    def tramitacao_atual(self):
        return self.tramitacoes.order_by('-data', '-id').first()

    def transformar_em(self, tipo_destino, numero, data_apresentacao):
        """Converte APL admitido em projeto (novo registro vinculado)."""
        nova = Materia.objects.create(
            tipo=tipo_destino,
            numero=numero,
            ano=data_apresentacao.year,
            ementa=self.ementa,
            data_apresentacao=data_apresentacao,
            regime=self.regime,
            materia_origem=self,
            processo_numero=self.processo_numero,
            processo_ano=self.processo_ano,
        )
        for autoria in self.autoria_set.all():
            Autoria.objects.create(materia=nova, autor=autoria.autor,
                                   principal=autoria.principal)
        self.em_tramitacao = False
        self.save(update_fields=['em_tramitacao'])
        return nova


class Autoria(models.Model):
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    autor = models.ForeignKey(Autor, on_delete=models.PROTECT,
                              verbose_name='Autor')
    principal = models.BooleanField(
        'Primeiro signatário?', default=True,
        help_text='Art. 88, §2º: considera-se autor o primeiro '
                  'signatário. Coautoria admitida (§3º).')

    class Meta:
        verbose_name = 'Autoria'
        verbose_name_plural = 'Autorias'
        constraints = [
            models.UniqueConstraint(fields=('materia', 'autor'),
                                    name='autoria_unica'),
        ]

    def __str__(self):
        return f'{self.autor} — {self.materia}'


class AnalisePrevia(models.Model):
    """Análise Prévia da Procuradoria/Assessoria Técnica Legislativa.

    Exame de admissibilidade (art. 88 do RI), prejudicialidade
    (art. 142 do RI), constitucionalidade e técnica legislativa dos
    Anteprojetos de Lei e demais proposições, prévio à tramitação.
    """

    class Item(models.TextChoices):
        SEM_VICIO = 'OK', 'Sem óbice'
        RESSALVA = 'RE', 'Com ressalvas'
        VICIO = 'VI', 'Com vício/óbice'
        NAO_SE_APLICA = 'NA', 'Não se aplica'

    class Conclusao(models.TextChoices):
        ADMISSIVEL = 'A', 'Admissível — apto a tramitar'
        ADMISSIVEL_RESSALVAS = 'R', 'Admissível com ressalvas'
        INADMISSIVEL = 'I', 'Inadmissível (art. 88, RI)'
        PREJUDICADA = 'P', 'Prejudicada (art. 142, RI)'

    materia = models.ForeignKey(
        Materia, on_delete=models.CASCADE, related_name='analises_previas',
        verbose_name='Matéria')
    data = models.DateField('Data da análise')
    admissibilidade_art88 = models.CharField(
        'Admissibilidade (art. 88, RI)', max_length=2,
        choices=Item.choices, default=Item.SEM_VICIO)
    prejudicialidade_art142 = models.CharField(
        'Prejudicialidade (art. 142, RI)', max_length=2,
        choices=Item.choices, default=Item.SEM_VICIO)
    constitucionalidade_material = models.CharField(
        'Constitucionalidade material', max_length=2,
        choices=Item.choices, default=Item.SEM_VICIO)
    constitucionalidade_formal_objetiva = models.CharField(
        'Constitucionalidade formal objetiva (processo legislativo)',
        max_length=2, choices=Item.choices, default=Item.SEM_VICIO)
    constitucionalidade_formal_subjetiva = models.CharField(
        'Constitucionalidade formal subjetiva (iniciativa)',
        max_length=2, choices=Item.choices, default=Item.SEM_VICIO)
    tecnica_legislativa = models.CharField(
        'Técnica legislativa (art. 92, RI)', max_length=2,
        choices=Item.choices, default=Item.SEM_VICIO)
    fundamentacao = models.TextField(
        'Fundamentação', blank=True,
        help_text='Análise desenvolvida item a item.')
    conclusao = models.CharField(
        'Conclusão', max_length=1, choices=Conclusao.choices)
    responsavel = models.CharField(
        'Responsável pela análise', max_length=150, blank=True)
    arquivo = models.FileField(
        'Arquivo da Análise', upload_to='analises/%Y/', blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Análise Prévia'
        verbose_name_plural = 'Análises Prévias'
        ordering = ('-data', '-id')

    def __str__(self):
        return (f'Análise Prévia — {self.materia} — '
                f'{self.get_conclusao_display()}')


class UnidadeTramitacao(models.Model):
    nome = models.CharField('Nome', max_length=150, unique=True)
    ativa = models.BooleanField('Ativa', default=True)

    class Meta:
        verbose_name = 'Unidade de Tramitação'
        verbose_name_plural = 'Unidades de Tramitação'
        ordering = ('nome',)

    def __str__(self):
        return self.nome


class StatusTramitacao(models.Model):
    descricao = models.CharField('Descrição', max_length=100, unique=True)
    fim_tramitacao = models.BooleanField(
        'Encerra a tramitação?', default=False)

    class Meta:
        verbose_name = 'Status de Tramitação'
        verbose_name_plural = 'Status de Tramitação'
        ordering = ('descricao',)

    def __str__(self):
        return self.descricao


class Tramitacao(models.Model):
    materia = models.ForeignKey(
        Materia, on_delete=models.CASCADE, related_name='tramitacoes',
        verbose_name='Matéria')
    data = models.DateField('Data')
    unidade_origem = models.ForeignKey(
        UnidadeTramitacao, on_delete=models.PROTECT,
        related_name='tramitacoes_origem', verbose_name='Unidade de origem')
    unidade_destino = models.ForeignKey(
        UnidadeTramitacao, on_delete=models.PROTECT,
        related_name='tramitacoes_destino',
        verbose_name='Unidade de destino')
    status = models.ForeignKey(
        StatusTramitacao, on_delete=models.PROTECT, verbose_name='Status')
    despacho = models.TextField('Texto do despacho', blank=True)
    data_prazo = models.DateField(
        'Prazo regimental', null=True, blank=True,
        help_text='Art. 54, RI: 3 dias (urgência), 9 (prioridade), '
                  '15 (ordinária) para parecer de comissão.')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, verbose_name='Usuário')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tramitação'
        verbose_name_plural = 'Tramitações'
        ordering = ('-data', '-id')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status.fim_tramitacao and self.materia.em_tramitacao:
            self.materia.em_tramitacao = False
            self.materia.save(update_fields=['em_tramitacao'])

    def __str__(self):
        return f'{self.materia} — {self.status} ({self.data:%d/%m/%Y})'


class Parecer(models.Model):
    class Sentido(models.TextChoices):
        FAVORAVEL = 'F', 'Favorável'
        CONTRARIO = 'C', 'Contrário'
        FAVORAVEL_EMENDAS = 'E', 'Favorável com emendas'

    materia = models.ForeignKey(
        Materia, on_delete=models.CASCADE, related_name='pareceres',
        verbose_name='Matéria')
    comissao = models.ForeignKey(
        Comissao, on_delete=models.PROTECT, related_name='pareceres',
        verbose_name='Comissão')
    relator = models.ForeignKey(
        Vereador, on_delete=models.PROTECT, null=True, blank=True,
        related_name='relatorias', verbose_name='Relator')
    sentido = models.CharField(
        'Sentido', max_length=1, choices=Sentido.choices)
    data = models.DateField('Data')
    texto = models.TextField('Texto/ementa do parecer', blank=True)
    arquivo = models.FileField(
        'Arquivo', upload_to='pareceres/%Y/', blank=True)

    class Meta:
        verbose_name = 'Parecer de Comissão'
        verbose_name_plural = 'Pareceres de Comissões'
        ordering = ('-data',)

    def __str__(self):
        return (f'Parecer {self.get_sentido_display().lower()} — '
                f'{self.comissao} — {self.materia}')


class DocumentoAcessorio(models.Model):
    materia = models.ForeignKey(
        Materia, on_delete=models.CASCADE, related_name='documentos',
        verbose_name='Matéria')
    descricao = models.CharField('Descrição', max_length=200)
    data = models.DateField('Data', null=True, blank=True)
    arquivo = models.FileField(
        'Arquivo', upload_to='documentos/%Y/', blank=True)

    class Meta:
        verbose_name = 'Documento Acessório'
        verbose_name_plural = 'Documentos Acessórios'
        ordering = ('-data', '-id')

    def __str__(self):
        return f'{self.descricao} — {self.materia}'
