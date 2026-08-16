"""Normas jurídicas do Município de Duque de Caxias."""
from django.db import models

from materias.models import Materia


class TipoNorma(models.Model):
    sigla = models.CharField('Sigla', max_length=10, unique=True)
    descricao = models.CharField('Descrição', max_length=100)

    class Meta:
        verbose_name = 'Tipo de Norma'
        verbose_name_plural = 'Tipos de Norma'
        ordering = ('sigla',)

    def __str__(self):
        return self.descricao


class Norma(models.Model):
    class Situacao(models.TextChoices):
        VIGENTE = 'V', 'Vigente'
        ALTERADA = 'A', 'Vigente com alterações'
        REVOGADA = 'R', 'Revogada'
        SUSPENSA = 'S', 'Eficácia suspensa'

    tipo = models.ForeignKey(
        TipoNorma, on_delete=models.PROTECT, related_name='normas',
        verbose_name='Tipo')
    numero = models.CharField('Número', max_length=20)
    ano = models.PositiveIntegerField('Ano')
    ementa = models.TextField('Ementa')
    data_promulgacao = models.DateField('Data de promulgação',
                                        null=True, blank=True)
    data_publicacao = models.DateField('Data de publicação',
                                       null=True, blank=True)
    veiculo_publicacao = models.CharField(
        'Veículo de publicação', max_length=100, blank=True,
        help_text='Ex.: Boletim Oficial do Município.')
    situacao = models.CharField(
        'Situação', max_length=1, choices=Situacao.choices,
        default=Situacao.VIGENTE)
    materia = models.ForeignKey(
        Materia, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='normas', verbose_name='Matéria de origem')
    texto = models.FileField('Texto integral', upload_to='normas/%Y/',
                             blank=True)
    observacao = models.TextField('Observação', blank=True)

    class Meta:
        verbose_name = 'Norma Jurídica'
        verbose_name_plural = 'Normas Jurídicas'
        ordering = ('-ano', '-id')
        constraints = [
            models.UniqueConstraint(fields=('tipo', 'numero', 'ano'),
                                    name='norma_unica'),
        ]

    def __str__(self):
        return f'{self.tipo.descricao} nº {self.numero}/{self.ano}'


class VinculoNorma(models.Model):
    class Tipo(models.TextChoices):
        ALTERA = 'A', 'Altera'
        REVOGA = 'R', 'Revoga'
        REVOGA_PARCIAL = 'P', 'Revoga parcialmente'
        REGULAMENTA = 'G', 'Regulamenta'
        SUSPENDE = 'S', 'Suspende a execução'

    norma_origem = models.ForeignKey(
        Norma, on_delete=models.CASCADE, related_name='vinculos_ativos',
        verbose_name='Norma que age')
    norma_destino = models.ForeignKey(
        Norma, on_delete=models.CASCADE, related_name='vinculos_passivos',
        verbose_name='Norma atingida')
    tipo = models.CharField('Tipo de vínculo', max_length=1,
                            choices=Tipo.choices)
    observacao = models.CharField('Observação', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Vínculo entre Normas'
        verbose_name_plural = 'Vínculos entre Normas'
        constraints = [
            models.UniqueConstraint(
                fields=('norma_origem', 'norma_destino', 'tipo'),
                name='vinculo_unico'),
        ]

    def __str__(self):
        return (f'{self.norma_origem} {self.get_tipo_display().lower()} '
                f'{self.norma_destino}')
