from django import template
from django.forms.fields import RegexField

register = template.Library()

@register.simple_tag
def mult_neg_one(value):
    return value * -1

@register.simple_tag
def get_last_image_date(site):
    image = site.image_set.order_by('date_time').last()
    return image.date_time.strftime("%m/%d/%Y")
    
@register.simple_tag
def get_first_image_date(site):
    image = site.image_set.order_by('date_time').first()
    return image.date_time.strftime("%m/%d/%Y")
    
@register.simple_tag
def site_last_updated_str(site):
    return site.last_updated.strftime("%m/%d/%Y, %H:%M:%S")

@register.simple_tag
def get_num_site_imgs(site):
    return site.image_set.all().count() - 1

@register.simple_tag
def get_first_datetime(site):
    return site.image_set.order_by('date_time').first().date_time.strftime("%m/%d/%Y, %H:%M:%S")
