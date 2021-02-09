import json
import os
import time
from datetime import date, datetime

import numpy as np
import pandas as pd
import pytz

"""Create CSV Data for ArcGIS to Interface With"""


def get_min_max_years(base_dir, sites_data_paths):
    min_year = 2009
    max_year = 2018
    for filepath in sites_data_paths:
        if 'meta' in filepath:
            with open(file=os.path.join(base_dir, filepath)) as f:
                meta_data = json.load(f)
            year_start = int(meta_data['phenocam_site']['date_start'][:4])
            year_end = int(meta_data['phenocam_site']['date_end'][:4])

            min_year = min([min_year, year_start])
            max_year = max([max_year, year_end])
    return min_year, max_year


def calc_days_between_date_strs(date_str1, date_str2):
    date_list1 = date_str1.split('-')
    date_list1 = [int(n) for n in date_list1]
    date_list2 = date_str2.split('-')
    date_list2 = [int(n) for n in date_list2]

    date1 = datetime(year=date_list1[0], month=date_list1[1], day=date_list1[2], tzinfo=pytz.timezone('UTC'))
    date2 = datetime(year=date_list2[0], month=date_list2[1], day=date_list2[2], tzinfo=pytz.timezone('UTC'))

    diff = date2 - date1
    return int(diff.total_seconds() / (3600 * 24))


def calc_avg_last3yrs_stats(phases_yrly):
    # try to get two phases beforehand
    tdates = []
    doys = []
    durs = []
    for phase in reversed(phases_yrly):
        try:
            if len(tdates) <= 3:
                tdates.append(datetime(year=2000, month=phase['month'], day=phase['day'], tzinfo=pytz.timezone('UTC')).timestamp())
            if len(tdates) <= 3:
                if phase['doy']==179 and not phase['rising']: print(phase)
                doys.append(phase['doy'])
            if len(durs) <= 3 and phase['duration'] != None:
                durs.append(phase['duration'])
        except:
            pass

    avg_last3yrs_tdate = None
    avg_last3yrs_doy = None
    avg_last3yrs_dur = None

    if len(tdates) != 0:
        avg_tdate = datetime.fromtimestamp(sum(tdates) / len(tdates))
        avg_last3yrs_tdate = '{}/{}'.format(avg_tdate.month, avg_tdate.day)
    if len(doys) != 0:
        avg_last3yrs_doy = int(sum(doys) / len(doys))
    if len(durs) != 0:
        avg_last3yrs_dur = int(sum(durs) / len(durs))

    return avg_last3yrs_tdate, avg_last3yrs_doy, avg_last3yrs_dur


def calc_avg_diff_yrly_stats(phases_yrly):
    total_diff_tdate = []
    total_diff_dur = []
    total_diff_dur_prcnt = []
    for phase in phases_yrly:
        try:
            total_diff_tdate.append(phase['diff_tdate'])
        except:
            pass
        try:
            total_diff_dur.append(phase['diff_duration'])
        except:
            pass
        try:
            total_diff_dur_prcnt.append(phase['diff_duration_prcnt'])
        except:
            pass

    total_diff_tdate = [x for x in total_diff_tdate if x != None]
    total_diff_dur = [x for x in total_diff_dur if x != None]
    total_diff_dur_prcnt = [x for x in total_diff_dur_prcnt if x != None]

    avg_diff_tdate = None
    avg_diff_dur = None
    avg_diff_dur_prcnt = None
    try:
        avg_diff_tdate = int(sum(total_diff_tdate) / len(total_diff_tdate))
    except:
        pass
    try:
        avg_diff_dur = sum(total_diff_dur) / len(total_diff_dur)
    except:
        pass
    try:
        avg_diff_dur_prcnt = sum(total_diff_dur_prcnt) / len(total_diff_dur_prcnt)
    except:
        pass
    return avg_diff_tdate, avg_diff_dur, avg_diff_dur_prcnt


