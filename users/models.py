from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# 1. Profile Model
class Profile(models.Model):
    # La relazione uno-a-uno con il modello User di Django
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Campo booleano per il ruolo di caricatore/processore
    is_uploader = models.BooleanField(default=False)
    
    # Campo booleano per il ruolo di cercatore/visualizzatore
    is_searcher = models.BooleanField(default=False)

    def __str__(self):
        # Rappresentazione leggibile del profilo
        return f'{self.user.username} Profile'

# 2. Signals per la Creazione Automatica del Profilo
# Questi segnali assicurano che ogni volta che un oggetto User viene salvato, 
# viene creato o aggiornato automaticamente anche l'oggetto Profile corrispondente.

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()