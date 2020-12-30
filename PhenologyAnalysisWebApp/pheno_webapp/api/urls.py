from django.urls import path
from .views import SiteView

urlpatterns = [
    path('', SiteView.as_view())
]