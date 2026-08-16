"""Carga inicial do SAPL-DC com os dados institucionais da CMDC.

Fontes (consultadas em 16/08/2026):
- Vereadores da 20ª Legislatura: https://www.cmdc.rj.gov.br/?page_id=29390
  (página oficial, que se declara "em processo de atualização" — 29 nomes
  listados; confirmar se há 30ª vaga/licenciados).
- Mesa Diretora 2025-2027: https://www.cmdc.rj.gov.br/?page_id=144
- Comissões Permanentes 2025/2026: https://www.cmdc.rj.gov.br/?page_id=3017
- Regimento Interno (Resolução nº 1.835/2000):
  https://www.cmdc.rj.gov.br/wp-content/uploads/2013/06/Regimento_Interno_da_Camara.pdf

LACUNAS CONHECIDAS (completar pela interface administrativa):
- Filiação partidária dos vereadores: apenas as noticiadas na posse
  foram registradas (Claudio Thomaz/PRD, Junior Reis/MDB, Catiti/PDT).
- Composição completa das comissões (vices e membros): o site oficial
  publica apenas os presidentes.

Uso: python manage.py seed_cmdc
Idempotente: pode ser reexecutado sem duplicar registros.
"""
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import CasaLegislativa, Legislatura, SessaoLegislativa
from materias.models import (Autor, StatusTramitacao, TipoMateria,
                             UnidadeTramitacao)
from normas.models import TipoNorma
from parlamentares.models import (CargoMesa, Comissao, ComposicaoMesa,
                                  Mandato, MembroComissao, Partido,
                                  Vereador)

# (nome civil, nome parlamentar, sigla do partido ou None)
VEREADORES = [
    ('Ailton Abreu Nascimento', 'Chiquinho Caipira', None),
    ('Alex Freitas Marques', 'Alex Freitas', None),
    ('Andréia Almeida Zito dos Santos Hotz', 'Andréia Zito', None),
    ('Carlos Alberto de Paula Dias Junior', 'Junior Uios', None),
    ('Carlos Augusto Pereira Sodré', 'Carlinhos da Barreira', None),
    ('Claudio de Oliveira Thomaz', 'Claudio Thomaz', 'PRD'),
    ('Clovis Mororo Magalhães', 'Clovinho Sempre Junto', None),
    ("Delza Oliveira Sant'Anna de Almeida", 'Delza de Oliveira', None),
    ('Divair Alves de Oliveira Junior', 'Junior Reis', 'MDB'),
    ('Eduardo Anderson Goes Lopes', 'Anderson Lopes', None),
    ('Eduardo Moreira da Silva', 'Eduardo Moreira', None),
    ('Fernanda Izabel da Costa', 'Dra. Fernanda Costa', None),
    ('Giorgio Carvalho Monteiro', 'Giorgio Monteiro', None),
    ('Juliana Fant Alves Machado Miranda', 'Juliana do Taxi', None),
    ('Leandro da Silva Lourenço', 'Leandro Enfermeiro', None),
    ('Marcelo Cardoso Rodrigues', 'Catiti', 'PDT'),
    ('Marcos Fernandes Araújo', 'Marquinho Oi', None),
    ('Marcos Oliveira Pereira', 'Marquinho Dentista', None),
    ('Marcos Paulo Casal Barbosa', 'Marquinho da Pipa', None),
    ('Mauricio Guimarães Nascimento', 'Dr. Maurício', None),
    ('Michel Reis da Silva', 'Michel Reis', None),
    ('Michele Barbosa Perisse Tavares', 'Michele Tavares', None),
    ('Moises Luiz Gomes', 'Moises Neguinho', None),
    ('Roberto Gabriel de Souza', 'Beto Gabriel', None),
    ('Saulo Henrique Silva de Paula', 'Saulo Henrique', None),
    ('Sergio Alberto Correa da Rocha', 'Serginho Corrêa', None),
    ('Valdecy Nunes da Rosa Filho', 'Valdecy Nunes', None),
    ('Victor Hugo Leonel da Silva', 'Vitinho Grandão', None),
    ('Wendell Oliveira Nascimento', 'Wendell Oliveira', None),
]

# Mesa Diretora 2025-2027 (cargo, nome parlamentar)
MESA_2025_2027 = [
    ('Presidente', 'Claudio Thomaz'),
    ('1º Vice-Presidente', 'Junior Reis'),
    ('2º Vice-Presidente', 'Catiti'),
    ('1º Secretário', 'Delza de Oliveira'),
    ('2º Secretário', 'Clovinho Sempre Junto'),
]

