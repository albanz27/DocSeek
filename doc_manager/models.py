from django.db import models
from django.contrib.auth.models import User # Importamos il modello User

class Document(models.Model):
    # 1. Collegamento all'utente che ha caricato il documento (ForeignKey)
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # 2. Il file fisico
    # Questo campo gestirà l'upload nel filesystem
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    
    # 3. Metadati e tracciamento
    title = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # 4. Campo per tracciare lo stato di elaborazione
    is_processed = models.BooleanField(default=False)
    
    # Campo opzionale per i risultati del processo (es. testo estratto)
    processing_output = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-uploaded_at'] # Ordina i documenti dal più recente