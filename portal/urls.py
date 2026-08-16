from django.urls import path

from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.home, name='home'),
    path('materias/', views.materias, name='materias'),
    path('materias/<int:pk>/', views.materia_detalhe,
         name='materia_detalhe'),
    path('sessoes/', views.sessoes, name='sessoes'),
    path('sessoes/<int:pk>/', views.sessao_detalhe, name='sessao_detalhe'),
    path('normas/', views.normas, name='normas'),
    path('vereadores/', views.vereadores, name='vereadores'),
    path('comissoes/', views.comissoes, name='comissoes'),
]
