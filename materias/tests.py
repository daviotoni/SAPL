"""Testes do fluxo legislativo da CMDC: APL → Análise Prévia → PL."""
import datetime

from django.core.management import call_command
from django.test import TestCase

from materias.models import (AnalisePrevia, Autor, Autoria, Materia,
                             StatusTramitacao, TipoMateria, Tramitacao,
                             UnidadeTramitacao)
from parlamentares.models import Vereador


class SeedTest(TestCase):
    def test_seed_completo_e_idempotente(self):
        call_command('seed_cmdc', verbosity=0)
        call_command('seed_cmdc', verbosity=0)  # não deve duplicar
        self.assertEqual(Vereador.objects.count(), 29)
        self.assertEqual(
            TipoMateria.objects.filter(sigla='APL').count(), 1)
        self.assertTrue(
            TipoMateria.objects.get(sigla='APL').exige_analise_previa)
        # Art. 24, §1º: Mesa com 5 cargos
        from parlamentares.models import CargoMesa, Comissao
        self.assertEqual(CargoMesa.objects.count(), 5)
        # 30 comissões permanentes (site oficial 2025/2026)
        self.assertEqual(
            Comissao.objects.filter(tipo='P').count(), 30)
        # Cada vereador tem um Autor correspondente
        self.assertEqual(
            Autor.objects.filter(tipo='V').count(), 29)


class FluxoAPLTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_cmdc', verbosity=0)
        cls.apl_tipo = TipoMateria.objects.get(sigla='APL')
        cls.pl_tipo = TipoMateria.objects.get(sigla='PL')
        cls.autor = Autor.objects.filter(tipo='V').first()

    def _criar_apl(self):
        apl = Materia.objects.create(
            tipo=self.apl_tipo, numero=1, ano=2026,
            ementa='Denomina Rua Projetada A a via que menciona.',
            data_apresentacao=datetime.date(2026, 3, 10),
            processo_numero=1234, processo_ano=2026)
        Autoria.objects.create(materia=apl, autor=self.autor)
        return apl

    def test_apl_com_analise_previa_admissivel_vira_pl(self):
        apl = self._criar_apl()
        AnalisePrevia.objects.create(
            materia=apl, data=datetime.date(2026, 3, 15),
            conclusao=AnalisePrevia.Conclusao.ADMISSIVEL)
        pl = apl.transformar_em(
            self.pl_tipo, numero=42,
            data_apresentacao=datetime.date(2026, 4, 1))
        apl.refresh_from_db()
        self.assertFalse(apl.em_tramitacao)
        self.assertEqual(pl.materia_origem, apl)
        self.assertEqual(pl.ementa, apl.ementa)
        self.assertEqual(str(pl), 'PL 42/2026')
        # autoria copiada
        self.assertEqual(list(pl.autores.all()), list(apl.autores.all()))
        # processo administrativo preservado
        self.assertEqual(pl.processo_numero, 1234)

    def test_status_fim_tramitacao_encerra_materia(self):
        apl = self._criar_apl()
        origem = UnidadeTramitacao.objects.get(
            nome='Protocolo Legislativo')
        destino = UnidadeTramitacao.objects.get(
            nome='Procuradoria / Assessoria Técnica Legislativa')
        status_devolvida = StatusTramitacao.objects.get(
            descricao='Devolvida ao autor (art. 88, RI)')
        self.assertTrue(status_devolvida.fim_tramitacao)
        Tramitacao.objects.create(
            materia=apl, data=datetime.date(2026, 3, 20),
            unidade_origem=origem, unidade_destino=destino,
            status=status_devolvida)
        apl.refresh_from_db()
        self.assertFalse(apl.em_tramitacao)

    def test_tramitacao_atual(self):
        apl = self._criar_apl()
        origem = UnidadeTramitacao.objects.get(
            nome='Protocolo Legislativo')
        destino = UnidadeTramitacao.objects.get(nome='Plenário')
        s1 = StatusTramitacao.objects.get(descricao='Protocolada')
        s2 = StatusTramitacao.objects.get(
            descricao='Incluída na Ordem do Dia')
        Tramitacao.objects.create(
            materia=apl, data=datetime.date(2026, 3, 11),
            unidade_origem=origem, unidade_destino=origem, status=s1)
        t2 = Tramitacao.objects.create(
            materia=apl, data=datetime.date(2026, 3, 20),
            unidade_origem=origem, unidade_destino=destino, status=s2)
        self.assertEqual(apl.tramitacao_atual, t2)
