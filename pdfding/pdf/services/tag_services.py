from collections import OrderedDict
from urllib.parse import parse_qs, urlparse

from django.db.models.functions import Lower
from django.urls import reverse
from pdf.models.tag_models import Tag
from pdf.models.workspace_models import Workspace
from users.models import Profile


class TagServices:
    @staticmethod
    def process_tag_names(tag_names: list[str], workspace: Workspace) -> list[Tag]:
        """
        Process the specified tags. If the tag is existing it will simply be added to the return list. If it does not
        exist it, it will be created and then be added to the return list.
        """

        tags = []
        for tag_name in tag_names:
            try:
                tag = Tag.objects.get(name=tag_name, workspace=workspace)
            except Tag.DoesNotExist:
                tag = Tag.objects.create(name=tag_name, workspace=workspace)

            tags.append(tag)

        return tags

    @classmethod
    def get_tag_info_dict(cls, profile: Profile) -> dict[str, dict]:
        """
        Get the tag info dict used for displaying the tags in the pdf overview.
        """

        if profile.tag_tree_mode:
            tag_info_dict = cls.get_tag_info_dict_tree_mode(profile)
        else:
            tag_info_dict = cls.get_tag_info_dict_normal_mode(profile)

        return tag_info_dict

    @staticmethod
    def get_tag_info_dict_normal_mode(profile: Profile) -> dict[str, dict]:
        """
        Get the tag info dict used for displaying the tags in the pdf overview when normal mode is activated.
        Key: name of the tag. Value: display name of the tag
        """

        # it is important that the tags are sorted. As parent tags need come before children,
        # e.g. "programming" before "programming/python"
        tags = profile.tags.order_by(Lower('name'))
        tag_info_dict = OrderedDict()

        for tag in tags:
            tag_info_dict[tag.name] = {'display_name': tag.name}

        return tag_info_dict

    @staticmethod
    def get_tag_info_dict_tree_mode(profile: Profile) -> dict[str, dict]:
        """
        Get the tag info dict used for displaying the tags in the pdf overview when tree mode is activated.
        Key: name of the tag. Value: Information about the tag necessary for displaying it in tree mode, e.g. display
        name, indent level, has_children, slug and the condition for showing it via alpine js.
        """

        # it is important that the tags are sorted. As parent tags need come before children,
        # e.g. "programming" before "programming/python"
        tags = profile.tags.order_by(Lower('name'))
        tag_info_dict = OrderedDict()

        for tag in tags:
            tag_split = tag.name.split('/', maxsplit=2)
            current = ''
            words = []
            show_conditions = []

            for level, word in enumerate(tag_split):
                prev = current
                words.append(word)
                current = '/'.join(words)

                if level:
                    tag_info_dict[prev]['has_children'] = True

                if current not in tag_info_dict:
                    tag_info_dict[current] = {
                        'display_name': current.split('/', level)[-1],
                        'level': level,
                        'has_children': False,
                        'show_cond': ' && '.join(show_conditions),
                        'slug': current.replace('-', '_').replace('/', '___'),
                    }

                # alpine js will not work if the tag starts with a number. therefore, we have "tag_" in front so it
                # will still work.
                show_conditions.append(f'tag_{current.replace('-', '_').replace('/', '___')}_show_children')

        return tag_info_dict

    def adjust_referer_for_tag_view(referer_url: str, replace: str, replace_with: str) -> str:
        """
        Adjust the referer url for tag views. If a tag is renamed or deleted, the query part of the tag string will be
        adjusted accordingly. E.g. for renaming tag 'some' to 'other': 'http://127.0.0.1:5000/pdf/?q=%23some' to
        'http://127.0.0.1:5000/pdf/?q=%23other'.
        """

        parsed_referer_url = urlparse(referer_url)
        query_parameters = parse_qs(parsed_referer_url.query)

        tag_query = []

        for tag in query_parameters.get('tags', [''])[0].split(' '):
            if tag and tag != replace:
                tag_query.append(tag)
            elif tag and replace_with:
                tag_query.append(replace_with)

        query_parameters['tags'] = tag_query

        query_string = '&'.join(
            f'{key}={"+".join(query)}' for key, query in query_parameters.items() if query not in [[], ['']]
        )

        overview_url = reverse('pdf_overview')

        if query_string:
            overview_url = f'{overview_url}?{query_string}'

        return overview_url
