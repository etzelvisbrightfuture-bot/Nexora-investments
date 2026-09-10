import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
# Wrap the application with WhiteNoise to serve static files
application = WhiteNoise(application, root='staticfiles/')