from django import forms
from .models import Site

class CreateNewSite(forms.Form):
    sitename = forms.CharField(label='Site Name', max_length=50)
    location_desc = forms.CharField(label='Location', max_length=500)
