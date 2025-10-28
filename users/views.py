from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegistrationForm # Importiamo il nostro form

def home(request):
    """
    La view per la home page.
    """
    # Renderizza il template che creeremo a breve
    return render(request, 'home.html')

def signup(request):
    """
    Funzione View per gestire la registrazione di un nuovo utente.
    """
    if request.method == 'POST':
        # Se la richiesta è POST, creiamo il form con i dati inviati
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            # Se il form è valido, salviamo l'utente e il profilo
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            
            # Reindirizziamo l'utente alla pagina di login
            return redirect('login') 
            
    else:
        # Se la richiesta è GET, mostriamo un form vuoto
        form = UserRegistrationForm()
        
    # Rendiamo il template 'registration/signup.html'
    return render(request, 'registration/signup.html', {'form': form})