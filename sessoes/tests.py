"""Testes das sessões plenárias e votações (arts. 74-75 e 156+ do RI)."""
import datetime

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from core.models import SessaoLegislativa
from materias.models import Materia, TipoMateria
from parlamentares.models import Vereador
from sessoes.models import (ItemPauta, SessaoPlenaria, Votacao,
                            VotoVereador)


class VotacaoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_cmdc', verbosity=0)
        cls.sessao = SessaoPlenaria.objects.create(
            tipo=SessaoPlenaria.Tipo.ORDINARIA, numero=1,
            sessao_legislativa=SessaoLegislativa.objects.get(ano=2026),
            data=datetime.date(2026, 3, 17))
        materia = Materia.objects.create(
            tipo=TipoMateria.objects.get(sigla='PL'), numero=10,
            ano=2026, ementa='Teste',
            data_apresentacao=datetime.date(2026, 2, 1))
        cls.item = ItemPauta.objects.create(
            sessao=cls.sessao, fase=ItemPauta.Fase.ORDEM_DO_DIA,
            ordem=1, materia=materia)

    def test_votacao_nominal_com_votos_individuais(self):
        votacao = Votacao.objects.create(
            item_pauta=self.item,
            processo=Votacao.Processo.NOMINAL,
            resultado=Votacao.Resultado.APROVADA,
            votos_sim=20, votos_nao=5, abstencoes=4)
        for i, vereador in enumerate(Vereador.objects.all()):
            voto = (VotoVereador.Voto.SIM if i < 20
                    else VotoVereador.Voto.NAO if i < 25
                    else VotoVereador.Voto.ABSTENCAO)
            VotoVereador.objects.create(
                votacao=votacao, vereador=vereador, voto=voto)
        self.assertEqual(votacao.votos.count(), 29)
        self.assertEqual(
            votacao.votos.filter(voto=VotoVereador.Voto.SIM).count(), 20)

    def test_nominal_nao_admite_marcador_unanime(self):
        votacao = Votacao(
            item_pauta=self.item,
            processo=Votacao.Processo.NOMINAL,
            resultado=Votacao.Resultado.APROVADA,
            unanime=True)
        with self.assertRaises(ValidationError):
            votacao.full_clean()

    def test_fases_da_pauta_cmdc(self):
        # Art. 75 do RI: Expediente Inicial, Ordem do Dia,
        # Expediente Final
        fases = [f[0] for f in ItemPauta.Fase.choices]
        self.assertEqual(fases, ['EI', 'OD', 'EF'])
