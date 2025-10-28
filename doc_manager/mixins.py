from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect

class UploaderRequiredMixin(UserPassesTestMixin):
    """
    Mixin che verifica se l'utente è autenticato e ha il ruolo 'is_uploader'.
    """
    
    def test_func(self):
        # 1. Verifichiamo che l'utente sia loggato E
        # 2. Verifichiamo che la flag 'is_uploader' sul suo profilo sia True.
        # Il 'profile' è accessibile direttamente tramite l'utente grazie alla relazione OneToOne.
        user = self.request.user
        return user.is_authenticated and user.profile.is_uploader

    def handle_no_permission(self):
        # Se il test fallisce (utente non loggato o non uploader), 
        # reindirizziamo alla home.
        return redirect('home')