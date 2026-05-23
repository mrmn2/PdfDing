from django.urls import include, path
from rest_framework.routers import SimpleRouter
from users import views
from users.api import TokenViewSet

router = SimpleRouter()
router.register('token', TokenViewSet, basename='token')

urlpatterns = [
    path('account_settings', views.account_settings, name="account_settings"),
    path('access_token', views.access_token_settings, name="access_token"),
    path('danger_settings', views.danger_settings, name="danger_settings"),
    path('ui_settings', views.ui_settings, name="ui_settings"),
    path('viewer_settings', views.viewer_settings, name="viewer_settings"),
    path('delete', views.Delete.as_view(), name="profile-delete"),
    path('change_setting/<field_name>', views.ChangeSetting.as_view(), name="profile-setting-change"),
    path('create_demo_user', views.CreateDemoUser.as_view(), name="create_demo_user"),
    path('change_layout/<layout>', views.ChangeLayout.as_view(), name="change_layout"),
    path('change_sorting/<sorting_category>/<sorting>', views.ChangeSorting.as_view(), name="change_sorting"),
    path('change_tree_mode', views.ChangeTreeMode.as_view(), name="change_tree_mode"),
    path('change_workspace/<workspace_id>', views.ChangeWorkspace.as_view(), name="change_workspace"),
    path('change_collection/<collection_id>', views.ChangeCollection.as_view(), name="change_collection"),
    path('open_collapse_tags', views.OpenCollapseTags.as_view(), name="open_collapse_tags"),
    path('signatures', views.Signatures.as_view(), name="signatures"),
    path('', include(router.urls)),
]
