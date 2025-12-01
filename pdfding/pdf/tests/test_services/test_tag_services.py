from collections import OrderedDict
from unittest import mock

import pdf.service as service
from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models.pdf_models import Pdf
from pdf.models.tag_models import Tag


class TestTagServices(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='username', password='password', email='a@a.com')

    def test_process_tag_names(self):
        Tag.objects.create(name='existing', owner=self.user.profile)

        tag_names = ['existing', 'generated']
        tags = service.TagServices.process_tag_names(tag_names, self.user.profile)

        for tag, tag_name in zip(tags, tag_names):
            self.assertEqual(tag.name, tag_name)

        # check if new tag was generated with correct owner
        self.assertEqual(tags[1].owner, self.user.profile)

    def test_process_tag_names_empty(self):
        tags = service.TagServices.process_tag_names([], self.user.profile)

        self.assertEqual(tags, [])

    @mock.patch('pdf.service.TagServices.get_tag_info_dict_tree_mode')
    def test_get_tag_info_dict_tree_mode_enabled(self, mock_get_tag_info_dict_tree_mode):
        profile = self.user.profile
        profile.tag_tree_mode = True
        profile.save()

        service.TagServices.get_tag_info_dict(profile)
        mock_get_tag_info_dict_tree_mode.assert_called_once_with(profile)

    @mock.patch('pdf.service.TagServices.get_tag_info_dict_normal_mode')
    def test_get_tag_info_dict_tree_mode_disabled(self, mock_get_tag_info_dict_normal_mode):
        profile = self.user.profile
        profile.tag_tree_mode = False
        profile.save()

        service.TagServices.get_tag_info_dict(profile)
        mock_get_tag_info_dict_normal_mode.assert_called_once_with(profile)

    def test_get_tag_info_dict_normal_mode(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf_1')

        tag_names = [
            'programming/python/django',
            'programming/python',
            'programming/java/springboot',
            'programming/python/flask',
            'hobbies/sports/team',
            'No_children',
            'programming2',
            'programming',
        ]

        tags = []

        for tag_name in tag_names:
            tag = Tag.objects.create(
                name=tag_name, owner=self.user.profile, workspace=self.user.profile.current_workspace
            )
            tags.append(tag)

        pdf.tags.set(tags)

        generated_tag_dict = service.TagServices.get_tag_info_dict_normal_mode(self.user.profile)
        create_list = [(tag_name, {'display_name': tag_name}) for tag_name in sorted(tag_names, key=str.casefold)]
        expected_tag_dict = OrderedDict(create_list)

        self.assertEqual(expected_tag_dict, generated_tag_dict)

    def test_get_tag_info_dict_tree_mode(self):
        pdf = Pdf.objects.create(collection=self.user.profile.current_collection, name='pdf_1')

        tag_names = [
            'programming/python/django',
            'programming/python',
            'programming/python/django/tutorials',
            'programming/java/springboot',
            'programming/python/flask',
            'hobbies/sports/team',
            'No-children',
            'programming2',
            'programming',
        ]

        tags = []

        for tag_name in tag_names:
            tag = Tag.objects.create(
                name=tag_name, owner=self.user.profile, workspace=self.user.profile.current_workspace
            )
            tags.append(tag)

        pdf.tags.set(tags)

        generated_tag_dict = service.TagServices.get_tag_info_dict_tree_mode(self.user.profile)
        expected_tag_dict = OrderedDict(
            [
                (
                    'hobbies',
                    {'display_name': 'hobbies', 'level': 0, 'has_children': True, 'show_cond': '', 'slug': 'hobbies'},
                ),
                (
                    'hobbies/sports',
                    {
                        'display_name': 'sports',
                        'level': 1,
                        'has_children': True,
                        'show_cond': 'tag_hobbies_show_children',
                        'slug': 'hobbies___sports',
                    },
                ),
                (
                    'hobbies/sports/team',
                    {
                        'display_name': 'team',
                        'level': 2,
                        'has_children': False,
                        'show_cond': 'tag_hobbies_show_children && tag_hobbies___sports_show_children',
                        'slug': 'hobbies___sports___team',
                    },
                ),
                (
                    'No-children',
                    {
                        'display_name': 'No-children',
                        'level': 0,
                        'has_children': False,
                        'show_cond': '',
                        'slug': 'No_children',
                    },
                ),
                (
                    'programming',
                    {
                        'display_name': 'programming',
                        'level': 0,
                        'has_children': True,
                        'show_cond': '',
                        'slug': 'programming',
                    },
                ),
                (
                    'programming/java',
                    {
                        'display_name': 'java',
                        'level': 1,
                        'has_children': True,
                        'show_cond': 'tag_programming_show_children',
                        'slug': 'programming___java',
                    },
                ),
                (
                    'programming/java/springboot',
                    {
                        'display_name': 'springboot',
                        'level': 2,
                        'has_children': False,
                        'show_cond': 'tag_programming_show_children && tag_programming___java_show_children',
                        'slug': 'programming___java___springboot',
                    },
                ),
                (
                    'programming/python',
                    {
                        'display_name': 'python',
                        'level': 1,
                        'has_children': True,
                        'show_cond': 'tag_programming_show_children',
                        'slug': 'programming___python',
                    },
                ),
                (
                    'programming/python/django',
                    {
                        'display_name': 'django',
                        'level': 2,
                        'has_children': False,
                        'show_cond': 'tag_programming_show_children && tag_programming___python_show_children',
                        'slug': 'programming___python___django',
                    },
                ),
                (
                    'programming/python/django/tutorials',
                    {
                        'display_name': 'django/tutorials',
                        'level': 2,
                        'has_children': False,
                        'show_cond': 'tag_programming_show_children && tag_programming___python_show_children',
                        'slug': 'programming___python___django___tutorials',
                    },
                ),
                (
                    'programming/python/flask',
                    {
                        'display_name': 'flask',
                        'level': 2,
                        'has_children': False,
                        'show_cond': 'tag_programming_show_children && tag_programming___python_show_children',
                        'slug': 'programming___python___flask',
                    },
                ),
                (
                    'programming2',
                    {
                        'display_name': 'programming2',
                        'level': 0,
                        'has_children': False,
                        'show_cond': '',
                        'slug': 'programming2',
                    },
                ),
            ]
        )

        self.assertEqual(expected_tag_dict, generated_tag_dict)
