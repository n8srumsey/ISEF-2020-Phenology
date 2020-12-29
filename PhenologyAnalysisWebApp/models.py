from django.db import models

# Create your models here.
class Site(models.Model):
    sitename = models.CharField(max_length=50)
    long_name = models.CharField(max_length=500)

    def __str__(self):
        return self.sitename

class Image(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, name='site')
    image_upload = models.ImageField(max_length=200, name='image_upload')
    date_time = models.DateTimeField(name='date_time')
    is_rising = models.BooleanField(name='is_rising')

    def __str__(self):
        return self.image_upload.name

class TransitionDate(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, name='site')
    date = models.DateField(name='date')
    falling_to_rising = models.BooleanField(name='falling_to_rising')
    
    def __str__(self):
        return str(self.date)