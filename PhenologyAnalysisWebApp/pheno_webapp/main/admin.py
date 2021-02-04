from django.contrib import admin
from .models import Site, Image, TransitionDate

# Register your models here.
admin.site.register(Site)
admin.site.register(Image)
admin.site.register(TransitionDate)