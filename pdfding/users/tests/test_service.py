from unittest.mock import patch

import users.service as service
from django.contrib.auth.models import User
from django.test import TestCase, override_settings


class TestUserServices(TestCase):
    def test_clean_convert_hex_to_rgb_correct(self):
        self.assertEqual(service.convert_hex_to_rgb('#FFB3A5'), (255, 179, 165))
        self.assertEqual(service.convert_hex_to_rgb('ffb3a5'), (255, 179, 165))

    def test_convert_rgb_to_hex(self):
        self.assertEqual(service.convert_rgb_to_hex(255, 179, 165), '#ffb3a5')

    def test_get_color_shades(self):
        self.assertEqual(service.get_color_shades('#b5edff'), ('#91becc', '#6d8e99', '#d3f4ff'))

    def test_get_viewer_colors_profile(self):
        user = User.objects.create_user(username='user', password="password")

        profile = user.profile
        profile.theme_color = 'Green'
        profile.dark_mode = 'light'

        generated_color_dict = service.get_viewer_colors(profile)
        expected_color_dict = {
            'primary_color': '255 255 255',
            'secondary_color': '242 242 242',
            'text_color': '15 23 42',
            'theme_color': '74 222 128',
        }

        self.assertEqual(generated_color_dict, expected_color_dict)

        # also test custom color and inverted mode
        profile.theme_color = 'Custom'
        profile.pdf_inverted_mode = 'Enabled'
        profile.custom_theme_color = '#000000'

        generated_color_dict = service.get_viewer_colors(profile)
        expected_color_dict = {
            'primary_color': '71 71 71',
            'secondary_color': '61 61 61',
            'text_color': '226 232 240',
            'theme_color': '0 0 0',
        }

        self.assertEqual(generated_color_dict, expected_color_dict)

    @override_settings(DEFAULT_THEME='creme', DEFAULT_THEME_COLOR='Brown')
    def test_get_viewer_colors_no_profile(self):
        generated_color_dict = service.get_viewer_colors()
        expected_color_dict = {
            'primary_color': '226 220 208',
            'secondary_color': '196 191 181',
            'text_color': '68 64 60',
            'theme_color': '76 37 24',
        }

        self.assertEqual(generated_color_dict, expected_color_dict)

    def test_get_demo_pdf(self):
        demo_pdf = service.get_demo_pdf()

        self.assertEqual(demo_pdf.size, 29451)

    @patch('users.service.PdfProcessingServices.process_with_pypdfium')
    def test_create_demo_user(self, mock_process_with_pypdfium):
        email = 'demo@pdfding.com'
        user = service.create_demo_user(email, 'password')

        self.assertEqual(user.profile.pdf_set.all().count(), 4)
        self.assertEqual(user.profile.tag_set.all().count(), 5)
        self.assertEqual(mock_process_with_pypdfium.call_count, 4)
        self.assertEqual(user.email, email)
