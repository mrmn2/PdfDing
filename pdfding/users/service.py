from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from pdf.models import Pdf, Tag
from pdf.service import process_with_pypdfium


def convert_hex_to_rgb(hex_color: str) -> tuple[int, ...]:
    """Converts a hex color representation to RGB representation"""

    hex_color = hex_color.replace('#', '')

    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # noqa


def convert_rgb_to_hex(r: int, g: int, b: int) -> str:
    """Converts RGB color representation to a hex representation"""

    hex_color = ('{:02X}' * 3).format(r, g, b)

    return f'#{str.lower(hex_color)}'


def lighten_color(red: int, green: int, blue: int, percentage: float) -> tuple[int, ...]:
    """Lighting a RGB color by the specified percentage"""

    correction_factor = percentage

    return tuple(round((255 - val) * correction_factor + val) for val in (red, green, blue))


def darken_color(red: int, green: int, blue: int, percentage: float) -> tuple[int, ...]:
    """Darkening a RGB color by the specified percentage"""

    correction_factor = 1 - percentage

    return tuple(round(val * correction_factor) for val in (red, green, blue))


def get_color_shades(custom_color: str) -> tuple[str, ...]:
    """Get the color shades needed for custom theme colors."""

    rgb_color = convert_hex_to_rgb(str(custom_color))

    secondary_color = darken_color(*rgb_color, percentage=0.2)
    tertiary_color_1 = darken_color(*rgb_color, percentage=0.4)
    tertiary_color_2 = lighten_color(*rgb_color, percentage=0.4)

    return tuple(convert_rgb_to_hex(*color) for color in (secondary_color, tertiary_color_1, tertiary_color_2))


def get_demo_pdf():
    """Get the pdf file used in the demo mode."""

    file_path = settings.BASE_DIR / 'users' / 'demo_data' / 'demo.pdf'
    demo_pdf = File(file=open(file_path, 'rb'), name=file_path.name)

    return demo_pdf


def create_demo_user(email: str, password: str):
    """Create a demo user"""

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

    user = User.objects.create_user(username=email, password=password, email=email)  # nosec

    # set email address to verified
    user.save()  # this will create email address object if not yet existing
    email_address = EmailAddress.objects.get_primary(user)
    email_address.verified = True
    email_address.save()

    for pdf_name, description, tag_names in zip(pdf_names, descriptions, tag_names_list):
        tags = [Tag.objects.create(name=tag_name, owner=user.profile) for tag_name in tag_names]

        pdf_file = get_demo_pdf()

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

    return user


def get_example_notes():  # pragma: no cover
    """
    Get example notes for demo user
    """

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
