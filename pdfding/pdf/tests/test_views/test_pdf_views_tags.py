from unittest import mock
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect
from pdf import forms
from pdf.models.pdf_models import Pdf, Tag
from pdf.views import pdf_views


def set_up(self):
    self.client = Client()
    self.user = User.objects.create_user(username=self.username, password=self.password, email='a@a.com')
    self.client.login(username=self.username, password=self.password)


class TestTagViews(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    def test_edit_tag_get(self):
        tag = Tag.objects.create(name='tag_name', owner=self.user.profile)

        response = self.client.get(f"{reverse('edit_tag')}?tag_name={tag.name}")
        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)

    def test_edit_tag_get_htmx(self):
        tag = Tag.objects.create(name='tag_name', owner=self.user.profile)
        headers = {'HTTP_HX-Request': 'true'}

        response = self.client.get(f"{reverse('edit_tag')}?tag_name={tag.name}", **headers)

        self.assertEqual(response.context['tag_name'], tag.name)
        self.assertIsInstance(response.context['form'], forms.TagNameForm)
        self.assertTemplateUsed(response, 'partials/tag_name_form.html')

    def test_edit_tag_name_post_invalid_form(self):
        Tag.objects.create(name='tag_name', owner=self.user.profile)

        # post is invalid because data is missing
        # follow=True is needed for getting the message
        response = self.client.post(reverse('edit_tag'), follow=True)
        message = list(response.context['messages'])[0]

        self.assertEqual(message.message, 'This field is required.')
        self.assertEqual(message.tags, 'warning')

    @patch('pdf.views.pdf_views.EditTag.rename_tag')
    @patch('pdf.service.TagServices.adjust_referer_for_tag_view', return_value='pdf_overview')
    def test_edit_tag_post_normal_mode(self, mock_adjust_referer_for_tag_view, mock_rename_tag):
        profile = self.user.profile
        profile.tag_tree_mode = False
        profile.save()

        tag = Tag.objects.create(name='tag_name', owner=self.user.profile)
        # should not be changed
        tag_2 = Tag.objects.create(name='tag_name/child', owner=self.user.profile)
        self.client.post(reverse('edit_tag'), data={'name': 'new', 'current_name': 'tag_name'})

        mock_adjust_referer_for_tag_view.assert_called_once_with('pdf_overview', 'tag_name', 'new')
        mock_rename_tag.assert_called_once_with(tag, 'new', self.user.profile)
        self.assertEqual(tag_2.name, 'tag_name/child')

    @patch('pdf.views.pdf_views.EditTag.rename_tag')
    @patch('pdf.service.TagServices.adjust_referer_for_tag_view', return_value='pdf_overview')
    def test_edit_tag_post_tree_mode(self, mock_adjust_referer_for_tag_view, mock_rename_tag):
        profile = self.user.profile
        profile.tag_tree_mode = True
        profile.save()

        tags = []

        for name in ['programming', 'programming/python', 'programming/python/django', 'programming/python/flask']:
            tag = Tag.objects.create(name=name, owner=self.user.profile)
            tags.append(tag)

        self.client.post(reverse('edit_tag'), data={'name': 'new', 'current_name': 'programming/python'})

        mock_adjust_referer_for_tag_view.assert_called_once_with('pdf_overview', 'programming/python', 'new')
        mock_rename_tag.assert_has_calls(
            [
                mock.call(tags[1], 'new', self.user.profile),
                mock.call(tags[2], 'new/django', self.user.profile),
                mock.call(tags[3], 'new/flask', self.user.profile),
            ]
        )

    def test_rename_tag_normal(self):
        tag = Tag.objects.create(name='tag_name', owner=self.user.profile)
        pdf_views.EditTag.rename_tag(tag, 'new', self.user.profile)

        # get pdf again with the changes
        tag = self.user.profile.tag_set.get(id=tag.id)
        self.assertEqual(tag.name, 'new')

    def test_rename_tag_existing(self):
        tag_1 = Tag.objects.create(name='tag_1', owner=self.user.profile)
        tag_2 = Tag.objects.create(name='tag_2', owner=self.user.profile)
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')
        pdf.tags.set([tag_2])

        pdf_views.EditTag.rename_tag(tag_2, tag_1.name, self.user.profile)

        self.assertEqual(pdf.tags.count(), 1)
        self.assertEqual(self.user.profile.tag_set.count(), 1)
        self.assertEqual(pdf.tags.first(), tag_1)

    def test_rename_tag_existing_and_present(self):
        # if the pdf has both tags after one to the other only one should remain
        tag_1 = Tag.objects.create(name='tag_1', owner=self.user.profile)
        tag_2 = Tag.objects.create(name='tag_2', owner=self.user.profile)
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')
        pdf.tags.set([tag_1, tag_2])

        pdf_views.EditTag.rename_tag(tag_2, tag_1.name, self.user.profile)

        self.assertEqual(pdf.tags.count(), 1)
        self.assertEqual(self.user.profile.tag_set.count(), 1)
        self.assertEqual(pdf.tags.first(), tag_1)

    @patch('pdf.service.TagServices.adjust_referer_for_tag_view', return_value='pdf_overview')
    def test_delete_tag_normal_mode(self, mock_adjust_referer_for_tag_view):
        profile = self.user.profile
        profile.tag_tree_mode = False
        profile.save()

        tag = Tag.objects.create(name='tag_name', owner=self.user.profile)
        tag_2 = Tag.objects.create(name='tag_name/child', owner=self.user.profile)

        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.post(reverse('delete_tag'), **headers, data={'tag_name': tag.name})

        self.assertFalse(self.user.profile.tag_set.filter(id=tag.id).exists())
        self.assertTrue(self.user.profile.tag_set.filter(id=tag_2.id).exists())
        self.assertEqual(type(response), HttpResponseClientRedirect)

        mock_adjust_referer_for_tag_view.assert_called_with('pdf_overview', 'tag_name', '')

    @patch('pdf.service.TagServices.adjust_referer_for_tag_view', return_value='pdf_overview')
    def test_delete_tag_tree_mode(self, mock_adjust_referer_for_tag_view):
        profile = self.user.profile
        profile.tag_tree_mode = True
        profile.save()

        tags = []

        for name in ['programming', 'programming/python', 'programming/python/django', 'programming/python/flask']:
            tag = Tag.objects.create(name=name, owner=self.user.profile)
            tags.append(tag)

        headers = {'HTTP_HX-Request': 'true'}
        response = self.client.post(reverse('delete_tag'), **headers, data={'tag_name': 'programming/python'})

        self.assertTrue(self.user.profile.tag_set.filter(id=tags[0].id).exists())
        for i in range(1, 4):
            self.assertFalse(self.user.profile.tag_set.filter(id=tags[i].id).exists())

        self.assertEqual(type(response), HttpResponseClientRedirect)

        mock_adjust_referer_for_tag_view.assert_called_with('pdf_overview', 'programming/python', '')

    def test_delete_no_htmx(self):
        Tag.objects.create(name='tag_name', owner=self.user.profile)

        response = self.client.post(reverse('delete_tag'))
        self.assertRedirects(response, reverse('pdf_overview'), status_code=302)


class TestTagMixin(TestCase):
    username = 'user'
    password = '12345'

    def setUp(self):
        self.user = None
        set_up(self)

    def test_get_tag_by_name(self):
        tag = Tag.objects.create(name='tag_name', owner=self.user.profile)

        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        tag_retrieved = pdf_views.TagMixin.get_tag_by_name(response.wsgi_request, tag.name)

        self.assertEqual(tag, tag_retrieved)

    def test_get_tags_by_name_single(self):
        tag = Tag.objects.create(name='programming/python', owner=self.user.profile)

        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        tags_retrieved = pdf_views.TagMixin.get_tags_by_name(response.wsgi_request, tag.name)

        self.assertEqual([tag], tags_retrieved)

    def test_get_tags_by_name_multiple(self):
        tags = []

        for name in ['programming', 'programming/python/django', 'programming/python/flask']:
            tag = Tag.objects.create(name=name, owner=self.user.profile)
            tags.append(tag)

        # do a dummy request so we can get a request object
        response = self.client.get(reverse('pdf_overview'))
        tags_retrieved = pdf_views.TagMixin.get_tags_by_name(response.wsgi_request, 'programming/python')

        self.assertEqual(tags[1:], tags_retrieved)
