import os
from celery import Celery

# Imposta la configurazione predefinita di Django per il programma 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Crea l'istanza dell'applicazione Celery.
app = Celery('config')

# Carica la configurazione da django settings.
# Il namespace 'CELERY' garantisce che Celery cerchi tutte le chiavi di configurazione 
# che iniziano con 'CELERY_' nel file settings.py.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Individua automaticamente i task in tutti i file tasks.py di tutte le app installate
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')