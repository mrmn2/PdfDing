from django.contrib.auth.models import User
from django.test import TestCase
from pdf.models.pdf_models import Pdf, Tag


class TestSignals(TestCase):
    def test_delete_orphan_tag(self):
        # create pdfs and tags
        user = User.objects.create_user(username='test_user', password='12345')
        pdf_1 = Pdf.objects.create(owner=user.profile, name='pdf_1')
        pdf_2 = Pdf.objects.create(owner=user.profile, name='pdf_2')
        tag_1 = Tag.objects.create(name='tag_1', owner=pdf_1.owner)
        tag_2 = Tag.objects.create(name='tag_2', owner=pdf_2.owner)
        pdf_1.tags.set([tag_1, tag_2])
        pdf_2.tags.set([tag_2])

        pdf_1.delete()

        # check that the tag of pdf 2 was not touched
        pdf_2_tag_names = [tag.name for tag in pdf_2.tags.all()]
        self.assertEqual(pdf_2_tag_names, ['tag_2'])

        # check that tag 1 was deleted
        self.assertFalse(user.profile.tags.filter(name='tag_1').exists())
