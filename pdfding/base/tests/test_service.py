from core.service import construct_query_overview_url
from django.test import TestCase
from django.urls import reverse


class TestService(TestCase):
    def test_construct_query_overview_url_empty_search(self):
        referer_url = f'{reverse('pdf_overview')}?q=searching'
        generated_url = construct_query_overview_url(referer_url, '', '', 'pdf')

        self.assertEqual(generated_url, reverse('pdf_overview'))

    def test_construct_query_overview_url_sort(self):
        referer_url = f'{reverse('pdf_overview')}?q=searching&sort=title_desc'
        generated_url = construct_query_overview_url(referer_url, 'title_asc', '', 'pdf')

        self.assertEqual(generated_url, f'{reverse('pdf_overview')}?q=searching&sort=title_asc')

    def test_construct_query_overview_url_search(self):
        referer_url = f'{reverse('pdf_overview')}?q=searching&sort=title_desc'
        generated_url = construct_query_overview_url(referer_url, '', 'another', 'pdf')

        self.assertEqual(generated_url, f'{reverse('pdf_overview')}?q=another&sort=title_desc')
