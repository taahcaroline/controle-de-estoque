from django import forms
from .models import Cadastroitens, Produto, Movimentacao, MovimentacaoItem



class CadastroitensForm(forms.ModelForm):
    class Meta:
     model = Cadastroitens
     fields = '__all__'
     widgets = {
            'validade': forms.DateInput(attrs={'type': 'date'})}


class CadastroprodutoForm(forms.ModelForm):
    class Meta:
     model = Produto
     fields = '__all__'
     
class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ['tipo_movimentacao', 'requisitante']

class MovimentacaoItemForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoItem
        fields = ['produto', 'descricao','lote', 'quantidade_baixada']
    
