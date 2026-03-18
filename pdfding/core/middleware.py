from django.middleware.locale import LocaleMiddleware


class PdfDingLocaleMiddleware(LocaleMiddleware):
    """Local middleware for setting the language code via the profile model."""

    def process_request(self, request):
        # unauthenticated users and auto mode should use the default django way
        # for determening the language_code
        if request.user.is_anonymous or request.user.profile.language_code == 'auto':
            # set language code via default django way
            # https://docs.djangoproject.com/en/6.0/topics/i18n/translation/#how-django-discovers-language-preference
            super().process_request(request)
        else:
            request.LANGUAGE_CODE = request.user.profile.language_code
