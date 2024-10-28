from django.db import models

class Document(models.Model):
    project_title = models.CharField(max_length=200, default='Untitled Project')
    project_description = models.TextField(default='No description provided')
    readme = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.project_title

class SourceCode(models.Model):
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE,
        related_name='source_codes'
    )
    file = models.FileField(upload_to='uploads/source_code/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document.project_title} - {self.file.name}"

class Presentation(models.Model):
    document = models.ForeignKey(
        Document, 
        on_delete=models.CASCADE,
        related_name='presentations'
    )
    file = models.FileField(upload_to='uploads/presentations/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document.project_title} - {self.file.name}"