# Changelog

## 0.10.0 - Markdown Notes  (Jan 5, 2025)
* Add markdown notes to PDFs. The notes can be shown in the PDF overview.
* Add healthz endpoint. This endpoint is primarily used for restarting the demo instance
  every `x` minutes.
* Improve design of view shared PDF prompt page

## 0.9.1 - Demo Mode  (Jan 2, 2025)
* Introduce demo mode
* Add hover tooltips to the buttons of the viewer
* make parent-children relationships for tags in tree mode clearer by adding guiding lines
* Add PDF ID to details page
* minor UI improvements for PDF details page
* fix: Adjust viewer navigation bar for mobile devices
* fix: Display correct version in admin area. This did not work due to the migration from
  woodpacker to gh actions.

## 0.9.0 - Annotations, Highlighting and Drawings  (Dec 25, 2024)
* Add editing functionality to the PDF viewer. Users can add annotations, highlighting and drawings to PDFs
  and save them. More information can be found
  [here](https://github.com/mrmn2/PdfDing/blob/master/docs/guides.md#editing).
* Show pdf name as the site title.
* Update dependencies

## 0.8.0 - Tag Tree Mode (Dec 22, 2024)
* Add tree mode for tags. Pdfs can now be organized with hierarchical tags. Instructions
  can be found [here](https://github.com/mrmn2/PdfDing/blob/master/docs/guides.md#tags).
* Minor UI improvements

### Breaking Changes
* Due to the internal workings of the tree mode for tags, naming of tags had to be restricted.
  From now on tags can only contain letters, numbers, '/', '-' and '_'. Furthermore, names cannot
  start or end with '/' and consecutive occurrences of '/' are also not allowed. These restrictions
  are only enforced for newly created tags. For existing tags users will need to activate normal
  mode for tags and manually adjust the tags, so they are valid. Otherwise, tree mode will not work.

## 0.7.0 - Consumption Directory (Dec 15, 2024)
* Add consumption directory as an alternative way for adding PDF files
* Show user ID in the header dropdown menu
* Fix: set extension to ".pdf" when downloading a PDF

## 0.6.2 - Progress Bars Improvements (Dec 11, 2024)
* Only display the progress bar if a PDF's number of pages are valid
* Set the current page in the reading progress to 0 if it is unopened
* Slight refactoring for getting the number of pages in a PDF. Hopefully,
  this will fix some problems regarding this topic.

## 0.6.1 - Fix Settings (Dec 07, 2024)
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
