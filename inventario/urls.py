from django.urls import path
from inventario import views


urlpatterns = [
     path('', views.home, name='home'),
     path('cadastro/', views.cadastro, name='cadastro'),
     path('baixa/', views.baixa_estoque, name='baixa'),
     path('get_lotes/<int:produto_id>/', views.get_lotes, name='get_lotes'),
     path('cadastroproduto/', views.cadastroproduto, name='cadastroproduto'),
     path("estoque/", views.estoque, name="estoque"),
     path("estoque/<int:item_id>/editar/", views.editar_estoque, name="editar_item"),
     path("estoque/<int:item_id>/excluir/", views.excluir_item, name="excluir_item"),
     path('relatorio/<int:movimentacao_id>/', views.gerar_relatorio_pdf, name='gerar_relatorio_pdf'),
     path('historico/', views.historico_movimentacoes, name='historico_movimentacoes'),
     path('relatorio-periodo/', views.relatorio_consumo_periodo, name='relatorio_consumo_periodo'),  
     path('entradas/', views.historico_entradas, name='historico_entradas'),
     path('relatorio-entrada/<int:cadastroitens_id>/', views.gerar_relatorio_entrada_pdf, name='gerar_relatorio_entrada_pdf'),

]


    
