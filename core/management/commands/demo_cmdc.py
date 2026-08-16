"""Cria um caso de demonstração percorrendo o fluxo da CMDC.

APL protocolado -> Análise Prévia da Procuradoria -> conversão em PL ->
tramitação -> parecer da CLJR -> inclusão na Ordem do Dia -> votação
nominal -> norma promulgada.

Dados FICTÍCIOS, apenas para demonstração da interface.
Uso: python manage.py demo_cmdc
"""
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import SessaoLegislativa
from materias.models import (AnalisePrevia, Autor, Autoria, Materia,
                             Parecer, StatusTramitacao, TipoMateria,
                             Tramitacao, UnidadeTramitacao)
from normas.models import Norma, TipoNorma
from parlamentares.models import Comissao, Vereador
from sessoes.models import (ItemPauta, PresencaSessao, SessaoPlenaria,
                            Votacao, VotoVereador)


class Command(BaseCommand):
    help = 'Cria um caso de demonstração (dados fictícios) do fluxo CMDC.'

    @transaction.atomic
    def handle(self, *args, **options):
        if Materia.objects.filter(ano=2026, numero=1).exists():
            self.stdout.write('Demonstração já criada.')
            return

        autor = Autor.objects.filter(tipo=Autor.Tipo.VEREADOR).first()
        prot = UnidadeTramitacao.objects.get(nome='Protocolo Legislativo')
        proc = UnidadeTramitacao.objects.get(
            nome='Procuradoria / Assessoria Técnica Legislativa')
        cljr_unid = UnidadeTramitacao.objects.get(
            nome='Comissão de Legislação, Justiça e Redação Final')
        plenario = UnidadeTramitacao.objects.get(nome='Plenário')

        # 1. APL protocolado
        apl = Materia.objects.create(
            tipo=TipoMateria.objects.get(sigla='APL'),
            numero=1, ano=2026,
            processo_numero=1234, processo_ano=2026,
            ementa='Institui a Semana Municipal de Valorização do '
                   'Patrimônio Histórico de Duque de Caxias.',
            data_apresentacao=datetime.date(2026, 3, 3),
            regime=Materia.Regime.ORDINARIA)
        Autoria.objects.create(materia=apl, autor=autor)
        Tramitacao.objects.create(
            materia=apl, data=datetime.date(2026, 3, 3),
            unidade_origem=prot, unidade_destino=proc,
            status=StatusTramitacao.objects.get(descricao='Protocolada'),
            despacho='Encaminhe-se à Procuradoria para Análise Prévia.')

        # 2. Análise Prévia
        AnalisePrevia.objects.create(
            materia=apl, data=datetime.date(2026, 3, 10),
            admissibilidade_art88=AnalisePrevia.Item.SEM_VICIO,
            prejudicialidade_art142=AnalisePrevia.Item.SEM_VICIO,
            constitucionalidade_material=AnalisePrevia.Item.SEM_VICIO,
            constitucionalidade_formal_objetiva=AnalisePrevia.Item.SEM_VICIO,
            constitucionalidade_formal_subjetiva=AnalisePrevia.Item.SEM_VICIO,
            tecnica_legislativa=AnalisePrevia.Item.RESSALVA,
            fundamentacao='A proposição institui data comemorativa, '
                          'matéria de competência municipal e de '
                          'iniciativa parlamentar concorrente, sem '
                          'criação de despesa. Sugere-se ajuste de '
                          'técnica legislativa na cláusula de vigência '
                          '(art. 92, VI, do Regimento Interno).',
            conclusao=AnalisePrevia.Conclusao.ADMISSIVEL_RESSALVAS,
            responsavel='Assessoria Técnica Legislativa')
        Tramitacao.objects.create(
            materia=apl, data=datetime.date(2026, 3, 10),
            unidade_origem=proc, unidade_destino=prot,
            status=StatusTramitacao.objects.get(
                descricao='Análise Prévia concluída — admissível'),
            despacho='Admissível com ressalvas de técnica legislativa.')

        # 3. Conversão em Projeto de Lei
        pl = apl.transformar_em(
            TipoMateria.objects.get(sigla='PL'), numero=42,
            data_apresentacao=datetime.date(2026, 3, 17))
        Tramitacao.objects.create(
            materia=apl, data=datetime.date(2026, 3, 17),
            unidade_origem=prot, unidade_destino=prot,
            status=StatusTramitacao.objects.get(
                descricao='Convertida em projeto'),
            despacho='Convertido no PL 42/2026.')

        cljr = Comissao.objects.get(
            nome='Legislação, Justiça e Redação Final')
        Tramitacao.objects.create(
            materia=pl, data=datetime.date(2026, 3, 17),
            unidade_origem=prot, unidade_destino=cljr_unid,
            status=StatusTramitacao.objects.get(
                descricao='Aguardando parecer de comissão (art. 54, RI)'),
            data_prazo=datetime.date(2026, 4, 1),
            despacho='Prazo de 15 dias — tramitação ordinária '
                     '(art. 54, III, RI).')

        # 4. Parecer da CLJR
        relator = Vereador.objects.get(nome_parlamentar='Dr. Maurício')
        Parecer.objects.create(
            materia=pl, comissao=cljr, relator=relator,
            sentido=Parecer.Sentido.FAVORAVEL,
            data=datetime.date(2026, 3, 26),
            texto='Parecer favorável quanto à constitucionalidade, '
                  'juridicidade e técnica legislativa.')
        Tramitacao.objects.create(
            materia=pl, data=datetime.date(2026, 3, 26),
            unidade_origem=cljr_unid, unidade_destino=plenario,
            status=StatusTramitacao.objects.get(
                descricao='Com parecer — aguardando pauta'))

        # 5. Sessão plenária e votação nominal
        sessao = SessaoPlenaria.objects.create(
            tipo=SessaoPlenaria.Tipo.ORDINARIA, numero=12,
            sessao_legislativa=SessaoLegislativa.objects.get(ano=2026),
            data=datetime.date(2026, 3, 31),
            hora_inicio=datetime.time(17, 30),
            hora_fim=datetime.time(19, 30))
        vereadores = list(Vereador.objects.all())
        for i, v in enumerate(vereadores):
            PresencaSessao.objects.create(
                sessao=sessao, vereador=v, presente=i < 26,
                justificativa='' if i < 26 else 'Ausência justificada')

        item = ItemPauta.objects.create(
            sessao=sessao, fase=ItemPauta.Fase.ORDEM_DO_DIA, ordem=1,
            materia=pl, turno=ItemPauta.Turno.UNICO)
        votacao = Votacao.objects.create(
            item_pauta=item, processo=Votacao.Processo.NOMINAL,
            resultado=Votacao.Resultado.APROVADA,
            votos_sim=24, votos_nao=1, abstencoes=1)
        for i, v in enumerate(vereadores[:26]):
            voto = (VotoVereador.Voto.SIM if i < 24
                    else VotoVereador.Voto.NAO if i == 24
                    else VotoVereador.Voto.ABSTENCAO)
            VotoVereador.objects.create(votacao=votacao, vereador=v,
                                        voto=voto)
        for v in vereadores[26:]:
            VotoVereador.objects.create(votacao=votacao, vereador=v,
                                        voto=VotoVereador.Voto.AUSENTE)

        Tramitacao.objects.create(
            materia=pl, data=datetime.date(2026, 3, 31),
            unidade_origem=plenario, unidade_destino=prot,
            status=StatusTramitacao.objects.get(
                descricao='Aprovada — enviada à sanção'),
            despacho='Aprovado em turno único por 24 votos a 1, '
                     'uma abstenção.')

        # 6. Norma promulgada
        Norma.objects.create(
            tipo=TipoNorma.objects.get(sigla='LO'),
            numero='3.150', ano=2026,
            ementa='Institui a Semana Municipal de Valorização do '
                   'Patrimônio Histórico de Duque de Caxias.',
            data_promulgacao=datetime.date(2026, 4, 20),
            data_publicacao=datetime.date(2026, 4, 22),
            veiculo_publicacao='Boletim Oficial do Município',
            materia=pl)

        # Um segundo caso: APL inadmitido (art. 88)
        apl2 = Materia.objects.create(
            tipo=TipoMateria.objects.get(sigla='APL'),
            numero=2, ano=2026, processo_numero=1310, processo_ano=2026,
            ementa='Dispõe sobre a criação de cargos no quadro do '
                   'Poder Executivo Municipal.',
            data_apresentacao=datetime.date(2026, 3, 5))
        Autoria.objects.create(materia=apl2, autor=autor)
        AnalisePrevia.objects.create(
            materia=apl2, data=datetime.date(2026, 3, 12),
            constitucionalidade_formal_subjetiva=AnalisePrevia.Item.VICIO,
            fundamentacao='Vício de iniciativa: a criação de cargos na '
                          'administração direta do Executivo é de '
                          'iniciativa privativa do Prefeito Municipal.',
            conclusao=AnalisePrevia.Conclusao.INADMISSIVEL,
            responsavel='Assessoria Técnica Legislativa')
        Tramitacao.objects.create(
            materia=apl2, data=datetime.date(2026, 3, 12),
            unidade_origem=proc, unidade_destino=prot,
            status=StatusTramitacao.objects.get(
                descricao='Devolvida ao autor (art. 88, RI)'),
            despacho='Devolvido nos termos do art. 88, II e §1º, do RI.')

        self.stdout.write(self.style.SUCCESS(
            'Demonstração criada: APL 1/2026 -> PL 42/2026 -> Lei '
            '3.150/2026, sessão 12ª com votação nominal, e APL 2/2026 '
            'inadmitido por vício de iniciativa.'))
