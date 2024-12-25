# PdfDing
PdfDing is a selfhosted PDF manager, viewer and editor offering a seamless user experience on multiple devices.

[![GitHub Repo Stars](https://img.shields.io/github/stars/mrmn2/PdfDing?style=flat&logo=github)](https://github.com/mrmn2/PdfDing)
[![Docker Pulls](https://img.shields.io/docker/pulls/mrmn/pdfding?style=flat&logo=docker&logoColor=white)](https://hub.docker.com/r/mrmn/pdfding)
[![Version](https://img.shields.io/github/v/release/mrmn2/PdfDing?style=flat&label=version)](https://github.com/mrmn2/PdfDing/releases)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/mrmn2/PdfDing/test.yaml?style=flat&logo=github&label=ci)](https://github.com/mrmn2/PdfDing/actions)
[![Last Commit](https://img.shields.io/github/last-commit/mrmn2/PdfDing?style=flat&logo=github)](https://github.com/mrmn2/PdfDing/commits/master/)

![](https://github.com/mrmn2/PdfDing-Screenshots/blob/master/screenshots/pdf_overview_dark_green.png)

## Overview
- [Introduction](#introduction)
- [Installation](#installation)
- [Guides](#guides)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledements)

## Introduction
PdfDing is a PDF manager, viewer and editor that you can host yourself. It offers a seamless user experience on multiple
devices. It's designed be to be minimal, fast, and easy to set up using Docker. As all data stays on your server
you have full control over your data and privacy.

With its simple, intuitive and adjustable UI, PdfDing makes it easy for users to keep track of their PDFs
and access them whenever they need to. With a dark mode and colored themes users can style the app to
their liking. As PdfDing offers SSO support via OIDC it can be easily integrated into existing setups.

The name is a combination of PDF and *ding*. Ding is the German word for thing. Thus, PdfDing is a thing for
your PDFs. The name and PdfDing's design are inspired by the excellent bookmark manager
[linkding](https://github.com/sissbruecker/linkding).


### Feature Overview
* Seamless browser based PDF viewing on multiple devices
* Organize PDFs with multi-level tags
* Edit PDFs by adding annotations, highlighting and drawings
* Dark Mode, colored themes and custom theme colors
* Inverted color mode for reading PDFs
* Remembers current position - continue where you stopped reading
* SSO support via OIDC
* Share PDFs with an external audience via a link or a QR Code
* Shared PDFs can be password protected and access can be controlled with a maximum number of views and an expiration date
* Progress bars show the reading progress of each PDF at a quick glance
* Every user can upload its own PDFs. There is no admin curating the content.
* Automated and encrypted backups to S3 compatible storage
* Consumption directory as an alternative way to add PDFs
* Simple Admin area for user management

### Screenshots
Screenshots can be found [here](https://github.com/mrmn2/PdfDing/blob/master/docs/screenshots.md).

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
To install PdfDing using Docker Compose, you can use one of the files in the
[deploy](https://github.com/mrmn2/PdfDing/tree/master/deploy) directory and run e.g.:

```
docker-compose -d -f sqlite.docker-compose.yaml
```

## Guides
Guides about various aspects of PdfDing can be found in the
[guides](https://github.com/mrmn2/PdfDing/blob/master/docs/guides.md) section of the docs.

## Configuration
Information about the different configuration options can be found in the
[configuration](https://github.com/mrmn2/PdfDing/blob/master/docs/configuration.md) section of the docs.

## Contributing
Small improvements, bugfixes and documentation improvements are always welcome.
If you want to contribute a larger feature, consider opening an issue first to
discuss it. I may choose to ignore PRs for features that don't align with the
project's goals or that I don't want to maintain.

If you are interested in contributing more information can be found in the
[development](https://github.com/mrmn2/PdfDing/blob/master/docs/development.md) section of the docs.

## Acknowledements
* This project started by adjusting the django starter of Andreas Jud: [django-starter](https://github.com/andyjud/django-starter), [django-starter-assets](https://github.com/andyjud/django-starter-assets)
* As mentioned above, inspired by [linkding](https://github.com/sissbruecker/linkding).
