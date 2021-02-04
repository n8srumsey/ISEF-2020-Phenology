from datetime import datetime

import pytz
from django import template
import logging

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


@register.simple_tag
def imgname_to_datetime(imgname):
    date_time_list = imgname.split('_')
    del date_time_list[0]
    try: 
        del date_time_list[4]
    except: 
        pass
    hrminsec = date_time_list[3]
    date_time_list[3] = hrminsec[:2]
    date_time_list.append(hrminsec[2:4])
    date_time_list.append(hrminsec[4:])
    date_time_list = [int(i) for i in date_time_list]
    date_time = datetime(year=date_time_list[0], month=date_time_list[1], day=date_time_list[2], hour=date_time_list[3],
                         minute=date_time_list[4], second=date_time_list[5], tzinfo=pytz.timezone('UTC'))
    return date_time.strftime("%m/%d/%Y  %H:%M:%S")
