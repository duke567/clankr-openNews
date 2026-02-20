from django.urls import path, include
from .views import sign_up, log_in, welcome

urlpatterns = [
    path("signup/", sign_up, name="signup"),
    path("login/", log_in, name="login"),
    path("welcome/", welcome, name="welcome"),
]