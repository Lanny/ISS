from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^status$', views.Status.as_view(), name='taboo-status'),
    re_path(r'^register$', views.Register.as_view(), name='taboo-register'),
    re_path(r'^unregister$', views.Unregister.as_view(), name='taboo-unregister'),
    re_path(r'^leader-board$', views.leader_board, name='taboo-leader-board')
]
