"""
PhenoCam Raw Data Processing

This is the code for the the processing of the raw PhenoCam data, downloaded from both the PhenoCam dataset and the images hosted by UNH.
"""
import os
import csv
import json


def delete_tif():
    # delete all .tif files in this data directory
    directory = "./phenocam_data/"

    files_in_directory = os.listdir(directory)
    filtered_files = [file for file in files_in_directory if file.endswith(".tif")]
    for file in filtered_files:
        path_to_file = os.path.join(directory, file)
        os.remove(path_to_file)

def delete_meta_txt():
    directory = "./phenocam_data/"

    files_in_directory = os.listdir(directory)
    filtered_files = [file for file in files_in_directory if file.endswith(".txt")]
    for file in filtered_files:
        path_to_file = os.path.join(directory, file)
        os.remove(path_to_file)

def delete_non_deciduous():
    # delete all <sitename>_<veg_type>....csv files in this data directory that are not for Deciduous Broadleafs (DB)
    directory = "./phenocam_data/"

    files_in_directory = os.listdir(directory)
    filtered_files = [file for file in files_in_directory if file.endswith(".csv")]
    non_DB_data_records = [file for file in filtered_files if (file[file.find("_") + 1:file.find("_") + 3] != "DB")]

    for file in non_DB_data_records:
        path_to_file = os.path.join(directory, file)
        os.remove(path_to_file)

def delete_non_1day_transitions():
    # delete all non 1day_transtion_dates CSV files
    directory = "./phenocam_data/"

    files_in_directory = os.listdir(directory)
    filtered_files = [file for file in files_in_directory if file.endswith(".csv")]

    for file in filtered_files:
        is_transition_dates = file.find('1day_transition_dates')
        if is_transition_dates == -1:
            path_to_file = os.path.join(directory, file)
            os.remove(path_to_file)

def delete_non_1000_roi():
    # delete all non 1000 ROI transition dates CSV files
    directory = "./phenocam_data/"

    files_in_directory = os.listdir(directory)
    filtered_files = [file for file in files_in_directory if file.endswith(".csv")]

    for file in filtered_files:
        is_transition_dates = file.find('1000')
        if is_transition_dates == -1:
            path_to_file = os.path.join(directory, file)
            os.remove(path_to_file)

def delete_non_site_type_I():
    # delete all non site type 1 files
    directory = "./phenocam_data/"

    files_in_directory = os.listdir(directory)
    filtered_files = [file for file in files_in_directory if file.endswith(".json")]

    for file in filtered_files:
        with open(os.path.join(directory, file)) as f:
            data = json.load(f)
        sitename = data["phenocam_site"]["sitename"]
        site_type = data["phenocam_site"]["site_type"]
        is_site_type_i = site_type == "I"   # choose only site I sites because they have high data quality; long historical data is not as important for just phenophase classification

        if not is_site_type_i:
            files = [foo for foo in files_in_directory if foo.find(sitename) != -1]

            for fo in files:
                path_to_file = os.path.join(directory, fo)
                os.remove(path_to_file)

def delete_unneeded_sites():
    # delete the following remaining sites that I will not be using
    remove_these = ['ashbottoms', 'barrocolorado', 'groundhog', 'harvardbarn', 'harvardhemlock', 'hawbeckereddy', 'huyckpreserveny', 'kingmanfarm', 'NEON.D03.JERK.DP1.00033', 
                    'NEON.D05.TREE.DP1.00033', 'ninemileprairie', 'northattleboroma', 'proctor', 'sweetbriar', 'sylvania', 'ugseros', 'uwmfieldsta', 'woodstockvt', 'worcester', 
                    'caryinstitute', 'donanapajarera', 'NEON.D05.STEI.DP1', 'NEON.D05.UNDE.DP1']

    directory = "./phenocam_data/"
    files_in_directory = os.listdir(directory)

    for sitename in remove_these:
        files = [foo for foo in files_in_directory if foo.find(sitename) != -1]

        for f in files:
            path_to_file = os.path.join(directory, f)
            os.remove(path_to_file)

def delete_redundant_metas():
    # delete all redundant <sitename>_meta.json files
    directory = "./phenocam_data/"

    files_in_directory = os.listdir(directory)
    filtered_files = [file for file in files_in_directory if file.endswith(".json")]

    for file in filtered_files:
        sitename = file[:file.find('_')]
        
        site_data_files_left = [f for f in files_in_directory if (f.endswith('.csv') and (f.find(sitename) != -1))]
        
        if len(site_data_files_left) == 0:
            path_to_file = os.path.join(directory, file)
            os.remove(path_to_file)

def remove_csv_headers():
    # remove comments at beginning of CSV files
    directory = "./phenocam_data/"

    files_in_directory = os.listdir(directory)
    filtered_files = [file for file in files_in_directory if file.endswith(".csv")]

    for file in filtered_files:
        path_to_file = os.path.join(directory, file)
        lines = list()
        with open(path_to_file, 'r') as readFile:
            reader = csv.reader(readFile)
            for row in reader:
                lines.append(row)
            lines = lines[16:]
        with open(path_to_file, 'w', newline='') as writeFile:
            writer = csv.writer(writeFile)
            writer.writerows(lines)

def print_all_sites_used():
    # print all sites being used
    directory = "./phenocam_data/"

    files_in_directory = os.listdir(directory)
    filtered_files = [file for file in files_in_directory if file.endswith("meta.json")]

    print('[{}]'.format(len(filtered_files)))
    for file in filtered_files:
        sitename = file[:file.find('_')]
        print(sitename)

def process_image_data():
    # process image data, saving a list for each site containing only one image per day
    import json
    img_directory = '../PhenoCam_v2/images/'

    site_folders = [sitefldr for sitefldr in os.listdir(img_directory)]
    for site in site_folders:
        sitename = site[:site.find('_')]
        site_directory = img_directory + site + '/phenocamdata/' + sitename + '/'

        site_imgs = []

        for year in [yr for yr in os.listdir(site_directory) if (yr.find('.')==-1)]:
            year_directory = site_directory + year + '/'
            for month in os.listdir(year_directory):
                month_directory = year_directory + month + '/'
                imgs = [(month_directory + img) for img in os.listdir(month_directory) if img.endswith('.jpg')]

                dates_in_month = []
                for img_filename in imgs:
                    date_str = img_filename[-21:-4]
                    date_str_no_time = date_str[:10]
                    if not date_str_no_time in dates_in_month:
                        dates_in_month.append(date_str_no_time)

                for day in dates_in_month:
                    imgs_in_day = [img_filename for img_filename in imgs if img_filename.find(day) != -1]
                    distance_to_noon = {}
                    for img_filename in imgs_in_day:
                        time = int(img_filename[-10:-4])
                        if time / 120000 < 1:
                            distance = 116000 - time
                        else:
                            distance = time - 120000
                        distance_to_noon[img_filename] = distance
                    closest_img = min(distance_to_noon.items(), key=lambda x: x[1])[0]
                    
                    site_imgs.append(closest_img)

        # save into json in phenocam_data folder
        directory = './phenocam_data/'            
        imgs_json = {'img_file_names' : site_imgs}

        with open(directory + sitename + '_imgs.json', 'w') as file:
            json.dump(imgs_json, file, indent=4)

if __name__=='__main__':
    delete_tif()
    delete_meta_txt()
    delete_non_deciduous()
    delete_non_1day_transitions()
    delete_non_1000_roi()
    delete_non_site_type_I()
    delete_unneeded_sites()
    delete_redundant_metas()
    remove_csv_headers()
    print_all_sites_used()
    process_image_data()