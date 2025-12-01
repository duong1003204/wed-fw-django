# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('ajax/search/', views.search_suggestions, name='search_suggestions'),
]