import copy
import json
import os
from datetime import datetime, timedelta
import csv

import pytz
from django.db.models.functions import Lower
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from .forms import SiteForm
from .models import Image, Site, TransitionDate


def is_rising(sitename, date_time):
    # method, given input of img_file, output boolean indicating if rising or falling
    if date_time.month in [12, 1, 2, 3]:
        return False
    elif date_time.month in [6, 7, 8]:
        return True

    # load json transition dates file
    module_dir = os.path.dirname(__file__)  # get current directory
    file_path = os.path.join(module_dir, 'static/transition_dates/{}_transition_dates.json'.format(sitename))
    with open(file_path, 'r') as f:
        site_transitions = json.load(f)['transitions']

    # find closest
    distances = []
    for i in range(len(site_transitions)):
        trans_date = datetime(site_transitions[i]['year'], site_transitions[i]['month'], site_transitions[i]['day'], tzinfo=pytz.timezone('UTC'))
        distance = date_time - trans_date
        abs_distance = abs(distance)
        distances.append((i, distance, abs_distance))

    closest = min(distances, key=lambda x: x[2])
    if site_transitions[closest[0]]['rising']:
        return closest[1] >= timedelta()
    else:
        return closest[1] < timedelta()


def transition_dates_on_site_update(site, based_off_images=False):
    # delete all previous transition dates
    site.transitiondate_set.all().delete()

    if based_off_images:
        # get list of is_rising booleans
        images = site.image_set.order_by('date_time')
        rising_bools = [im.is_rising for im in images]

        def calc_changes(rising_bools):
            phase = rising_bools[0]
            prev_i = 0
            changes = []  # contains (pos, start_of_section_w_bool, len)
            for i in range(len(rising_bools)):
                if rising_bools[i] != phase:
                    changes.append({'pos': prev_i, 'phase': phase, 'len': i - prev_i})

                    phase = not phase
                    prev_i = i
            changes.append({'pos': prev_i, 'phase': phase, 'len': len(rising_bools) - prev_i})
            return changes

        def remove_noise(rising_bools, ):
            # calculate all transitions, including noise
            """eliminate noise"""
            # remove tiny blips
            min_len = 62
            for x in [j+2 for j in range(min_len+2)]:
                changes = calc_changes(rising_bools)
                for change in changes:
                    if change['len'] < x:
                        for i in range(change['len']):
                            rising_bools[change['pos'] + i] = not rising_bools[change['pos'] + i]
            return rising_bools

        processed_rising_bools = remove_noise(rising_bools)

        # go from indecies to transition dates
        transitions = calc_changes(processed_rising_bools)
        for i in range(len(transitions)):
            date_time = images[transitions[i]['pos']].date_time
            t = TransitionDate(site=site, date_time=date_time, rising_phase=transitions[i]['phase'], duration=transitions[i]['len'])
            if (i == 0) or (i == len(transitions)-1):
                t = TransitionDate(site=site, date_time=date_time, rising_phase=transitions[i]['phase'], duration=None)
            elif date_time - images[transitions[i]['pos']-1].date_time > timedelta(days=31):
                t = TransitionDate(site=site, date_time=date_time, rising_phase=transitions[i]['phase'], duration=None)
            elif transitions[i]['len'] < 30:
                t = TransitionDate(site=site, date_time=date_time, rising_phase=transitions[i]['phase'], duration=None)
            t.save()

        tdates = site.transitiondate_set.order_by('date_time')
        reference = tdates[0]
        for tdate in tdates[1:]:
            tdelta = tdate.date_time - reference.date_time
            days = int(tdelta.total_seconds() / 86400)
            if days > 280:  # remove large gaps
                days = None
            reference.duration = days
            reference.save()
            reference = tdate

        # fix image is_rising fields according to transition dates
        for i in range(len(processed_rising_bools)):
            images[i].is_rising = processed_rising_bools[i]
            images[i].save
    else:
        # load json transition dates file
        module_dir = os.path.dirname(__file__)  # get current directory
        file_path = os.path.join(module_dir, 'static/transition_dates/{}_transition_dates.json'.format(site.sitename))
        with open(file_path, 'r') as f:
            transitions = json.load(f)['transitions']
        transitions.sort(key=lambda x: datetime(x['year'], x['month'], x['day'], tzinfo=pytz.timezone('UTC')))
        for i in range(len(transitions)):
            date_time = datetime(transitions[i]['year'], transitions[i]['month'], transitions[i]['day'], tzinfo=pytz.timezone('UTC'))
            rising_phase = transitions[i]['rising']

            t = TransitionDate(site=site, date_time=date_time, rising_phase=rising_phase, duration=None)
            if (i == 0) or (i == len(transitions)-1):
                t = TransitionDate(site=site, date_time=date_time, rising_phase=rising_phase, duration=None)
            t.save()

        tdates = site.transitiondate_set.order_by('date_time')
        reference = tdates[0]
        for tdate in tdates[1:]:
            tdelta = tdate.date_time - reference.date_time
            days = int(tdelta.total_seconds() / 86400)
            if days > 280 or days < 95:  # remove large gaps
                days = None
            reference.duration = days
            reference.save()
            reference = tdate


