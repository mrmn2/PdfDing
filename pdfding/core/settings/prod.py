import os

from .base import *  # noqa: F401 F403

try:
    from .version import VERSION
except ModuleNotFoundError:
    VERSION = 'unknown'

# security related settings
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# By default, Django’s hashed static files system creates two copies of each file in STATIC_ROOT:
# one using the original name, e.g. app.js, and one using the hashed name, e.g. app.db8f2edc0c8a.js.
# If WhiteNoise’s compression backend is being used this will create another two copies of each of
# these files (using Gzip and Brotli compression) resulting in six output files for each input file.
# In some deployment scenarios it can be important to reduce the size of the build artifact as much as possible.
# This setting removes the “un-hashed” version of the file (which should be not be referenced in any case)
# which should reduce the space required for static files by half.
WHITENOISE_KEEP_ONLY_HASHED_FILES = True

# web security settings
ALLOWED_HOSTS = os.environ.get('HOST_NAME', '').split(',')
ALLOWED_HOSTS = [allowed_host.strip() for allowed_host in ALLOWED_HOSTS if allowed_host != '']

if ALLOWED_HOSTS:
    CSRF_TRUSTED_ORIGINS = []
    for allowed_host in ALLOWED_HOSTS:
        CSRF_TRUSTED_ORIGINS.extend([f'https://{allowed_host}', f'http://{allowed_host}'])

SECRET_KEY = os.environ.get('SECRET_KEY')

if os.environ.get('CSRF_COOKIE_SECURE', 'TRUE') == 'TRUE':
    CSRF_COOKIE_SECURE = True
if os.environ.get('SESSION_COOKIE_SECURE', 'TRUE') == 'TRUE':
    SESSION_COOKIE_SECURE = True
if os.environ.get('SECURE_SSL_REDIRECT') == 'TRUE':
    SECURE_SSL_REDIRECT = True
if os.environ.get('SECURE_HSTS_SECONDS'):
    SECURE_HSTS_SECONDS = os.environ.get('SECURE_HSTS_SECONDS')

# backup settings
if os.environ.get('BACKUP_ENABLE') == 'TRUE':
    # without a dummy value, huey will not start
    BACKUP_ENABLED = True
    BACKUP_ENDPOINT = os.environ.get('BACKUP_ENDPOINT', 'minio.pdfding.com')
    BACKUP_ACCESS_KEY = os.environ.get('BACKUP_ACCESS_KEY')
    BACKUP_SECRET_KEY = os.environ.get('BACKUP_SECRET_KEY')
    BACKUP_BUCKET_NAME = os.environ.get('BACKUP_BUCKET_NAME', 'pdfding')
    BACKUP_SCHEDULE = os.environ.get('BACKUP_SCHEDULE', '0 2 * * *')
    if os.environ.get('BACKUP_SECURE') == 'TRUE':
        BACKUP_SECURE = True
    else:
        BACKUP_SECURE = False

    if os.environ.get('BACKUP_ENCRYPTION_ENABLE') == 'TRUE':
        BACKUP_ENCRYPTION_ENABLED = True
        BACKUP_ENCRYPTION_PASSWORD = os.environ['BACKUP_ENCRYPTION_PASSWORD']
        BACKUP_ENCRYPTION_SALT = os.environ.get('BACKUP_ENCRYPTION_SALT', 'pdfding')
    else:
        BACKUP_ENCRYPTION_ENABLED = False
        # set to none, so that backups.tasks.backup_function raises no attribute error
        BACKUP_ENCRYPTION_PASSWORD = None
        BACKUP_ENCRYPTION_SALT = None
else:
    BACKUP_ENABLED = False
    BACKUP_SCHEDULE = '*/1 * * * *'

# consume settings
if os.environ.get('CONSUME_ENABLE') == 'TRUE':
    CONSUME_ENABLED = True
    CONSUME_TAG_STRING = os.environ.get('CONSUME_TAGS', '')
    if os.environ.get('CONSUME_SKIP_EXISTING') == 'FALSE':
        CONSUME_SKIP_EXISTING = False
    else:
        CONSUME_SKIP_EXISTING = True
else:
    CONSUME_ENABLED = False
    CONSUME_SKIP_EXISTING = False

