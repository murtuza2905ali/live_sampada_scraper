import os
from pathlib import Path
# Top of settings.py, right after imports
import sys
print(">>> DEBUG:", DEBUG, file=sys.stderr)
print(">>> ALLOWED_HOSTS from ENV:", os.getenv("ALLOWED_HOSTS"), file=sys.stderr)
print(">>> FINAL ALLOWED_HOSTS:", ALLOWED_HOSTS, file=sys.stderr)

# ─── Base dir ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Secret & Debug from ENV ────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-very-secret-key")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# ─── Allowed hosts ────────────────────────────────────────────────────────────
# If ALLOWED_HOSTS env set, use that; else if DEBUG=False, allow all; else localhost
if os.getenv("ALLOWED_HOSTS"):
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")
elif not DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# ─── CSRF trusted origins ─────────────────────────────────────────────────────
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if os.getenv("CSRF_TRUSTED_ORIGINS") else []

# ─── Use forwarded host header (behind Render’s proxy) ───────────────────────
USE_X_FORWARDED_HOST = True

# ─── Installed apps ───────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',
]

# ─── Middleware (add WhiteNoise) ─────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',     # static file serving
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ─── URL conf & WSGI ─────────────────────────────────────────────────────────
ROOT_URLCONF = 'sampada_scraper.urls'
WSGI_APPLICATION = 'sampada_scraper.wsgi.application'

# ─── Templates ────────────────────────────────────────────────────────────────
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

# ─── Database (default SQLite) ────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ─── Password validators ──────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = []

# ─── Internationalization ─────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ─── Static files (WhiteNoise) ────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'myapp' / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ─── Default auto field ───────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
