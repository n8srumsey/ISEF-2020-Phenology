from django.http.response import HttpResponseRedirect
from django.shortcuts import render
from .models import Site, Image, TransitionDate
from .forms import CreateNewSite

from datetime import datetime

# Create your views here.
def home(response):
    context = {}
    return render(response, 'main/home.html', context)

def data_management(response):
    most_recent_sites = Site.objects.order_by('-last_updated')[:5]
    context = {'most_recent': most_recent_sites}
    return render(response, 'main/data_management.html', context)

def sites(response):
    all_sites = Site.objects.all().order_by('sitename')
    most_recent_sites = Site.objects.order_by('-last_updated')[:5]
    context = {'sites': all_sites, 'most_recent': most_recent_sites}
    return render(response, 'main/site_list.html', context)

def site_add(response):
    if response.method == 'POST':
        form=CreateNewSite(response.POST)
        if form.is_valid() and 'save_leave' in response.POST:
            stnm = form.cleaned_data['sitename']
            loc = form.cleaned_data['location_desc']
            s = Site(sitename=stnm, location_desc=loc)
            s.save()
            return HttpResponseRedirect('/data-management/sites/')
        if form.is_valid() and 'save_add_more' in response.POST:
            stnm = form.cleaned_data['sitename']
            loc = form.cleaned_data['location_desc']
            s = Site(sitename=stnm, location_desc=loc)
            s.save()
            form = CreateNewSite()
    else:
        form = CreateNewSite()

    most_recent_sites = Site.objects.order_by('-last_updated')[:5]
    context = {'form': form, 'most_recent': most_recent_sites}
    return render(response, 'main/site_add.html', context)

def site_view(response, sitename):
    site = Site.objects.all().filter(sitename=sitename)[0]
    most_recent_sites = Site.objects.order_by('-last_updated')[:5]
    context = {'site': site, 'most_recent': most_recent_sites}
    return render(response, 'main/site_view.html', context)

def site_gallery(response, sitename):
    site = Site.objects.all().filter(sitename=sitename)[0]
    images = 0 # figure out later
    context = {'site': site, 'images': images}
    return render(response, 'main/site_image_gallery.html', context)

def individual_image_view(response, sitename, imagename):
    site = Site.objects.all().filter(sitename=sitename)[0]
    image = 0 # figure out later
    context = {'site': site, 'image': image}
    return render(response, 'main/image_individual_view.html', context)

def upload_images(response):
    if response.method == 'POST':
        post = response.POST
        uploads = response.FILES
        # check if files were uploaded
        sitename = post['site_selected']
        images = response.FILES.getlist('images')
        for image in images:
            date_time_list = image.name.split('_')
            del date_time_list[0]
            hrminsec = date_time_list[3]
            date_time_list[3] = hrminsec[:2]
            date_time_list.append(hrminsec[2:4])
            date_time_list.append(hrminsec[4:])
            date_time_list[-1] = date_time_list[-1].split('.')[0]
            date_time_list = [int(i) for i in date_time_list]
            date_time = datetime(date_time_list[0], date_time_list[1], date_time_list[2],
                                 date_time_list[3], date_time_list[4], date_time_list[5], 0)
            # run tensorflow model - DO NOT FORGET ABOUT THIS!!!!
            i = Image(site=Site.objects.get(sitename=sitename), date_time=date_time, is_rising=False, image_upload=image)
            i.save()
        # return HttpResponseRedirect('/data-management/sites/{site}/'.format(site = sitename))
        return HttpResponseRedirect('#')
    
    all_sites = Site.objects.all().order_by('sitename')
    most_recent_sites = Site.objects.order_by('-last_updated')[:5]
    sitenames = [str(site.sitename) for site in all_sites]
    context = {'sites': sitenames, 'most_recent': most_recent_sites}
    return render(response, 'main/upload_images.html', context)

def analysis(response):
    context = {}
    return render(response, 'main/analysis_home.html', context)

def analysis_site(response, sitename):
    context = {'sitename': sitename}
    return render(response, 'main/analysis_site.html', context)