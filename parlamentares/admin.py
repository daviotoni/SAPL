from django.contrib import admin

from .models import (CargoMesa, Comissao, ComposicaoMesa, Mandato,
                     MembroComissao, Partido, Vereador)


@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'nome')
    search_fields = ('sigla', 'nome')


class MandatoInline(admin.TabularInline):
    model = Mandato
    extra = 0


@admin.register(Vereador)
class VereadorAdmin(admin.ModelAdmin):
    list_display = ('nome_parlamentar', 'nome_civil', 'partido', 'ativo')
    list_filter = ('ativo', 'partido')
    search_fields = ('nome_parlamentar', 'nome_civil')
    inlines = (MandatoInline,)


@admin.register(CargoMesa)
class CargoMesaAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'ordem')


@admin.register(ComposicaoMesa)
class ComposicaoMesaAdmin(admin.ModelAdmin):
    list_display = ('cargo', 'vereador', 'legislatura',
                    'data_inicio', 'data_fim')
    list_filter = ('legislatura', 'cargo')


class MembroComissaoInline(admin.TabularInline):
    model = MembroComissao
    extra = 0
    autocomplete_fields = ('vereador',)


@admin.register(Comissao)
class ComissaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'ativa')
    list_filter = ('tipo', 'ativa')
    search_fields = ('nome',)
    inlines = (MembroComissaoInline,)
