from os import environ

from django.contrib.auth.hashers import check_password

from .base import *  # noqa: F401 F403

try:
    from .version import VERSION  # pyright: ignore
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
ALLOWED_HOSTS = environ.get('HOST_NAME', '').split(',')
ALLOWED_HOSTS = [allowed_host.strip() for allowed_host in ALLOWED_HOSTS if allowed_host != '']

if ALLOWED_HOSTS:
    CSRF_TRUSTED_ORIGINS = []
    for allowed_host in ALLOWED_HOSTS:
        CSRF_TRUSTED_ORIGINS.extend([f'https://{allowed_host}', f'http://{allowed_host}'])

SECRET_KEY = environ.get('SECRET_KEY')

if environ.get('CSRF_COOKIE_SECURE', 'TRUE') == 'TRUE':
    CSRF_COOKIE_SECURE = True
if environ.get('SESSION_COOKIE_SECURE', 'TRUE') == 'TRUE':
    SESSION_COOKIE_SECURE = True
if environ.get('SECURE_SSL_REDIRECT') == 'TRUE':
    SECURE_SSL_REDIRECT = True
if environ.get('SECURE_HSTS_SECONDS'):
    SECURE_HSTS_SECONDS = environ.get('SECURE_HSTS_SECONDS')

# backup settings
if environ.get('BACKUP_ENABLE') == 'TRUE':
    # without a dummy value, huey will not start
    BACKUP_ENABLED = True
    BACKUP_ENDPOINT = environ.get('BACKUP_ENDPOINT', 'minio.pdfding.com')
    BACKUP_ACCESS_KEY = environ.get('BACKUP_ACCESS_KEY')
    BACKUP_SECRET_KEY = environ.get('BACKUP_SECRET_KEY')
    BACKUP_BUCKET_NAME = environ.get('BACKUP_BUCKET_NAME', 'pdfding')
    BACKUP_SCHEDULE = environ.get('BACKUP_SCHEDULE', '0 2 * * *')
    if environ.get('BACKUP_SECURE') == 'TRUE':
        BACKUP_SECURE = True
    else:
        BACKUP_SECURE = False

    if environ.get('BACKUP_ENCRYPTION_ENABLE') == 'TRUE':
        BACKUP_ENCRYPTION_ENABLED = True
        BACKUP_ENCRYPTION_PASSWORD = environ['BACKUP_ENCRYPTION_PASSWORD']
        BACKUP_ENCRYPTION_SALT = environ.get('BACKUP_ENCRYPTION_SALT', 'pdfding')
    else:
        BACKUP_ENCRYPTION_ENABLED = False
        # set to none, so that backups.tasks.backup_function raises no attribute error
        BACKUP_ENCRYPTION_PASSWORD = None
        BACKUP_ENCRYPTION_SALT = None
else:
    BACKUP_ENABLED = False
    BACKUP_SCHEDULE = '*/1 * * * *'

# consume settings
if environ.get('CONSUME_ENABLE') == 'TRUE':
    CONSUME_ENABLED = True
    CONSUME_TAG_STRING = environ.get('CONSUME_TAGS', '')
    CONSUME_SCHEDULE = environ.get('CONSUME_SCHEDULE', '*/5 * * * *')
    if environ.get('CONSUME_SKIP_EXISTING') == 'FALSE':
        CONSUME_SKIP_EXISTING = False
    else:
        CONSUME_SKIP_EXISTING = True
else:
    CONSUME_ENABLED = False
    CONSUME_SKIP_EXISTING = False
    CONSUME_SCHEDULE = '*/5 * * * *'

# mail settings
if environ.get('EMAIL_BACKEND') == 'SMTP':
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = environ.get('SMTP_HOST')
    EMAIL_PORT = environ.get('SMTP_PORT', 587)
    EMAIL_HOST_USER = environ.get('SMTP_USER')
    EMAIL_HOST_PASSWORD = environ.get('SMTP_PASSWORD')
    if environ.get('SMTP_USE_TLS') == 'TRUE':
        EMAIL_USE_TLS = True
    if environ.get('SMTP_USE_SSL') == 'TRUE':
        EMAIL_USE_SSL = True

if environ.get('EMAIL_ADDRESS'):
    DEFAULT_FROM_EMAIL = environ.get('EMAIL_ADDRESS')
else:
    try:
        DEFAULT_FROM_EMAIL = f'info@{ALLOWED_HOSTS[0]}'
    except IndexError:
        DEFAULT_FROM_EMAIL = 'info@pdfding'

