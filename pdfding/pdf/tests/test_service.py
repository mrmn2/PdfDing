import filecmp
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from uuid import uuid4

import pdf.service as service
from core.settings import MEDIA_ROOT
from django.contrib.auth.models import User
from django.core.files import File
from django.db.models.functions import Lower
from django.http.response import Http404
from django.test import TestCase
from django.urls import reverse
from pdf.models.pdf_models import Pdf, PdfComment, PdfHighlight, Tag
from PIL import Image
from pypdfium2 import PdfDocument
from users.service import get_demo_pdf


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
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_1')

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
            tag = Tag.objects.create(name=tag_name, owner=pdf.owner)
            tags.append(tag)

        pdf.tags.set(tags)

        generated_tag_dict = service.TagServices.get_tag_info_dict_normal_mode(self.user.profile)
        create_list = [(tag_name, {'display_name': tag_name}) for tag_name in sorted(tag_names, key=str.casefold)]
        expected_tag_dict = OrderedDict(create_list)

        self.assertEqual(expected_tag_dict, generated_tag_dict)

    def test_get_tag_info_dict_tree_mode(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_1')

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
            tag = Tag.objects.create(name=tag_name, owner=pdf.owner)
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


class TestPdfProcessingServices(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='username', password='password', email='a@a.com')

    def test_create_pdf(self):
        pdf_name = 'some_pdf'
        pdf_file = get_demo_pdf()
        tag_string = 'some tags'
        description = 'some description'
        file_directory = 'some/dir'
        owner = self.user.profile

        pdf = service.PdfProcessingServices.create_pdf(
            name=pdf_name,
            owner=owner,
            pdf_file=pdf_file,
            tag_string=tag_string,
            description=description,
            file_directory=file_directory,
        )

        self.assertEqual(pdf.name, pdf_name)
        self.assertEqual(pdf.owner, owner)
        self.assertEqual(pdf.description, description)
        self.assertEqual(pdf.file_directory, file_directory)
        self.assertEqual(pdf.notes, '')
        self.assertEqual(pdf.number_of_pages, 5)
        self.assertTrue(pdf.preview)
        self.assertTrue(pdf.thumbnail)
        self.assertEqual(pdf.pdfcomment_set.count(), 2)
        self.assertEqual(pdf.pdfhighlight_set.count(), 2)

        for tag, expected_tag_name in zip(pdf.tags.all().order_by('name'), tag_string.split(' ')):
            self.assertEqual(tag.name, expected_tag_name)

    @mock.patch('pdf.service.PdfProcessingServices.set_thumbnail_and_preview')
    def test_set_process_with_pypdfium_no_images(self, mock_set_thumbnail_and_preview):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_1')
        self.assertEqual(pdf.number_of_pages, -1)

        dummy_path = Path(__file__).parent / 'data' / 'dummy.pdf'
        with dummy_path.open(mode="rb") as f:
            pdf.file = File(f, name=dummy_path.name)
            pdf.save()

        service.PdfProcessingServices.process_with_pypdfium(pdf, False)

        pdf = self.user.profile.pdf_set.get(name=pdf.name)
        self.assertEqual(pdf.number_of_pages, 2)
        mock_set_thumbnail_and_preview.assert_not_called()

    @mock.patch('pdf.service.PdfProcessingServices.set_thumbnail_and_preview')
    def test_set_process_with_pypdfium_with_images(self, mock_set_thumbnail_and_preview):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_1')
        self.assertEqual(pdf.number_of_pages, -1)

        dummy_path = Path(__file__).parent / 'data' / 'dummy.pdf'
        with dummy_path.open(mode="rb") as f:
            pdf.file = File(f, name=dummy_path.name)
            pdf.save()

        mock_set_thumbnail_and_preview.return_value = pdf

        service.PdfProcessingServices.process_with_pypdfium(pdf)

        pdf = self.user.profile.pdf_set.get(name=pdf.name)
        self.assertEqual(pdf.number_of_pages, 2)
        mock_set_thumbnail_and_preview.assert_called_once()

    def test_set_process_with_pypdfium_exception(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_1')

        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'test1.pdf'
        pdf.file = file_mock
        pdf.save()

        service.PdfProcessingServices.process_with_pypdfium(pdf, False)
        pdf = self.user.profile.pdf_set.get(name=pdf.name)
        self.assertEqual(pdf.number_of_pages, -1)

    def test_set_thumbnail_and_preview(self):
        dummy_path = Path(__file__).parent / 'data' / 'dummy.pdf'
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')
        with dummy_path.open(mode="rb") as f:
            pdf.file = File(f, name=dummy_path.name)
            pdf.save()

        pdf_document = PdfDocument(pdf.file.path, autoclose=True)

        pdf = service.PdfProcessingServices.set_thumbnail_and_preview(pdf, pdf_document, 120, 2, 400)
        thumbnail_pil_image = Image.open(pdf.thumbnail.file)
        preview_pil_image = Image.open(pdf.preview.file)

        self.assertEqual(thumbnail_pil_image.size, (120, 60))
        self.assertEqual(preview_pil_image.width, 400)

        pdf_document.close()

    def test_set_thumbnail_and_preview_exception(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf')

        # check that exception is caught and thumbnail stays unset
        pdf = service.PdfProcessingServices.set_thumbnail_and_preview(pdf, None, 120, 2, 150)

        self.assertFalse(pdf.thumbnail)

    def test_get_pdf_info_list(self):
        dummy_path = Path(__file__).parent / 'data' / 'dummy.pdf'

        for i in range(3):
            pdf = Pdf.objects.create(owner=self.user.profile, name=f'pdf_{i}')
            with dummy_path.open(mode="rb") as f:
                pdf.file = File(f, name=dummy_path.name)
                pdf.save()

        generated_info_list = service.get_pdf_info_list(self.user.profile)
        expected_info_list = [(f'pdf_{i}', 8885) for i in range(3)]

        self.assertEqual(generated_info_list, expected_info_list)

    def test_set_highlights_and_comments(self):
        creation_date = datetime.strptime('20250311081649-+00:00', '%Y%m%d%H%M%S-%z')

        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_with_annotations', file=get_demo_pdf())

        comment_1 = PdfComment.objects.create(text='demo comment page 2', page=2, creation_date=creation_date, pdf=pdf)
        comment_2 = PdfComment.objects.create(text='last page', page=5, creation_date=creation_date, pdf=pdf)
        highlight_1 = PdfHighlight.objects.create(
            text='Massa ullamcorper aenean molestie laoreet aenean sed laoreet. '
            'Ante non cursus proin mauris dictumst magnis',
            page=3,
            creation_date=creation_date,
            pdf=pdf,
        )
        highlight_2 = PdfHighlight.objects.create(
            text='Semper curabitur est maecenas orci dis accumsan sem dictum commodo?',
            page=2,
            creation_date=creation_date,
            pdf=pdf,
        )

        service.PdfProcessingServices.set_highlights_and_comments(pdf)

        for generated_comment, expected_comment in zip(
            pdf.pdfcomment_set.all().order_by(Lower('text')), [comment_1, comment_2]
        ):
            self.assertEqual(generated_comment.text, expected_comment.text)
            self.assertEqual(generated_comment.creation_date, expected_comment.creation_date)
            self.assertEqual(generated_comment.page, expected_comment.page)
            # if id is different it comments were as expected recreated
            self.assertNotEqual(generated_comment.id, expected_comment.id)

        for generated_highlight, expected_comment_highlight in zip(
            pdf.pdfhighlight_set.all().order_by(Lower('text')), [highlight_1, highlight_2]
        ):
            self.assertEqual(generated_highlight.text, expected_comment_highlight.text)
            self.assertEqual(generated_highlight.creation_date, expected_comment_highlight.creation_date)
            self.assertEqual(generated_highlight.page, expected_comment_highlight.page)
            # if id is different it highlights were as expected recreated
            self.assertNotEqual(generated_highlight.id, expected_comment_highlight.id)

    def test_set_highlights_and_comments_exception(self):
        pdf = Pdf.objects.create(owner=self.user.profile, name='pdf_with_annotations', file='dummy_file')

        # check that exception is caught and thumbnail stays unset
        service.PdfProcessingServices.set_highlights_and_comments(pdf)

        self.assertFalse(pdf.pdfcomment_set.count())
        self.assertFalse(pdf.pdfhighlight_set.count())

    @mock.patch('pdf.service.PdfProcessingServices.export_annotations_to_yaml')
    def test_export_annotations(self, mock_export_annotation_to_yaml):
        pdf_1 = Pdf.objects.create(owner=self.user.profile, name='pdf_1')
        pdf_2 = Pdf.objects.create(owner=self.user.profile, name='pdf_2')

        comment_1 = PdfComment.objects.create(text='c1', page=1, creation_date=pdf_1.creation_date, pdf=pdf_1)
        comment_2 = PdfComment.objects.create(text='c2', page=2, creation_date=pdf_2.creation_date, pdf=pdf_2)
        highlight_1 = PdfHighlight.objects.create(text='h1', page=1, creation_date=pdf_1.creation_date, pdf=pdf_1)
        highlight_2 = PdfHighlight.objects.create(text='h2', page=2, creation_date=pdf_2.creation_date, pdf=pdf_2)

        # kind = comments and all pdfs
        service.PdfProcessingServices.export_annotations(profile=self.user.profile, kind='comments')
        comment_arg, id_arg = mock_export_annotation_to_yaml.call_args.args
        self.assertEqual(id_arg, str(self.user.id))
        for actual_comment, expected_comment in zip(comment_arg.order_by('text'), [comment_1, comment_2]):
            self.assertEqual(actual_comment, expected_comment)

        # kind = highlights and all pdfs
        service.PdfProcessingServices.export_annotations(profile=self.user.profile, kind='highlights')
        highlight_arg, id_arg = mock_export_annotation_to_yaml.call_args.args
        self.assertEqual(id_arg, str(self.user.id))
        for actual_highlight, expected_highlight in zip(highlight_arg.order_by('text'), [highlight_1, highlight_2]):
            self.assertEqual(actual_highlight, expected_highlight)

        # kind = comments and single pdfs
        service.PdfProcessingServices.export_annotations(profile=self.user.profile, kind='comments', pdf=pdf_1)
        comment_arg, id_arg = mock_export_annotation_to_yaml.call_args.args
        self.assertEqual(id_arg, str(self.user.id))
        for actual_comment, expected_comment in zip(comment_arg.order_by('text'), [comment_1]):
            self.assertEqual(actual_comment, expected_comment)

        # kind = highlights and single pdfs
        service.PdfProcessingServices.export_annotations(profile=self.user.profile, kind='highlights', pdf=pdf_1)
        highlight_arg, id_arg = mock_export_annotation_to_yaml.call_args.args
        self.assertEqual(id_arg, str(self.user.id))
        for actual_highlight, expected_highlight in zip(highlight_arg.order_by('text'), [highlight_1]):
            self.assertEqual(actual_highlight, expected_highlight)

    @mock.patch(
        'pdf.service.PdfProcessingServices.get_annotation_export_path',
        return_value=Path(__file__).parent / 'data' / 'tmp_export.yaml',
    )
    def test_export_annotation_to_yaml(self, mock_get_annotation_export_path):
        creation_date = datetime.strptime('2025-03-17 20:26:48+00:00', '%Y-%m-%d %H:%M:%S%z')

        pdf_1 = Pdf.objects.create(owner=self.user.profile, name='some_pdf')
        pdf_2 = Pdf.objects.create(owner=self.user.profile, name='another_pdf')

        PdfComment.objects.create(text='c1', page=1, creation_date=creation_date, pdf=pdf_1)
        PdfComment.objects.create(text='c2', page=2, creation_date=creation_date, pdf=pdf_2)
        PdfComment.objects.create(text='another c', page=0, creation_date=creation_date, pdf=pdf_2)

        export_path = service.PdfProcessingServices.get_annotation_export_path(str(self.user.id))
        service.PdfProcessingServices.export_annotations_to_yaml(PdfComment.objects.all(), str(self.user.id))

        self.assertTrue(filecmp.cmp(export_path, Path(__file__).parent / 'data' / 'dummy_export.yaml', shallow=False))

        export_path.unlink()

    @mock.patch('pdf.service.delete_empty_dirs_after_rename_or_delete')
    @mock.patch('pdf.service.get_file_path')
    @mock.patch('pdf.service.copy')
    def test_process_renaming_pdf(self, mock_copy, mock_get_file_path, mock_delete_empty_dirs_after_rename_or_delete):
        current_pdf_name = 'some_pdf'
        current_file_name = f'{self.user.id}/pdf/{current_pdf_name}.pdf'
        current_path = MEDIA_ROOT / current_file_name
        current_path.touch()

        new_pdf_name = 'changed'
        new_file_name = f'{self.user.id}/pdf/child_dir/{new_pdf_name}.pdf'
        new_path = MEDIA_ROOT / new_file_name
        mock_get_file_path.return_value = new_file_name

        pdf = Pdf.objects.create(owner=self.user.profile, name=current_pdf_name)
        pdf.file = current_file_name
        pdf.save()

        # set new name as it will be saved by process_renaming_pdf
        pdf.name = new_pdf_name

        # check that the name is still not changed, as saving it is part of process_renaming_pdf
        unchanged_pdf = Pdf.objects.get(id=pdf.id)
        self.assertEqual(current_pdf_name, unchanged_pdf.name)

        new_path_parent = new_path.parent
        # dir should not exist, instead it should be created during the rename_pdf
        self.assertFalse(new_path_parent.exists())

        service.PdfProcessingServices.process_renaming_pdf(pdf)
        changed_pdf = Pdf.objects.get(id=pdf.id)

        # check that the file was copied, the original file was deleted, empty dirs were deleted,
        # name and file name were adjusted
        mock_get_file_path.assert_called_once_with(pdf, None)
        self.assertEqual(new_pdf_name, changed_pdf.name)
        self.assertTrue(new_path_parent.exists())
        self.assertEqual(changed_pdf.file.name, new_file_name)
        mock_copy.assert_called_once_with(current_path, new_path)
        self.assertFalse(current_path.exists())
        mock_delete_empty_dirs_after_rename_or_delete.assert_called_once_with(current_file_name, self.user.id)

        # cleanup
        new_path_parent.rmdir()

    @mock.patch('pdf.service.copy')
    @mock.patch('pdf.service.delete_empty_dirs_after_rename_or_delete')
    @mock.patch('pdf.service.get_file_path')
    def test_process_renaming_pdf_unchanged_file_path(
        self, mock_get_file_path, mock_delete_empty_dirs_after_rename_or_delete, mock_copy
    ):
        original_pdf_name = 'some_pdf'
        new_pdf_name = 'changed'
        file_name = 'subdir/some.pdf'
        mock_get_file_path.return_value = file_name

        pdf = Pdf.objects.create(owner=self.user.profile, name=original_pdf_name)
        pdf.file = file_name
        pdf.save()

        pdf.name = new_pdf_name

        # check that the name is still not changed
        unchanged_pdf = Pdf.objects.get(id=pdf.id)
        self.assertEqual(original_pdf_name, unchanged_pdf.name)

        service.PdfProcessingServices.process_renaming_pdf(pdf)

        # check that the new name was saved
        changed_pdf = Pdf.objects.get(id=pdf.id)
        self.assertEqual(new_pdf_name, changed_pdf.name)

        mock_get_file_path.assert_called_once_with(pdf, None)

        # check that blocks are not called as the file path did not change
        mock_copy.assert_not_called()
        mock_delete_empty_dirs_after_rename_or_delete.assert_not_called()


class TestOtherServices(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='username', password='password', email='a@a.com')

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
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'some_name'

        generated_name = service.create_name_from_file(file_mock)
        self.assertEqual(generated_name, 'some_name')

    def test_create_name_from_file_different_suffix(self):
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'some.name'

        generated_name = service.create_name_from_file(file_mock)
        self.assertEqual(generated_name, 'some.name')

    def test_create_name_from_file_pdf_suffix(self):
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'some.name.PdF'

        generated_name = service.create_name_from_file(file_mock)
        self.assertEqual(generated_name, 'some.name')

    @mock.patch('pdf.service.create_name_from_file', return_value='existing_name')
    @mock.patch('pdf.service.uuid4', return_value='123456789')
    def test_create_unique_name_from_file_existing_name(self, mock_uuid4, mock_create_name_from_file):
        user = User.objects.create_user(username='user', password='12345', email='a@a.com')
        Pdf.objects.create(owner=user.profile, name='existing_name')
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'existing_name.pdf'

        generated_name = service.create_unique_name_from_file(file_mock, user.profile)
        self.assertEqual(generated_name, 'existing_name_12345678')
        mock_create_name_from_file.assert_called_once_with(file_mock)

    @mock.patch('pdf.service.create_name_from_file', return_value='not_existing_name')
    def test_create_unique_name_from_file_not_existing_name(self, mock_create_name_from_file):
        user = User.objects.create_user(username='user', password='12345', email='a@a.com')
        file_mock = mock.MagicMock(spec=File, name='FileMock')
        file_mock.name = 'not_existing_name.pdf'

        generated_name = service.create_unique_name_from_file(file_mock, user.profile)
        self.assertEqual(generated_name, 'not_existing_name')
        mock_create_name_from_file.assert_called_once_with(file_mock)

    def test_adjust_referer_for_tag_view_no_replace(self):
        # url of searched for #other
        url = f'{reverse("pdf_overview")}?search=searching&tags=tag1+tag2'
        adjusted_url = service.TagServices.adjust_referer_for_tag_view(url, 'tag', 'other_tag')

        self.assertEqual(url, adjusted_url)

    def test_adjust_referer_for_tag_view_no_query(self):
        url = reverse('pdf_overview')

        adjusted_url = service.TagServices.adjust_referer_for_tag_view(url, 'tag', 'other_tag')

        self.assertEqual(url, adjusted_url)

    def test_adjust_referer_for_tag_view_space(self):
        # url of searched for #other
        url = f'{reverse("pdf_overview")}?search=searching&tags=tag1+tag2'

        adjusted_url = service.TagServices.adjust_referer_for_tag_view(url, 'tag1', '')
        expected_url = f'{reverse("pdf_overview")}?search=searching&tags=tag2'

        self.assertEqual(expected_url, adjusted_url)

    def test_adjust_referer_for_tag_view_space_remove(self):
        # url of searched for #other
        url = f'{reverse("pdf_overview")}?search=searching&tags=other'

        adjusted_url = service.TagServices.adjust_referer_for_tag_view(url, 'other', '')
        expected_url = f'{reverse("pdf_overview")}?search=searching'

        self.assertEqual(expected_url, adjusted_url)

    def test_adjust_referer_for_tag_view_word(self):
        # url of searched for #other
        url = f'{reverse("pdf_overview")}?tags=other'

        adjusted_url = service.TagServices.adjust_referer_for_tag_view(url, 'other', 'another')
        expected_url = f'{reverse("pdf_overview")}?tags=another'

        self.assertEqual(expected_url, adjusted_url)
