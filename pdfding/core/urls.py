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

from core.views import HealthView
from django.urls import include, path
from pdf.views.pdf_views import redirect_to_overview
from users.views import (
    PdfDingLoginView,
    PdfDingPasswordResetDoneView,
    PdfDingPasswordResetView,
    PdfDingSignupView,
    pdfding_oidc_callback,
    pdfding_oidc_login,
)

from pdfding.api.views import AccessTokenView

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
]

# API URLs
urlpatterns += [
    path('api/token/<int:pk>/', AccessTokenView.as_view(), name='api_token_detail'),
]