# Comissões Permanentes 2025/2026 (nome, presidente por nome parlamentar)
COMISSOES = [
    ('Legislação, Justiça e Redação Final', 'Dr. Maurício'),
    ('Finanças e Orçamento', 'Alex Freitas'),
    ('Educação e Cultura', 'Alex Freitas'),
    ('Saúde e Assistência Social', 'Juliana do Taxi'),
    ('Transportes', 'Vitinho Grandão'),
    ('Defesa do Consumidor', 'Moises Neguinho'),
    ('Obras e Serviços Públicos', 'Vitinho Grandão'),
    ('Meio Ambiente e Qualidade de Vida', 'Dr. Maurício'),
    ('Fiscalização', 'Vitinho Grandão'),
    ('Desenvolvimento Urbano', 'Juliana do Taxi'),
    ('Direitos da Mulher e da Criança e do Adolescente',
     'Juliana do Taxi'),
    ('Defesa dos Direitos Humanos', 'Michel Reis'),
    ('Defesa dos Direitos da Pessoa com Deficiência', 'Dr. Maurício'),
    ('Segurança Alimentar e Nutricional', 'Delza de Oliveira'),
    ('Segurança', 'Beto Gabriel'),
    ('Esporte, Lazer e Turismo', 'Marquinho Oi'),
    ('Prevenção e Combate às Drogas', 'Delza de Oliveira'),
    ('Prevenção e Combate à Pirataria', 'Moises Neguinho'),
    ('Defesa dos Direitos do Idoso', 'Leandro Enfermeiro'),
    ('Defesa dos Direitos da Juventude', 'Vitinho Grandão'),
    ('Defesa dos Animais', 'Michele Tavares'),
    ('Desenvolvimento Econômico, da Indústria e do Comércio',
     'Carlinhos da Barreira'),
    ('Agricultura, Pecuária, Abastecimento, Pesca e Desenvolvimento '
     'Rural', 'Junior Reis'),
    ('Promoção de Igualdade Racial', 'Catiti'),
    ('Trabalho, Emprego e Geração de Renda', 'Marquinho Dentista'),
    ('Defesa Civil', 'Carlinhos da Barreira'),
    ('Administração e Assuntos Referentes à Gestão de Pessoal',
     'Junior Reis'),
    ('Habitação e Regularização Fundiária', 'Dr. Maurício'),
    ('Prevenção e Combate à Pedofilia', 'Junior Reis'),
    ('Atenção aos Recursos Hídricos e Serviços de Esgoto e Energia '
     'Elétrica', 'Dr. Maurício'),
]

# Art. 87, §1º do Regimento Interno + APL (prática administrativa da CMDC)
TIPOS_MATERIA = [
    # (sigla, descricao, exige_analise_previa, ordem)
    ('APL', 'Anteprojeto de Lei', True, 10),
    ('PELOM', 'Proposta de Emenda à Lei Orgânica', False, 20),
    ('PLC', 'Projeto de Lei Complementar à Lei Orgânica', False, 30),
    ('PL', 'Projeto de Lei', False, 40),
    ('PR', 'Projeto de Resolução', False, 50),
    ('PDL', 'Projeto de Decreto Legislativo', False, 60),
    ('PLD', 'Projeto de Lei Delegada', False, 70),
    ('EME', 'Emenda', False, 80),
    ('IND', 'Indicação Legislativa', False, 90),
    ('REQ', 'Requerimento', False, 100),
    ('REC', 'Recurso', False, 110),
    ('VET', 'Veto', False, 120),
]

UNIDADES_TRAMITACAO = [
    'Protocolo Legislativo',
    'Procuradoria / Assessoria Técnica Legislativa',
    'Mesa Diretora',
    'Gabinete da Presidência',
    'Comissão de Legislação, Justiça e Redação Final',
    'Comissões Permanentes',
    'Departamento de Assuntos de Plenário',
    'Plenário',
    'Setor de Atas',
    'Poder Executivo',
    'Arquivo',
]

STATUS_TRAMITACAO = [
    # (descricao, fim_tramitacao)
    ('Protocolada', False),
    ('Em Análise Prévia (Procuradoria)', False),
    ('Análise Prévia concluída — admissível', False),
    ('Devolvida ao autor (art. 88, RI)', True),
    ('Convertida em projeto', True),
    ('Aguardando parecer de comissão (art. 54, RI)', False),
    ('Com parecer — aguardando pauta', False),
    ('Incluída na Ordem do Dia', False),
    ('Aprovada em 1º turno', False),
    ('Em Redação Final (art. 162, RI)', False),
    ('Aprovada — enviada à sanção', False),
    ('Aprovada — promulgada', True),
    ('Rejeitada', True),
    ('Rejeitada — parecer contrário das comissões (art. 93, RI)', True),
    ('Prejudicada (art. 142, RI)', True),
    ('Retirada pelo autor', True),
    ('Vetada — veto em apreciação', False),
    ('Arquivada (art. 95, RI — fim de legislatura)', True),
    ('Arquivada', True),
]

TIPOS_NORMA = [
    ('LO', 'Lei Ordinária'),
    ('LC', 'Lei Complementar'),
    ('ELOM', 'Emenda à Lei Orgânica'),
    ('RES', 'Resolução'),
    ('DL', 'Decreto Legislativo'),
    ('LD', 'Lei Delegada'),
]

