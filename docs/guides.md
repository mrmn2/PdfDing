## Overview
- [SSO via OIDC](#sso-via-oidc)
- [Tags](#tags)
- [Editing](#editing)
- [Admin Users](#admin-users)
- [Consumption Directory](#consumption-directory)
- [Backups](#backups)

## SSO via OIDC
PdfDing supports SSO via OIDC. OIDC is set up by using environment variables. An example OIDC
configuration on PdfDings site can look like this:

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

## Tags
PdfDing uses tags for organizing Pdf files. Tags are displayed on the right hand side of the PDF
overview. Users have the option to display them hierarchically via `tree mode` or simple via `normal mode`. This
can be set up in the user's settings.

### Examples
Here are some examples of tags for a better understanding.
* `#hobbies` This is the simplest form of a tag and is used to categorize PDFs related to hobbies.
* `#programming/python` Multi-level tags are supported. It helps you organize PDFs about Python programming
  under the "programming" category. Note that tree mode needs to activated for a visual representation of
  hierarchical tags

### Renaming and Deleting tags
* Find the Tags section on the right sidebar.
* Hover over the # sign next to the tag, it will change to ⁝.
* Click on the menu button and then choose "Rename" or "Delete".

## Editing
PdfDing supports editing PDFs inside the PDF Viewer. Users can add annotations, highlighting and drawings
to PDFs.

### Usage
To start editing simply press one of the corresponding buttons on the right side of the navigation
bar. When the PDF was changed, the character `*` is placed before the PDF name in the site title as an visual
indicator. Once finished, press the save button to save the changes to PdfDing.

### Considerations
* Currently, everytime a user presses save, the whole file gets send to the backend. Thus, it might be better
  not to spam the save button, when editing bigger files.
* Rarely, on some browsers reopening the PDF will not show the newest changes after saving and closing the edited
  PDF. The changes are still saved to the backend, which can be verified by opening the page in a private Window
  or downloading it.

## Admin Users
If needed or wished it is possible to create an admin user. Admin users can view and delete users.
Creating an admin user is optional. To give a user admin rights execute
```
python pdfding/manage.py make_admin -e admin@pdfding.com
```
inside the shell of the running container and specify the correct email address.
Admin users can can also give other users admin rights via the ui.

## Consumption Directory
As an alternative to the UI based approach PDF files can be added to PdfDing by putting them into the
consumption directory of the running container. This feature is not activated by default and must be configured
via environment variables.

As PdfDing is created with multiple users in mind, each user has its own subfolder for adding PDF files.
The path of these subfolders is: `/home/nonroot/pdfding/consume/<user_id>`. `<user_id>` needs to be replaced with
the ID of the respective user. The user ID can be found in the dropdown menu that gets opened by clicking
on the user icon in the header. The subfolders are not created automatically and need to be created by the
administrator (e.g.: via the shell or docker volumes). The administrator might also want to make the consumption
directory persistent, for example via docker volumes.

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
