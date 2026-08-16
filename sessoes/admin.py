from django.contrib import admin

from .models import (ItemPauta, PresencaSessao, SessaoPlenaria, Votacao,
                     VotoVereador)


class ItemPautaInline(admin.TabularInline):
    model = ItemPauta
    extra = 0
    autocomplete_fields = ('materia',)


class PresencaInline(admin.TabularInline):
    model = PresencaSessao
    extra = 0


@admin.register(SessaoPlenaria)
class SessaoPlenariaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tipo', 'sessao_legislativa', 'data')
    list_filter = ('tipo', 'sessao_legislativa')
    date_hierarchy = 'data'
    inlines = (ItemPautaInline, PresencaInline)


class VotoVereadorInline(admin.TabularInline):
    model = VotoVereador
    extra = 0


@admin.register(Votacao)
class VotacaoAdmin(admin.ModelAdmin):
    list_display = ('item_pauta', 'processo', 'resultado', 'placar')
    list_filter = ('processo', 'resultado')
    inlines = (VotoVereadorInline,)

    @admin.display(description='Placar')
    def placar(self, obj):
        if obj.unanime:
            return 'Unânime'
        return f'{obj.votos_sim} × {obj.votos_nao} ({obj.abstencoes} abst.)'


@admin.register(ItemPauta)
class ItemPautaAdmin(admin.ModelAdmin):
    list_display = ('sessao', 'fase', 'ordem', 'materia', 'turno')
    list_filter = ('fase', 'turno')
    autocomplete_fields = ('materia',)
