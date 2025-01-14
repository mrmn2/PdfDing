import logging

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from pdf.models import Pdf, Tag
from pdf.service import process_with_pypdfium

logger = logging.getLogger('management')


class Command(BaseCommand):
    help = "Create Users and PDFs for demo mode"

    def handle(self, *args, **kwargs):
        logger.info('Create Users and PDFs for demo mode')

        suffixes = list(range(1, 6))
        # sometimes the django random filter in the login template returned an empty string instead of a number
        # resulting in "user_@pdfding.com". Therefore, we'll also create that user.
        suffixes.append('')

        demo_file_path = settings.MEDIA_ROOT / 'demo' / 'demo.pdf'
        pdf_names = [
            'The best self-hosted applications',
            'My favorite book',
            'User Manual',
            'Self-hosting Guide',
        ]
        descriptions = [
            '',
            'This is the best book I have ever read.',
            'Everyone will understand this guide!',
            'A guide about getting starting with self-hosting apps on k8s',
        ]
        tag_names_list = [['self-hosted/apps'], ['books'], ['guide'], ['self-hosted', 'k8s']]

        for i in suffixes:
            # delete the old data
            email = f'user_{i}@pdfding.com'
            try:
                user = User.objects.get(username=email)
                user.delete()
            except User.DoesNotExist:
                pass

        # create new data
        for user_id, suffix in enumerate(suffixes):
            email = f'user_{suffix}@pdfding.com'
            user = User.objects.create_user(username=email, password='demo', email=email, id=user_id)  # nosec

            # set email address to verified
            user.save()  # this will create email address object if not yet existing
            email_address = EmailAddress.objects.get_primary(user)
            email_address.verified = True
            email_address.save()

            for pdf_name, description, tag_names in zip(pdf_names, descriptions, tag_names_list):
                tags = [Tag.objects.create(name=tag_name, owner=user.profile) for tag_name in tag_names]

                with demo_file_path.open(mode="rb") as f:
                    pdf_file = File(f, name=demo_file_path.name)

                    if pdf_name == 'Self-hosting Guide':
                        notes = get_example_notes()
                    else:
                        notes = ''

                    pdf = Pdf.objects.create(
                        owner=user.profile,
                        name=pdf_name,
                        file=pdf_file,
                        description=description,
                        notes=notes,
                        number_of_pages=5,
                    )
                    pdf.tags.set(tags)
                    process_with_pypdfium(pdf)


def get_example_notes():  # pragma: no cover
    notes = '''
## **`Example Note`**

In the notes you can add further information about your PDF. Notes support markdown, so it is possible to use `inline code` or [links](https://github.com/mrmn2/PdfDing). You can also use lists:

* here is an example element
    * nested lists are also possible
* here is another one

Of course you can also use code blocks

```
# example code
def example_code():
    print('hi')
```
or block quotes
> this is a block quote
>> with a nested block quote
'''  # noqa: E501

    return notes
