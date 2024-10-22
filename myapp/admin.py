from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'project_title', 'created_at', 'image_folder']  # 목록에서 보여줄 필드들
    search_fields = ['project_title', 'project_description']  # 검색 가능한 필드들
    list_filter = ['created_at']  # 필터링 가능한 필드들

# 또는 더 간단하게:
# admin.site.register(Document)