import os, sys
from django.core.wsgi import get_wsgi_application

# Debug dump
print(">>> WSGI: DEBUG =", os.getenv("DEBUG"), file=sys.stderr)
print(">>> WSGI: ALLOWED_HOSTS env =", os.getenv("ALLOWED_HOSTS"), file=sys.stderr)

application = get_wsgi_application()
