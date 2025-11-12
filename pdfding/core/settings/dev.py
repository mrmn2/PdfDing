from .base import *  # noqa: F401 F403

try:
    # set the minio acces and secret key and the SOCIALACCOUNT_PROVIDERS in dev_secrets
    from .dev_secrets import *  # noqa: F401 F403
except ModuleNotFoundError:  # pragma: no cover
    # dummy SOCIALACCOUNT_PROVIDERS for tests
    SOCIALACCOUNT_PROVIDERS = {
        "openid_connect": {
            'EMAIL_AUTHENTICATION': True,
            "OAUTH_PKCE_ENABLED": True,
            "APPS": [
                {
                    "provider_id": "oidc",
                    'name': 'OIDC',
                    "client_id": "dummy_id",
                    "secret": "dummy_secret",
                    "settings": {
                        "server_url": "dummy_url",
                    },
                }
            ],
        }
    }

# Turn on debug mode
DEBUG = True
VERSION = 'DEV'

INTERNAL_IPS = ['127.0.0.1']

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'some_key'  # nosec B105

SUPPORTER_EDITION = True

ACCOUNT_EMAIL_VERIFICATION = 'optional'

DEFAULT_FROM_EMAIL = 'info@localhost'
SIGNUP_CLOSED = False

OIDC_GROUPS_CLAIM = 'groups'
OIDC_ADMIN_GROUP = 'admins'

BACKUP_ENABLED = True
BACKUP_SECURE = False
BACKUP_ENDPOINT = '127.0.0.1:9000'
BACKUP_BUCKET_NAME = 'pdfding'
BACKUP_SCHEDULE = '*/1 * * * *'
BACKUP_ENCRYPTION_ENABLED = True
BACKUP_ENCRYPTION_SALT = 'pdfding'

CONSUME_ENABLED = True
CONSUME_TAG_STRING = 'consumed file'
CONSUME_SKIP_EXISTING = True

ALLOW_PDF_SUB_DIRECTORIES = True

# check if minio access and secret keys are set in dev_secrets
if 'BACKUP_ACCESS_KEY' not in locals():
    BACKUP_ACCESS_KEY = 'add_access_key'
if 'BACKUP_SECRET_KEY' not in locals():
    BACKUP_SECRET_KEY = 'add_secret_key'  # nosec

# check if backup encryption password is set in dev_secrets
if 'BACKUP_ENCRYPTION_PASSWORD' not in locals():
    BACKUP_ENCRYPTION_PASSWORD = 'password'  # nosec

# themes
DEFAULT_THEME = 'dark'
DEFAULT_THEME_COLOR = 'Green'

# demo mode
DEMO_MODE = False
DEMO_MAX_USERS = 10
DEMO_MODE_RESTART_INTERVAL = 60
