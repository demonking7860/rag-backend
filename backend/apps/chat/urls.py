from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat, name='chat'),
    path('history/<int:conversation_id>/', views.chat_history, name='chat_history'),
]

