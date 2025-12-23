from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_files, name='list_files'),
    path('presign/', views.presign_upload, name='presign_upload'),
    path('finalize/', views.finalize_upload, name='finalize_upload'),
    path('<int:file_id>/', views.delete_file, name='delete_file'),
    path('<int:file_id>/update/', views.update_file, name='update_file'),
    path('<int:file_id>/retry-finalize/', views.retry_finalize, name='retry_finalize'),
    path('<int:file_id>/retry-chunks/', views.retry_chunks, name='retry_chunks'),
    path('deletion-failed/', views.deletion_failed_files, name='deletion_failed_files'),
]

