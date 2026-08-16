"""Vereadores, mandatos, Mesa Diretora e Comissões da CMDC.

A Mesa Diretora da CMDC compõe-se de presidente, dois vice-presidentes e
dois secretários (Regimento Interno). As comissões permanentes são as 30
listadas no site oficial.
"""
from django.db import models

from core.models import Legislatura


class Partido(models.Model):
    sigla = models.CharField('Sigla', max_length=20, unique=True)
    nome = models.CharField('Nome', max_length=100)

    class Meta:
        verbose_name = 'Partido'
        verbose_name_plural = 'Partidos'
        ordering = ('sigla',)

    def __str__(self):
        return self.sigla


class Vereador(models.Model):
    nome_civil = models.CharField('Nome civil', max_length=150)
    nome_parlamentar = models.CharField('Nome parlamentar', max_length=100)
    partido = models.ForeignKey(
        Partido, on_delete=models.PROTECT, null=True, blank=True,
        verbose_name='Partido atual')
    foto = models.FileField('Foto', upload_to='vereadores/', blank=True)
    email = models.EmailField('E-mail', blank=True)
    telefone = models.CharField('Telefone', max_length=50, blank=True)
    biografia = models.TextField('Biografia', blank=True)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Vereador'
        verbose_name_plural = 'Vereadores'
        ordering = ('nome_parlamentar',)

    def __str__(self):
        return self.nome_parlamentar


class Mandato(models.Model):
    class Condicao(models.TextChoices):
        TITULAR = 'T', 'Titular'
        SUPLENTE = 'S', 'Suplente em exercício'

    vereador = models.ForeignKey(
        Vereador, on_delete=models.PROTECT, related_name='mandatos',
        verbose_name='Vereador')
    legislatura = models.ForeignKey(
        Legislatura, on_delete=models.PROTECT, related_name='mandatos',
        verbose_name='Legislatura')
    condicao = models.CharField(
        'Condição', max_length=1, choices=Condicao.choices,
        default=Condicao.TITULAR)
    data_inicio = models.DateField('Início do exercício')
    data_fim = models.DateField('Fim do exercício', null=True, blank=True)
    observacao = models.TextField('Observação', blank=True)

    class Meta:
        verbose_name = 'Mandato'
        verbose_name_plural = 'Mandatos'
        ordering = ('legislatura', 'vereador__nome_parlamentar')

    def __str__(self):
        return f'{self.vereador} — {self.legislatura}'


class CargoMesa(models.Model):
    """Cargos da Mesa Diretora conforme o Regimento da CMDC."""
    descricao = models.CharField('Cargo', max_length=50, unique=True)
    ordem = models.PositiveIntegerField('Ordem de precedência')

    class Meta:
        verbose_name = 'Cargo da Mesa'
        verbose_name_plural = 'Cargos da Mesa'
        ordering = ('ordem',)

    def __str__(self):
        return self.descricao


class ComposicaoMesa(models.Model):
    """Ocupação de um cargo da Mesa em um período (na CMDC, biênio)."""
    legislatura = models.ForeignKey(
        Legislatura, on_delete=models.PROTECT,
        related_name='composicoes_mesa', verbose_name='Legislatura')
    cargo = models.ForeignKey(
        CargoMesa, on_delete=models.PROTECT, verbose_name='Cargo')
    vereador = models.ForeignKey(
        Vereador, on_delete=models.PROTECT,
        related_name='cargos_mesa', verbose_name='Vereador')
    data_inicio = models.DateField('Início')
    data_fim = models.DateField('Fim', null=True, blank=True)

    class Meta:
        verbose_name = 'Composição da Mesa'
        verbose_name_plural = 'Composições da Mesa'
        ordering = ('-data_inicio', 'cargo__ordem')

    def __str__(self):
        return f'{self.cargo}: {self.vereador}'


class Comissao(models.Model):
    class Tipo(models.TextChoices):
        PERMANENTE = 'P', 'Permanente'
        TEMPORARIA = 'T', 'Temporária/Especial'
        CPI = 'C', 'Comissão Parlamentar de Inquérito'
        PROCESSANTE = 'R', 'Comissão Processante'

    nome = models.CharField('Nome', max_length=200, unique=True)
    tipo = models.CharField('Tipo', max_length=1, choices=Tipo.choices,
                            default=Tipo.PERMANENTE)
    finalidade = models.TextField('Finalidade', blank=True)
    data_criacao = models.DateField('Data de criação', null=True, blank=True)
    data_extincao = models.DateField('Data de extinção', null=True,
                                     blank=True)
    ativa = models.BooleanField('Ativa', default=True)

    class Meta:
        verbose_name = 'Comissão'
        verbose_name_plural = 'Comissões'
        ordering = ('nome',)

    def __str__(self):
        return self.nome


class MembroComissao(models.Model):
    class Cargo(models.TextChoices):
        PRESIDENTE = 'P', 'Presidente'
        VICE = 'V', 'Vice-Presidente'
        MEMBRO = 'M', 'Membro'
        SUPLENTE = 'S', 'Suplente'

    comissao = models.ForeignKey(
        Comissao, on_delete=models.CASCADE, related_name='membros',
        verbose_name='Comissão')
    vereador = models.ForeignKey(
        Vereador, on_delete=models.PROTECT, related_name='comissoes',
        verbose_name='Vereador')
    cargo = models.CharField('Cargo', max_length=1, choices=Cargo.choices,
                             default=Cargo.MEMBRO)
    periodo = models.CharField('Período', max_length=20, blank=True,
                               help_text='Ex.: 2025/2026')
    data_inicio = models.DateField('Início', null=True, blank=True)
    data_fim = models.DateField('Fim', null=True, blank=True)

    class Meta:
        verbose_name = 'Membro de Comissão'
        verbose_name_plural = 'Membros de Comissões'
        ordering = ('comissao', 'cargo')

    def __str__(self):
        return f'{self.vereador} — {self.get_cargo_display()} — {self.comissao}'
