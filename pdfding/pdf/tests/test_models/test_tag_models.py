from django.test import TestCase
from pdf.models.tag_models import Tag


class TestTag(TestCase):
    def test_parse_tag_string(self):
        input_tag_str = '#Tag1  ###tag2      ta&g3 ta+g4'
        expected_tags = ['tag1', 'tag2', 'tag3', 'tag4']
        generated_tags = Tag.parse_tag_string(input_tag_str)

        self.assertEqual(expected_tags, generated_tags)

    def test_parse_tag_string_empty(self):
        generated_tags = Tag.parse_tag_string('')

        self.assertEqual([], generated_tags)
