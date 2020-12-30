from django.contrib import admin
from .models import Site, TransitionDate, Image


class SiteAdmin(admin.ModelAdmin):
    fields = ['sitename', 'longname']

class TransitionDateAdmin(admin.ModelAdmin):
    fields = ['site',  'date_time', 'falling_to_rising']

class ImageAdmin(admin.ModelAdmin):
    fields = ['site', 'image_upload', 'date_time', 'is_rising']

# Register your models here.
admin.site.register(Site, SiteAdmin)
admin.site.register(TransitionDate, TransitionDateAdmin)
admin.site.register(Image, ImageAdmin)