from rest_framework import serializers
from .models import Site, Image, TransitionDate

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id', 'image_upload', 'date_time', 'is_rising', 'obj_created', 'last_updated')

class TransitionDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransitionDate
        fields = ('id', 'date_time', 'falling_to_rising', 'obj_created', 'last_updated')

class SiteSerializer(serializers.ModelSerializer):
    transition_dates = TransitionDateSerializer(source='transitiondate_set', many=True)
    images = ImageSerializer(source='image_set', many=True)
    class Meta:
        model = Site
        fields = ('id', 'sitename', 'longname', 'obj_created', 'last_updated', 
                    'transition_dates', 'images')