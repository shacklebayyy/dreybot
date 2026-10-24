import os

env = os.getenv('DJANGO_ENV', os.getenv('ENVIRONMENT', '')).lower()
is_production = (
    env == 'production'
    or os.getenv('RENDER') == 'true'
    or os.getenv('DEBUG', '').lower() in ('false', '0', 'f')
)

if is_production:
    from .production import *
else:
    from .development import *
