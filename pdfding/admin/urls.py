from admin import views
from django.urls import path

urlpatterns = [
    path('users', views.Overview.as_view(), name='user_overview'),
    path('info', views.Information.as_view(), name='instance_info'),
    path('query/', views.OverviewQuery.as_view(), name='user_overview_query'),
    path('get_next_overview_page/<int:page>/', views.Overview.as_view(), name='get_next_user_overview_page'),
    path('rights/<identifier>', views.AdjustAdminRights.as_view(), name='admin_adjust_rights'),
    path('delete/<identifier>', views.DeleteProfile.as_view(), name='admin_delete_profile'),
]
