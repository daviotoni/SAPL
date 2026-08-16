from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from core.models import Legislatura
from materias.models import Materia, TipoMateria
from normas.models import Norma, TipoNorma
from parlamentares.models import Comissao, ComposicaoMesa, Vereador
from sessoes.models import SessaoPlenaria


def home(request):
    return render(request, 'portal/home.html', {
        'ultimas_materias': (Materia.objects
                             .select_related('tipo')[:5]),
        'proximas_sessoes': SessaoPlenaria.objects.all()[:5],
        'ultimas_normas': Norma.objects.select_related('tipo')[:5],
    })


def _paginar(request, queryset, por_pagina=25):
    paginator = Paginator(queryset, por_pagina)
    return paginator.get_page(request.GET.get('pagina'))


def materias(request):
    qs = (Materia.objects.select_related('tipo')
          .prefetch_related('autores'))
    busca = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '')
    ano = request.GET.get('ano', '')
    if busca:
        qs = qs.filter(Q(ementa__icontains=busca) |
                       Q(numero__icontains=busca))
    if tipo:
        qs = qs.filter(tipo__sigla=tipo)
    if ano.isdigit():
        qs = qs.filter(ano=int(ano))
    return render(request, 'portal/materias.html', {
        'pagina': _paginar(request, qs),
        'tipos': TipoMateria.objects.all(),
        'busca': busca, 'tipo': tipo, 'ano': ano,
    })


def materia_detalhe(request, pk):
    materia = get_object_or_404(
        Materia.objects.select_related('tipo')
        .prefetch_related('tramitacoes__status', 'analises_previas',
                          'pareceres__comissao', 'autores'),
        pk=pk)
    return render(request, 'portal/materia_detalhe.html',
                  {'materia': materia})


def sessoes(request):
    return render(request, 'portal/sessoes.html', {
        'pagina': _paginar(request, SessaoPlenaria.objects.all()),
    })


def sessao_detalhe(request, pk):
    sessao = get_object_or_404(
        SessaoPlenaria.objects.prefetch_related(
            'pauta__materia__tipo', 'pauta__votacao__votos__vereador',
            'presencas__vereador'),
        pk=pk)
    return render(request, 'portal/sessao_detalhe.html',
                  {'sessao': sessao})


def normas(request):
    qs = Norma.objects.select_related('tipo')
    busca = request.GET.get('q', '').strip()
    if busca:
        qs = qs.filter(Q(ementa__icontains=busca) |
                       Q(numero__icontains=busca))
    return render(request, 'portal/normas.html', {
        'pagina': _paginar(request, qs),
        'tipos': TipoNorma.objects.all(),
        'busca': busca,
    })


def vereadores(request):
    legislatura = Legislatura.objects.first()
    return render(request, 'portal/vereadores.html', {
        'vereadores': (Vereador.objects.filter(ativo=True)
                       .select_related('partido')),
        'mesa': (ComposicaoMesa.objects
                 .filter(legislatura=legislatura)
                 .select_related('cargo', 'vereador')
                 .order_by('cargo__ordem')) if legislatura else [],
        'legislatura': legislatura,
    })


def comissoes(request):
    return render(request, 'portal/comissoes.html', {
        'comissoes': (Comissao.objects.filter(ativa=True)
                      .prefetch_related('membros__vereador')),
    })
