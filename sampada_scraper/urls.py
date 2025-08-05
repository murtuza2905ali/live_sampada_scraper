from django.contrib import admin
from django.urls import path, include  # include imported

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myapp.urls')),        # root -> myapp
    path('myapp/', include('myapp.urls')),  # optional extra prefix if you want it
]
