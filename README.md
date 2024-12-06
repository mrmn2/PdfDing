# PdfDing

## Overview

- [Introduction](#introduction)
- [Installation](#installation)
  - [Using Docker](#using-docker)
  - [Using Docker Compose](#using-docker-compose)
  - [Admin User](#admin-user)
  - [SSO](#single-sign-on-sso)
  - [Backups](#backups)
- [Configuration](#configuration)
- [Tech Stack](#tech-stack)
- [Acknowledgements](#acknowledements)
- [Contributing](#contributing)

## Introduction

PdfDing is a PDF manager and viewer that you can host yourself. It offers a seamless user experience on multiple
devices. It's designed be to be minimal, fast, and easy to set up using Docker. As all data stays on your server
you have full control over your data and privacy.

With its simple, intuitive and adjustable UI, PdfDing makes it easy for users to keep track of their PDFs
and access them whenever they need to. With a dark mode and colored themes users can style the app to
their liking. As PdfDing offers SSO support via OIDC it can be easily integrated into existing setups.

The name is a combination of PDF and *ding*. Ding is the German word for thing. Thus, PdfDing is a thing for
your PDFs. The name and the design of PdfDing are inspired by [linkding](https://github.com/sissbruecker/linkding).
Linkding is an excellent selfhostable bookmark manager. If you are unfamiliar with it be sure to check it out!

### Feature Overview
* Seamless browser based PDF viewing on multiple devices
* Organize PDFs with tags
* Clean and responsive UI
* Dark Mode, colored themes and custom theme colors
* Inverted color mode for reading PDFs
* Remembers current position - continue where you stopped reading
* SSO support via OIDC
* Share PDFs with an external audience via a link or a QR Code
* Shared PDFs can be password protected and access can be controlled with a maximum number of views and an expiration date
* Automated and encrypted backups to S3 compatible storage
* PDF bulk upload
* Every user can upload its own PDFs. There is no admin curating the content.
* Simple Admin area for user management

### Screenshots
![](https://github.com/mrmn2/PdfDing-Screenshots/blob/master/screenshots/pdf_overview_dark_green.png)

More screenshots can be found [here](https://github.com/mrmn2/PdfDing/blob/master/docs/screenshots.md).

### Why PdfDing?
I started developing PdfDing as I was searching for a solution for viewing and managing PDF files.
I had a few simple requirements:

* view PDFs seamlessly in the browser of my desktop and mobile devices
* every user can upload files
* can be self-hosted via Docker
* minimal and resource-friendly
* SSO support

I was quite surprised to find out that there was no app matching my simple requirements. While there
were some existing solutions they still had some problems:

* They are using the inbuilt PDF viewer of the browser. This works fine on desktops and laptops but on smartphones
  it will simply download the PDF file and not display it in the browser.
* They are really feature rich and therefore resource-hungry. I do not need fancy AI or OCR. I just want
  to view and organize my PDFs.
* The content needs to be curated by an admin user. Normal users are not allowed to add PDFs.
* PDFs can not be uploaded via the UI.

Thus, I am developing PDfDing as a simple webapp with a clear focus on a single thing: viewing and managing PDFs.

## Installation
PdfDing is designed to be run with container solutions like Docker. The Docker image is compatible with ARM64 platforms,
so it can be run on a Raspberry Pi 4.

PdfDing uses an SQLite database by default. Alternatively PdfDing supports PostgreSQL.

### Using Docker

To install PdfDing using Docker you can just run the image from [Docker Hub](https://hub.docker.com/r/mrmn/pdfding):

```
docker run --name pdfding \
    -p 8000:8000 \
    -v sqlite_data:/home/nonroot/pdfding/db -v media:/home/nonroot/pdfding/media \
    -e HOST_NAME=127.0.0.1 -e SECRET_KEY=some_secret -e CSRF_COOKIE_SECURE=FALSE -e SESSION_COOKIE_SECURE=FALSE \
    -d \
    mrmn/pdfding:latest
```

If everything completed successfully, the application should now be running
and can be accessed at http://127.0.0.1:8000.

If you use selinux it might be necessary to add the `:Z` after the volumes, e.g.
`sqlite_data:/home/nonroot/pdfding/db:Z`.

### Using Docker Compose
To install linkding using Docker Compose, you can use one of the files in the
[deploy](https://github.com/mrmn2/PdfDing/tree/master/deploy) directory and run e.g.:

```
docker-compose -d -f sqlite.docker-compose.yaml
```

### Admin user
If needed or wished it is possible to create an admin user. Admin users can view and delete users.
Creating an admin user is optional. To give a user admin rights execute
```
python pdfding/manage.py make_admin -e admin@pdfding.com
```
inside the shell of the running container and specify the correct email address.
Admin users can can also give other users admin rights via the ui.

### Single Sign on (SSO)
PdfDing supports SSO via OIDC. OIDC is set up by using environment variables:
```
OIDC_ENABLE: "TRUE"
OIDC_CLIENT_ID: "pdfding"
OIDC_CLIENT_SECRET: "client_secret"
OIDC_AUTH_URL: "https://auth.pdfding.com/.well-known/openid-configuration"
OIDC_PROVIDER_NAME: "Authelia"
```

More information about the environment variables can be found in the [Configuration](#configuration) section.

Once PdfDing is set up for using OIDC the same needs to be done on the OIDC identity provider's side. Of course, this
configuration depends on the used identity provider. Here is an example configuration
for [Authelia](https://www.authelia.com/):
```
oidc:
    ## The other portions of the mandatory OpenID Connect 1.0 configuration go here.
    ## See: https://www.authelia.com/c/oidc
    clients:
      - id: pdfding
            description: PdfDing
            # create client secret and hash with
            # docker run --rm authelia/authelia:latest authelia crypto rand --length 64 --charset alphanumeric
            secret: '$pbkdf2-sha512$310000$<rest_of_hashed_secret>'
            public: false
            authorization_policy: two_factor
            scopes:
              - openid
              - email
              - profile
            redirect_uris:
              - https://pdfding.com/accountoidc/login/callback/
```

## Backups

PdfDing supports automated backups to S3 compatible storage. During backups the Sqlite database and uploaded
PDF files will be backed up.

**IMPORTANT**: The backup of Postgres databases is as of now not supported. Postgres databases should be
backed up by using `pg_dump`.

### Enabling Backups
Backups are set up by using environment variables:
```
BACKUP_ENABLE: "TRUE"
BACKUP_SCHEDULE: "0 2 * * *"
BACKUP_ENDPOINT: 'minio.pdfding.com'
BACKUP_ACCESS_KEY: 'some_access_key'
BACKUP_SECRET_KEY: 'some_secret_key'
BACKUP_SECURE: 'FALSE'
```

More information about the environment variables can be found in the [Configuration](#configuration) section.

### Enabling Encrypted Backups
PDfDing supports encrypted backups. Encryption is done via Fernet, a symmetric encryption algorithm
provided by the [cryptography](https://cryptography.io/en/stable/fernet/#cryptography.fernet.Fernet)
library. Encrypted backups can be enabled by using environment variables:
```
BACKUP_ENCRYPTION_ENABLED: "TRUE"
BACKUP_ENCRYPTION_PASSWORD: 'some_password'
BACKUP_ENCRYPTION_SALT: 'some_salt'
```

**IMPORTANT: If you enable encrypted backups or change the encryption password/salt, it is absolutely necessary
to delete your existing backups in the S3 compatible storage. Not doing so will destroy your backup!**

### Recovering Data from Backups

PDFs and the Sqlite database can easily be recovered from the backups by executing
```
python pdfding/manage.py recover_data
```
inside the shell of the running container.

## Configuration
### `DEFAULT_THEME`
Values: `light`, `dark` | Default `light`

Specify the default theme.

### `DEFAULT_THEME_COLOR`
Values: `green`, `blue`, `gray`, `red`, `pink`, `orange` | Default `green`

Specify the default theme color.

### `SECRET_KEY`
Values: `string` | Default = `None`

This value is the key to securing signed data. Should be to a large random value! Example: `some_secret`

### `HOST_NAME`
Values: `string` | Default = `None`

The host/domain name where PdfDing will be reachable. Example: `pdfding.com`

### `HOST_PORT`
Values: `integer` | Default: `8000`

Allows to set a custom port for the PdfDing server.

### `DATABASE_TYPE`
Values: `SQLITE`, `POSTGRES` | Default `POSTGRES`

Specify which database type should be used.

### `POSTGRES_HOST`
Values: `string` | Default = `postgres`

The host of the postgres DB: Example: `postgres.pdfding.com`

### `POSTGRES_PASSWORD`
Values: `string` | Default = `None`

The password for the postgres DB: Example: `password`

### `POSTGRES_PORT`
Values: `integer` | Default: `5432`

The port of the postgres DB.

### `ACCOUNT_EMAIL_VERIFICATION`
Values: `TRUE`, `FALSE` | Default: `TRUE`

Block users until they have verified their email address.

### `DISABLE_USER_SIGNUP`
Values: `TRUE`, `FALSE` | Default: `FALSE`

Flag for disabling user signup. By setting this value to `TRUE` user signup will be disabled.

### `OIDC_ENABLE`
Values: `TRUE`, `FALSE` | Default: `FALSE`

Flag for enabling SSO via OIDC. By setting this value to `TRUE` OIDC will be activated.

### `OIDC_CLIENT_ID`
Values: `string` | Default = `None`

PdfDing's OIDC client id. Example: `pdfding`

### `OIDC_CLIENT_SECRET`
Values: `string` | Default = `None`

PdfDing's OIDC client secret. Should be a large random value! Example: `another_long_secret`

### `OIDC_AUTH_URL`
Values: `string` | Default = `None`

The URL to the OpenID configuration of the auth server. Example:
`https://auth.pdfding.com/.well-known/openid-configuration`

### `OIDC_ONLY`
Values: `TRUE`, `FALSE` | Default: `TRUE`

By setting this to `TRUE` users will only be able to authenticate using OIDC.

### `OIDC_PROVIDER_NAME`
Values: `string` | Default = `OIDC`

The name of the OIDC provider. The name will be displayed on the login screen as `OIDC_LOG IN VIA <PROVIDER_NAME>`.
Example: `Authelia`

### `CSRF_COOKIE_SECURE`
Values: `TRUE`, `FALSE` | Default: `TRUE`

Set this to True to avoid transmitting the CSRF cookie over HTTP accidentally.

### `SESSION_COOKIE_SECURE`
Values: `TRUE`, `FALSE` | Default: `TRUE`

Set this to True to avoid transmitting the session cookie over HTTP accidentally.

### `SECURE_SSL_REDIRECT`
Values: `FALSE`, `TRUE` | Default: `FALSE`

Redirects all non-HTTPS requests to HTTPS. If PdfDing is running behind a reverse proxy this can cause infinite
redirects.

### `SECURE_HSTS_SECONDS`
Values: `integer` | Default: `None`

For sites that should only be accessed over HTTPS, you can instruct modern browsers to refuse to connect to your domain
name via an insecure connection (for a given period of time) by setting the “Strict-Transport-Security” header.
`SECURE_HSTS_SECONDS` will set this header for you on all HTTPS responses for the specified number of seconds. Test this
with a small value first. If everything works it can be set to a large value, e.g. `31536000` (1 year) , in order to
protect infrequent visitors.

### `ACCOUNT_DEFAULT_HTTP_PROTOCOL`
Values: `https`, `http` | Default: `https`

The default protocol for account related URLs, e.g. for the password forgotten procedure.

### `EMAIL_BACKEND `
Values: `CONSOLE`, `SMTP` | Default: `CONSOLE`

Whether to send account related emails, e.g a password reset or account verification, to the console or via an SMTP
server.

### `SMTP_HOST`
Values: `string` | Default = `None`

The host/domain name of the SMTP server. Example: `pdfding.com`

### `SMTP_PORT`
Values: `integer` | Default: `587`

The port of the SMTP server.

### `SMTP_USER`
Values: `string` | Default = `None`

The username used for logging into the SMTP server.

### `SMTP_PASSWORD`
Values: `string` | Default = `None`

The password used for logging into the SMTP server.

### `SMTP_USE_TLS`
Values: `FALSE`, `TRUE` | Default: `FALSE`

Secure the connection to the SMTP server with TLS. Some SMTP servers support only one kind and
some support both. Note that `SMTP_USE_TLS`/`SMTP_USE_SSL` are mutually exclusive.

### `EMAIL_USE_SSL`
Values: `FALSE`, `TRUE` | Default: `FALSE`

Secure the connection to the SMTP server with SSL. Some SMTP servers support only one kind and
some support both. Note that `SMTP_USE_TLS`/`SMTP_USE_SSL` are mutually exclusive.

### `BACKUP_ENABLE`
Values: `TRUE`, `FALSE` | Default: `FALSE`

Flag for enabling periodic backups to S3 compatible storage. By setting this value to `TRUE`
periodic backups will be activated.

### `BACKUP_ENDPOINT`
Values: `string` | Default: `None`

The endpoint of the S3 compatible storage. Example: `minio.pdfding.com`

### `BACKUP_ACCESS_KEY`
Values: `string` | Default: `None`

The access key of the S3 compatible storage. Example: `random_access_key`

### `BACKUP_SECRET_KEY`
Values: `string` | Default: `None`

The secret key of the S3 compatible storage. Example: `random_secret_key`

### `BACKUP_BUCKET_NAME`
Values: `string` | Default: `pdfding`

The name of the bucket where PdfDing should be backed up to. Example: `pdfding`

### `BACKUP_SCHEDULE`
Values: `string` | Default: `0 2 * * *`

The schedule for the periodic backups. Example: `0 2 * * *`. This schedule will start the backup
every night at 2:00. More information can be found [here](https://crontab.guru/#0_2_*_*_*).

### `BACKUP_SECURE`
Values: `TRUE`, `FALSE` | Default: `FALSE`

Flag to indicate to use secure (TLS) connection to S3 service or not.

### `BACKUP_ENCRYPTION_ENABLE`
Values: `TRUE`, `FALSE` | Default: `FALSE`

Flag to enable encrypted backups.

**IMPORTANT: If you enable encrypted backups or change the encryption password/salt, it is absolutely necessary
to delete your existing backups in the S3 compatible storage. Not doing so will destroy your backup!**

### `BACKUP_ENCRYPTION_PASSWORD`
Values: `string` | Default: `None`

Password used for generating the encryption key. The encryption key generation is done via PBKDF2
with 1000000 iterations.

Should be to a large random value! Example: `some_secret`

### `BACKUP_ENCRYPTION_SALT`
Values: `string` | Default: `pdfding`

Salt used for generating the encryption key. Example: `some_salt`


## Tech Stack
* The web app is build using the Python web framework [Django](https://www.djangoproject.com/)
* Mozilla's [PDF.js](https://mozilla.github.io/pdf.js/) is used for viewing PDF files in the browser
* The frondend is build using [Alpine.js](https://alpinejs.dev/), [htmx](https://htmx.org/),
[jQuery](https://jquery.com/) and [Tailwind CSS](https://tailwindcss.com/)
* Authentication, registration, account management and OIDC is achieved by [django-allauth](https://docs.allauth.org/en/latest/)

## Acknowledements
* This project started by adjusting the django starter of Andreas Jud: [django-starter](https://github.com/andyjud/django-starter), [django-starter-assets](https://github.com/andyjud/django-starter-assets)
* As mentioned above, inspired by [linkding](https://github.com/sissbruecker/linkding).

## Contributing
PdfDing is open source, so you are free to modify or contribute. PdfDing is built using the Django web framework. You
can get started by checking out the excellent [Django docs](https://docs.djangoproject.com/en/stable/). Currently,
PdfDing consists of four applications:
* Inside the `pdf` folder is the one related to managing and viewing PDFs
* the folder `users` contains the logic related to users
* the admin area is implemented inside the `admin` folder
* `core` is the Django root application
* backups are handled inside `backup`

Other than that the code should be self-explanatory / standard Django stuff 🙂.

### Prerequisites

* Python 3
* pipx
* Poetry: `pipx install poetry`
* Node.js

### Pre-Commit
This project has support for `pre-commit` hooks. They are used for checking the code quality,
e.g. with: `black`, `flake8` and `bandit`. If `pre-commit` is installed on your system just run
```
pre-commit install
```
Now whenever you commit your changes the pre-commit hooks will be triggered. If you want to bypass
`pre-commit` for some reason just add `--no-verify` to your commit command, e.g.:
```
git commit -m 'some commit message' --no-verify
```


### Setup

Clone the repository:
```
git clone https://github.com/mrmn2/PdfDing.git
```

cd into the project:
```
cd PdfDing
```

Create the virtual environment and install all dependencies:
```
poetry install
```

Activate the environment for your shell:
```
poetry shell
```

Install frontend dependencies:
```
mkdir ./js && mkdir ./css
npm ci
npm run build
```

Initialize the database:
```
python pdfding/manage.py migrate
```

Create a user for the frontend:
```
python pdfding/manage.py createsuperuser
```

Start the development server with:

```
# in one shell run
python pdfding/manage.py runserver
# in another run
npx tailwindcss -i pdfding/static/css/input.css -o pdfding/static/css/tailwind.css -c tailwind.config.js --watch
```
The frontend is now available under http://127.0.0.1:8000. Any changes in regard to Tailwind CSS will be automatically
reflected.

### Testing

Run all tests with:
```
pytest
```
It's also possible to run unit tests and e2e tests separately. Unit tests can be run with:
```
pytest pdfding/admin pdfding/pdf pdfding/users --cov=pdfding/admin --cov=pdfding/pdf --cov=pdfding/users
```
E2e tests with
```
pytest pdfding/e2e
```

### Code Quality
Formatting is done via `black`:
```
black .
```

Further code quality checks are done via `flake8`:
```
flake8
```
