from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_page, name='login_page'),
    path('api/login.php', views.login_api, name='login_api'),
    path('api/register.php', views.register_api, name='register_api'),
    path('api/logout.php', views.logout_view, name='logout_api'),
    path('api/session_status.php', views.session_status_api, name='session_status_api'),
]