PARTIDOS = {
    'PRD': 'Partido Renovação Democrática',
    'MDB': 'Movimento Democrático Brasileiro',
    'PDT': 'Partido Democrático Trabalhista',
}


class Command(BaseCommand):
    help = ('Carga inicial: CMDC, 20ª Legislatura (2025-2028), '
            'vereadores, Mesa 2025-2027, comissões, tipos e status '
            'conforme o Regimento Interno.')

    @transaction.atomic
    def handle(self, *args, **options):
        casa, _ = CasaLegislativa.objects.update_or_create(
            pk=1,
            defaults=dict(
                nome='Câmara Municipal de Duque de Caxias',
                sigla='CMDC',
                municipio='Duque de Caxias',
                uf='RJ',
                endereco='Rua Paulo Lins, 41 — Jardim 25 de Agosto, '
                         'Duque de Caxias/RJ',
                telefone='(21) 2784-6900',
                site='https://www.cmdc.rj.gov.br',
            ))
        self.stdout.write(f'Casa: {casa}')

        legislatura, _ = Legislatura.objects.get_or_create(
            numero=20,
            defaults=dict(data_inicio=datetime.date(2025, 1, 1),
                          data_fim=datetime.date(2028, 12, 31)))
        for n, ano in enumerate(range(2025, 2029), start=1):
            SessaoLegislativa.objects.get_or_create(
                legislatura=legislatura, numero=n,
                defaults=dict(ano=ano,
                              data_inicio=datetime.date(ano, 2, 1),
                              data_fim=datetime.date(ano, 12, 15)))
        self.stdout.write(f'Legislatura: {legislatura} + 4 sessões '
                          'legislativas')

        partidos = {
            sigla: Partido.objects.get_or_create(
                sigla=sigla, defaults={'nome': nome})[0]
            for sigla, nome in PARTIDOS.items()
        }

        vereadores = {}
        for nome_civil, nome_parlamentar, sigla in VEREADORES:
            v, _ = Vereador.objects.get_or_create(
                nome_parlamentar=nome_parlamentar,
                defaults=dict(nome_civil=nome_civil,
                              partido=partidos.get(sigla)))
            vereadores[nome_parlamentar] = v
            Mandato.objects.get_or_create(
                vereador=v, legislatura=legislatura,
                defaults=dict(data_inicio=datetime.date(2025, 1, 1)))
            # Autor correspondente (para autoria de matérias)
            Autor.objects.get_or_create(
                vereador=v, defaults=dict(tipo=Autor.Tipo.VEREADOR))
        self.stdout.write(f'Vereadores: {len(vereadores)} '
                          '(fonte oficial em atualização — conferir '
                          '30ª vaga e filiações partidárias)')

        # Mesa Diretora — art. 24, §1º do RI: 1 Presidente, 2 Vices,
        # 2 Secretários
        for ordem, (cargo_nome, parlamentar) in enumerate(MESA_2025_2027,
                                                          start=1):
            cargo, _ = CargoMesa.objects.get_or_create(
                descricao=cargo_nome, defaults={'ordem': ordem})
            ComposicaoMesa.objects.get_or_create(
                legislatura=legislatura, cargo=cargo,
                vereador=vereadores[parlamentar],
                defaults=dict(data_inicio=datetime.date(2025, 1, 1),
                              data_fim=datetime.date(2027, 12, 31)))
        self.stdout.write('Mesa Diretora 2025-2027: 5 cargos')

        for nome, presidente in COMISSOES:
            comissao, _ = Comissao.objects.get_or_create(
                nome=nome,
                defaults={'tipo': Comissao.Tipo.PERMANENTE})
            MembroComissao.objects.get_or_create(
                comissao=comissao,
                vereador=vereadores[presidente],
                cargo=MembroComissao.Cargo.PRESIDENTE,
                defaults={'periodo': '2025/2026'})
        self.stdout.write(f'Comissões permanentes: {len(COMISSOES)} '
                          '(somente presidentes — completar membros)')

        for sigla, descricao, exige_ap, ordem in TIPOS_MATERIA:
            TipoMateria.objects.get_or_create(
                sigla=sigla,
                defaults=dict(descricao=descricao,
                              exige_analise_previa=exige_ap,
                              ordem=ordem))
        for nome in UNIDADES_TRAMITACAO:
            UnidadeTramitacao.objects.get_or_create(nome=nome)
        for descricao, fim in STATUS_TRAMITACAO:
            StatusTramitacao.objects.get_or_create(
                descricao=descricao,
                defaults={'fim_tramitacao': fim})
        for sigla, descricao in TIPOS_NORMA:
            TipoNorma.objects.get_or_create(
                sigla=sigla, defaults={'descricao': descricao})

        self.stdout.write(self.style.SUCCESS(
            'Seed concluído: tipos de matéria (art. 87, RI + APL), '
            'unidades, status de tramitação e tipos de norma criados.'))
