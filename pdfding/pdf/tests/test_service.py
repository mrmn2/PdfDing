from datetime import datetime, timedelta, timezone
from unittest import mock
from uuid import uuid4

import pdf.service as service
from django.contrib.auth.models import User
from django.core.files import File
from django.http.response import Http404
from django.test import TestCase
from pdf.models import Pdf, Tag


class TestService(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='username', password='password', email='a@a.com')

    def test_process_tag_names(self):
        Tag.objects.create(name='existing', owner=self.user.profile)

        tag_names = ['existing', 'generated']
        tags = service.process_tag_names(tag_names, self.user.profile)

        for tag, tag_name in zip(tags, tag_names):
            self.assertEqual(tag.name, tag_name)

        # check if new tag was generated with correct owner
        self.assertEqual(tags[1].owner, self.user.profile)

    def test_process_tag_names_empty(self):
        tags = service.process_tag_names([], self.user.profile)

        self.assertEqual(tags, [])

    def test_get_tag_dict(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_1')
        tag_a = Tag.objects.create(name='a', owner=pdf.owner)
        tag_bread = Tag.objects.create(name='bread', owner=pdf.owner)
        tag_1 = Tag.objects.create(name='tag1', owner=pdf.owner)
        tag_3 = Tag.objects.create(name='tag3', owner=pdf.owner)
        tag_banana = Tag.objects.create(name='banana', owner=pdf.owner)
        tags = [tag_a, tag_bread, tag_banana, tag_3, tag_1]
        pdf.tags.set(tags)

        expected_tag_dict = {'a': [tag_a], 'b': [tag_banana, tag_bread], 't': [tag_1, tag_3]}
        generated_tag_dict = service.get_tag_dict(self.user.profile)

        self.assertEqual(expected_tag_dict, generated_tag_dict)

        # make sure first characters are sorted correctly
        self.assertEqual(['a', 'b', 't'], list(generated_tag_dict.keys()))

    @staticmethod
    @service.check_object_access_allowed
    def get_object(pdf_id: str, user: User):
        user_profile = user.profile
        pdf = user_profile.pdf_set.get(id=pdf_id)

        return pdf

    def test_check_object_access_allowed_existing(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        self.assertEqual(pdf, self.get_object(pdf.id, self.user))

    def test_check_object_access_allowed_validation(self):
        with self.assertRaises(Http404):
            self.get_object('12345', self.user)

    def test_check_object_access_allowed_does_not_exist(self):
        with self.assertRaises(Http404):
            self.get_object(str(uuid4()), self.user)

    def test_get_future_datetime(self):
        expected_result = datetime.now(timezone.utc) + timedelta(days=1, hours=0, minutes=22)
        generated_result = service.get_future_datetime('1d0h22m')

        self.assertTrue((generated_result - expected_result).total_seconds() < 0.1)

    def test_get_future_datetime_empty(self):
        self.assertEqual(service.get_future_datetime(''), None)

    def test_create_name_from_file_no_suffix(self):
        user = User.objects.create_user(username='user', password='12345', email='a@a.com')
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'some_name'

        generated_name = service.create_name_from_file(file_mock, user.profile)
        self.assertEqual(generated_name, 'some_name')

    def test_create_name_from_file_suffix(self):
        user = User.objects.create_user(username='user', password='12345', email='a@a.com')
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'some_name.PdF'

        generated_name = service.create_name_from_file(file_mock, user.profile)
        self.assertEqual(generated_name, 'some_name')

    @mock.patch('pdf.service.uuid4', return_value='123456789')
    def test_create_name_from_file_existing_name(self, mock_uuid4):
        user = User.objects.create_user(username='user', password='12345', email='a@a.com')
        Pdf.objects.create(owner=user.profile, name='existing_name')
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'existing_name.pdf'

        generated_name = service.create_name_from_file(file_mock, user.profile)
        self.assertEqual(generated_name, 'existing_name_12345678')

    def test_adjust_referer_for_tag_view_no_replace(self):
        # url of searched for #other
        url = 'http://127.0.0.1:5000/pdf/?q=%23other'

        adjusted_url = service.adjust_referer_for_tag_view(url, 'tag', 'other_tag')

        self.assertEqual(url, adjusted_url)

    def test_adjust_referer_for_tag_view_no_query(self):
        url = 'http://127.0.0.1:5000/pdf/bla'

        adjusted_url = service.adjust_referer_for_tag_view(url, 'tag', 'other_tag')

        self.assertEqual(url, adjusted_url)

    def test_adjust_referer_for_tag_view_space(self):
        # url of searched for #other
        url = 'http://127.0.0.1:5000/pdf/?q=%23other'

        adjusted_url = service.adjust_referer_for_tag_view(url, 'other', '')

        self.assertEqual('http://127.0.0.1:5000/pdf/?q=', adjusted_url)

    def test_adjust_referer_for_tag_view_word(self):
        # url of searched for #other
        url = 'http://127.0.0.1:5000/pdf/?q=%23other'

        adjusted_url = service.adjust_referer_for_tag_view(url, 'other', 'another')

        self.assertEqual('http://127.0.0.1:5000/pdf/?q=%23another', adjusted_url)
