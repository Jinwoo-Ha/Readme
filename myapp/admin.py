from django.contrib import admin
from .models import Document, SourceCode, Presentation

class SourceCodeInline(admin.TabularInline):
    model = SourceCode
    extra = 1

class PresentationInline(admin.TabularInline):
    model = Presentation
    extra = 1

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'project_title', 'created_at', 'source_code_count', 'presentation_count']
    search_fields = ['project_title', 'project_description']
    list_filter = ['created_at']
    inlines = [SourceCodeInline, PresentationInline]

    def source_code_count(self, obj):
        return obj.source_codes.count()
    source_code_count.short_description = 'Source Files'

    def presentation_count(self, obj):
        return obj.presentations.count()
    presentation_count.short_description = 'Presentation Files'

@admin.register(SourceCode)
class SourceCodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'file', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['document__project_title', 'file']

@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'file', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['document__project_title', 'file']