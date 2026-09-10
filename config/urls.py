from django.http import HttpResponse
from django.core.management import call_command
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    path('accounts/', include('accounts.urls')),
    path('investments/', include('investments.urls')),
    path('run-migrations-now/', lambda request: HttpResponse(str(call_command('migrate')))),
]

# Add this at the bottom to serve images in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)