def calc_days_between_firstlast_tdate(phases_yrly):
    if len(phases_yrly) >= 2:
        month1 = phases_yrly[0]['month']
        day1 = phases_yrly[0]['day']
        month2 = phases_yrly[-1]['month']
        day2 = phases_yrly[-1]['day']

        try:
            date1 = datetime(year=2020, month=month1, day=day1, tzinfo=pytz.timezone('UTC'))
            date2 = datetime(year=2020, month=month2, day=day2, tzinfo=pytz.timezone('UTC'))

            diff = date2 - date1
            return int(diff.total_seconds() / (3600 * 24))
        except:
            return None
    else:
        return None


def calc_stats(siteJSON):
    transitions = siteJSON['transitions']

    # sort transitions by date
    transitions.sort(key=lambda x: x['year']*365 + x['doy'])

    # get min_max years
    min_year = transitions[0]['year']
    max_year = transitions[-1]['year']

    # calculate durations
    for i in range(len(transitions)-1):
        this_date = datetime(year=transitions[i]['year'], month=transitions[i]['month'], day=transitions[i]['day'], tzinfo=pytz.timezone('UTC'))
        next_date = datetime(year=transitions[i+1]['year'], month=transitions[i+1]['month'], day=transitions[i+1]['day'], tzinfo=pytz.timezone('UTC'))
        diff = next_date - this_date
        duration = int(diff.total_seconds() / (3600 * 24))
        if duration != 0:
            transitions[i]['duration'] = duration
        else:
            transitions[i]['duration'] = None
    transitions[-1]['duration'] = None

    # reading-friendly date
    for transition in transitions:
        tdate = str(transition['month']) + '/' + str(transition['day']) + '/' + str(transition['year'])
        transition['tdate'] = tdate

    # sort into respective yearly phenophases
    budburst_phases_yrly = []
    senescence_phases_yrly = []
    for phase in [transition for transition in transitions if transition['rising']]:
        budburst_phases_yrly.append(phase)
    for phase in [transition for transition in transitions if not transition['rising']]:
        senescence_phases_yrly.append(phase)

    # calculate changes from previous year
    # calculate changes for bud burst phases
    phases = budburst_phases_yrly
    for i, phase in enumerate(phases[1:]):
        current_date = datetime(year=2000, month=phase['month'], day=phase['day'], tzinfo=pytz.timezone('UTC'))
        prev_date = datetime(year=2000, month=phases[i]['month'], day=phases[i]['day'], tzinfo=pytz.timezone('UTC'))
        current_date_j = int(current_date.strftime('%j'))
        prev_date_j = int(prev_date.strftime('%j'))
        diff = current_date_j - prev_date_j

        current_duration = phase['duration']
        prev_duration = phases[i]['duration']
        diff_duration = None
        diff_duration_prcnt = None
        try:
            diff_duration = int(float(current_duration) - float(prev_duration))
            diff_duration_prcnt = float(diff_duration / prev_duration)
        except:
            pass

        phase['diff_tdate'] = diff
        phase['diff_duration'] = diff_duration
        phase['diff_duration_prcnt'] = diff_duration_prcnt

    # calculate changes for sensescence phases
    phases = senescence_phases_yrly
    for i, phase in enumerate(phases[1:]):
        current_date = datetime(year=2000, month=phase['month'], day=phase['day'], tzinfo=pytz.timezone('UTC'))
        prev_date = datetime(year=2000, month=phases[i]['month'], day=phases[i]['day'], tzinfo=pytz.timezone('UTC'))
        current_date_j = int(current_date.strftime('%j'))
        prev_date_j = int(prev_date.strftime('%j'))
        diff = current_date_j - prev_date_j

        current_duration = phase['duration']
        prev_duration = phases[i]['duration']
        diff_duration = None
        diff_duration_prcnt = None
        try:
            diff_duration = int(float(current_duration) - float(prev_duration))
            diff_duration_prcnt = float(diff_duration / prev_duration)
        except:
            pass

        phase['diff_tdate'] = diff
        phase['diff_duration'] = diff_duration
        phase['diff_duration_prcnt'] = diff_duration_prcnt

    # input statistics into stats dict
    stats = {'MINYEAR': min_year, 'MAXYEAR': max_year, }

    # input yearly stats
    # input yearly bud burst stats
    phases = budburst_phases_yrly
    for phase in phases:
        stats['{}_yrly_budburst_tdate'.format(phase['year'])] = phase['tdate']
        stats['{}_yrly_budburst_doy'.format(phase['year'])] = phase['doy']
        stats['{}_yrly_budburst_dur'.format(phase['year'])] = phase['duration']
        try:
            stats['{}_diff_yrly_budburst_tdate'.format(phase['year'])] = phase['diff_tdate']
            stats['{}_diff_yrly_budburst_dur'.format(phase['year'])] = phase['diff_duration']
            stats['{}_diff_yrly_budburst_dur_prcnt'.format(phase['year'])] = phase['diff_duration_prcnt']
        except:
            pass

    # input yearly senescence stats
    phases = senescence_phases_yrly
    for phase in phases:
        stats['{}_yrly_senescence_tdate'.format(phase['year'])] = phase['tdate']
        stats['{}_yrly_senescence_doy'.format(phase['year'])] = phase['doy']
        stats['{}_yrly_senescence_dur'.format(phase['year'])] = phase['duration']
        try:
            stats['{}_diff_yrly_senescence_tdate'.format(phase['year'])] = phase['diff_tdate']
            stats['{}_diff_yrly_senescence_dur'.format(phase['year'])] = phase['diff_duration']
            stats['{}_diff_yrly_senescence_dur_prcnt'.format(phase['year'])] = phase['diff_duration_prcnt']
        except:
            pass

    # input general stats
    # calculate bud burst general stats
    last_budburst_tdate = None
    last_budburst_doy = None
    last_budburst_dur = None
    try:
        last_budburst_tdate = budburst_phases_yrly[-1]['tdate']
        last_budburst_doy = budburst_phases_yrly[-1]['doy']
        last_budburst_dur = [x for x in budburst_phases_yrly if x['duration'] != None][-1]['duration']
    except:
        pass
    avg_last3yrs_budburst_tdate, avg_last3yrs_budburst_doy, avg_last3yrs_budburst_dur = calc_avg_last3yrs_stats(budburst_phases_yrly)
    avg_diff_yrly_budburst_tdate, avg_diff_yrly_budburst_dur, avg_diff_yrly_budburst_dur_prcnt = calc_avg_diff_yrly_stats(budburst_phases_yrly)
    diff_firstlast_budburst_tdate = calc_days_between_firstlast_tdate(budburst_phases_yrly)
    diff_firstlast_budburst_dur = None
    diff_firstlast_budburst_dur_prcnt = None
    try:
        diff_firstlast_budburst_dur = last_budburst_dur - budburst_phases_yrly[0]['duration']
        diff_firstlast_budburst_dur_prcnt = diff_firstlast_budburst_dur / budburst_phases_yrly[0]['duration']
    except:
        pass

    # calculate leaf senescence general stats
    last_senescence_tdate = None
    last_senescence_doy = None
    last_senescence_dur = None
    try:
        last_senescence_tdate = senescence_phases_yrly[-1]['tdate']
        last_senescence_doy = senescence_phases_yrly[-1]['doy']
        last_senescence_dur = [x for x in senescence_phases_yrly if x['duration'] != None][-1]['duration']
    except:
        pass
    avg_last3yrs_senescence_tdate, avg_last3yrs_senescence_doy, avg_last3yrs_senescence_dur = calc_avg_last3yrs_stats(senescence_phases_yrly)
    avg_diff_yrly_senescence_tdate, avg_diff_yrly_senescence_dur, avg_diff_yrly_senescence_dur_prcnt = calc_avg_diff_yrly_stats(senescence_phases_yrly)
    diff_firstlast_sensescence_tdate = calc_days_between_firstlast_tdate(senescence_phases_yrly)
    diff_firstlast_senescence_dur = None
    diff_firstlast_senescence_dur_prcnt = None
    try:
        diff_firstlast_senescence_dur = last_senescence_dur - senescence_phases_yrly[0]['duration']
        diff_firstlast_senescence_dur_prcnt = diff_firstlast_senescence_dur / senescence_phases_yrly[0]['duration']
    except:
        pass

    # input bud burst general stats
    stats['last_budburst_tdate'] = last_budburst_tdate
    stats['last_budburst_doy'] = last_budburst_doy
    stats['last_budburst_dur'] = last_budburst_dur
    stats['avg_last3yrs_budburst_tdate'] = avg_last3yrs_budburst_tdate
    stats['avg_last3yrs_budburst_doy'] = avg_last3yrs_budburst_doy
    stats['avg_last3yrs_budburst_dur'] = avg_last3yrs_budburst_dur
    stats['avg_diff_yrly_budburst_tdate'] = avg_diff_yrly_budburst_tdate
    stats['avg_diff_yrly_budburst_dur'] = avg_diff_yrly_budburst_dur
    stats['avg_diff_yrly_budburst_dur_prcnt'] = avg_diff_yrly_budburst_dur_prcnt
    stats['diff_firstlast_budburst_tdate'] = diff_firstlast_budburst_tdate
    stats['diff_firstlast_budburst_dur'] = diff_firstlast_budburst_dur
    stats['diff_firstlast_budburst_dur_prcnt'] = diff_firstlast_budburst_dur_prcnt

    # calculate leaf senescence general stats
    # input leaf senescence general stats
    stats['last_senescence_tdate'] = last_senescence_tdate
    stats['last_senescence_doy'] = last_senescence_doy
    stats['last_senescence_dur'] = last_senescence_dur
    stats['avg_last3yrs_senescence_tdate'] = avg_last3yrs_senescence_tdate
    stats['avg_last3yrs_senescence_doy'] = avg_last3yrs_senescence_doy
    stats['avg_last3yrs_senescence_dur'] = avg_last3yrs_senescence_dur
    stats['avg_diff_yrly_senescence_tdate'] = avg_diff_yrly_senescence_tdate
    stats['avg_diff_yrly_senescence_dur'] = avg_diff_yrly_senescence_dur
    stats['avg_diff_yrly_senescence_dur_prcnt'] = avg_diff_yrly_senescence_dur_prcnt
    stats['diff_firstlast_senescence_tdate'] = diff_firstlast_sensescence_tdate
    stats['diff_firstlast_senescence_dur'] = diff_firstlast_senescence_dur
    stats['diff_firstlast_senescence_dur_prcnt'] = diff_firstlast_senescence_dur_prcnt

    return stats