def save_images(images, sitename):
    site = Site.objects.get(sitename=sitename)
    for image in images:
        date_time_list = image.name.split('_')
        del date_time_list[0]
        hrminsec = date_time_list[3]
        date_time_list[3] = hrminsec[:2]
        date_time_list.append(hrminsec[2:4])
        date_time_list.append(hrminsec[4:])
        date_time_list[-1] = date_time_list[-1].split('.')[0]
        date_time_list = [int(i) for i in date_time_list]
        date_time = datetime(date_time_list[0], date_time_list[1], date_time_list[2], date_time_list[3],
                             date_time_list[4], date_time_list[5], 0, tzinfo=pytz.timezone('UTC'))
        # run tensorflow model - DO NOT FORGET ABOUT THIS!!!!
        try:
            i = Image(site=site, date_time=date_time, is_rising=is_rising(sitename, date_time), image_upload=image)
            i.save()
        except:
            pass

    transition_dates_on_site_update(site)


# Create your views here.
def home(response):
    context = {}
    return render(response, 'main/home.html', context)


def settings(response):
    if response.method == 'POST':
        if 'delete_all_images' in response.POST:
            Image.objects.all().delete()
    sites = Site.objects.order_by(Lower('sitename'))
    context = {'sites': sites}
    return render(response, 'main/settings.html', context)


def data_management(response):
    context = {}
    return render(response, 'main/data_management.html', context)


def sites(response):
    if response.method == 'POST':
        post = response.POST
        sitename = post['site_selected']
        return HttpResponseRedirect('{}/'.format(sitename))
    all_sites = Site.objects.all().order_by(Lower('sitename'))
    context = {'sites': all_sites}
    return render(response, 'main/site_list.html', context)


def site_add(response):
    if response.method == 'POST':
        form = SiteForm(response.POST)
        if form.is_valid() and 'save_leave' in response.POST:
            stnm = form.cleaned_data['sitename']
            loc = form.cleaned_data['location']
            lat = form.cleaned_data['latitude']
            long = form.cleaned_data['longitude']
            elev = form.cleaned_data['elevation']
            dominant_species = form.cleaned_data['dominant_species']
            s = Site(sitename=stnm, location_desc=loc, latitude=lat, longitude=long, elevation=elev, dominant_species=dominant_species)
            s.save()
            sitename = s.sitename
            images = response.FILES.getlist('images')
            save_images(images, sitename)
            return HttpResponseRedirect('/data-management/sites/')
        if form.is_valid() and 'save_add_more' in response.POST:
            stnm = form.cleaned_data['sitename']
            loc = form.cleaned_data['location']
            lat = form.cleaned_data['latitude']
            long = form.cleaned_data['longitude']
            s = Site(sitename=stnm, location_desc=loc, latitude=lat, longitude=long,  elevation=elev, dominant_species=dominant_species)
            s.save()
            sitename = s.sitename
            images = response.FILES.getlist('images')
            save_images(images, sitename)

    context = {}
    return render(response, 'main/site_add.html', context)


def site_view(response, sitename):
    site = Site.objects.all().filter(sitename=sitename)[0]
    dates = [img.date_time.strftime("%m/%d/%Y, %H:%M:%S") for img in site.image_set.order_by('date_time')]
    img_paths = [str(img.image_upload.name) for img in site.image_set.order_by('date_time')]
    context = {'site': site, 'date_list': dates, 'img_paths': img_paths}
    return render(response, 'main/site_view.html', context)


