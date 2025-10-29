from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegistrationForm

def home(request):
    """
    La view per la home page.
    """
    return render(request, 'home.html')

def signup(request):
    """
    Funzione View per gestire la registrazione di un nuovo utente.
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            
            return redirect('login') 
            
    else:
        form = UserRegistrationForm()
        
    return render(request, 'registration/signup.html', {'form': form})