def calc_constants(data, min_year, max_year):
    str_formats = ['{YEAR}_yrly_{PHASE}_tdate',
                   '{YEAR}_yrly_{PHASE}_doy',
                   '{YEAR}_yrly_{PHASE}_dur',

                   '{YEAR}_diff_yrly_{PHASE}_tdate',
                   '{YEAR}_diff_yrly_{PHASE}_dur',
                   '{YEAR}_diff_yrly_{PHASE}_dur_prcnt',

                   'last_{PHASE}_tdate',
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

    desired_constants = [['MIN_BUDBURST_TDATE', 'MAX_BUDBURST_TDATE', 'MIN_SENESCENCE_TDATE', 'MAX_SENESCENCE_TDATE'],  # YEARLY
                         ['MIN_BUDBURST_DOY', 'MAX_BUDBURST_DOY', 'MIN_SENESCENCE_DOY', 'MAX_SENESCENCE_DOY'],
                         ['MIN_BUDBURST_DUR', 'MAX_BUDBURST_DUR', 'MIN_SENESCENCE_DUR', 'MAX_SENESCENCE_DUR'],

                         ['MIN_BUDBURST_DIFF_TDATE', 'MAX_BUDBURST_DIFF_TDATE', 'MIN_SENESCENCE_DIFF_TDATE', 'MAX_SENESCENCE_DIFF_TDATE'],
                         ['MIN_BUDBURST_DIFF_DUR', 'MAX_BUDBURST_DIFF_DUR', 'MIN_SENESCENCE_DIFF_DUR', 'MAX_SENESCENCE_DIFF_DUR'],
                         ['MIN_BUDBURST_DIFF_DUR_PRCNT', 'MAX_BUDBURST_DIFF_DUR_PRCNT', 'MIN_SENESCENCE_DIFF_DUR_PRCNT', 'MAX_SENESCENCE_DIFF_DUR_PRCNT'],  # END YEARLY

                         ['MIN_BUDBURST_RECENT_TDATE', 'MAX_BUDBURST_RECENT_TDATE', 'MIN_SENESCENCE_RECENT_TDATE', 'MAX_SENESCENCE_RECENT_TDATE'],  # MOST RECENT
                         ['MIN_BUDBURST_RECENT_DOY', 'MAX_BUDBURST_RECENT_DOY', 'MIN_SENESCENCE_RECENT_DOY', 'MAX_SENESCENCE_RECENT_DOY'],
                         ['MIN_BUDBURST_RECENT_DUR', 'MAX_BUDBURST_RECENT_DUR', 'MIN_SENESCENCE_RECENT_DUR', 'MAX_SENESCENCE_RECENT_DUR'],  # END MOST RECENT

                         ['MIN_BUDBURST_AVG3YRS_TDATE', 'MAX_BUDBURST_AVG3YRS_TDATE', 'MIN_SENESCENCE_AVG3YRS_TDATE', 'MAX_SENESCENCE_AVG3YRS_TDATE'],  # 3YR AVERAGE
                         ['MIN_BUDBURST_AVG3YRS_DOY', 'MAX_BUDBURST_AVG3YRS_DOY', 'MIN_SENESCENCE_AVG3YRS_DOY', 'MAX_SENESCENCE_AVG3YRS_DOY'],
                         ['MIN_BUDBURST_AVG3YRS_DUR', 'MAX_BUDBURST_AVG3YRS_DUR', 'MIN_SENESCENCE_AVG3YRS_DUR', 'MAX_SENESCENCE_AVG3YRS_DUR'],  # END 3YR AVERAGE

                         ['MIN_BUDBURST_AVG_DIFF_TDATE', 'MAX_BUDBURST_AVG_DIFF_TDATE', 'MIN_SENESCENCE_AVG_DIFF_TDATE', 'MAX_SENESCENCE_AVG_DIFF_TDATE'],  # AVG DIFF
                         ['MIN_BUDBURST_AVG_DIFF_DUR', 'MAX_BUDBURST_AVG_DIFF_DUR', 'MIN_SENESCENCE_AVG_DIFF_DUR', 'MAX_SENESCENCE_AVG_DIFF_DUR'],
                         ['MIN_BUDBURST_AVG_DIFF_DUR_PRCNT', 'MAX_BUDBURST_AVG_DIFF_DUR_PRCNT',
                             'MIN_SENESCENCE_AVG_DIFF_DUR_PRCNT', 'MAX_SENESCENCE_AVG_DIFF_DUR_PRCNT'],  # END AVG DIF

                         ['MIN_BUDBURST_TOTAL_DIFF_DOY', 'MAX_BUDBURST_TOTAL_DIFF_DOY', 'MIN_SENESCENCE_TOTAL_DIFF_DOY', 'MAX_SENESCENCE_TOTAL_DIFF_DOY'],  # TOTAL DIFF
                         ['MIN_BUDBURST_TOTAL_DIFF_DUR', 'MAX_BUDBURST_TOTAL_DIFF_DUR', 'MIN_SENESCENCE_TOTAL_DIFF_DUR', 'MAX_SENESCENCE_TOTAL_DIFF_DUR'],
                         ['MIN_BUDBURST_TOTAL_DIFF_DUR_PRCNT', 'MAX_BUDBURST_TOTAL_DIFF_DUR_PRCNT', 'MIN_SENESCENCE_TOTAL_DIFF_DUR_PRCNT', 'MAX_SENESCENCE_TOTAL_DIFF_DUR_PRCNT']]  # END TOTAL DIFF
    constants = {}

    def get_min_max_both_phenophases(str_format, constant_list, i):
        yearly_stat = i < 6

        def compare_dates(datestr1, datestr2):  # returns true if datestr1 occurs before datestr2
            datelist1 = [int(x) for x in datestr1.split('/')]
            datelist2 = [int(x) for x in datestr2.split('/')]
            datetime1 = date(year=2000, month=datelist1[0], day=datelist1[1])
            datetime2 = date(year=2000, month=datelist2[0], day=datelist2[1])
            return datetime1 < datetime2

        if not yearly_stat:
            # create constants for budburst
            phase = 'budburst'
            minval = 99999999
            maxval = -99999999
            tdate = None

            if 'tdate' in str_format and not 'diff' in str_format:
                minval = '12/31'
                maxval = '01/01'
                tdate = True

            for value in [site.get(str_format.format(PHASE=phase)) for site in data]:
                if value!=None:
                    if tdate:
                        if compare_dates(value, minval):
                            minval = value
                        elif compare_dates(maxval, value):
                            maxval = value
                    else:
                        if minval > value:
                            if not ('{PHASE}_DUR' in str_format  and value <=60):
                                minval = value
                        elif maxval < value:
                            if not ('{PHASE}_DUR' in str_format  and value >= 315):
                                maxval = value
            constants[constant_list[0]] = minval
            constants[constant_list[1]] = maxval
            if tdate:
                minval_list = minval.split('/')
                maxval_list = maxval.split('/')
                constants[constant_list[0]] = '{}/{}'.format(minval_list[0], minval_list[1])
                constants[constant_list[1]] = '{}/{}'.format(maxval_list[0], maxval_list[1])

            # create constants for senescence
            phase = 'senescence'
            minval = 99999999
            maxval = -99999999
            tdate = False

            if 'tdate' in str_format and not 'diff' in str_format:
                minval = '12/12/2021'
                maxval = '01/01/2000'
                tdate = True

            for i, value in enumerate([site.get(str_format.format(PHASE=phase)) for site in data]):
                if value != None:
                    if tdate:
                        if compare_dates(value, minval):
                            minval = value[0:4]
                        elif compare_dates(maxval, value):
                            maxval = value[0:4]
                    else:
                        if minval > value:
                            if not ('{PHASE}_DUR' in str_format and value <=60):
                                minval = value
                            else:
                                print('uh oh!!!', str_format, value, minval)
                        elif maxval < value:
                            if not ('{PHASE}_DUR' in str_format and value >= 315):
                                maxval = value
                            else:
                                print('uh oh!!!', str_format, value, maxval)

            constants[constant_list[2]] = minval
            constants[constant_list[3]] = maxval
            if tdate:
                minval_list = minval.split('/')
                maxval_list = maxval.split('/')
                constants[constant_list[2]] = '{}/{}'.format(minval_list[0], minval_list[1])
                constants[constant_list[3]] = '{}/{}'.format(maxval_list[0], maxval_list[1])

        else:  # if yearly stats
            years = [x for x in range(min_year, max_year)]
            
            # create constants for budburst
            phase = 'budburst'
            minval = 99999999
            maxval = -99999999
            tdate = False

            if 'tdate' in str_format and not 'diff' in str_format:
                    minval = '12/12/2021'
                    maxval = '01/01/2000'
                    tdate = True

            for year in years:
                for value in [site.get(str_format.format(YEAR=year, PHASE=phase)) for site in data]:
                    if value != None:
                        if tdate:
                            if compare_dates(value, minval):
                                minval = value
                            elif compare_dates(maxval, value):
                                maxval = value
                        else:
                            if minval > value:
                                if not ('{PHASE}_DUR' in str_format  and value <=60):
                                    minval = value
                                else:
                                    print('uh oh!!!', str_format, value, minval)
                            elif maxval < value:
                                if not ('{PHASE}_DUR' in str_format  and value >= 315):
                                    maxval = value
                                else:
                                    print('uh oh!!!', str_format, value, maxval)

            constants[constant_list[0]] = minval
            constants[constant_list[1]] = maxval

            # create constants for senescence
            phase = 'senescence'
            minval = 99999999
            maxval = -99999999
            tdate = False

            if 'tdate' in str_format and not 'diff' in str_format:
                minval = '12/12/2021'
                maxval = '01/01/2000'
                tdate = True

            for year in years:    
                for value in [site.get(str_format.format(YEAR=year, PHASE=phase)) for site in data]:
                    if value != None:
                        if tdate:
                            if compare_dates(value, minval):
                                minval = value
                            elif compare_dates(maxval, value):
                                maxval = value
                        else:
                            if minval > value:
                                if not ('{PHASE}_DUR' in str_format  and value <=60):
                                    minval = value
                            elif maxval < value:
                                if not ('{PHASE}_DUR' in str_format  and value >= 315):
                                    maxval = value
                constants[constant_list[2]] = minval
                constants[constant_list[3]] = maxval

    for i, (str_format, constant_list) in enumerate(zip(str_formats, desired_constants)):
        get_min_max_both_phenophases(str_format, constant_list, i)

    return constants


def get_site_data(site_data_paths, base_dir):
    meta_filepath = [filepath for filepath in site_data_paths if 'meta' in filepath][0]
    transition_dates_filepath = [filepath for filepath in site_data_paths if 'transition_dates' in filepath][0]
    with open(file=os.path.join(base_dir, meta_filepath)) as f:
        meta_data = json.load(f)
    with open(file=os.path.join(base_dir, transition_dates_filepath)) as f:
        transition_data = json.load(f)

    """meta data"""
    meta = {'sitename': meta_data['phenocam_site']['sitename'], 'location': meta_data['phenocam_site']['long_name'], 'latitude': meta_data['phenocam_site']['lat'],
            'longitude': meta_data['phenocam_site']['lon'], 'elevation': meta_data['phenocam_site']['elevation'], 'first_im_date': meta_data['phenocam_site']['date_start'],
            'last_im_date': meta_data['phenocam_site']['date_end'], 'last_updated': meta_data['last_updated'], 'dominant_species': meta_data['phenocam_site']['dominant_species'].replace('\n', ' '),
            'num_images': calc_days_between_date_strs(meta_data['phenocam_site']['date_start'], meta_data['phenocam_site']['date_end'])}
    first_im_str = meta['first_im_date']
    last_im_str = meta['last_im_date']
    last_updated_str = meta['last_updated']
    first_im_str1 = first_im_str + ' 12:00AM UTC'
    last_im_str1 = last_im_str + ' 12:00AM UTC'
    last_updated_str1 = last_updated_str + ' 12:00AM UTC'
    first_im_datetime = datetime.strptime(first_im_str1, '%Y-%m-%d %H:%M%p %Z')
    last_im_datetime = datetime.strptime(last_im_str1, '%Y-%m-%d %H:%M%p %Z')
    last_updated_datetime = datetime.strptime(last_updated_str1, '%Y-%m-%d %H:%M%p %Z')
    meta['first_im_date'] = first_im_datetime.strftime('%m/%d/%Y')
    meta['last_im_date'] = last_im_datetime.strftime('%m/%d/%Y')
    meta['last_updated'] = last_updated_datetime.strftime('%m/%d/%Y')

    """"stats data"""
    stats = calc_stats(transition_data)

    return {**meta, **stats}


def create_csv():
    # get all meta and transition date json filepaths
    source_dir = './../../Phenophase_Classification/phenocam_data/'
    sites_data = [site_data for site_data in os.listdir(source_dir) if site_data.endswith('_meta.json') or site_data.endswith('_transition_dates.json')]
    sitenames = list(set([site_data[:site_data.find('_')+1] for site_data in sites_data]))
    sitenames.sort(key=lambda x: x.lower())
    min_year, max_year = get_min_max_years(source_dir, sites_data)

    sites_data_paths = []
    for sitename in sitenames:
        sites_data_paths.append([file for file in sites_data if sitename in file])

    # gather data for each site
    data = [get_site_data(site, source_dir) for site in sites_data_paths]
    constants = calc_constants(data, min_year, max_year)
    data_with_constants = [{**sitedata, **constants} for sitedata in data]

    # create dataframe
    df = pd.DataFrame(data_with_constants)

    # sort data alphabetically by sitename
    df.sort_values('sitename')

    # convert empty string and None cells to NaN
    df.replace('', np.nan)
    df.fillna(np.nan)

    # drop columns that only have NaN
    df.dropna(1, 'all')

    # save dataframe
    module_dir = os.path.dirname(__file__)  # get current directory
    file_path = os.path.join(module_dir, 'static/mapdata.csv')
    df.to_csv(file_path)


if __name__ == '__main__':
    create_csv()
