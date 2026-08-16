from core.models import CasaLegislativa


def casa_legislativa(request):
    return {'casa': CasaLegislativa.objects.first()}
