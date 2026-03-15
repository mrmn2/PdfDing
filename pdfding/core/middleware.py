from django.middleware.locale import LocaleMiddleware


class PdfDingLocalMiddleware(LocaleMiddleware):
    """Local middleware for setting the language code via the profile model."""

    def process_request(self, request):
        request.LANGUAGE_CODE = 'en'