def site_view_edit(response, sitename):
    site = get_object_or_404(Site, sitename=sitename)
    if response.method == 'POST':
        form = SiteForm(response.POST)
        if form.is_valid():
            site.sitename = form.cleaned_data['sitename']
            site.location_desc = form.cleaned_data['location']
            site.latitude = form.cleaned_data['latitude']
            site.longitude = form.cleaned_data['longitude']
            site.elevation = form.cleaned_data['elevation']
            site.dominant_species = form.cleaned_data['dominant_species']
            site.save()
            return HttpResponseRedirect('/data-management/sites/{}/'.format(site.sitename))
    else:
        form = SiteForm(initial={'sitename': site.sitename, 'location_desc': site.location_desc, 'latitude': site.latitude, 
                                 'longitude': site.longitude, 'elevation': site.elevation, 'dominant_species': site.dominant_species})

    dates = [img.date_time.strftime("%m/%d/%Y, %H:%M:%S") for img in site.image_set.order_by('date_time')]
    img_paths = [str(img.image_upload.name) for img in site.image_set.order_by('date_time')]
    context = {'site': site, 'date_list': dates, 'img_paths': img_paths, 'form': form}
    return render(response, 'main/site_view_edit.html', context)


def site_gallery(response, sitename):
    site = Site.objects.all().filter(sitename=sitename)[0]
    images = site.image_set.order_by('date_time')
    context = {'site': site, 'images': images}
    return render(response, 'main/site_image_gallery.html', context)


def individual_image_view(response, sitename, imagename):
    site = Site.objects.all().filter(sitename=sitename)[0]
    image = [im for im in site.image_set.filter() if imagename in im.image_upload.name][0]
    context = {'site': site, 'image': image}
    return render(response, 'main/image_individual_view.html', context)


def upload_images(response):
    if response.method == 'POST':
        post = response.POST
        # check if files were uploaded
        sitename = post['site_selected']
        images = response.FILES.getlist('images')
        save_images(images, sitename)
        # return HttpResponseRedirect('/data-management/sites/{site}/'.format(site = sitename))
        return HttpResponseRedirect('#')

    all_sites = Site.objects.all().order_by(Lower('sitename'))
    sitenames = [str(site.sitename) for site in all_sites]
    context = {'sites': sitenames}
    return render(response, 'main/upload_images.html', context)


def analysis(response):
    if response.method == 'POST':
        post = response.POST
        sitename = post['site_selected']
        return HttpResponseRedirect('/analysis/{}/'.format(sitename))

    all_sites = Site.objects.all().order_by(Lower('sitename'))
    sitenames = [str(site.sitename) for site in all_sites]
    context = {'sites': sitenames}
    return render(response, 'main/analysis_home.html', context)


