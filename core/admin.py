from django.contrib import admin

from .models import CasaLegislativa, Legislatura, SessaoLegislativa


@admin.register(CasaLegislativa)
class CasaLegislativaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'municipio', 'uf')

    def has_add_permission(self, request):
        return not CasaLegislativa.objects.exists()


class SessaoLegislativaInline(admin.TabularInline):
    model = SessaoLegislativa
    extra = 0


@admin.register(Legislatura)
class LegislaturaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'data_inicio', 'data_fim')
    inlines = (SessaoLegislativaInline,)


@admin.register(SessaoLegislativa)
class SessaoLegislativaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'legislatura', 'data_inicio', 'data_fim')
    list_filter = ('legislatura',)
