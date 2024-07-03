from django.urls import path
from pdf.views import (
    add_pdf_view,
    current_page_view,
    delete_pdf_view,
    download_pdf_view,
    pdf_details_view,
    pdf_edit_view,
    pdf_overview,
    serve_pdf,
    update_page_view,
    view_pdf_view,
)

urlpatterns = [
    path('', pdf_overview, name='pdf_overview'),
    path('<int:page>/', pdf_overview, name='pdf_overview_page'),
    path('add', add_pdf_view, name='add_pdf'),
    path('current_page/<pdf_id>', current_page_view, name='current_page'),
    path('delete/<pdf_id>', delete_pdf_view, name='delete_pdf'),
    path('details/<pdf_id>', pdf_details_view, name='pdf_details'),
    path('download/<pdf_id>', download_pdf_view, name='download_pdf'),
    path('edit/<pdf_id>/<field>', pdf_edit_view, name='edit_pdf'),
    path('get/<pdf_id>', serve_pdf, name='serve_pdf'),
    path('update_page', update_page_view, name='update_page'),
    path('view/<pdf_id>', view_pdf_view, name='view_pdf'),
]
