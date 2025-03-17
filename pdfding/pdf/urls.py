import pdf.views.pdf_views as pdf_views
import pdf.views.share_views as share_views
from django.urls import path

urlpatterns = [
    # pdf related views
    path('', pdf_views.Overview.as_view(), name='pdf_overview'),
    path('query/', pdf_views.OverviewQuery.as_view(), name='pdf_overview_query'),
    path('get_next_overview_page/<int:page>/', pdf_views.Overview.as_view(), name='get_next_pdf_overview_page'),
    path('add', pdf_views.Add.as_view(), name='add_pdf'),
    path('bulk_add', pdf_views.BulkAdd.as_view(), name='bulk_add_pdfs'),
    path('delete/<identifier>', pdf_views.Delete.as_view(), name='delete_pdf'),
    path('download/<identifier>', pdf_views.Download.as_view(), name='download_pdf'),
    path('edit/<identifier>/<field_name>', pdf_views.Edit.as_view(), name='edit_pdf'),
    path('get/<identifier>/<revision>', pdf_views.Serve.as_view(), name='serve_pdf'),
    path('get_thumbnail/<identifier>', pdf_views.ServeThumbnail.as_view(), name='serve_thumbnail'),
    path('get_preview/<identifier>', pdf_views.ServePreview.as_view(), name='serve_preview'),
    path('get_notes/<identifier>', pdf_views.GetNotes.as_view(), name='get_notes'),
    path('show_preview/<identifier>', pdf_views.ShowPreview.as_view(), name='show_preview'),
    path('update_page', pdf_views.UpdatePage.as_view(), name='update_page'),
    path('update_pdf', pdf_views.UpdatePdf.as_view(), name='update_pdf'),
    path('view/<identifier>', pdf_views.ViewerView.as_view(), name='view_pdf'),
    path('star/<identifier>', pdf_views.Star.as_view(), name='star'),
    path('archive/<identifier>', pdf_views.Archive.as_view(), name='archive'),
    path('highlights', pdf_views.HighlightOverview.as_view(), name='pdf_highlight_overview'),
    path(
        'highlights/get_next_overview_page/<int:page>/',
        pdf_views.HighlightOverview.as_view(),
        name='get_next_pdf_highlight_overview_page',
    ),
    path('comments', pdf_views.CommentOverview.as_view(), name='pdf_comment_overview'),
    path(
        'comments/get_next_overview_page/<int:page>/',
        pdf_views.CommentOverview.as_view(),
        name='get_next_pdf_comment_overview_page',
    ),
    path('annotations/export/<kind>', pdf_views.ExportAnnotations.as_view(), name='export_annotations'),
    path('annotations/export/<kind>/<identifier>', pdf_views.ExportAnnotations.as_view(), name='export_annotations'),
    # pdf details related views
    path('details/<identifier>', pdf_views.Details.as_view(), name='pdf_details'),
    path(
        'details/<identifier>/highlights',
        pdf_views.DetailsHighlightOverview.as_view(),
        name='pdf_details_highlight_overview',
    ),
    path(
        'details/<identifier>/get_next_highlight_overview_page/<int:page>/',
        pdf_views.DetailsHighlightOverview.as_view(),
        name='get_next_pdf_details_highlight_overview_page',
    ),
    path(
        'details/<identifier>/comments',
        pdf_views.DetailsCommentOverview.as_view(),
        name='pdf_details_comment_overview',
    ),
    path(
        'details/<identifier>/get_next_comment_overview_page/<int:page>/',
        pdf_views.DetailsCommentOverview.as_view(),
        name='get_next_pdf_details_comment_overview_page',
    ),
    # sharing related views
    path('share/<identifier>', share_views.Share.as_view(), name='share_pdf'),
    path('shared/overview/', share_views.Overview.as_view(), name='shared_pdf_overview'),
    path(
        'shared/get_next_overview_page/<int:page>/',
        share_views.Overview.as_view(),
        name='get_next_shared_overview_page',
    ),
    path('shared/overview/query/', share_views.OverviewQuery.as_view(), name='shared_pdf_overview_query'),
    path('shared/overview/<int:page>/', share_views.Overview.as_view(), name='shared_pdf_overview_page'),
    path('shared/delete/<identifier>', share_views.Delete.as_view(), name='delete_shared_pdf'),
    path('shared/details/<identifier>', share_views.Details.as_view(), name='shared_pdf_details'),
    path('shared/download/<identifier>', share_views.Download.as_view(), name='download_shared_pdf'),
    path('shared/edit/<identifier>/<field_name>', share_views.Edit.as_view(), name='edit_shared_pdf'),
    path('shared/get/<identifier>/<revision>', share_views.Serve.as_view(), name='serve_shared_pdf'),
    path('shared/get_qrcode/<identifier>', share_views.ServeQrCode.as_view(), name='serve_qrcode'),
    path('shared/download_qrcode/<identifier>', share_views.DownloadQrCode.as_view(), name='download_qrcode'),
    path('shared/<identifier>', share_views.ViewShared.as_view(), name='view_shared_pdf'),
    # tag related views
    path('delete_tag/', pdf_views.DeleteTag.as_view(), name='delete_tag'),
    path('edit_tag/', pdf_views.EditTag.as_view(), name='edit_tag'),
]
