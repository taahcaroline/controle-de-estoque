from django.shortcuts import render

# Create your views here.


from django.shortcuts import render, redirect 
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from .forms import RegisterForm

# Create your views here.

def registro(request):
    template_name = 'registration/register.html'
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(settings.LOGIN_URL)
        
    context = {
        'form' : RegisterForm()
    }
    return render(request, 'registration/register.html', context)

