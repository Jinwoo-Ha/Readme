from django.db import models

class Document(models.Model):
    source_code = models.FileField(upload_to='uploads/source_code/')
    presentation = models.FileField(upload_to='uploads/presentations/')
    readme = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)