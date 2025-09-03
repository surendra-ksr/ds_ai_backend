# E:/Repos/ds_ai_backend/config/settings/prod.py

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
# In production, the SECRET_KEY environment variable MUST be set.
SECRET_KEY = os.environ['SECRET_KEY']

# Set the allowed hosts from an environment variable (e.g., 'www.myapp.com,myapp.com')
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')

# Production-specific database configuration (e.g., using a cloud provider)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('DB_NAME'),
#         'USER': os.environ.get('DB_USER'),
#         'PASSWORD': os.environ.get('DB_PASSWORD'),
#         'HOST': os.environ.get('DB_HOST'),
#         'PORT': os.environ.get('DB_PORT'),
#     }
# }

# Add any other production-specific settings here, like logging, caching, etc.
