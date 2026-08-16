"""API REST pública do SAPL-DC (leitura anônima, escrita autenticada)."""
from rest_framework import routers, serializers, viewsets

from materias.models import AnalisePrevia, Materia, Tramitacao
from normas.models import Norma
from parlamentares.models import Comissao, Vereador
from sessoes.models import SessaoPlenaria, Votacao


class VereadorSerializer(serializers.ModelSerializer):
    partido = serializers.StringRelatedField()

    class Meta:
        model = Vereador
        fields = ('id', 'nome_parlamentar', 'nome_civil', 'partido',
                  'ativo')


class TramitacaoSerializer(serializers.ModelSerializer):
    unidade_origem = serializers.StringRelatedField()
    unidade_destino = serializers.StringRelatedField()
    status = serializers.StringRelatedField()

    class Meta:
        model = Tramitacao
        fields = ('data', 'unidade_origem', 'unidade_destino', 'status',
                  'despacho')


class MateriaSerializer(serializers.ModelSerializer):
    tipo = serializers.StringRelatedField()
    autores = serializers.StringRelatedField(many=True)
    tramitacao_atual = TramitacaoSerializer(read_only=True)

    class Meta:
        model = Materia
        fields = ('id', 'tipo', 'numero', 'ano', 'ementa', 'regime',
                  'data_apresentacao', 'em_tramitacao', 'autores',
                  'tramitacao_atual')


class AnalisePreviaSerializer(serializers.ModelSerializer):
    materia = serializers.StringRelatedField()
    conclusao = serializers.CharField(source='get_conclusao_display')

    class Meta:
        model = AnalisePrevia
        fields = ('id', 'materia', 'data', 'conclusao')


class NormaSerializer(serializers.ModelSerializer):
    tipo = serializers.StringRelatedField()

    class Meta:
        model = Norma
        fields = ('id', 'tipo', 'numero', 'ano', 'ementa', 'situacao',
                  'data_publicacao')


class ComissaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comissao
        fields = ('id', 'nome', 'tipo', 'ativa')


class VotacaoSerializer(serializers.ModelSerializer):
    materia = serializers.StringRelatedField(source='item_pauta.materia')
    votos = serializers.SerializerMethodField()

    class Meta:
        model = Votacao
        fields = ('id', 'materia', 'processo', 'resultado', 'votos_sim',
                  'votos_nao', 'abstencoes', 'unanime', 'votos')

    def get_votos(self, obj):
        return [
            {'vereador': v.vereador.nome_parlamentar,
             'voto': v.get_voto_display()}
            for v in obj.votos.select_related('vereador')
        ]


class SessaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessaoPlenaria
        fields = ('id', 'tipo', 'numero', 'data', 'hora_inicio',
                  'hora_fim')


class VereadorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vereador.objects.filter(ativo=True)
    serializer_class = VereadorSerializer
    search_fields = ('nome_parlamentar', 'nome_civil')


class MateriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (Materia.objects
                .select_related('tipo')
                .prefetch_related('autores'))
    serializer_class = MateriaSerializer
    filterset_fields = ('tipo__sigla', 'ano', 'em_tramitacao', 'regime')
    search_fields = ('ementa',)


class AnalisePreviaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnalisePrevia.objects.select_related('materia')
    serializer_class = AnalisePreviaSerializer
    filterset_fields = ('conclusao',)


class NormaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Norma.objects.select_related('tipo')
    serializer_class = NormaSerializer
    filterset_fields = ('tipo__sigla', 'ano', 'situacao')
    search_fields = ('ementa',)


class ComissaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Comissao.objects.filter(ativa=True)
    serializer_class = ComissaoSerializer


class SessaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SessaoPlenaria.objects.all()
    serializer_class = SessaoSerializer
    filterset_fields = ('tipo',)


class VotacaoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (Votacao.objects
                .select_related('item_pauta__materia')
                .prefetch_related('votos__vereador'))
    serializer_class = VotacaoSerializer
    filterset_fields = ('processo', 'resultado')


router = routers.DefaultRouter()
router.register('vereadores', VereadorViewSet)
router.register('materias', MateriaViewSet)
router.register('analises-previas', AnalisePreviaViewSet)
router.register('normas', NormaViewSet)
router.register('comissoes', ComissaoViewSet)
router.register('sessoes', SessaoViewSet)
router.register('votacoes', VotacaoViewSet)

urlpatterns = router.urls
