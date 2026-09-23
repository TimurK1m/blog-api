import os

from django.core.wsgi import get_wsgi_application

from settings.conf import ENV_ID

assert ENV_ID, "ENV_ID is not set. Please set the ENV_ID environment variable."

os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'settings.env.{ENV_ID}')

application = get_wsgi_application()
