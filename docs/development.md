# Development
PdfDing is built using the Django web framework. You
can get started by checking out the excellent [Django docs](https://docs.djangoproject.com/en/stable/). Currently,
PdfDing consists of four applications:
* Inside the `pdf` folder is the one related to managing and viewing PDFs
* the folder `users` contains the logic related to users
* the admin area is implemented inside the `admin` folder
* `core` is the Django root application
* backups are handled inside `backup`

Other than that the code should be self-explanatory / standard Django stuff 🙂.

## Tech Stack
* The web app is build using the Python web framework [Django](https://www.djangoproject.com/)
* Mozilla's [PDF.js](https://mozilla.github.io/pdf.js/) is used for viewing PDF files in the browser
* The frondend is build using [Alpine.js](https://alpinejs.dev/), [htmx](https://htmx.org/),
[jQuery](https://jquery.com/) and [Tailwind CSS](https://tailwindcss.com/)
* Authentication, registration, account management and OIDC is achieved by [django-allauth](https://docs.allauth.org/en/latest/)

## Prerequisites
* Python 3
* pipx
* Poetry: `pipx install poetry`
* Node.js

## Setup
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

## Testing
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

## Code Quality
Formatting is done via `black`:
```
black .
```

Further code quality checks are done via `flake8`:
```
flake8
```

## Pre-Commit
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
