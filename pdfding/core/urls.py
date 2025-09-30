"""
URL configuration for pdfding project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from rest_framework.routers import DefaultRouter
from core.views import HealthView, SupportView
from django.urls import include, path
from pdf.views.pdf_views import redirect_to_overview
from pdfding.api_auth.views import AccessTokenViewSet
from users.views import (
    PdfDingLoginView,
    PdfDingPasswordResetDoneView,
    PdfDingPasswordResetView,
    PdfDingSignupView,
    pdfding_oidc_callback,
    pdfding_oidc_login,
)

urlpatterns = [
    # overwrite some allauth urls as they are blocked otherwise because of the LoginRequiredMiddleware
    path('accountlogin/', PdfDingLoginView.as_view(), name='login'),
    path('accountsignup/', PdfDingSignupView.as_view(), name='signup'),
    path('accountpassword/reset/', PdfDingPasswordResetView.as_view(), name='password_reset'),
    path('accountpassword/reset/done/', PdfDingPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accountoidc/login/', pdfding_oidc_login, name='oidc_login'),
    path('accountoidc/login/callback/', pdfding_oidc_callback, name='oidc_callback'),
    # normal inc
    path('admin/', include('admin.urls')),
    path('account', include('allauth.urls')),
    path('', redirect_to_overview, name='home'),
    path('profile/', include('users.urls')),
    path('pdf/', include('pdf.urls')),
    path('healthz', HealthView.as_view(), name='healthz'),
    path('support', SupportView.as_view(), name='support'),
]


router = DefaultRouter()
router.register(prefix="tokens", viewset=AccessTokenViewSet, basename="api_tokens")

urlpatterns += [
    path("api/", include(router.urls)),
]
