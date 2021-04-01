""" Organize Data
This is where the code for the organization of data for phenophase classification will reside.

Three important parts of this: (1) finding average transition dates for each site and each year 
                               (2) storing this data in a readable JSON format
                               (3) organizing images according to transition date

"""
import statistics
import pandas as pd
import json
import os
from PIL import Image


# helper functions
def date_to_doy(date):
    year = int(date[:date.find('-')])
    adjusted_input = date[date.find('-')+1:]
    month = int(adjusted_input[:adjusted_input.find('-')])
    day = int(adjusted_input[adjusted_input.find('-')+1:])

    dates_in_prev_months = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334] #index 0 is jan, 1 is feb etc.
    doy = dates_in_prev_months[month - 1] + day
    
    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) and month > 2:
        doy += 1

    return doy, year

def doy_to_date(doy, year):
    leap_year = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    dates_in_prev_months = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334] #index 0 is jan, 1 is feb etc.
    dates_in_prev_months_lyr = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]

    month = 0
    day = 1

    for i in range(len(dates_in_prev_months)):
        if leap_year:
            if i == 11:
                month = 12
                day = doy - dates_in_prev_months_lyr[i]
                return year, month, day

            elif doy > dates_in_prev_months_lyr[i] and doy <= dates_in_prev_months_lyr[i+1]:
                month = i + 1
                if month >= 2:
                    day = doy - dates_in_prev_months_lyr[i]
                else: 
                    day = doy - dates_in_prev_months[i]
                return year, month, day
        else:
            if i == 11:
                month = 12
                day = doy - dates_in_prev_months[i]
                return year, month, day
            elif doy > dates_in_prev_months[i] and doy <= dates_in_prev_months[i+1]:
                month = i + 1
                day = doy - dates_in_prev_months[i]
                return year, month, day
        
    return year, month, day

def calc_average_transition_date(str_dates_list, is_rising):
    years = []
    doys = []
    for string in str_dates_list:
        doy, year = date_to_doy(string)
        doys.append(doy)
        years.append(year)
    avg_year = int(statistics.median(years))
    avg_doy = int(statistics.median(doys))
    _, avg_month, avg_day = doy_to_date(avg_doy, avg_year)
    date = str(avg_year) + '_' + str(avg_month) + '_' + str(avg_day)

    return {'rising':is_rising, 'date':date , 'year':avg_year, 'month':avg_month, 'day':avg_day, 'doy':avg_doy}

def is_rising(filename):
    # method, given input of img_file, output boolean indicating if rising or falling
    truncated_filename = filename[filename.rfind('/')+1:]
    sitename = truncated_filename[:truncated_filename.find('_')]
    date = truncated_filename[truncated_filename.find('_')+1:-11].replace('_', '-') 
    doy, year = date_to_doy(date)
    total_days = 365.2422 * year + doy

    # load json transition dates file
    with open('./phenocam_data/' + sitename + '_transition_dates.json', 'r') as file:
         site_transitions =  json.load(file)['transitions']

    # find closest
    distances = []
    for i in range(len(site_transitions)):
        year_trans = site_transitions[i]['year']
        doy_trans = site_transitions[i]['doy']
        total_days_trans = 365.2422 * year_trans + doy_trans
        distance = total_days - total_days_trans
        abs_distance = abs(distance)
        distances.append((i, distance, abs_distance))
    
    closest = min(distances, key=lambda x: x[2])
    if site_transitions[closest[0]]['rising']:
        return closest[1] >= 0
    else:
        return closest[1] < 0


# action functions
def extract_save_transition_dates():
    # Extract all transition dates from CSV files, then caculate median date, and save the respective transition dates for each to a JSON file
    directory = "./phenocam_data/"
    files_in_directory = os.listdir(directory)
    filtered_files = [file for file in files_in_directory if file.endswith(".csv")]

    for file in filtered_files:
        path_to_file = os.path.join(directory, file)
        sitename = file[:file.find('_')]

        df = pd.read_csv(path_to_file, index_col=False)
        df_lists = df.values.tolist()
        
        num_rising = 0
        num_falling = 0
        for list in df_lists:
            if 'rising' in (string for string in list): 
                num_rising += 1
            elif 'falling' in (string for string in list): 
                num_falling += 1 

        num_rising_transitions = int(num_rising / 4)
        num_falling_transitions = int(num_falling / 4)

        rising = [[] for _ in range(num_rising_transitions)]
        falling = [[] for _ in range(num_falling_transitions)]

        i = 0
        for list in df_lists:
            if 'rising' in (string for string in list): 
                rising[i].extend(list[5:14])
                i += 1
                if i==num_rising_transitions: i=0
            elif 'falling' in (string for string in list): 
                falling[i].extend(list[5:14])  
                i += 1
                if i==num_falling_transitions: i=0
        
        avg_transitions = [calc_average_transition_date(transition, True) for transition in rising]
        avg_transitions.extend([calc_average_transition_date(transition, False) for transition in falling])

        transition_date_data = {
            'sitename': sitename,
            'transitions': avg_transitions,
        }

        file_to_save = sitename + '_transition_dates.json'
        path_to_target = os.path.join(directory, file_to_save) 
        with open(path_to_target, 'w') as f:
            json.dump(transition_date_data, f, indent=4)

def sort_images_rising_falling():
    # sort images into "sorted_images" folder according to rising or falling
    directory = "./phenocam_data/"
    target_directory = '../PhenoCam_v2/sorted_images/'

    files_in_directory = os.listdir(directory)
    filtered_files = [file for file in files_in_directory if file.endswith("imgs.json")]

    print("Started sorting!")
    for file in filtered_files:
        print("Site:", file[:-10])
        with open(directory + file, 'r') as f:
            img_list = json.load(f)['img_file_names']
        for img_filename in img_list:
            filename = img_filename[img_filename.rfind('/')+1:] 
            if is_rising(img_filename):
                img = Image.open(img_filename)
                img.save(target_directory + 'rising/' + filename)
            else:
                img = Image.open(img_filename)
                img.save(target_directory + 'falling/' + filename)


if __name__=='__main__':
    extract_save_transition_dates()
    sort_images_rising_falling()