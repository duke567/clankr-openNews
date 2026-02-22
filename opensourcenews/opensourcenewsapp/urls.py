from django.urls import path
from .views import (
    api_auth_csrf,
    api_auth_login,
    api_auth_logout,
    api_auth_me,
    api_auth_register,
    sign_up,
    log_in,
    welcome,
    ingest_scrape,
)

urlpatterns = [
    path("signup/", sign_up, name="signup"),
    path("login/", log_in, name="login"),
    path("welcome/", welcome, name="welcome"),
    path("api/auth/csrf/", api_auth_csrf, name="api_auth_csrf"),
    path("api/auth/login/", api_auth_login, name="api_auth_login"),
    path("api/auth/register/", api_auth_register, name="api_auth_register"),
    path("api/auth/me/", api_auth_me, name="api_auth_me"),
    path("api/auth/logout/", api_auth_logout, name="api_auth_logout"),
    path("api/ingest-scrape/", ingest_scrape, name="ingest_scrape"),
]
