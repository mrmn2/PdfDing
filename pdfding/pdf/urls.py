import pdf.views.pdf_views as pdf_views
import pdf.views.share_views as share_views
from django.urls import path

urlpatterns = [
    path('', pdf_views.Overview.as_view(), name='pdf_overview'),
    path('query/', pdf_views.OverviewQuery.as_view(), name='pdf_overview_query'),
    path('<int:page>/', pdf_views.Overview.as_view(), name='pdf_overview_page'),
    path('add', pdf_views.Add.as_view(), name='add_pdf'),
    path('bulk_add', pdf_views.BulkAdd.as_view(), name='bulk_add_pdfs'),
    path('current_page/<identifier>', pdf_views.CurrentPage.as_view(), name='current_page'),
    path('delete/<identifier>', pdf_views.Delete.as_view(), name='delete_pdf'),
    path('details/<identifier>', pdf_views.Details.as_view(), name='pdf_details'),
    path('download/<identifier>', pdf_views.Download.as_view(), name='download_pdf'),
    path('edit/<identifier>/<field_name>', pdf_views.Edit.as_view(), name='edit_pdf'),
    path('get/<identifier>', pdf_views.Serve.as_view(), name='serve_pdf'),
    path('update_page', pdf_views.UpdatePage.as_view(), name='update_page'),
    path('view/<identifier>', pdf_views.ViewerView.as_view(), name='view_pdf'),
    path('share/<identifier>', share_views.Share.as_view(), name='share_pdf'),
    path('shared/overview/', share_views.Overview.as_view(), name='shared_pdf_overview'),
    path('shared/overview/query/', share_views.OverviewQuery.as_view(), name='shared_pdf_overview_query'),
    path('shared/overview/<int:page>/', share_views.Overview.as_view(), name='shared_pdf_overview_page'),
    path('shared/delete/<identifier>', share_views.Delete.as_view(), name='delete_shared_pdf'),
    path('shared/details/<identifier>', share_views.Details.as_view(), name='shared_pdf_details'),
    path('shared/download/<identifier>', share_views.Download.as_view(), name='download_shared_pdf'),
    path('shared/edit/<identifier>/<field_name>', share_views.Edit.as_view(), name='edit_shared_pdf'),
    path('shared/get/<identifier>', share_views.Serve.as_view(), name='serve_shared_pdf'),
    path('shared/get_qrcode/<identifier>', share_views.ServeQrCode.as_view(), name='serve_qrcode'),
    path('shared/download_qrcode/<identifier>', share_views.DownloadQrCode.as_view(), name='download_qrcode'),
    path('shared/<identifier>', share_views.ViewShared.as_view(), name='view_shared_pdf'),
    path('delete_tag/<identifier>', pdf_views.DeleteTag.as_view(), name='delete_tag'),
    path('edit_tag/<identifier>', pdf_views.EditTag.as_view(), name='edit_tag'),
]
