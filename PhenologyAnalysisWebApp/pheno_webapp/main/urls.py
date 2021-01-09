from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'), 
    path('data-management/', views.data_management, name='data_management'),
    path('data-management/sites/', views.sites, name='sites'),
    path('data-management/sites/add/', views.site_add, name='add_site'), 
    path('data-management/sites/<str:sitename>/', views.site_view, name='site_view'),
    path('data-management/sites/<str:sitename>/gallery/', views.site_gallery, name='site_gallery'),
    path('data-management/sites/<str:sitename>/<str:imagename>/', views.individual_image_view, name='individual_image_view'),
    path('data-management/upload_images/', views.upload_images, name='upload_images'),
    path('analysis/', views.analysis, name='analysis'),
    path('analysis/<str:sitename>', views.analysis_site, name='analysis-site'),
]
