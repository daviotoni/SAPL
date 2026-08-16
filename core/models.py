"""Estrutura institucional: a Casa e o recorte temporal do mandato.

Inspirado em sapl.base e sapl.parlamentares (Legislatura/SessaoLegislativa)
do SAPL/Interlegis, reduzido ao que a CMDC utiliza.
"""
from django.db import models


class CasaLegislativa(models.Model):
    """Identidade da Casa. Registro único (singleton)."""
    nome = models.CharField('Nome', max_length=200,
                            default='Câmara Municipal de Duque de Caxias')
    sigla = models.CharField('Sigla', max_length=20, default='CMDC')
    municipio = models.CharField('Município', max_length=100,
                                 default='Duque de Caxias')
    uf = models.CharField('UF', max_length=2, default='RJ')
    endereco = models.CharField('Endereço', max_length=255, blank=True)
    telefone = models.CharField('Telefone', max_length=50, blank=True)
    site = models.URLField('Site', blank=True)
    email = models.EmailField('E-mail', blank=True)
    brasao = models.FileField('Brasão', upload_to='casa/', blank=True)

    class Meta:
        verbose_name = 'Casa Legislativa'
        verbose_name_plural = 'Casa Legislativa'

    def save(self, *args, **kwargs):
        self.pk = 1  # singleton
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome


class Legislatura(models.Model):
    """Período de quatro anos de mandato (ex.: 20ª Legislatura, 2025-2028)."""
    numero = models.PositiveIntegerField('Número', unique=True)
    data_inicio = models.DateField('Início')
    data_fim = models.DateField('Fim')

    class Meta:
        verbose_name = 'Legislatura'
        verbose_name_plural = 'Legislaturas'
        ordering = ('-numero',)

    def __str__(self):
        return (f'{self.numero}ª Legislatura '
                f'({self.data_inicio.year}-{self.data_fim.year})')


class SessaoLegislativa(models.Model):
    """Sessão legislativa anual dentro de uma legislatura."""
    legislatura = models.ForeignKey(
        Legislatura, on_delete=models.PROTECT,
        related_name='sessoes_legislativas', verbose_name='Legislatura')
    numero = models.PositiveIntegerField('Número')
    ano = models.PositiveIntegerField('Ano')
    data_inicio = models.DateField('Início')
    data_fim = models.DateField('Fim')

    class Meta:
        verbose_name = 'Sessão Legislativa'
        verbose_name_plural = 'Sessões Legislativas'
        ordering = ('-ano',)
        constraints = [
            models.UniqueConstraint(fields=('legislatura', 'numero'),
                                    name='sessaolegislativa_unica'),
        ]

    def __str__(self):
        return f'{self.numero}ª Sessão Legislativa ({self.ano})'
