# chat/models.py
from django.db import models

class Document(models.Model):
    file = models.FileField(upload_to='documents/')  # Campo para guardar el archivo
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Fecha de subida
    converted_text = models.TextField(blank=True, null=True)  # Texto convertido desde PDF o TXT

    def __str__(self):
        return f"{self.file.name}"
