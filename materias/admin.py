from django.contrib import admin

from .models import (AnalisePrevia, Autor, Autoria, DocumentoAcessorio,
                     Materia, Parecer, StatusTramitacao, TipoMateria,
                     Tramitacao, UnidadeTramitacao)


@admin.register(TipoMateria)
class TipoMateriaAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'descricao', 'exige_analise_previa', 'ordem')
    list_editable = ('ordem',)


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo')
    list_filter = ('tipo',)
    search_fields = ('nome',)
    autocomplete_fields = ('vereador', 'comissao')


class AutoriaInline(admin.TabularInline):
    model = Autoria
    extra = 1
    autocomplete_fields = ('autor',)


class TramitacaoInline(admin.TabularInline):
    model = Tramitacao
    extra = 0
    fields = ('data', 'unidade_origem', 'unidade_destino', 'status',
              'despacho', 'data_prazo')


class AnalisePreviaInline(admin.StackedInline):
    model = AnalisePrevia
    extra = 0


class ParecerInline(admin.TabularInline):
    model = Parecer
    extra = 0


class DocumentoAcessorioInline(admin.TabularInline):
    model = DocumentoAcessorio
    extra = 0


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'ementa_curta', 'regime',
                    'data_apresentacao', 'em_tramitacao')
    list_filter = ('tipo', 'ano', 'regime', 'em_tramitacao')
    search_fields = ('ementa', 'numero')
    date_hierarchy = 'data_apresentacao'
    inlines = (AutoriaInline, AnalisePreviaInline, TramitacaoInline,
               ParecerInline, DocumentoAcessorioInline)

    @admin.display(description='Ementa')
    def ementa_curta(self, obj):
        return (obj.ementa[:120] + '…') if len(obj.ementa) > 120 \
            else obj.ementa


@admin.register(AnalisePrevia)
class AnalisePreviaAdmin(admin.ModelAdmin):
    list_display = ('materia', 'data', 'conclusao', 'responsavel')
    list_filter = ('conclusao',)
    date_hierarchy = 'data'


@admin.register(UnidadeTramitacao)
class UnidadeTramitacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativa')


@admin.register(StatusTramitacao)
class StatusTramitacaoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'fim_tramitacao')


@admin.register(Tramitacao)
class TramitacaoAdmin(admin.ModelAdmin):
    list_display = ('materia', 'data', 'unidade_origem',
                    'unidade_destino', 'status')
    list_filter = ('status', 'unidade_destino')
    date_hierarchy = 'data'


@admin.register(Parecer)
class ParecerAdmin(admin.ModelAdmin):
    list_display = ('materia', 'comissao', 'relator', 'sentido', 'data')
    list_filter = ('sentido', 'comissao')