# mail settings
if os.environ.get('EMAIL_BACKEND') == 'SMTP':
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.environ.get('SMTP_HOST')
    EMAIL_PORT = os.environ.get('SMTP_PORT', 587)
    EMAIL_HOST_USER = os.environ.get('SMTP_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('SMTP_PASSWORD')
    if os.environ.get('SMTP_USE_TLS') == 'TRUE':
        EMAIL_USE_TLS = True
    if os.environ.get('SMTP_USE_SSL') == 'TRUE':
        EMAIL_USE_SSL = True

try:
    DEFAULT_FROM_EMAIL = f'info@{ALLOWED_HOSTS[0]}'
except IndexError:
    DEFAULT_FROM_EMAIL = 'info@pdfding'

# authentication settings
ACCOUNT_DEFAULT_HTTP_PROTOCOL = os.environ.get('ACCOUNT_DEFAULT_HTTP_PROTOCOL', 'https')
if os.environ.get('ACCOUNT_EMAIL_VERIFICATION') == 'TRUE':
    ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
else:
    ACCOUNT_EMAIL_VERIFICATION = 'optional'

if os.environ.get('DISABLE_USER_SIGNUP') == 'TRUE':
    SIGNUP_CLOSED = True
else:
    SIGNUP_CLOSED = False

# configure the oidc provider
if os.environ.get('OIDC_ENABLE') == 'TRUE':
    # enable social logins only
    if os.environ.get('OIDC_ONLY') == 'TRUE':
        SOCIALACCOUNT_ONLY = True
        ACCOUNT_EMAIL_VERIFICATION = 'none'

    OIDC_GROUPS_CLAIM = os.environ.get('OIDC_GROUPS_CLAIM', 'groups')
    OIDC_ADMIN_GROUP = os.environ.get('OIDC_ADMIN_GROUP', '')
    OIDC_SCOPE = ['openid', 'profile', 'email']
    if OIDC_GROUPS_CLAIM not in OIDC_SCOPE:
        OIDC_SCOPE.append(OIDC_GROUPS_CLAIM)

    SOCIALACCOUNT_PROVIDERS = {
        'openid_connect': {
            'EMAIL_AUTHENTICATION': True,
            # Optional PKCE defaults to False, but may be required by your provider
            # Applies to all APPS.
            'OAUTH_PKCE_ENABLED': True,
            'APPS': [
                {
                    'provider_id': 'oidc',
                    'name': os.environ.get('OIDC_PROVIDER_NAME', 'OIDC').upper(),
                    'client_id': os.environ['OIDC_CLIENT_ID'],
                    'secret': os.environ['OIDC_CLIENT_SECRET'],
                    'settings': {
                        'server_url': os.environ['OIDC_AUTH_URL'],
                        # Optional token endpoint authentication method.
                        # May be one of 'client_secret_basic', 'client_secret_post'
                        # If omitted, a method from the server's
                        # token auth methods list is used
                        # 'token_auth_method': 'client_secret_basic',
                    },
                }
            ],
            'SCOPE': OIDC_SCOPE,
        }
    }

# themes
theme_colors = ['green', 'blue', 'gray', 'red', 'pink', 'orange', 'brown']
themes = ['light', 'dark', 'creme']

if not os.environ.get('DEFAULT_THEME'):
    DEFAULT_THEME = 'light'
elif os.environ.get('DEFAULT_THEME') in themes:
    DEFAULT_THEME = os.environ.get('DEFAULT_THEME')
else:
    raise ValueError(
        f'Provided DEFAULT_THEME value {os.environ.get('DEFAULT_THEME')} is not valid. '
        f'Valid values are: {", ".join(themes)}.'
    )

if not os.environ.get('DEFAULT_THEME_COLOR'):
    DEFAULT_THEME_COLOR = 'Green'
elif os.environ.get('DEFAULT_THEME_COLOR') in theme_colors:
    # tailwind css expects a leading capitalized letter, see pdfding/static/css/tailwind.css.
    DEFAULT_THEME_COLOR = os.environ.get('DEFAULT_THEME_COLOR').capitalize()
else:
    raise ValueError(
        f'Provided DEFAULT_THEME_COLOR value {os.environ.get('DEFAULT_THEME_COLOR')} is not valid. '
        f'Valid values are: {", ".join(theme_colors)}.'
    )

# Allow subdirectories when saving PDFs to the media dir in the UI
if os.environ.get('ALLOW_PDF_SUB_DIRECTORIES', 'FALSE') == 'TRUE':
    ALLOW_PDF_SUB_DIRECTORIES = True
else:
    ALLOW_PDF_SUB_DIRECTORIES = False

# demo mode
if os.environ.get('DEMO_MODE', 'FALSE') == 'TRUE':
    DEMO_MODE = True
    DEMO_MODE_RESTART_INTERVAL = int(os.environ.get('DEMO_MODE_RESTART_INTERVAL', 60))  # in minutes
    DEMO_MAX_USERS = int(os.environ.get('DEMO_MAX_USERS', 500))
else:
    DEMO_MODE = False
