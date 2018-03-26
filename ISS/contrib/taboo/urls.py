from django.conf.urls import url

import views

urlpatterns = [
    url(r'^status$', views.Status.as_view(), name='taboo-status'),
    url(r'^register$', views.Register.as_view(), name='taboo-register'),
    url(r'^unregister$', views.Unregister.as_view(), name='taboo-unregister'),
    url(r'^leader-board$', views.leader_board, name='taboo-leader-board')
]
