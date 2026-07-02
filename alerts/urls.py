"""
alerts/urls.py
--------------
URL patterns for the alerts app.
Currently only one route: the main alert list at the site root.
"""

from django.urls import path
from . import views

app_name = 'alerts'   # namespace so we can use {% url 'alerts:list' %} in templates

urlpatterns = [
    # '/'  →  alert_list view
    path('', views.alert_list, name='list'),
    path("lightcurve/<str:object_id>/", views.object_view, name="lightcurve")
]
