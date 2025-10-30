from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)    
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    title = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    processing_output = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-uploaded_at'] 