"""Sessões plenárias da CMDC.

Referências regimentais (Resolução nº 1.835/2000 e alterações):
- Art. 74 — espécies: preparatórias, ordinárias, extraordinárias e
  solenes. Ordinárias às terças, quartas e quintas-feiras, das 17h30
  às 19h30 (redação da Resolução nº 2.398/2013); extraordinárias com
  duração máxima de três horas.
- Art. 75 — partes da sessão ordinária: Expediente Inicial (60 min,
  art. 78), Ordem do Dia e Expediente Final.
- Art. 162 — aprovadas em 1º turno, as proposições vão à Comissão de
  Legislação, Justiça e Redação Final para Redação Final.
"""
from django.core.exceptions import ValidationError
from django.db import models

from core.models import SessaoLegislativa
from materias.models import Materia
from parlamentares.models import Vereador


class SessaoPlenaria(models.Model):
    class Tipo(models.TextChoices):
        # Art. 74 do Regimento Interno.
        PREPARATORIA = 'P', 'Preparatória'
        ORDINARIA = 'O', 'Ordinária'
        EXTRAORDINARIA = 'E', 'Extraordinária'
        SOLENE = 'S', 'Solene'

    tipo = models.CharField('Tipo', max_length=1, choices=Tipo.choices,
                            default=Tipo.ORDINARIA)
    numero = models.PositiveIntegerField('Número')
    sessao_legislativa = models.ForeignKey(
        SessaoLegislativa, on_delete=models.PROTECT,
        related_name='sessoes_plenarias',
        verbose_name='Sessão Legislativa')
    data = models.DateField('Data')
    hora_inicio = models.TimeField('Hora de início', null=True, blank=True)
    hora_fim = models.TimeField('Hora de encerramento', null=True,
                                blank=True)
    ata_arquivo = models.FileField(
        'Ata da sessão', upload_to='atas/%Y/', blank=True,
        help_text='Versão final revisada pelo Setor de Atas.')
    resumo = models.TextField('Resumo/observações', blank=True)

    class Meta:
        verbose_name = 'Sessão Plenária'
        verbose_name_plural = 'Sessões Plenárias'
        ordering = ('-data', '-numero')
        constraints = [
            models.UniqueConstraint(
                fields=('tipo', 'numero', 'sessao_legislativa'),
                name='sessao_unica'),
        ]

    def __str__(self):
        return (f'{self.numero}ª Sessão {self.get_tipo_display()} — '
                f'{self.data:%d/%m/%Y}')


