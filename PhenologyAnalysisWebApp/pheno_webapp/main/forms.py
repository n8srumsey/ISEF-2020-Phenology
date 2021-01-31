from django import forms

class SiteForm(forms.Form):
    sitename = forms.CharField(label='Site Name', max_length=50)
    location_desc = forms.CharField(label='Location', max_length=500)
    latitude = forms.FloatField(label='Latitude')
    longitude = forms.FloatField(label='Longitude')   