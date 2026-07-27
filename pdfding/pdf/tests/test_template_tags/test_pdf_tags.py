from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models.pdf_models import Pdf
from pdf.services.pdf_services import get_or_create_pdf_reading_info
from pdf.templatetags import pdf_tags


class TestPdfTags(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='12345')
        self.profile = self.user.profile
        self.pdf = Pdf.objects.create(
            name='pdf_1',
            collection=self.user.profile.current_collection,
        )

    def test_get_progress(self):
        self.pdf.number_of_pages = 1000
        self.pdf.save()
        pdf_reading_info = get_or_create_pdf_reading_info(self.pdf, self.profile)
        pdf_reading_info.views = 1
        pdf_reading_info.save()

        for current_page, expected_progress in [(0, 0), (202, 20), (995, 100), (1200, 100)]:
            pdf_reading_info.current_page = current_page
            pdf_reading_info.save()

            assert expected_progress == pdf_tags.get_progress(self.pdf, self.profile)

    def test_get_current_page(self):
        pdf_reading_info = get_or_create_pdf_reading_info(self.pdf, self.profile)
        assert 0 == pdf_tags.get_current_page(self.pdf, self.profile)

        pdf_reading_info.views = 1
        pdf_reading_info.current_page = 20
        pdf_reading_info.save()

        assert 20 == pdf_tags.get_current_page(self.pdf, self.profile)

        pdf_reading_info.current_page = -1
        pdf_reading_info.save()

        assert 0 == pdf_tags.get_current_page(self.pdf, self.profile)
