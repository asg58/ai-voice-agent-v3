import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuratie-inhoud verplaatst vanuit verspreide bestanden
# Voeg hier relevante configuratie toe

INSTALLED_APPS = [
    # Andere geïnstalleerde apps
    'django.contrib.staticfiles',  # Voor het bedienen van statische bestanden
]

MIDDLEWARE = [
    # Andere middleware
    'django.middleware.security.SecurityMiddleware',
]

# Beveiligingsinstellingen
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# CSRF-instellingen
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Statische bestanden
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media bestanden
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# E-mail instellingen
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@example.com'
EMAIL_HOST_PASSWORD = 'your_password'

# Debugging
DEBUG = True

# Toegestane hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

# Database-instellingen
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Tijdzone
TIME_ZONE = 'UTC'

# Taalcode
LANGUAGE_CODE = 'en-us'

# Sleutels en geheimen
SECRET_KEY = 'your_secret_key'

# Andere relevante configuratie
# ...existing code...