class PresencaSessao(models.Model):
    sessao = models.ForeignKey(
        SessaoPlenaria, on_delete=models.CASCADE, related_name='presencas',
        verbose_name='Sessão')
    vereador = models.ForeignKey(
        Vereador, on_delete=models.PROTECT, related_name='presencas',
        verbose_name='Vereador')
    presente = models.BooleanField('Presente?', default=True)
    justificativa = models.CharField(
        'Justificativa de ausência', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Presença'
        verbose_name_plural = 'Presenças'
        constraints = [
            models.UniqueConstraint(fields=('sessao', 'vereador'),
                                    name='presenca_unica'),
        ]

    def __str__(self):
        estado = 'presente' if self.presente else 'ausente'
        return f'{self.vereador} — {estado} — {self.sessao}'


class ItemPauta(models.Model):
    class Fase(models.TextChoices):
        # Art. 75 do Regimento Interno.
        EXPEDIENTE_INICIAL = 'EI', 'Expediente Inicial'
        ORDEM_DO_DIA = 'OD', 'Ordem do Dia'
        EXPEDIENTE_FINAL = 'EF', 'Expediente Final'

    class Turno(models.TextChoices):
        UNICO = 'U', 'Turno único'
        PRIMEIRO = '1', 'Primeiro turno'
        SEGUNDO = '2', 'Segundo turno'
        REDACAO_FINAL = 'R', 'Redação Final'

    sessao = models.ForeignKey(
        SessaoPlenaria, on_delete=models.CASCADE, related_name='pauta',
        verbose_name='Sessão')
    fase = models.CharField('Fase', max_length=2, choices=Fase.choices,
                            default=Fase.ORDEM_DO_DIA)
    ordem = models.PositiveIntegerField('Ordem na pauta', default=1)
    materia = models.ForeignKey(
        Materia, on_delete=models.PROTECT, related_name='itens_pauta',
        verbose_name='Matéria')
    turno = models.CharField('Turno', max_length=1, choices=Turno.choices,
                             default=Turno.UNICO)
    observacao = models.CharField('Observação', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Item de Pauta'
        verbose_name_plural = 'Itens de Pauta'
        ordering = ('sessao', 'fase', 'ordem')

    def __str__(self):
        return (f'{self.get_fase_display()} #{self.ordem} — '
                f'{self.materia} — {self.sessao}')


class Votacao(models.Model):
    class Processo(models.TextChoices):
        SIMBOLICA = 'S', 'Simbólica'
        NOMINAL = 'N', 'Nominal'
        SECRETA = 'E', 'Escrutínio secreto'
        LEITURA = 'L', 'Leitura (sem votação)'

    class Resultado(models.TextChoices):
        APROVADA = 'A', 'Aprovada'
        REJEITADA = 'R', 'Rejeitada'
        RETIRADA = 'T', 'Retirada de pauta'
        ADIADA = 'D', 'Adiada'
        VISTA = 'V', 'Pedido de vista'
        PREJUDICADA = 'P', 'Prejudicada (art. 142, RI)'
        LIDA = 'L', 'Lida'

    item_pauta = models.OneToOneField(
        ItemPauta, on_delete=models.CASCADE, related_name='votacao',
        verbose_name='Item de pauta')
    processo = models.CharField(
        'Processo de votação', max_length=1, choices=Processo.choices,
        default=Processo.SIMBOLICA)
    resultado = models.CharField(
        'Resultado', max_length=1, choices=Resultado.choices)
    votos_sim = models.PositiveIntegerField('Votos SIM', default=0)
    votos_nao = models.PositiveIntegerField('Votos NÃO', default=0)
    abstencoes = models.PositiveIntegerField('Abstenções', default=0)
    unanime = models.BooleanField('Unânime?', default=False)
    observacao = models.TextField('Observação', blank=True)

    class Meta:
        verbose_name = 'Votação'
        verbose_name_plural = 'Votações'

    def clean(self):
        if self.processo == self.Processo.NOMINAL and self.unanime:
            # Unânime é anotação típica de votação simbólica na prática
            # da CMDC; na nominal, o placar individual é o registro.
            raise ValidationError(
                'Votação nominal registra o placar individual; use os '
                'votos por vereador em vez do indicador de unanimidade.')

    def __str__(self):
        return (f'{self.item_pauta.materia} — '
                f'{self.get_processo_display()} — '
                f'{self.get_resultado_display()}')


class VotoVereador(models.Model):
    """Voto individual em votação nominal (chamada vereador a vereador)."""

    class Voto(models.TextChoices):
        SIM = 'S', 'Sim'
        NAO = 'N', 'Não'
        ABSTENCAO = 'A', 'Abstenção'
        AUSENTE = 'U', 'Ausente'
        PRESIDENTE = 'P', 'Presidente (não vota)'

    votacao = models.ForeignKey(
        Votacao, on_delete=models.CASCADE, related_name='votos',
        verbose_name='Votação')
    vereador = models.ForeignKey(
        Vereador, on_delete=models.PROTECT, related_name='votos',
        verbose_name='Vereador')
    voto = models.CharField('Voto', max_length=1, choices=Voto.choices)

    class Meta:
        verbose_name = 'Voto de Vereador'
        verbose_name_plural = 'Votos de Vereadores'
        constraints = [
            models.UniqueConstraint(fields=('votacao', 'vereador'),
                                    name='voto_unico'),
        ]

    def __str__(self):
        return f'{self.vereador}: {self.get_voto_display()}'
