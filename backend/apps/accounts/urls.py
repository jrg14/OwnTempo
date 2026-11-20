from django.urls import path

from .views import CurrentUserView, csrf, login, logout

app_name = "accounts"

urlpatterns = [
    path("auth/csrf/", csrf, name="csrf"),
    path("auth/login/", login, name="login"),
    path("auth/logout/", logout, name="logout"),
    path("account/me/", CurrentUserView.as_view(), name="current-user"),
]
