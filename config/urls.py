from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.core.management import call_command
from django.db import connection
from io import StringIO

# This function forces Django to rebuild the missing tables
def force_build_database(request):
    # 1. Clear the migration history so Django is forced to build the tables again
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM django_migrations WHERE app='investments';")
    
    # 2. Run the migrations to actually create the tables
    out = StringIO()
    call_command('migrate', 'investments', stdout=out)
    
    return HttpResponse(f"<pre>{out.getvalue()}</pre>")

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # THE MAGIC FIX URL
    path('force-build-db/', force_build_database),
    
    path('', include('pages.urls')),
    path('accounts/', include('accounts.urls')),
    path('investments/', include('investments.urls')),
]
