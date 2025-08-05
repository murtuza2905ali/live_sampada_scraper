from django.urls import path
from . import views

urlpatterns = [
    path('trigger-scrape/', views.trigger_scrape, name='trigger_scrape'),
]
