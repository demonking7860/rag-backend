"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/files/', include('apps.files.urls')),
    path('api/chat/', include('apps.chat.urls')),
    path('api/health/', include('apps.rag.urls')),  # Health check in RAG app
]

