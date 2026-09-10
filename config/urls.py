from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.core.management import call_command
from io import StringIO

# This function will run your migrations and show you the result
def trigger_migrations(request):
    out = StringIO()
    call_command('migrate', stdout=out)
    return HttpResponse(f"<pre>{out.getvalue()}</pre>")

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # THE MAGIC URL
    path('run-migrations-now/', trigger_migrations),
    
    path('', include('pages.urls')),
    path('accounts/', include('accounts.urls')),
    path('investments/', include('investments.urls')),
]