# authentication settings
ACCOUNT_DEFAULT_HTTP_PROTOCOL = environ.get('ACCOUNT_DEFAULT_HTTP_PROTOCOL', 'https')
if environ.get('ACCOUNT_EMAIL_VERIFICATION') == 'TRUE':
    ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
else:
    ACCOUNT_EMAIL_VERIFICATION = 'optional'

if environ.get('DISABLE_USER_SIGNUP') == 'TRUE':
    SIGNUP_CLOSED = True
else:
    SIGNUP_CLOSED = False

# configure the oidc provider
if environ.get('OIDC_ENABLE') == 'TRUE':
    # enable social logins only
    if environ.get('OIDC_ONLY') == 'TRUE':
        SOCIALACCOUNT_ONLY = True
        ACCOUNT_EMAIL_VERIFICATION = 'none'

    OIDC_GROUPS_CLAIM = environ.get('OIDC_GROUPS_CLAIM', 'groups')
    OIDC_ADMIN_GROUP = environ.get('OIDC_ADMIN_GROUP', '')
    OIDC_EXTRA_SCOPE = environ.get('OIDC_EXTRA_SCOPE', '')
    OIDC_SCOPE = ['openid', 'profile', 'email']
    if OIDC_EXTRA_SCOPE and OIDC_EXTRA_SCOPE not in OIDC_SCOPE:
        OIDC_SCOPE.append(OIDC_EXTRA_SCOPE)

    SOCIALACCOUNT_PROVIDERS = {
        'openid_connect': {
            'EMAIL_AUTHENTICATION': True,
            # Optional PKCE defaults to False, but may be required by your provider
            # Applies to all APPS.
            'OAUTH_PKCE_ENABLED': True,
            'APPS': [
                {
                    'provider_id': 'oidc',
                    'name': environ.get('OIDC_PROVIDER_NAME', 'OIDC').upper(),
                    'client_id': environ['OIDC_CLIENT_ID'],
                    'secret': environ['OIDC_CLIENT_SECRET'],
                    'settings': {
                        'server_url': environ['OIDC_AUTH_URL'],
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
themes = ['light', 'dark', 'creme', 'system']

if not environ.get('DEFAULT_THEME'):
    DEFAULT_THEME = 'system'
elif environ.get('DEFAULT_THEME') in themes:
    DEFAULT_THEME = environ.get('DEFAULT_THEME')
else:
    raise ValueError(
        f'Provided DEFAULT_THEME value {environ.get('DEFAULT_THEME')} is not valid. '
        f'Valid values are: {", ".join(themes)}.'
    )

if not environ.get('DEFAULT_THEME_COLOR'):
    DEFAULT_THEME_COLOR = 'Green'
elif environ.get('DEFAULT_THEME_COLOR') in theme_colors:
    # tailwind css expects a leading capitalized letter, see pdfding/static/css/tailwind.css.
    DEFAULT_THEME_COLOR = environ.get('DEFAULT_THEME_COLOR', '').capitalize()
else:
    raise ValueError(
        f'Provided DEFAULT_THEME_COLOR value {environ.get('DEFAULT_THEME_COLOR')} is not valid. '
        f'Valid values are: {", ".join(theme_colors)}.'
    )

# Allow subdirectories when saving PDFs to the media dir in the UI
if environ.get('ALLOW_PDF_SUB_DIRECTORIES', 'FALSE') == 'TRUE':
    ALLOW_PDF_SUB_DIRECTORIES = True
else:
    ALLOW_PDF_SUB_DIRECTORIES = False

# supporter edition settings
SUPPORTER_KEY_HASH = 'pbkdf2_sha256$1000000$supporter$ZHnPv0AcYm6ZV5Pcyw8ULh3C1Dd5EGD2XG49gWpeTns='
SUPPORTER_KEY = environ.get('SUPPORTER_KEY', '')

if check_password(SUPPORTER_KEY, SUPPORTER_KEY_HASH):
    SUPPORTER_EDITION = True
else:
    SUPPORTER_EDITION = False

# demo mode
if environ.get('DEMO_MODE', 'FALSE') == 'TRUE':
    DEMO_MODE = True
    DEMO_MODE_RESTART_INTERVAL = int(environ.get('DEMO_MODE_RESTART_INTERVAL', 60))  # in minutes
    DEMO_MAX_USERS = int(environ.get('DEMO_MAX_USERS', 500))
else:
    DEMO_MODE = False
