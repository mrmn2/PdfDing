# Changelog
<hr>

## 0.6.1 - Fix settings (Dec 07, 2024)
* Fix: Use prod settings file
* Fix: Set correct overview queries after renaming or deleting tag
* Update django to address vulnarabilities

## YANKED! 0.6.0 - Overview improvements (Dec 06, 2024)
Migrating from woodpecker CI to gh actions resulted in a faulty publish pipeline.
The publish workflow did not use the .dockerignore file which caused the dev settings to be used.

* Searches and applied tags are now displayed as filters. Closing the filter will
  remove the respective search / tag from the filtering.
* Optional progress bars show the reading process for each PDF
  at a quick glance on the overview
* Tags can be renamed and deleted
* Add option to skip existing files when bulk uploading
* Add date tooltips to admin overview
* Add environment variable for setting the log level

## 0.5.0 - Inverted Color Mode and Bulk Upload  (Nov 23, 2024)
* Inverted color mode for reading PDFs
* Bulk uploading for PDFs
* Use file name when uploading individual PDFs
* Add date tooltips in the PDF and shared PDF overviews
* Add loading spinners to PDF uploads
* Clean up shared PDFs with a deletion date in the past on container start
* Bug Fix: Backup QR code svgs

## 0.4.2 - Bug Fixes and Small Features  (Nov 10, 2024)
* Bug Fix: Adjust base.html, so that x-cloak of Alpine JS  works on all themes.
           Did only work on custom theme colors after introducing that feature.
* Bug Fix: Adjust 404.html so that it hsa correct font colors in dark mode
* Sort PDFs by recently viewed
* Disable user signup via the env variable `DISABLE_USER_SIGNUP`
* Add about page
* Add footer
* Only execute backups if at least 1 user and 1 pdf present

## 0.4.1 - Custom Theme Colors and Default Themes  (Nov 07, 2024)
* Add functionality to use custom theme colors
* Set the default theme via env variables

## 0.4.0 - Shared PDFs  (Oct 24, 2024)
* Add functionality to share PDFs with an external audience via a link or a QR Code
* Shared PDFs can be password protected and access can be controlled with a maximum number of views and an expiration date
* Update dependencies

## 0.3.4 - Encrypted Backups to S3 Compatible Storage  (Aug 27, 2024)

* Add option to encrypt the PDFs and the Sqlite database when performing backups
* Bug Fix: Setting the Postgres host to something different from `postgres` was not possible beforehand

## 0.3.3 - Revamp tag sidebar, new version available and further image size reduction (Aug 17, 2024)

* Revamp the tag sidebar section, so that tags will be grouped by their starting character
* Add a new version available banner in admin section
* Further image size reduction by over 30% by switching to alpine
* Update dependencies

## 0.3.2 - Fix backup functionality (Aug 11, 2024)

* Fix backup functionality by re-adding setuptools to virtual environment

## 0.3.1 - Reduce image size and add PDFs per page setting (Aug 11, 2024)

* Reduce image size by almost 20%
* Add PDFs per page setting: control how many PDFs are shown in the PDF overview

### Bug introduced
* removing setuptools from virtual environment broke backup functionality


## 0.3.0 - Periodic Backups to S3 Compatible Storage (Aug 03, 2024)

* Add periodic backups to S3 compatible storage

## 0.2.0 - New Admin Area (Jul 27, 2024)

* Add new Admin Area - admins can delete users and grant + remove admin rights
* Remove standard Django Admin Area
* Add `OIDC_ENABLE` environment variable for enabling SSO via OIDC

### Breaking Changes

* In order to use SSO via OIDC the environment variable `OIDC_ENABLE` needs to be set to `TRUE`.
  For more information refer to the [configuration](https://github.com/mrmn2/PdfDing#configuration) section of the README.

## 0.1.2 - Colored Themes (Jul 24, 2024)

* Add theme colors
* Add view counter for PDFs
* Change profile icon



## 0.1.1 - Dark Mode (Jul 15, 2024)

* Add dark mode
* Update dependencies

## 0.1.0 - Initial Release (Jul 13, 2024)

* Browser based PDF viewing
* Organize PDFs with tags
* Clean and responsive UI Remembers current position - continue where you stopped reading
* SSO support via OIDC
* Every user can upload its own PDFs. There is no admin curating the content.
