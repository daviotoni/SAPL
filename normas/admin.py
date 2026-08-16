from django.contrib import admin

from .models import Norma, TipoNorma, VinculoNorma


@admin.register(TipoNorma)
class TipoNormaAdmin(admin.ModelAdmin):
    list_display = ('sigla', 'descricao')


class VinculoAtivoInline(admin.TabularInline):
    model = VinculoNorma
    fk_name = 'norma_origem'
    extra = 0
    verbose_name_plural = 'Normas que esta norma atinge'


class VinculoPassivoInline(admin.TabularInline):
    model = VinculoNorma
    fk_name = 'norma_destino'
    extra = 0
    verbose_name_plural = 'Normas que atingem esta norma'


@admin.register(Norma)
class NormaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'ementa_curta', 'situacao',
                    'data_publicacao')
    list_filter = ('tipo', 'situacao', 'ano')
    search_fields = ('ementa', 'numero')
    inlines = (VinculoAtivoInline, VinculoPassivoInline)

    @admin.display(description='Ementa')
    def ementa_curta(self, obj):
        return (obj.ementa[:120] + '…') if len(obj.ementa) > 120 \
            else obj.ementa
