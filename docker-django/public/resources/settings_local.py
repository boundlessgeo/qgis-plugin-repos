ADMINS = (
  ('Larry Shaffer', 'lshaffer@boundlessgeo.com'),
)

MANAGERS = ADMINS
# Tell django which clients may receive debug messages...used by django-debug-toolbar
INTERNAL_IPS = ('127.0.0.1','')

# Disable for prod machine
DEBUG = True
TEMPLATE_DEBUG = DEBUG
LOGGING_OUTPUT_ENABLED=DEBUG
LOGGING_LOG_SQL=DEBUG


# ADMINS = (
#     # ('Your Name', 'your_email@domain.com'),
# )

DATABASES = {
    'default': {
        # Newer django versions may require you to use the postgis backed

        'ENGINE': 'django.contrib.gis.db.backends.postgis', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        #'ENGINE': 'django.db.backends.postgresql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'qgis-django', # Or path to database file if using sqlite3.
        'USER': 'docker', # Not used with sqlite3.
        'PASSWORD': 'docker', # Not used with sqlite3.
        'HOST': '192.168.117.128', # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '25432', # Set to empty string for default. Not used with sqlite3.
    }
}

#Tim for google maps in user community page
#qgis-django.localhost
GOOGLE_API_KEY='ABQIAAAAyZw9WlHOs4CazzwUByOgZxQok5WFiNcwymBq4ClbhSeQY6fSMhTl0KHT2Donh18dLk3P4AC4ddOarA'

PAGINATION_DEFAULT_PAGINATION=5

# ABP: More portable config
import os
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = SITE_ROOT  + '/static/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = 'http://localhost:8000/static/'

SERVE_STATIC_MEDIA = True

# TIM: Place where search indexes are stored for snippets - should be non web accessible
HAYSTACK_WHOOSH_PATH = '/home/web/qgis-django/search-index'

# Tim Email settings
EMAIL_HOST = 'localhost'
#EMAIL_PORT =
DEFAULT_FROM_EMAIL = 'noreply@qgis.org'