def analysis_site(response, sitename):
    if response.method == 'POST':
        post = response.POST
        sitename = post['site_selected']
        return HttpResponseRedirect('/analysis/{}/'.format(sitename))
    site = Site.objects.get(sitename=sitename)
    transition_dates_on_site_update(site)
    all_sites = Site.objects.all().order_by(Lower('sitename'))
    sitenames = [str(site.sitename) for site in all_sites]

    def get_phase_data(site):
        rising_transition_dates = site.transitiondate_set.filter(rising_phase__exact=True).order_by('date_time')
        falling_transition_dates = site.transitiondate_set.filter(rising_phase__exact=False).order_by('date_time')
        rising_phases = []
        falling_phases = []
        for i in range(max([rising_transition_dates.count(), falling_transition_dates.count()])):
            try:
                rising_phase = rising_transition_dates[i]
                if rising_phase.date_time.day < 10:
                    rising_phases.append({'year': rising_phase.date_time.year, 'year_month_day': '0{}/0{}/{}'.format(rising_phase.date_time.month, rising_phase.date_time.day, rising_phase.date_time.year),
                                          'month': rising_phase.date_time.month, 'day': rising_phase.date_time.day, 'duration': rising_phase.duration, 'percent_change': None})
                else:
                    rising_phases.append({'year': rising_phase.date_time.year, 'year_month_day': '0{}/{}/{}'.format(rising_phase.date_time.month, rising_phase.date_time.day, rising_phase.date_time.year),
                                          'month': rising_phase.date_time.month, 'day': rising_phase.date_time.day, 'duration': rising_phase.duration, 'percent_change': None})
            except:
                pass
            try:
                falling_phase = falling_transition_dates[i]
                if falling_phase.date_time.day < 10:
                    falling_phases.append({'year': falling_phase.date_time.year, 'year_month_day': '{}/0{}/{}'.format(falling_phase.date_time.month, falling_phase.date_time.day, falling_phase.date_time.year),
                                           'month': falling_phase.date_time.month, 'day': falling_phase.date_time.day, 'duration': falling_phase.duration, 'percent_change': None})
                else:
                    falling_phases.append({'year': falling_phase.date_time.year, 'year_month_day': '{}/{}/{}'.format(falling_phase.date_time.month, falling_phase.date_time.day, falling_phase.date_time.year),
                                           'month': falling_phase.date_time.month, 'day': falling_phase.date_time.day, 'duration': falling_phase.duration, 'percent_change': None})
            except:
                pass
        min_year = 0
        max_year = 0
        if len(rising_phases) != 0 and len(falling_phases) != 0:
            min_year = min([rising_phases[0]['year'], falling_phases[0]['year']])
            max_year = max([rising_phases[-1]['year'], falling_phases[-1]['year']])
        elif len(rising_phases) == 0:
            min_year = falling_phases[0]['year']
            max_year = falling_phases[-1]['year']
        elif len(falling_phases) == 0:
            min_year = rising_phases[0]['year']
            max_year = rising_phases[-1]['year']

        tdates_by_yr = []
        for yr in range(min_year, max_year+1):
            rising = None
            for rsng in rising_phases:
                if yr == rsng['year'] and rsng['duration'] != None:
                    rising = rsng
            falling = None
            for fllng in falling_phases:
                if yr == fllng['year'] and fllng['duration'] != None:
                    falling = fllng
            tdates_by_yr.append((rising, falling))

        tdates = []
        for rising_phase, falling_phase in tdates_by_yr:
            row = [None, None]
            try:
                row[0] = rising_phase
            except:
                pass
            try:
                row[1] = falling_phase
            except:
                pass
            tdates.append(row)

        # calculate % change in duration
        for i in range(len(tdates)):
            for j in range(len(tdates[i])):
                if tdates[i][j] != None and i != 0:
                    try:
                        percent_change = float(tdates[i][j]['duration'] - tdates[i-1][j]['duration']) / (0.01 * tdates[i-1][j]['duration'])
                        tdates[i][j]['percent_change'] = percent_change
                    except:
                        pass
                    if tdates[i][j]['percent_change'] is None:
                        tdates[1][j]['percent_change'] = 'null'
                elif tdates[i][j] != None and i == 0:
                    tdates[i][j]['percent_change'] = 'null'

        # replace null with default dict
        pad_tdates = copy.deepcopy(tdates)
        for i in range(len((pad_tdates))):
            for j in range(len(pad_tdates[i])):
                if pad_tdates[i][j] is None:
                    pad_tdates[i][j] = {'year': i + min_year, 'year_month_day': None, 'month': None, 'day': None, 'duration': 0, 'percent_change': 'null'}
        return tdates, pad_tdates

    def get_phase_years(site):
        rising_transition_dates = site.transitiondate_set.filter(rising_phase__exact=True).order_by('date_time')
        falling_transition_dates = site.transitiondate_set.filter(rising_phase__exact=False).order_by('date_time')
        rising_phases = []
        falling_phases = []
        for i in range(max([rising_transition_dates.count(), falling_transition_dates.count()])):
            try:
                rising_phase = rising_transition_dates[i]
                # if rising_phase.duration is not None:
                rising_phases.append({'year': rising_phase.date_time.year, 'month_day': '{}/{}'.format(rising_phase.date_time.month, rising_phase.date_time.day),
                                      'duration': rising_phase.duration, 'percent_change': None})
            except:
                pass
            try:
                falling_phase = falling_transition_dates[i]
                # if falling_phase.duration is not None:
                falling_phases.append({'year': falling_phase.date_time.year, 'month_day': '{}/{}'.format(falling_phase.date_time.month, falling_phase.date_time.day),
                                       'duration': falling_phase.duration, 'percent_change': None})
            except:
                pass
        min_year = 0
        max_year = 0
        if len(rising_phases) != 0 and len(falling_phases) != 0:
            min_year = min([rising_phases[0]['year'], falling_phases[0]['year']])
            max_year = max([rising_phases[-1]['year'], falling_phases[-1]['year']])
        elif len(rising_phases) == 0:
            min_year = falling_phases[0]['year']
            max_year = falling_phases[-1]['year']
        elif len(falling_phases) == 0:
            min_year = rising_phases[0]['year']
            max_year = rising_phases[-1]['year']
        years = [yr for yr in range(min_year, max_year+1)]
        return years

    def get_transition_dates(site):
        rising_transition_dates = site.transitiondate_set.filter(rising_phase__exact=True).order_by('date_time')
        falling_transition_dates = site.transitiondate_set.filter(rising_phase__exact=False).order_by('date_time')
        rising_transitions = [r for r in rising_transition_dates]
        falling_transitions = [f for f in falling_transition_dates]

        min_year = 0
        max_year = 0
        if len(rising_transitions) != 0 and len(falling_transitions) != 0:
            min_year = min([rising_transitions[0].date_time.year, falling_transitions[0].date_time.year])
            max_year = max([rising_transitions[-1].date_time.year, falling_transitions[-1].date_time.year])
        elif len(rising_transitions) == 0:
            min_year = falling_transitions[0].date_time.year
            max_year = falling_transitions[-1].date_time.year
        elif len(falling_transitions) == 0:
            min_year = rising_transitions[0].date_time.year
            max_year = rising_transitions[-1].date_time.year
        years = [yr for yr in range(min_year, max_year+1)]

        rising_transitions_yearly = []
        falling_transitions_yearly = []
        for year in years:
            rising = None
            falling = None
            for transition in rising_transitions:
                try:
                    if transition.date_time.year == year:
                        rising = transition
                except:
                    pass
            for transition in falling_transitions:
                try:
                    if transition.date_time.year == year:
                        falling = transition
                except:
                    pass
            rising_transitions_yearly.append(rising)
            falling_transitions_yearly.append(falling)

        rising_years = copy.deepcopy(years)
        falling_years = copy.deepcopy(years)
        for i in range(len(years)):
            try:
                if rising_transitions_yearly[i] is None:
                    del rising_years[i]
                    del rising_transitions_yearly[i]
            except:
                pass
        for i in range(len(falling_years)):
            try:
                if falling_transitions_yearly[i] is None:
                    del falling_years[i]
                    del falling_transitions_yearly[i]
            except:
                pass
        r = [(x, y) for x, y in zip(rising_years, rising_transitions_yearly)]
        f = [(x, y) for x, y in zip(falling_years, falling_transitions_yearly)]

        return (rising_years, rising_transitions_yearly), (falling_years, falling_transitions_yearly), r, f

    phases, padded_phases = get_phase_data(site)
    _, _, r_data, f_data = get_transition_dates(site)

    dates = [img.date_time.strftime("%m/%d/%Y, %H:%M:%S") for img in site.image_set.order_by('date_time')]
    img_paths = [str(img.image_upload.name) for img in site.image_set.order_by('date_time')]
    phenophases = [img.is_rising for img in site.image_set.order_by('date_time')]

    context = {'sites': sitenames, 'site': site, 'phases': phases, 'padded_phases': padded_phases, 'use_spline': len(get_phase_years(site)) >= 3,
               'phase_years': get_phase_years(site), 'bud_burst_data': r_data, 'senescence_data': f_data, 'date_list': dates, 'img_paths': img_paths, 'phenophases': phenophases}
    return render(response, 'main/analysis_site.html', context)


