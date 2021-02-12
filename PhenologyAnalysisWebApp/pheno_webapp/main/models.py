from django.db import models

# Create your models here.
class Site(models.Model):
    sitename = models.CharField(max_length=50, unique=True)
    location_desc = models.CharField(max_length=500)
    obj_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    elevation = models.IntegerField(default=0)
    dominant_species = models.CharField(max_length=1000, default='')


    def __str__(self):
        return self.sitename

class Image(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    date_time = models.DateTimeField(unique=True)
    is_rising = models.BooleanField()
    obj_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)   
    image_upload = models.ImageField(upload_to='images/')
    
    def __str__(self):
        return self.image_upload.name

class TransitionDate(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    rising_phase = models.BooleanField()
    duration = models.IntegerField(default=0, null=True)    
    
    def __str__(self):
        if self.rising_phase: return 'Rising Phase - Starts At {}'.format(self.date_time.strftime("%m/%d/%Y"))
        else: return 'Falling Phase - Starts At {}'.format(self.date_time.strftime("%m/%d/%Y"))