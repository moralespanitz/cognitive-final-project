"""
Development settings using SQLite (no PostgreSQL required).
Use this for local development without Docker.
"""

from .settings import *

# Override database to use SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Override Redis to use in-memory backend for development (no Redis required)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

print("✓ Using SQLite database and in-memory cache (development mode)")