def aggregate_analysis(response):
    """
        phenophase table
        ~~~~~~~~~~~~~~~~~
        list of data containing sets of each year
        each year set is dict with:
        - year
        - avg budburst month/day
        - avg budburst duration
        - avg senescence month/day
        - avg senescence duration
    """
    years = sorted(list(set([tdate.date_time.year for tdate in TransitionDate.objects.all()])))
    yearly_avg_budburst_monthdays = []
    for year in years:
        date_times = []
        for td in TransitionDate.objects.filter(rising_phase__exact=True):
            if td.date_time.year == year:
                date_times.append(td.date_time)
        try:
            avg = datetime.fromtimestamp(int(sum([datetime.timestamp(dt) for dt in date_times]) / len(date_times)))
            yearly_avg_budburst_monthdays.append(avg.strftime('%m/%d/%Y'))
        except:
            pass
    
    yearly_avg_budburst_durations = []
    for year in years:
        durations = [td.duration for td in TransitionDate.objects.filter(rising_phase__exact=True) if td.duration != None and td.date_time.year==year]
        avg = int(sum(durations) / len(durations))
        try: 
            yearly_avg_budburst_durations.append(avg)
        except: 
            pass
    
    yearly_avg_senescence_monthdays = []
    for year in years:
        date_times = []
        for td in TransitionDate.objects.filter(rising_phase__exact=False):
            if td.date_time.year == year:
                date_times.append(td.date_time)
        try:
            avg = datetime.fromtimestamp(int(sum([datetime.timestamp(dt) for dt in date_times]) / len(date_times)))
            yearly_avg_senescence_monthdays.append(avg.strftime('%m/%d/%Y'))
        except:
            pass

    yearly_avg_senescence_durations = []
    for year in years:
        durations = [td.duration for td in TransitionDate.objects.filter(rising_phase__exact=False) if td.duration != None and td.date_time.year==year]
        try: 
            avg = int(sum(durations) / len(durations))
            yearly_avg_senescence_durations.append(avg)
        except:
            yearly_avg_senescence_durations.append(None)

    table_data = []
    for i in range(len(years)):
        table_data.append({'year': years[i], 'bb_date': yearly_avg_budburst_monthdays[i], 'bb_dur': yearly_avg_budburst_durations[i], 
                           'ls_date': yearly_avg_senescence_monthdays[i], 'ls_dur':yearly_avg_senescence_durations[i]})

    """
        analysis graphs
        ~~~~~~~~~~~~~~~~~~~
        1. average budburst onset date from previous year (col 2, row 1)
        2. average senescence onset date from previous year (col 2, row 2)
        3. average budburst duration from prev year (col 1, row 3)
        4. average senescence duration from prev year (col 2, row 3)

        Data:
        - list of all years there are transition dates (int)
        - list of all average budburst onset datetimes (will be handeled js side)
        - list of all average budburst duration
        - list of all average senescence onset (will be handeled js side)
        - list of all average senescence duration differences 

        - list of [year, y-value pairings] for all of the above
    """
    
    yearly_avg_budburst_datetimes = []
    for year in years:
        date_times = []
        for td in TransitionDate.objects.filter(rising_phase__exact=True):
            if td.date_time.year == year:
                date_times.append(td.date_time)
        try:
            avg = datetime.fromtimestamp(int(sum([datetime.timestamp(dt) for dt in date_times]) / len(date_times)))
            yearly_avg_budburst_datetimes.append(avg)
        except:
            pass
    
    yearly_avg_senescence_datetimes = []
    for year in years:
        date_times = []
        for td in TransitionDate.objects.filter(rising_phase__exact=False):
            if td.date_time.year == year:
                date_times.append(td.date_time)
        try:
            avg = datetime.fromtimestamp(int(sum([datetime.timestamp(dt) for dt in date_times]) / len(date_times)))
            yearly_avg_senescence_datetimes.append(avg)
        except:
            pass

    budburst_onset_data = [[year, onset] for year, onset in zip(years, yearly_avg_budburst_datetimes)]

    senescence_onset_data = [[year, onset] for year, onset in zip(years, yearly_avg_senescence_datetimes)]

    budburst_duration_data = [[year, duration] for year, duration in zip(years, yearly_avg_budburst_durations)]

    senescence_duration_data = [[year, duration] for year, duration in zip(years, yearly_avg_senescence_durations)]
    
    
    context = {'table_data': table_data, 'years': years, 'budburst_avg_onset': yearly_avg_budburst_datetimes, 'budburst_avg_dur': yearly_avg_budburst_durations, 
               'senescence_avg_onset': yearly_avg_senescence_datetimes, 'senescence_avg_dur': yearly_avg_senescence_durations, 
               'budburst_onset_data': budburst_onset_data, 'budburst_dur_data': budburst_duration_data, 
               'senescence_onset_data': senescence_onset_data, 'senescence_dur_data': senescence_duration_data}
    return render(response, 'main/analysis_aggregate.html', context)


