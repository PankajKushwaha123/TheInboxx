from django.urls import include, path, re_path
from . import views

urlpatterns = [
    path('', views.home),
    path('get_emails', views.get_emails),
    path('create_inbox', views.create_inbox),
    path('delete_inbox', views.delete_inbox),
    path('delete_email', views.delete_email),
]