from unittest.mock import patch

from base.service import construct_query_overview_url, construct_search_and_tag_queries, process_raw_search_query
from django.test import TestCase
from django.urls import reverse


class TestService(TestCase):
    def test_process_raw_search_query(self):
        input_str_list = ['#tag_1 #tag_2    sear&ch_#str_1 search_str_2', '#tag_1 #', 'search_str_1', '']
        expected_search_list = ['search_str_1 search_str_2', '', 'search_str_1', '']
        expected_tags_list = [['tag_1', 'tag_2'], ['tag_1'], [], []]

        for input_str, expected_search, expected_tags in zip(input_str_list, expected_search_list, expected_tags_list):
            generated_search, generated_tags = process_raw_search_query(input_str)
            self.assertEqual(generated_search, expected_search)
            self.assertEqual(generated_tags, expected_tags)

    def test_construct_search_and_tag_queries_new_only(self):
        search, tags = construct_search_and_tag_queries('search ing #tag1 #tag2', '', '', '')

        self.assertEqual(search, 'search+ing')
        self.assertEqual(tags, ['tag1', 'tag2'])

    def test_construct_search_and_tag_queries_do_nothing(self):
        search, tags = construct_search_and_tag_queries('', '', '', '')

        self.assertEqual(search, '')
        self.assertEqual(tags, [])

    def test_construct_search_and_tag_queries_add_remove_tag(self):
        search, tags = construct_search_and_tag_queries('#new', 'old2', 'old1 old2', 'searching')
        self.assertEqual(search, 'searching')
        self.assertEqual(tags, ['old1', 'new'])

    def test_construct_search_and_tag_queries_add_tag_change_search(self):
        search, tags = construct_search_and_tag_queries('other search #new', '', 'old', 'searching')
        self.assertEqual(search, 'other+search')
        self.assertEqual(tags, ['old', 'new'])

    def test_construct_search_and_tag_queries_change_search(self):
        search, tags = construct_search_and_tag_queries('other', '', 'old', 'searching')
        self.assertEqual(search, 'other')
        self.assertEqual(tags, ['old'])

    def test_construct_search_and_tag_queries_reset_search(self):
        search, tags = construct_search_and_tag_queries('', '', 'old', 'searching')
        self.assertEqual(search, '')
        self.assertEqual(tags, ['old'])

    @patch('base.service.construct_search_and_tag_queries')
    def test_construct_query_overview_url_search(self, mock_construct_search_and_tag_queries):
        mock_construct_search_and_tag_queries.return_value = ('search', ['tag'])
        referer_url = f'{reverse('pdf_overview')}?search=searching&tags=asd'
        generated_url = construct_query_overview_url(referer_url, 'search #tag', '', 're', 'pdf')

        self.assertEqual(generated_url, f'{reverse('pdf_overview')}?search=search&tags=tag')
        mock_construct_search_and_tag_queries.assert_called_once_with('search #tag', 're', 'asd', 'searching')

    def test_construct_query_overview_url_selection(self):
        referer_url = f'{reverse('pdf_overview')}?search=searching&tags=asd&selection=starred'
        generated_url = construct_query_overview_url(referer_url, '', 'starred', '', 'pdf')

        self.assertEqual(generated_url, f'{reverse('pdf_overview')}?search=searching&tags=asd&selection=starred')
