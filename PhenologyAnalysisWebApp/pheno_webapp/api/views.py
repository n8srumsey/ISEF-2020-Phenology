from django.shortcuts import render
from rest_framework import generics
from .serializers import SiteSerializer
from .models import Site, Image, TransitionDate

# Create your views here.
class SiteView(generics.CreateAPIView):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer