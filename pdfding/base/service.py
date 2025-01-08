from urllib.parse import parse_qs, urlparse

from django.urls import reverse


def process_raw_search_query(raw_search_query: str) -> tuple[str, list[str]]:
    """
    Process the raw search query.

    Example input: #tag1 #tag2 searchstring1 searchstring2
    Example output: ('searchstring1 searchstring2', ['tag1', 'tag2'])
    """

    search = []
    tags = []

    if raw_search_query:
        split_query = raw_search_query.split(sep=' ')

        for query in split_query:
            if query.startswith('#'):
                # ignore hashtags only
                if len(query) > 1:
                    tags.append(query[1:])
            elif query:
                # strip and remove '#' and '&' that to not belong to tags search, as a hashtag will cause the rest of
                # the search to be ignored
                query = query.replace('#', '').replace('&', '')
                search.append(query.strip().replace('#', ''))

    search = ' '.join(search)

    return search, tags


def construct_search_and_tag_queries(
    new_search_query: str, remove_tag_query: str, old_tags_str: str, old_search: str
) -> tuple[str, list[str]]:
    """
    Construct the search and tag queries for the overview pages.

    - Tags in "new_search_query" are always added to the existing ones. A Tag that should be removed, is specified via
    "remove_tag_query".
    - Adding or removing tags should not change the existing search
    - If no search and tag inputs are provided the search is reset
    """

    new_search, new_tags = process_raw_search_query(new_search_query)

    old_tags = []
    if old_tags_str:
        old_tags = old_tags_str.split(' ')

    # if there is a new search use it. if there is no tag action we use the new search (which will be empty and resets
    # the search)
    if new_search or not (new_tags or remove_tag_query):
        search = new_search
    # the old search is only kept if there is tag action and no new search
    else:
        search = old_search

    # add new tags to old tags and remove tag if specified
    tags = old_tags + [new_tag for new_tag in new_tags if new_tag not in old_tags]
    tags = [tag for tag in tags if tag != remove_tag_query]

    return search, tags


def construct_query_overview_url(
    referer_url: str,
    sort_query: str,
    search_query: str,
    special_selection_query: str,
    remove_tag_query: str,
    obj_name: str,
) -> str:
    """Constructs the overview url after performing a search or sorting in the overview pages."""

    parsed_referer_url = urlparse(referer_url)
    query_parameters = parse_qs(parsed_referer_url.query)

    # special selection, sorting and searching are never performed at the same time, thus we can use if ... elif
    if special_selection_query:
        query_parameters['selection'] = [special_selection_query]
    elif sort_query:
        query_parameters['sort'] = [sort_query]
    else:
        referer_tags = query_parameters.get('tags', [''])[0]
        referer_search = query_parameters.get('search', [''])[0]
        search, tags = construct_search_and_tag_queries(search_query, remove_tag_query, referer_tags, referer_search)

        query_parameters['search'] = [search]
        query_parameters['tags'] = tags

    query_string = '&'.join(
        f'{key}={"+".join(query)}' for key, query in query_parameters.items() if query not in [[], ['']]
    )

    overview_url = reverse(f'{obj_name}_overview')

    if query_string:
        overview_url = f'{overview_url}?{query_string}'

    return overview_url
