from django import forms
from django.forms.fields import IntegerField

class SiteForm(forms.Form):
    sitename = forms.CharField(label='Site Name', max_length=50)
    location_desc = forms.CharField(label='Location', max_length=500)
    latitude = forms.FloatField(label='Latitude')
    longitude = forms.FloatField(label='Longitude')  
    elevation = forms.IntegerField(label = 'Elevation')
    dominant_species = forms.CharField(label='Dominant Species', max_length=1000, required=False)
  