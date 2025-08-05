from django.urls import path
from .views import trigger_scrape

urlpatterns = [
    path('', trigger_scrape, name='trigger_scrape'),  # root → trigger_scrape view
]
