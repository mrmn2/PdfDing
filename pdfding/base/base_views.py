from base.service import construct_query_overview_url
from core.settings import ITEMS_PER_PAGE, MEDIA_ROOT
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import FileResponse, HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.static import serve
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh


class BaseAdd(View):
    """View for adding new objects."""

    def get(self, request: HttpRequest, identifier: str = None):
        """Display the form for adding an object."""

        context = self.get_context_get(request, identifier)

        return render(request, self.template_name, context)

    def post(self, request: HttpRequest, identifier: str = None):
        """Create the new object."""

        form = self.form(request.POST, request.FILES, owner=request.user.profile)

        if form.is_valid():
            self.obj_save(form, request, identifier)

            return redirect(f'{self.obj_name}_overview')

        return render(request, self.template_name, {'form': form})


class BaseOverview(View):
    """
    Base view for the overview pages. This view performs the searching and sorting. It's also responsible for
    paginating the objects.
    """

    def get(self, request: HttpRequest, page: int = 1, items_per_page: int = ITEMS_PER_PAGE):
        """
        Display the overview.
        """

        sorting = self.get_sorting(request)
        page_object, next_page_available = self.get_page_objects(request, sorting, page, items_per_page)
        context = {
            'page_obj': page_object,
            'sorting': sorting,
            'items_per_page': items_per_page,
            'next_page_available': next_page_available,
            'current_page': page,
        }

        context |= self.get_extra_context(request)

        if request.htmx:
            return render(request, f'includes/{self.overview_page_name}.html', context)
        else:
            return render(request, f'{self.obj_name}_overview.html', context)

    def get_page_objects(self, request: HttpRequest, sorting: str, page: int, items_per_page: int):
        # filter objects
        objects = self.filter_objects(request)

        # sort objects
        objects = objects.order_by(sorting)

        paginator = Paginator(objects, per_page=items_per_page, allow_empty_first_page=True)
        page_object = paginator.get_page(page)

        next_page_available = page_object.end_index() < objects.count()

        return page_object, next_page_available


class BaseOverviewQuery(View):
    """Base view for performing searches in the overview pages."""

    def get(self, request: HttpRequest):
        referer_url = request.META.get('HTTP_REFERER', f'{self.obj_name}_overview')

        search_query = request.GET.get('search', '')
        remove_tag_query = request.GET.get('remove', '')
        special_selection_query = request.GET.get('selection', '')

        redirect_url = construct_query_overview_url(
            referer_url, search_query, special_selection_query, remove_tag_query, self.obj_name
        )

        return redirect(redirect_url)


class BaseServe(View):
    """Base view used for serving PDF files specified by the PDF id."""

    def get(self, request: HttpRequest, identifier: str, revision=None):
        """
        Returns the specified file as a FileResponse

        There is a revision parameter, because of occasional problems related to viewing edited pdfs. When editing pdfs
        in the viewer and saving them, sometimes the old version is still shown in the viewer even though the backend
        has the correct version. This is probably caused by the browser's caching. This commit fixes the problem by
        adding a revision to the serve views so that the browser is forced to refresh the pdf.
        """

        serve_object = self.get_object(request, identifier)

        return serve(request, document_root=MEDIA_ROOT, path=self.get_file_path(serve_object))

    @staticmethod
    def get_file_path(serve_object):
        return serve_object.file.name


class BaseDownload(View):
    """Base view for downloading the PDF specified by the ID."""

    @staticmethod
    def get_suffix():  # pragma: no cover
        """
        Get an empty suffix. This is currently used for pdf files as otherwise download prompt is not started,
        but instead the build browser pdf view is opened.
        """

        return '.pdf'

    def get(self, request: HttpRequest, identifier: str):
        """Return the specified file as a FileResponse."""

        download_object = self.get_object(request, identifier)
        file_name = f'{download_object.name.replace(" ", "_").lower()}{self.get_suffix()}'

        response = FileResponse(open(download_object.file.path, 'rb'), as_attachment=True, filename=file_name)

        return response


class BaseDetails(View):
    """Base view for displaying the details page of an object."""

    def get(self, request: HttpRequest, identifier: str):
        """Display the details page."""

        obj = self.get_object(request, identifier)
        context = {self.obj_name: obj}

        return render(request, f'{self.obj_name}_details.html', context)


class BaseDetailsEdit(View):
    """
    The base view for editing fields of an object in the details page. The field, that is to be changed, is specified
    by the 'field' argument.
    """

    def get(self, request: HttpRequest, identifier: str, field_name: str):
        """Triggered by htmx. Display an inline form for editing the correct field."""

        obj = self.get_object(request, identifier)

        if request.htmx:
            form = self.get_edit_form_get(field_name, obj)

            return render(
                request,
                'partials/details_form.html',
                {
                    'action_url': reverse(
                        f'edit_{self.obj_name}', kwargs={'field_name': field_name, 'identifier': identifier}
                    ),
                    'details_url': reverse(f'{self.obj_name}_details', kwargs={'identifier': identifier}),
                    'edit_id': f'{field_name}-edit',
                    'form': form,
                    'field_name': field_name,
                },
            )

        return redirect(f'{self.obj_name}_details', identifier=identifier)

    def post(self, request: HttpRequest, identifier: str, field_name: str):
        """
        POST: Change the specified field by submitting the form.
        """

        obj = self.get_object(request, identifier)
        form_dict = self.get_edit_form_dict()
        form = form_dict[field_name](request.POST, instance=obj)

        if form.is_valid():
            # if tags are changed the provided tag string needs to processed, the PDF's tags need updating and orphaned
            # tags need to be deleted.

            if field_name in self.fields_requiring_extra_processing:
                self.process_field(field_name, obj, request, form.data)

            # if the name is changed we need to check that it is a unique name not used by another pdf of this user.
            elif field_name == 'name':
                existing_obj = self.obj_class.objects.filter(
                    owner=request.user.profile, name__iexact=form.data.get('name')
                ).first()

                if existing_obj and str(existing_obj.id) != identifier:
                    messages.warning(request, 'This name is already used by another PDF!')
                else:
                    form.save()

            # for any other field just save it
            else:
                form.save()
        else:
            try:
                error_dict = dict(form.errors)
                error_field = list(error_dict.keys())[0]
                messages.warning(request, error_dict[error_field][0])
            except:  # noqa # pragma: no cover
                messages.warning(request, 'Input is not valid!')
        return redirect(f'{self.obj_name}_details', identifier=identifier)


class BaseDelete(View):
    """Base view for deleting the object specified by its ID."""

    def delete(self, request: HttpRequest, identifier: str):
        """Delete the specified object."""

        redirect_target = f'{self.obj_name}_overview'

        if request.htmx:
            obj = self.get_object(request, identifier)
            obj.delete()

            # try to redirect to current page
            if 'details' not in request.META.get('HTTP_REFERER', ''):
                return HttpResponseClientRefresh()
            # if deleted from the details page the details page will no longer exist
            else:
                return HttpResponseClientRedirect(reverse(redirect_target))

        return redirect(redirect_target)
