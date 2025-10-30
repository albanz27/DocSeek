from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect

class UploaderRequiredMixin(UserPassesTestMixin):
    """
    Mixin che verifica se l'utente è autenticato e ha il ruolo 'is_uploader'.
    """
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.profile.is_uploader

    def handle_no_permission(self):
        return redirect('home')
    
class SearcherRequiredMixin(UserPassesTestMixin):
    """
    Mixin che verifica se l'utente è autenticato e ha il ruolo 'is_searcher'.
    """
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.profile.is_searcher
    
    def handle_no_permission(self):
        return redirect('home')