def site_map(response, view):
    str_formats = ['last_{PHASE}_tdate',
                   'last_{PHASE}_doy',
                   'last_{PHASE}_dur',

                   'avg_last3yrs_{PHASE}_tdate',
                   'avg_last3yrs_{PHASE}_doy',
                   'avg_last3yrs_{PHASE}_dur',

                   'avg_diff_yrly_{PHASE}_tdate',
                   'avg_diff_yrly_{PHASE}_dur',
                   'avg_diff_yrly_{PHASE}_dur_prcnt',

                   'diff_firstlast_{PHASE}_tdate',
                   'diff_firstlast_{PHASE}_dur',
                   'diff_firstlast_{PHASE}_dur_prcnt']

    constant_pairs = [['MIN_BUDBURST_RECENT_TDATE', 'MAX_BUDBURST_RECENT_TDATE'], ['MIN_SENESCENCE_RECENT_TDATE', 'MAX_SENESCENCE_RECENT_TDATE'],  # MOST RECENT
                      ['MIN_BUDBURST_RECENT_DOY', 'MAX_BUDBURST_RECENT_DOY'], ['MIN_SENESCENCE_RECENT_DOY', 'MAX_SENESCENCE_RECENT_DOY'],
                      ['MIN_BUDBURST_RECENT_DUR', 'MAX_BUDBURST_RECENT_DUR'], ['MIN_SENESCENCE_RECENT_DUR', 'MAX_SENESCENCE_RECENT_DUR'],  # END MOST RECENT

                      ['MIN_BUDBURST_AVG3YRS_TDATE', 'MAX_BUDBURST_AVG3YRS_TDATE'], 
                      ['MIN_SENESCENCE_AVG3YRS_TDATE', 'MAX_SENESCENCE_AVG3YRS_TDATE'],  # 3YR AVERAGE
                      ['MIN_BUDBURST_AVG3YRS_DOY', 'MAX_BUDBURST_AVG3YRS_DOY'], ['MIN_SENESCENCE_AVG3YRS_DOY', 'MAX_SENESCENCE_AVG3YRS_DOY'],
                      ['MIN_BUDBURST_AVG3YRS_DUR', 'MAX_BUDBURST_AVG3YRS_DUR'], ['MIN_SENESCENCE_AVG3YRS_DUR', 'MAX_SENESCENCE_AVG3YRS_DUR'],  # END 3YR AVERAGE

                      ['MIN_BUDBURST_AVG_DIFF_TDATE', 'MAX_BUDBURST_AVG_DIFF_TDATE'], 
                      ['MIN_SENESCENCE_AVG_DIFF_TDATE', 'MAX_SENESCENCE_AVG_DIFF_TDATE'],  # AVG DIFF
                      ['MIN_BUDBURST_AVG_DIFF_DUR', 'MAX_BUDBURST_AVG_DIFF_DUR'], ['MIN_SENESCENCE_AVG_DIFF_DUR', 'MAX_SENESCENCE_AVG_DIFF_DUR'],
                      ['MIN_BUDBURST_AVG_DIFF_DUR_PRCNT', 'MAX_BUDBURST_AVG_DIFF_DUR_PRCNT'], 
                      ['MIN_SENESCENCE_AVG_DIFF_DUR_PRCNT', 'MAX_SENESCENCE_AVG_DIFF_DUR_PRCNT'],  # END AVG DIF

                      ['MIN_BUDBURST_TOTAL_DIFF_DOY', 'MAX_BUDBURST_TOTAL_DIFF_DOY'], 
                      ['MIN_SENESCENCE_TOTAL_DIFF_DOY', 'MAX_SENESCENCE_TOTAL_DIFF_DOY'],  # TOTAL DIFF
                      ['MIN_BUDBURST_TOTAL_DIFF_DUR', 'MAX_BUDBURST_TOTAL_DIFF_DUR'], ['MIN_SENESCENCE_TOTAL_DIFF_DUR', 'MAX_SENESCENCE_TOTAL_DIFF_DUR'],
                      ['MIN_BUDBURST_TOTAL_DIFF_DUR_PRCNT', 'MAX_BUDBURST_TOTAL_DIFF_DUR_PRCNT'], ['MIN_SENESCENCE_TOTAL_DIFF_DUR_PRCNT', 'MAX_SENESCENCE_TOTAL_DIFF_DUR_PRCNT']]  # END TOTAL DIFF

    titles = ['Most Recent {PHASE} Onset Date', # most recent *complete* ...?
              'Most Recent {PHASE} Onset Date',
              'Most Recent {PHASE} Duration',

              'Three Year Average {PHASE} Onset Date',
              'Three Year Average {PHASE} Onset Date',
              'Three Year Average {PHASE} Duration',

              'Average Yearly Change in {PHASE} Onset Date', # move {PHASE} first??
              'Average Yearly Change in {PHASE} Duration',
              'Average Yearly Change in {PHASE} Duration',

              'Change in {PHASE} Onset Date Since First Year of Data',
              'Change in {PHASE} Duration Since First Year of Data',
              'Change in {PHASE} Duration Since First Year of Data']

    legend_descs = ['Earlier onset dates reflected by darker gradients and smaller circles',
                    'Earlier onset dates reflected by darker gradients and smaller circles',
                    'Lower phenophase durations reflected by darker gradients and smaller circles',

                    'Earlier onset dates reflected by darker gradients and smaller circles',
                    'Earlier onset dates reflected by darker gradients and smaller circles',
                    'Lower phenophase durations reflected by darker gradients and smaller circles',

                    'Lower average yearly phenophase onset date differences reflected by darker gradients and smaller circles',
                    'Lower average yearly phenophase duration differences reflected by darker gradients and smaller circles',
                    'Lower average yearly phenophase duration differences in percentage reflected by darker gradients and smaller circles',

                    'Lower differences in phenophase onset date compared to first record reflected by darker gradients and smaller circles',
                    'Lower differences in phenophase duration compared to first record reflected by darker gradients and smaller circles',
                    'Lower differences in phenophase duration compared to first record in percentage reflected by darker gradients and smaller circles']

    units = ['',
             '',
             'days',

             '',
             '',
             'days',

             'days',
             'days',
             '%',

             'days',
             'days',
             '%']

    fields = []
    for i, format in enumerate(str_formats):
        phase = 'budburst'
        phase_title = 'Bud Burst'
        field = format.format(PHASE = phase)
        title = titles[i].format(PHASE = phase_title)
        legend_desc = legend_descs[i].format(PHASE = phase_title.lower())
        fields.append([field, constant_pairs[2*i][0], constant_pairs[2*i][1], constant_pairs[2*i][0], constant_pairs[2*i][1], title, legend_desc, units[i]])
    
        phase = 'senescence'
        phase_title = 'Leaf Senescence'
        field = format.format(PHASE = phase)
        title = titles[i].format(PHASE = phase_title)
        legend_desc = legend_descs[i].format(PHASE = phase_title.lower())
        fields.append([field, constant_pairs[2*i+1][0], constant_pairs[2*i+1][1], constant_pairs[2*i+1][0], constant_pairs[2*i+1][1], title, legend_desc, units[i]])

    field_data = []

    with open('./main/static/mapdata.csv') as f:
        data = [{k: v for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    
    for field_set in fields:
        set_data = {'field': field_set[0], 'min_field': field_set[1], 'min': data[0][field_set[1]], 'max_field': field_set[2], 'max': data[0][field_set[2]], 'min_label': data[0][field_set[3]], 
                    'max_label': data[0][field_set[4]], 'title': field_set[5], 'legend_description': field_set[6], 'unit': field_set[7]}
        field_data.append(set_data)


    # only return requested data
    idx = 0
    for i, set_data in enumerate(field_data):
        if view == set_data['field']:
            idx = i
            break

    # fix date of year labels
    target_field = field_data[idx]['field']
    if ('doy' in target_field) and (not 'diff' in target_field):
        field_data[idx]['min_label'] = field_data[idx-2]['min_label']
        field_data[idx]['max_label'] = field_data[idx-2]['max_label']
    
    if 'PRCNT' in field_data[idx]['min_field'] or 'PRCNT' in field_data[idx]['max_field']:
        minfield = float(field_data[idx]['min_label']) * 100
        maxfield = float(field_data[idx]['max_label']) * 100

        field_data[idx]['min_label'] = f"{minfield:.4f}"
        field_data[idx]['max_label'] = f"{maxfield:.4f}"
            
    context = {'view': view, 'field': field_data[idx]}
    return render(response, 'main/site-map.html', context)


def site_datamap(response):
    str_formats = ['last_{PHASE}_doy',
                   'last_{PHASE}_dur',

                   'avg_last3yrs_{PHASE}_doy',
                   'avg_last3yrs_{PHASE}_dur',

                   'avg_diff_yrly_{PHASE}_tdate',
                   'avg_diff_yrly_{PHASE}_dur',
                   'avg_diff_yrly_{PHASE}_dur_prcnt',

                   'diff_firstlast_{PHASE}_tdate',
                   'diff_firstlast_{PHASE}_dur',
                   'diff_firstlast_{PHASE}_dur_prcnt']

    titles = ['Most Recent {PHASE} Onset Date',
              'Most Recent {PHASE} Duration',

              'Three Year Average {PHASE} Onset Date',
              'Three Year Average {PHASE} Duration',

              'Average Yearly Change in {PHASE} Onset Date',
              'Average Yearly Change in {PHASE} Duration',
              'Average Yearly Change in {PHASE} Duration',

              'Change in {PHASE} Onset Date Since First Year of Data',
              'Change in {PHASE} Duration Since First Year of Data',
              'Change in {PHASE} Duration Since First Year of Data']

    fields = []
    for i, format in enumerate(str_formats):
            phase = 'budburst'
            phase_title = 'Bud Burst'
            field = format.format(PHASE = phase)
            title = titles[i].format(PHASE = phase_title)
            fields.append({'field': field, 'title': title})
        
            phase = 'senescence'
            phase_title = 'Leaf Senescence'
            field = format.format(PHASE = phase)
            title = titles[i].format(PHASE = phase_title)
            fields.append({'field': field, 'title': title})

    context = {'fields': fields}
    return render(response, 'main/site-datamap.html', context)