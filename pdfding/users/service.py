from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from pdf.models import Pdf, Tag
from pdf.service import PdfProcessingServices
from users.models import Profile


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


def get_viewer_colors(user_profile: Profile = None) -> dict[str, str]:
    primary_color_dict = {'light': '255 255 255', 'dark': '15 23 42', 'inverted': '71 71 71', 'creme': '226 220 208'}
    secondary_color_dict = {'light': '242 242 242', 'dark': '25 34 50', 'inverted': '61 61 61', 'creme': '196 191 181'}
    text_color_dict = {'light': '15 23 42', 'dark': '226 232 240', 'inverted': '226 232 240', 'creme': '68 64 60'}
    theme_color_dict = {
        'Green': '74 222 128',
        'Blue': '71 147 204',
        'Gray': '151 170 189',
        'Red': '248 113 113',
        'Pink': '218 123 147',
        'Orange': '255 203 133',
        'Brown': '76 37 24',
    }

    if user_profile:
        rgb_as_str = [str(val) for val in convert_hex_to_rgb(user_profile.custom_theme_color)]
        custom_color_rgb_str = ' '.join(rgb_as_str)
        theme_color_dict['Custom'] = custom_color_rgb_str

        theme_color = user_profile.theme_color

        if user_profile.pdf_inverted_mode == 'Enabled':
            theme = 'inverted'
        else:
            theme = user_profile.dark_mode_str
    else:
        theme_color = settings.DEFAULT_THEME_COLOR
        theme = settings.DEFAULT_THEME

    color_dict = {
        'primary_color': primary_color_dict[theme],
        'secondary_color': secondary_color_dict[theme],
        'text_color': text_color_dict[theme],
        'theme_color': theme_color_dict[theme_color],
    }

    return color_dict


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

    user.profile.tags_open = True
    user.profile.save()

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
        PdfProcessingServices.process_with_pypdfium(pdf)
        PdfProcessingServices.set_highlights_and_comments(pdf)

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
