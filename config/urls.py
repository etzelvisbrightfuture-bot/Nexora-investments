from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.core.management import call_command

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # TEMPORARY: Run migrations on Render
    path('run-migrations-now/', lambda request: HttpResponse(str(call_command('migrate')))),
    
    # Your App URLs
    path('', include('pages.urls')),
    path('accounts/', include('accounts.urls')),
    path('investments/', include('investments.urls')),
]