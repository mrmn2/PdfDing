"""
Django settings for pdfding project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parents[2]


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.openid_connect',
    'django_htmx',
    'huey.contrib.djhuey',
    'admin',
    'backup',
    'pdf',
    'users',
    # django_cleanup needs to be placed last in INSTALLED_APPS
    'django_cleanup.apps.CleanupConfig',
]

# remove these apps for the e2e tests as they cause problems and are not needed
if os.environ.get('E2E_TESTS'):
    INSTALLED_APPS.remove('huey.contrib.djhuey')
    INSTALLED_APPS.remove('backup')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.pdfding_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

if os.environ.get('DATABASE_TYPE') == 'POSTGRES':  # pragma: no cover
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_NAME', 'pdfding'),
            'USER': os.environ.get('POSTGRES_USER', 'pdfding'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'password'),
            'HOST': os.environ.get('POSTGRES_HOST', 'postgres'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db' / 'db.sqlite3',
            'BACKUP_NAME': BASE_DIR / 'db' / 'backup.sqlite3',
            'TEST': {
                'NAME': BASE_DIR / 'db' / 'test.sqlite3',
            },
        }
    }

    # remove entry for the e2e tests as it causes problems and is not needed
    if os.environ.get('E2E_TESTS'):
        DATABASES['default'].pop('TEST')


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

# number of items of overview paginations
ITEMS_PER_PAGE = 12

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_CHANGE_EMAIL = True  # users are limited to one email address. this address can be changed.
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_LOGOUT_REDIRECT_URL = '/accountlogin/'
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_ADAPTER = 'users.adapters.DisableSignupAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'users.adapters.HandleAdminNewUserAdapter'

LOGIN_REDIRECT_URL = '/pdf'
LOGIN_URL = '/accountlogin/'

SOCIALACCOUNT_OPENID_CONNECT_URL_PREFIX = ''

# Huey task queue
HUEY = {
    'huey_class': 'huey.SqliteHuey',
    'filename': BASE_DIR / 'db' / 'tasks.sqlite3',
    'immediate': False,  # settings.DEBUG,  # If DEBUG=True, run synchronously.
    'results': False,  # Store return values of tasks.
    'store_none': False,  # If a task returns None, do not save to results.
    'utc': True,  # Use UTC for all times internally.
    'consumer': {
        'workers': 1,
        'worker_type': 'thread',
        'initial_delay': 5,
        'backoff': 1.15,
        'max_delay': 10,
        'scheduler_interval': 10,
        'periodic': True,
        'check_worker_health': True,
        'health_check_interval': 10,
    },
}

CONSUME_DIR = BASE_DIR / 'consume'

log_level = os.environ.get('LOG_LEVEL', 'ERROR')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': log_level,
    },
    'django': {
        'handlers': ['console'],
        'level': log_level,
        'propagate': True,
    },
    'django.request': {
        'handlers': ['mail_admins'],
        'filters': ['require_debug_false'],
        'level': log_level,
        'propagate': False,
    },
    'loggers': {
        'management': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
