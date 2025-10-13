from django import forms
from .models import Cadastroitens, Produto, Movimentacao, MovimentacaoItem
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm


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
    

class CustomLoginForm(forms.Form):
    username = forms.CharField(
        label='Nome de Usuário',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    # Validação customizada, por exemplo, verificar se o usuário existe
    def clean_username(self):
        username = self.cleaned_data['username']
        if not User.objects.filter(username=username).exists():
            raise ValidationError("Usuário não encontrado.")
        return username
    
    
class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    username = forms.CharField(
        label='Nome de Usuário',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirme sua senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )