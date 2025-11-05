from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    # Tipi di documento
    DOCUMENT_TYPES = [
        ('native', 'Native PDF'),
        ('scanned', 'Scanned PDF'),
    ]
    
    # Stati di processamento
    PROCESSING_STATES = [
        ('pending', 'Pending'),
        ('ocr_queued', 'OCR Queued'),
        ('ocr_processing', 'OCR Processing'),
        ('ocr_completed', 'OCR Completed'),
        ('ocr_failed', 'OCR Failed'),
        ('rag_processing', 'RAG Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    uploader = models.ForeignKey(User, on_delete=models.CASCADE)    
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    title = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    document_type = models.CharField(
        max_length=20, 
        choices=DOCUMENT_TYPES, 
        default='native'
    )
    processing_state = models.CharField(
        max_length=20,
        choices=PROCESSING_STATES,
        default='pending'
    )
    
    is_processed = models.BooleanField(default=False)
    processing_output = models.TextField(blank=True, null=True)
    
    ocr_text = models.TextField(blank=True, null=True, help_text="Extracted text from OCR")
    ocr_completed_at = models.DateTimeField(null=True, blank=True)
    ocr_error = models.TextField(blank=True, null=True)
    
    processed_file = models.FileField(
        upload_to='documents/processed/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="PDF with OCR text layer"
    )

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-uploaded_at']