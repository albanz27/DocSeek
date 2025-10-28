# Assicura che l'app Celery sia sempre importata quando Django si avvia
from .celery import app as celery_app

__all__ = ('celery_app',)