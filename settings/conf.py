from decouple import config




SECRET_KEY = config("CRM_SECRET_KEY", cast=str)
ENV_ID = config("ENV_ID", cast=str)