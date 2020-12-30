from django.db import models

# Create your models here.
class Site(models.Model):
    sitename = models.CharField(max_length=50)
    longname = models.CharField(max_length=500)
    obj_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sitename

class Image(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    image_upload = models.ImageField(max_length=200)
    date_time = models.DateTimeField()
    is_rising = models.BooleanField()
    obj_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.image_upload.name

class TransitionDate(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    falling_to_rising = models.BooleanField()
    obj_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return str(self.date)