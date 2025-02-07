from unittest.mock import patch

import users.service as service
from django.test import TestCase


class TestUserServices(TestCase):
    def test_clean_convert_hex_to_rgb_correct(self):
        self.assertEqual(service.convert_hex_to_rgb('#FFB3A5'), (255, 179, 165))
        self.assertEqual(service.convert_hex_to_rgb('ffb3a5'), (255, 179, 165))

    def test_convert_rgb_to_hex(self):
        self.assertEqual(service.convert_rgb_to_hex(255, 179, 165), '#ffb3a5')

    def test_get_color_shades(self):
        self.assertEqual(service.get_color_shades('#b5edff'), ('#91becc', '#6d8e99', '#d3f4ff'))

    def test_get_demo_pdf(self):
        demo_pdf = service.get_demo_pdf()

        self.assertEqual(demo_pdf.size, 26140)

    @patch('users.service.process_with_pypdfium')
    def test_create_demo_user(self, mock_process_with_pypdfium):
        email = 'demo@pdfding.com'
        user = service.create_demo_user(email, 'password')

        self.assertEqual(user.profile.pdf_set.all().count(), 4)
        self.assertEqual(user.profile.tag_set.all().count(), 5)
        self.assertEqual(mock_process_with_pypdfium.call_count, 4)
        self.assertEqual(user.email, email)
