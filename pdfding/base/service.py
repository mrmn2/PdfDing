from urllib.parse import parse_qs, urlparse

from django.urls import reverse


def construct_query_overview_url(referer_url: str, sort_query: str, search_query: str, obj_name: str) -> str:
    """
    Constructs the overview url with search and/or sort after performing a search or sorting in the overview pages.
    """

    parsed_referer_url = urlparse(referer_url)
    referer_query_parameters = parse_qs(parsed_referer_url.query)

    # sorting and searching are never performed at the same time, thus we can use if ... elif
    if sort_query:
        referer_query_parameters['sort'] = [sort_query]
    elif search_query:
        referer_query_parameters['q'] = search_query.split(' ')
    else:
        # empty search -> remove so search is cleared
        referer_query_parameters.pop('q', None)

    query_string = '&'.join(f'{key}={"+".join(query)}' for key, query in referer_query_parameters.items())
    query_string = query_string.replace('#', '%23')

    overview_url = reverse(f'{obj_name}_overview')

    if query_string:
        overview_url = f'{overview_url}?{query_string}'

    return overview_url
