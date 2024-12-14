# Configuration
This page lists PdfDing's configuration options and provides additional information about each setting. Each
configuration option is set via environment variables.

## Overview
- [General](#general)
- [Security Related](#security-related)
- [Databases](#databases)
- [Admin Users](#admin-users)
- [SSO via OIDC](#sso-via-oidc)
- [Emails](#emails)
- [Customization](#customization)
- [Backups](#backups)

## General
By using the following environment variables the admin can control general settings of his PdfDing instance.

### `HOST_NAME`
Values: `string` | Default = `None`

The host/domain name where PdfDing will be reachable. Example: `pdfding.com`

### `HOST_PORT`
Values: `integer` | Default: `8000`

Allows to set a custom port for the PdfDing server.

### `LOG_LEVEL`
Values: `DEBUG`, `INFO`, `WARNING`, `ERROR` | Default: `ERROR`

Set the log level.

### `ACCOUNT_EMAIL_VERIFICATION`
Values: `TRUE`, `FALSE` | Default: `TRUE`

Block users until they have verified their email address.

### `DISABLE_USER_SIGNUP`
Values: `TRUE`, `FALSE` | Default: `FALSE`

Flag for disabling user signup. By setting this value to `TRUE` user signup will be disabled.

## Security Related
By using the following environment variables different security related settings can be adjusted.

### `SECRET_KEY`
Values: `string` | Default = `None`

This value is the key to securing signed data. Should be to a large random value! Example: `some_secret`

### `CSRF_COOKIE_SECURE`
Values: `TRUE`, `FALSE` | Default: `TRUE`

Set this to `TRUE` to avoid transmitting the CSRF cookie over HTTP accidentally.

### `SESSION_COOKIE_SECURE`
Values: `TRUE`, `FALSE` | Default: `TRUE`

Set this to `TRUE` to avoid transmitting the session cookie over HTTP accidentally.

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

## Databases
Specifies the used database type and related settings.

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

## Admin Users
If needed or wished it is possible to create an admin user. Admin users can view and delete users.
Creating an admin user is optional. To give a user admin rights execute
```
python pdfding/manage.py make_admin -e admin@pdfding.com
```
inside the shell of the running container and specify the correct email address.
Admin users can can also give other users admin rights via the ui.

## SSO via OIDC
PdfDing supports SSO via OIDC. OIDC is set up by using the following environment variables.
An example can be found at the of this section.

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


### Example configuration
An example OIDC configuration on PdfDings site can look like this:

```
OIDC_ENABLE: "TRUE"
OIDC_CLIENT_ID: "pdfding"
OIDC_CLIENT_SECRET: "client_secret"
OIDC_AUTH_URL: "https://auth.pdfding.com/.well-known/openid-configuration"
OIDC_PROVIDER_NAME: "Authelia"
```

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

## Emails
PdfDing sends emails for account related operations, e.g. creating an account or changing the email address. The
settings are controlled by the following environment variables.

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

## Customization
By using these options the admin can control the looks of PdfDing for not logged in visitors of their PdfDing
instance (login page, signup page, etc ...). This will also set the theme of newly signed-up users.

### `DEFAULT_THEME`
Values: `light`, `dark` | Default `light`

Specify the default theme.

### `DEFAULT_THEME_COLOR`
Values: `green`, `blue`, `gray`, `red`, `pink`, `orange` | Default `green`

Specify the default theme color.

## Backups
PdfDing supports automated backups to S3 compatible storage. During backups the Sqlite database and uploaded
PDF files will be backed up. PDfDing supports encrypted backups. Encryption is done via Fernet, a
symmetric encryption algorithm provided by the [cryptography](https://cryptography.io/en/stable/fernet/#cryptography.fernet.Fernet) library.

The backup of Postgres databases is as of now not supported. Postgres databases should be
backed up by using `pg_dump`.

**IMPORTANT: If you enable encrypted backups or change the encryption password/salt, it is absolutely necessary
to delete your existing backups in the S3 compatible storage. Not doing so will destroy your backup!**

### Recovering Data from Backups
PDFs and the Sqlite database can easily be recovered from the backups by executing
```
python pdfding/manage.py recover_data
```
inside the shell of the running container.

### Environment Variables
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
