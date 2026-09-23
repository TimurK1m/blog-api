from settings.base import *
from decouple import config

DEBUG = False

ALLOWED_HOSTS = []

DATABASES = {
    'default'   : {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config("CRM_POSTGRES_DB", cast=str),
        'USER': config("CRM_POSTGRES_USER", cast=str),
        'PASSWORD': config("CRM_POSTGRES_PASSWORD", cast=str),
        'HOST': config("CRM_POSTGRES_HOST", cast=str),
        'PORT': config("CRM_POSTGRES_PORT", cast=int),
    }
}