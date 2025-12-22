from django.contrib import admin
from .models import FileAsset


@admin.register(FileAsset)
class FileAssetAdmin(admin.ModelAdmin):
    list_display = ('filename', 'user', 'file_type', 'status', 'ingestion_status', 'deletion_failed', 'uploaded_at')
    list_filter = ('status', 'ingestion_status', 'deletion_failed', 'file_type')
    search_fields = ('filename', 'user__username')
    readonly_fields = ('uploaded_at', 'metadata')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')

