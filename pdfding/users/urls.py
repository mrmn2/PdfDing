from django.urls import path
from users.views import ChangeSetting, CreateDemoUser, Delete, settings

urlpatterns = [
    path('settings', settings, name="profile-settings"),
    path('delete', Delete.as_view(), name="profile-delete"),
    path('change_setting/<field_name>', ChangeSetting.as_view(), name="profile-setting-change"),
    path('create_demo_user', CreateDemoUser.as_view(), name="create_demo_user"),
]
