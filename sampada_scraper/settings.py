import os
from pathlib import Path

# Base dir
BASE_DIR = Path(__file__).resolve().parent.parent

# 1) Secret & Debug from ENV
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-very-secret-key")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# 2) Allowed hosts from ENV
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# 3) Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',
]

# 4) Middleware (Whitenoise for static files)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # added
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sampada_scraper.urls'

# 5) Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'myapp' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sampada_scraper.wsgi.application'

# 6) Database (SQLite for dev; switch to Postgres via DATABASE_URL in PROD if needed)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 7) Password validators (kept empty)
AUTH_PASSWORD_VALIDATORS = []

# 8) Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# 9) Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'             # collectstatic yahan karega
STATICFILES_DIRS = [BASE_DIR / 'myapp' / 'static']  # agar static app folder mein hai
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 10) Default primary key field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
