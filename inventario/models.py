from django.db import models

# Create your models here.

class Produto(models.Model):
    nome = models.CharField('Produto', max_length=100)
    descricao = models.CharField('Descrição', max_length=100, blank=True, null=True)  # nova coluna

    def __str__(self):
        # Mostra nome + descrição se houver
        if self.descricao:
            return f"{self.nome} - {self.descricao}"
        return self.nome



class Cadastroitens(models.Model):
    produto = models.ForeignKey(Produto, related_name="lotes", on_delete=models.CASCADE)
    lote = models.CharField('Lote', max_length=15)
    validade = models.DateField('Validade')
    fornecedor = models.CharField('Fornecedor', max_length=50)
    quantidade = models.IntegerField('Quantidade')
    
    UNIDADE_MEDIDA_CHOICES = [
        ('UN', 'Unidade'),
        ('CX', 'Caixa'),
        ('PCT', 'PCT'),
    ] 
    
    
    ORIGEM_CHOICES = [
        ('Almoxarifado', 'Almoxarifado'),
        ('Doação', 'Doação'),
        ('Empréstimo', 'Empréstimo'),
    ] 
    
    unidade = models.CharField('Unidade de Medida', max_length=5, choices=UNIDADE_MEDIDA_CHOICES, default='UN')
    origem = models.CharField('Origem', max_length=15, choices=ORIGEM_CHOICES, default='Almoxarifado')
    data = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.lote} - {self.produto.nome}"
    


class Movimentacao(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('baixa', 'Baixa por requisição'),
        ('transferencia', 'Transferência'),
        ('devolucao', 'Devolução'),
        ('vencidos', 'Validade vencida'),
    ]
    tipo_movimentacao = models.CharField(max_length=50, choices=TIPO_CHOICES)
    requisitante = models.CharField(max_length=255)
    data = models.DateTimeField(auto_now_add=True)

class MovimentacaoItem(models.Model):
    movimentacao = models.ForeignKey(Movimentacao, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, related_name='movimentacao_produto', on_delete=models.CASCADE)
    descricao = models.ForeignKey(Produto, related_name='movimentacao_descricao', on_delete=models.CASCADE, null=True, blank=True)
    lote = models.ForeignKey(Cadastroitens, on_delete=models.CASCADE)
    quantidade_baixada = models.PositiveIntegerField()
